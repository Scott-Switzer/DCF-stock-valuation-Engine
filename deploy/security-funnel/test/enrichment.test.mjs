import assert from 'node:assert/strict';
import {eligibleCik,enrichmentQueue} from '../enrichment.mjs';
assert.equal(eligibleCik(null),false);assert.equal(eligibleCik('0000000000'),false);assert.equal(eligibleCik('0000000001'),true);
let saved,acked=0,retried=0;
const env={TOKEN:'synthetic',DATA:{get:async()=>{const raw=JSON.stringify({plan:{sha256:'a'.repeat(64)},runtime_version:'v',assessed_at:'2026-10-21'});return {size:raw.length,text:async()=>raw}},put:async(k,v)=>saved=JSON.parse(v)},PACKET_BUILDER:{fetch:async()=>Response.json({error:'TEMPORARY'},{status:503})}};
const msg={body:{job:'source-enrichment-v1',cik:'0000000001',run_id:'b'.repeat(64)},attempts:1,ack:()=>acked++,retry:()=>retried++};
await enrichmentQueue({messages:[msg]},env);assert.equal(saved.terminal,false);assert.equal(retried,1);
msg.attempts=3;await enrichmentQueue({messages:[msg]},env);assert.equal(saved.terminal,true);assert.equal(acked,1);
env.PACKET_BUILDER.fetch=async()=>Response.json({runtime_version:'wrong',assessed_at:'2026-10-21'});
msg.attempts=1;await enrichmentQueue({messages:[msg]},env);assert.equal(saved.error,'ENRICHMENT_TRANSPORT_FAILED');assert.equal(saved.terminal,false);
console.log('Issuer cohort validation, retry exhaustion and pinned runtime guards passed.');

// An immutable enrichment part must use the pinned parent accounting job even
// when the latest legacy pointer changes while the ledger is being built.
const {enrichmentRoute,ENRICH}=await import('../enrichment.mjs');
const {createHash}=await import('node:crypto');
const db=new Map(),digest=raw=>createHash('sha256').update(raw).digest('hex');
function store(key,value){const raw=JSON.stringify(value);db.set(key,raw);return {key,sha256:digest(raw)};}
const run='c'.repeat(64),parent={run_id:'old-parent',assessed_at:'2026-10-21',symbols:['TEST']};
const planRef=store('plan-content',{ciks:['0000000001'],symbols:['TEST'],excluded:[],source:{snapshot_date:'2026-10-15'}});
store(ENRICH+'plan.json',planRef);store(ENRICH+'job.json',{run_id:run,plan:planRef,runtime_version:'v',assessed_at:'2026-10-21'});
const assetsRef=store('frozen-assets',{index:{}}),contextRef=store('frozen-context',{run_id:run,parentJob:parent,assetsRef,directoryRef:null});
store(ENRICH+'runs/'+run+'/ledger-context.json',contextRef);
store('staging/security-funnel/2026-10-20/9beaa712e71650a2/full-history-2026-10-21-v1/batches/0.json',{input_sha256:'68db69ad8e4693616d5735b836764e7cd034c45bf9e7a79e483a99bd3163507a',rows:[{symbol:'TEST',identity:{cik:'0000000001'},valuation:{}}]});
const ledgerEnv={DATA:{get:async key=>{assert.ok(!key.endsWith('/packet-job.json'),'mutable parent pointer must not be read');const raw=db.get(key);return raw?{size:raw.length,text:async()=>raw,json:async()=>JSON.parse(raw)}:null},put:async(key,raw)=>db.set(key,raw)}};
await enrichmentRoute(ledgerEnv,new URL('https://internal/connect/enrichment-ledger-batch?n=0'));
const marker=JSON.parse(db.get(ENRICH+'runs/'+run+'/ledger-parts/0.json')),part=JSON.parse(db.get(marker.key));
assert.equal(part.context_sha256,contextRef.sha256);assert.equal(part.rows[0].valuation.accounting_rebuild.run_id,'old-parent');
await assert.rejects(()=>enrichmentRoute(ledgerEnv,new URL('https://internal/enrichment-ledger?part=0')),/PIN_REQUIRED/);
