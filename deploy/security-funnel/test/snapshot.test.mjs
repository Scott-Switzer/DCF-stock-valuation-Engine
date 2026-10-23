import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readSnapshot, stampedRead, answerDate} from '../snapshot.mjs';
const snapshot={bundle_id:'a'.repeat(64),source_releases:{SEC:'sec-original',shared_history:'crsp-original'},data_as_of:null};
test('pins before reading and rejects a changed snapshot afterwards',async()=>{
 let calls=0;
 const env={TOKEN:'test',FINANCIAL_API:{fetch:async()=>Response.json({...snapshot,bundle_id:(++calls===1?'a':'b').repeat(64)})}};
 await assert.rejects(()=>stampedRead(env,null,async()=>({answer:'test',source:{provider:'SEC',release:'sec-original'}})),/RELEASE_MISMATCH/);
});
test('preserves source releases and uses answer coverage rather than freshness of publication',async()=>{
 const env={TOKEN:'test',FINANCIAL_API:{fetch:async()=>Response.json(snapshot)}};
 const result=await stampedRead(env,snapshot.bundle_id,async()=>({source:{provider:'SEC',release:'sec-original'},result:{observations:[{period_end:'2025-12-31',available_at:'2026-10-22'}]}}));
 assert.equal(result.bundle_id,snapshot.bundle_id);assert.equal(result.data_as_of,'2025-12-31');
 assert.deepEqual(result.source,{provider:'SEC',release:'sec-original'});
 await assert.rejects(()=>stampedRead(env,'wrong',async()=>assert.fail()),/RELEASE_MISMATCH/);
 await assert.rejects(()=>stampedRead(env,null,async()=>({source:{release:'unlisted'}})),/RELEASE_MISMATCH/);
 assert.equal(answerDate({result:{observations:[]}}),null);
});
test('accepts a prior-session release anchored to a bundle-pinned session index',async()=>{
 const env={TOKEN:'test',FINANCIAL_API:{fetch:async()=>Response.json({...snapshot,source_releases:{...snapshot.source_releases,daily_session_index:'index-1'}})}};
 const result=await stampedRead(env,snapshot.bundle_id,async()=>({source:{provider:'alpaca',release:'prior-session-release',session_index_release:'index-1'},result:{date:'2026-10-21'}}));
 assert.equal(result.source.release,'prior-session-release');assert.equal(result.data_as_of,'2026-10-21');
 await assert.rejects(()=>stampedRead(env,snapshot.bundle_id,async()=>({source:{release:'prior-session-release',session_index_release:'unlisted-index'}})),/RELEASE_MISMATCH/);
 await assert.rejects(()=>stampedRead(env,snapshot.bundle_id,async()=>({source:{release:'prior-session-release'}})),/RELEASE_MISMATCH/);
});
