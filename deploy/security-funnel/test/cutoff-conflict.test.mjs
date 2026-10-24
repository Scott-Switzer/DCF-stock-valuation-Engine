import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute} from '../queries.mjs';
import {FULL} from '../history.mjs';
import {createHash} from 'node:crypto';
const packet={observations:[],source_records:{}};
const raw=JSON.stringify(packet),sha=createHash('sha256').update(raw).digest('hex');
const db=new Map([[FULL+'symbol-batches.json',JSON.stringify({PEP:0})],[FULL+'batches/0.json',JSON.stringify({rows:[{symbol:'PEP',identity:{cik:'0000000001'},valuation:{inputs:{}}}]})]]);
const baseEnv={DATA:{get:async key=>{const value=db.get(key);return value?{size:value.length,text:async()=>value}:null;}}};
function envWithCutoffs(cutoffs){
 let i=0;
 return {...baseEnv,TOKEN:'test',FINANCIAL_API:{fetch:async request=>{
  const url=new URL(request.url);
  const cutoff=cutoffs[Math.min(i++,cutoffs.length-1)];
  return Response.json({provenance:{company_maximum_as_of:cutoff+'T00:00:00Z'},observations:[],source_records:{},pagination:{next_cursor:null}});
 }}};
}
test('conflicting cutoffs across annual windows fail instead of inheriting a stale date',async()=>{
 const env=envWithCutoffs(['2026-09-24','2026-08-15']);
 await assert.rejects(queryRoute(env,new URL('https://internal/query?query=PEP+revenue')),/FINANCIAL_SOURCE_CONTEXT_CHANGED/);
});
test('conflicting cutoffs across pages within one window fail',async()=>{
 let n=0;
 const env={...baseEnv,TOKEN:'test',FINANCIAL_API:{fetch:async request=>{
  const url=new URL(request.url);
  const first=!url.searchParams.has('cursor');
  if(n++===0)return Response.json({provenance:{company_maximum_as_of:'2026-09-24T00:00:00Z'},observations:[],source_records:{},pagination:{next_cursor:'next'}});
  return Response.json({provenance:{company_maximum_as_of:'2026-06-30T00:00:00Z'},observations:[],source_records:{},pagination:{next_cursor:null}});
 }}};
 await assert.rejects(queryRoute(env,new URL('https://internal/query?query=PEP+revenue')),/FINANCIAL_SOURCE_CONTEXT_CHANGED/);
});
