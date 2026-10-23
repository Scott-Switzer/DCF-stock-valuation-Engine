// One financial query implementation for Slack, the terminal and the website.
import {FULL,historyRoute} from './history.mjs';
import {ENRICH} from './enrichment.mjs';
// Stable machine codes stay first so clients can branch on them; the sentence after
// the colon is what a website, Slack or MCP caller shows the person who asked.
const HINTS={
 INVALID_QUESTION:'Enter a financial question of at most 2,000 characters.',
 UNKNOWN_TICKER:'That ticker is not in the stored universe. Use a covered US symbol or a company name.',
 INCLUDE_A_TICKER:'Name one covered company or ticker, for example "AAPL revenue 2025".',
 ASK_FOR_ONE_TICKER:'Ask about one company at a time.',
 INVALID_DATE:'Use a real calendar date formatted YYYY-MM-DD.',
 INVALID_DATE_RANGE:'Use one year or two dates, earliest first.',
 PRICE_NEEDS_EXACT_SESSION_DATE:'Price and return questions need an exact trading session (YYYY-MM-DD) or a start and end date; a bare year has no single close.',
 PRICE_NEEDS_ONE_DATE_OR_TWO_FOR_GROWTH:'Use one exact session date, or two dates for growth.',
 START_MUST_PRECEDE_END:'The start date must come before the end date.',
 ASK_FOR_PRICE_GROWTH_OR_FINANCIALS:'Ask for a price, price growth, revenue, revenue growth or operating margin.',
 ONLY_ANNUAL_FINANCIALS_SUPPORTED:'Stored financial history is annual; ask about a fiscal year rather than a quarter or TTM.',
 NO_UNIQUE_PRICE_ON_REQUESTED_DATE:'No unique stored close exists on that session; use an exact exchange trading day.',
 REQUESTED_DATE_NOT_IN_LATEST_RELEASE:'Only the latest stored session is served for recent prices; ask for that date or an older historical session.'
};
const fail=(code,detail)=>{throw Error((HINTS[code]?code+': '+HINTS[code]:code)+(detail?' '+detail:''))};
async function read(env,key,hash,max=16*1048576){const o=await env.DATA.get(key);if(!o||o.size>max)fail('DATA_UNAVAILABLE');const raw=await o.text();if(hash){const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),x=>x.toString(16).padStart(2,'0')).join('');if(actual!==hash)fail('DATA_INTEGRITY');}return JSON.parse(raw);}
export function requestQuery(query,symbols,aliases={}){
 if(typeof query!=='string'||query.length>2000)fail('INVALID_QUESTION');
 const words=query.toUpperCase().replace(/['’]S\b/g,'').match(/[A-Z0-9][A-Z0-9.-]*/g)||[];
 const stop=new Set(['A','I','ON','IN','TO','FROM','OF','AND','FOR','IT','AS','AT','BE','BY','DO','OR','SO','ALL','HAS','HAVE','HAD','HOW','WHAT','WAS','IS','ARE','THE','DOES','DID','CAN','WILL','SHOW','ME','PLEASE','ITS','THAT','THIS','AN','WITH','ABOUT','OVER','BETWEEN','TELL','RECENT','LATEST','PAST','LAST','YEAR','YEARS','ANNUAL','COMPANY','STOCK']);
 const explicit=query.match(/\$([A-Za-z][A-Za-z0-9.-]*)/g)?.map(s=>s.slice(1).toUpperCase())||[];
 const unknown=explicit.filter(s=>!Object.hasOwn(symbols,s));
 if(unknown.length)fail('UNKNOWN_TICKER',`The stored universe holds ${Object.keys(symbols).length} symbols and ${unknown.join(', ')} is not one of them.`);
 const command=/^(?:price|prices|growth|return|revenue|sales|financials|margin)\s+([A-Za-z][A-Za-z0-9.-]*)\b/i.exec(query)?.[1]?.toUpperCase();
 const matches=[...new Set([...explicit,...(command&&Object.hasOwn(symbols,command)?[command]:[]),...words.filter(w=>!stop.has(w)&&Object.hasOwn(symbols,w))])];
 {
  const normalized=companyWords(query),found=[];
  for(const [name,candidates]of Object.entries(aliases))if(name.length>=3&&(' '+normalized+' ').includes(' '+name+' '))found.push({name,candidates});
  // A shorter name contained in a longer matched name is a substring capture
  // ("apple" inside "apple hospitality"), not a second company.
  const tops=found.filter(f=>!found.some(g=>g!==f&&(' '+g.name+' ').includes(' '+f.name+' ')));
  const named=[...new Set(tops.flatMap(f=>f.candidates))];
  // Two companies named in one question must not silently resolve to one of them.
  if(named.length>1)fail('ASK_FOR_ONE_TICKER');
  if(named.length===1)matches.splice(0,matches.length,...new Set([...matches,...named]));
 }
 if(matches.length!==1)fail(matches.length?'ASK_FOR_ONE_TICKER':'INCLUDE_A_TICKER');
 // Stored financials are annual only; never answer a quarterly or TTM question with annual figures.
 if(/\b(?:quarterly|quarter|quarters|ttm|trailing)\b|\bq[1-4]\b/i.test(query))fail('ONLY_ANNUAL_FINANCIALS_SUPPORTED');
 const dates=query.match(/\d{4}-\d{2}-\d{2}/g)||[];
 for(const d of dates)if(!Number.isFinite(Date.parse(d))||new Date(d).toISOString().slice(0,10)!==d)fail('INVALID_DATE');
 const text=query.toLowerCase(),symbol=matches[0];
 if(!dates.length&&/\b(revenue|sales|margin|financials)\b/.test(text)){const years=query.match(/\b(?:19|20)\d{2}\b/g)||[];if(years.length===1)dates.push(years[0]+'-01-01',years[0]+'-12-31');else if(years.length===2)dates.push(years[0]+'-01-01',years[1]+'-12-31');}
 if(dates.length>2||(dates.length===2&&dates[0]>dates[1]))fail('INVALID_DATE_RANGE');
 if(/\b(revenue|sales|margin|financials|financial history)\b/.test(text))return {action:'financials',symbol,dates,metric:/margin/.test(text)?'operating_margin':/\b(growth|grew|change)\b/.test(text)?'revenue_growth':'revenue'};
 if(/\b(price|prices|return|growth|grew)\b/.test(text)){
  // A bare year is not a trading session; silently serving the latest close would misstate the date.
  if(!dates.length&&/\b(?:19|20)\d{2}\b/.test(query))fail('PRICE_NEEDS_EXACT_SESSION_DATE');
  const growthRequested=/\b(growth|return|grew|change)\b/.test(text);
  if(!dates.length&&!growthRequested)return {action:'latest_price',symbol,dates,basis:'raw_observed_price'};
  const growth=(growthRequested||/\b(between|from)\b/.test(text))&&dates.length===2;
  if(dates.length!==(growth?2:1))fail('PRICE_NEEDS_ONE_DATE_OR_TWO_FOR_GROWTH');
  if(growth&&dates[0]>=dates[1])fail('START_MUST_PRECEDE_END');
  return {action:growth?'growth':'price',symbol,dates,basis:/unadjusted|raw/.test(text)?'raw_observed_price':growth?'split_adjusted_price':'raw_observed_price'};
 }
 fail('ASK_FOR_PRICE_GROWTH_OR_FINANCIALS');
}
export function companyWords(value){return value.toLowerCase().replace(/['’]s\b/g,'').replace(/[^a-z0-9]+/g,' ').replace(/\b(incorporated|inc|corporation|corp|limited|ltd|plc)\b/g,' ').replace(/\s+/g,' ').trim();}
export function companyAliases(directory){
 const names={};for(const [symbol,rows]of Object.entries(directory||{}))for(const row of rows){if(!row.name)continue;const name=companyWords(row.name);(names[name]??=[]).push(symbol);}
 return names;
}
function reportedNumber(value){return typeof value==='string'&&/^-?\d+(?:\.\d+)?$/.test(value)?Number(value):NaN;}
export function revenueGrowth(rows){
 const ordered=[...rows].sort((a,b)=>a.period_end.localeCompare(b.period_end)),result=[],gaps=[];
 if(new Set(ordered.map(r=>r.period_end)).size!==ordered.length)fail('AMBIGUOUS_ANNUAL_REVENUE_PERIODS');
 for(let i=1;i<ordered.length;i++){
  const before=ordered[i-1],after=ordered[i],a=reportedNumber(before.value_decimal),b=reportedNumber(after.value_decimal);
  const days=r=>(Date.parse(r.period_end)-Date.parse(r.period_start))/86400000+1;
  const consecutive=(Date.parse(after.period_start)-Date.parse(before.period_end))/86400000===1;
  if(!Number.isFinite(a)||!Number.isFinite(b)||a<=0||b<0||!before.unit||before.unit!==after.unit||!consecutive||![before,after].every(r=>days(r)>=330&&days(r)<=380)){
   gaps.push({period_end:after.period_end,reason:'ANNUAL_REVENUE_NOT_COMPARABLE_OR_CONSECUTIVE'});continue;
  }
  result.push({metric:'revenue_growth',period_end:after.period_end,prior_period_end:before.period_end,value_decimal:String(b/a-1),unit:'ratio',available_at:[before.available_at,after.available_at].sort().at(-1),derivation:{formula:'current annual revenue / previous annual revenue - 1',components:[before,after]},source_observation_ids:[...new Set([...(before.source_observation_ids||[]),...(after.source_observation_ids||[])])]});
 }
 return {observations:result,gaps};
}
export function priceGrowth(first,last,basis){
 const a=first?.[basis],b=last?.[basis];
 if(typeof a!=='number'||typeof b!=='number'||!Number.isFinite(a)||!Number.isFinite(b)||a<=0||b<0)fail('PRICE_OR_ADJUSTMENT_MISSING');
 const years=(Date.parse(last.date)-Date.parse(first.date))/(365.25*86400000);
 if(years<=0)fail('START_MUST_PRECEDE_END');
 return {start_date:first.date,end_date:last.date,start_price:a,end_price:b,change:b/a-1,annualized_growth:Math.pow(b/a,1/years)-1,basis,includes_dividends:false};
}
// A missing metric is a stored-data gap, not an unknown company or an empty range.
// Say which one it is and cite the reasons already recorded on the stored row.
export function coverageExplanation(row,requested,data){
 const cloud=row.financials?.cloud||{},stored=row.valuation?.inputs||{},available=cloud.annual_metrics_available||[];
 const observed=data.observations||[],date_min=stored.date_min||null,date_max=stored.date_max||null;
 const dates=requested?.dates||[],outside=dates.length===2&&date_min&&date_max&&(dates[1]<date_min||dates[0]>date_max);
 const reason=outside?'REQUESTED_RANGE_OUTSIDE_STORED_COVERAGE':!observed.length?'NO_STORED_ANNUAL_OBSERVATIONS':'METRIC_NOT_REPORTED_BY_ISSUER';
 const parts=[];
 if(reason==='REQUESTED_RANGE_OUTSIDE_STORED_COVERAGE')parts.push(`The requested range is outside stored coverage for ${row.symbol} (${date_min} to ${date_max}).`);
 else if(reason==='NO_STORED_ANNUAL_OBSERVATIONS')parts.push(`The stored SEC release has no annual observations for ${row.symbol}${cloud.status?' ('+cloud.status+')':''}.`);
 else parts.push(`Stored annual history for ${row.symbol} covers ${date_min} to ${date_max} without a ${requested?.metric||'requested'} observation; metrics present: ${available.length?available.join(', '):'none'}.`);
 if(cloud.coverage_gap_reasons?.length)parts.push(`Source coverage gaps: ${cloud.coverage_gap_reasons.join(', ')}.`);
 parts.push(reason==='REQUESTED_RANGE_OUTSIDE_STORED_COVERAGE'?'Ask for a period inside stored coverage.':'This is a stored-data gap, not an unknown company or an empty result.');
 return {reason,date_min,date_max,cloud_status:cloud.status||null,metrics_present:available,coverage_gap_reasons:cloud.coverage_gap_reasons||[],sentence:parts.join(' ')};
}
export function dailyQuote(pointer,daily,symbol,requestedDate=null){
 const matches=(daily.bars||[]).filter(b=>(b.provider_symbol||b.symbol)===symbol);
 if(matches.length!==1)fail(matches.length?'AMBIGUOUS_LATEST_QUOTE':'NO_PRICE_IN_LATEST_STORED_RELEASE');
 const bar=matches[0],session=bar.session_date||daily.session;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(session||'')||session!==pointer.session||daily.session!==pointer.session)fail('LATEST_QUOTE_SESSION_MISMATCH');
 if(requestedDate&&requestedDate!==session)fail('REQUESTED_DATE_NOT_IN_LATEST_RELEASE');
 const price=typeof bar.close==='number'?bar.close:reportedNumber(bar.close);
 if(!Number.isFinite(price)||price<=0)fail('LATEST_PRICE_MISSING');
 return {symbol,date:session,price,basis:'SOURCE_REPORTED_CLOSE',provider:bar.provider||daily.provider,feed:bar.feed||daily.feed,source_security_id:bar.security_id||null,source_key:pointer.data_key,source_sha256:pointer.sha256};
}
// Immutable release objects cannot change under a fixed digest, so an isolate can
// reuse the parsed symbol index and company-name map instead of re-reading and
// re-hashing the SEC directory on every question.
let INDEX_CACHE=null,ALIAS_CACHE=null;
async function symbolIndex(env){
 const object=await env.DATA.get(FULL+'symbol-batches.json');
 if(!object)return null;
 const etag=object.etag||null;
 if(etag&&INDEX_CACHE?.etag===etag)return INDEX_CACHE.value;
 if(object.size>16*1048576)fail('DATA_UNAVAILABLE');
 const value=JSON.parse(await object.text());
 if(etag)INDEX_CACHE={etag,value};
 return value;
}
async function directoryAliases(env){
 const object=await env.DATA.get(ENRICH+'sec-directory-index.json');
 if(!object)return {};
 if(object.size>1048576)fail('DIRECTORY_REFERENCE_BUDGET');
 const ref=await object.json();
 if(ALIAS_CACHE?.sha256===ref.sha256)return ALIAS_CACHE.value;
 const directory=await read(env,ref.key,ref.sha256),value=companyAliases(directory.index);
 ALIAS_CACHE={sha256:ref.sha256,value};
 return value;
}
async function currentDailyPointer(env){
 const object=await env.DATA.get('control/daily-prices/CURRENT.json');
 if(!object)return null;
 if(object.size>65536)fail('LATEST_PRICE_REFERENCE_INVALID');
 const pointer=JSON.parse(await object.text()),sha=pointer.sha256;
 if(!/^[a-f0-9]{64}$/.test(sha||'')||pointer.version!==sha||pointer.data_key!==`gold/daily-prices/releases/${sha}/data.json`)fail('LATEST_PRICE_REFERENCE_INVALID');
 return {session:pointer.session,data_key:pointer.data_key,sha256:sha};
}
async function latestQuote(env,symbol,requestedDate){
 const live=await currentDailyPointer(env);
 const capabilities=live?null:await read(env,'staging/security-funnel/2026-10-20/9beaa712e71650a2/existing-capabilities.json',null,1048576);
 const pointer=live||capabilities.daily_pointer;
 if(!/^gold\/daily-prices\/releases\/[a-f0-9]{64}\/data.json$/.test(pointer.data_key||'')||!/^[a-f0-9]{64}$/.test(pointer.sha256||''))fail('LATEST_PRICE_REFERENCE_INVALID');
 const daily=await read(env,pointer.data_key,pointer.sha256,8*1048576),result=dailyQuote(pointer,daily,symbol,requestedDate);
 return {world:'real/us-public-markets',symbol,action:'latest_price',complete_valuation:false,answer:`${symbol}: $${result.price.toFixed(4)} — latest stored ${result.provider||'provider'} close, as of ${result.date}.`,result,source:{provider:result.provider,feed:result.feed,release:pointer.sha256,date:result.date,source_security_id:result.source_security_id},warnings:[live?`Latest close from the collector's current daily release pointer. Stored close, not a real-time quote. Source-native reference; no CRSP/provider history splice is implied.`:`Latest close in the connected snapshot; the collector's current pointer was unavailable, so this may be older. Stored close, not a real-time quote. Source-native reference; no CRSP/provider history splice is implied.`]};
}
export async function queryRoute(env,u,dependencies={}){
 const index=await symbolIndex(env);
 if(!index)fail('DATA_UNAVAILABLE');
 const aliases=await directoryAliases(env);
 const parsed=requestQuery(u.searchParams.get('query'),index,aliases);
 const part=await read(env,FULL+`batches/${index[parsed.symbol]}.json`),security=part.rows.find(r=>r.symbol===parsed.symbol);
 const base={world:'real/us-public-markets',symbol:parsed.symbol,action:parsed.action,complete_valuation:false};
 if(parsed.action==='latest_price')return latestQuote(env,parsed.symbol);
 if(parsed.action==='price'&&security.full_history?.date_max&&parsed.dates[0]>security.full_history.date_max)return latestQuote(env,parsed.symbol,parsed.dates[0]);
 const getHistory=dependencies.history||((url)=>historyRoute(env,url));
 if(parsed.action==='price'||parsed.action==='growth'){
  const pages=await Promise.all(parsed.dates.map(async date=>{
   const url=new URL('https://internal/history');url.searchParams.set('symbol',parsed.symbol);url.searchParams.set('date_from',date);url.searchParams.set('date_to',date);url.searchParams.set('limit','10');return getHistory(url);
  }));
  const rows=pages.map(p=>{if(p.rows.length!==1)fail('NO_UNIQUE_PRICE_ON_REQUESTED_DATE');return p.rows[0];});
  const warnings=['CRSP stored history; dates are exact trading sessions.'];
  if(parsed.action==='growth'){
   if(pages[0].permno!==pages[1].permno||pages[0].input_sha256!==pages[1].input_sha256)fail('PRICE_SERIES_CHANGED');
   const result=priceGrowth(rows[0],rows[1],parsed.basis);
   return {...base,answer:`${parsed.symbol} rose ${(result.change*100).toFixed(2)}% from ${result.start_date} to ${result.end_date} (${(result.annualized_growth*100).toFixed(2)}% annualized), using ${parsed.basis==='raw_observed_price'?'unadjusted':'split-adjusted'} prices. Dividends are excluded.`,result,warnings,source:{provider:'CRSP',release:pages[0].input_sha256,permno:pages[0].permno,coverage:pages[0].coverage}};
  }
  const value=rows[0][parsed.basis];if(typeof value!=='number'||!Number.isFinite(value))fail('PRICE_MISSING');
  return {...base,answer:`${parsed.symbol}: $${value.toFixed(4)} on ${rows[0].date} (unadjusted historical price).`,result:{date:rows[0].date,price:value,basis:parsed.basis},warnings,source:{provider:'CRSP',release:pages[0].input_sha256,permno:pages[0].permno,coverage:pages[0].coverage}};
 }
 const cik=security.identity.cik;if(!/^\d{10}$/.test(cik||''))fail('ISSUER_NOT_CONNECTED');
 let data;
 const stored=security.valuation.inputs;
 const engine=snapshot?.source_releases?.SEC_ENGINE_MANIFEST_KEY||'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb';
 if(stored?.key&&stored?.sha256){data=await read(env,stored.key,stored.sha256);}
 const materializedRelease=data?.source_release_id||data?.provenance?.release_id||'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb';
 if(!data||materializedRelease!==engine) {
  data={source_release_id:engine,observations:[],source_records:{},coverage_gaps:[],source_cutoff:'2026-09-24'};
  for(const [from,to]of [['1900-01-01','1999-12-31'],['2000-01-01','2026-09-24']]){
   const url=new URL('https://zion.internal/private/v1/financial-history');
   for(const [k,v]of Object.entries({cik,metrics:'revenue,operating_income',frequency:'annual',date_from:from,date_to:to,limit:'1000',release_id:engine}))url.searchParams.set(k,v);
   let cursor=null;
   for(let n=0;n<8;n++){
    if(cursor)url.searchParams.set('cursor',cursor);
    const response=await env.FINANCIAL_API.fetch(new Request(url,{headers:{Authorization:'Bearer '+env.TOKEN,...(snapshot?.bundle_id?{'x-zion-bundle-id':snapshot.bundle_id}:{})}}));const page=await response.json();if(response.status!==200)fail(page.error?.code||'FINANCIAL_HISTORY_NOT_MATERIALIZED');
    data.observations.push(...(page.observations||[]));Object.assign(data.source_records,page.source_records||{});data.coverage_gaps.push(...(page.coverage_gaps||[]));
    cursor=page.pagination?.next_cursor;if(!cursor)break;if(n===7)fail('FINANCIAL_HISTORY_PAGE_BUDGET');
   }
  }
 }

 const all=data.observations||[];
 const revenues=all.filter(r=>r.metric==='revenue');
 let observations=revenues.filter(r=>(!parsed.dates[0]||r.period_end>=parsed.dates[0])&&(!parsed.dates[1]||r.period_end<=parsed.dates[1]));
 if(parsed.metric==='operating_margin'){observations=observations.flatMap(r=>{
  const income=all.find(i=>i.metric==='operating_income'&&i.period_end===r.period_end&&i.period_start===r.period_start);
  const revenue=reportedNumber(r.value_decimal),profit=reportedNumber(income?.value_decimal);
  if(!income||!Number.isFinite(revenue)||revenue===0||!Number.isFinite(profit))return [];
  return [{metric:'operating_margin',period_start:r.period_start,period_end:r.period_end,value_decimal:String(profit/revenue),unit:'ratio',available_at:[r.available_at,income.available_at].sort().at(-1),derivation:{formula:'operating_income / revenue',components:[income,r]},source_observation_ids:[...new Set([...(income.source_observation_ids||[]),...(r.source_observation_ids||[])])]}];
 });}
 let growthGaps=[];
 if(parsed.metric==='revenue_growth'){const computed=revenueGrowth(revenues);observations=computed.observations.filter(r=>(!parsed.dates[0]||r.period_end>=parsed.dates[0])&&(!parsed.dates[1]||r.period_end<=parsed.dates[1]));growthGaps=computed.gaps.filter(r=>(!parsed.dates[0]||r.period_end>=parsed.dates[0])&&(!parsed.dates[1]||r.period_end<=parsed.dates[1]));}
 observations.sort((a,b)=>a.period_end.localeCompare(b.period_end));
 const lines=observations.slice(-15).map(r=>`${r.period_end}: ${r.unit==='ratio'?(Number(r.value_decimal)*100).toFixed(2)+'%':Number(r.value_decimal).toLocaleString('en-US')+' '+r.unit}`);
 const coverage=lines.length?null:coverageExplanation(security,parsed,data);
 return {...base,answer:lines.length?`${parsed.symbol} annual ${parsed.metric.replaceAll('_',' ')}${parsed.metric==='revenue_growth'?' (year over year)':''}:\n${lines.join('\n')}`:`No annual ${parsed.metric} observations are available for ${parsed.symbol} in this range. ${coverage.sentence}`,result:{...data,observations,calculation_gaps:growthGaps,...(coverage?{coverage}:{})},source:{provider:'SEC',release:data.source_release_id||data.provenance?.release_id||'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb',cik,source_cutoff:'2026-09-24',...(coverage?{coverage_status:coverage.reason}:{})},warnings:[...(observations.length>15?['Showing the latest 15 of '+observations.length+' available annual observations.']:[]),...(growthGaps.length?['Some annual growth rates could not be computed; explicit gaps are included.']:[]),...(coverage?[coverage.sentence]:[])]};
}
export async function companyPacket(env,symbol){
 if(!/^[A-Z0-9][A-Z0-9.-]{0,24}$/.test(symbol||''))fail('INVALID_SYMBOL');
 const index=await read(env,FULL+'symbol-batches.json');if(!Object.hasOwn(index,symbol))fail('UNKNOWN_SYMBOL');
 const part=await read(env,FULL+`batches/${index[symbol]}.json`),row=part.rows.find(r=>r.symbol===symbol),job=await read(env,ENRICH+'job.json');
 const task=await read(env,ENRICH+'runs/'+job.run_id+'/tasks/'+row.identity.cik+'.json');
 if(task.run_id!==job.run_id||task.runtime_version!==job.runtime_version||task.http_status!==200)fail('COMPANY_DATA_UNAVAILABLE');
 const p=task.symbols.find(p=>p.symbol===symbol);if(!p?.packet)fail('COMPANY_PACKET_UNAVAILABLE');
 return read(env,p.packet.key,p.packet.sha256);
}
