"""Check a pinned Company Facts cohort through the live claims API and existing bridge.

Input enterprise scenarios must already have independent arithmetic reconciliation.
This tests issuer common-share scenarios, not tradable prices or security identities.
No remote writes, source promotion, class aggregation, or missing-to-zero replacement.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def reconcile(outcome):
    """Independent Decimal bridge, refusing unavailable or uncertified inputs."""
    if outcome['primary']['status'] != 'AVAILABLE' or outcome['unresolved']['blocking']:
        return None
    with localcontext() as ctx:
        ctx.prec = 40
        d = lambda v: Decimal(str(v))
        b = outcome['bridge']
        equity = d(outcome['enterprise_value']) + d(b['cash']) + d(b['other_nonoperating_assets'])
        equity -= sum(d(b[k]) for k in ('short_term_debt','long_term_debt','preferred_equity','minority_interest'))
        selected = outcome['scenarios'][outcome['primary_scenario']]
        shares = d(outcome['shares_outstanding']) + d(selected['shares_added'])
        per_share = equity / shares
        error = abs(per_share - d(outcome['primary']['value_per_share']))
        if error >= Decimal('0.000001'):
            raise ValueError('Independent bridge reconciliation failed')
        return dict(equity_value_decimal=str(equity), value_per_share_decimal=str(per_share),
                    absolute_error_decimal=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enterprise-receipt', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--credential-file', type=Path, default=Path.home()/'.config/zion/private-api.env')
    parser.add_argument('--base', default='https://zion-financial-serving-v2-thin-staging.scswitzer.workers.dev')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must be new')
    enterprise = json.loads(args.enterprise_receipt.read_bytes())
    raw = args.source_manifest.read_bytes()
    manifest = json.loads(raw)
    members = manifest['members']
    if not 1 <= len(members) <= 500 or manifest['rights'] != 'PUBLIC_SEC_ONLY':
        parser.error('A bounded public SEC manifest is required')
    token = None
    for line in args.credential_file.read_text().splitlines():
        key, sep, value = line.removeprefix('export ').partition('=')
        if sep and key == 'ZION_PRIVATE_API_TOKEN':
            token = value.strip().strip("\"'")
    if not token:
        parser.error('Existing owner credential unavailable')
    from dcf_loader import JsonHTTP, ProviderError
    from equity_claims_provider import load_equity_claims, unresolved_claims, value_per_share
    by_cik = {r['cik']:r for r in enterprise['results']}
    results = []
    for cik in members:
        row = by_cik.get(cik, {})
        result = dict(cik=cik,ticker=row.get('ticker'),status='BLOCKED')
        try:
            claims = load_equity_claims(row.get('ticker') or cik, row.get('valuation_date') or '2026-10-15',
                JsonHTTP(budget=40), cik=cik, base=args.base, token=token,
                expected_release_id=enterprise['screen']['engine_release_id'],
                source_asof=enterprise['screen']['archive_cutoff'],
                expected_source_release_id=manifest['release_id'])
            result.update(claims_verified=True,source_release_id=claims['source']['source_bundle']['source_release_id'],
                claim_states={k:dict(state=v['evidence_state'],permitted=v.get('permitted_for_valuation'))
                              for k,v in claims['claims'].items()},
                unresolved=unresolved_claims(claims))
            if (row.get('status') != 'ENTERPRISE_SCENARIO_VERIFIED'
                    or Decimal(row.get('independent_absolute_error_decimal','Infinity')) >= Decimal('.01')):
                result['blocker'] = 'NO_INDEPENDENTLY_VERIFIED_ENTERPRISE_SCENARIO'
            else:
                outcome = value_per_share(row['enterprise_value'], claims)
                result.update(primary=outcome['primary'],scenario=outcome['primary_scenario'],
                              shares_basis=outcome['shares_basis'])
                independent = reconcile(outcome)
                if independent is not None:
                    result.update(status='ISSUER_COMMON_SHARE_SCENARIO_VERIFIED',independent=independent)
                else:
                    result['blocker'] = 'UNRESOLVED_EQUITY_CLAIMS'
        except (ProviderError,ValueError,KeyError) as error:
            result['blocker'] = 'CLAIMS_OR_BRIDGE_REFUSED'
            result['reason'] = str(error).replace(token,'[redacted]')[:280]
        results.append(result)
        print(json.dumps(dict(cik=cik,status=result['status'],blocker=result.get('blocker'))),flush=True)
    receipt = dict(schema_version='claims-cohort-acceptance-v1',generated_utc=datetime.now(timezone.utc).isoformat(),
        selected=len(members),accounted=len(results),counts=dict(Counter(r['status'] for r in results)),
        claims_verified=sum(r.get('claims_verified',False) for r in results),
        source_release_id=manifest['release_id'],source_manifest_sha256=hashlib.sha256(raw).hexdigest(),
        engine_release_id=enterprise['screen']['engine_release_id'],results=results,
        execution='LIVE_AUTHENTICATED_CLAIMS_API_WITH_EXISTING_LOCAL_BRIDGE',
        qualifications=['STANDARDIZED_RESEARCH_SCENARIOS_NOT_COMPANY_FORECASTS',
                        'ISSUER_COMMON_SHARE_COUNTS_NOT_CERTIFIED_SECURITY_PRICES',
                        'NO_CALLER_PREFERRED_CONVERSION_ASSUMPTIONS_ADDED'],
        remote_writes=0,publication_pointer_writes=0)
    with args.output.open('x') as handle:
        json.dump(receipt,handle,indent=2,allow_nan=False)
    print(json.dumps({k:receipt[k] for k in ('selected','accounted','counts','claims_verified')}))


if __name__ == '__main__':
    main()
