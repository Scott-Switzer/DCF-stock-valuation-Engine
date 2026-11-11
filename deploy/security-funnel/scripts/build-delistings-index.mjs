// Reproducible local build of the CRSP delisting index. The Worker route
// /connect/delistings-init applies the same rules through delistingEntries();
// this script exists so the index can be rebuilt without the operator token.
//
//   curl -sS -H "Authorization: Bearer $ZION_PRIVATE_API_TOKEN" \
//     "$ZION_PRIVATE_BASE_URL/private/v1/datasets/catalog/4833fe6633fc104b61475e35b253898a" > detail.json
//   node scripts/build-delistings-index.mjs \
//     --parquet /tmp/dsedelist.parquet --catalog-detail detail.json \
//     --history-catalog /tmp/history-catalog.json --out /tmp/delistings-index.json
import {readFileSync,writeFileSync} from 'node:fs';
import {parquetReadObjects} from 'hyparquet';
import {decompress} from 'fzstd';
import {delistingIndexPayload} from '../history.mjs';

const args=Object.fromEntries(process.argv.slice(2).reduce((pairs,value,index,all)=>
 index%2?pairs:[...pairs,[value.replace(/^--/,''),all[index+1]]],[]));
for(const name of ['parquet','catalog-detail','history-catalog','out']){
 if(!args[name]){console.error('Missing --'+name);process.exit(2);}
}
const detail=JSON.parse(readFileSync(args['catalog-detail'],'utf8'));
const object=(detail.objects||[])[0];
if(detail.store!=='research'||!object?.key||!/^[a-f0-9]{64}$/.test(object.sha256||'')){
 console.error('Catalog detail is not the expected delisting archive.');process.exit(2);
}
const buffer=readFileSync(args.parquet);
const rows=await parquetReadObjects({file:buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength),compressors:{ZSTD:value=>decompress(value)}});
const catalog=JSON.parse(readFileSync(args['history-catalog'],'utf8'));
const source={dataset:detail.dataset,catalog_id:detail.id,catalog_release_id:detail.catalog_release_id,store:detail.store,
 object:{key:object.key,sha256:object.sha256,rows:object.rows??null}};
const {payload,summary}=await delistingIndexPayload({rows,universe:new Set(Object.keys(catalog)),source});
writeFileSync(args.out,JSON.stringify(payload));
console.log(JSON.stringify(summary,null,2));
