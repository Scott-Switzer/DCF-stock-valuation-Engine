import {valuationOverlay,VAL} from './valuation.mjs';
// Continue the existing private queue using the newer archive already stored in R2.
export const ENRICH='staging/security-funnel/2026-10-20/9beaa712e71650a2/source-enrichment-2026-10-21-v1/';
const FULL='staging/security-funnel/2026-10-20/9beaa712e71650a2/full-history-2026-10-21-v1/';
const FULL_PIN='68db69ad8e4693616d5735b836764e7cd034c45bf9e7a79e483a99bd3163507a';
const MANIFEST='sec/bulk/sec-nightly-20261015/manifest-corrected.json';
const MANIFEST_SHA='9f30450b4465fabcf445e50b69d76774553d5b7bbbb55723184b7f59a649ad0d';
const INDEX='sec/bulk/sec-nightly-20261015/member-index.json';
const INDEX_SHA='af4aef61b64818cf49bbe0edc0b2cd9fde6e293263783e85145bf86adb83396d';
const JOB='source-enrichment-v1';
const fail=code=>{throw Error(code)};
const sha=async raw=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),x=>x.toString(16).padStart(2,'0')).join('');
async function read(bucket,key,digest=null,max=8*1048576){const o=await bucket.get(key);if(!o||o.size>max)fail('ENRICHMENT_SOURCE_MISSING_OR_BUDGET');const raw=await o.text();if(digest&&await sha(raw)!==digest)fail('ENRICHMENT_SOURCE_HASH');return JSON.parse(raw);}
async function put(env,key,value){await env.DATA.put(key,JSON.stringify(value),{httpMetadata:{contentType:'application/json'}});}
async function immutable(env,kind,value){const raw=JSON.stringify(value),digest=await sha(raw),key=ENRICH+kind+'/by-sha256/'+digest+'.json';await env.DATA.put(key,raw);return {key,sha256:digest};}
export function eligibleCik(value){return typeof value==='string'&&/^\d{10}$/.test(value)&&value!=='0000000000';}
export async function enrichmentRoute(env,u){
 if(u.pathname==='/connect/enrichment-init'){
  const manifest=await read(env.RESEARCH,MANIFEST,MANIFEST_SHA),index=await read(env.RESEARCH,INDEX,INDEX_SHA);
  if(manifest.snapshot_date!=='2026-10-15'||manifest.archive.r2_member_index.sha256!==INDEX_SHA||manifest.archive.stored_etag!=='d29bd665a067752760c34067dd96038e'||manifest.archive.stored_bytes!==1410532244)fail('ENRICHMENT_SOURCE_CONTEXT');
  const source={bucket:'financial-data-wrds-private',key:manifest.archive.key,bytes:manifest.archive.stored_bytes,etag:manifest.archive.stored_etag,sha256:manifest.archive.sha256,snapshot_date:manifest.snapshot_date,manifest_key:MANIFEST,manifest_sha256:MANIFEST_SHA,index_key:INDEX,index_sha256:INDEX_SHA};
  const byCik={},excluded=[],symbols=[];
  for(let first=0;first<132;first+=8){
   const batches=await Promise.all(Array.from({length:Math.min(8,132-first)},(_,i)=>read(env.DATA,FULL+`batches/${first+i}.json`)));
   for(const b of batches){if(b.input_sha256!==FULL_PIN)fail('ENRICHMENT_COHORT_PIN');for(const r of b.rows){
    symbols.push(r.symbol);const cik=r.identity.cik,entry=index[`CIK${cik}.json`]||index[cik];
    if(!eligibleCik(cik)||!entry){excluded.push({symbol:r.symbol,cik:cik||null,reason:!eligibleCik(cik)?'NO_CIK_IN_FROZEN_LEDGER':'CIK_NOT_IN_NEW_ARCHIVE'});continue;}
    (byCik[cik]??={cik,entry,symbols:[],new_symbols:[]}).symbols.push(r.symbol);if(!r.financials.cloud?.query_fingerprint)byCik[cik].new_symbols.push(r.symbol);
   }}
  }
  if(symbols.length!==2629||new Set(symbols).size!==2629)fail('ENRICHMENT_UNIVERSE');
  const shards={};for(let n=0;n<100;n++){const suffix=String(n).padStart(2,'0');const entries=Object.fromEntries(Object.entries(byCik).filter(([cik])=>cik.endsWith(suffix)));if(Object.keys(entries).length)shards[suffix]=await immutable(env,'source-index-shards',entries);}
  const plan={schema_version:JOB,source,input_sha256:FULL_PIN,ciks:Object.keys(byCik).sort(),symbols,excluded,shards,eligible_symbols:Object.values(byCik).reduce((a,v)=>a+v.symbols.length,0),newly_source_eligible_symbols:Object.values(byCik).reduce((a,v)=>a+v.new_symbols.length,0)};
  const ref=await immutable(env,'plans',plan);await put(env,ENRICH+'plan.json',ref);
  return {plan:ref,accounted:2629,issuers:plan.ciks.length,eligible_symbols:plan.eligible_symbols,newly_source_eligible_symbols:plan.newly_source_eligible_symbols,new_symbol_examples:Object.values(byCik).flatMap(v=>v.new_symbols.map(symbol=>({symbol,cik:v.cik}))).slice(0,5),excluded:excluded.length,source_snapshot:'2026-10-15',upstream_requests:0};
 }
 if(u.pathname==='/enrichment-ledger'){
  const pin=u.searchParams.get('expected_manifest_sha256');
  if((pin&&!/^[a-f0-9]{64}$/.test(pin))||(u.searchParams.has('part')&&!pin))fail('ENRICHMENT_LEDGER_PIN_REQUIRED');
  const manifest=await read(env.DATA,pin?ENRICH+'ledger-manifests/by-sha256/'+pin+'.json':ENRICH+'ledger-manifest.json',pin);
  const digest=pin||await sha(JSON.stringify(manifest));if(!u.searchParams.has('part'))return {...manifest,manifest_sha256:digest};
  const n=Number(u.searchParams.get('part')),ref=manifest.parts.find(p=>p.batch===n);if(!ref)fail('INVALID_ENRICHMENT_LEDGER_PART');
  return {...await read(env.DATA,ref.key,ref.sha256),ledger_manifest_sha256:digest};
 }
 const pointer=await read(env.DATA,ENRICH+'plan.json'),plan=await read(env.DATA,pointer.key,pointer.sha256);
 if(u.pathname==='/connect/enrichment-ledger-init'){
  const job=await read(env.DATA,ENRICH+'job.json');if(job.plan.sha256!==pointer.sha256)fail('ENRICHMENT_PLAN_CHANGED');
  const parentJob=await read(env.DATA,VAL+'packet-job.json'),assets=await read(env.DATA,VAL+'asset-references.json');
  const assetsRef=await immutable(env,'ledger-asset-references',assets),directoryObject=await env.DATA.get(ENRICH+'sec-directory-index.json'),directoryRef=directoryObject?await directoryObject.json():null;
  const probeObject=await env.DATA.get(ENRICH+'sec-directory-summary.json'),directoryProbe=probeObject?await probeObject.json():null;
  const context=await immutable(env,'ledger-contexts',{run_id:job.run_id,parentJob,assetsRef,directoryRef,directoryProbe});await put(env,ENRICH+'runs/'+job.run_id+'/ledger-context.json',context);return {context,run_id:job.run_id,parent_run_id:parentJob.run_id};
 }
 if(u.pathname==='/connect/enrichment-ledger-batch'){
  const job=await read(env.DATA,ENRICH+'job.json');if(job.plan.sha256!==pointer.sha256)fail('ENRICHMENT_PLAN_CHANGED');
  const n=Number(u.searchParams.get('n'));if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_ENRICHMENT_LEDGER_BATCH');
  const part=await read(env.DATA,FULL+`batches/${n}.json`);if(part.input_sha256!==FULL_PIN)fail('ENRICHMENT_COHORT_PIN');
  const contextRef=await read(env.DATA,ENRICH+'runs/'+job.run_id+'/ledger-context.json'),context=await read(env.DATA,contextRef.key,contextRef.sha256);if(context.run_id!==job.run_id)fail('ENRICHMENT_LEDGER_CONTEXT');
  const assets=await read(env.DATA,context.assetsRef.key,context.assetsRef.sha256),directory=context.directoryRef?await read(env.DATA,context.directoryRef.key,context.directoryRef.sha256):null;
  const rows=await Promise.all(part.rows.map(async original=>{
   const row=await valuationOverlay(env,original,context.parentJob,assets),cik=row.identity.cik;
   const object=eligibleCik(cik)&&plan.ciks.includes(cik)?await env.DATA.get(ENRICH+'runs/'+job.run_id+'/tasks/'+cik+'.json'):null;
   const task=object?await object.json():null;
   const valid=task?.run_id===job.run_id&&task?.http_status===200&&task?.runtime_version===job.runtime_version&&task?.assessed_at===job.assessed_at;
   const packet=valid?task.symbols.find(p=>p.symbol===row.symbol):null;
   const matches=directory?.index[row.symbol]||[];row.current_sec_issuer_reference={status:!directory?(context.directoryProbe?'SEC_DIRECTORY_UNAVAILABLE':'SEC_DIRECTORY_NOT_ASSESSED'):matches.length===1?(matches[0].cik===cik?'CURRENT_SEC_CIK_TICKER_CONFIRMED':'CURRENT_SEC_CIK_CONFLICT'):matches.length>1?'AMBIGUOUS_SEC_DIRECTORY':'NO_CURRENT_SEC_DIRECTORY_MATCH',candidates:matches,source:directory?.source||null,collected_at:directory?.collected_at||context.directoryProbe?.collected_at||null,probe_status:context.directoryProbe?.status||null,historical_share_class_bridge:'NOT_CERTIFIED'};
   const exclusion=plan.excluded.find(p=>p.symbol===row.symbol);
   const state=exclusion?exclusion.reason:!task||task.terminal===false?'CLOUD_ENRICHMENT_PENDING':!valid?'CLOUD_ENRICHMENT_BLOCKED':packet?.eligible?'ACCOUNTING_GATE_PASSED':'ACCOUNTING_GAPS';
   row.source_enrichment={run_id:job.run_id,plan:job.plan,status:state,source_snapshot:plan.source.snapshot_date,assessed_at:job.assessed_at,source_age_days:Math.floor((Date.now()-Date.parse(plan.source.snapshot_date+'T00:00:00Z'))/86400000),source_member:valid?task.source_member:null,annual_accounting:packet||null,recent_capital_claims:valid?{reference:task.recent_claims,period_end:task.recent_claim_period,fields_complete:task.recent_claims_complete,gaps:task.claim_gaps,scope:'SAME_FILING_REPORTED_CLAIMS;WEIGHTED_AVERAGE_SHARES_NOT_SPOT_OR_CLASS_SPECIFIC'}:null,error:!valid&&task?task.error||'ENRICHMENT_CONTEXT_MISMATCH':null,complete_valuation:false};
   return row;
  }));
  const ref=await immutable(env,'ledger-parts',{run_id:job.run_id,context_sha256:contextRef.sha256,input_sha256:FULL_PIN,rows}),states={};for(const r of rows)states[r.source_enrichment.status]=(states[r.source_enrichment.status]||0)+1;
  await put(env,ENRICH+`runs/${job.run_id}/ledger-parts/${n}.json`,{...ref,run_id:job.run_id,symbols:rows.map(r=>r.symbol),states});return {batch:n,accounted:rows.length,states};
 }
 if(u.pathname==='/connect/enrichment-ledger-finish'){
  const job=await read(env.DATA,ENRICH+'job.json');if(job.plan.sha256!==pointer.sha256)fail('ENRICHMENT_PLAN_CHANGED');
  const contextRef=await read(env.DATA,ENRICH+'runs/'+job.run_id+'/ledger-context.json'),context=await read(env.DATA,contextRef.key,contextRef.sha256);if(context.run_id!==job.run_id)fail('ENRICHMENT_LEDGER_CONTEXT');
  const parts=[],symbols=new Set(),states={},identity_states={};
  for(let n=0;n<132;n++){
   const ref=await read(env.DATA,ENRICH+`runs/${job.run_id}/ledger-parts/${n}.json`),part=await read(env.DATA,ref.key,ref.sha256);
   if(ref.run_id!==job.run_id||part.run_id!==job.run_id||part.context_sha256!==contextRef.sha256||part.input_sha256!==FULL_PIN||part.rows.length!==ref.symbols.length)fail('ENRICHMENT_LEDGER_CONTEXT');
   for(const [i,r]of part.rows.entries()){if(r.symbol!==ref.symbols[i]||symbols.has(r.symbol)||!plan.symbols.includes(r.symbol)||r.source_enrichment.run_id!==job.run_id||r.valuation.accounting_rebuild.run_id!==context.parentJob.run_id||r.source_enrichment.complete_valuation!==false)fail('ENRICHMENT_LEDGER_SYMBOL');symbols.add(r.symbol);const identityState=r.current_sec_issuer_reference.status;identity_states[identityState]=(identity_states[identityState]||0)+1;}
   for(const [k,v]of Object.entries(ref.states))states[k]=(states[k]||0)+v;parts.push({batch:n,key:ref.key,sha256:ref.sha256,rows:part.rows.length});
  }
  if(symbols.size!==2629)fail('ENRICHMENT_LEDGER_UNIVERSE');
  const manifest={run_id:job.run_id,context:contextRef,plan:job.plan,input_sha256:FULL_PIN,source:plan.source,accounted:symbols.size,states,identity_states,parts,complete_valuations:0,reconciled_at:new Date().toISOString(),qualification:'SOURCE_AND_ACCOUNTING_ENRICHMENT;IDENTITY_CURRENT_PRICE_CLASS_CAPITAL_AND_RESEARCH_FORECAST_GATES_REMAIN'};
  const ref=await immutable(env,'ledger-manifests',manifest);await put(env,ENRICH+'ledger-manifest.json',manifest);return {...manifest,manifest_sha256:ref.sha256,parts:parts.length};
 }

 if(u.pathname==='/connect/enrichment-sec-directory'){
  const existing=await env.DATA.get(ENRICH+'sec-directory-summary.json');if(existing)return {...await existing.json(),cached:true};
  const url='https://www.sec.gov/files/company_tickers_exchange.json';
  const response=await fetch(url,{headers:{'User-Agent':'Scott Switzer scswitzer@chapman.edu academic-research (Cloudflare data plane)','Accept':'application/json'},signal:AbortSignal.timeout(20000)});
  const collected_at=new Date().toISOString();
  if(!response.ok){await response.body?.cancel();const result={status:'PUBLIC_SEC_DIRECTORY_UNAVAILABLE_FROM_CLOUD',http_status:response.status,url,collected_at,upstream_requests:1};await put(env,ENRICH+'sec-directory-summary.json',result);return result;}
  const reader=response.body.getReader(),chunks=[];let bytes=0;while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.length;if(bytes>4*1048576){await reader.cancel();fail('SEC_DIRECTORY_BYTE_BUDGET');}chunks.push(value);}
  const merged=new Uint8Array(bytes);let offset=0;for(const chunk of chunks){merged.set(chunk,offset);offset+=chunk.length;}const raw=new TextDecoder().decode(merged),data=JSON.parse(raw);
  if(!Array.isArray(data.fields)||!Array.isArray(data.data)||!['cik','ticker','exchange'].every(k=>data.fields.includes(k)))fail('SEC_DIRECTORY_SHAPE');
  const source=await immutable(env,'sec-directories',data),index={};
  for(const values of data.data){const row=Object.fromEntries(data.fields.map((k,i)=>[k,values[i]])),symbol=row.ticker;if(!plan.symbols.includes(symbol))continue;const cik=String(row.cik).padStart(10,'0');if(!eligibleCik(cik))continue;(index[symbol]??=[]).push({cik,exchange:row.exchange,name:row.name||null});}
  const reference=await immutable(env,'sec-directory-indexes',{source,url,collected_at,index,scope:'CURRENT_SEC_ISSUER_TICKER_DIRECTORY;NOT_HISTORICAL_OR_SHARE_CLASS_CERTIFICATION'});
  await put(env,ENRICH+'sec-directory-index.json',reference);const result={status:'CURRENT_SEC_DIRECTORY_CONNECTED',source,reference,url,collected_at,cohort_symbols:Object.keys(index).length,ambiguous_symbols:Object.values(index).filter(v=>v.length!==1).length,upstream_requests:1};await put(env,ENRICH+'sec-directory-summary.json',result);return result;
 }
 if(u.pathname==='/connect/enrichment-canary'){
  const cik=u.searchParams.get('cik');if(!eligibleCik(cik)||!plan.ciks.includes(cik))fail('CIK_OUTSIDE_ENRICHMENT_PLAN');
  const response=await env.PACKET_BUILDER.fetch(new Request(`https://packets.internal/enrich?cik=${cik}&expected_plan_sha256=${pointer.sha256}`,{method:'POST',headers:{Authorization:'Bearer '+env.TOKEN}}));return {...await response.json(),http_status:response.status};
 }
 if(u.pathname==='/connect/enrichment-submit'){
  const contextResponse=await env.PACKET_BUILDER.fetch(new Request('https://packets.internal/context',{headers:{Authorization:'Bearer '+env.TOKEN}}));if(!contextResponse.ok)fail('ENRICHMENT_RUNTIME_UNAVAILABLE');const context=await contextResponse.json();
  const run_id=await sha(JSON.stringify({plan:pointer.sha256,context,submitted_at:new Date().toISOString()})),job={job:JOB,run_id,plan:pointer,...context};
  await put(env,ENRICH+'runs/'+run_id+'/job.json',job);await put(env,ENRICH+'job.json',job);
  for(let i=0;i<plan.ciks.length;i+=100)await env.VALUATION_QUEUE.sendBatch(plan.ciks.slice(i,i+100).map(cik=>({body:{job:JOB,run_id,cik}})));
  return {run_id,issuers_queued:plan.ciks.length,symbols_covered:plan.eligible_symbols,source_snapshot:plan.source.snapshot_date,upstream_requests:0};
 }
 if(u.pathname==='/connect/enrichment-status-batch'){
  const job=await read(env.DATA,ENRICH+'job.json');if(job.plan.sha256!==pointer.sha256)fail('ENRICHMENT_PLAN_CHANGED');
  const n=Number(u.searchParams.get('n'));if(!Number.isInteger(n)||n<0||n>=Math.ceil(plan.ciks.length/100))fail('INVALID_ENRICHMENT_BATCH');
  const counts={run_id:job.run_id,assessed_at:new Date().toISOString(),issuers:0,source_ready:0,source_blocked:0,pending:0,accounting_packets:0,accounting_eligible:0,recent_claims_complete:0,new_source_symbols:0,errors:{},accounting_gaps:{},claim_gaps:{},eligible_symbols:[]};
  await Promise.all(plan.ciks.slice(n*100,n*100+100).map(async cik=>{
   counts.issuers++;const o=await env.DATA.get(ENRICH+'runs/'+job.run_id+'/tasks/'+cik+'.json');if(!o){counts.pending++;return;}const r=await o.json();
   if(r.terminal===false||r.run_id!==job.run_id||(r.http_status===200&&(r.runtime_version!==job.runtime_version||r.assessed_at!==job.assessed_at))){counts.pending++;return;}
   if(r.http_status!==200){counts.source_blocked++;counts.errors[r.error||'ENRICHMENT_FAILED']=(counts.errors[r.error||'ENRICHMENT_FAILED']||0)+1;return;}
   counts.source_ready++;counts.new_source_symbols+=r.new_source_symbols;
   if(r.recent_claims_complete)counts.recent_claims_complete++;
   for(const code of r.claim_gaps)counts.claim_gaps[code]=(counts.claim_gaps[code]||0)+1;
   for(const p of r.symbols){if(p.packet)counts.accounting_packets++;if(p.eligible){counts.accounting_eligible++;counts.eligible_symbols.push(p.symbol);}for(const code of p.gaps)counts.accounting_gaps[code]=(counts.accounting_gaps[code]||0)+1;}
  }));
  await put(env,ENRICH+`runs/${job.run_id}/status/${n}.json`,counts);return counts;
 }
 if(u.pathname==='/connect/enrichment-status'){
  const job=await read(env.DATA,ENRICH+'job.json');if(job.plan.sha256!==pointer.sha256)fail('ENRICHMENT_PLAN_CHANGED');const counts={run_id:job.run_id,plan:job.plan,source_snapshot:plan.source.snapshot_date,accounted:plan.symbols.length,eligible_symbols_in_plan:plan.eligible_symbols,excluded_symbols:plan.excluded.length,issuers:0,source_ready:0,source_blocked:0,pending:0,accounting_packets:0,accounting_eligible:0,recent_claims_complete:0,new_source_symbols:0,errors:{},accounting_gaps:{},claim_gaps:{},eligible_symbols:[],upstream_requests:0,complete_valuations:0};
  for(let n=0;n<Math.ceil(plan.ciks.length/100);n++){
   const part=await read(env.DATA,ENRICH+`runs/${job.run_id}/status/${n}.json`);if(part.run_id!==job.run_id)fail('ENRICHMENT_RUN_CHANGED');
   for(const k of ['issuers','source_ready','source_blocked','pending','accounting_packets','accounting_eligible','recent_claims_complete','new_source_symbols'])counts[k]+=part[k];
   for(const k of ['errors','accounting_gaps','claim_gaps'])for(const [reason,v]of Object.entries(part[k]))counts[k][reason]=(counts[k][reason]||0)+v;counts.eligible_symbols.push(...part.eligible_symbols);
  }
  if(counts.issuers!==plan.ciks.length||counts.source_ready+counts.source_blocked+counts.pending!==counts.issuers)fail('ENRICHMENT_STATUS_ACCOUNTING');
  await put(env,ENRICH+'summary.json',counts);return counts;
 }
 fail('UNKNOWN_ENRICHMENT_ROUTE');
}
export async function enrichmentQueue(batch,env){
 for(const message of batch.messages){
  const b=message.body||{};if(b.job!==JOB||!eligibleCik(b.cik)||!/^[a-f0-9]{64}$/.test(b.run_id||'')){message.ack();continue;}
  const path=ENRICH+'runs/'+b.run_id+'/tasks/'+b.cik+'.json';
  try{
   const job=await read(env.DATA,ENRICH+'runs/'+b.run_id+'/job.json');
   const response=await env.PACKET_BUILDER.fetch(new Request(`https://packets.internal/enrich?cik=${b.cik}&expected_plan_sha256=${job.plan.sha256}`,{method:'POST',headers:{Authorization:'Bearer '+env.TOKEN}}));const r=await response.json();
   if(response.ok&&(r.runtime_version!==job.runtime_version||r.assessed_at!==job.assessed_at))fail('ENRICHMENT_RUNTIME_CHANGED');
   const terminal=response.status<500||message.attempts>=3;await put(env,path,{...r,run_id:b.run_id,http_status:response.status,terminal});
   if(terminal)message.ack();else message.retry({delaySeconds:60});
  }catch{const terminal=message.attempts>=3;await put(env,path,{run_id:b.run_id,cik:b.cik,http_status:503,terminal,error:'ENRICHMENT_TRANSPORT_FAILED'});if(terminal)message.ack();else message.retry({delaySeconds:60});}
 }
}
