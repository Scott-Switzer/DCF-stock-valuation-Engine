"""Private cloud packet builder. Reuses PPE accounting code and pinned stored SEC bytes."""
import hashlib
import json
import re
import struct
import zlib
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from workers import Response, WorkerEntrypoint
from pyodide.ffi import to_js
from js import Object
from ppe_packets import build_packet
from dcf_loader import ProviderError
from sec_first import eligibility_gate, valuation_readiness
from runtime_manifest import VERSION

BASE='staging/security-funnel/2026-10-20/9beaa712e71650a2/'
OUT=BASE+'valuation-completion-2026-10-21-v1/'
MANIFEST='gold/sec-engine/releases/b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb/manifest.json'
MANIFEST_SHA='4e0d6b9eac28ea2352dd255c4f8323f1fd4d486796063921cec691942660be7b'

def fail(code): raise ValueError(code)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def plain(value): return value.to_py() if hasattr(value,'to_py') else value
async def read(bucket,key,digest=None,maximum=16*1048576):
 obj=await bucket.get(key)
 if not obj or obj.size>maximum: fail('PACKET_SOURCE_UNAVAILABLE')
 raw=str(await obj.text()).encode()
 if digest and sha(raw)!=digest: fail('PACKET_SOURCE_HASH')
 return json.loads(raw)
async def put(env,key,value):
 raw=json.dumps(value,separators=(',',':'),allow_nan=False)
 await env.DATA.put(key,raw)
 return {'key':key,'sha256':sha(raw.encode())}
async def immutable(env,kind,value):
 raw=json.dumps(value,separators=(',',':'),allow_nan=False)
 digest=sha(raw.encode());key=OUT+kind+'/by-sha256/'+digest+'.json'
 await env.DATA.put(key,raw)
 return {'key':key,'sha256':digest}

async def member(env,m,e,cik):
 digest=e['materialized']['member_sha256'];cache=OUT+'companyfacts/'+cik+'/'+digest+'.json'
 old=await env.DATA.get(cache)
 if old:
  raw=str(await old.text()).encode()
  if sha(raw)!=digest:fail('COMPANYFACTS_CACHE_HASH')
  return json.loads(raw),{'key':cache,'sha256':digest,'archive_bytes_read':0,'cache':'HIT'}
 source=m['source'];a=e['archive_entry']
 if source.get('key')!='sec/bulk/sec-nightly-20260924/companyfacts.zip' or source.get('bucket')!='financial-data-wrds-private' or a['name']!=f'CIK{cik}.json':fail('UNAPPROVED_SEC_MEMBER')
 if a['flags']&1 or a['compression'] not in (0,8) or not 0<a['uncompressed_bytes']<=24*1048576 or not 0<a['compressed_bytes']<=8*1048576:fail('SEC_MEMBER_BUDGET')
 head=await env.RESEARCH.head(source['key'])
 if not head or head.size!=source['bytes'] or head.etag.strip('"')!=source['etag'].strip('"'):fail('SEC_ARCHIVE_CHANGED')
 async def part(offset,length):
  if not 0<length<=1048576 or not 0<=offset<=source['bytes']-length:fail('SEC_RANGE_BUDGET')
  o=await env.RESEARCH.get(source['key'],to_js({'range':{'offset':offset,'length':length},'onlyIf':{'etagMatches':source['etag'].strip('"')}},dict_converter=Object.fromEntries))
  if not o or o.etag.strip('"')!=source['etag'].strip('"'):fail('SEC_RANGE_CHANGED')
  raw=bytes(plain(await o.arrayBuffer()))
  if len(raw)!=length:fail('SEC_RANGE_LENGTH')
  return raw
 h=struct.unpack('<4s5H3I2H',await part(a['offset'],30))
 if h[0]!=b'PK\x03\x04' or h[2]!=a['flags'] or h[3]!=a['compression']:fail('SEC_ZIP_HEADER')
 if (await part(a['offset']+30,h[-2])).decode()!=a['name']:fail('SEC_ZIP_NAME')
 offset=a['offset']+30+h[-2]+h[-1];remaining=a['compressed_bytes'];chunks=[]
 while remaining:
  count=min(remaining,1048576);chunks.append(await part(offset,count));offset+=count;remaining-=count
 compressed=b''.join(chunks)
 if a['compression']==8:
  decoder=zlib.decompressobj(-15);raw=decoder.decompress(compressed,24*1048576+1)
  if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:fail('SEC_ZIP_STREAM')
 else:raw=compressed
 if len(raw)!=a['uncompressed_bytes'] or zlib.crc32(raw)!=a['crc'] or sha(raw)!=digest:fail('SEC_MEMBER_INTEGRITY')
 data=json.loads(raw)
 if str(data.get('cik')).zfill(10)!=cik or not isinstance(data.get('facts'),dict):fail('SEC_MEMBER_IDENTITY')
 await env.DATA.put(cache,raw.decode())
 return data,{'key':cache,'sha256':digest,'archive_bytes_read':30+h[-2]+len(compressed),'cache':'MATERIALIZED_ONCE_FROM_EXISTING_CLOUD_SOURCE'}

class Default(WorkerEntrypoint):
 async def fetch(self,request):
  if not getattr(self.env,'TOKEN',None) or request.headers.get('Authorization')!='Bearer '+self.env.TOKEN:return Response('Unauthorized',status=401)
  try:
   if request.method=='GET' and urlparse(request.url).path=='/context':
    return Response(json.dumps({'runtime_version':VERSION,'assessed_at':datetime.now(timezone.utc).date().isoformat(),'manifest_sha256':MANIFEST_SHA}),headers={'content-type':'application/json','cache-control':'private, no-store'})
   if request.method!='POST' or urlparse(request.url).path!='/packet':fail('INVALID_PACKET_ROUTE')
   q=parse_qs(urlparse(request.url).query);symbol=q.get('symbol',[''])[0]
   if not re.fullmatch(r'[A-Z0-9][A-Z0-9.-]{0,24}',symbol):fail('INVALID_SYMBOL')
   index=await read(self.env.DATA,BASE+'full-history-2026-10-21-v1/symbol-batches.json')
   if symbol not in index:fail('SYMBOL_OUTSIDE_COHORT')
   batch=await read(self.env.DATA,BASE+f'full-history-2026-10-21-v1/batches/{index[symbol]}.json')
   row=next(r for r in batch['rows']if r['symbol']==symbol);cik=row['identity']['cik']
   if not row['financials']['cloud'].get('query_fingerprint'):fail('NO_PREVIOUSLY_MATERIALIZED_SEC_ISSUER')
   asof=datetime.now(timezone.utc).date().isoformat()
   done=await self.env.DATA.get(OUT+'packets/'+symbol+'.receipt.json')
   if done:
    receipt=json.loads(str(await done.text()))
    if receipt.get('runtime_version')==VERSION and receipt.get('assessed_at')==asof:
     await read(self.env.DATA,receipt['packet']['key'],receipt['packet']['sha256'])
     return Response(json.dumps(receipt),headers={'content-type':'application/json','cache-control':'private, no-store'})
   m=await read(self.env.DATA,MANIFEST,MANIFEST_SHA)
   ref=m['shards'][cik[-2:]];shard=await read(self.env.DATA,ref['key'],ref['sha256']);e=shard[cik]
   if e.get('quarantine') or not e.get('materialized'):fail('SEC_SOURCE_INELIGIBLE')
   facts,source=await member(self.env,m,e,cik)
   packet=build_packet(symbol,cik,[],facts,'2026-09-24',{'provider':'SEC_COMPANY_FACTS','sec_source':{'member_sha256':source['sha256'],'member_key':source['key']},'engine_release_id':m['release_id']})
   ref=await immutable(self.env,'packets',packet)
   gate=eligibility_gate(packet,symbol,asof);ready=valuation_readiness(packet,symbol,asof)
   diagnostic_ref=await immutable(self.env,'diagnostics',{'input_gate':gate,'readiness':ready})
   codes=sorted(set(re.match(r'[a-z_]+',r).group() if re.match(r'[a-z_]+',r) else 'ACCOUNTING_GATE_BLOCKED' for r in gate['reasons']))
   result={'symbol':symbol,'cik':cik,'status':'PPE_PACKET_REBUILT_IN_CLOUD','packet':ref,'diagnostics':diagnostic_ref,'source_member':source,'runtime_version':VERSION,'assessed_at':asof,'input_gate':{'eligible':gate['eligible'],'reason_codes':codes},'readiness':{'states':{k:v['met'] for k,v in ready['states'].items()},'valuation_ready':ready['valuation_ready']},'upstream_requests':0,'laptop_financial_payload_bytes':0,'assumption_status':'COMPANY_SPECIFIC_RESEARCH_REQUIRED'}
   await put(self.env,OUT+'packets/'+symbol+'.receipt.json',result)
   return Response(json.dumps(result),headers={'content-type':'application/json','cache-control':'private, no-store'})
  except Exception as error:
   code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z_]+',str(error)) else 'PACKET_BUILD_FAILED_'+type(error).__name__.upper()
   return Response(json.dumps({'error':code}),status=422 if isinstance(error,(ValueError,ProviderError,KeyError)) else 503,headers={'content-type':'application/json','cache-control':'private, no-store'})
