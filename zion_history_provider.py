"""Native SEC history consumer; no fallback providers or missing-to-zero mapping."""
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import hmac
import json
import re

from dcf_loader import BRIDGE_FIELDS, HISTORY_FIELDS, ProviderError, blank_document

METRICS = {
    'revenue': 'revenue', 'operating_income': 'ebit', 'net_income': 'net_income',
    'capital_expenditures': 'capex', 'cash': 'cash', 'diluted_shares': 'diluted_shares',
}
EVIDENCE_SCHEMA = 'zion-native-evidence-mac-v1'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def leaf_hash_valid(sid, leaf):
    concept = leaf.get('concept', '')
    record = leaf.get('source_record', {})
    if (not isinstance(sid, str) or not re.fullmatch(r'[0-9a-f]{64}', sid)
            or leaf.get('source_observation_id') != sid
            or not isinstance(concept, str) or not concept.startswith('us-gaap:')
            or not isinstance(record, dict)
            or record.get('end') != leaf.get('period_end')
            or record.get('start') != leaf.get('period_start')
            or record.get('accn') != leaf.get('accession')
            or record.get('form') != leaf.get('form')
            or record.get('form') not in {'10-K', '10-K/A', '10-Q', '10-Q/A'}):
        return False
    tag = concept.removeprefix('us-gaap:')
    val = decimal(record.get('val'))
    candidates = [dict(record)]
    if val == val.to_integral_value():
        candidates.append(dict(record, val=int(val)))
    try:
        candidates.append(dict(record, val=float(record['val'])))
    except (ValueError, OverflowError):
        pass
    for item in candidates:
        digest = hashlib.sha256(
            encoded({'cik': leaf.get('cik'), 'concept': tag, 'unit': leaf.get('unit'), 'source_record': item})
        ).hexdigest()
        if digest == sid:
            return True
    return False


def evidence_digest(pages, ticker, asof, cik):
    pin = release_pin(pages[0]) if pages and isinstance(pages[0], dict) else ()
    return hashlib.sha256(
        encoded({
            'schema': EVIDENCE_SCHEMA,
            'ticker': ticker,
            'valuation_date': asof,
            'cik': cik,
            'release_pin': list(pin),
            'pages': pages,
        })
    ).hexdigest()


def sign_evidence(pages, ticker, asof, cik, secret):
    if not isinstance(secret, str) or not secret:
        fail('server evidence signing key required')
    digest = evidence_digest(pages, ticker, asof, cik)
    key = hmac.new(secret.encode(), EVIDENCE_SCHEMA.encode(), hashlib.sha256).digest()
    return {
        'schema_version': EVIDENCE_SCHEMA,
        'payload_sha256': digest,
        'hmac_sha256': hmac.new(key, digest.encode(), hashlib.sha256).hexdigest(),
    }


def verify_evidence(doc, secret):
    if not isinstance(doc, dict):
        fail('financial document must be a JSON object')
    if not isinstance(secret, str) or not secret:
        fail('native Zion verification is not configured on this server')
    source = doc.get('source', {})
    company = doc.get('company', {})
    pages = source.get('native_history')
    ticker = company.get('ticker')
    asof = doc.get('valuation_date')
    cik = source.get('cik')
    if (source.get('adapter_version') != 'zion-native-history-v1'
            or not isinstance(pages, list) or not pages
            or not isinstance(ticker, str) or not isinstance(asof, str)
            or not isinstance(cik, str) or not re.fullmatch(r'\d{10}', cik)):
        fail('verified native Zion input bundle required')
    attestation = source.get('evidence_attestation')
    if not isinstance(attestation, dict) or attestation.get('schema_version') != EVIDENCE_SCHEMA:
        fail('unattested caller-supplied evidence bundle rejected')
    expected = sign_evidence(pages, ticker, asof, cik, secret)
    if (not hmac.compare_digest(str(attestation.get('payload_sha256', '')), expected['payload_sha256'])
            or not hmac.compare_digest(str(attestation.get('hmac_sha256', '')), expected['hmac_sha256'])):
        fail('evidence attestation mismatch; caller-supplied bundle rejected')
    return history_document(pages, ticker, asof, cik)


def fail(message):
    raise ProviderError('Native Zion history: ' + message)


def instant(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            fail('availability must have a timezone')
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        fail('invalid availability timestamp')


def decimal(value):
    try:
        if not isinstance(value, str):
            fail('exact decimal strings required')
        result = Decimal(value)
        if not result.is_finite():
            fail('nonfinite decimal')
        return result
    except InvalidOperation:
        fail('invalid decimal')


def release_pin(page):
    p = page.get('provenance', {})
    pin = (p.get('release_id'), p.get('registry_sha256'), p.get('manifest_sha256'),
           page.get('member_sha256'), page.get('registry_version'), page.get('as_of'))
    if not all(isinstance(v, str) and v for v in pin):
        fail('missing release/registry/member/availability identity')
    if p.get('source_lineage', {}).get('rights') != 'PUBLIC_SEC_ONLY':
        fail('only the public SEC consumer is supported')
    return pin


def history_document(pages, ticker, asof, cik):
    if not pages:
        fail('empty history')
    pin = release_pin(pages[0])
    cutoff = instant(pin[-1])
    if cutoff.date() > date.fromisoformat(asof):
        fail('source cutoff exceeds valuation date')
    doc = blank_document(ticker, ticker, asof, 'zion')
    groups = {}
    for page in pages:
        if (page.get('schema_version') != 'sec-financial-engine-v2' or page.get('cik') != cik
                or page.get('frequency') != 'annual' or release_pin(page) != pin):
            fail('incompatible company, frequency or release')
        leaves = page.get('source_records', {})
        for row in page.get('observations', []):
            metric = row.get('metric')
            if metric not in METRICS:
                continue
            field = METRICS[metric]
            expected_unit = 'shares' if metric == 'diluted_shares' else 'USD'
            end = row.get('period_end')
            try:
                end_date = date.fromisoformat(end)
                start = row.get('period_start')
                if field != 'cash' and not 330 <= (end_date - date.fromisoformat(start)).days + 1 <= 380:
                    fail('nonannual context')
            except (TypeError, ValueError):
                fail('invalid period')
            expected_currency = None if metric == 'diluted_shares' else 'USD'
            if (row.get('unit') != expected_unit or row.get('currency') != expected_currency
                    or row.get('frequency') != 'annual' or row.get('member_sha256') != pin[3]
                    or end_date > cutoff.date() or instant(row.get('available_at')) > cutoff):
                fail('incompatible units, context, member or availability')
            value = decimal(row.get('value_decimal'))
            terms = row.get('source_terms', [])
            ids = row.get('source_observation_ids', [])
            if not ids or set(ids) != {t.get('source_observation_id') for t in terms}:
                fail('missing source terms')
            reproduced = Fraction(0)
            for term in terms:
                sid = term['source_observation_id']
                leaf = leaves.get(sid, {})
                if (leaf.get('cik') != cik or leaf.get('member_sha256') != pin[3]
                        or leaf.get('unit') != expected_unit or instant(leaf.get('available_at')) > cutoff
                        or not leaf_hash_valid(sid, leaf)):
                    fail('incompatible leaf source')
                original = decimal(leaf.get('source_record', {}).get('val'))
                if original != decimal(leaf.get('value_decimal')):
                    fail('leaf differs from original SEC token')
                coefficient = term.get('coefficient')
                if isinstance(coefficient, bool) or not isinstance(coefficient, int):
                    fail('invalid linear source coefficient')
                reproduced += Fraction(original) * coefficient
            if reproduced != Fraction(value):
                fail('source arithmetic does not reconcile')
            number = float(value)
            if not Decimal(str(number)).is_finite():
                fail('numeric conversion overflow')
            record = groups.setdefault(end, {})
            if field in record and record[field][0] != value:
                fail('conflicting period facts')
            record[field] = (value, deepcopy(row))
    ends = sorted(k for k, rows in groups.items() if 'revenue' in rows)[-3:]
    if len(ends) != 3 or any(not 300 <= (date.fromisoformat(b) - date.fromisoformat(a)).days <= 430 for a, b in zip(ends, ends[1:])):
        fail('three consecutive annual revenue periods are required')
    for end in ends:
        rows = groups[end]
        history = dict(period_end=end, **dict.fromkeys(HISTORY_FIELDS))
        provenance = {}
        for field in HISTORY_FIELDS:
            if field in rows:
                if field == 'capex' and rows[field][0] < 0:
                    fail('capex must be a nonnegative source outflow')
                history[field] = float(rows[field][0])
                provenance[field] = rows[field][1]
        history.update(available_at=max(r[1]['available_at'] for r in rows.values()), provenance=provenance)
        doc['historical'].append(history)
    latest = groups[ends[-1]]
    if 'cash' in latest:
        doc['bridge']['cash'] = float(latest['cash'][0])
    if 'diluted_shares' in latest:
        doc['market']['diluted_shares'] = float(latest['diluted_shares'][0])
        doc['market']['shares_basis'] = 'Reported annual weighted-average diluted shares; not actual shares outstanding'
    doc['bridge']['as_of'] = ends[-1]
    missing = {}
    for row in doc['historical']:
        for field in HISTORY_FIELDS:
            if row[field] is None:
                missing[f'historical.{row["period_end"]}.{field}'] = 'NO_VERIFIED_NATIVE_MAPPING'
    for section, fields in [('bridge', BRIDGE_FIELDS), ('market', ['price', 'diluted_shares'])]:
        for field in fields:
            if doc[section][field] is None:
                missing[f'{section}.{field}'] = 'NO_VERIFIED_NATIVE_MAPPING'
    doc['source'].update(name='Zion immutable public SEC history', cik=cik, release_id=pin[0],
                         adapter_version='zion-native-history-v1', native_history=deepcopy(pages),
                         missing_fields=missing, historical_cutoff=pin[-1],
                         identity_status='EXPLICIT_USER_CIK_NOT_TICKER_CERTIFIED',
                         warnings=['Partial native history; suitability and missing valuation fields require reviewed inputs.',
                                   'Source arithmetic reconciliation is not full accounting certification.'])
    return doc


def load_history(ticker, asof, http, *, cik, base, token, expected_release_id=None):
    if not isinstance(cik, str) or not re.fullmatch(r'\d{10}', cik):
        fail('explicit ten-digit CIK required')
    if not token:
        fail('private bearer credential required')
    params = dict(cik=cik, frequency='annual', metrics=','.join(METRICS),
                  date_from=f'{max(2015, date.fromisoformat(asof).year - 6)}-01-01',
                  date_to=asof, as_of=asof+'T00:00:00Z', limit=1000)
    if expected_release_id:
        params['expected_release_id'] = expected_release_id
        params['release_id'] = expected_release_id
    pages, seen, size, offset, total = [], set(), 0, 0, None
    for _ in range(20):
        page = http.get(base.rstrip('/')+'/private/v1/financial-history',
                        headers={'Authorization':'Bearer '+token, 'User-Agent':'Zion-DCF-Native/1'}, params=dict(params))
        pin = release_pin(page)
        if params.get('expected_release_id') and pin[0] != params['expected_release_id']:
            fail('release mismatch')
        params['expected_release_id'] = pin[0]
        params['release_id'] = pin[0]
        size += len(json.dumps(page).encode())
        if size > 8 * 1048576:
            fail('response budget exceeded')
        pagination = page.get('pagination', {})
        if pagination.get('offset') != offset:
            fail('pagination offset mismatch')
        count = sum(len(page.get(key, [])) for key in ['observations','coverage_gaps','accounting_checks'])
        if pagination.get('returned_items') != count:
            fail('pagination count mismatch')
        total = pagination.get('total_items') if total is None else total
        if pagination.get('total_items') != total:
            fail('pagination total changed')
        offset += count
        pages.append(page)
        cursor = pagination.get('next_cursor')
        if not cursor:
            if offset != total:
                fail('incomplete pagination')
            doc = history_document(pages, ticker, asof, cik)
            doc['source']['evidence_attestation'] = sign_evidence(pages, ticker, asof, cik, token)
            return doc
        if cursor in seen or count == 0:
            fail('pagination loop')
        seen.add(cursor)
        params['cursor'] = cursor
    fail('page budget exceeded')
