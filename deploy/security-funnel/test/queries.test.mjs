import assert from 'node:assert/strict';
import {requestQuery,priceGrowth} from '../queries.mjs';
const symbols={AAPL:0,MSFT:0,ON:1,A:1};
assert.equal(requestQuery("What was AAPL's price on 2020-01-02?",symbols).symbol,'AAPL');
assert.equal(requestQuery('AAPL growth from 2010-01-04 to 2020-01-02',symbols).action,'growth');
assert.throws(()=>requestQuery('AAPL price on 2020-02-30',symbols),/INVALID_DATE/);
assert.throws(()=>requestQuery('AAPL MSFT price on 2020-01-02',symbols),/ONE_TICKER/);
const result=priceGrowth({date:'2020-01-01',split_adjusted_price:50},{date:'2021-01-01',split_adjusted_price:100},'split_adjusted_price');
assert.equal(result.change,1);assert.equal(result.includes_dividends,false);
assert.throws(()=>priceGrowth({date:'2020-01-01',split_adjusted_price:null},{date:'2021-01-01',split_adjusted_price:100},'split_adjusted_price'),/MISSING/);
assert.throws(()=>priceGrowth({date:'2021-01-01',split_adjusted_price:50},{date:'2020-01-01',split_adjusted_price:100},'split_adjusted_price'),/PRECEDE/);

const {queryRoute}=await import('../queries.mjs');
const {FULL}=await import('../history.mjs');
const {createHash}=await import('node:crypto');
const packet={observations:[{metric:'revenue',period_end:'2025-12-31',period_start:'2025-01-01',value_decimal:'100',unit:'USD',available_at:'2026-02-01',source_observation_ids:['rev']},{metric:'operating_income',period_end:'2025-12-31',period_start:'2025-01-01',value_decimal:'20',unit:'USD',available_at:'2026-02-01',source_observation_ids:['income']}],source_records:{rev:{},income:{}}};
const raw=JSON.stringify(packet),sha=createHash('sha256').update(raw).digest('hex');
const db=new Map([[FULL+'symbol-batches.json',JSON.stringify({PEP:0})],[FULL+'batches/0.json',JSON.stringify({rows:[{symbol:'PEP',identity:{cik:'0000000001'},valuation:{inputs:{key:'stored',sha256:sha}}}]})],['stored',raw]]);
const env={DATA:{get:async key=>{const value=db.get(key);return value?{size:value.length,text:async()=>value}:null;}}};
const margin=await queryRoute(env,new URL('https://internal/query?query=PEP+operating+margin'));
assert.equal(margin.result.observations[0].value_decimal,'0.2');
assert.deepEqual(margin.result.observations[0].source_observation_ids,['income','rev']);
assert.equal(margin.result.observations[0].derivation.components.length,2);
const source=JSON.parse(db.get(FULL+'batches/0.json'));source.rows[0].valuation.inputs={};db.set(FULL+'batches/0.json',JSON.stringify(source));
const calls=[];env.FINANCIAL_API={fetch:async request=>{const url=new URL(request.url);calls.push(url);return Response.json({observations:[],source_records:{},pagination:{next_cursor:url.searchParams.get('date_from')==='1900-01-01'&&!url.searchParams.has('cursor')?'next':null}});}};
await queryRoute(env,new URL('https://internal/query?query=PEP+revenue'));
assert.equal(calls.length,3);assert.equal(calls.at(-1).searchParams.get('date_to'),'2026-09-24');
assert.ok(calls.every(url=>url.searchParams.has('release_id')));

const {companyAliases,revenueGrowth}=await import('../queries.mjs');
const aliases=companyAliases({AAPL:[{name:'Apple Inc.'}],MSFT:[{name:'Microsoft Corporation'}]});
assert.equal(requestQuery('Apple revenue growth',symbols,aliases).metric,'revenue_growth');
assert.equal(requestQuery("What was Microsoft's revenue growth?",symbols,aliases).symbol,'MSFT');
assert.equal(requestQuery('AAPL revenue growth',symbols).metric,'revenue_growth');
const annual=[{metric:'revenue',period_start:'2024-01-01',period_end:'2024-12-31',value_decimal:'100',unit:'USD',source_observation_ids:['prior']},{metric:'revenue',period_start:'2025-01-01',period_end:'2025-12-31',value_decimal:'110',unit:'USD',source_observation_ids:['current']}];
const computed=revenueGrowth(annual);assert.ok(Math.abs(Number(computed.observations[0].value_decimal)-0.1)<1e-12);assert.deepEqual(computed.observations[0].source_observation_ids,['prior','current']);
assert.equal(revenueGrowth([annual[0],{...annual[1],period_start:'2026-01-01',period_end:'2026-12-31'}]).gaps.length,1);
assert.equal(revenueGrowth([annual[0],{...annual[1],value_decimal:null}]).observations.length,0);
assert.throws(()=>revenueGrowth([annual[0],annual[0]]),/AMBIGUOUS/);
assert.equal(requestQuery('How has Apple revenue growth changed?',{...symbols,HAS:0},aliases).symbol,'AAPL');
assert.equal(requestQuery('$HAS revenue growth',{...symbols,HAS:0},aliases).symbol,'HAS');
assert.throws(()=>requestQuery('AAPL Microsoft revenue growth',symbols,aliases),/ONE_TICKER/);
assert.deepEqual(requestQuery('Apple revenue growth in 2025',symbols,aliases).dates,['2025-01-01','2025-12-31']);
// Two named companies must not silently resolve to whichever name is longest.
assert.throws(()=>requestQuery('Apple and Microsoft revenue 2025',symbols,aliases),/ONE_TICKER/);
assert.equal(requestQuery('Apple revenue growth',symbols,aliases).symbol,'AAPL');
// A shorter alias captured inside a longer company name is not a second company.
const nested=companyAliases({AAPL:[{name:'Apple Inc.'}],APLE:[{name:'Apple Hospitality REIT'}],MSFT:[{name:'Microsoft Corporation'}]});
assert.equal(requestQuery('Apple Hospitality REIT revenue 2025',{...symbols,APLE:1},nested).symbol,'APLE');
// An unknown ticker must name the stored universe instead of leaving the caller to guess coverage.
assert.throws(()=>requestQuery('$ZZZZ revenue',symbols),/UNKNOWN_TICKER.*4 symbols/s);
assert.equal(requestQuery('$HAS revenue',{...symbols,HAS:0}).symbol,'HAS');
// Quarterly and TTM questions must retain their frequency; fiscal quarter labels stay explicit.
assert.equal(requestQuery('AAPL quarterly revenue 2025',symbols).frequency,'quarterly');
assert.throws(()=>requestQuery('AAPL revenue Q1 2025',symbols),/EXACT_PERIOD_RANGE/);
assert.equal(requestQuery('AAPL TTM revenue',symbols).frequency,'ttm');
// A bare year is not an exact trading session; it must not serve the latest close.
assert.throws(()=>requestQuery('AAPL price 2025',symbols),/EXACT_SESSION_DATE/);
assert.throws(()=>requestQuery('AAPL return 2025',symbols),/EXACT_SESSION_DATE/);
assert.equal(requestQuery('AAPL price today',symbols).action,'latest_price');
const growthPacket={observations:annual,source_records:{prior:{},current:{}}},growthRaw=JSON.stringify(growthPacket),growthSha=createHash('sha256').update(growthRaw).digest('hex');
source.rows[0].valuation.inputs={key:'growth',sha256:growthSha};db.set(FULL+'batches/0.json',JSON.stringify(source));db.set('growth',growthRaw);
const requestedYear=await queryRoute(env,new URL('https://internal/query?query=PEP+revenue+growth+in+2025'));
assert.equal(requestedYear.result.observations.length,1);assert.equal(requestedYear.result.observations[0].prior_period_end,'2024-12-31');
const {dailyQuote}=await import('../queries.mjs');
assert.equal(requestQuery('AAPL price',symbols).action,'latest_price');
assert.equal(requestQuery('What is the latest Apple price?',symbols,aliases).action,'latest_price');
assert.throws(()=>requestQuery('Apple price growth',symbols,aliases),/DATE/);
const pointer={session:'2026-10-20',data_key:'synthetic',sha256:'synthetic'},daily={session:'2026-10-20',provider:'fixture',bars:[{provider_symbol:'AAPL',session_date:'2026-10-20',close:'100.5',security_id:'fixture-source'}]};
assert.equal(dailyQuote(pointer,daily,'AAPL').price,100.5);
assert.throws(()=>dailyQuote(pointer,daily,'AAPL','2026-10-19'),/REQUESTED_DATE/);
assert.throws(()=>dailyQuote(pointer,{...daily,bars:[{...daily.bars[0],close:null}]},'AAPL'),/MISSING/);
assert.throws(()=>dailyQuote(pointer,{...daily,bars:[...daily.bars,...daily.bars]},'AAPL'),/AMBIGUOUS/);
assert.throws(()=>dailyQuote(pointer,{...daily,session:'2026-10-19'},'AAPL'),/MISMATCH/);

// A missing metric must name its stored-data cause instead of implying an empty range.
const coverDb=new Map(),putCover=(key,value)=>coverDb.set(key,value);
const coverEnv={DATA:{get:async key=>{const value=coverDb.get(key);return value?{size:value.length,text:async()=>value}:null;}}};
const coverRow=(row)=>{const raw=JSON.stringify(row),sha256=createHash('sha256').update(raw).digest('hex');putCover(FULL+'symbol-batches.json',JSON.stringify({WMT:0}));putCover(FULL+'batches/0.json',JSON.stringify({rows:[{symbol:'WMT',identity:{cik:'0000000002'},financials:{cloud:row.cloud},valuation:{inputs:{key:'wmt',sha256,date_min:row.date_min,date_max:row.date_max}}}]}));putCover('wmt',raw);};
coverRow({cloud:{status:'CLOUD_HISTORY_VERIFIED',annual_metrics_available:['assets','cash'],coverage_gap_reasons:['REVENUE_CONCEPT_NOT_MAPPED']},date_min:'2008-01-31',date_max:'2026-07-31',observations:[{metric:'assets',period_start:'2025-01-01',period_end:'2025-12-31',value_decimal:'100',unit:'USD',available_at:'2026-02-01',source_observation_ids:['a']}],source_records:{a:{}}});
const uncovered=await queryRoute(coverEnv,new URL('https://internal/query?query=WMT+revenue+2025'));
assert.equal(uncovered.result.coverage.reason,'METRIC_NOT_REPORTED_BY_ISSUER');
assert.match(uncovered.answer,/without a revenue observation/);assert.match(uncovered.answer,/REVENUE_CONCEPT_NOT_MAPPED/);
assert.match(uncovered.answer,/not an unknown company/);assert.equal(uncovered.source.coverage_status,'METRIC_NOT_REPORTED_BY_ISSUER');
coverRow({cloud:{status:'CLOUD_HISTORY_EMPTY'},date_min:null,date_max:null,observations:[],source_records:{}});
assert.equal((await queryRoute(coverEnv,new URL('https://internal/query?query=WMT+revenue'))).result.coverage.reason,'NO_STORED_ANNUAL_OBSERVATIONS');
coverRow({cloud:{status:'CLOUD_HISTORY_VERIFIED',annual_metrics_available:['assets']},date_min:'2008-01-31',date_max:'2026-07-31',observations:[{metric:'assets',period_start:'2025-01-01',period_end:'2025-12-31',value_decimal:'100',unit:'USD',available_at:'2026-02-01',source_observation_ids:['a']}],source_records:{a:{}}});
const outsideRange=await queryRoute(coverEnv,new URL('https://internal/query?query=WMT+revenue+2001'));
assert.equal(outsideRange.result.coverage.reason,'REQUESTED_RANGE_OUTSIDE_STORED_COVERAGE');assert.match(outsideRange.answer,/2008-01-31 to 2026-07-31/);

const liveRaw=JSON.stringify({session:'2026-10-21',provider:'alpaca',feed:'sip',bars:[{provider_symbol:'PEP',session_date:'2026-10-21',close:'50.25',security_id:'live-source'}]});
const liveSha=createHash('sha256').update(liveRaw).digest('hex'),liveKey='gold/daily-prices/releases/'+liveSha+'/data.json';
db.set('control/daily-prices/CURRENT.json',JSON.stringify({version:liveSha,sha256:liveSha,session:'2026-10-21',data_key:liveKey}));
db.set(liveKey,liveRaw);
const live=await queryRoute(env,new URL('https://internal/query?query=PEP+price'));
assert.equal(live.result.price,50.25);assert.equal(live.result.date,'2026-10-21');assert.equal(live.source.release,liveSha);
assert.ok(!live.warnings.some(w=>/may be older/.test(w)));
db.set('control/daily-prices/CURRENT.json',JSON.stringify({version:'0'.repeat(64),sha256:liveSha,session:'2026-10-21',data_key:liveKey}));
await assert.rejects(queryRoute(env,new URL('https://internal/query?query=PEP+price')),/LATEST_PRICE_REFERENCE_INVALID/);
db.delete('control/daily-prices/CURRENT.json');


// A stored materialization must not hide a promoted canonical financial release.
const canonical='f'.repeat(64);let canonicalCalls=0;
const promoted={...env,TOKEN:'test',FINANCIAL_API:{fetch:async request=>{
 const url=new URL(request.url);assert.equal(url.searchParams.get('release_id'),canonical);
 assert.equal(request.headers.get('x-zion-bundle-id'),'a'.repeat(64));canonicalCalls++;
 return Response.json({observations:url.searchParams.get('date_from')==='2000-01-01'?packet.observations:[],source_records:packet.source_records,coverage_gaps:[]});
}}};
const promotedAnswer=await queryRoute(promoted,new URL('https://internal/query?query=PEP+revenue+2025'),{snapshot:{bundle_id:'a'.repeat(64),source_releases:{SEC_ENGINE_MANIFEST_KEY:canonical}}});
assert.equal(canonicalCalls,2);assert.equal(promotedAnswer.source.release,canonical);
assert.equal(promotedAnswer.result.observations[0].value_decimal,'100');
