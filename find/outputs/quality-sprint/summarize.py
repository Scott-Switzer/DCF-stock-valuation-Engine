import json,math
from pathlib import Path
root=Path(__file__).resolve().parent
def q(values,p):
 values=sorted(values)
 return values[max(0,math.ceil(len(values)*p)-1)] if values else None
def stats(values):return {'n':len(values),'p50_ms':q(values,.5),'p95_ms':q(values,.95),'min_ms':min(values) if values else None,'max_ms':max(values) if values else None}
def summarize(filename):
 d=json.loads((root/filename).read_text());groups={};rows=[]
 for o in d['observations']:
  b=o.get('loadBody') or {}; state=b.get('cacheState') or 'UNKNOWN';source=b.get('statementSource') or 'UNKNOWN'
  def mark(key):
   v=[v-o['t0'] for k,v in o.get('marks',[]) if k==key]
   return v[0] if v else None
  resource=next((r for r in o.get('resources',[]) if r['url'].endswith('load/dcf')),{})
  row={'ticker':o['ticker'],'state':state,'source':source,'value_ms':mark('workspace:value-painted'),'editor_ready_ms':mark('workspace:editor-ready:dcf'),'brief_ms':mark('workspace:brief-painted'),'load_response_ms':mark('workspace:load-response'),'request_duration_ms':resource.get('duration'),'transfer_bytes':resource.get('transferSize'),'stages_s':b.get('stageSeconds'),'status':o.get('loadStatus'),'error':o.get('error'),'timeout':o.get('timeout',False)}
  rows.append(row)
  for group in [state,state+'/'+source]:groups.setdefault(group,[]).append(row)
 return {'file':filename,'commit':d['revision']['commit'],'groups':{k:{'samples':len(v),'successful_value_paints':stats([r['value_ms'] for r in v if r['value_ms'] is not None]),'request_duration':stats([r['request_duration_ms'] for r in v if r['request_duration_ms'] is not None]),'editor_ready':stats([r['editor_ready_ms'] for r in v if r['editor_ready_ms'] is not None])} for k,v in groups.items()},'rows':rows}
files=['before-browser.json','after-browser.json','production-readonly-browser.json']
out={'quantile':'nearest rank ceil(p*n), not interpolated; first value-painted mark relative to submit; cold labels do not establish provider-cache misses','runs':[summarize(f) for f in files]}
(root/'performance-summary.json').write_text(json.dumps(out,indent=2))
for d in out['runs']:
 print(d['file'],d['commit'])
 for k,v in d['groups'].items():print(k,v['successful_value_paints'])
 print('MISS',[(r['ticker'],r['value_ms'],r['stages_s']) for r in d['rows'] if r['state']=='MISS'])
