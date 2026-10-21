"""Metadata-only controls for the existing private Cloudflare enrichment queue."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from run_cloud_reconciliation import OUT, request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'submit', 'status', 'ledger'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.action == 'status':
        plan = json.loads((OUT / 'source-enrichment-plan.json').read_text())
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda n: request('/connect/enrichment-status-batch?n=' + str(n)),
                          range((plan['issuers'] + 99) // 100)))
    if args.action == 'ledger':
        request('/connect/enrichment-ledger-init')
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda n: request('/connect/enrichment-ledger-batch?n=' + str(n)), range(132)))
        result = request('/connect/enrichment-ledger-finish')
    else:
        result = request('/connect/enrichment-' + args.action)
    name = 'plan' if args.action == 'init' else args.action
    (OUT / ('source-enrichment-' + name + '.json')).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
