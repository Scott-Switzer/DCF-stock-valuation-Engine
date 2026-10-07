// Bounded publisher transport. Credentials stay inside Wrangler's remote proxy.
import {createHash} from 'node:crypto';
import { createRequire } from 'node:module';
import { createInterface } from 'node:readline';
const require = createRequire(import.meta.url);
const { getPlatformProxy } = require(process.env.WRANGLER_MODULE || 'wrangler');
const platform = await getPlatformProxy({ configPath: process.argv[2], persist: false });
const readAllowed = key => key === 'gold/serving/coverage25/CURRENT.json' || key === 'control/valuation/CURRENT.json' || (/^gold\/serving\/releases\/[a-f0-9]+\/(manifest\.json|identity\/resolver_index\.json|entities\/entity_sec_cik_[0-9]+(?:_[A-Z-]+)?\/fundamentals\/annual\.json)$/.test(key));
const writeAllowed = key => /^gold\/valuation\/releases\/[a-f0-9]{64}\/companies\/[A-Z-]+\.json$/.test(key) || key === 'control/valuation/CURRENT.json' || /^raw\/valuation-sec\/[a-f0-9]{64}\/companyfacts\.json$/.test(key);
async function execute(cmd) {
   let result;
   if (cmd.op === 'get' && readAllowed(cmd.key)) {
    const obj = await platform.env.DATA.get(cmd.key);
    if (obj && obj.size > 16*1024*1024) throw new Error('OBJECT_TOO_LARGE');
    result = obj ? { body: Buffer.from(await obj.arrayBuffer()).toString('base64'), etag:obj.etag } : null;
   } else if (cmd.op === 'put' && writeAllowed(cmd.key)) {
    const bytes = Buffer.from(cmd.body, 'base64');
    if (bytes.length > (cmd.key.startsWith('raw/') ? 8*1024*1024 : 512*1024)) throw new Error('OBJECT_TOO_LARGE');
    const existing = cmd.key === 'control/valuation/CURRENT.json' ? null : await platform.env.DATA.head(cmd.key);
    if (!existing) {
     const options = {httpMetadata:{contentType:'application/json'}};
     if (cmd.key === 'control/valuation/CURRENT.json') options.onlyIf = cmd.expectedEtag ? {etagMatches:cmd.expectedEtag} : {etagDoesNotMatch:'*'};
     const written = await platform.env.DATA.put(cmd.key, bytes, options);
     if (!written) throw new Error('POINTER_CHANGED');
    }
    const verified = await platform.env.DATA.get(cmd.key);
    if (!verified || createHash('sha256').update(Buffer.from(await verified.arrayBuffer())).digest('hex') !== createHash('sha256').update(bytes).digest('hex')) throw new Error('READBACK_MISMATCH');
    result = {key:cmd.key, bytes:bytes.length};
   } else throw new Error('OPERATION_NOT_ALLOWED');
   return result;
}
try {
 for await (const line of createInterface({input:process.stdin})) {
  try {
   const cmd = JSON.parse(line);
   if(cmd.op === 'close') break;
   const result = cmd.op === 'batch' && Array.isArray(cmd.items) && cmd.items.length <= 4
     ? await Promise.all(cmd.items.map(execute)) : await execute(cmd);
   console.log('R2JSON'+JSON.stringify({result}));
  } catch {console.log('R2JSON'+JSON.stringify({error:'R2_OPERATION_FAILED'}));}
 }
} finally {await platform.dispose();} 
