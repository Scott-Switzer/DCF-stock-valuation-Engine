import {test} from 'node:test';
import assert from 'node:assert/strict';
import {queryRoute} from '../queries.mjs';
const bundle='a'.repeat(64),release='c'.repeat(64);
const snapshot={bundle_id:bundle,source_releases:{COLLECTION_CATALOG_KEY:release}};
const id='1'.repeat(32),sha='e'.repeat(64);
const objects=[{key:'raw/test/part-000.parquet',sha256:sha,bytes:1234,rows:900},{key:'raw/test/part-001.parquet',sha256:'f'.repeat(64),bytes:4321,rows:100}];
function catalog(change=x=>x){
 return change({catalog_release_id:release,id,dataset:'test__funda',family:'test',release:'run-1',rows_declared:1000,
  store:'research',objects,columns:[{name:'fyear',type:'INT32'}]});
}
function env({detail=catalog(),native=nativeRows(),reader=true}={}){
 const calls=[];
 return {calls,TOKEN:'fixture',
  DATA:{get:async()=>assert.fail('archive reads must not touch the company index')},
  FINANCIAL_API:{fetch:async request=>{
   assert.equal(new URL(request.url).pathname,'/private/v1/datasets/catalog/'+id);
   assert.equal(request.headers.get('x-zion-bundle-id'),bundle);
   return Response.json(detail,{headers:{'x-zion-bundle-id':bundle}});
  }},
  ...(reader?{ZION_DATASETS:{fetch:async request=>{
   calls.push(new URL(request.url));
   return native instanceof Response?native:Response.json(native);
  }}}:{})};
}
const nativeSchema=()=>({schema_version:'zion-native-table-v1',operation:'schema',quality:'SOURCE_UNVALIDATED',normalization:'NATIVE_SOURCE_FIELDS',
 source:{store:'research',path:'raw/test/part-000.parquet',etag:'etag-1',bytes:1234,integrity:'ETAG_PINNED_RANGES; FULL_OBJECT_SHA_NOT_REHASHED'},
 data:{schema_status:'PARQUET_FOOTER_DECODED',row_count_status:'FOOTER_DECLARED_NOT_FULL_SCAN',row_count:900,row_groups:2,
  columns:[{name:'fyear',type:'INT32',converted_type:'NONE',logical_type:{type:'INT'}},{name:'gvkey',type:'BYTE_ARRAY'}]},
 cache:'MISS'});
const nativeRows=()=>({schema_version:'zion-native-table-v1',operation:'rows',quality:'SOURCE_UNVALIDATED',normalization:'NATIVE_SOURCE_FIELDS',
 source:{store:'research',path:'raw/test/part-000.parquet',etag:'etag-1',bytes:1234,integrity:'ETAG_PINNED_RANGES; FULL_OBJECT_SHA_NOT_REHASHED'},
 data:{columns:[{name:'fyear',type:'INT32'},{name:'gvkey',type:'BYTE_ARRAY'}],row_count:900,row_offset:0,
  rows:[{fyear:2024,gvkey:'001234'},{fyear:2024,gvkey:'005678'}]},
 next_cursor:'eyJ2IjoxfQ',cache:'MISS'});
const url=request=>new URL('https://internal/query?'+new URLSearchParams({request:JSON.stringify(request)}));

test('dataset schema reads the catalog object through the native reader',async()=>{
 const e=env({native:nativeSchema()});
 const result=await queryRoute(e,url({action:'dataset_schema',dataset_id:id}),{snapshot});
 assert.equal(result.action,'dataset_schema');
 assert.equal(e.calls.length,1);
 const called=e.calls[0];
 assert.equal(called.pathname,'/v1/datasets/research/schema');
 assert.equal(called.searchParams.get('path'),'raw/test/part-000.parquet');
 assert.equal(result.result.dataset,'test__funda');
 assert.equal(result.result.store,'research');
 assert.equal(result.result.sha256,sha);
 assert.equal(result.result.schema.row_count,900);
 assert.equal(result.result.schema.row_groups,2);
 assert.deepEqual(result.result.schema.columns.map(c=>c.name),['fyear','gvkey']);
 assert.equal(result.source.provider,'WRDS');
 assert.equal(result.source.path,'raw/test/part-000.parquet');
 assert.match(result.answer,/native parquet footer declares 900 rows/);
 assert.match(result.warnings.join(' '),/not normalized/);
});

test('dataset rows returns a bounded page with the catalog object key',async()=>{
 const e=env();
 const result=await queryRoute(e,url({action:'dataset_rows',dataset_id:id,columns:['fyear','gvkey'],offset:0,limit:2}),{snapshot});
 const called=e.calls[0];
 assert.equal(called.pathname,'/v1/datasets/research/rows');
 assert.equal(called.searchParams.get('path'),'raw/test/part-000.parquet');
 assert.equal(called.searchParams.get('columns'),'fyear,gvkey');
 assert.equal(called.searchParams.get('limit'),'2');
 assert.equal(result.action,'dataset_rows');
 assert.equal(result.result.records.length,2);
 assert.equal(result.result.row_count,900);
 assert.equal(result.result.next_cursor,'eyJ2IjoxfQ');
 assert.deepEqual(result.result.columns,['fyear','gvkey']);
 assert.equal(result.result.metadata_only,false);
 assert.match(result.answer,/returned 2 native rows from offset 0 of 900/);
});

test('the second catalog object is addressable by index, never by path',async()=>{
 const e=env();
 await queryRoute(e,url({action:'dataset_rows',dataset_id:id,object_index:1,limit:5}),{snapshot});
 assert.equal(e.calls[0].searchParams.get('path'),'raw/test/part-001.parquet');
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,object_index:1,offset:0,limit:5,path:'raw/other.parquet'}),{snapshot}),/Unsupported field: path/);
});

test('rows rejects out-of-range objects, bad paging and bad columns',async()=>{
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,object_index:9}),{snapshot}),/DATASET_OBJECT_NOT_FOUND/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,limit:1001}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,limit:0}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,offset:-1}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,columns:['fyear','fyear']}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,columns:['bad name']}),{snapshot}),/INVALID_REQUEST/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:id,cursor:'eyJ2IjoxfQ',offset:0}),{snapshot}),/not both/);
 await assert.rejects(queryRoute(env(),url({action:'dataset_rows',dataset_id:'short'}),{snapshot}),/INVALID_REQUEST/);
});

test('an unsupported store, a missing reader and a reader error fail closed',async()=>{
 await assert.rejects(queryRoute(env({detail:catalog(x=>({...x,store:'compustat'}))}),url({action:'dataset_schema',dataset_id:id}),{snapshot}),/DATASET_STORE_UNSUPPORTED/);
 await assert.rejects(queryRoute(env({reader:false}),url({action:'dataset_schema',dataset_id:id}),{snapshot}),/DATASET_READER_UNAVAILABLE/);
 const failure={schema_version:'zion-native-table-v1',operation:'rows'};
 await assert.rejects(queryRoute(env({native:Response.json({error:{code:'INVALID_COLUMNS'}},{status:422})}),url({action:'dataset_rows',dataset_id:id}),{snapshot}),/INVALID_COLUMNS/);
 await assert.rejects(queryRoute(env({native:Response.json(failure,{status:200})}),url({action:'dataset_rows',dataset_id:id}),{snapshot}),/DATASET_RESPONSE_INVALID/);
});

test('catalog drift still rejects before any object is read',async()=>{
 const e=env({detail:catalog(x=>({...x,catalog_release_id:'d'.repeat(64)}))});
 await assert.rejects(queryRoute(e,url({action:'dataset_rows',dataset_id:id}),{snapshot}),/RELEASE_MISMATCH/);
 assert.equal(e.calls.length,0);
});
