import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute,requestQuery} from '../queries.mjs';
import {FULL} from '../history.mjs';
const bundle='a'.repeat(64),release='b'.repeat(64),cik='0000000001';
const snapshot={bundle_id:bundle,source_releases:{SEC_ENGINE_MANIFEST_KEY:release}};
const row=(metric,value,id)=>({metric,value_decimal:value,unit:'USD',frequency:'quarterly',period_start:'2025-01-01',period_end:'2025-03-31',available_at:'2025-05-01T00:00:00Z',source_observation_ids:[id]});
function fixture(change=x=>x){
 const db=new Map([[FULL+'symbol-batches.json',{AAPL:0}],[FULL+'batches/0.json',{rows:[{symbol:'AAPL',identity:{cik},valuation:{inputs:{key:'annual-must-not-be-read'}}}]}]]);
 const calls=[];
 return {calls,env:{TOKEN:'fixture',DATA:{get:async key=>{assert.notEqual(key,'annual-must-not-be-read');const x=db.get(key);return x?{size:JSON.stringify(x).length,text:async()=>JSON.stringify(x)}:null;}},FINANCIAL_API:{fetch:async req=>{
  const u=new URL(req.url);calls.push(u);assert.equal(u.searchParams.get('materialized_only'),'true');assert.equal(u.searchParams.get('release_id'),release);assert.equal(req.headers.get('x-zion-bundle-id'),bundle);
  const r=row('revenue','100','rev'),i=row('operating_income','20','income');
  return Response.json(change({cik,bundle_id:bundle,frequency:'quarterly',as_of:'2025-10-01T00:00:00Z',provenance:{release_id:release,materialization_release_id:release},observations:u.searchParams.has('cursor')?[i]:[r],source_records:u.searchParams.has('cursor')?{income:{}}:{rev:{}},coverage_gaps:[],accounting_checks:[],pagination:{next_cursor:u.searchParams.has('cursor')?null:'next'}}));
 }}}};
}
function url(request){return new URL('https://internal/query?'+new URLSearchParams({request:JSON.stringify(request)}));}
test('quarterly margin reuses native engine pages and source lineage, never annual packets',async()=>{
 const {env,calls}=fixture();
 const r=await queryRoute(env,url({action:'financials',symbol:'AAPL',frequency:'quarterly',metric:'operating_margin',date_from:'2025-01-01',date_to:'2025-12-31'}),{snapshot});
 assert.equal(calls.length,2);assert.equal(calls[0].searchParams.get('frequency'),'quarterly');
 assert.equal(r.result.observations[0].value_decimal,'0.2');assert.deepEqual(r.result.observations[0].source_observation_ids,['income','rev']);assert.match(r.answer,/quarterly/);assert.equal(r.source.release,release);
});
test('period source mismatches, unsupported growth and missing currency fail explicitly',async()=>{
 const request={action:'financials',symbol:'AAPL',frequency:'quarterly'};
 for(const change of [x=>({...x,bundle_id:'c'.repeat(64)}),x=>({...x,frequency:'annual'}),x=>({...x,cik:'0000000002'}),x=>({...x,provenance:{release_id:'d'.repeat(64)}}),x=>({...x,source_records:{}})]){
  await assert.rejects(queryRoute(fixture(change).env,url(request),{snapshot}));
 }
 await assert.rejects(queryRoute(fixture().env,url({...request,metric:'revenue_growth'}),{snapshot}),/NON_ANNUAL_GROWTH/);
 const changed=fixture(x=>({...x,observations:x.observations.map(r=>({...r,unit:r.metric==='revenue'?'USD':'EUR'}))}));
 const result=await queryRoute(changed.env,url({...request,metric:'operating_margin'}),{snapshot});
 assert.equal(result.result.observations.length,0);assert.equal(result.result.calculation_gaps[0].reason,'MARGIN_COMPONENTS_NOT_COMPARABLE');
});
test('natural financial periods are explicit and fiscal quarter numbers stay ambiguous',()=>{
 assert.equal(requestQuery('AAPL quarterly revenue 2025',{AAPL:0}).frequency,'quarterly');
 assert.equal(requestQuery('AAPL TTM revenue',{AAPL:0}).frequency,'ttm');
 assert.throws(()=>requestQuery('AAPL revenue Q1 2025',{AAPL:0}),/EXACT_PERIOD_RANGE/);
 assert.throws(()=>requestQuery('AAPL quarterly TTM revenue',{AAPL:0}),/AMBIGUOUS_FREQUENCY/);
});

test('TTM values come from the native engine without summing them again',async()=>{
 const {env,calls}=fixture(x=>({...x,frequency:'ttm',observations:x.observations.map(r=>({...r,frequency:'ttm'}))}));
 const result=await queryRoute(env,url({action:'financials',symbol:'AAPL',frequency:'ttm'}),{snapshot});
 assert.equal(calls[0].searchParams.get('frequency'),'ttm');assert.equal(result.result.observations[0].value_decimal,'100');
 assert.equal(result.result.frequency,'ttm');assert.match(result.warnings.join(' '),/source defaults/);
});
test('repeated pagination and missing stored materializations fail without partial answers',async()=>{
 await assert.rejects(queryRoute(fixture(x=>({...x,pagination:{next_cursor:'same'}})).env,url({action:'financials',symbol:'AAPL',frequency:'quarterly'}),{snapshot}),/PAGE_BUDGET/);
 const {env}=fixture();env.FINANCIAL_API.fetch=async()=>Response.json({error:{code:'MATERIALIZATION_REQUIRED'}},{status:202});
 await assert.rejects(queryRoute(env,url({action:'financials',symbol:'AAPL',frequency:'quarterly'}),{snapshot}),/MATERIALIZATION_REQUIRED/);
});
