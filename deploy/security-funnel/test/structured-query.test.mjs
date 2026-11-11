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
  {action:'dataset_catalog',search:null,limit:null},
  {action:'financials',symbol:'AAPL',metric:null},
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

test('total return chains stored CRSP returns and keeps the price comparison explicit',async()=>{
 const {FULL}=await import('../history.mjs');
 const {delistingRecord}=await import('../history.mjs');
 const rows=[{date:'2020-01-02',split_adjusted_price:100,source_total_return:null,dlydelflg:'N'},
  {date:'2020-06-30',split_adjusted_price:105,source_total_return:0.07,dlydelflg:'N'},
  {date:'2020-12-31',split_adjusted_price:110,source_total_return:1.15/1.07-1,dlydelflg:'N'}];
 const db=new Map([[FULL+'symbol-batches.json',JSON.stringify({PEP:0})],
  [FULL+'batches/0.json',JSON.stringify({rows:[{symbol:'PEP',identity:{cik:'0000000001'},full_history:{security_id:'CRSP:PERMNO:12345',permno:12345,date_min:'2020-01-02',date_max:'2020-12-31',rows:3}}]})]]);
 const env={DATA:{get:async key=>{const value=db.get(key);return value?{size:value.length,text:async()=>value}:null;}}};
 const dependencies={seriesRows:async()=>({rows,input_sha256:'e'.repeat(64),parts:1}),delistingsIndex:async()=>({summary:{entries_sha256:'f'.repeat(64)},source:{object:{sha256:'d'.repeat(64)}},entries:{}})};
 const result=await queryRoute(env,url({action:'total_return',symbol:'PEP',date_from:'2020-01-02',date_to:'2020-12-31'}),dependencies);
 assert.equal(result.action,'total_return');
 assert.ok(Math.abs(result.result.summary.total_return-0.15)<1e-12);
 assert.ok(Math.abs(result.result.summary.price_growth-0.10)<1e-12);
 assert.ok(Math.abs(result.result.summary.dividend_contribution-(1.15/1.10-1))<1e-12);
 assert.equal(result.result.series_included,true);
 assert.equal(result.result.series.length,3);
 assert.match(result.answer,/Split-adjusted price growth over the same window/);
 assert.equal(result.source.release,'e'.repeat(64));
 assert.equal(result.source.permno,12345);
 const summaryOnly=await queryRoute(env,url({action:'total_return',symbol:'PEP',date_from:'2020-01-02',date_to:'2020-12-31',include_series:false}),dependencies);
 assert.equal(summaryOnly.result.series,undefined);
 assert.equal(summaryOnly.result.series_included,false);
 assert.equal(delistingRecord({entries:{12345:['2020-12-31',233,0.003628,0.003628]}},12345).code,233);
 assert.equal(delistingRecord({entries:{}},12345),null);
});

test('a delisting window reports the source-applied return and never re-adds it',async()=>{
 const {FULL}=await import('../history.mjs');
 const db=new Map([[FULL+'symbol-batches.json',JSON.stringify({PEP:0})],
  [FULL+'batches/0.json',JSON.stringify({rows:[{symbol:'PEP',identity:{cik:'0000000001'},full_history:{permno:12345,date_min:'2010-01-04',date_max:'2010-12-01',rows:3}}]})]]);
 const env={DATA:{get:async key=>{const value=db.get(key);return value?{size:value.length,text:async()=>value}:null;}}};
 const rows=[{date:'2010-01-04',split_adjusted_price:20,source_total_return:null,dlydelflg:'N'},
  {date:'2010-11-30',split_adjusted_price:20.95,source_total_return:0.000956,dlydelflg:'N'},
  {date:'2010-12-01',split_adjusted_price:null,source_total_return:0.003628,dlydelflg:'Y'}];
 const dependencies={seriesRows:async()=>({rows,input_sha256:'e'.repeat(64),parts:1}),
  delistingsIndex:async()=>({summary:{entries_sha256:'f'.repeat(64)},source:{object:{sha256:'d'.repeat(64)}},entries:{12345:['2010-11-30',233,0.003628,0.003628]}})};
 const result=await queryRoute(env,url({action:'total_return',symbol:'PEP',date_from:'2010-01-04',date_to:'2010-12-01'}),dependencies);
 assert.equal(result.result.delisting.status,'DELISTING_RETURN_INCLUDED_IN_SOURCE_TOTAL_RETURN');
 assert.equal(result.result.delisting.cross_check,'MATCH_OR_NOT_RECORDED');
 assert.ok(Math.abs(result.result.summary.total_return-((1.000956*1.003628)-1))<1e-12);
 assert.match(result.answer,/applied once/);
 assert.equal(result.source.delisting_source_sha256,'d'.repeat(64));
});

test('total return input rejects widening fields and impossible points',async()=>{
 for(const request of [
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02'},
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02',date_to:'2020-01-02'},
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02',date_to:'2020-12-31',basis:'raw_observed_price'},
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02',date_to:'2020-12-31',max_points:1},
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02',date_to:'2020-12-31',max_points:5001},
  {action:'total_return',symbol:'AAPL',date_from:'2020-01-02',date_to:'2020-12-31',include_series:'yes'},
 ])assert.throws(()=>structuredQuery(request,symbols));
 const {requestQuery}=await import('../queries.mjs');
 assert.equal(requestQuery('AAPL total return from 2020-01-02 to 2020-12-31',symbols).action,'total_return');
 assert.equal(requestQuery('AAPL dividend-adjusted return from 2020-01-02 to 2020-12-31',symbols).action,'total_return');
 assert.throws(()=>requestQuery('AAPL total return',symbols),/TOTAL_RETURN_NEEDS_TWO_SESSIONS/);
 assert.throws(()=>requestQuery('AAPL total return from 2020-12-31 to 2020-01-02',symbols),/INVALID_DATE_RANGE|START_MUST_PRECEDE_END/);
});

test('repeated JSON fields including escaped spellings are rejected',()=>{
 for(const raw of ['{"action":"price","symbol":"AAPL","symbol":"ON"}', '{"action":"price","symbol":"AAPL","sym\\u0062ol":"ON"}']){
  assert.throws(()=>queryInput(new URL('https://internal/query?'+new URLSearchParams({request:raw}))),/Repeated JSON field/);
 }
});
