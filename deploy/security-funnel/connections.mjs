// Consume existing materializations, never raw provider archives. Owner-only routes.
import {parquetMetadataAsync, parquetRead} from 'hyparquet';
import {decompress} from 'fzstd';
const BASE='staging/security-funnel/2026-10-20/9beaa712e71650a2/';
const OLD=BASE+'reconciled-2026-10-21-v1/';
export const CONNECTED=BASE+'connected-2026-10-21-v1/';
const ASOF='2026-10-21';
const enc=new TextEncoder();
const fail=s=>{throw new Error(s);};
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const sha=async b=>hex(await crypto.subtle.digest('SHA-256',typeof b==='string'?enc.encode(b):b));
const safe=v=>typeof v==='bigint'?v.toString():v instanceof Date?v.toISOString().slice(0,10):v;
async function put(env,key,v){await env.DATA.put(key,JSON.stringify(v,(_,v)=>safe(v)),{httpMetadata:{contentType:'application/json'}});}
async function json(bucket,key,digest=null,max=16*1048576){
 const o=await bucket.get(key);if(!o||o.size>max)fail('CONNECTION_OBJECT_UNAVAILABLE');
 const raw=await o.text();if(digest&&await sha(raw)!==digest)fail('CONNECTION_HASH_MISMATCH');return JSON.parse(raw);
}
export async function openMaterialized(env,ref){
 if(!ref.key.startsWith('research/financial-research-canonical-v1/')||!ref.key.endsWith('.parquet'))fail('UNAPPROVED_MATERIALIZED_OBJECT');
 const o=await env.RESEARCH.get(ref.key);if(!o||o.size!==ref.bytes||o.size>64*1048576)fail('MATERIALIZED_OBJECT_SIZE');
 const file=await o.arrayBuffer();if(await sha(file)!==ref.sha256)fail('MATERIALIZED_OBJECT_HASH');
 const metadata=await parquetMetadataAsync(file);if(Number(metadata.num_rows)!==ref.rows)fail('MATERIALIZED_ROW_COUNT');
 const options={file,metadata,compressors:{ZSTD:(input,size)=>decompress(input,new Uint8Array(size))},parsers:{dateFromDays:days=>new Date(days*86400000).toISOString().slice(0,10)}};
 return {column:async name=>{
  const values=[];
  await parquetRead({...options,columns:[name],onChunk:chunk=>{
   for(let i=0;i<chunk.columnData.length;i++)values[chunk.rowStart+i]=chunk.columnData[i];
  }});
  if(values.length!==ref.rows)fail('PARQUET_COLUMN_ROW_COUNT');return values;
 }};
}
async function selectedRows(env,ref,key,targets,columns){
 const p=await openMaterialized(env,ref),ids=await p.column(key),positions=[];
 for(let i=0;i<ids.length;i++)if(targets.has(String(ids[i])))positions.push(i);
 const out=positions.map(i=>({[key]:safe(ids[i])}));
 for(const name of columns){const values=await p.column(name);for(let j=0;j<positions.length;j++)out[j][name]=safe(values[positions[j]]);}
 return out;
}
function active(a,date){return a.effective_from&&a.effective_to&&a.effective_from<=date&&date<=a.effective_to;}
function uniq(xs){return [...new Set(xs)];}
export function sourceFreshness(date){
 const t=typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)?Date.parse(date+'T00:00:00Z'):NaN;
 if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==date)return {status:'UNKNOWN_OR_INVALID',observed_through:date||null,policy_max_age_days:7};
 const age=(Date.parse(ASOF+'T00:00:00Z')-t)/86400000;
 return {status:age<0?'FUTURE':age>7?'STALE':'WITHIN_POLICY',observed_through:date,age_days:age,policy_max_age_days:7};
}
async function plan(env){return json(env.DATA,CONNECTED+'plan.json');}
async function init(env){
 const pins=await json(env.DATA,BASE+'connection-sources.json',env.CONNECTION_SOURCES_SHA256);
 const prices=await json(env.RESEARCH,pins.prices.key,pins.prices.sha256);
 const identity=await json(env.RESEARCH,pins.identity.key,pins.identity.sha256);
 const links=await json(env.RESEARCH,pins.issuer_links.key,pins.issuer_links.sha256);
 if(prices.policy_version!=='crsp-ciz-research-v1'||prices.rows!==110245749)fail('PRICE_POLICY_OR_UNIVERSE_CHANGED');
 const ledger=await json(env.DATA,OLD+'ledger.json');
 if(ledger.securities.length!==2629||new Set(ledger.securities.map(r=>r.symbol)).size!==2629)fail('CONNECTION_SOURCE_UNIVERSE_CHANGED');
 const targetCiks=new Set(ledger.securities.map(r=>r.identity.cik).filter(Boolean));
 const targetPermnos=new Set(ledger.securities.flatMap(r=>r.identity.crsp_candidates||[]).map(r=>String(r.permno)));
 const headerRows=[],ccmRows=[],datedRows=[];
 for(const ref of links.objects){
  if(ref.kind==='issuer_cik_headers')headerRows.push(...await selectedRows(env,ref,'cik',targetCiks,['gvkey','evidence_status','source_manifest_sha256','source_object_sha256']));
  if(ref.kind==='dated_cik')datedRows.push(...await selectedRows(env,ref,'identifier_value',targetCiks,['permno','effective_from','effective_to','assertion_id','endpoint_policy','source_manifest_sha256']));
 }
 // Include native issuer associations beyond old ticker candidates. Preserve dates/ambiguity.
 const gvkeys=new Set(headerRows.map(r=>r.gvkey));
 for(const ref of links.objects)if(ref.kind==='ccm')ccmRows.push(...await selectedRows(env,ref,'gvkey',gvkeys,
  ['permno','effective_from','effective_to','eligible','link_scope','link_type','link_prim','assertion_id','primary_issue','source_manifest_sha256']));
 for(const r of [...ccmRows,...datedRows])if(r.permno)targetPermnos.add(String(r.permno));
 const inputHash=await sha(JSON.stringify({pins,ledger_pin:ledger.summary.effective_input_sha256,asof:ASOF,version:'native-connect-v1'}));
 const old=await env.DATA.get(CONNECTED+'plan.json');if(old&&(await old.json()).input_sha256!==inputHash)fail('CONNECTION_INPUT_CHANGED');
 await put(env,CONNECTED+'issuer-links.json',{headers:headerRows,ccm:ccmRows,dated:datedRows});
 await put(env,CONNECTED+'price-parts.json',prices.objects);
 await put(env,CONNECTED+'identity-parts.json',identity.objects.filter(r=>r.kind==='assertions'));
 const daily=pins.daily_pointer;
 if(!/^gold\/daily-prices\/releases\/[a-f0-9]{64}\/data.json$/.test(daily.data_key))fail('INVALID_DAILY_REFERENCE');
 const bars=await json(env.DATA,daily.data_key,daily.sha256,8*1048576);
 const recent={};
 const universe=new Set(ledger.securities.map(r=>r.symbol));
 for(const b of bars.bars||[]){const symbol=b.provider_symbol||b.symbol;if(universe.has(symbol)){
  if(recent[symbol]||!b.security_id||b.session_date!==daily.session||!Number.isFinite(b.close)||b.close<=0)fail('RECENT_BAR_IDENTITY_OR_VALUE_CONFLICT');
  recent[symbol]={
  symbol,source_security_id:b.security_id,session:b.session_date,close:b.close,provider:'alpaca',feed:daily.feed,
  source_key:daily.data_key,source_sha256:daily.sha256,price_basis:'SOURCE_DAILY_BAR',
  qualification:'SOURCE_NATIVE;NOT_A_CIK_OR_CRSP_IDENTITY_JOIN'};}}
 await put(env,CONNECTED+'recent-prices.json',recent);
 const result={input_sha256:inputHash,pins,asof:ASOF,securities:2629,permnos:[...targetPermnos],
  price_parts:prices.objects.length,identity_parts:identity.objects.filter(r=>r.kind==='assertions').length,
  ledger_batches:132,recent_source_symbols:Object.keys(recent).length,price_policy:prices.policy_version,
  source_adjustment_base:'SOURCE_LAST_TRADING_DAY_RETROSPECTIVE;NOT_PIT_QUOTE',
  dated_cik_assertions_selected:datedRows.length,current_cik_header_associations:headerRows.length};
 await put(env,CONNECTED+'plan.json',result);return {...result,permnos:result.permnos.length};
}
async function identityPart(env,n){
 const p=await plan(env),refs=await json(env.DATA,CONNECTED+'identity-parts.json');
 if(!Number.isInteger(n)||!refs[n])fail('INVALID_IDENTITY_PART');
 const key=CONNECTED+`identity/${n}.json`,done=await env.DATA.get(key);if(done){const d=await done.json();if(d.input_sha256!==p.input_sha256)fail('IDENTITY_CHECKPOINT_CHANGED');return {part:n,reused:true};}
 const wanted=new Set(p.permnos);const rows=await selectedRows(env,refs[n],'permno',wanted,
  ['identifier_type','identifier_value','effective_from','effective_to','evidence_status','assertion_id']);
 const byPermno={};
 for(const r of rows)if(r.evidence_status==='NATIVE_DATED_EVIDENCE'){
  (byPermno[r.permno]??=[]).push(r);
 }
 await put(env,key,{input_sha256:p.input_sha256,source:refs[n],securities:byPermno});
 return {part:n,native_securities:Object.keys(byPermno).length};
}
async function pricePart(env,n){
 const p=await plan(env),refs=await json(env.DATA,CONNECTED+'price-parts.json');
 if(!Number.isInteger(n)||!refs[n])fail('INVALID_PRICE_PART');
 const key=CONNECTED+`prices/${n}.json`,done=await env.DATA.get(key);if(done){if((await done.json()).input_sha256!==p.input_sha256)fail('PRICE_CHECKPOINT_CHANGED');return {part:n,reused:true};}
 const wanted=new Set(p.permnos),source=await openMaterialized(env,refs[n]),ids=await source.column('permno'),positions=[],summary={};
 for(let i=0;i<ids.length;i++)if(wanted.has(String(ids[i]))){positions.push(i);const id=String(ids[i]);summary[id]??={permno:Number(id),rows:0,split_adjusted_rows:0,distribution_adjusted_rows:0,missing_factor_rows:0,date_min:null,date_max:null};summary[id].rows++;}
 if(positions.length){
  const last={};const dates=await source.column('dlycaldt');
  for(const i of positions){const id=String(ids[i]),day=String(safe(dates[i])).slice(0,10),r=summary[id];
   if(!/^\d{4}-\d{2}-\d{2}$/.test(day))fail('INVALID_MATERIALIZED_PRICE_DATE');
   if(!r.date_min||day<r.date_min)r.date_min=day;
   if(!r.date_max||day>r.date_max){r.date_max=day;last[id]=i;}
  }
  for(const [field,count]of [['split_adjusted_price','split_adjusted_rows'],['distribution_adjusted_price','distribution_adjusted_rows']]){
   const values=await source.column(field);
   for(const i of positions){const id=String(ids[i]),v=values[i];if(typeof v==='number'&&Number.isFinite(v)&&v>0)summary[id][count]++;
    if(last[id]===i)summary[id]['latest_'+field]=v==null?null:String(v);}
  }
  const missing=await source.column('missing_adjustment_factors');for(const i of positions)if(missing[i])summary[String(ids[i])].missing_factor_rows++;
 }
 await put(env,key,{input_sha256:p.input_sha256,source_sha256:refs[n].sha256,rows:refs[n].rows,securities:summary});
 return {part:n,selected_rows:positions.length,securities:Object.keys(summary).length};
}
async function priceIndex(env){
 const p=await plan(env),all={},refs=await json(env.DATA,CONNECTED+'price-parts.json');let rows=0;
 for(let n=0;n<p.price_parts;n++){
  const d=await json(env.DATA,CONNECTED+`prices/${n}.json`);if(d.input_sha256!==p.input_sha256||d.source_sha256!==refs[n].sha256||d.rows!==refs[n].rows)fail('PRICE_INDEX_PIN_CHANGED');rows+=d.rows;
  for(const [id,r]of Object.entries(d.securities)){
   const sourceObject={key:refs[n].key,sha256:refs[n].sha256,permno:r.permno,date:r.date_max};
   if(!all[id]){all[id]={...r,latest_source_object:sourceObject};continue;}const a=all[id];
   for(const field of ['rows','split_adjusted_rows','distribution_adjusted_rows','missing_factor_rows'])a[field]+=r[field];
   if(r.date_min<a.date_min)a.date_min=r.date_min;
   if(r.date_max===a.date_max&&(r.latest_split_adjusted_price!==a.latest_split_adjusted_price||r.latest_distribution_adjusted_price!==a.latest_distribution_adjusted_price))a.latest_adjusted_price_conflict=true;
   if(r.date_max>a.date_max){a.date_max=r.date_max;a.latest_split_adjusted_price=r.latest_split_adjusted_price;a.latest_distribution_adjusted_price=r.latest_distribution_adjusted_price;a.latest_source_object=sourceObject;a.latest_adjusted_price_conflict=false;}
  }
 }
 if(rows!==110245749)fail('PRICE_INDEX_ACCOUNTING_FAILED');
 await put(env,CONNECTED+'price-index.json',{input_sha256:p.input_sha256,index_version:'native-price-index-v2',source_rows_checked:rows,securities:all});
 return {source_rows_checked:rows,native_securities:Object.keys(all).length};
}
async function connectBatch(env,n){
 const p=await plan(env);if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_CONNECTION_BATCH');
 const key=CONNECTED+`batches/${n}.json`,done=await env.DATA.get(key);if(done){const d=await done.json();if(d.input_sha256!==p.input_sha256)fail('CONNECTED_CHECKPOINT_CHANGED');if(d.connection_version==='native-connected-v2')return {batch:n,reused:true};}
 const batch=await json(env.DATA,OLD+`batches/${n}.json`),briefs=await json(env.DATA,OLD+`briefs/${n}.json`);
 const links=await json(env.DATA,CONNECTED+'issuer-links.json'),recent=await json(env.DATA,CONNECTED+'recent-prices.json');
 const prices=await json(env.DATA,CONNECTED+'price-index.json');if(prices.input_sha256!==p.input_sha256||prices.index_version!=='native-price-index-v2')fail('CONNECTED_PRICE_PIN_CHANGED');
 const identityRefs=await json(env.DATA,CONNECTED+'identity-parts.json'),cache={};
 const batchCiks=new Set(batch.rows.map(r=>r.identity.cik));
 const batchGvkeys=new Set(links.headers.filter(r=>batchCiks.has(r.cik)).map(r=>r.gvkey));
 const neededIds=new Set(batch.rows.flatMap(r=>(r.identity.crsp_candidates||[]).map(c=>String(c.permno))));
 for(const r of links.ccm)if(batchGvkeys.has(r.gvkey)&&r.permno)neededIds.add(String(r.permno));
 for(const r of links.dated)if(batchCiks.has(r.identifier_value)&&r.permno)neededIds.add(String(r.permno));
 async function native(id){const bucket=Number(id)%32;let found=cache[bucket];if(!found){
   const ix=identityRefs.findIndex(r=>r.key.includes(`bucket=${String(bucket).padStart(2,'0')}/`));if(ix<0)return [];
   const d=await json(env.DATA,CONNECTED+`identity/${ix}.json`);if(d.input_sha256!==p.input_sha256)fail('CONNECTED_IDENTITY_PIN_CHANGED');
   found={};for(const id of neededIds)if(d.securities[id])found[id]=d.securities[id];cache[bucket]=found;}
   return found[String(id)]||[];}
 for(const row of batch.rows){
  const cik=row.identity.cik,headers=links.headers.filter(r=>r.cik===cik),gvkeys=new Set(headers.map(r=>r.gvkey));
  const currentAssociations=links.ccm.filter(r=>r.eligible&&r.link_scope==='ISSUER_SECURITY'&&gvkeys.has(r.gvkey));
  const dated=links.dated.filter(r=>r.identifier_value===cik);
  const candidates=uniq([...(row.identity.crsp_candidates||[]).map(c=>String(c.permno)),...currentAssociations.map(r=>String(r.permno)),...dated.map(r=>String(r.permno))]);
  const connected=[];
  for(const id of candidates){
   const evidence=await native(id),history=prices.securities[id];
   const intervals=evidence.filter(a=>['TICKER','TRADING_SYMBOL'].includes(a.identifier_type)&&a.identifier_value===row.symbol);
   if(!intervals.length&&!dated.some(a=>String(a.permno)===id))continue;
   const at=history?.date_max;
   const datedLinks=dated.filter(a=>String(a.permno)===id&&at&&active(a,at));
   const identifiers=at?evidence.filter(a=>active(a,at)):[],groups={};
   for(const a of identifiers)(groups[a.identifier_type]??=new Set()).add(a.identifier_value);
   const conflicts=Object.entries(groups).filter(([,values])=>values.size>1).map(([identifier_type,values])=>({identifier_type,values:[...values]}));
   connected.push({permno:Number(id),security_id:'CRSP:PERMNO:'+id,
    ticker_intervals:intervals,latest_source_date:at||null,
    latest_date_symbol_supported:!!at&&intervals.some(a=>active(a,at)),
    dated_cik_links:datedLinks,all_dated_cik_links:dated.filter(a=>String(a.permno)===id),issuer_associations:currentAssociations.filter(a=>String(a.permno)===id),
    cik_header_validity:'UNDATED_SOURCE_HEADER;NOT_HISTORICAL_CIK_VALIDITY',
    native_identity_conflicts_at_latest:conflicts,
    identifiers_at_latest:at?evidence.filter(a=>active(a,at)&&['CUSIP','CUSIP9','SECURITY_TYPE','SHARE_TYPE'].includes(a.identifier_type)):[],
    adjusted_history:history||null});
  }
  const nativeMatches=connected.filter(c=>c.adjusted_history&&c.ticker_intervals.some(a=>
   a.effective_from<=c.adjusted_history.date_max&&a.effective_to>=c.adjusted_history.date_min));
  const datedMatches=nativeMatches.filter(c=>c.dated_cik_links.length);
  const currentMatches=nativeMatches.filter(c=>c.issuer_associations.some(a=>active(a,c.latest_source_date)));
  row.identity.connections={status:nativeMatches.some(c=>c.native_identity_conflicts_at_latest.length)?'CONFLICTING_NATIVE_IDENTITY_EVIDENCE':datedMatches.length===1?'EFFECTIVE_DATED_ISSUER_LINK_CONNECTED':
   currentMatches.length===1?'NATIVE_ISSUER_ASSOCIATION_CONNECTED':nativeMatches.length===1?'NATIVE_DATED_SECURITY_CONNECTED':
   nativeMatches.length?'AMBIGUOUS_NATIVE_SECURITIES':'NO_MATCHED_NATIVE_SECURITY',candidates:connected,
   public_availability:'NOT_ESTABLISHED',cross_provider_identity:'NOT_CERTIFIED',
   boundary_policy:'EXISTING_DATED_CIK_LINKS_USE_PROVISIONAL_INCLUSIVE_ENDPOINTS'};
  row.recent_prices=recent[row.symbol]||{status:'NO_RECENT_PUBLISHED_BAR'};
  if(recent[row.symbol]){
   row.recent_prices.freshness=sourceFreshness(row.recent_prices.session);
   row.recent_prices.status=row.recent_prices.freshness.status==='WITHIN_POLICY'?'RECENT_SOURCE_PRICE_CONNECTED':'SOURCE_PRICE_'+row.recent_prices.freshness.status;
   if(!row.valuation.blockers.includes('RECENT_PRICE_ISSUER_JOIN_REQUIRED'))row.valuation.blockers.push('RECENT_PRICE_ISSUER_JOIN_REQUIRED');
  }
  const usable=nativeMatches.filter(c=>c.adjusted_history.split_adjusted_rows>0&&c.adjusted_history.distribution_adjusted_rows>0&&!c.adjusted_history.latest_adjusted_price_conflict);
  row.adjusted_prices.connections={status:nativeMatches.length===1&&usable.length===1?'NATIVE_ADJUSTED_HISTORY_CONNECTED':nativeMatches.length?'MULTIPLE_OR_INCOMPLETE_NATIVE_ADJUSTED_HISTORIES':'NO_NATIVE_ADJUSTED_HISTORY',
   securities:nativeMatches.map(c=>({permno:c.permno,...c.adjusted_history})),policy:p.price_policy,adjustment_base:p.source_adjustment_base,
   qualification:'EXISTING_MATERIALIZATION_HASH_VERIFIED;PERMNO_SOURCE_SCOPE;NOT_A_CROSS_PROVIDER_PIT_CERTIFICATION'};
  if(nativeMatches.length===1&&usable.length===1){
   row.adjusted_prices.archive_freshness=row.adjusted_prices.freshness;
   row.adjusted_prices.freshness=sourceFreshness(usable[0].adjusted_history.date_max);
   row.adjusted_prices.blockers=row.adjusted_prices.blockers.filter(b=>b!=='ADJUSTMENT_EVIDENCE_MISSING');row.valuation.blockers=row.valuation.blockers.filter(b=>b!=='ADJUSTMENT_EVIDENCE_MISSING');
   const h=usable[0].adjusted_history;
   if(h.rows!==h.split_adjusted_rows||h.rows!==h.distribution_adjusted_rows){
    row.adjusted_prices.blockers.push('ADJUSTMENT_ROWS_MISSING_OR_INVALID');row.valuation.blockers.push('ADJUSTMENT_ROWS_MISSING_OR_INVALID');
   }
  }
  const brief=briefs.briefs.find(b=>b.symbol===row.symbol);
  if(brief){brief.native_identity=row.identity.connections;brief.adjusted_history=row.adjusted_prices.connections;brief.recent_prices=row.recent_prices;
   brief.valuation=row.valuation;brief.archive_price_check=brief.price_check;brief.price_freshness=row.adjusted_prices.freshness;
   brief.price_check={native_status:row.adjusted_prices.connections.status,cross_provider_join_verified:false,point_in_time_eligible:false};
   brief.gaps=uniq(['identity','adjusted_prices','financials','valuation'].flatMap(k=>row[k].blockers||[]));
   brief.citations.push({kind:'existing_crsp_adjusted_materialization',manifest_sha256:p.pins.prices.sha256,policy:p.price_policy},
    {kind:'existing_native_identity_materialization',manifest_sha256:p.pins.identity.sha256},
    {kind:'existing_issuer_links_materialization',manifest_sha256:p.pins.issuer_links.sha256});
   if(recent[row.symbol])brief.citations.push({kind:'existing_recent_alpaca_publication',key:recent[row.symbol].source_key,sha256:recent[row.symbol].source_sha256,session:recent[row.symbol].session});}
 }
 await put(env,CONNECTED+`briefs/${n}.json`,briefs);
 await put(env,key,{input_sha256:p.input_sha256,connection_version:'native-connected-v2',rows:batch.rows});return {batch:n,securities:batch.rows.length};
}
async function finish(env){
 const p=await plan(env),stages={},repairs={},index={},hashes=[];let count=0,rowBytes=0;
 for(let n=0;n<132;n++){
  const obj=await env.DATA.get(CONNECTED+`batches/${n}.json`);if(!obj||obj.size>16*1048576)fail('CONNECTED_BATCH_UNAVAILABLE');
  const raw=await obj.text(),b=JSON.parse(raw);hashes.push(await sha(raw));
  if(b.input_sha256!==p.input_sha256||b.connection_version!=='native-connected-v2'||!b.rows.length)fail('FINAL_CONNECTION_PIN_CHANGED');
  rowBytes+=enc.encode(JSON.stringify(b.rows).slice(1,-1)).byteLength;
  for(const r of b.rows){
   if(r.symbol in index)fail('CONNECTION_DUPLICATE_SYMBOL');index[r.symbol]=n;count++;
   for(const [name,status]of Object.entries({identity:r.identity.connections.status,adjusted_history:r.adjusted_prices.connections.status,recent_prices:r.recent_prices.status})){
    stages[name]??={};stages[name][status]=(stages[name][status]||0)+1;}
   for(const reason of uniq(['identity','adjusted_prices','financials','valuation'].flatMap(k=>r[k].blockers||[])))(repairs[reason]??=[]).push(r.symbol);
  }
 }
 if(count!==2629)fail('CONNECTION_UNIVERSE_CHANGED');
 const queue=Object.entries(repairs).map(([blocker,symbols])=>({blocker,affected_securities:symbols.length,symbols})).sort((a,b)=>b.affected_securities-a.affected_securities);
 const summary={status:'CONNECTED',asof:ASOF,accounted:2629,stages,source_pins:p.pins,input_sha256:p.input_sha256,
  data_rights:'PRIVATE_OWNER_WRDS_CRSP_RESEARCH_ONLY;OWNER_ONLY_ALPACA_MARKET_DATA',
  top_repairs:queue.slice(0,12).map(({symbols,...r})=>r),
  full_workflow_verified:0,production_writes:0,upstream_downloads:0,laptop_normalizations:0,output_prefix:CONNECTED};
 const header=JSON.stringify({summary,repair_queue:queue}).slice(0,-1)+',"securities":[',tail=']}';
 const stream=new FixedLengthStream(enc.encode(header).byteLength+rowBytes+131+enc.encode(tail).byteLength);
 const writer=stream.writable.getWriter();
 const storing=env.DATA.put(CONNECTED+'ledger.json',stream.readable,{httpMetadata:{contentType:'application/json'}})
  .catch(async e=>{await writer.abort(e).catch(()=>{});throw e;});
 const writing=(async()=>{
  await writer.write(enc.encode(header));
  for(let n=0;n<132;n++){
   const obj=await env.DATA.get(CONNECTED+`batches/${n}.json`);if(!obj)fail('CONNECTED_BATCH_DISAPPEARED');
   const raw=await obj.text();if(await sha(raw)!==hashes[n])fail('CONNECTED_BATCH_CHANGED_DURING_PUBLICATION');
   const b=JSON.parse(raw);await writer.write(enc.encode((n?',':'')+JSON.stringify(b.rows).slice(1,-1)));
  }
  await writer.write(enc.encode(tail));await writer.close();
 })().catch(async e=>{await writer.abort(e).catch(()=>{});throw e;});
 await Promise.all([storing,writing]);
 await put(env,CONNECTED+'symbol-batches.json',index);
 const report=`# Connected security datasets — ${ASOF}\n\nAll 2,629 frozen symbols accounted for.\n\n${Object.entries(stages).map(([stage,counts])=>`## ${stage}\n\n${Object.entries(counts).map(([status,count])=>`- ${status}: ${count}`).join('\n')}`).join('\n\n')}\n\nExisting CRSP identity assertions, issuer-link materialization, adjusted-price outputs and recent Alpaca bars are connected. Native source history is not a cross-provider or point-in-time certification. CIK header dates are unknown; dated CIQ link boundaries retain their existing provisional policy. Split/distribution adjustments remain retrospective and separate from raw bars. No missing economic assumptions were filled. No full valuation workflow is certified.\n\n## Remaining repair cohorts\n\n${queue.map(r=>`- ${r.blocker}: ${r.affected_securities}`).join('\n')}\n\nAll financial payload processing ran in Cloudflare; no upstream acquisitions, laptop normalization, or production pointer changes.\n`;
 await env.DATA.put(CONNECTED+'REPORT.md',report,{httpMetadata:{contentType:'text/markdown'}});
 // Completion marker last: readers never switch to a partially connected release.
 await put(env,CONNECTED+'summary.json',summary);
 return summary;
}
export async function connectionRoute(env,path,n){
 if(path==='/connect/init')return init(env);
 if(path==='/connect/identity')return identityPart(env,n);
 if(path==='/connect/prices')return pricePart(env,n);
 if(path==='/connect/price-index')return priceIndex(env);
 if(path==='/connect/batch')return connectBatch(env,n);
 if(path==='/connect/finish')return finish(env);
 fail('UNKNOWN_CONNECTION_ROUTE');
}
