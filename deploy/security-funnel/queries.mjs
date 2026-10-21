// One financial query implementation for Slack, the terminal and the website.
import {FULL,historyRoute} from './history.mjs';
import {ENRICH} from './enrichment.mjs';
const fail=code=>{throw Error(code)};
async function read(env,key,hash){const o=await env.DATA.get(key);if(!o||o.size>16*1048576)fail('DATA_UNAVAILABLE');const raw=await o.text();if(hash){const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),x=>x.toString(16).padStart(2,'0')).join('');if(actual!==hash)fail('DATA_INTEGRITY');}return JSON.parse(raw);}
export function requestQuery(query,symbols){
 if(typeof query!=='string'||query.length>2000)fail('INVALID_QUESTION');
 const words=query.toUpperCase().replace(/['’]S\b/g,'').match(/[A-Z0-9][A-Z0-9.-]*/g)||[];
 const stop=new Set(['A','I','ON','IN','TO','FROM','OF','AND','FOR','IT','AS','AT','BE','BY','DO','OR','SO','ALL']);
 const explicit=query.match(/\$([A-Za-z][A-Za-z0-9.-]*)/g)?.map(s=>s.slice(1).toUpperCase())||[];
 const command=/^(?:price|prices|growth|return|revenue|sales|financials|margin)\s+([A-Za-z][A-Za-z0-9.-]*)\b/i.exec(query)?.[1]?.toUpperCase();
 const matches=[...new Set([...explicit,...(command&&Object.hasOwn(symbols,command)?[command]:[]),...words.filter(w=>!stop.has(w)&&Object.hasOwn(symbols,w))])];
 if(matches.length!==1)fail(matches.length?'ASK_FOR_ONE_TICKER':'INCLUDE_A_TICKER');
 const dates=query.match(/\d{4}-\d{2}-\d{2}/g)||[];
 for(const d of dates)if(!Number.isFinite(Date.parse(d))||new Date(d).toISOString().slice(0,10)!==d)fail('INVALID_DATE');
 const text=query.toLowerCase(),symbol=matches[0];
 if(/\b(revenue|sales|margin|financials|financial history)\b/.test(text))return {action:'financials',symbol,dates,metric:/margin/.test(text)?'operating_margin':'revenue'};
 if(/\b(price|prices|return|growth|grew)\b/.test(text)){
  const growth=/\b(growth|return|grew|change|between|from)\b/.test(text)&&dates.length===2;
  if(dates.length!==(growth?2:1))fail('PRICE_NEEDS_ONE_DATE_OR_TWO_FOR_GROWTH');
  if(growth&&dates[0]>=dates[1])fail('START_MUST_PRECEDE_END');
  return {action:growth?'growth':'price',symbol,dates,basis:/unadjusted|raw/.test(text)?'raw_observed_price':growth?'split_adjusted_price':'raw_observed_price'};
 }
 fail('ASK_FOR_PRICE_GROWTH_OR_FINANCIALS');
}
export function priceGrowth(first,last,basis){
 const a=first?.[basis],b=last?.[basis];
 if(typeof a!=='number'||typeof b!=='number'||!Number.isFinite(a)||!Number.isFinite(b)||a<=0||b<0)fail('PRICE_OR_ADJUSTMENT_MISSING');
 const years=(Date.parse(last.date)-Date.parse(first.date))/(365.25*86400000);
 if(years<=0)fail('START_MUST_PRECEDE_END');
 return {start_date:first.date,end_date:last.date,start_price:a,end_price:b,change:b/a-1,annualized_growth:Math.pow(b/a,1/years)-1,basis,includes_dividends:false};
}
export async function queryRoute(env,u,dependencies={}){
 const index=await read(env,FULL+'symbol-batches.json');
 const parsed=requestQuery(u.searchParams.get('query'),index),part=await read(env,FULL+`batches/${index[parsed.symbol]}.json`),security=part.rows.find(r=>r.symbol===parsed.symbol);
 const base={world:'real/us-public-markets',symbol:parsed.symbol,action:parsed.action,complete_valuation:false};
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
 if(stored?.key&&stored?.sha256){data=await read(env,stored.key,stored.sha256);}
 else {
  data={observations:[],source_records:{},coverage_gaps:[],source_cutoff:'2026-09-24'};
  for(const [from,to]of [['1900-01-01','1999-12-31'],['2000-01-01','2026-09-24']]){
   const url=new URL('https://zion.internal/private/v1/financial-history');
   for(const [k,v]of Object.entries({cik,metrics:'revenue,operating_income',frequency:'annual',date_from:from,date_to:to,limit:'1000',release_id:'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb'}))url.searchParams.set(k,v);
   let cursor=null;
   for(let n=0;n<8;n++){
    if(cursor)url.searchParams.set('cursor',cursor);
    const response=await env.FINANCIAL_API.fetch(new Request(url,{headers:{Authorization:'Bearer '+env.TOKEN}}));const page=await response.json();if(response.status!==200)fail(page.error?.code||'FINANCIAL_HISTORY_NOT_MATERIALIZED');
    data.observations.push(...(page.observations||[]));Object.assign(data.source_records,page.source_records||{});data.coverage_gaps.push(...(page.coverage_gaps||[]));
    cursor=page.pagination?.next_cursor;if(!cursor)break;if(n===7)fail('FINANCIAL_HISTORY_PAGE_BUDGET');
   }
  }
 }

 const all=data.observations||[];
 let observations=all.filter(r=>r.metric==='revenue'&&(!parsed.dates[0]||r.period_end>=parsed.dates[0])&&(!parsed.dates[1]||r.period_end<=parsed.dates[1]));
 if(parsed.metric==='operating_margin'){observations=observations.flatMap(r=>{
  const income=all.find(i=>i.metric==='operating_income'&&i.period_end===r.period_end&&i.period_start===r.period_start);
  const revenue=Number(r.value_decimal),profit=Number(income?.value_decimal);
  if(!income||!Number.isFinite(revenue)||revenue===0||!Number.isFinite(profit))return [];
  return [{metric:'operating_margin',period_start:r.period_start,period_end:r.period_end,value_decimal:String(profit/revenue),unit:'ratio',available_at:[r.available_at,income.available_at].sort().at(-1),derivation:{formula:'operating_income / revenue',components:[income,r]},source_observation_ids:[...new Set([...(income.source_observation_ids||[]),...(r.source_observation_ids||[])])]}];
 });}
 observations.sort((a,b)=>a.period_end.localeCompare(b.period_end));
 const lines=observations.slice(-15).map(r=>`${r.period_end}: ${r.value_decimal??r.value??'missing'} ${r.unit||''}`);
 return {...base,answer:lines.length?`${parsed.symbol} annual ${parsed.metric}:\n${lines.join('\n')}`:`No annual ${parsed.metric} observations are available for ${parsed.symbol} in this range.`,result:{...data,observations},source:{provider:'SEC',cik,source_cutoff:'2026-09-24'},warnings:data.next?['More observations are available; narrow the date range.']:[]};
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
