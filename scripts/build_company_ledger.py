#!/usr/bin/env python3
"""Build a 25-company coverage ledger from dated snapshots or the deployed API.

Never publishes data or saves valuations. Offline and live evidence stay distinct.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from company_packets import assemble_packet  # noqa: E402
from financial_qa import QA_UNIVERSE  # noqa: E402


def summarize(packet):
    fields = packet.get('fields', [])
    return {key: packet.get(key) for key in ('ticker', 'valuation_date', 'status', 'reason', 'components', 'datasets', 'methods')} | {
        'field_count': len(fields), 'present_fields': sum(x['present'] for x in fields),
        'freshness_counts': {status: sum(x['freshness']['status'] == status for x in fields)
                             for status in ('WITHIN_POLICY', 'HISTORICAL', 'STALE', 'UNKNOWN', 'FUTURE', 'INVALID_DATE')},
        'independent_source_verification': packet.get('independent_source_verification'),
        'cache': packet.get('cache'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--snapshots', type=Path)
    group.add_argument('--base', help='Live API base URL')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--delay', type=float, default=3.2, help='Seconds between live requests; respect shared reference rate limit')
    args = parser.parse_args()
    if args.delay < 0:
        parser.error('--delay cannot be negative')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    packet_dir = args.output.parent / (args.output.stem + '-packets')
    packet_dir.mkdir(exist_ok=True)
    report = {'schema_version': 'company-coverage-ledger-v1',
              'captured_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'live' if args.base else 'offline_dated_snapshots',
              'source_accuracy': 'NOT_ESTABLISHED', 'companies': []}
    for index, ticker in enumerate(QA_UNIVERSE):
        started = time.monotonic()
        try:
            if args.base:
                if index: time.sleep(args.delay)
                started = time.monotonic()
                request = Request(args.base.rstrip('/') + f'/api/company/{ticker}/packet',
                                  headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                with urlopen(request, timeout=60) as response:
                    raw = response.read(2_000_001)
                if len(raw) > 2_000_000: raise ValueError('Oversized packet')
                packet = json.loads(raw)
            else:
                snapshot = json.loads((args.snapshots / f'{ticker}.json').read_text())
                if snapshot.get('ticker') != ticker: raise ValueError('Snapshot identity mismatch')
                packet = assemble_packet(snapshot.get('bundle'), ticker=ticker, error=snapshot.get('error'))
            if packet.get('ticker') != ticker: raise ValueError('Packet identity mismatch')
            (packet_dir / f'{ticker}.json').write_text(json.dumps(packet, allow_nan=False))
            row = summarize(packet)
        except (HTTPError, URLError, OSError, ValueError, KeyError, TypeError) as exc:
            row = {'ticker': ticker, 'status': 'FETCH_OR_CONTRACT_FAILED', 'reason': str(exc),
                   'independent_source_verification': 'NOT_ESTABLISHED'}
        row['seconds'] = round(time.monotonic() - started, 3)
        report['companies'].append(row)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False))
        print(f"{ticker}: {row['status']} ({row['seconds']}s)", flush=True)
    lines = ['# Company coverage ledger', '', f"Mode: {report['mode']}",
             'Connectivity, mapping, freshness and independent accuracy are separate. No observation is independently filing-verified by this assembler.', '',
             '| Ticker | Status | Present / mapped fields | Stale fields | Missing date | Seconds |',
             '| --- | --- | --- | --- | --- | --- |']
    for row in report['companies']:
        f = row.get('freshness_counts', {})
        lines.append(f"| {row['ticker']} | {row['status']} | {row.get('present_fields', 0)} / {row.get('field_count', 0)} | {f.get('STALE', 0)} | {f.get('UNKNOWN', 0)} | {row['seconds']} |")
    lines += ['', '## Unavailable companies', '']
    lines += [f"- {x['ticker']}: {x.get('reason', 'See packet issues.')}" for x in report['companies'] if x['status'] in {'BLOCKED', 'FAIL', 'FETCH_OR_CONTRACT_FAILED'}]
    args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    return int(any(x['status'] in {'FAIL', 'FETCH_OR_CONTRACT_FAILED'} for x in report['companies']))


if __name__ == '__main__':
    sys.exit(main())
