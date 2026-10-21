"""Metadata-only controller. Financial reads, reconciliation and briefs run in Workers."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = 'https://zion-security-funnel-staging.scswitzer.workers.dev'
OUT = Path(os.environ.get('FUNNEL_RUN_DIR', str(Path(__file__).resolve().parents[1].parent /
           'artifacts/security-funnel-2026-10-20')))


def credential():
    """Use the established private API profile; never write or print its values."""
    if os.environ.get('ZION_PRIVATE_API_TOKEN'):
        return os.environ['ZION_PRIVATE_API_TOKEN']
    for line in (Path.home() / '.config/zion/private-api.env').read_text().splitlines():
        if line.startswith('#') or '=' not in line:
            continue
        key, value = line.removeprefix('export ').split('=', 1)
        if key.strip() == 'ZION_PRIVATE_API_TOKEN':
            return value.strip().strip('\"\'')
    raise RuntimeError('Private API credential is not configured')


def request(path, method='POST'):
    req = Request(BASE + path, data=b'' if method == 'POST' else None, method=method,
                  headers={'Authorization': 'Bearer ' + credential(),
                           'User-Agent': 'Zion-Security-Funnel/1.0'})
    try:
        with urlopen(req, timeout=300) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(error.read(4096).decode()) from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['initialize', 'batch', 'run', 'finalize', 'status'])
    parser.add_argument('--batch', type=int, default=0)
    args = parser.parse_args()
    if args.action == 'run':
        plan = json.loads((OUT / 'reconciliation-input.json').read_text())
        receipts = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            pending = {pool.submit(request, '/batch?n=' + str(n)): n for n in range(plan['batches'])}
            for future in as_completed(pending):
                result = future.result()
                receipts.append(result)
                (OUT / 'reconciliation-batch-receipts.json').write_text(json.dumps(receipts))
                print(json.dumps(result), flush=True)
        return
    path = '/batch?n=' + str(args.batch) if args.action == 'batch' else '/' + args.action
    result = request(path, 'GET' if args.action == 'status' else 'POST')
    name = 'reconciliation-input.json' if args.action == 'initialize' else 'reconciliation-' + args.action + '.json'
    (OUT / name).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
