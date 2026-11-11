// Reuse full materialized histories and existing serving services; no acquisition.
import {openMaterialized,finish} from './connections.mjs';
const BASE='staging/security-funnel/2026-10-20/9beaa712e71650a2/';
const PARENT=BASE+'source-dated-2026-10-21-v1/';
const CONNECTED=BASE+'connected-2026-10-21-v1/';
export const FULL=BASE+'full-history-2026-10-21-v1/';
const RELEASE='b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb';
const RIGHTS='PRIVATE_OWNER_WRDS_CRSP_RESEARCH_ONLY;OWNER_ONLY_ALPACA_MARKET_DATA';
const enc=new TextEncoder();
const fail=c=>{throw Error(c)};
const sha=async raw=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',typeof raw==='string'?enc.encode(raw):raw)),x=>x.toString(16).padStart(2,'0')).join('');
async function read(bucket,key,digest=null,max=16*1048576){const o=await bucket.get(key);if(!o||o.size>max)fail('HISTORY_OBJECT_UNAVAILABLE');const raw=await o.text();if(digest&&await sha(raw)!==digest)fail('HISTORY_HASH_CHANGED');return JSON.parse(raw);}
async function put(env,key,value){await env.DATA.put(key,JSON.stringify(value),{httpMetadata:{contentType:'application/json'}});}
export function factorAudit(h){
 if(!h)return {status:'NO_HISTORY',missing_source_factor_rows:0,unusable_adjusted_rows_lower_bound:0,split_unusable_rows:0,distribution_unusable_rows:0};
 const unusable=h.rows-Math.min(h.split_adjusted_rows,h.distribution_adjusted_rows);
 return {status:h.missing_factor_rows?'SOURCE_FACTOR_ROWS_ABSENT':unusable?'UNUSABLE_ADJUSTED_ROWS_REQUIRE_DIAGNOSIS':'ALL_ROWS_HAVE_ADJUSTED_VALUES',
  missing_source_factor_rows:h.missing_factor_rows,unusable_adjusted_rows_lower_bound:unusable,split_unusable_rows:h.rows-h.split_adjusted_rows,distribution_unusable_rows:h.rows-h.distribution_adjusted_rows,
  qualification:'UNUSABLE_VALUES_ARE_NOT_ALL_MISSING_FACTORS;NO_FORWARD_FILL_OR_FACTOR_ONE_SUBSTITUTION'};
}
export function sourceInputs(data,cik){
 if(data.cik!==cik||data.frequency!=='annual'||data.provenance?.release_id!==RELEASE)fail('SOURCE_INPUT_CONTEXT_CHANGED');
 const obs=data.observations||[];
 for(const o of obs)if(typeof o.value_decimal!=='string'||! /^-?\d+(?:\.\d+)?$/.test(o.value_decimal)||!o.unit||!o.period_end||!o.available_at||!o.source_observation_ids?.length||o.source_observation_ids.some(id=>!data.source_records?.[id]))fail('SOURCE_INPUT_LINEAGE_INCOMPLETE');
 const dates=obs.map(o=>o.period_end).sort();
 return {schema_version:'sec-engine-valuation-inputs-v1',cik,frequency:'annual',source_release_id:RELEASE,
  date_min:dates[0]||null,date_max:dates.at(-1)||null,observations:obs,source_records:data.source_records||{},coverage_gaps:data.coverage_gaps||[],
  semantics:'EXISTING_SEC_ENGINE_DEFINITIONS_AND_DECIMAL_VALUES_UNCHANGED',
  share_basis:'WEIGHTED_AVERAGE_DILUTED_SHARES_ARE_NOT_SPOT_OUTSTANDING_SHARES',
  model_ready:false,assumptions:null,missing_model_inputs:['METHOD_SPECIFIC_ACCOUNTING_INPUTS','DATED_FORECAST_AND_DISCOUNT_ASSUMPTIONS','CURRENT_SECURITY_PRICE_BRIDGE']};
}
async function init(env){
 const prior=await env.DATA.get(FULL+'plan.json');if(prior)return prior.json();
 const parent=await read(env.DATA,PARENT+'summary.json'),p=await read(env.DATA,CONNECTED+'plan.json');
 const refs=await read(env.DATA,CONNECTED+'price-parts.json'),catalog={};
 for(let n=0;n<refs.length;n++){
  const part=await read(env.DATA,CONNECTED+`prices/${n}.json`);
  if(part.input_sha256!==p.input_sha256||part.source_sha256!==refs[n].sha256||part.rows!==refs[n].rows)fail('HISTORY_PROJECTION_CHANGED');
  for(const [id,h]of Object.entries(part.securities))(catalog[id]??=[]).push({ref:refs[n],date_min:h.date_min,date_max:h.date_max,security_rows:h.rows});
 }
 for(const entries of Object.values(catalog))entries.sort((a,b)=>a.date_min.localeCompare(b.date_min)||a.ref.key.localeCompare(b.ref.key));
 const packetsObject=await env.DATA.get('control/valuation/CURRENT.json');if(!packetsObject||packetsObject.size>1048576)fail('PACKET_INDEX_UNAVAILABLE');
 const packetsRaw=await packetsObject.text(),packets=JSON.parse(packetsRaw);if(packets.schema_version!=='ppe-valuation-index-v1')fail('PACKET_INDEX_SCHEMA');
 const targetObject=await env.DATA.get('evidence/us-security-universe-coverage-v1/price_target_v1.json');if(!targetObject||targetObject.size>8*1048576)fail('PRICE_TARGET_UNAVAILABLE');
 const targetRaw=await targetObject.text(),target=JSON.parse(targetRaw);if(!Array.isArray(target.targets))fail('PRICE_TARGET_SCHEMA');
 await env.DATA.put(FULL+'price-target.json',targetRaw);await env.DATA.put(FULL+'valuation-index.json',packetsRaw);
 const catalogRaw=JSON.stringify(catalog);await env.DATA.put(FULL+'history-catalog.json',catalogRaw);
 const pin=await sha(JSON.stringify({parent:parent.input_sha256,prices:p.input_sha256,packets:await sha(packetsRaw),targets:await sha(targetRaw),version:'full-history-v1'}));
 const result={input_sha256:pin,parent_input_sha256:parent.input_sha256,projection_input_sha256:p.input_sha256,source_date:parent.source_reference_date,
  catalog_sha256:await sha(catalogRaw),policy:'FULL_NATIVE_PERMNO_HISTORY;LATEST_SOURCE_DATE_IS_SELECTION_ONLY',ledger_batches:132,history_securities:Object.keys(catalog).length,
  history_parts:refs.length,valuation_index_sha256:await sha(packetsRaw),valuation_index_companies:Object.keys(packets.companies).length,
  target_sha256:await sha(targetRaw),target_generated_at:target.generated_at};
 await put(env,FULL+'plan.json',result);return result;
}
async function batch(env,n,signedRead,checkPacket){
 const plan=await read(env.DATA,FULL+'plan.json');if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_FULL_HISTORY_BATCH');
 const existing=await env.DATA.get(FULL+`batches/${n}.json`);if(existing){const done=await existing.json();if(done.input_sha256!==plan.input_sha256)fail('FULL_HISTORY_PIN_CHANGED');if(!['full-history-v1','full-history-v2','full-history-v3'].includes(done.connection_version))fail('UNKNOWN_FULL_HISTORY_CHECKPOINT');if(done.connection_version==='full-history-v1'){const briefs=await read(env.DATA,FULL+`briefs/${n}.json`);for(const row of done.rows){const c=row.identity.connections,selected=c.candidates.find(a=>a.security_id===c.selected_security_id);row.full_history.factor_audit=factorAudit(selected?.adjusted_history);const brief=briefs.briefs.find(a=>a.symbol===row.symbol);if(brief)brief.full_history=row.full_history;}done.connection_version='full-history-v2';await put(env,FULL+`briefs/${n}.json`,briefs);await put(env,FULL+`batches/${n}.json`,done);}return {batch:n,reused:true};}
 const b=await read(env.DATA,PARENT+`batches/${n}.json`),briefs=await read(env.DATA,PARENT+`briefs/${n}.json`);
 if(b.input_sha256!==plan.parent_input_sha256||b.connection_version!=='source-dated-v1')fail('FULL_HISTORY_PARENT_CHANGED');
 const catalog=await read(env.DATA,FULL+'history-catalog.json',plan.catalog_sha256),packets=await read(env.DATA,FULL+'valuation-index.json',plan.valuation_index_sha256),targets=await read(env.DATA,FULL+'price-target.json',plan.target_sha256,8*1048576);
 for(let offset=0;offset<b.rows.length;offset+=4)await Promise.all(b.rows.slice(offset,offset+4).map(async row=>{
  const c=row.identity.connections,selected=c.candidates.find(a=>a.security_id===c.selected_security_id),h=selected?.adjusted_history;
  const alternatives=c.candidates.filter(a=>a.adjusted_history).map(a=>({security_id:a.security_id,permno:a.permno,date_min:a.adjusted_history.date_min,date_max:a.adjusted_history.date_max,rows:a.adjusted_history.rows,parts:(catalog[a.permno]||[]).length}));
  row.full_history={status:selected?'FULL_NATIVE_HISTORY_CONNECTED':alternatives.length?'EXPLICIT_SECURITY_SELECTION_REQUIRED':'NO_NATIVE_HISTORY',
   security_id:selected?.security_id||null,permno:selected?.permno||null,date_min:h?.date_min||null,date_max:h?.date_max||null,rows:h?.rows||0,
   selection_date:plan.source_date,selection_date_is_history_start:false,alternatives,
   factor_audit:factorAudit(h),endpoint:'/history?symbol='+row.symbol,
   historical_availability:'NOT_ESTABLISHED',source_policy:'crsp-ciz-research-v1',rights:RIGHTS};
  const matches=targets.targets.filter(t=>t.display_ticker===row.symbol&&t.security_id===row.recent_prices.source_security_id&&t.provider_symbol===row.symbol);
  row.recent_prices.bridge={status:matches.length===1?'EXACT_PUBLISHED_TARGET_ID_CONNECTED':'NO_UNIQUE_PUBLISHED_TARGET_ID',
   source_namespace:'PPE_DAILY_PRICE_TARGET_SECURITY_ID',target_sha256:plan.target_sha256,target_snapshot_at:plan.target_generated_at,
   cross_provider_certified:false,effective_dated_issuer_share_class_bridge:'NOT_ESTABLISHED',
   reason:'DAILY_NORMALIZER_USES_PUBLISHED_TARGET_MAPPING;NOT_AN_ALPACA_UUID_OR_CRSP_ID'};
  row.valuation.inputs={status:'NO_CLOUD_HISTORY_INPUTS',observations:0,model_ready:false};
  const cloud=row.financials.cloud;
  if(cloud?.status==='CLOUD_HISTORY_VERIFIED'){
   const data=await signedRead(env,`gold/sec-engine/releases/${RELEASE}/queries/${cloud.query_fingerprint}.json`);
   const packet=sourceInputs(data,row.identity.cik);if(packet.observations.length!==cloud.observations)fail('FULL_SOURCE_INPUT_COUNTS_CHANGED');
   const raw=JSON.stringify(packet),key=FULL+'valuation-inputs/'+row.symbol+'.json';await env.DATA.put(key,raw,{httpMetadata:{contentType:'application/json'}});
   row.valuation.inputs={status:'SOURCE_HISTORY_INPUTS_CONNECTED',key,sha256:await sha(raw),date_min:packet.date_min,date_max:packet.date_max,observations:packet.observations.length,model_ready:false,missing_model_inputs:packet.missing_model_inputs};
  }
  const ref=packets.companies[row.symbol];
  if(ref){try{const verified=await checkPacket(env,ref,row);if(verified){row.valuation.packet=verified;row.valuation.blockers=row.valuation.blockers.filter(x=>x!=='VALUATION_ADAPTER_PACKET_REQUIRED');}}
   catch(e){row.valuation.current_packet_error=e.message;}}
  if(h){for(const stage of ['adjusted_prices','valuation']){
   row[stage].blockers=row[stage].blockers.filter(x=>x!=='ADJUSTMENT_ROWS_MISSING_OR_INVALID');
   if(h.missing_factor_rows)row[stage].blockers.push('SOURCE_FACTOR_ROWS_ABSENT');
   if(h.rows>Math.min(h.split_adjusted_rows,h.distribution_adjusted_rows))row[stage].blockers.push('UNUSABLE_ADJUSTED_ROWS_REQUIRE_DIAGNOSIS');
  }}
  const brief=briefs.briefs.find(a=>a.symbol===row.symbol);if(brief){brief.full_history=row.full_history;brief.recent_prices=row.recent_prices;brief.valuation=row.valuation;
   brief.gaps=[...new Set(['identity','adjusted_prices','financials','valuation'].flatMap(k=>row[k].blockers||[]))];
   brief.citations.push({kind:'full_native_history_catalog',input_sha256:plan.input_sha256},{kind:'source_history_valuation_inputs',...row.valuation.inputs});}
 }));
 await put(env,FULL+`briefs/${n}.json`,briefs);await put(env,FULL+`batches/${n}.json`,{input_sha256:plan.input_sha256,connection_version:'full-history-v2',rows:b.rows});
 return {batch:n,securities:b.rows.length,source_input_packets:b.rows.filter(r=>r.valuation.inputs.observations>0).length};
}
async function expandBatch(env,n,signedRead){
 const plan=await read(env.DATA,FULL+'plan.json');if(!Number.isInteger(n)||n<0||n>=132)fail('INVALID_FULL_HISTORY_BATCH');
 const b=await read(env.DATA,FULL+`batches/${n}.json`),briefs=await read(env.DATA,FULL+`briefs/${n}.json`);
 if(b.input_sha256!==plan.input_sha256)fail('FULL_HISTORY_PIN_CHANGED');
 if(b.connection_version==='full-history-v3'&&!b.rows.some(r=>r.valuation.inputs.full_range_expansion))return {batch:n,reused:true};
 if(!['full-history-v2','full-history-v3'].includes(b.connection_version))fail('FACTOR_METADATA_UPGRADE_REQUIRED');
 for(let offset=0;offset<b.rows.length;offset+=3)await Promise.all(b.rows.slice(offset,offset+3).map(async row=>{
  if(!row.financials.cloud?.query_fingerprint||row.valuation.inputs.status==='FULL_RANGE_SOURCE_INPUTS_CONNECTED'||row.valuation.inputs.status==='FULL_RANGE_SOURCE_HISTORY_EMPTY')return;
  try{
   const combined={cik:row.identity.cik,frequency:'annual',provenance:{release_id:RELEASE},observations:[],source_records:{},coverage_gaps:[]},queries=[];
   for(const [from,to]of [['1900-01-01','1999-12-31'],['2000-01-01','2026-09-24']]){
    const u=new URL('https://zion.internal/private/v1/financial-history');
    u.search=new URLSearchParams({release_id:RELEASE,cik:row.identity.cik,date_from:from,date_to:to,as_of:'2026-09-24T00:00:00Z',frequency:'annual',metrics:'revenue,operating_income,net_income,operating_cash_flow,capital_expenditures,cash,total_debt,diluted_shares,free_cash_flow',limit:'1'});
    const response=await env.FINANCIAL_API.fetch(new Request(u,{headers:{Authorization:'Bearer '+env.TOKEN},redirect:'manual'}));
    if(response.status!==200){const error=await response.json();fail('FULL_HISTORY_ENGINE_'+(error.error?.code||'HTTP_'+response.status));}
    const first=await response.json(),fp=first.cache?.query_fingerprint;
    if(!/^[a-f0-9]{64}$/.test(fp)||first.cache.archive_bytes_read_interactively!==0)fail('FULL_HISTORY_ENGINE_CONTEXT');
    const data=await signedRead(env,`gold/sec-engine/releases/${RELEASE}/queries/${fp}.json`);sourceInputs(data,row.identity.cik);
    if(data.observations.some(o=>o.period_end<from||o.period_end>to))fail('FULL_HISTORY_WINDOW_CONTEXT');
    combined.observations.push(...data.observations);combined.coverage_gaps.push(...(data.coverage_gaps||[]));
    for(const [id,record]of Object.entries(data.source_records||{})){if(combined.source_records[id]&&JSON.stringify(combined.source_records[id])!==JSON.stringify(record))fail('SOURCE_RECORD_CONFLICT');combined.source_records[id]=record;}
    queries.push({date_from:from,date_to:to,query_fingerprint:fp});
   }
   const packet=sourceInputs(combined,row.identity.cik);packet.source_queries=queries;
   packet.requested_date_from='1900-01-01';packet.requested_date_to='2026-09-24';packet.requested_metrics=['revenue','operating_income','net_income','operating_cash_flow','capital_expenditures','cash','total_debt','diluted_shares','free_cash_flow'];
   const raw=JSON.stringify(packet),key=FULL+'valuation-inputs/'+row.symbol+'.full-annual.json';await env.DATA.put(key,raw,{httpMetadata:{contentType:'application/json'}});
   row.valuation.inputs={status:packet.observations.length?'FULL_RANGE_SOURCE_INPUTS_CONNECTED':'FULL_RANGE_SOURCE_HISTORY_EMPTY',key,sha256:await sha(raw),date_min:packet.date_min,date_max:packet.date_max,requested_date_from:'1900-01-01',frequency:'annual',observations:packet.observations.length,source_queries:queries,model_ready:false,missing_model_inputs:packet.missing_model_inputs};
   row.financials.full_history={...row.valuation.inputs,source_release_id:RELEASE,quarterly_ttm_endpoint:'/financial-history?cik='+row.identity.cik};
  }catch(e){row.valuation.inputs.full_range_expansion={status:'BLOCKED',reason:e.message};}
  const brief=briefs.briefs.find(x=>x.symbol===row.symbol);if(brief){brief.valuation=row.valuation;brief.full_financial_history=row.financials.full_history||row.valuation.inputs.full_range_expansion;brief.citations.push({kind:'full_range_financial_inputs',...row.valuation.inputs});}
 }));
 b.connection_version='full-history-v3';await put(env,FULL+`briefs/${n}.json`,briefs);await put(env,FULL+`batches/${n}.json`,b);
 return {batch:n,securities:b.rows.length,full_range_inputs:b.rows.filter(r=>r.valuation.inputs.status==='FULL_RANGE_SOURCE_INPUTS_CONNECTED').length,blocked:b.rows.filter(r=>r.valuation.inputs.full_range_expansion).map(r=>({symbol:r.symbol,reason:r.valuation.inputs.full_range_expansion.reason}))};
}
async function security(env,symbol){if(!/^[A-Z0-9][A-Z0-9.-]{0,24}$/.test(symbol||''))fail('INVALID_SYMBOL');const index=await read(env.DATA,FULL+'symbol-batches.json');if(!(symbol in index))fail('SYMBOL_NOT_IN_FROZEN_UNIVERSE');const b=await read(env.DATA,FULL+`batches/${index[symbol]}.json`),plan=await read(env.DATA,FULL+'plan.json');if(b.input_sha256!==plan.input_sha256||!['full-history-v2','full-history-v3'].includes(b.connection_version))fail('FULL_HISTORY_PIN_CHANGED');return b.rows.find(r=>r.symbol===symbol);}
// One decode per part for every column a total-return window needs.
export async function seriesRows(env,permno,from,to,cap=20000){
 const plan=await read(env.DATA,FULL+'plan.json'),catalog=await read(env.DATA,FULL+'history-catalog.json',plan.catalog_sha256);
 const refs=(catalog[String(permno)]||[]).filter(a=>(!from||a.date_max>=from)&&(!to||a.date_min<=to));
 if(!refs.length)fail('PERMNO_NOT_IN_STORED_HISTORY');
 const fields=['permno','dlycaldt','split_adjusted_price','source_total_return','dlydelflg','delisting_return_present'];
 const rows=[];
 for(const entry of refs){
  const p=await openMaterialized(env,entry.ref),data=await p.columns(fields),ids=data.permno,dates=data.dlycaldt;
  for(let i=0;i<ids.length;i++){
   if(String(ids[i])!==String(permno))continue;
   const date=dates[i];if(from&&date<from)continue;if(to&&date>to)continue;
   if(rows.length>cap)fail('HISTORY_WINDOW_TOO_LARGE');
   rows.push({date,split_adjusted_price:data.split_adjusted_price[i],source_total_return:data.source_total_return[i],
    dlydelflg:data.dlydelflg[i],delisting_return_present:data.delisting_return_present[i]===true});
  }
 }
 rows.sort((a,b)=>a.date.localeCompare(b.date));
 return {rows,input_sha256:plan.input_sha256,parts:refs.length};
}
// The CRSP delisting file is a small, hash-pinned source object. Its compact
// derived index is built once and read by every total-return question.
let DELISTING_CACHE=null;
export async function delistingsIndex(env){
 const object=await env.DATA.get(FULL+'delistings-index.json');
 if(!object)return null;
 const etag=object.etag||null;
 if(etag&&DELISTING_CACHE?.etag===etag)return DELISTING_CACHE.value;
 if(object.size>4*1048576)fail('DELISTINGS_INDEX_BUDGET');
 const value=JSON.parse(await object.text());
 if(value.schema_version!=='zion-crsp-delistings-v1'||typeof value.entries!=='object')fail('DELISTINGS_INDEX_SCHEMA');
 if(etag)DELISTING_CACHE={etag,value};
 return value;
}
export function delistingRecord(index,permno){
 const row=index?.entries?.[String(permno)];
 if(!Array.isArray(row)||row.length<3)return null;
 return {date:row[0],code:Number(row[1]),dlret:typeof row[2]==='number'?row[2]:null,dlretx:typeof row[3]==='number'?row[3]:null};
}
// Owner-only build. Reads the catalogued delisting file through the datasets
// service, keeps only true delistings (dlstcd >= 200) for the frozen universe and
// writes a deterministic index pinned by the source object's digest.
async function delistingsInit(env){
 const id='4833fe6633fc104b61475e35b253898a';
 const response=await env.FINANCIAL_API.fetch(new Request('https://zion.internal/private/v1/datasets/catalog/'+id,{headers:{Authorization:'Bearer '+env.TOKEN},signal:AbortSignal.timeout(15000)}));
 const detail=await boundedJson(response,262144);
 if(!response.ok)fail(detail.error?.code||'DELISTING_CATALOG_UNAVAILABLE');
 const store=detail.store,object=(detail.objects||[])[0];
 if(store!=='research'||!object?.key||!/^[a-f0-9]{64}$/.test(object.sha256||''))fail('DELISTING_SOURCE_UNSUPPORTED');
 const existing=await env.DATA.get(FULL+'delistings-index.json');
 if(existing&&existing.size<=4*1048576){const done=JSON.parse(await existing.text());if(done.source?.object?.sha256===object.sha256)return {...done.summary,reused:true};}
 const plan=await read(env.DATA,FULL+'plan.json'),catalog=await read(env.DATA,FULL+'history-catalog.json',plan.catalog_sha256);
 const universe=new Set(Object.keys(catalog)),rows=[];
 let cursor;
 for(let page=0;page<120;page++){
  const target=new URL('https://datasets.internal/v1/datasets/'+store+'/rows');
  target.searchParams.set('path',object.key);
  target.searchParams.set('columns','permno,dlstdt,dlstcd,dlret,dlretx');
  target.searchParams.set('limit','1000');
  if(cursor)target.searchParams.set('cursor',cursor);
  const pageResponse=await env.ZION_DATASETS.fetch(new Request(target,{headers:{'User-Agent':'Zion-Security-Funnel/1.0'},signal:AbortSignal.timeout(20000)}));
  const data=await boundedJson(pageResponse,4*1048576);
  if(!pageResponse.ok)fail(data.error?.code||'DELISTING_SOURCE_READ_FAILED');
  if(data.schema_version!=='zion-native-table-v1')fail('DELISTING_SOURCE_SCHEMA');
  rows.push(...(data.data?.rows||[]));
  cursor=data.next_cursor||null;
  if(!cursor)break;
  if(page===119)fail('DELISTING_SOURCE_PAGE_BUDGET');
 }
 const source={dataset:detail.dataset,catalog_id:id,catalog_release_id:detail.catalog_release_id,store,
  object:{key:object.key,sha256:object.sha256,rows:object.rows??null}};
 const {payload,summary}=await delistingIndexPayload({rows,universe,source});
 await put(env,FULL+'delistings-index.json',payload);
 return summary;
}
// Shared by the Worker route and the reproducible local build script so both
// produce byte-identical indexes from the same rules.
export function delistingEntries(rows,universe){
 const entries={},families={};let scanned=0,delistings=0;
 for(const row of rows){
  scanned++;
  const permno=Number(row.permno),code=Number(row.dlstcd);
  if(!Number.isInteger(code)||code<200||!universe.has(String(permno)))continue;
  delistings++;
  const family=String(code).slice(0,1)+'00';
  families[family]=(families[family]||0)+1;
  const date=String(row.dlstdt||'').slice(0,10);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date))continue;
  entries[String(permno)]=[date,code,typeof row.dlret==='number'?row.dlret:null,typeof row.dlretx==='number'?row.dlretx:null];
 }
 return {entries,families,scanned,delistings};
}
export async function delistingIndexPayload({rows,universe,source}){
 const built=delistingEntries(rows,universe);
 const entries_sha256=await sha(JSON.stringify(built.entries));
 const summary={source_dataset:source.dataset,catalog_id:source.catalog_id,catalog_release_id:source.catalog_release_id,
  rows_scanned:built.scanned,delistings_in_universe:built.delistings,indexed_permnos:Object.keys(built.entries).length,
  code_families:built.families,entries_sha256,reused:false};
 return {payload:{schema_version:'zion-crsp-delistings-v1',source,summary,entries:built.entries},summary};
}
async function boundedJson(response,max){
 if(!response.body)throw Error('SOURCE_UNAVAILABLE');
 const raw=await response.text();
 if(raw.length>max)throw Error('SOURCE_RESPONSE_TOO_LARGE');
 return JSON.parse(raw);
}
export function validateHistoryQuery(u){
 const allowed=new Set(['symbol','permno','date_from','date_to','part','offset','limit','expected_input_sha256','metadata_only']);
 for(const k of u.searchParams.keys())if(!allowed.has(k)||u.searchParams.getAll(k).length!==1)fail('INVALID_HISTORY_PARAMETER');
 const number=(k,d,max)=>{const s=u.searchParams.get(k)??String(d);if(!/^\d{1,7}$/.test(s)||Number(s)>max)fail('INVALID_HISTORY_'+k.toUpperCase());return Number(s)};
 const date=k=>{const s=u.searchParams.get(k);if(s&&(!/^\d{4}-\d{2}-\d{2}$/.test(s)||!Number.isFinite(Date.parse(s+'T00:00:00Z'))||new Date(s+'T00:00:00Z').toISOString().slice(0,10)!==s))fail('INVALID_HISTORY_DATE');return s};
 const from=date('date_from'),to=date('date_to');if(from&&to&&from>to)fail('INVALID_HISTORY_DATE_RANGE');
 const limit=number('limit',100,500);if(!limit)fail('INVALID_HISTORY_LIMIT');
 return {from,to,part:number('part',0,1000),offset:number('offset',0,1000000),limit};
}
async function history(env,u){
 const q=validateHistoryQuery(u),plan=await read(env.DATA,FULL+'plan.json');
 if(u.searchParams.get('expected_input_sha256')&&u.searchParams.get('expected_input_sha256')!==plan.input_sha256)fail('HISTORY_RELEASE_CHANGED');
 if((q.part||q.offset)&&u.searchParams.get('expected_input_sha256')!==plan.input_sha256)fail('HISTORY_PAGINATION_REQUIRES_RELEASE_PIN');
 const row=await security(env,u.searchParams.get('symbol')),catalog=await read(env.DATA,FULL+'history-catalog.json',plan.catalog_sha256);
 const id=u.searchParams.get('permno')||String(row.full_history.permno||'');
 if(!/^\d+$/.test(id)||!row.full_history.alternatives.some(a=>String(a.permno)===id))fail('EXPLICIT_MATCHED_PERMNO_REQUIRED');
 const selected=row.full_history.alternatives.find(a=>String(a.permno)===id);
 const refs=(catalog[id]||[]).filter(a=>(!q.from||a.date_max>=q.from)&&(!q.to||a.date_min<=q.to));
 const result={symbol:row.symbol,permno:Number(id),input_sha256:plan.input_sha256,coverage:selected,parts:refs.length,
  basis:'FULL_PERMNO_HISTORY_INCLUDING_FORMER_TICKERS;NO_LATEST_DATE_TRUNCATION',adjustment_policy:'crsp-ciz-research-v1',
  adjustment_base:'SOURCE_LAST_TRADING_DAY_RETROSPECTIVE;NOT_PIT_QUOTE',historical_availability:'NOT_ESTABLISHED',rights:RIGHTS,rows:[]};
 if(u.searchParams.get('metadata_only')==='true')return result;
 if(q.part>=refs.length){if(!refs.length&&q.part===0)return {...result,next:null};fail('HISTORY_PART_OUT_OF_RANGE');}
 const ref=refs[q.part].ref,p=await openMaterialized(env,ref),positions=[];
 const priceColumns=['raw_observed_price','split_adjusted_price','distribution_adjusted_price','source_total_return','source_return_ex_ordinary_dividends','missing_adjustment_factors'];
 // One decode for every column a page needs; per-column decodes reread the whole part.
 const data=await p.columns(['permno','dlycaldt',...priceColumns]),ids=data.permno,dates=data.dlycaldt;
 for(let i=0;i<ids.length;i++)if(String(ids[i])===id&&(!q.from||dates[i]>=q.from)&&(!q.to||dates[i]<=q.to))positions.push(i);
 if(q.offset>positions.length)fail('HISTORY_OFFSET_OUT_OF_RANGE');
 const take=positions.slice(q.offset,q.offset+q.limit),rows=take.map(i=>({date:dates[i],permno:Number(id)}));
 for(const name of priceColumns)for(let j=0;j<take.length;j++)rows[j][name]=data[name][take[j]];
 result.rows=rows;result.source={key:ref.key,sha256:ref.sha256};
 const more=q.offset+take.length<positions.length;
 result.next=more?{part:q.part,offset:q.offset+take.length}:q.part+1<refs.length?{part:q.part+1,offset:0}:null;
 if(result.next)result.next.expected_input_sha256=plan.input_sha256;
 return result;
}
export async function historyRoute(env,u,signedRead,checkPacket){
 if(u.pathname==='/connect/history-acceptance'){
  const results=[];
  for(const symbol of ['AAPL','MSFT','ABG']){
   const row=await security(env,symbol),page=await history(env,new URL('https://internal/history?symbol='+symbol+'&limit=10'));
   if(!page.rows.length||!page.coverage.date_min||page.coverage.date_min>='2015-01-01'||page.rows.every(r=>r.date>='2015-01-01')||page.rows.some(r=>r.date<page.coverage.date_min||r.date>page.coverage.date_max))fail('EARLY_HISTORY_ACCEPTANCE_FAILED');
   const ref=row.valuation.inputs;if(ref.status!=='FULL_RANGE_SOURCE_INPUTS_CONNECTED')fail('FULL_FINANCIAL_INPUTS_NOT_READY');
   const inputs=await read(env.DATA,ref.key,ref.sha256);
   if(inputs.requested_date_from!=='1900-01-01'||inputs.requested_metrics.length!==9||inputs.source_queries.length!==2||inputs.observations.length!==ref.observations)fail('FULL_INPUT_ACCEPTANCE_FAILED');
   results.push({symbol,history_date_min:page.coverage.date_min,history_date_max:page.coverage.date_max,history_rows:page.coverage.rows,early_page_rows:page.rows.length,earliest_returned_date:page.rows.map(r=>r.date).sort()[0],annual_input_observations:ref.observations,annual_input_date_min:ref.date_min,annual_input_date_max:ref.date_max,financial_windows:inputs.source_queries.map(q=>({date_from:q.date_from,date_to:q.date_to})),factor_audit:row.full_history.factor_audit,recent_bridge:row.recent_prices.bridge.status});
  }
  const result={status:'LIVE_VERIFIED',checks:results,financial_values_returned_to_controller:0};await put(env,FULL+'acceptance.json',result);return result;
 }
 if(u.pathname==='/connect/history-factor-source-audit'){
  const digest='db2262bc67d3ae7f5ae7e88b8d98794f5397f9933135300f6984633991873642';
  const catalog=await read(env.RESEARCH,'research/financial-research-canonical-v1/pinned-sources/'+digest+'.json',digest);
  const index=await read(env.DATA,CONNECTED+'price-index.json'),main=catalog.datasets.crsp_a_stock__stkdlycumulativeadjfactor,alias=catalog.datasets.crsp__stkdlycumulativeadjfactor,sample=catalog.datasets.crspsamp_all__stkdlycumulativeadjfactor;
  if(sample.objects.length!==1)fail('SAMPLE_FACTOR_BUDGET_CHANGED');
  const missing=new Set(Object.entries(index.securities).filter(([,h])=>h.missing_factor_rows>0).map(([id])=>id));
  const p=await openMaterialized(env,sample.objects[0],'pinned-crsp-sample-factors'),ids=await p.column('permno'),positions=[],byId={};
  for(let i=0;i<ids.length;i++)if(missing.has(String(ids[i]))){positions.push(i);(byId[String(ids[i])]??={rows:0,date_min:null,date_max:null,positive_split_factors:0,positive_distribution_factors:0}).rows++;}
  const dates=await p.column('dlycaldt');for(const i of positions){const h=byId[String(ids[i])],d=dates[i];if(!h.date_min||d<h.date_min)h.date_min=d;if(!h.date_max||d>h.date_max)h.date_max=d;}
  for(const [name,count]of [['dlycumfacshr','positive_split_factors'],['dlycumfacpr','positive_distribution_factors']]){const values=await p.column(name);for(const i of positions)if(typeof values[i]==='number'&&Number.isFinite(values[i])&&values[i]>0)byId[String(ids[i])][count]++;}
  const equality=JSON.stringify(main.objects.map(x=>x.sha256).sort())===JSON.stringify(alias.objects.map(x=>x.sha256).sort());
  const result={source_catalog_sha256:digest,full_factor_alias_same_payload_hashes:equality,full_factor_rows:main.manifest_rows,
   sample_factor_rows:sample.manifest_rows,securities_with_missing_source_factors:missing.size,sample_overlapping_securities:Object.keys(byId).length,
   sample_matching_adjustment_base_date:Object.entries(byId).filter(([id,h])=>h.date_max===index.securities[id].date_max).length,
   source_factor_rows_repaired:0,qualification:'NO_SOURCE_SUBSTITUTION;SAMPLE_FACTOR_BASE_AND_EXACT_DATE_KEYS_REQUIRE_VALIDATION',provider_requests:0,laptop_payload_bytes:0};
  await put(env,FULL+'factor-source-audit.json',{...result,candidates:byId});return result;
 }
 if(u.pathname==='/connect/history-source-audit'){
  const digest='db2262bc67d3ae7f5ae7e88b8d98794f5397f9933135300f6984633991873642';
  const catalog=await read(env.RESEARCH,'research/financial-research-canonical-v1/pinned-sources/'+digest+'.json',digest);
  const datasets=Object.entries(catalog.datasets).filter(([id])=>/dsf|cumulativeadjfactor|stksecurityinfohist|ciq.*symbol|comp.*security/.test(id)).map(([id,d])=>({dataset:id,rows:d.manifest_rows,objects:d.objects.length,columns:d.columns,manifest_key:d.manifest_key,manifest_sha256:d.manifest_sha256}));
  const result={source_catalog_sha256:digest,datasets,provider_requests:0,raw_payload_reads:0};await put(env,FULL+'source-repair-audit.json',result);return result;
 }
 if(u.pathname==='/connect/delistings-init')return delistingsInit(env);
 if(u.pathname==='/connect/history-expand-batch')return expandBatch(env,Number(u.searchParams.get('n')),signedRead);
 if(u.pathname==='/connect/history-init')return init(env);
 if(u.pathname==='/connect/history-batch')return batch(env,Number(u.searchParams.get('n')),signedRead,checkPacket);
 if(u.pathname==='/connect/history-finish'){const p=await read(env.DATA,FULL+'plan.json');return finish(env,FULL,'full-history-v3',p);}
 if(u.pathname==='/history')return history(env,u);
 if(u.pathname==='/valuation-inputs'){const row=await security(env,u.searchParams.get('symbol'));if(!row.valuation.inputs.key)fail('NO_SOURCE_HISTORY_INPUTS');return read(env.DATA,row.valuation.inputs.key,row.valuation.inputs.sha256);}
 fail('UNKNOWN_HISTORY_ROUTE');
}
