"""Metadata-only dispatch for existing materialization connections. No local data reads."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from run_cloud_reconciliation import OUT, request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'identity', 'prices', 'price-index', 'batch', 'finish'])
    parser.add_argument('--part', type=int)
    args = parser.parse_args()
    if args.action in ['identity', 'prices', 'batch']:
        plan = json.loads((OUT / 'connection-plan.json').read_text())
        count = plan[{'identity': 'identity_parts', 'prices': 'price_parts', 'batch': 'ledger_batches'}[args.action]]
        parts = [args.part] if args.part is not None else range(count)
        receipts, failures = [], []
        with ThreadPoolExecutor(max_workers=3) as pool:
            pending = {pool.submit(request, '/connect/' + args.action + '?n=' + str(n)): n for n in parts}
            for future in as_completed(pending):
                try:
                    result = future.result()
                except Exception as error:
                    result = {'part': pending[future], 'error': str(error)}
                    failures.append(result)
                receipts.append(result)
                (OUT / ('connection-' + args.action + '-receipts.json')).write_text(json.dumps(receipts))
                print(json.dumps(result), flush=True)
        if failures:
            raise SystemExit(str(len(failures)) + ' cloud tasks failed; successful checkpoints preserved')
    else:
        result = request('/connect/' + args.action)
        (OUT / ('connection-plan.json' if args.action == 'init' else 'connection-' + args.action + '.json')).write_text(json.dumps(result, indent=2))
        print(json.dumps({k: v for k, v in result.items() if k not in ['pins', 'source_pins']}), flush=True)


if __name__ == '__main__':
    main()
