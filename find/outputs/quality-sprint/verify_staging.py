import json,time,requests
from pathlib import Path
root=Path(__file__).resolve().parent
base='https://dcf-valuation-engine-staging.scswitzer.workers.dev'
s=requests.Session()
health=s.get(base+'/health',timeout=30).json()
assert health['release']['commit']=='6eb7821332b8d8ecb59e3ed55c59245b41630e23' and not health['release']['tracked_dirty']
checks=[]
for ticker in ['AAPL','PEP']:
 rates=[.231,.24,.25,.26,.27]
 r=s.post(base+'/api/load/dcf',json={'ticker':ticker,'tax_override':rates},timeout=45)
 r.raise_for_status();b=r.json()
 assert b['load_summary']['assembly_cache']['state']=='BYPASSED',b.get('load_summary')
 assert [b['form'][f'tax_rate_{i}']/100 for i in range(5)]==rates
 assert b['preview']['assumptions']['tax_rates']==rates
 assert b['preview']['wacc']==b['brief']['dcf']['wacc']
 assert b['preview']['intrinsic_value']==b['brief']['dcf']['intrinsic_value']
 # JSON preview on the same snapshot; no save or export persistence.
 raw={'financials':b['financials'],'assumptions':b['preview']['assumptions']}
 p=s.post(base+'/api/preview/dcf',json=raw,timeout=30);p.raise_for_status();p=p.json()
 assert p['wacc']==b['preview']['wacc'] and p['intrinsic_value']==b['preview']['intrinsic_value']
 assert p['input_financials']['historical']==b['financials']['historical']
 checks.append({'ticker':ticker,'state':'BYPASSED','source':b['financials']['source'].get('statement_source'),'wacc':p['wacc'],'price':p['intrinsic_value'],'tax_rates':rates,'historical_preserved':True,'form_preview_brief_json_parity':True,'stage_seconds':b['load_summary']['stage_seconds']})
 time.sleep(7)
# Read-only method loads; deliberately no account/research writes.
for ticker in ['CAT','T','PAYX','ORCL']:
 r=s.post(base+'/api/load/dcf',json={'ticker':ticker},timeout=45)
 b=r.json()
 checks.append({'ticker':ticker,'status':r.status_code,'source':(b.get('financials') or {}).get('source',{}).get('statement_source'),'error':b.get('error'),'cache':b.get('load_summary',{}).get('assembly_cache',{})})
 if ticker=='ORCL': assert r.status_code>=400
 else: assert r.status_code==200 and b['financials']['source']['statement_source']=='SEC-first'
 time.sleep(7)
report={'health':health,'checks':checks,'scope':'Staging only, no accounts, research or financial-data writes'}
(root/'staging-parity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
