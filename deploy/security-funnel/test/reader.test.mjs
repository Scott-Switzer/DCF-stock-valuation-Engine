import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {openMaterialized,sourceFreshness,chooseSourceDate} from '../connections.mjs';
const raw=await readFile(new URL('./synthetic.parquet',import.meta.url));
const file=raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength);
const ref={key:'research/financial-research-canonical-v1/test/synthetic.parquet',bytes:raw.length,rows:4,
  sha256:createHash('sha256').update(raw).digest('hex')};
const env={RESEARCH:{get:async()=>({size:raw.length,arrayBuffer:async()=>file})}};
const p=await openMaterialized(env,ref);
assert.deepEqual((await p.column('permno')).map(Number),[101,101,202,202]);
assert.deepEqual(await p.column('dlycaldt'),['2025-01-01','2025-01-02','2025-02-01','2025-02-02']);
assert.deepEqual(await p.column('split_adjusted_price'),[10,11,null,20]);
assert.deepEqual(await p.column('missing_adjustment_factors'),[false,false,true,false]);
await assert.rejects(openMaterialized(env,{...ref,sha256:'0'.repeat(64)}),/MATERIALIZED_OBJECT_HASH/);
await assert.rejects(openMaterialized(env,{...ref,rows:5}),/MATERIALIZED_ROW_COUNT/);
assert.equal(sourceFreshness('2026-10-20').status,'WITHIN_POLICY');
assert.equal(sourceFreshness('2025-12-31').status,'STALE');
assert.equal(sourceFreshness('2026-10-22').status,'FUTURE');
assert.equal(sourceFreshness('2026-02-30').status,'UNKNOWN_OR_INVALID');
const old={security_id:'old',adjusted_history:{date_min:'1990-01-01',date_max:'1999-12-31'},
 ticker_intervals:[{effective_from:'1990-01-01',effective_to:'1999-12-31'}]};
const current={security_id:'current',adjusted_history:{date_min:'2000-01-01',date_max:'2025-12-31'},
 ticker_intervals:[{effective_from:'2000-01-01',effective_to:'2025-12-31'}]};
assert.equal(chooseSourceDate([old,current],'2025-12-31').candidates[0].security_id,'current');
assert.equal(chooseSourceDate([old,current],'2025-12-31').status,'SOURCE_DATE_SECURITY_RESOLVED');
assert.equal(chooseSourceDate([current,{...current,security_id:'another'}],'2025-12-31').status,'SOURCE_DATE_SECURITY_AMBIGUOUS');
assert.equal(chooseSourceDate([old],'2025-12-31').basis,'HISTORICAL_INTERVAL_OVERLAP');
console.log('Parquet projection, ZSTD, dates, nulls and integrity checks passed.');
