"""Read-only native integration probe. Configure ZION_HISTORY_BASE_URL/TOKEN.

Prints aggregate coverage only. Optional output contains PUBLIC_SEC_ONLY
financial observations and is created with owner-only permissions.
"""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dcf_loader import load_document, ProviderError  # noqa: E402


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ticker');parser.add_argument('cik');parser.add_argument('as_of')
    parser.add_argument('--expected-release-id');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        doc=load_document('zion_history',args.ticker,args.as_of,cik=args.cik,expected_release_id=args.expected_release_id)
        if args.output:
            fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:json.dump(doc,stream,allow_nan=False)
        print(json.dumps({'ticker':args.ticker,'release_id':doc['source']['release_id'],
            'periods':[r['period_end'] for r in doc['historical']],
            'missing_fields':doc['source']['missing_fields'],'status':'PARTIAL_INPUTS' if doc['source']['missing_fields'] else 'INPUTS_MAPPED'}))
    except (ProviderError,ValueError,OSError) as exc:
        print(json.dumps({'status':'FAILED','error_class':type(exc).__name__}),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':sys.exit(main())
