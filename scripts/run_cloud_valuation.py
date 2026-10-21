"""Control cloud packet work; download only metadata, never statements or archives."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from run_cloud_reconciliation import request, OUT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['submit', 'status', 'reconcile'])
    args = parser.parse_args()
    if args.action == 'submit':
        result = request('/connect/valuation-packet-submit')
    elif args.action == 'reconcile':
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda n: request('/connect/valuation-ledger-batch?n=' + str(n)), range(132)))
        result = request('/connect/valuation-ledger-finish')
    else:
        plan = json.loads((OUT / 'valuation-packet-plan.json').read_text())
        pages = (plan['eligible'] + 99) // 100
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda n: request('/connect/valuation-packet-status-batch?n=' + str(n)), range(pages)))
        result = request('/connect/valuation-packet-status')
    (OUT / ('valuation-packet-' + args.action + '.json')).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
