import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute} from '../queries.mjs';
import {stampedRead} from '../snapshot.mjs';
import {FULL} from '../history.mjs';

const bundle='a'.repeat(64), index='b'.repeat(64), release='c'.repeat(64);
const snapshot={bundle_id:bundle,source_releases:{daily_prices:'d'.repeat(64),daily_session_index:index}};
function fixture(change=x=>x,status=200){
 const requests=[];
 const objects={[FULL+'symbol-batches.json']:{PEP:0},[FULL+'batches/0.json']:{rows:[{symbol:'PEP',full_history:{date_max:'2025-12-31'}}]}};
 const env={TOKEN:'fixture',DATA:{get:async key=>objects[key]?{size:100,text:async()=>JSON.stringify(objects[key])}:null},FINANCIAL_API:{fetch:async request=>{
  const url=new URL(request.url);requests.push(request);
  if(url.pathname==='/private/v1/snapshot')return Response.json(snapshot);
  assert.equal(url.pathname,'/v1/market/prices/PEP');assert.equal(url.searchParams.get('session'),'2026-10-21');
  assert.equal(request.headers.get('x-zion-bundle-id'),bundle);
  assert.equal(request.headers.get('Authorization'),'Bearer fixture');
  return Response.json(change({bundle_id:bundle,source_releases:snapshot.source_releases,release:{market_release_id:release,sha256:release,data_key:`gold/daily-prices/releases/${release}/data.json`,session:'2026-10-21',provider:'alpaca',feed:'sip'},coverage:{index_status:'SESSION_INDEX_VERIFIED',session_index_key:`control/daily-prices/sessions/${index}.json`,point_in_time_status:'NOT_ESTABLISHED'},data:{prices:[{provider_symbol:'PEP',symbol:'PEP',session_date:'2026-10-21',close:'50.25',security_id:'fixture'}]}}),{status});
 }}};
 return {env,requests};
}
const url=new URL('https://internal/query?query=PEP+price+2026-10-21');
test('prior daily session flows through the source and shared bundle boundary',async()=>{
 const {env,requests}=fixture();
 const answer=await stampedRead(env,bundle,s=>queryRoute(env,url,{snapshot:s}));
 assert.equal(answer.action,'price');assert.equal(answer.result.price,50.25);
 assert.equal(answer.data_as_of,'2026-10-21');assert.equal(answer.source.release,release);
 assert.equal(answer.source.session_index_sha256,index);assert.equal(answer.bundle_id,bundle);
 assert.doesNotMatch(answer.answer,/latest/);assert.equal(requests.length,3);
});
test('no substitution on missing sessions, malformed data, or mismatched provenance',async()=>{
 for(const mutate of [x=>({...x,bundle_id:'e'.repeat(64)}),x=>({...x,data:{prices:[]}}),x=>({...x,coverage:{...x.coverage,session_index_key:'wrong'}}),x=>({...x,release:{...x.release,session:'2026-10-20'}}),x=>({...x,data:{prices:[{...x.data.prices[0],close:null}]}})]){
  const {env}=fixture(mutate);await assert.rejects(()=>stampedRead(env,bundle,s=>queryRoute(env,url,{snapshot:s})));
 }
 const {env}=fixture(()=>({error:{code:'SESSION_NOT_INDEXED'}}),503);
 await assert.rejects(()=>queryRoute(env,url,{snapshot}),/SESSION_NOT_INDEXED/);
});
test('unlisted sources still fail without a verified session-index chain',async()=>{
 const {env}=fixture();
 await assert.rejects(()=>stampedRead(env,bundle,async()=>({source:{release,session_index_sha256:index}})),/RELEASE_MISMATCH/);
 await assert.rejects(()=>stampedRead(env,bundle,async()=>({bundle_id:bundle,source:{release,session_index_sha256:'f'.repeat(64)}})),/RELEASE_MISMATCH/);
});
