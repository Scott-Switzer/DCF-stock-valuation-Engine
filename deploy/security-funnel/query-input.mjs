import {financialCutoff} from './financial-cutoff.mjs';
// Strict input normalization shared by the existing question route. No provider calls.
const invalid=detail=>{throw Error('INVALID_REQUEST: '+detail);};
function object(value){if(!value||typeof value!=='object'||Array.isArray(value))invalid('request must be an object.');}
function fields(value,allowed){for(const key of Object.keys(value))if(!allowed.includes(key))invalid('Unsupported field: '+key);}
export function queryInput(url){
 const questions=url.searchParams.getAll('query'),requests=url.searchParams.getAll('request');
 if(questions.length+requests.length!==1)invalid('Provide exactly one query or structured request.');
 if(questions.length){if(!questions[0].trim()||questions[0].length>2000)invalid('Question must contain 1–2,000 characters.');return {question:questions[0]};}
 if(requests[0].length>4096)invalid('Structured request exceeds 4,096 characters.');
 let request;try{request=JSON.parse(requests[0]);}catch{invalid('Structured request must be valid JSON.');}
 // The contract is flat. Scan complete JSON strings so escaped key names also
 // collide; JSON.parse alone silently keeps the last repeated property.
 const keys=new Set();
 for(let i=0;i<requests[0].length;i++){
  if(requests[0][i]!==String.fromCharCode(34))continue;
  const start=i++;
  while(i<requests[0].length){if(requests[0][i]==='\\'){i+=2;continue;}if(requests[0][i]===String.fromCharCode(34))break;i++;}
  let next=i+1;while(/\s/.test(requests[0][next]||'')&&next<requests[0].length)next++;
  if(requests[0][next]===':'){const key=JSON.parse(requests[0].slice(start,i+1));if(keys.has(key))invalid('Repeated JSON field: '+key);keys.add(key);}
 }
 object(request);return {request};
}
function date(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||!Number.isFinite(Date.parse(value))||new Date(value).toISOString().slice(0,10)!==value)invalid('Use real dates formatted YYYY-MM-DD.');
 return value;
}
export function structuredQuery(value,symbols={}){
 object(value);
 if(Object.values(value).some(v=>v===null))invalid('Explicit null is not an omitted field.');
 const action=value.action;
 if(typeof action!=='string'||!['price','growth','total_return','financials','dataset_catalog','dataset_detail','dataset_schema','dataset_rows'].includes(action))invalid('Unsupported action.');
 // Licensed source archives are addressed by catalog identity plus the catalog's own
 // object key allowlist; no caller-supplied path ever reaches R2.
 const datasetId=value=>{
  const id=value??'';
  if(typeof id!=='string'||!/^[a-f0-9]{32}$/.test(id))invalid('dataset_id must be the 32-character catalog id.');
  return id;
 };
 const objectIndex=value=>{
  const index=value??0;
  if(!Number.isSafeInteger(index)||index<0||index>10000)invalid('object_index must be 0–10,000.');
  return index;
 };
 if(action==='dataset_schema'){
  fields(value,['action','dataset_id','object_index']);
  return {action,dataset_id:datasetId(value.dataset_id),object_index:objectIndex(value.object_index)};
 }
 if(action==='dataset_rows'){
  fields(value,['action','dataset_id','object_index','columns','offset','limit','cursor']);
  const offset=value.offset??0,limit=value.limit??100;
  if(!Number.isSafeInteger(offset)||offset<0||offset>1000000000)invalid('Rows offset must be 0–1,000,000,000.');
  if(!Number.isSafeInteger(limit)||limit<1||limit>1000)invalid('Rows limit must be 1–1,000.');
  let columns;
  if(value.columns!==undefined){
   if(!Array.isArray(value.columns)||!value.columns.length||value.columns.length>64)invalid('columns must list 1–64 column names.');
   if(value.columns.some(c=>typeof c!=='string'||!/^[A-Za-z0-9_]{1,64}$/.test(c))||new Set(value.columns).size!==value.columns.length)invalid('Column names must be unique source field names.');
   columns=[...value.columns];
  }
  let cursor;
  if(value.cursor!==undefined){
   if(typeof value.cursor!=='string'||value.cursor.length<8||value.cursor.length>512||!/^[A-Za-z0-9_-]+=*$/.test(value.cursor))invalid('cursor must be the opaque value from a previous rows page.');
   if(value.offset!==undefined)invalid('Use a cursor or an offset, not both.');
   cursor=value.cursor;
  }
  return {action,dataset_id:datasetId(value.dataset_id),object_index:objectIndex(value.object_index),offset,limit,...(columns?{columns}:{}),...(cursor?{cursor}:{})};
 }
 if(action==='dataset_detail'){
  fields(value,['action','dataset_id']);
  const dataset_id=value.dataset_id??'';
  if(typeof dataset_id!=='string'||!/^[a-f0-9]{32}$/.test(dataset_id))invalid('dataset_id must be the 32-character catalog id.');
  return {action,dataset_id};
 }
 if(action==='dataset_catalog'){
  fields(value,['action','search','offset','limit']);
  const search=value.search??'',offset=value.offset??0,limit=value.limit??50;
  if(typeof search!=='string'||(search!==''&&!/^[a-z0-9_.-]{1,128}$/i.test(search)))invalid('Catalog search must be a short dataset or family name.');
  if(!Number.isSafeInteger(offset)||offset<0||offset>1000000||!Number.isSafeInteger(limit)||limit<1||limit>50)invalid('Catalog offset must be 0–1,000,000 and limit 1–50.');
  return {action,search,offset,limit};
 }
 const allowed={price:['date'],growth:['date_from','date_to','basis'],total_return:['date_from','date_to','include_series','max_points'],financials:['metric','frequency','date_from','date_to','as_of']}[action];
 if(!allowed)invalid('Use price, growth, total_return, financials, dataset_catalog, or dataset_detail.');
 fields(value,['action','symbol',...allowed]);
 if(typeof value.symbol!=='string'||!Object.hasOwn(symbols,value.symbol.toUpperCase()))invalid('Symbol is not in the stored universe.');
 const symbol=value.symbol.toUpperCase();
 if(action==='price')return {action:value.date===undefined?'latest_price':'price',symbol,dates:value.date===undefined?[]:[date(value.date)],basis:'raw_observed_price'};
 if((value.date_from===undefined)!==(value.date_to===undefined))invalid('Supply both date_from and date_to.');
 const dates=value.date_from===undefined?[]:[date(value.date_from),date(value.date_to)];
 if(dates.length&&dates[0]>dates[1])invalid('Date range must be earliest first.');
 if(action==='growth'){
  if(dates.length!==2||dates[0]===dates[1])invalid('Growth needs two different exact session dates.');
  const basis=value.basis??'split_adjusted_price';
  if(!['split_adjusted_price','raw_observed_price'].includes(basis))invalid('Unsupported price basis.');
  return {action,symbol,dates,basis};
 }
 if(action==='total_return'){
  if(dates.length!==2||dates[0]===dates[1])invalid('Total return needs two different exact session dates.');
  const include_series=value.include_series??true,max_points=value.max_points??500;
  if(typeof include_series!=='boolean')invalid('include_series must be true or false.');
  if(!Number.isSafeInteger(max_points)||max_points<2||max_points>5000)invalid('max_points must be 2–5,000.');
  return {action,symbol,dates,include_series,max_points};
 }
 const metric=value.metric??'revenue';
 if(!['revenue','revenue_growth','operating_margin'].includes(metric))invalid('Unsupported financial metric.');
 const frequency=value.frequency??'annual';
 if(!['annual','quarterly','ttm'].includes(frequency))invalid('Unsupported financial frequency.');
 return {action,symbol,dates,metric,frequency,...(value.as_of===undefined?{}:{as_of:financialCutoff(value.as_of)})};
}
