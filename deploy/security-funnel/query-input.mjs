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
 object(request);return {request};
}
function date(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||!Number.isFinite(Date.parse(value))||new Date(value).toISOString().slice(0,10)!==value)invalid('Use real dates formatted YYYY-MM-DD.');
 return value;
}
export function structuredQuery(value,symbols={}){
 object(value);
 const action=value.action;
 if(typeof action!=='string'||!['price','growth','financials','dataset_catalog'].includes(action))invalid('Unsupported action.');
 if(action==='dataset_catalog'){
  fields(value,['action','search','offset','limit']);
  const search=value.search??'',offset=value.offset??0,limit=value.limit??50;
  if(typeof search!=='string'||(search!==''&&!/^[a-z0-9_.-]{1,128}$/i.test(search)))invalid('Catalog search must be a short dataset or family name.');
  if(!Number.isSafeInteger(offset)||offset<0||offset>1000000||!Number.isSafeInteger(limit)||limit<1||limit>50)invalid('Catalog offset must be 0–1,000,000 and limit 1–50.');
  return {action,search,offset,limit};
 }
 const allowed={price:['date'],growth:['date_from','date_to','basis'],financials:['metric','frequency','date_from','date_to']}[action];
 if(!allowed)invalid('Use price, growth, financials, or dataset_catalog.');
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
 const metric=value.metric??'revenue';
 if(!['revenue','revenue_growth','operating_margin'].includes(metric))invalid('Unsupported financial metric.');
 const frequency=value.frequency??'annual';
 if(!['annual','quarterly','ttm'].includes(frequency))invalid('Unsupported financial frequency.');
 return {action,symbol,dates,metric,frequency};
}
