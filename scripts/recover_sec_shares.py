"""Recover reviewable share evidence from a filer's latest available original XBRL.

Public SEC only. No cloud writes or valuation overrides. One filing per issuer per run;
older submissions can be supplied in a later bounded recovery pass, never guessed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sec_share_evidence import extract_shares  # noqa: E402


def get(session, url):
    target = urlparse(url)
    if target.scheme != 'https' or target.hostname not in ('www.sec.gov', 'data.sec.gov'):
        raise ValueError('SEC source required')
    time.sleep(.15)
    with session.get(url, timeout=(5, 30), stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError('SEC source did not return a complete document')
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 30_000_000:
                raise ValueError('SEC document exceeds 30 MB budget')
            chunks.append(chunk)
        return b''.join(chunks)


def recover(cik, as_of, session):
    if not re.fullmatch(r'\d{10}', cik):
        raise ValueError('Ten-digit CIK required')
    submissions_url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    raw = get(session, submissions_url)
    doc = json.loads(raw)
    if str(doc.get('cik')).zfill(10) != cik:
        raise ValueError('Submission identity mismatch')
    recent = doc['filings']['recent']
    candidates = [i for i, form in enumerate(recent['form'])
                  if form in ('10-K', '10-Q', '10-K/A', '10-Q/A')
                  and recent['filingDate'][i] <= as_of]
    if not candidates:
        return dict(cik=cik, status='NO_AVAILABLE_FILING_IN_RECENT_SUBMISSIONS', facts=[],
                    permitted_for_valuation=False)
    selected = max(candidates, key=lambda i: (recent['filingDate'][i], recent['accessionNumber'][i]))
    accession = recent['accessionNumber'][selected]
    base = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/'
    index_raw = get(session, base + 'index.json')
    index = json.loads(index_raw)
    names = [item['name'] for item in index['directory']['item']
             if item['name'].endswith('_htm.xml') and '/' not in item['name']]
    if len(names) != 1:
        return dict(cik=cik, status='ORIGINAL_XBRL_INSTANCE_NOT_UNIQUE', facts=[],
                    permitted_for_valuation=False)
    url = base + names[0]
    result = extract_shares(get(session, url), cik=cik, accession=accession, source_url=url,
                            filed=recent['filingDate'][selected], as_of=as_of)
    result['source'].update(submissions_url=submissions_url,
                            submissions_sha256=hashlib.sha256(raw).hexdigest(),
                            filing_index_sha256=hashlib.sha256(index_raw).hexdigest(),
                            retrieved_utc=datetime.now(timezone.utc).isoformat())
    return result


def main():
    import requests
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ciks', nargs='+')
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--identity', required=True, help='SEC request identity including contact')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    from datetime import date
    date.fromisoformat(args.as_of)
    if len(args.ciks) > 50 or len(set(args.ciks)) != len(args.ciks):
        parser.error('Select at most 50 distinct issuers')
    session = requests.Session()
    session.headers['User-Agent'] = args.identity
    results = []
    for cik in args.ciks:
        try:
            result = recover(cik, args.as_of, session)
        except Exception as error:
            # No response bodies, URLs with credentials or exception messages in receipts.
            result = dict(cik=cik, status='SOURCE_UNAVAILABLE', error_class=type(error).__name__,
                          facts=[], permitted_for_valuation=False)
        results.append(result)
        print(json.dumps(dict(cik=cik, status=result['status'], candidates=len(result['facts']))), flush=True)
    receipt = dict(schema_version='sec-share-recovery-run-v1', as_of=args.as_of, issuers=results,
                   cloud_writes=0, valuation_overrides=0)
    fd = os.open(args.output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream, allow_nan=False, indent=2)


if __name__ == '__main__':
    main()
