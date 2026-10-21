import assert from 'node:assert/strict';
import {factorAudit,sourceInputs,validateHistoryQuery,historyRoute} from '../history.mjs';
import worker from '../worker.mjs';
assert.equal(factorAudit({rows:10,split_adjusted_rows:8,distribution_adjusted_rows:8,missing_factor_rows:0}).status,'UNUSABLE_ADJUSTED_ROWS_REQUIRE_DIAGNOSIS');
assert.equal(factorAudit({rows:10,split_adjusted_rows:8,distribution_adjusted_rows:8,missing_factor_rows:2}).missing_source_factor_rows,2);
assert.equal(factorAudit({rows:10,split_adjusted_rows:8,distribution_adjusted_rows:7,missing_factor_rows:0}).unusable_adjusted_rows_lower_bound,3);
const data={cik:'0000000001',frequency:'annual',provenance:{release_id:'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb'},observations:[{metric:'revenue',value_decimal:'123.123456789123456789',unit:'USD',period_end:'1992-12-31',available_at:'1993-03-01T00:00:00Z',source_observation_ids:['x']}],source_records:{x:{}}};
const packet=sourceInputs(data,data.cik);
assert.equal(packet.date_min,'1992-12-31');assert.equal(packet.observations[0].value_decimal,data.observations[0].value_decimal);assert.equal(packet.model_ready,false);
assert.throws(()=>sourceInputs(data,'0000000002'),/CONTEXT/);
assert.throws(()=>sourceInputs({...data,source_records:{}},data.cik),/LINEAGE/);
assert.throws(()=>validateHistoryQuery(new URL('https://x/history?date_from=2025-02-30')),/DATE/);
assert.throws(()=>validateHistoryQuery(new URL('https://x/history?limit=501')),/LIMIT/);
assert.throws(()=>validateHistoryQuery(new URL('https://x/history?limit=1&limit=2')),/PARAMETER/);
assert.equal(validateHistoryQuery(new URL('https://x/history?date_from=1925-12-31')).from,'1925-12-31');
assert.equal((await worker.fetch(new Request('https://x/history'),{TOKEN:'test'})).status,401);
// Metadata requests never open a financial Parquet; full history includes earlier aliases.
const prefix='staging/security-funnel/2026-10-20/9beaa712e71650a2/full-history-2026-10-21-v1/';
const {createHash}=await import('node:crypto');
const catalog=JSON.stringify({'101':[{ref:{key:'never-read.parquet'},date_min:'1925-12-31',date_max:'2025-12-31'}]});
const objects={
 [prefix+'plan.json']:{input_sha256:'pin',catalog_sha256:createHash('sha256').update(catalog).digest('hex')},
 [prefix+'symbol-batches.json']:{TEST:0},
 [prefix+'batches/0.json']:{input_sha256:'pin',connection_version:'full-history-v2',rows:[{symbol:'TEST',full_history:{permno:101,alternatives:[{permno:101,date_min:'1925-12-31',date_max:'2025-12-31'}]}}]},
 [prefix+'history-catalog.json']:catalog};
const env={DATA:{get:async key=>{const v=objects[key];if(v===undefined)throw Error('Unexpected read');const raw=typeof v==='string'?v:JSON.stringify(v);return {size:raw.length,text:async()=>raw}}},RESEARCH:{get:()=>{throw Error('Financial payload read')}}};
const result=await historyRoute(env,new URL('https://x/history?symbol=TEST&metadata_only=true'));
assert.equal(result.coverage.date_min,'1925-12-31');assert.equal(result.parts,1);
await assert.rejects(historyRoute(env,new URL('https://x/history?symbol=TEST&part=1')),/PAGINATION_REQUIRES_RELEASE_PIN/);
console.log('Full-history coverage, source inputs, factor classification, auth and release gates passed.');
// Existing engine enforces a 100-year window; full history must expose continuation.
const auth={Authorization:'Bearer test'};
let forwarded;
const financial=await worker.fetch(new Request('https://x/financial-history?cik=0000000001',{headers:auth}),{TOKEN:'test',FINANCIAL_API:{fetch:async request=>{forwarded=new URL(request.url);return Response.json({pagination:{next_cursor:null}})}}});
assert.equal(forwarded.searchParams.get('date_from'),'1900-01-01');
assert.equal(forwarded.searchParams.get('date_to'),'1999-12-31');
assert.equal((await financial.json()).full_history_window.next.date_from,'2000-01-01');
// Expansion joins disjoint source windows and cannot be downgraded by a resumed batch.
const mutable={
 [prefix+'plan.json']:{input_sha256:'pin'},
 [prefix+'batches/0.json']:{input_sha256:'pin',connection_version:'full-history-v2',rows:[{symbol:'TEST',identity:{cik:data.cik},financials:{cloud:{query_fingerprint:'old'}},valuation:{inputs:{status:'SOURCE_HISTORY_INPUTS_CONNECTED'}}}]},
 [prefix+'briefs/0.json']:{briefs:[{symbol:'TEST',citations:[]}]}};
const mem={get:async key=>{const v=mutable[key];if(!v)throw Error('Unexpected object '+key);const raw=JSON.stringify(v);return {size:raw.length,text:async()=>raw,json:async()=>JSON.parse(raw)}},put:async(key,raw)=>{mutable[key]=JSON.parse(raw)}};
const expandedEnv={TOKEN:'test',DATA:mem,FINANCIAL_API:{fetch:async request=>{
 const from=new URL(request.url).searchParams.get('date_from');return Response.json({cache:{query_fingerprint:(from==='1900-01-01'?'a':'b').repeat(64),archive_bytes_read_interactively:0}});
}}};
const signed=async(env,key)=>key.includes('a'.repeat(64))?structuredClone(data):{...structuredClone(data),observations:[{...data.observations[0],period_end:'2025-12-31',source_observation_ids:['y']}],source_records:{y:{}}};
const expanded=await historyRoute(expandedEnv,new URL('https://x/connect/history-expand-batch?n=0'),signed);
assert.equal(expanded.full_range_inputs,1);assert.equal(expanded.blocked.length,0);
assert.equal(mutable[prefix+'valuation-inputs/TEST.full-annual.json'].observations.length,2);
assert.equal(mutable[prefix+'batches/0.json'].connection_version,'full-history-v3');
await historyRoute(expandedEnv,new URL('https://x/connect/history-batch?n=0'));
assert.equal(mutable[prefix+'batches/0.json'].connection_version,'full-history-v3');
console.log('Century-window continuation, full-range source expansion and resume semantics passed.');
