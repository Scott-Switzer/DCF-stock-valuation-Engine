import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute} from '../queries.mjs';
const bundle='a'.repeat(64),release='c'.repeat(64);
const snapshot={bundle_id:bundle,source_releases:{COLLECTION_CATALOG_KEY:release}};
const id='1'.repeat(32);
function env(change=x=>x){
 return {TOKEN:'fixture',DATA:{get:async()=>assert.fail('detail must not read a company index')},FINANCIAL_API:{fetch:async request=>{
  const url=new URL(request.url);
  assert.equal(url.pathname,'/private/v1/datasets/catalog/'+id);
  assert.equal(request.headers.get('x-zion-bundle-id'),bundle);
  return Response.json(change({catalog_release_id:release,id,dataset:'test__funda',family:'test',release:'run',source:'WRDS',rows_declared:2,PIT_status:'NOT_ESTABLISHED',quality:'SOURCE_UNVALIDATED',schema_status:'SOURCE_MANIFEST_DECLARED',schema_version:'zion-native-dataset-v1',store:'research',object_hash_status:'SOURCE_MANIFEST_DECLARED_NOT_REHASHED',manifest:{key:'raw/test/manifest.json',sha256:'b'.repeat(64)},normalization:{availability_time:null,canonical_ready:false,encoding:'parquet',null_semantics:'SQL_NULL',publication_state:'registered',status:'SOURCE_SPECIFIC_NOT_UNIVERSAL',remaining_gates:['UNITS','IDENTITY']},objects:[{path:'raw/test/part.parquet',bytes:123,etag:'abc',secret:'drop'}],columns:[{name:'fyear',type:'INT32',secret:'drop'}],secret_extra:'must not forward',raw_records:['forbidden'],rows:['forbidden']}),{headers:{'x-zion-bundle-id':bundle}});
 }}};
}
const url=request=>new URL('https://internal/query?'+new URLSearchParams({request:JSON.stringify(request)}));
test('dataset detail returns only projected metadata, never payloads',async()=>{
 const result=await queryRoute(env(),url({action:'dataset_detail',dataset_id:id}),{snapshot});
 assert.equal(result.action,'dataset_detail');
 assert.equal(result.result.dataset_id,id);
 assert.equal(result.result.detail.dataset,'test__funda');
 assert.equal(result.result.detail.secret_extra,undefined);
 assert.equal(result.result.detail.raw_records,undefined);
 assert.equal(result.result.detail.rows,undefined);
 assert.equal(result.result.detail.PIT_status,'NOT_ESTABLISHED');
 assert.equal(result.result.detail.store,'research');
 assert.equal(result.result.detail.manifest.key,'raw/test/manifest.json');
 assert.deepEqual(result.result.detail.normalization.remaining_gates,['UNITS','IDENTITY']);
 assert.equal(result.result.detail.objects[0].secret,undefined);
 assert.equal(result.result.detail.columns[0].secret,undefined);
 assert.equal(result.result.metadata_only,true);
 assert.match(result.answer,/not normalized/);
});
test('dataset detail natural language resolves the 32-character id',async()=>{
 const result=await queryRoute(env(),new URL('https://internal/query?query='+encodeURIComponent('WRDS dataset '+id)),{snapshot});
 assert.equal(result.action,'dataset_detail');
});
test('detail rejects bad ids, wrong releases and bundle drift',async()=>{
 await assert.rejects(queryRoute(env(),url({action:'dataset_detail',dataset_id:'short'}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(x=>({...x,catalog_release_id:'d'.repeat(64)})),url({action:'dataset_detail',dataset_id:id}),{snapshot}),/RELEASE_MISMATCH/);
 const wrong={...env(),FINANCIAL_API:{fetch:async()=>Response.json({catalog_release_id:release},{headers:{'x-zion-bundle-id':'b'.repeat(64)}})}};
 await assert.rejects(queryRoute(wrong,url({action:'dataset_detail',dataset_id:id}),{snapshot}),/RELEASE_MISMATCH/);
});
