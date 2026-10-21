"""Ask the shared financial backend. No local acquisition or calculation."""
import argparse
import json
from urllib.parse import urlencode
from run_cloud_reconciliation import request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question', nargs='+')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = request('/query?' + urlencode({'query': ' '.join(args.question)}), 'GET')
    print(json.dumps(result, indent=2) if args.json else result['answer'])


if __name__ == '__main__':
    main()
