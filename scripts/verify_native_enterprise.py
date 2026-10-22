"""Reproduce a frozen public-data enterprise scenario through the existing API.

No provider calls, acquisition or cloud writes. Inputs are native-history probe
exports and PPE Damodaran releases. Equity/per-share values must remain null.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app  # noqa: E402


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--financials',type=Path,required=True)
    parser.add_argument('--releases',type=Path,required=True)
    parser.add_argument('--industry',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--growth',type=Decimal,required=True)
    parser.add_argument('--terminal-growth',type=Decimal,required=True)
    parser.add_argument('--terminal-roic',type=Decimal,required=True)
    args=parser.parse_args()
    doc=json.loads(args.financials.read_bytes())
    ids={}
    for path in args.releases.iterdir():
        if path.name.startswith('.') or not path.is_dir():continue
        manifest=json.loads((path/'manifest.json').read_bytes())
        dataset=manifest['dataset_id']
        if dataset in ids:raise ValueError('Multiple dataset releases; provide a directory with explicitly selected versions')
        ids[dataset]=path.name
    os.environ['DAMODARAN_RELEASE_ROOT']=str(args.releases.resolve())
    if not os.environ.get('ZION_HISTORY_TOKEN'):
        raise ValueError('Configure ZION_HISTORY_TOKEN to verify server-attested native history.')
    selected={target:dict(release_id=ids[dataset],subject=args.industry,measure=measure,mode='current')
              for target,dataset,measure in [('wacc','cost_of_capital','wacc'),
                  ('tax_rate','cost_of_capital','tax_rate'),('sales_capital','reinvestment','sales_capital')]}
    response=app.test_client().post('/api/calculate/enterprise',json=dict(
        financials=doc,valuation_date=datetime.now(timezone.utc).date().isoformat(),
        benchmark_selections=selected,revenue_growth_rates=[float(args.growth)]*5,
        terminal_growth=float(args.terminal_growth),terminal_roic=float(args.terminal_roic),suitable=True))
    if response.status_code!=200:raise ValueError('Enterprise calculation rejected: '+str(response.json))
    result=response.json
    with localcontext() as context:
        context.prec=40
        actual=doc['historical'][-1]
        rev=Decimal(str(actual['revenue']));margin=Decimal(str(actual['ebit']))/rev
        chosen=result['benchmark_assumptions']
        wacc=Decimal(chosen['wacc']['value_decimal']);tax=Decimal(chosen['tax_rate']['value_decimal'])
        efficiency=Decimal(chosen['sales_capital']['value_decimal']);stage=Decimal(0)
        for year in range(1,6):
            previous=rev;rev*=1+args.growth;nopat=rev*margin*(1-tax)
            fcff=nopat-(rev-previous)/efficiency
            stage+=fcff/(1+wacc)**year
        terminal=nopat*(1+args.terminal_growth)*(1-args.terminal_growth/args.terminal_roic)/(wacc-args.terminal_growth)
        independent=stage+terminal/(1+wacc)**5
        error=abs(Decimal(str(result['enterprise_value']))-independent)
    if error>=Decimal('.01') or result['equity_value'] is not None or result['intrinsic_value'] is not None:
        raise ValueError('Independent valuation or missing-bridge gate failed')
    summary=dict(ticker=doc['company']['ticker'],http_status=200,status=result['status'],
        enterprise_value=result['enterprise_value'],independent_enterprise_value_decimal=str(independent),
        absolute_error_decimal=str(error),financial_release=doc['source']['release_id'],
        benchmark_releases=ids,industry_assumption=args.industry,
        equity_value=None,intrinsic_value=None,valuation_date=result['valuation_date'])
    fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(dict(summary=summary,result=result),stream,allow_nan=False)
    print(json.dumps(summary,allow_nan=False))


if __name__=='__main__':main()
