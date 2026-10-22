"""Account for 50 screened issuers through existing providers and valuation routes.

Reads live Zion plus the public SEC ticker directory. Uses an isolated temporary LOCAL
account/store for the new private screen routes, never a fake authenticated user or production
account. The three optional scenarios reuse already-reviewed, explicitly dated assumptions.
No remote records, source pointers or credentials are written.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def account_cohort(rows, evaluate):
    ciks = [row['cik'] for row in rows]
    if len(ciks) != len(set(ciks)):
        raise ValueError('Select distinct issuers')
    results = []
    for row in rows:
        try:
            result = evaluate(row)
            if result.get('cik') != row['cik'] or result.get('status') not in ('BLOCKED', 'ENTERPRISE_SCENARIO_VERIFIED'):
                raise ValueError('Invalid cohort result')
        except Exception as error:
            result = dict(cik=row['cik'], status='BLOCKED',
                          blockers=['TRANSPORT_OR_INPUT_FAILURE:' + type(error).__name__])
        results.append(result)
        print(json.dumps(dict(cik=row['cik'], status=result['status'])), flush=True)
    return dict(selected=len(rows), accounted=len(results), results=results,
                counts=dict(Counter(row['status'] for row in results)))


def standard_scenario(prepared, *, industry, valuation_date, growth, terminal_growth, terminal_roic):
    """A labelled research scenario, never a substitute for missing company observations."""
    import math
    from copy import deepcopy
    from datetime import date
    if (not industry or not valuation_date or any(value is None or not math.isfinite(value)
            for value in (growth,terminal_growth,terminal_roic))):
        raise ValueError('An explicit industry, date and every forecast assumption are required')
    date.fromisoformat(valuation_date)
    body=deepcopy(prepared['request_template'])
    body.update(valuation_date=valuation_date,revenue_growth_rates=[growth]*5,
                terminal_growth=terminal_growth,terminal_roic=terminal_roic,suitable=True,
                benchmark_selections={target:dict(ref,subject=industry,mode='historical',source='zion')
                    for target,ref in prepared['benchmark_references'].items()})
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credential-file', type=Path,
                        default=Path.home()/'.config/zion/private-api.env')
    parser.add_argument('--base', default='https://zion-financial-serving-v2-thin-staging.scswitzer.workers.dev')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewed-scenarios', action='store_true',
                        help='Run the three explicitly reviewed October 15 assumptions')
    parser.add_argument('--size', type=int, default=50)
    parser.add_argument('--scenario-industry')
    parser.add_argument('--scenario-date')
    parser.add_argument('--growth', type=float)
    parser.add_argument('--terminal-growth', type=float)
    parser.add_argument('--terminal-roic', type=float)
    args = parser.parse_args()
    if not 3 <= args.size <= 500:
        parser.error('Choose 3 to 500 issuers')
    if args.scenario_industry:
        standard_scenario({'request_template':{},'benchmark_references':{}},
            industry=args.scenario_industry,valuation_date=args.scenario_date,growth=args.growth,
            terminal_growth=args.terminal_growth,terminal_roic=args.terminal_roic)
    values = {}
    for line in args.credential_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.removeprefix('export ').split('=', 1)
            values[key] = value.strip().strip("\"'")
    token = values['ZION_PRIVATE_API_TOKEN']
    os.environ.update(ZION_HISTORY_TOKEN=token, ZION_HISTORY_BASE_URL=args.base,
                      ZION_BENCHMARK_TOKEN=token,
                      ZION_BENCHMARK_BASE_URL='https://zion-ddfi-benchmark-staging.scswitzer.workers.dev')
    from app import app, resolve_benchmark_selections
    from enterprise_valuation import value_enterprise
    from research_screen import BENCHMARK_REFERENCES
    from dcf_loader import ProviderError, load_document
    from issuer_classification import reviewed_identity
    from research_screen import issuer_identity, load_screen
    from recover_sec_shares import get
    import requests

    screen = load_screen({'method':'operating_dcf', 'limit':str(args.size)})
    special = {'0000320193':'AAPL', '0000789019':'MSFT', '0001652044':'GOOGL'}
    rows = [row for row in screen['matches'] if row['cik'] not in special][:args.size-3]
    for cik in special:
        page = load_screen({'cik':cik, 'expected_index_id':screen['index_id']})
        rows.extend(page['matches'])
    if len(rows) != args.size:
        raise ValueError('The source did not provide the requested distinct issuer count')
    session = requests.Session()
    session.headers['User-Agent'] = 'Zion Financial Research scswitzer@chapman.edu'
    directory_url = 'https://www.sec.gov/files/company_tickers.json'
    directory = get(session, directory_url)
    aliases = {}
    for item in json.loads(directory).values():
        aliases.setdefault(str(item['cik_str']).zfill(10), []).append(item['ticker'])
    with tempfile.TemporaryDirectory(prefix='dcf-cohort-') as tmp:
        os.environ['DCF_STATE_PATH'] = str(Path(tmp)/'state.sqlite3')
        app.config.update(TESTING=True, STATE_PATH=str(Path(tmp)/'limits.sqlite3'))
        client = app.test_client()
        signup = client.post('/api/account/signup', json={
            'email':'cohort-acceptance@example.invalid', 'password':secrets.token_urlsafe(30)})
        if signup.status_code != 201 and signup.status_code != 200:
            raise ValueError('Local test account could not be created')

        shared_benchmarks = None
        if args.scenario_industry:
            selection = standard_scenario({'request_template':{},'benchmark_references':BENCHMARK_REFERENCES},
                industry=args.scenario_industry,valuation_date=args.scenario_date,growth=args.growth,
                terminal_growth=args.terminal_growth,terminal_roic=args.terminal_roic)
            with app.test_request_context():
                shared_benchmarks = resolve_benchmark_selections(selection['benchmark_selections'],args.scenario_date)

        def evaluate(row):
            cik = row['cik']
            symbol = special.get(cik) or next(iter(aliases.get(cik, [])), None)
            result = dict(cik=cik, label=row['label'], status='BLOCKED',
                          screening_missing=row['missing'], blockers=[], ticker=symbol)
            if not symbol:
                result['blockers'] = ['MISSING_CURRENT_TICKER_ALIAS', 'DATED_ASSUMPTIONS_REQUIRED']
                return result
            try:
                doc = load_document('zion_history', symbol, screen['archive_cutoff'], cik=cik,
                                    expected_release_id=screen['engine_release_id'])
            except ProviderError as error:
                result['blockers'] = ['NATIVE_HISTORY_ADAPTER_REFUSED_INPUTS', 'DATED_ASSUMPTIONS_REQUIRED']
                result['adapter_refusal'] = str(error).replace(token, '[redacted]')[:256]
                return result
            result.update(history_periods=[r['period_end'] for r in doc['historical']],
                          financial_release_id=doc['source']['release_id'],
                          source_missing=doc['source']['missing_fields'],
                          ticker_identity='DATED_REVIEWED' if reviewed_identity(symbol,cik,screen['archive_cutoff']) else 'CURRENT_ALIAS_ONLY_NOT_HISTORICAL')
            identity = issuer_identity(symbol,cik,screen['archive_cutoff'])
            result['issuer_identity'] = identity
            if identity is None:
                result['blockers'].append('SEC_ISSUER_ALIAS_MISMATCH')
                return result
            if not args.scenario_industry and (cik not in special or not args.reviewed_scenarios):
                result['blockers'].append('DATED_ASSUMPTIONS_REQUIRED')
                return result
            if args.scenario_industry and cik not in special:
                # Reuse the exact public model function and the already pinned common
                # benchmark observations. No API-rate-limit bypass is claimed as API proof.
                financials = doc
                body=standard_scenario({'request_template':dict(ticker=symbol,cik=cik,
                    financials=doc,source_asof=screen['archive_cutoff'],expected_release_id=screen['engine_release_id']),
                    'benchmark_references':BENCHMARK_REFERENCES},industry=args.scenario_industry,
                    valuation_date=args.scenario_date,growth=args.growth,
                    terminal_growth=args.terminal_growth,terminal_roic=args.terminal_roic)
                try:
                    valuation=value_enterprise(doc,shared_benchmarks,body['revenue_growth_rates'],
                        body['terminal_growth'],body['terminal_roic'],valuation_date=body['valuation_date'],
                        suitable=True,evidence_secret=token)
                except ValueError as error:
                    result['blockers'].append('ENTERPRISE_MODEL_REFUSED_INPUTS')
                    result['calculation_error']=str(error).replace(token,'[redacted]')[:256]
                    return result
                result['execution_path']='EXISTING_PROVIDER_AND_MODEL_WITH_LIVE_SOURCES'
            else:
                prepared = client.post('/api/research-screen/prepare', json={
                    'ticker':symbol, 'cik':cik, 'expected_index_id':screen['index_id']})
                if prepared.status_code != 200:
                    result['blockers'].append('PREPARE_HTTP_' + str(prepared.status_code))
                    return result
                financials=prepared.json['financials']
                if args.scenario_industry:
                    body=standard_scenario(prepared.json,industry=args.scenario_industry,
                        valuation_date=args.scenario_date,growth=args.growth,
                        terminal_growth=args.terminal_growth,terminal_roic=args.terminal_roic)
                else:
                    try:
                        from verify_staging_e2e import payload
                    except SystemExit:
                        result['blockers'].append('REVIEWED_SCENARIO_ARTIFACTS_MISSING')
                        return result
                    body = payload(symbol, financials, '2026-10-15')
                response = client.post(prepared.json['calculate_endpoint'], json=body)
                if response.status_code != 200:
                    result['blockers'].append('ENTERPRISE_CALCULATION_HTTP_' + str(response.status_code))
                    result['calculation_error'] = response.json.get('error')
                    return result
                valuation = response.json
                result['execution_path']='AUTHENTICATED_LOCAL_API_WITH_LIVE_SOURCES'
            # Independent Decimal arithmetic, not a second call to the DCF implementation.
            from decimal import Decimal, localcontext
            with localcontext() as context:
                context.prec = 40
                D = lambda value: Decimal(str(value))
                last = financials['historical'][-1]
                revenue, margin = D(last['revenue']), D(last['ebit'])/D(last['revenue'])
                refs = valuation['benchmark_assumptions']
                wacc, tax, efficiency = (D(refs[k]['value_decimal']) for k in ('wacc','tax_rate','sales_capital'))
                pv = Decimal(0)
                for year, growth in enumerate(body['revenue_growth_rates'],1):
                    previous, revenue = revenue, revenue*(1+D(growth))
                    nopat = revenue*margin*(1-tax)
                    pv += (nopat-(revenue-previous)/efficiency)/(1+wacc)**year
                g, roic = D(body['terminal_growth']), D(body['terminal_roic'])
                independent = pv + nopat*(1+g)*(1-g/roic)/(wacc-g)/(1+wacc)**len(body['revenue_growth_rates'])
                error = abs(D(valuation['enterprise_value'])-independent)
            if error >= Decimal('.01') or valuation['equity_value'] is not None or valuation['intrinsic_value'] is not None:
                raise ValueError('Independent enterprise reconciliation failed')
            result.update(status='ENTERPRISE_SCENARIO_VERIFIED', blockers=[],
                          enterprise_value=valuation['enterprise_value'],
                          equity_value=None, value_per_share=None,
                          equity_blockers=['MATCHING_CLAIMS_ENGINE_RELEASE_REQUIRED'],
                          independent_absolute_error_decimal=str(error),
                          valuation_date=body['valuation_date'],
                          assumption_source=('STANDARDIZED_RESEARCH_SCENARIO_NOT_COMPANY_FORECAST' if args.scenario_industry else 'EXPLICIT_PREVIOUSLY_REVIEWED_SCENARIO'),
                          analyst_assumptions=valuation['analyst_assumptions'],
                          benchmark_assumptions=valuation['benchmark_assumptions'])
            return result

        report = account_cohort(rows, evaluate)
    report.update(schema_version='usable-sec-cohort-v1',
                  generated_utc=datetime.now(timezone.utc).isoformat(),
                  execution=('LOCAL_PROVIDER_AND_MODEL_WITH_THREE_API_CASES_AND_LIVE_ZION_SOURCES' if args.scenario_industry else 'LOCAL_DCF_ROUTES_WITH_LIVE_ZION_SOURCES'),
                  screen={k:screen[k] for k in ('index_id','release_id','engine_release_id','archive_cutoff','availability_cutoff')},
                  ticker_directory=dict(url=directory_url, sha256=hashlib.sha256(directory).hexdigest(),
                                        historical_eligible=False),
                  remote_writes=0, publication_pointer_writes=0)
    fd = os.open(args.output, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(selected=report['selected'],accounted=report['accounted'],counts=report['counts'])))


if __name__ == '__main__':
    main()
