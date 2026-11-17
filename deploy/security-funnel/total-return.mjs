// CRSP daily rows -> a total-return series with explicit delisting treatment.
//
// Source semantics this module is written against (verified on the materialized
// crsp-ciz-research-v1 projection, 2026-10-26):
// - source_total_return is CRSP RET as a decimal fraction (0.0123 = +1.23%).
//   The first stored row of a security has no prior close, so its return is null.
// - The delisting record carries dlydelflg='Y'. When CRSP reports a delisting
//   return, that record's RET is the delisting return itself and
//   delisting_return_present=true; the value must not be applied twice.
// - When CRSP does not report a delisting return (performance-related codes with
//   no recoverable price), the delisting record's RET is null. Chaining that as
//   zero would silently drop a total loss, so this module never substitutes a
//   value: it reports the observed chain as an upper bound and names the gap.
const DAY=86400000;
const fail=(code,detail)=>{throw Error(code+(detail?': '+detail:''))};
const finite=value=>typeof value==='number'&&Number.isFinite(value);

// CRSP delisting-code families. Only the family is asserted here; the raw code
// stays available so a caller can apply a stricter academic convention.
export function delistingFamily(code){
 if(!Number.isInteger(code)||code<100)return {family:'UNKNOWN',performance_related:false};
 if(code<200)return {family:'STILL_TRADING',performance_related:false};
 if(code<300)return {family:'MERGED',performance_related:false};
 if(code<400)return {family:'EXCHANGE',performance_related:false};
 if(code<500)return {family:'LIQUIDATION',performance_related:true};
 return {family:'DROPPED',performance_related:true};
}

function dates(rows){
 const out=rows.map(row=>row.date);
 if(out.some(date=>typeof date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(date)))fail('INVALID_SESSION_DATE');
 for(let i=1;i<out.length;i++)if(out[i]<=out[i-1])fail('SESSIONS_NOT_STRICTLY_INCREASING',out[i]);
 return out;
}

function annualized(total,years){
 if(!finite(total)||years<=0)return null;
 if(total<=-1)return -1;
 return Math.pow(1+total,1/years)-1;
}

// A caller may pass the already-read CRSP delisting record for this permno:
// {date, code, dlret, dlretx} or null when the security has no delisting record.
export function totalReturnSeries(rows,{from,to,delisting=null,maxPoints=1000}={}){
 if(!Array.isArray(rows)||rows.length<2)fail('TOTAL_RETURN_NEEDS_TWO_SESSIONS');
 const ordered=[...rows].sort((a,b)=>a.date.localeCompare(b.date));
 const sessionDates=dates(ordered);
 if(ordered[0].date!==from||ordered.at(-1).date!==to)fail('WINDOW_NOT_COVERED_BY_SESSIONS');
 const first=ordered[0],last=ordered.at(-1);

 // The window return is measured from the first row's close, so its own RET
 // (which describes the move into that close) is not applied.
 const applied=[],gaps=[];
 for(let i=1;i<ordered.length;i++){
  const row=ordered[i],ret=row.source_total_return;
  if(!finite(ret)){gaps.push({date:row.date,reason:'SOURCE_TOTAL_RETURN_MISSING'});continue;}
  if(ret<-1)fail('TOTAL_RETURN_OUT_OF_RANGE',row.date);
  applied.push({date:row.date,ret});
 }

 // Contiguous stretches of applied returns. A gap ends a segment rather than
 // being treated as a zero return.
 const segments=[];let current=null;
 for(let i=1;i<ordered.length;i++){
  const row=ordered[i],ret=row.source_total_return;
  if(!finite(ret)){current=null;continue;}
  if(!current){current={start_date:ordered[i-1].date,end_date:row.date,sessions:0,index:1};segments.push(current);}
  current.index*=1+ret;current.end_date=row.date;current.sessions++;
 }
 for(const segment of segments)segment.total_return=segment.index-1;
 const complete=gaps.length===0;
 const delistingRow=ordered.find(row=>row.dlydelflg==='Y')||null;
 // A missing return on the terminal delisting row is the one gap that still
 // yields a usable cumulative figure: it is the observed chain up to the last
 // close, an upper bound on an outcome that may be worthless. An interior gap
 // makes any single cumulative number invalid, so none is claimed.
 const terminalGap=!complete&&gaps.length===1&&gaps[0].date===last.date&&last.dlydelflg==='Y';
 const total=!complete&&!terminalGap?null:segments.length===1?segments[0].total_return:null;

 // A delisting row carries no adjusted price, so the price comparison ends at
 // the last priced session while the total return keeps the delisting return.
 const priced=[...ordered].reverse().find(row=>finite(row.split_adjusted_price)&&row.split_adjusted_price>0)||null;
 const startPrice=finite(first.split_adjusted_price)&&first.split_adjusted_price>0?first.split_adjusted_price:null;
 const priceGrowth=startPrice&&priced&&priced!==first?priced.split_adjusted_price/startPrice-1:null;
 const priceEndDate=priced?.date||null,priceComparable=Boolean(startPrice&&priced&&priceEndDate===last.date);
 const years=(Date.parse(last.date)-Date.parse(first.date))/(365.25*DAY);

 const block=delistingTreatment({delistingRow,record:delisting,last,total});

 const upperBound=block.status==='DELISTING_RETURN_NOT_OBSERVED'&&finite(total);
 const summary={
  start_date:first.date,end_date:last.date,sessions:ordered.length,returns_applied:applied.length,
  missing_return_rows:gaps.length,total_return:total,annualized_total_return:annualized(total,years),
  total_return_complete:complete,total_return_is_upper_bound:upperBound,
  bounds:upperBound&&finite(total)?{lower:block.lower_bound,upper:block.upper_bound,assumption:block.bounds_assumption}:null,
  delisting_status:block.status,
  price_growth:priceGrowth,annualized_price_growth:annualized(priceGrowth,years),price_growth_end_date:priceEndDate,
  split_adjusted_price:{start:startPrice,end:priced?.split_adjusted_price??null},
  dividend_contribution:priceComparable&&finite(total)&&priceGrowth>-1?(1+total)/(1+priceGrowth)-1:null,
  years:Number(years.toFixed(6)),
 };
 const points=pickPoints(ordered,maxPoints);
 return {summary,segments,delisting:block,gaps,series:points.rows,sampled:points.sampled};
}

// Delisting is classified from two independent records: the price row's own flag
// (what the stored return actually did) and the CRSP delisting file (why it
// happened). A reported delisting return must not be applied a second time.
function delistingTreatment({delistingRow,record,last,total}){
 const recordDate=record?.date&&/^\d{4}-\d{2}-\d{2}$/.test(record.date)?record.date:null;
 const family=delistingFamily(record?.code);
 const base={source:'CRSP_DSEDELIST',record:record?{date:recordDate,code:record.code??null,dlret:finite(record.dlret)?record.dlret:null,dlretx:finite(record.dlretx)?record.dlretx:null,...family}:null};
 if(!delistingRow){
  if(recordDate&&recordDate<=last.date)return {...base,status:'DELISTING_RECORD_OUTSIDE_STORED_SESSIONS',treatment:'NO_ADJUSTMENT_APPLIED'};
  if(recordDate)return {...base,status:'OPEN_AT_WINDOW_END',treatment:'NO_ADJUSTMENT_APPLIED'};
  return {...base,status:'NO_DELISTING_RECORD',treatment:'NOT_APPLICABLE'};
 }
 const observed=finite(delistingRow.source_total_return);
 const detail={...base,row_date:delistingRow.date,row_return:observed?delistingRow.source_total_return:null};
 if(observed){
  const crossCheck=finite(record?.dlret)&&Math.abs(record.dlret-delistingRow.source_total_return)>1e-6?'MISMATCH_ROW_VALUE_USED':'MATCH_OR_NOT_RECORDED';
  return {...detail,status:'DELISTING_RETURN_INCLUDED_IN_SOURCE_TOTAL_RETURN',
   treatment:'APPLIED_ONCE_BY_SOURCE_ROW',cross_check:crossCheck,
   note:'The stored delisting row return already contains CRSP DLRET; adding it again would double count.'};
 }
 // Unobserved delisting return: report bounds instead of inventing a value.
 const upper=finite(total)?total:null;
 const lower=upper===null?null:-1;
 return {...detail,status:'DELISTING_RETURN_NOT_OBSERVED',treatment:'NO_IMPUTATION_APPLIED',
  upper_bound:upper,lower_bound:lower,
  bounds_assumption:'A delisted position can be worth zero; the observed chain is the best case.',
  performance_related:family.performance_related,
  note:'CRSP reports no delisting return for this event. The series ends at the last observed close, so the observed total return overstates the outcome if the security was worthless.'};
}

// Evenly spaced points keep a chart honest without returning 10,000 rows; each
// point keeps the cumulative index at its own date, so the shape is unchanged.
function pickPoints(rows,maxPoints){
 if(rows.length<=maxPoints)return {rows:rows.map(point),sampled:false};
 const step=(rows.length-1)/(maxPoints-1),out=[];
 for(let i=0;i<maxPoints;i++)out.push(point(rows[Math.round(i*step)]));
 return {rows:out,sampled:true};
}
function point(row){
 return {date:row.date,split_adjusted_price:finite(row.split_adjusted_price)?row.split_adjusted_price:null,
  total_return:finite(row.source_total_return)?row.source_total_return:null};
}
