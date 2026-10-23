import {test} from 'node:test';
import assert from 'node:assert/strict';
import {structuredQuery,queryInput} from '../query-input.mjs';
import {queryRoute} from '../queries.mjs';
const symbols={A:0,ON:1,AAPL:2};
const url=value=>new URL('https://internal/query?'+new URLSearchParams({request:JSON.stringify(value)}));
test('structured requests resolve explicit symbols without natural-language ambiguity',()=>{
 assert.deepEqual(structuredQuery({action:'price',symbol:'on',date:'2020-01-02'},symbols),{action:'price',symbol:'ON',dates:['2020-01-02'],basis:'raw_observed_price'});
 assert.equal(structuredQuery({action:'price',symbol:'A'},symbols).action,'latest_price');
 assert.equal(structuredQuery({action:'financials',symbol:'AAPL',metric:'operating_margin',date_from:'2024-01-01',date_to:'2025-12-31'},symbols).metric,'operating_margin');
});
test('unsupported or contradictory fields cannot silently widen the query',()=>{
 for(const request of [
  {action:['price'],symbol:'AAPL'},
  {action:'toString',symbol:'AAPL'},
  {action:'price',symbol:'AAPL',date:'2025-02-30'},
  {action:'price',symbol:'AAPL',date_from:'2025-01-01'},
  {action:'price',symbol:'AAPL',basis:'split_adjusted_price'},
  {action:'financials',symbol:'AAPL',metric:'secret'},
  {action:'financials',symbol:'AAPL',date_from:'2025-01-01'},
  {action:'growth',symbol:'AAPL',date_from:'2025-01-01',date_to:'2025-01-01'},
  {action:'growth',symbol:'AAPL',date_from:'2025-01-01',date_to:'2024-01-01'},
  {action:'price',symbol:'UNKNOWN'},
  {action:'price',symbol:'AAPL',sql:'SELECT *'},
  {action:'dataset_catalog',search:'comp',offset:-1},
  {action:'dataset_catalog',search:'comp',limit:51},
  {action:'dataset_catalog',search:'comp',offset:'50'},
 ])assert.throws(()=>structuredQuery(request,symbols));
 for(const search of ['','query=AAPL+price&request=%7B%7D','request=%7B','query=x&query=y','request=null'])assert.throws(()=>queryInput(new URL('https://internal/query?'+search)));
});
test('catalog pagination reuses the existing route and only returns metadata',async()=>{
 const release='c'.repeat(64),bundle='a'.repeat(64);let fetched=false;
 const env={TOKEN:'fixture',DATA:{get:async()=>assert.fail('no company lookup for catalog')},FINANCIAL_API:{fetch:async request=>{
  fetched=true;const u=new URL(request.url);assert.equal(u.pathname,'/private/v1/datasets/catalog');
  assert.equal(u.searchParams.get('offset'),'50');assert.equal(u.searchParams.get('limit'),'10');assert.equal(u.searchParams.get('search'),'comp');
  return Response.json({release_id:release,registered_releases:75,unique_datasets:75,matching_releases:65,next_offset:60,entries:[{id:'fixture',dataset:'comp__funda',raw_records:['forbidden']}]},{headers:{'x-zion-bundle-id':bundle}});
 }}};
 const result=await queryRoute(env,url({action:'dataset_catalog',search:'comp',offset:50,limit:10}),{snapshot:{bundle_id:bundle,source_releases:{COLLECTION_CATALOG_KEY:release}}});
 assert.ok(fetched);assert.equal(result.result.offset,50);assert.equal(result.result.next_offset,60);assert.equal(result.result.entries[0].raw_records,undefined);
});
