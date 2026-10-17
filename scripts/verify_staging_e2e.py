"""Verify a deployed DCF staging Worker end to end against live Zion staging.

Every check below runs over the public origin of the Worker under test and against the
live Zion staging pair (the financial history Worker and the DDFI benchmark Worker), so a
passing run is evidence about the deployment, not about a local double:

* the health and readiness probes and the provider advertisements;
* the attested native-history leg (`provider=zion_history`) -- the evidence is signed with
  the same bearer the Worker used to reach Zion, so a stale or foreign snapshot is refused;
* one full equity-claims bridge per filer: enterprise value recomputed from the attested
  bundle, claims fetched over the internal service binding, the per-share scenario saved to
  the staging D1, and the expected value compared with the local reconciliation run;
* the library-scoped export of the saved record, and a second identity's 404;
* the refusals: a foreign Origin cannot write, and a wrong engine pin cannot be served.

    python3 scripts/verify_staging_e2e.py \\
        --base https://dcf-valuation-engine-staging.scswitzer.workers.dev \\
        --output docs/receipts/staging-verification.json

The workflow saves three test research records to the staging D1 and writes its
aggregate receipt to the named local output file. Source publication pointers
are never changed.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def integration_artifacts():
    """The reconciliation artifacts, which the sibling checkout also holds.

    `scripts/verify_equity_claims.py` writes them under this checkout; the verified
    enterprise runs recorded earlier live beside it. ZION_INTEGRATION_ARTIFACTS names the
    directory explicitly when neither default applies.
    """
    candidates = [Path(os.environ['ZION_INTEGRATION_ARTIFACTS'])] if os.environ.get(
        'ZION_INTEGRATION_ARTIFACTS') else []
    candidates += [ROOT / 'artifacts/zero-subscription-integration',
                   ROOT.parent / 'artifacts/zero-subscription-integration']
    for candidate in candidates:
        if (candidate / 'AAPL-enterprise-verification.json').is_file():
            return candidate
    raise SystemExit('set ZION_INTEGRATION_ARTIFACTS to the reconciliation artifacts directory; '
                     'checked: ' + ', '.join(str(c) for c in candidates))


ARTIFACTS = integration_artifacts()
CIK = {'AAPL': '0000320193', 'MSFT': '0000789019', 'GOOGL': '0001652044'}
# The pinned DDFI corpus release for cost-of-capital assumptions (wacc, tax rate) and for
# sales-to-invested-capital, as published in the benchmark index.
PUBLISHED = {
    'wacc': ('11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9', 'wacc'),
    'tax_rate': ('11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9', 'tax_rate'),
    'sales_capital': ('bcd291a646f52393ae5e6b539cfd3936e08aba566f7e34fc39448d81ca7f816c',
                      'sales_to_invested_capital'),
}
SUBJECT = {'AAPL': 'Computers/Peripherals', 'MSFT': 'Software (System & Application)',
           'GOOGL': 'Advertising'}
# Independently recorded by the local reconciliation run (docs/financial-validation.md and
# the §10 receipts of the integration document). A drift here means the deployed chain is
# not reproducing the verified local arithmetic.
EXPECTED = {'AAPL': 119.21703451950214, 'MSFT': 271.57328289297936,
            'GOOGL': 188.18558019134235}
EVIDENCE_CUTOFF = '2026-09-24'
RESULTS = {}


def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(base, op, path, body=None, headers=None):
    data = None if body is None else json.dumps(body).encode()
    head = {'Origin': base, 'User-Agent': 'dcf-staging-verifier/1'}
    if data is not None:
        head['Content-Type'] = 'application/json'
    head.update(headers or {})
    if data is None:
        # The staging environment enables the platform cache, so a plain probe can answer with
        # the revision that was live when the entry was stored: a receipt read that way named
        # the previous commit minutes after a successful deploy. Every read probe is therefore
        # cache-busted, which is what makes the recorded revision the revision actually served.
        path += ('&' if '?' in path else '?') + 'cache_bust=' + str(time.time_ns())
    request = urllib.request.Request(base + path, data=data, headers=head,
                                     method='POST' if data else 'GET')
    try:
        response = op.open(request, timeout=180)
        raw, status, extra = response.read().decode(), response.status, dict(response.headers)
    except urllib.error.HTTPError as error:
        raw, status, extra = error.read().decode(), error.code, dict(error.headers)
    except Exception as error:
        return 0, None, {}, str(error)
    try:
        return status, json.loads(raw), extra, raw
    except ValueError:
        return status, None, extra, raw


def record(name, status, detail, ok=None):
    RESULTS[name] = dict(http_status=status, ok=(200 <= status < 300) if ok is None else ok,
                         detail=detail)
    print('%-42s %-4s %s' % (name, status, json.dumps(detail, sort_keys=True, default=str)[:280]))


def selection_mode(valuation_date):
    """`current` is only meaningful for a valuation dated the runtime's current UTC day.

    The engine refuses a selection that says "use the newest release" while the valuation is
    dated in the past, and that guard compares the valuation date with the wall clock, so a
    fixed valuation date would pass on the day it was pinned and fail on every later day. A
    valuation dated before today is a reproduction of a past date against an explicitly pinned
    release, which is exactly what `historical` expresses; the release pin is unchanged.
    """
    return ('current' if valuation_date == datetime.now(timezone.utc).date().isoformat()
            else 'historical')


def payload(ticker, financials, valuation_date):
    """The bridge request the engine sends: attested bundle, pinned assumptions, cutoff."""
    verification = json.loads((ARTIFACTS / f'{ticker}-enterprise-verification.json').read_bytes())
    result = verification['result']
    analyst = result['analyst_assumptions']
    mode = selection_mode(valuation_date)
    selections = {}
    for target in (result['benchmark_assumptions'] or {}):
        release_id, measure = PUBLISHED[target]
        selections[target] = dict(release_id=release_id, subject=SUBJECT[ticker], measure=measure,
                                  mode=mode, source='zion')
    body = dict(ticker=ticker, cik=CIK[ticker], valuation_date=valuation_date,
                source_asof=EVIDENCE_CUTOFF, financials=financials,
                benchmark_selections=selections,
                revenue_growth_rates=analyst['revenue_growth_rates'],
                terminal_growth=analyst['terminal_growth'], terminal_roic=analyst['terminal_roic'],
                suitable=True)
    if ticker == 'GOOGL':
        body['preferred_terms'] = json.loads(
            (ROOT / 'fixtures/alphabet-mandatory-convertible-terms.json').read_bytes())
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='deployed Worker origin under test')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--financial-asof', default=EVIDENCE_CUTOFF)
    parser.add_argument('--valuation-date', default='2026-10-15')
    parser.add_argument('--expected-commit',
                        help='fail unless /health reports this revision, so a receipt names '
                             'the revision it actually exercised')
    args = parser.parse_args()
    base = args.base.rstrip('/')
    op = opener()

    revision = None
    for path, name in (('/health', 'health'), ('/ready', 'ready')):
        status, body, _, raw = call(base, op, path)
        if name == 'health' and isinstance(body, dict):
            revision = (body.get('release') or {}).get('commit')
        if name == 'health' and args.expected_commit:
            served = (body or {}).get('release', {}).get('commit') if isinstance(body, dict) else None
            record(name, status, dict((body if isinstance(body, dict) else {"raw": raw[:160]}),
                                      expected_commit=args.expected_commit,
                                      commit_matches=(served == args.expected_commit)),
                   ok=(status == 200 and served == args.expected_commit))
            continue
        record(name, status, body if isinstance(body, dict) else raw[:160])
    status, body, _, raw = call(base, op, '/api/equity-claims/status')
    record('claims_status', status, body if isinstance(body, dict) else raw[:200])
    status, body, _, raw = call(base, op, '/api/providers')
    providers = (body or {}).get('providers', {}) if isinstance(body, dict) else {}
    record('providers', status, {k: v.get('configured') for k, v in sorted(providers.items())}
           if providers else raw[:200], ok=(status == 200
               and providers.get('zion_history', {}).get('configured') is True
               and providers.get('zion_benchmarks', {}).get('configured') is True))

    bridges = {}
    for ticker in ('AAPL', 'MSFT', 'GOOGL'):
        status, body, _, raw = call(base, op, '/api/financials',
                                    dict(provider='zion_history', ticker=ticker,
                                         valuation_date=args.financial_asof, cik=CIK[ticker]))
        document = (body or {}).get('financials') if isinstance(body, dict) else None
        if not isinstance(document, dict) or not document.get('source'):
            record(f'{ticker}_financials', status, raw[:300])
            continue
        source = document['source']
        record(f'{ticker}_financials', status, dict(
            adapter=source.get('adapter_version'), kind=source.get('kind'),
            historical_cutoff=source.get('historical_cutoff'),
            attestation_schema=(source.get('evidence_attestation') or {}).get('schema_version'),
            history_rows=len(document.get('historical') or [])))

        status, body, _, raw = call(base, op, '/api/equity-claims/bridge',
                                    payload(ticker, document, args.valuation_date))
        if status not in (200, 201) or not isinstance(body, dict):
            record(f'{ticker}_bridge', status, raw[:400])
            continue
        receipt = body.get('receipt') or {}
        claims_source = receipt.get('source') or {}
        bundle = claims_source.get('source_bundle') or {}
        equal = body.get('value_per_share') == EXPECTED[ticker]
        bridges[ticker] = body
        record(f'{ticker}_bridge', status, dict(
            id=body.get('id'), enterprise_value=body.get('enterprise_value'),
            equity_value=body.get('equity_value'), value_per_share=body.get('value_per_share'),
            matches_local_run=equal, scenario=body.get('scenario_name'),
            engine_release_id=body.get('release_id'),
            companion_release_id=bundle.get('source_release_id'),
            reconciliation=bundle.get('reconciliation_status'),
            snapshot_date=bundle.get('snapshot_date'),
            evidence_cutoff=claims_source.get('evidence_cutoff'),
            served_cutoff_utc=claims_source.get('served_cutoff_utc'),
            cutoff_policy=claims_source.get('cutoff_policy'),
            bridge_valuation_date=claims_source.get('bridge_valuation_date'),
            attestation=(receipt.get('attestation') or {}).get('transport'),
            binding=(receipt.get('attestation') or {}).get('binding'),
            authenticated_via=(claims_source.get('audit') or {}).get('authenticated_via'),
            caller=(claims_source.get('audit') or {}).get('caller'),
            benchmarks=sorted(((receipt.get('enterprise_scenario') or {})
                               .get('benchmark_assumptions') or {}).keys()),
            noncontrolling_policy=receipt.get('noncontrolling_policy'),
            preferred_evidence_state=receipt.get('preferred_evidence_state'),
        ), ok=(status in (200, 201) and equal))

    for ticker, saved in bridges.items():
        identity = saved['id']
        status, body, headers, raw = call(base, op,
                                          f'/api/equity-claims/bridges/{identity}/export/json')
        record(f'{ticker}_export', status, dict(
            content_type=headers.get('Content-Type'),
            disposition=headers.get('Content-Disposition'), bytes=len(raw),
            cik=(body or {}).get('cik') if isinstance(body, dict) else None,
            value_per_share=(body or {}).get('value_per_share')
            if isinstance(body, dict) else None))
        status2, _, _, _ = call(base, opener(),
                                f'/api/equity-claims/bridges/{identity}/export/json')
        record(f'{ticker}_export_other_identity', status2, 'a second library identity',
               ok=status2 == 404)

    status, body, _, raw = call(base, op, '/api/equity-claims/bridge',
                                dict(ticker='AAPL', cik=CIK['AAPL'],
                                     valuation_date=args.valuation_date, financials={},
                                     benchmark_selections={}),
                                headers={'Origin': 'https://evil.example'})
    record('foreign_origin_write', status, body if isinstance(body, dict) else raw[:160],
           ok=status == 403)

    if bridges:
        status, body, _, raw = call(base, op, '/api/financials',
                                    dict(provider='zion_history', ticker='AAPL',
                                         valuation_date=args.financial_asof, cik=CIK['AAPL']))
        pinned = payload('AAPL', body['financials'], args.valuation_date)
        pinned['expected_release_id'] = '0' * 64
        status, body, _, raw = call(base, op, '/api/equity-claims/bridge', pinned)
        record('wrong_engine_pin', status, body if isinstance(body, dict) else raw[:200],
               ok=status == 503)

        for name, mutation in (
            ('foreign_issuer_bundle', 'issuer'),
            ('edited_attested_bundle', 'evidence'),
            ('forged_attestation', 'mac'),
        ):
            rejected = deepcopy(pinned)
            rejected.pop('expected_release_id', None)
            if mutation == 'issuer':
                rejected.update(ticker='MSFT', cik=CIK['MSFT'])
            elif mutation == 'evidence':
                rejected['financials']['source']['native_history'][0]['observations'][0]['value_decimal'] = '1'
            else:
                rejected['financials']['source']['evidence_attestation']['hmac_sha256'] = '0' * 64
            status, body, headers, raw = call(base, op, '/api/equity-claims/bridge', rejected)
            if status == 429:
                # A refused rate-limited write has not created a record; wait once
                # for the existing staging abuse-protection window, then retry.
                time.sleep(min(60, max(1, int(headers.get('Retry-After', '60')))))
                status, body, _, raw = call(base, op, '/api/equity-claims/bridge', rejected)
            record(name, status, body if isinstance(body, dict) else raw[:200], ok=status == 400)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(
            dict(base=base, revision=revision, valuation_date=args.valuation_date,
                 selection_mode=selection_mode(args.valuation_date),
                 evidence_cutoff=EVIDENCE_CUTOFF, results=RESULTS),
            indent=1, sort_keys=True, default=str) + '\n')
    failures = {k: v['detail'] for k, v in RESULTS.items() if not v['ok']}
    print('\nchecks: %d  failures: %d' % (len(RESULTS), len(failures)))
    if failures:
        print(json.dumps(failures, indent=1, default=str)[:2500])
        raise SystemExit(1)


if __name__ == '__main__':
    main()
