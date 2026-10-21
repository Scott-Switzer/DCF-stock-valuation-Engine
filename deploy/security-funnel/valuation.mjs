// Private valuation discovery; missing identity/accounting evidence remains explicit.
import {researchReviews} from './research.mjs';
const BASE='staging/security-funnel/2026-10-20/9beaa712e71650a2/';
const FULL=BASE+'full-history-2026-10-21-v1/';
const FULL_PIN='68db69ad8e4693616d5735b836764e7cd034c45bf9e7a79e483a99bd3163507a';
export const VAL=BASE+'valuation-completion-2026-10-21-v1/';
const enc=new TextEncoder();
const sha=async raw=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',typeof raw==='string'?enc.encode(raw):raw)),x=>x.toString(16).padStart(2,'0')).join('');
const fail=code=>{throw Error(code)};
const JOB='accounting-rebuild-v1';
async function read(env,key,digest=null,max=16*1048576){const obj=await env.DATA.get(key);if(!obj||obj.size>max)fail('VALUATION_SOURCE_UNAVAILABLE');const raw=await obj.text();if(digest&&await sha(raw)!==digest)fail('VALUATION_SOURCE_HASH');return JSON.parse(raw);}
async function put(env,key,value){await env.DATA.put(key,JSON.stringify(value),{httpMetadata:{contentType:'application/json'}});}
export function assetProjection(assets,cohort){
 const index=Object.create(null);
 for(const asset of assets)if(Object.hasOwn(cohort,asset.symbol)){const id=asset.id||asset.asset_id; (index[asset.symbol]??=[]).push({provider_asset_id:/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(id||'')?id:null,symbol:asset.symbol,exchange:asset.exchange||null,asset_class:asset.class||asset.asset_class||null,status:asset.status||null,name:asset.name||null});}
 return index;
}
export async function valuationOverlay(env,row,pinnedJob=null,pinnedAssets=null){
 const pointer=pinnedJob?null:await env.DATA.get(VAL+'packet-job.json');if(!pinnedJob&&!pointer)return row;
 const job=pinnedJob||await pointer.json(),obj=await env.DATA.get(VAL+'runs/'+job.run_id+'/tasks/'+row.symbol+'.json');
 const task=obj?await obj.json():null;
 const fresh=job.assessed_at===new Date().toISOString().slice(0,10);
 const current=task&&task.run_id===job.run_id&&(task.http_status!==200||(task.runtime_version===job.runtime_version&&task.assessed_at===job.assessed_at));
 const state=!job.symbols.includes(row.symbol)?'NO_PREVIOUSLY_COMPLETED_SEC_QUERY':!fresh?'ACCOUNTING_ASSESSMENT_STALE':!current?'CLOUD_REBUILD_PENDING':task.terminal===false?'CLOUD_REBUILD_RETRYING':task.http_status!==200?'CLOUD_REBUILD_BLOCKED':task.input_gate.eligible?'ACCOUNTING_GATE_PASSED':'ACCOUNTING_GAPS';
 const candidateResearch=researchReviews[row.symbol],research=candidateResearch?.cik===(row.identity?.cik||row.cik)?candidateResearch:null;
 const assetObject=pinnedAssets?null:await env.DATA.get(VAL+'asset-references.json'),assets=pinnedAssets||(assetObject?await assetObject.json():null),matches=assets?.index[row.symbol]||[];
 row.current_provider_asset_reference={status:matches.length===1&&matches[0].provider_asset_id?'PROVIDER_ASSET_UUID_CONNECTED_ISSUER_CLASS_LINK_UNVERIFIED':matches.length>1?'AMBIGUOUS_PROVIDER_ASSET':'NO_MATCHED_PROVIDER_ASSET',source:assets?.source||null,candidates:matches,issuer_class_bridge:'NOT_CERTIFIED',historical_identity:'UNCHANGED'};
 row.valuation={...row.valuation,accounting_rebuild:{run_id:job.run_id,assessed_at:job.assessed_at,status:state,...(current?{packet:task.packet,input_gate:task.input_gate,readiness:task.readiness,error:task.error}:{})},model_ready:false,complete_valuation:false,assumptions:{status:'COMPANY_SPECIFIC_RESEARCH_REQUIRED',research},remaining_model_gates:['CURRENT_SECURITY_PRICE_BRIDGE','CURRENT_CAPITAL_CLAIMS','COMPANY_SPECIFIC_CITED_FORECAST','DATED_COMPANY_DISCOUNT_RATE','EXECUTED_DCF']};
 return row;
}
export async function valuationSummary(env){
 const [pointer,obj]=await Promise.all([env.DATA.get(VAL+'packet-job.json'),env.DATA.get(VAL+'packet-summary.json')]);
 if(!pointer||!obj)return null;const job=await pointer.json(),summary=await obj.json();
 return summary.run_id===job.run_id?summary:null;
}
export async function valuationRoute(env,u){
 if(u.pathname==='/connect/valuation-assets'){
  const key='raw/alpaca/assets/continuous-v1/2026-10-20.json',obj=await env.DATA.get(key);
  if(!obj||obj.size!==6491941||obj.etag!=='5a68deb1b22fbce4edbca309ee08ba84')fail('ASSET_REFERENCE_CHANGED');
  const raw=await obj.text(),digest=await sha(raw),data=JSON.parse(raw),assets=Array.isArray(data)?data:data.assets||data.data||[];
  if(!Array.isArray(assets)||!assets.length)return {status:'ASSET_SHAPE_REQUIRES_ADAPTER',fields:Object.keys(data)};
  const cohort=await read(env,FULL+'symbol-batches.json'),index={};
  Object.assign(index,assetProjection(assets,cohort));
  const source={key,sha256:digest,bytes:obj.size,etag:obj.etag,collection_date_from_key:'2026-10-20',stored_at:'2026-10-20T21:11:02Z',provider_observation_timestamp:'NOT_IN_SOURCE_PAYLOAD',scope:'CURRENT_PROVIDER_ASSET_REFERENCE_ONLY;NOT_A_CIK_OR_HISTORICAL_SHARE_CLASS_BRIDGE'};
  await put(env,VAL+'asset-references.json',{source,index});
  const result={source,source_assets:assets.length,cohort_matches:Object.keys(index).length,symbols_with_single_uuid:Object.values(index).filter(a=>a.length===1&&a[0].provider_asset_id).length,distinct_provider_uuids:new Set(Object.values(index).flat().map(a=>a.provider_asset_id).filter(Boolean)).size,ambiguous_symbols:Object.values(index).filter(a=>a.length>1).length,fields:Object.keys(assets[0]),upstream_requests:0};
  await put(env,VAL+'asset-reference-summary.json',result);return result;
 }
 if(u.pathname==='/connect/valuation-ledger-batch'){
  const n=Number(u.searchParams.get('n'));if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_VALUATION_BATCH');
  const job=await read(env,VAL+'packet-job.json'),part=await read(env,FULL+`batches/${n}.json`);
  if(part.input_sha256!==FULL_PIN)fail('PACKET_INPUT_RELEASE_CHANGED');
  const assetObject=await env.DATA.get(VAL+'asset-references.json'),assets=assetObject?await assetObject.json():null;
  const rows=await Promise.all(part.rows.map(row=>valuationOverlay(env,row,job,assets)));
  const value={run_id:job.run_id,input_sha256:FULL_PIN,assessed_at:new Date().toISOString(),rows},raw=JSON.stringify(value),digest=await sha(raw),key=VAL+`runs/${job.run_id}/ledger-parts/by-sha256/${digest}.json`;
  await env.DATA.put(key,raw);const states={};for(const row of rows){const k=row.valuation.accounting_rebuild.status;states[k]=(states[k]||0)+1;}
  const marker={run_id:job.run_id,key,sha256:digest,symbols:rows.map(r=>r.symbol),states};await put(env,VAL+`runs/${job.run_id}/ledger-parts/${n}.json`,marker);
  return {batch:n,accounted:rows.length,states};
 }
 if(u.pathname==='/connect/valuation-ledger-finish'){
  const job=await read(env,VAL+'packet-job.json'),cohort=await read(env,FULL+'symbol-batches.json'),symbols=new Set(),parts=[],states={};
  for(let n=0;n<132;n++){
   const part=await read(env,VAL+`runs/${job.run_id}/ledger-parts/${n}.json`);if(part.run_id!==job.run_id)fail('LEDGER_RUN_CHANGED');
   const data=await read(env,part.key,part.sha256);
   if(data.run_id!==job.run_id||data.input_sha256!==FULL_PIN||data.rows.length!==part.symbols.length||data.rows.some((r,i)=>r.symbol!==part.symbols[i]||!Object.hasOwn(cohort,r.symbol)||r.valuation.complete_valuation!==false))fail('LEDGER_PART_CONTEXT');
   for(const s of part.symbols){if(symbols.has(s))fail('DUPLICATE_LEDGER_SYMBOL');symbols.add(s);}
   for(const [k,v]of Object.entries(part.states))states[k]=(states[k]||0)+v;parts.push({batch:n,key:part.key,sha256:part.sha256,rows:part.symbols.length});
  }
  if(symbols.size!==2629)fail('VALUATION_LEDGER_UNIVERSE');
  const assetObject=await env.DATA.get(VAL+'asset-reference-summary.json');
  const result={run_id:job.run_id,input_sha256:FULL_PIN,accounted:symbols.size,complete_valuations:0,states,parts,provider_asset_references:assetObject?await assetObject.json():null,reconciled_at:new Date().toISOString(),qualification:'ACCOUNTING_AND_RESEARCH_READINESS_ONLY;IDENTITY_FORECAST_CAPITAL_COST_AND_MODEL_RUN_GATES_REMAIN'};
  const digest=await sha(JSON.stringify(result));await put(env,VAL+'ledger-manifests/by-sha256/'+digest+'.json',result);
  await put(env,VAL+'ledger-manifest.json',result);return {...result,manifest_sha256:digest,parts:parts.length};
 }
 if(u.pathname==='/valuation-ledger'){
  const pin=u.searchParams.get('expected_manifest_sha256');
  if(u.searchParams.has('part')&&!/^[a-f0-9]{64}$/.test(pin||''))fail('LEDGER_PAGINATION_REQUIRES_MANIFEST_PIN');
  if(pin&&!/^[a-f0-9]{64}$/.test(pin))fail('INVALID_LEDGER_MANIFEST_PIN');
  const manifest=await read(env,pin?VAL+'ledger-manifests/by-sha256/'+pin+'.json':VAL+'ledger-manifest.json',pin);
  const digest=pin||await sha(JSON.stringify(manifest));if(!u.searchParams.has('part'))return {...manifest,manifest_sha256:digest};
  const n=Number(u.searchParams.get('part')),ref=manifest.parts.find(r=>r.batch===n);if(!ref)fail('INVALID_LEDGER_PART');
  const part=await read(env,ref.key,ref.sha256);return {...part,ledger_manifest_sha256:digest,pagination:{next:n<131?{part:n+1,expected_manifest_sha256:digest}:null}};
 }
 if(u.pathname==='/connect/valuation-packet-submit'){
  const plan=await valuationRoute(env,new URL('https://internal/connect/valuation-packet-plan'));
  const response=await env.PACKET_BUILDER.fetch(new Request('https://packets.internal/context',{headers:{Authorization:'Bearer '+env.TOKEN}}));
  if(!response.ok)fail('PACKET_CONTEXT_UNAVAILABLE');const context=await response.json();
  if(!/^[a-f0-9]{64}$/.test(context.runtime_version||'')||!/^\d{4}-\d{2}-\d{2}$/.test(context.assessed_at||''))fail('PACKET_CONTEXT_INVALID');
  const submitted_at=new Date().toISOString(),run_id=await sha(JSON.stringify({job:JOB,submitted_at,context,symbols:plan.symbols}));
  const job={job:JOB,run_id,submitted_at,input_sha256:FULL_PIN,...context,symbols:plan.symbols,expected:plan.eligible};
  await put(env,VAL+'runs/'+run_id+'/job.json',job);await put(env,VAL+'packet-job.json',job);
  for(let i=0;i<plan.symbols.length;i+=100)await env.VALUATION_QUEUE.sendBatch(plan.symbols.slice(i,i+100).map(symbol=>({body:{job:JOB,run_id,symbol}})));
  return {job:JOB,run_id,submitted:plan.eligible,cloud_execution:true,upstream_requests:0};
 }
 if(u.pathname==='/connect/valuation-packet-status-batch'){
  const job=await read(env,VAL+'packet-job.json'),counts={expected:job.expected,completed:0,failed:0,pending:0,input_complete:0,policy_valid:0,data_evaluable:0,gaps:{}},eligible=[];
  const n=Number(u.searchParams.get('n'));if(!Number.isInteger(n)||n<0||n>=Math.ceil(job.symbols.length/100))fail('INVALID_PACKET_STATUS_BATCH');
  counts.expected=job.symbols.slice(n*100,n*100+100).length;
  await Promise.all(job.symbols.slice(n*100,n*100+100).map(async symbol=>{
   const obj=await env.DATA.get(VAL+'runs/'+job.run_id+'/tasks/'+symbol+'.json');if(!obj){counts.pending++;return;}
   const r=await obj.json();if(r.terminal===false||r.run_id!==job.run_id||(r.http_status===200&&(r.runtime_version!==job.runtime_version||r.assessed_at!==job.assessed_at))){counts.pending++;return;}if(r.http_status!==200){counts.failed++;const code=r.error||'PACKET_FAILED';counts.gaps[code]=(counts.gaps[code]||0)+1;return;}
   counts.completed++;if(r.input_gate.eligible)counts.input_complete++;if(r.readiness.states.POLICY_VALID)counts.policy_valid++;if(r.readiness.valuation_ready){counts.data_evaluable++;eligible.push(symbol);}
   for(const code of r.input_gate.reason_codes)counts.gaps[code]=(counts.gaps[code]||0)+1;
  }));
  await put(env,VAL+`runs/${job.run_id}/packet-status/${n}.json`,{...counts,eligible,run_id:job.run_id,assessed_at:new Date().toISOString()});return {...counts,eligible};
 }
 if(u.pathname==='/connect/valuation-packet-status'){
  const job=await read(env,VAL+'packet-job.json'),counts={run_id:job.run_id,runtime_version:job.runtime_version,assessed_at:job.assessed_at,expected:job.expected,completed:0,failed:0,pending:0,input_complete:0,policy_valid:0,data_evaluable:0,gaps:{},eligible:[],status_assessments:[]};
  for(let n=0;n<Math.ceil(job.expected/100);n++){
   const part=await read(env,VAL+`runs/${job.run_id}/packet-status/${n}.json`);if(part.run_id!==job.run_id)fail('PACKET_STATUS_RUN_CHANGED');for(const k of ['completed','failed','pending','input_complete','policy_valid','data_evaluable'])counts[k]+=part[k];
   for(const [k,v]of Object.entries(part.gaps))counts.gaps[k]=(counts.gaps[k]||0)+v;counts.eligible.push(...part.eligible);counts.status_assessments.push(part.assessed_at);
  }
  if(counts.completed+counts.failed+counts.pending!==counts.expected)fail('PACKET_STATUS_ACCOUNTING');
  await put(env,VAL+'packet-summary.json',counts);return counts;
 }
 if(u.pathname==='/connect/valuation-packet-plan'){
  const symbols=[];
  for(let n=0;n<132;n++){
   const b=await read(env,FULL+`batches/${n}.json`);
   if(b.input_sha256!==FULL_PIN)fail('PACKET_INPUT_RELEASE_CHANGED');
   for(const r of b.rows)if(r.financials.cloud?.query_fingerprint)symbols.push(r.symbol);
  }
  if(new Set(symbols).size!==symbols.length)fail('DUPLICATE_PACKET_SYMBOL');
  return {symbols,accounted:2629,eligible:symbols.length,source_cutoff:'2026-09-24'};
 }
 if(u.pathname==='/connect/valuation-packet'){
  const symbol=u.searchParams.get('symbol')||'';
  if(!/^[A-Z0-9][A-Z0-9.-]{0,24}$/.test(symbol))fail('INVALID_SYMBOL');
  const response=await env.PACKET_BUILDER.fetch(new Request('https://packets.internal/packet?symbol='+encodeURIComponent(symbol),{method:'POST',headers:{Authorization:'Bearer '+env.TOKEN}}));
  const result=await response.json();
  return {...result,http_status:response.status};
 }
 if(u.pathname==='/connect/valuation-discover'){
  const universe=await read(env,'evidence/us-security-universe-coverage-v1/canonical_universe_v2.json','f603027061256d8eb1b9cf9bd61a011a76bdc97065d96c10f2a79dadc27902e9');
  const cohort=await read(env,FULL+'symbol-batches.json'),all=universe.securities;
  if(!Array.isArray(all)||all.length!==13156)fail('VALUATION_UNIVERSE_CONTEXT');
  const selected=all.filter(r=>[r.display_ticker,r.ticker,r.symbol].some(s=>s in cohort));
  await put(env,VAL+'canonical-reference.json',{source_sha256:'f603027061256d8eb1b9cf9bd61a011a76bdc97065d96c10f2a79dadc27902e9',generated_at:universe.built_at,reference_snapshots:universe.reference_snapshots,rows:selected});
  const result={universe_fields:Object.keys(universe),security_fields:Object.keys(all[0]),cohort_reference_rows:selected.length,identity_kinds:{},with_cik:0,with_figi:0,with_provider_asset_id:0};
  for(const r of selected){const kind=r.id_kind||r.security_id_kind||r.security_id_type||'UNSPECIFIED';result.identity_kinds[kind]=(result.identity_kinds[kind]||0)+1;if(r.cik)result.with_cik++;if(r.figi||r.composite_figi)result.with_figi++;if(r.alpaca_asset_id||r.provider_asset_id)result.with_provider_asset_id++;}
  await put(env,VAL+'discovery.json',result);return result;
 }
 if(u.pathname==='/connect/valuation-audit-batch'){
  const n=Number(u.searchParams.get('n'));if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_VALUATION_BATCH');
  const b=await read(env,FULL+`batches/${n}.json`),rows=[];
  const canonical=await read(env,VAL+'canonical-reference.json'),bySymbol=Object.fromEntries(canonical.rows.map(r=>[r.display_ticker,r]));
  for(const r of b.rows){
   const c=bySymbol[r.symbol],ref=r.valuation.packet,missing=[];
   const out={symbol:r.symbol,cik:r.identity.cik,packet_status:ref.status,reference_identity:{cik_matches:!!c?.cik&&c.cik===r.identity.cik,id_kind:c?.id_kind||null,instrument_type:c?.instrument_type||null,listing_status:c?.listing_status||null,reference_built_at:canonical.generated_at,current_quote_target_matches:c?.security_id===r.recent_prices.source_security_id},missing};
   if(ref.status==='SOURCE_PACKET_VERIFIED'){
    const p=await read(env,ref.key,ref.sha256,131072);
    if(p.cik!==r.identity.cik||p.ticker!==r.symbol)fail('VALUATION_PACKET_IDENTITY_CHANGED');
    if(p.historical.length!==3)missing.push('THREE_ANNUAL_PERIODS_REQUIRED');
    const common=new Set((p.common_income||[]).map(v=>v.period_end));
    for(const h of p.historical){for(const f of ['revenue','ebit','capex','d_and_a','nwc','book_value','tax_rate'])if(h.fields[f]===null||h.fields[f]===undefined)missing.push('MISSING_'+f.toUpperCase());if(!common.has(h.period_end))missing.push('COMMON_SHAREHOLDER_INCOME_REQUIRED');}
    for(const f of ['short_term_debt','long_term_debt','cash','preferred_equity','minority_interest'])if(!p.bridge?.[f])missing.push('MISSING_BRIDGE_'+f.toUpperCase());
    if(!p.diluted_shares||!(p.diluted_shares.value>0))missing.push('DILUTED_SHARE_BASIS_REQUIRED');
    if(!p.adjustment_facts?.facts||p.adjustment_facts.conflicts?.length)missing.push('ACCOUNTING_ADJUSTMENT_EVIDENCE_REQUIRED');
    out.annual_periods=p.historical.map(h=>h.period_end);out.source_packet={key:ref.key,sha256:ref.sha256};
   }else missing.push('NO_VERIFIED_METHOD_PACKET');
   out.missing=[...new Set(missing)];out.accounting_status=out.missing.length?'ACCOUNTING_GAPS':'ACCOUNTING_FIELDS_PRESENT_REQUIRES_MODEL_VALIDATION';rows.push(out);
  }
  await put(env,VAL+`audit/${n}.json`,{input_sha256:b.input_sha256,rows});
  return {batch:n,securities:rows.length,method_packets:rows.filter(r=>r.packet_status==='SOURCE_PACKET_VERIFIED').length,accounting_complete:rows.filter(r=>!r.missing.length).length};
 }
 if(u.pathname==='/connect/valuation-audit-finish'){
  const counts={accounted:0,method_packets:0,accounting_complete:0,identity_kinds:{},accounting_gaps:{}},ready=[];
  for(let n=0;n<132;n++){const part=await read(env,VAL+`audit/${n}.json`);for(const r of part.rows){counts.accounted++;if(r.packet_status==='SOURCE_PACKET_VERIFIED')counts.method_packets++;if(!r.missing.length){counts.accounting_complete++;ready.push(r);}for(const reason of r.missing)counts.accounting_gaps[reason]=(counts.accounting_gaps[reason]||0)+1;const kind=r.reference_identity.id_kind||'UNKNOWN';counts.identity_kinds[kind]=(counts.identity_kinds[kind]||0)+1;}}
  if(counts.accounted!==2629)fail('VALUATION_AUDIT_UNIVERSE');await put(env,VAL+'accounting-candidates.json',ready);await put(env,VAL+'audit-summary.json',counts);return counts;
 }
 fail('UNKNOWN_VALUATION_ROUTE');
}
export async function valuationQueue(batch,env){
 if(batch.queue!=='dcf-valuation-packets-staging')fail('UNKNOWN_PACKET_QUEUE');
 for(const message of batch.messages){
  const body=message.body||{};
  if(body.job!==JOB||!/^[a-f0-9]{64}$/.test(body.run_id||'')||!/^[A-Z0-9][A-Z0-9.-]{0,24}$/.test(body.symbol||'')){message.ack();continue;}
  try{
   const job=await read(env,VAL+'runs/'+body.run_id+'/job.json');
   if(!job.symbols.includes(body.symbol))fail('PACKET_SYMBOL_OUTSIDE_JOB');
   const r=await valuationRoute(env,new URL('https://internal/connect/valuation-packet?symbol='+encodeURIComponent(body.symbol)));
   if(r.http_status===200&&(r.runtime_version!==job.runtime_version||r.assessed_at!==job.assessed_at))fail('PACKET_RUNTIME_CHANGED');
   r.run_id=body.run_id;
   r.terminal=r.http_status<500||message.attempts>=3;
   await put(env,VAL+'runs/'+body.run_id+'/tasks/'+body.symbol+'.json',r);
   if(r.http_status>=500&&message.attempts<3)message.retry({delaySeconds:60});else message.ack();
  }catch{
   await put(env,VAL+'runs/'+body.run_id+'/tasks/'+body.symbol+'.json',{run_id:body.run_id,symbol:body.symbol,http_status:503,terminal:message.attempts>=3,error:'PACKET_TRANSPORT_FAILED'});
   if(message.attempts<3)message.retry({delaySeconds:60});else message.ack();
  }
 }
}
