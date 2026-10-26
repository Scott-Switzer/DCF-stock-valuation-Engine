import {test} from 'node:test';
import assert from 'node:assert/strict';
import {structuredQuery} from '../query-input.mjs';
import {queryRoute} from '../queries.mjs';
import {FULL} from '../history.mjs';
const cutoff='2025-05-02T00:00:00Z',bundle='a'.repeat(64),release='b'.repeat(64),cik='0000000001';
const snapshot={bundle_id:bundle,source_releases:{SEC_ENGINE_MANIFEST_KEY:release}};
const request={action:'financials',symbol:'PEP',frequency:'annual',date_from:'2024-01-01',date_to:'2025-03-31',as_of:cutoff};
const url=r=>new URL('https://internal/query?'+new URLSearchParams({request:JSON.stringify(r)}));
function fixture(change=x=>x){
 const calls=[];const db=new Map([[FULL+'symbol-batches.json',{PEP:0}],[FULL+'batches/0.json',{rows:[{symbol:'PEP',identity:{cik},valuation:{inputs:{key:'current-packet',sha256:'c'.repeat(64)}}}]}]]);
 const env={TOKEN:'test',DATA:{get:async key=>{assert.notEqual(key,'current-packet','historical requests must bypass current packets');const x=db.get(key);return x?{size:JSON.stringify(x).length,text:async()=>JSON.stringify(x)}:null;}},FINANCIAL_API:{fetch:async req=>{
  const u=new URL(req.url);calls.push(u);const frequency=u.searchParams.get('frequency');
  const observation={metric:'revenue',frequency,period_start:'2025-01-01',period_end:'2025-03-31',unit:'USD',value_decimal:'100',available_at:'2025-05-01T12:00:00Z',source_observation_ids:['rev']};
  return Response.json(change({cik,bundle_id:bundle,frequency,as_of:cutoff,provenance:{release_id:release,company_maximum_as_of:'2026-01-01T00:00:00Z'},observations:u.searchParams.get('date_to')==='1999-12-31'?[]:[observation],source_records:{rev:{available_at:observation.available_at}},coverage_gaps:[],accounting_checks:[],pagination:{next_cursor:null}}));
 }}};return {env,calls};
}
test('financial cutoff requires an explicit real UTC second timestamp',()=>{
 assert.equal(structuredQuery(request,{PEP:0}).as_of,cutoff);
 for(const as_of of ['2025-05-02','2025-02-30T00:00:00Z','2025-05-02T00:00:00','2025-05-02T00:00:00+00:00',null])assert.throws(()=>structuredQuery({...request,as_of},{PEP:0}));
 assert.throws(()=>structuredQuery({action:'price',symbol:'PEP',as_of:cutoff},{PEP:0}));
});
test('all frequencies forward cutoff and preserve the native selection without current packet reuse',async()=>{
 for(const frequency of ['annual','quarterly','ttm']){
  const {env,calls}=fixture();const result=await queryRoute(env,url({...request,frequency}),{snapshot});
  assert.ok(calls.length);assert.ok(calls.every(u=>u.searchParams.get('as_of')===cutoff));
  assert.equal(result.source.as_of,cutoff);assert.equal(result.result.request.as_of,cutoff);
  assert.ok(result.result.observations.length);
 }
});
test('historical responses reject changed cutoff or unavailable leaf evidence',async()=>{
 for(const frequency of ['annual','quarterly','ttm'])for(const mutate of [
  x=>({...x,as_of:'2026-01-01T00:00:00Z'}),
  x=>({...x,observations:x.observations.map(r=>({...r,available_at:'2025-05-02T00:00:00.000000001Z'}))}),
  x=>({...x,source_records:{rev:{available_at:'2025-05-03T00:00:00Z'}}}),
  x=>({...x,source_records:{rev:{}}}),
  x=>({...x,bundle_id:'d'.repeat(64)}),
 ])await assert.rejects(queryRoute(fixture(mutate).env,url({...request,frequency}),{snapshot}),/FINANCIAL_/);
});
test('historical reads require the authority snapshot before any source request',async()=>{
 const {env,calls}=fixture();await assert.rejects(queryRoute(env,url(request),{}),/BUNDLE_UNAVAILABLE/);assert.equal(calls.length,0);
});
test('native unavailable accounting checks remain explicit gaps rather than blocking valid financial rows',async()=>{
 const unavailable={status:'UNAVAILABLE',reason:'EXACT_SCOPE_BALANCE_TOTAL_MISSING_OR_AMBIGUOUS',source_observation_ids:[]};
 const result=await queryRoute(fixture(x=>({...x,accounting_checks:[unavailable]})).env,url({...request,frequency:'quarterly'}),{snapshot});
 assert.equal(result.result.accounting_checks[0].status,'UNAVAILABLE');assert.equal(result.result.observations.length,1);
 await assert.rejects(queryRoute(fixture(x=>({...x,accounting_checks:[{...unavailable,status:'PASS'}]})).env,url({...request,frequency:'quarterly'}),{snapshot}),/FINANCIAL_LINEAGE/);
});
test('all historical frequencies reject missing or malformed pagination and gap metadata',async()=>{
 for(const frequency of ['annual','quarterly','ttm'])for(const mutate of [
  x=>({...x,pagination:undefined}),x=>({...x,pagination:{}}),x=>({...x,pagination:{next_cursor:17}}),x=>({...x,pagination:{next_cursor:''}}),x=>({...x,coverage_gaps:null})
 ])await assert.rejects(queryRoute(fixture(mutate).env,url({...request,frequency}),{snapshot}),/FINANCIAL_/);
});
