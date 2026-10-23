"""Ask the shared financial backend. No local acquisition or calculation."""
import argparse
import json
from urllib.parse import urlencode
from run_cloud_reconciliation import request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question', nargs='*')
    parser.add_argument('--request', help='Structured request as a JSON object; exclusive with a question.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if bool(args.question) == (args.request is not None):
        parser.error('Provide a question or --request, not both.')
    if args.request is not None:
        try:
            value = json.loads(args.request)
            if not isinstance(value, dict) or len(args.request) > 4096:
                raise ValueError()
        except (ValueError, TypeError):
            parser.error('--request must be a JSON object of at most 4,096 characters.')
    params = {'request': args.request} if args.request is not None else {'query': ' '.join(args.question)}
    result = request('/query?' + urlencode(params), 'GET')
    print(json.dumps(result, indent=2) if args.json else result['answer'])


if __name__ == '__main__':
    main()
