// The thin source service is the only bundle authority. Never mint a local ID.
export function answerDate(value){
 const dates=[];
 const visit=node=>{
  if(Array.isArray(node)){node.forEach(visit);return;}
  if(!node||typeof node!=='object')return;
  for(const key of ['period_end','session_date','date','end_date','price_as_of']){
   const date=node[key];if(typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)&&Number.isFinite(Date.parse(date))&&new Date(date).toISOString().slice(0,10)===date)dates.push(date);
  }
  for(const key of ['data','result','observations','prices','rows','evidence','historical','financials','market'])if(node[key])visit(node[key]);
 };
 visit(value);return dates.sort().at(-1)||null;
}
export async function readSnapshot(env){
 const response=await env.FINANCIAL_API.fetch(new Request('https://zion.internal/private/v1/snapshot',{headers:{Authorization:'Bearer '+env.TOKEN},signal:AbortSignal.timeout(10000)}));
 if(!response.ok)throw Error('BUNDLE_UNAVAILABLE');
 const value=await response.json();
 if(!/^[a-f0-9]{64}$/.test(value.bundle_id||'')||!value.source_releases||typeof value.source_releases!=='object')throw Error('BUNDLE_UNAVAILABLE');
 return value;
}
export async function stampedRead(env,expected,read){
 const before=await readSnapshot(env);
 try{
  if(expected&&expected!==before.bundle_id)throw Error('RELEASE_MISMATCH');
  const result=await read(before);
  const after=await readSnapshot(env);
  if(after.bundle_id!==before.bundle_id||(result.bundle_id&&result.bundle_id!==before.bundle_id))throw Error('RELEASE_MISMATCH');
  if(result.source?.release&&!Object.values(before.source_releases).includes(result.source.release)){
   // The source authority verifies indexed historical releases. Preserve their
   // real release ID and require its parent index to belong to this bundle.
   const index=before.source_releases.daily_session_index;
   if(result.bundle_id!==before.bundle_id||!index||result.source.session_index_sha256!==index||result.source.session_index_key!==`control/daily-prices/sessions/${index}.json`)throw Error('RELEASE_MISMATCH');
  }
  return {...result,bundle_id:before.bundle_id,data_as_of:answerDate(result),source_releases:before.source_releases};
 }catch(error){error.snapshot=before;throw error;}
}
