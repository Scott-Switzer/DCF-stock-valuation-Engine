#!/usr/bin/env python3
"""Non-saving Zion -> DCF transport and client-observed latency audit.

GET public compact/assembled packets; optionally POST load and preview only.
Never flush caches, change publication pointers, save models or access accounts.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from company_packets import transport_evidence, valuation_date  # noqa: E402
from dcf_loader import ProviderError, parse_document, ticker_symbol  # noqa: E402
from ppe_packets import validate_packet  # noqa: E402
from reconciliation.reference_dcf import compare_result, reference_dcf  # noqa: E402
from scripts.build_company_ledger import write_json_atomic  # noqa: E402

VERSION = 'zion-dcf-pipeline-audit-v1'
MAXIMUM = 2_000_000
ASSUMPTIONS = {'revenue_growth_rates': [0.05] * 5, 'wacc_override': 0.10,
               'terminal_growth_rate': 0.02}
HEADERS = ('Cache-Control', 'Age', 'CF-Cache-Status', 'CF-Ray', 'Content-Type')


def percentile(values, quantile):
    """Nearest rank; descriptive only, with no interpolation hiding tail samples."""
    return sorted(values)[math.ceil(quantile * len(values)) - 1] if values else None


def distribution(values):
    return {'count': len(values), 'p50_seconds': percentile(values, .50),
            'p95_seconds': percentile(values, .95), 'max_seconds': max(values) if values else None,
            'sample_warning': 'SMALL_SAMPLE' if len(values) < 20 else 'SINGLE_CLIENT_NOT_GLOBAL_SLO'}


class Client:
    def __init__(self, base, timeout, delay, session=None):
        self.base, self.timeout, self.delay = base.rstrip('/'), timeout, delay
        self.session = session or requests.Session()
        self.next_start = 0

    def fetch(self, path, payload=None):
        time.sleep(max(0, self.next_start - time.monotonic()))
        start = time.monotonic()
        self.next_start = start + self.delay
        record = {'path': path, 'method': 'GET' if payload is None else 'POST',
                  'observed_at': datetime.now(timezone.utc).isoformat()}
        try:
            with self.session.request(
                record['method'], self.base + path, json=payload, stream=True,
                timeout=self.timeout, allow_redirects=False,
                headers={'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (DCF pipeline audit)'},
            ) as response:
                record['http_status'] = response.status_code
                record['headers'] = {key: response.headers.get(key) for key in HEADERS}
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAXIMUM:
                        raise ValueError('Response exceeds audit byte budget.')
                    chunks.append(chunk)
                body = b''.join(chunks)
                record['bytes'] = size
                record['body_sha256'] = hashlib.sha256(body).hexdigest()
                if response.status_code != 200:
                    raise ValueError(f'HTTP {response.status_code}; no retry or failure discarded.')
                if 'application/json' not in response.headers.get('Content-Type', '').lower():
                    raise ValueError('Expected application/json.')
                value = json.loads(body, parse_constant=lambda x: reject_constant(x))
                if not isinstance(value, dict):
                    raise ValueError('Expected a JSON object.')
                if 'saved_record_id' in value:
                    raise ValueError('Unexpected persisted valuation response.')
                record['status'] = 'PASS'
                return record, value
        except (requests.RequestException, ValueError, UnicodeError) as exc:
            record.update(status='FAIL', reason=str(exc))
            return record, None
        finally:
            record['seconds'] = round(time.monotonic() - start, 6)


def reject_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def contract_record(record, value, endpoint, ticker, asof):
    """Check the delivered contract, not just HTTP success. Preserve every failure."""
    record.update(endpoint=endpoint, ticker=ticker, valuation_date=asof)
    if value is None:
        return
    try:
        if endpoint == 'compact':
            validate_packet(value, ticker, asof)
            record['packet_cutoff'] = value['cutoff_date']
            record['transport'] = transport_evidence({'source': {'ppe_release': value['source']}})
            record['cache_state'] = 'STORAGE_UNKNOWN'
        else:
            if endpoint == 'assembled':
                if value.get('schema_version') != 'company-packet-v1' or value.get('ticker') != ticker or value.get('valuation_date') != asof:
                    raise ValueError('Assembled packet schema, ticker or date mismatch.')
                record['quality_status'] = value.get('status')
                if value.get('status') not in {'PASS', 'PARTIAL'}:
                    raise ValueError(f"Company packet is not usable: {value.get('status')}; {value.get('reason', '')}")
                doc, cache = value['financials'], value.get('cache')
            else:
                doc = value['financials']
                cache = value.get('load_summary', {}).get('assembly_cache')
            if doc['company']['ticker'] != ticker or doc['valuation_date'] != asof:
                raise ValueError('Financial snapshot ticker or valuation date mismatch.')
            if doc.get('source', {}).get('kind') == 'synthetic':
                raise ValueError('Synthetic data is not real-company acceptance.')
            parse_document(doc)
            record['transport'] = transport_evidence(doc, cache)
            record['cache_state'] = (cache or {}).get('state', 'UNKNOWN')
            record['assembly_cache'] = cache
            record['source_verification'] = 'NOT_ESTABLISHED'
        headers = record.get('headers', {})
        cache_status = (headers.get('CF-Cache-Status') or '').upper()
        outer_cached = cache_status in {'HIT', 'STALE', 'UPDATING', 'REVALIDATED'} or headers.get('Age') is not None
        no_store = 'no-store' in (headers.get('Cache-Control') or '').lower()
        record['invocation_evidence'] = (
            'CACHED_SNAPSHOT_ORIGIN_ONLY' if outer_cached or record['cache_state'] == 'HIT'
            else 'RESPONSE_ORIGIN_RECEIPT' if no_store else 'REPORTED_ORIGIN_OUTER_CACHE_NOT_EXCLUDED'
        )
    except (ProviderError, ValueError, KeyError, TypeError, AttributeError) as exc:
        record.update(status='FAIL', reason=str(exc))


def summarize(records):
    groups = {}
    for record in records:
        if record.get('endpoint') not in {'compact', 'assembled', 'load', 'preview', 'load_preview_flow'}:
            continue
        key = f"{record['endpoint']}:{record.get('cache_state', 'NOT_APPLICABLE')}"
        group = groups.setdefault(key, {'attempts': 0, 'failures': 0, 'seconds': [], 'failed_seconds': []})
        group['attempts'] += 1
        group['failures'] += record['status'] != 'PASS'
        group['seconds' if record['status'] == 'PASS' else 'failed_seconds'].append(record['seconds'])
    for group in groups.values():
        group['successful_latency'] = distribution(group.pop('seconds'))
        group['failed_latency'] = distribution(group.pop('failed_seconds'))
    return groups


def run(client, tickers, asof, samples, flow=False, require_zion=False, checkpoint=None):
    report = {'schema_version': VERSION, 'base': client.base, 'as_of': asof,
              'started_at': datetime.now(timezone.utc).isoformat(), 'samples_per_ticker': samples,
              'tickers': tickers, 'flow_enabled': flow, 'require_zion': require_zion,
              'measurement': {'connection': 'requests.Session connection reuse attempted, not guaranteed',
                              'concurrency': 1, 'delay_seconds': client.delay, 'timeout_seconds': client.timeout,
                              'cache_flush': False, 'cold_start': 'NOT_ESTABLISHED',
                              'percentile': 'nearest rank', 'location': 'CF-Ray suffix retained per request'},
              'proposed_targets_seconds': {'cached_packet_p95': .250, 'uncached_packet_p95': .750,
                                          'full_workspace_p95': 2.0},
              'target_acceptance': 'NOT_ESTABLISHED: storage cache, cold starts, browser render and realistic concurrency are not controlled.',
              'limitations': ['Single-client elapsed time includes network and body transfer, excludes pacing and contract checks.',
                              'First/repeated requests are not cold/warm evidence; assembly HIT/MISS is not storage cache state.',
                              'Load-preview flow excludes browser rendering, editor readiness, debounce and optional references.',
                              'Transport receipts certify the reported serving path, not independent financial source accuracy.',
                              'Failures are retained separately; success-only p95 is not an availability SLO.'],
              'records': []}

    def append(record):
        report['records'].append(record)
        if checkpoint:
            checkpoint(report)

    initial, health = client.fetch('/health')
    initial['endpoint'] = 'health_before'
    report['release_before'] = (health or {}).get('release')
    if health is not None and (health.get('status') != 'healthy' or not isinstance(health.get('release'), dict) or not health['release'].get('commit')):
        initial.update(status='FAIL', reason='Unhealthy deployment or missing release identity.')
    append(initial)
    ready_record, ready = client.fetch('/ready')
    ready_record['endpoint'] = 'readiness'
    report['readiness'] = ready
    if ready is not None and ready.get('status') != 'ready':
        ready_record.update(status='FAIL', reason='Deployment is not ready.')
    append(ready_record)
    for sample in range(samples):
        for ticker in tickers:
            for endpoint, path in [('compact', f'/api/company/{ticker}?as_of={asof}'),
                                   ('assembled', f'/api/company/{ticker}/packet?as_of={asof}')]:
                record, value = client.fetch(path)
                record['sample'] = sample + 1
                contract_record(record, value, endpoint, ticker, asof)
                if require_zion and endpoint == 'compact' and record['status'] == 'PASS':
                    if record['transport']['snapshot_origin'] != 'ZION_SERVICE_BINDING' or record['invocation_evidence'] != 'RESPONSE_ORIGIN_RECEIPT':
                        record.update(status='FAIL', reason='Current Zion invocation not established (fallback or potentially cached receipt).')
                append(record)
            if flow:
                load, value = client.fetch('/api/load/dcf', {'ticker': ticker, 'valuation_date': asof})
                load['sample'] = sample + 1
                contract_record(load, value, 'load', ticker, asof)
                append(load)
                total = load['seconds']
                passed = load['status'] == 'PASS'
                if passed:
                    doc = value['financials']
                    preview, actual = client.fetch('/api/preview/dcf', {'financials': doc, 'assumptions': ASSUMPTIONS})
                    preview.update(endpoint='preview', ticker=ticker, sample=sample + 1)
                    total += preview['seconds']
                    if actual is not None:
                        try:
                            differences = compare_result(reference_dcf(doc, ASSUMPTIONS), actual)
                            preview['arithmetic_differences'] = differences
                            if differences:
                                raise ValueError('Independent DCF arithmetic mismatch.')
                            preview['arithmetic'] = 'PASS'
                        except (ValueError, KeyError, TypeError, AttributeError, ZeroDivisionError) as exc:
                            preview.update(status='FAIL', reason=str(exc))
                    passed = preview['status'] == 'PASS'
                    append(preview)
                append({'endpoint': 'load_preview_flow', 'ticker': ticker, 'sample': sample + 1,
                        'seconds': round(total, 6), 'status': 'PASS' if passed else 'FAIL',
                        'cache_state': load.get('cache_state', 'UNKNOWN'),
                        'note': 'Sum of network requests only; not browser workspace latency.'})
    final, health = client.fetch('/health')
    final['endpoint'] = 'health_after'
    report['release_after'] = (health or {}).get('release')
    if health is not None and (health.get('status') != 'healthy' or not isinstance(health.get('release'), dict) or not health['release'].get('commit') or report['release_before'] != report['release_after']):
        final.update(status='FAIL', reason='Unhealthy or changed deployment during measurement.')
    append(final)
    report['summary'] = summarize(report['records'])
    report['transport_counts'] = dict(Counter(
        x.get('transport', {}).get('snapshot_origin', 'UNKNOWN')
        for x in report['records'] if x.get('endpoint') in {'compact', 'assembled', 'load'}))
    report['status'] = 'FAIL' if any(x['status'] != 'PASS' for x in report['records']) else 'PASS'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    return report


def markdown(report):
    lines = ['# Zion × DCF pipeline baseline', '', f"Audit: **{report['status']}**. Target acceptance: **NOT ESTABLISHED**.",
             f"Base: {report['base']}. As of: {report['as_of']}. Samples/ticker: {report['samples_per_ticker']}.",
             '', '## Latency (seconds, nearest-rank)', '',
             '| Endpoint / observed assembly cache | Attempts | Failures | Successful p50 | Successful p95 | Max |',
             '| --- | --- | --- | --- | --- | --- |']
    for key, group in report['summary'].items():
        d = group['successful_latency']
        lines.append(f"| {key} | {group['attempts']} | {group['failures']} | {d['p50_seconds']} | {d['p95_seconds']} | {d['max_seconds']} |")
    lines += ['', '## Reported snapshot origins', '', json.dumps(report['transport_counts'], sort_keys=True),
              '', '## Failures', '']
    lines += [f"- {x.get('ticker', '')} {x.get('endpoint')}: {x.get('reason', x.get('note', 'Failed'))}"
              for x in report['records'] if x['status'] != 'PASS'] or ['None.']
    lines += ['', '## Limits', ''] + ['- ' + x for x in report['limitations']]
    lines += ['- Groups with fewer than 20 successful samples have SMALL_SAMPLE descriptive p95s.',
              '- Proposed cached/uncached packet targets: 0.250/0.750 seconds; browser workspace: 2.0 seconds. No speedup is claimed.',
              '- Exact deployment identities and per-request cache, release, transport and network receipts are retained in the JSON report.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://dcf-valuation-engine.scswitzer.workers.dev')
    parser.add_argument('--tickers', default='AAPL,MSFT')
    parser.add_argument('--as-of', default=None)
    parser.add_argument('--samples', type=int, default=5)
    parser.add_argument('--delay', type=float, default=7.0)
    parser.add_argument('--timeout', type=float, default=45.0)
    parser.add_argument('--flow', action='store_true', help='Also exercise non-saving DCF load/preview and independent arithmetic')
    parser.add_argument('--require-zion', action='store_true', help='Fail unless compact responses establish a current Zion call (requires no-store receipts)')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    url = urlsplit(args.base)
    if (url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password or
            url.path not in {'', '/'} or url.query or url.fragment or
            (url.scheme == 'http' and url.hostname not in {'localhost', '127.0.0.1', '::1'})):
        parser.error('Use an HTTPS origin or loopback HTTP origin, without credentials, query or path.')
    if not 1 <= args.samples <= 100 or not math.isfinite(args.delay) or args.delay < 7 or not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
        parser.error('Use 1-100 samples, delay >= 7 seconds, timeout > 0 and <= 120 seconds.')
    try:
        tickers = list(dict.fromkeys(ticker_symbol(x.strip()) for x in args.tickers.split(',')))
        asof = valuation_date(args.as_of)
    except ValueError as exc:
        parser.error(str(exc))
    if not 1 <= len(tickers) <= 8:
        parser.error('Use 1-8 distinct tickers.')
    if args.output.suffix.lower() != '.json':
        parser.error('--output must be a .json file; the Markdown companion uses .md.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    client = Client(args.base, args.timeout, args.delay)
    try:
        report = run(client, tickers, asof, args.samples, args.flow, args.require_zion,
                     checkpoint=lambda x: write_json_atomic(args.output, x))
    finally:
        client.session.close()
    write_json_atomic(args.output, report)
    args.output.with_suffix('.md').write_text(markdown(report))
    print(markdown(report))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    sys.exit(main())
