import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute} from '../queries.mjs';
import {stampedRead} from '../snapshot.mjs';
const bundle='a'.repeat(64),release='c'.repeat(64);
const snapshot={bundle_id:bundle,source_releases:{COLLECTION_CATALOG_KEY:release}};
function env(change=x=>x){return {TOKEN:'fixture',DATA:{get:async()=>assert.fail('catalog must not read a company index')},FINANCIAL_API:{fetch:async request=>{
 const url=new URL(request.url);
 if(url.pathname==='/private/v1/snapshot')return Response.json(snapshot);
 assert.equal(url.pathname,'/private/v1/datasets/catalog');assert.equal(request.headers.get('x-zion-bundle-id'),bundle);
 return Response.json(change({release_id:release,registered_releases:3,unique_datasets:2,matching_releases:3,next_offset:null,entries:[{id:'1'.repeat(32),dataset:'test__funda',source:'WRDS',family:'test',rows_declared:2,objects:1,columns:3,release:'run',secret_extra:'must not forward'}]}),{headers:{'x-zion-bundle-id':bundle}});
}}};}
test('WRDS coverage uses the existing private metadata catalog with bundle lineage',async()=>{
 const result=await stampedRead(env(),bundle,s=>queryRoute(env(),new URL('https://internal/query?query=WRDS+coverage'),{snapshot:s}));
 assert.equal(result.action,'dataset_catalog');assert.equal(result.data_as_of,null);
 assert.equal(result.source.release,release);assert.equal(result.result.entries[0].dataset,'test__funda');
 assert.equal(result.result.entries[0].secret_extra,undefined);assert.match(result.answer,/not normalized/);
});
test('a catalog deployment differing from the source snapshot fails closed',async()=>{
 await assert.rejects(()=>queryRoute(env(x=>({...x,release_id:'d'.repeat(64)})),new URL('https://internal/query?query=WRDS+datasets'),{snapshot}),/RELEASE_MISMATCH/);
});
