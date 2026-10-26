// Compare native availability timestamps at nanosecond precision. A millisecond
// Date comparison could incorrectly admit a record just beyond the cutoff.
const fail=code=>{throw Error(code);};
function instant(value){
 const match=typeof value==='string'&&/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z$/.exec(value);
 if(!match)return null;
 const ms=Date.parse(match[1]+'Z');
 if(!Number.isFinite(ms)||new Date(ms).toISOString()!==match[1]+'.000Z')return null;
 return BigInt(ms)*1000000n+BigInt((match[2]||'').padEnd(9,'0'));
}
export function financialCutoff(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)||instant(value)===null)fail('INVALID_REQUEST: as_of must be a real UTC timestamp YYYY-MM-DDTHH:mm:ssZ.');
 return value;
}
export function validateCutoffPage(page,cutoff,{bundle,release,cik,frequency}){
 if(cutoff===undefined)return;
 const boundary=instant(cutoff);
 if(boundary===null||instant(page.as_of)!==boundary)fail('FINANCIAL_CUTOFF_MISMATCH');
 if(page.bundle_id!==bundle||page.provenance?.release_id!==release||page.cik!==cik||page.frequency!==frequency)fail('FINANCIAL_SOURCE_MISMATCH');
 if(!Array.isArray(page.observations)||!Array.isArray(page.accounting_checks)||!page.source_records||typeof page.source_records!=='object'||Array.isArray(page.source_records))fail('FINANCIAL_LINEAGE_MISSING');
 if(!Array.isArray(page.coverage_gaps)||!page.pagination||typeof page.pagination!=='object'||Array.isArray(page.pagination)||!Object.hasOwn(page.pagination,'next_cursor'))fail('FINANCIAL_RESPONSE_INVALID');
 const cursor=page.pagination.next_cursor;
 if(cursor!==null&&(typeof cursor!=='string'||!cursor.length||cursor.length>2048))fail('FINANCIAL_RESPONSE_INVALID');
 const available=record=>{const time=instant(record?.available_at);if(time===null||time>boundary)fail('FINANCIAL_AVAILABILITY_VIOLATION');};
 for(const record of Object.values(page.source_records))available(record);
 for(const row of [...page.observations,...page.accounting_checks]){
  // Accounting checks can carry component availability only; every referenced
  // source record is still required and independently checked above.
  if(page.observations.includes(row)||row.available_at!==undefined)available(row);
  const unavailableCheck=!page.observations.includes(row)&&row.status==='UNAVAILABLE'&&typeof row.reason==='string'&&row.reason.length>0;
  if(!Array.isArray(row.source_observation_ids)||(!row.source_observation_ids.length&&!unavailableCheck)||row.source_observation_ids.some(id=>!Object.hasOwn(page.source_records,id)))fail('FINANCIAL_LINEAGE_MISSING');
 }
}
