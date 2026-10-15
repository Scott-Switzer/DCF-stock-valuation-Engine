"""Paced timing for POST /api/load/dcf on a staging Worker.

Each ticker is requested twice in sequence. The script records wall time and the
server's own load_summary evidence (assembly_cache state, elapsed_seconds and
original_assembly_seconds). Requests are spaced to respect the 20 requests/60s
reference rate limit.
"""
import json
import sys
import time
import urllib.request

BASE = sys.argv[1].rstrip('/')
LABEL = sys.argv[2]
TICKERS = ['AAPL', 'MSFT', 'NVDA']
GAP_SECONDS = 3.5


def classify_cache(state):
    """Classify a request as HIT/MISS from genuine server evidence only.

    The server's own ``load_summary.assembly_cache.state`` is the evidence.
    Request order (attempt number) is never a substitute: a first attempt can
    HIT a pre-warmed cache and a later attempt can MISS after eviction.
    Anything other than an explicit HIT/MISS state is UNKNOWN.
    """
    if state == "HIT":
        return "HIT"
    if state == "MISS":
        return "MISS"
    return "UNKNOWN"


def load(ticker):
    body = json.dumps({'ticker': ticker}).encode()
    request = urllib.request.Request(
        BASE + '/api/load/dcf', data=body, method='POST',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                 'User-Agent': 'Mozilla/5.0'})
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read())
    wall = time.monotonic() - started
    summary = payload.get('load_summary', {})
    state = summary.get('assembly_cache', {}).get('state')
    return {
        'ticker': ticker,
        'wall_seconds': round(wall, 3),
        'state': state,
        'cache_class': classify_cache(state),
        'elapsed_seconds': summary.get('elapsed_seconds'),
        'original_assembly_seconds': summary.get('original_assembly_seconds'),
    }


def summarize(rows):
    """Latency summary grouped by server-evidenced cache class, never by attempt order."""
    groups = {}
    for row in rows:
        groups.setdefault(row.get('cache_class', 'UNKNOWN'), []).append(row.get('wall_seconds'))
    return {
        cls: {'n': len(v), 'p50': sorted(v)[len(v) // 2], 'max': max(v)}
        for cls, v in groups.items() if all(isinstance(x, (int, float)) for x in v)
    }


def main():
    rows = []
    for ticker in TICKERS:
        for attempt in (1, 2):
            row = load(ticker)
            row['attempt'] = attempt
            rows.append(row)
            print(json.dumps(row), flush=True)
            if attempt == 1 and row.get('cache_class') == 'HIT':
                print(json.dumps({'warning': 'first attempt HIT pre-warmed cache; '
                                             'do not read attempt order as cold/warm evidence',
                                  'ticker': ticker}), flush=True)
            time.sleep(GAP_SECONDS)
    print(json.dumps({'label': LABEL, 'base': BASE, 'rows': rows,
                      'by_cache_class': summarize(rows)}))


if __name__ == '__main__':
    main()
