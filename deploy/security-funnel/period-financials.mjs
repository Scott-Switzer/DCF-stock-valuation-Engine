import {boundedSourceJson} from './source-json.mjs';
const fail=code=>{throw Error(code);};
const number=value=>typeof value==='string'&&/^-?\d+(?:\.\d+)?$/.test(value)?Number(value):NaN;
// Quarter validation, TTM construction and revision selection belong to the native
// SEC engine. This adapter only paginates its results and aligns margin components.
export async function periodFinancials(env,parsed,cik,snapshot){
 if(parsed.metric==='revenue_growth')fail('NON_ANNUAL_GROWTH_UNSUPPORTED: Choose annual growth; quarterly comparisons need an explicit comparison policy.');
 const release=snapshot?.source_releases?.SEC_ENGINE_MANIFEST_KEY;
 if(!snapshot?.bundle_id||!/^[a-f0-9]{64}$/.test(release||''))fail('BUNDLE_UNAVAILABLE');
 const url=new URL('https://zion.internal/private/v1/financial-history');
 for(const [key,value]of Object.entries({cik,frequency:parsed.frequency,metrics:parsed.metric==='operating_margin'?'revenue,operating_income':'revenue',release_id:release,materialized_only:'true',limit:'500'}))url.searchParams.set(key,value);
 if(parsed.dates.length){url.searchParams.set('date_from',parsed.dates[0]);url.searchParams.set('date_to',parsed.dates[1]);}
 let data=null;const cursors=new Set(),deadline=Date.now()+35000;
 for(let pageNumber=0;pageNumber<8;pageNumber++){
  const left=deadline-Date.now();if(left<=0)fail('FINANCIAL_QUERY_DEADLINE');
  const response=await env.FINANCIAL_API.fetch(new Request(url,{headers:{Authorization:'Bearer '+env.TOKEN,'x-zion-bundle-id':snapshot.bundle_id},signal:AbortSignal.timeout(Math.min(left,20000))}));
  const page=await boundedSourceJson(response,2*1048576);
  if(response.status!==200)fail(page.error?.code||'STORED_FINANCIALS_UNAVAILABLE');
  if(page.bundle_id!==snapshot.bundle_id||page.provenance?.release_id!==release||page.cik!==cik||page.frequency!==parsed.frequency)fail('FINANCIAL_SOURCE_MISMATCH');
  if(!Array.isArray(page.observations)||!Array.isArray(page.coverage_gaps)||!Array.isArray(page.accounting_checks)||!page.source_records||!page.pagination)fail('FINANCIAL_RESPONSE_INVALID');
  for(const r of page.observations){
   if(r.frequency!==parsed.frequency||!Array.isArray(r.source_observation_ids)||!r.source_observation_ids.length||r.source_observation_ids.some(id=>!Object.hasOwn(page.source_records,id)))fail('FINANCIAL_LINEAGE_MISSING');
  }
  if(!data)data={...page,observations:[],coverage_gaps:[],accounting_checks:[],source_records:{}};
  if(page.as_of!==data.as_of||JSON.stringify(page.provenance)!==JSON.stringify(data.provenance))fail('FINANCIAL_SOURCE_MISMATCH');
  data.observations.push(...page.observations);data.coverage_gaps.push(...page.coverage_gaps);data.accounting_checks.push(...page.accounting_checks);
  for(const [id,record]of Object.entries(page.source_records)){
   if(Object.hasOwn(data.source_records,id)&&JSON.stringify(data.source_records[id])!==JSON.stringify(record))fail('FINANCIAL_SOURCE_MISMATCH');
   data.source_records[id]=record;
  }
  if(new TextEncoder().encode(JSON.stringify(data)).length>1800000)fail('FINANCIAL_RESPONSE_BUDGET: Narrow the date range.');
  const cursor=page.pagination.next_cursor;
  if(!cursor){delete data.pagination;break;}
  if(typeof cursor!=='string'||cursor.length>2048||cursors.has(cursor)||pageNumber===7)fail('FINANCIAL_PAGE_BUDGET: Narrow the date range.');
  cursors.add(cursor);url.searchParams.set('cursor',cursor);
 }
 const all=data.observations,revenues=all.filter(r=>r.metric==='revenue'),gaps=[];
 let observations=revenues;
 if(new Set(all.map(r=>[r.metric,r.period_start,r.period_end].join('|'))).size!==all.length)fail('AMBIGUOUS_FINANCIAL_PERIODS');
 if(parsed.metric==='operating_margin')observations=revenues.flatMap(r=>{
  const income=all.find(i=>i.metric==='operating_income'&&i.period_start===r.period_start&&i.period_end===r.period_end);
  const revenue=number(r.value_decimal),profit=number(income?.value_decimal);
  if(!income||!r.unit||income.unit!==r.unit||!Number.isFinite(revenue)||revenue<=0||!Number.isFinite(profit)||!Number.isFinite(profit/revenue)){
   gaps.push({period_end:r.period_end,reason:'MARGIN_COMPONENTS_NOT_COMPARABLE'});return [];
  }
  return [{metric:'operating_margin',frequency:parsed.frequency,period_start:r.period_start,period_end:r.period_end,value_decimal:String(profit/revenue),unit:'ratio',available_at:[r.available_at,income.available_at].sort().at(-1),derivation:{formula:'operating_income / revenue',components:[income,r]},source_observation_ids:[...new Set([...income.source_observation_ids,...r.source_observation_ids])]}];
 });
 observations.sort((a,b)=>a.period_end.localeCompare(b.period_end));
 const label=parsed.frequency==='ttm'?'TTM':'quarterly';
 const lines=observations.slice(-15).map(r=>`${r.period_end}: ${r.unit==='ratio'?(Number(r.value_decimal)*100).toFixed(2)+'%':Number(r.value_decimal).toLocaleString('en-US')+' '+r.unit}`);
 const warnings=['Stored public SEC source only; native period validation and availability rules apply. Source coverage is not full financial certification.'];
 if(!parsed.dates.length)warnings.push('No date range supplied: the source defaults start at 2015-01-01 or its later minimum and end at the company source cutoff. Supply explicit dates for older history.');
 if(observations.length>15)warnings.push(`Showing the latest 15 of ${observations.length} returned observations.`);
 if(!observations.length)warnings.push('No comparable observations exist for this request; native coverage gaps and calculation gaps are retained.');
 if(gaps.length)warnings.push('Some margins could not be computed; explicit calculation gaps are included.');
 const result={world:'real/us-public-markets',symbol:parsed.symbol,action:'financials',complete_valuation:false,bundle_id:snapshot.bundle_id,
  answer:lines.length?`${parsed.symbol} ${label} ${parsed.metric.replaceAll('_',' ')}:\n${lines.join('\n')}`:`No ${label} ${parsed.metric.replaceAll('_',' ')} observations are available for ${parsed.symbol}. See the explicit coverage gaps.`,
  result:{...data,observations,calculation_gaps:gaps,request:{frequency:parsed.frequency,date_from:parsed.dates[0]||null,date_to:parsed.dates[1]||null}},
  source:{provider:'SEC',release,cik,source_cutoff:data.provenance.company_maximum_as_of||null},warnings};
 if(new TextEncoder().encode(JSON.stringify(result)).length>1900000)fail('FINANCIAL_RESPONSE_BUDGET: Narrow the date range.');
 return result;
}
