"""Review candidates from original SEC XBRL; never a substitute for native attestations."""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import re
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

CONCEPTS = {'EntityCommonStockSharesOutstanding', 'CommonStockSharesOutstanding'}
XBRLI = 'http://www.xbrl.org/2003/instance'
IX = 'http://www.xbrl.org/2013/inlineXBRL'


def local(tag):
    return tag.rsplit('}', 1)[-1].split(':')[-1]


def extract_shares(raw, *, cik, accession, source_url, filed, as_of, max_age_days=400):
    """Extract instant counts and class axes with explicit availability and refusal reasons.

    `filed` must come from independently retrieved SEC submission metadata. This function
    does not authenticate that metadata: even valid observations require source review.
    Availability is date-only, end of day; no intraday eligibility is claimed.
    """
    if not re.fullmatch(r'\d{10}', cik) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession):
        raise ValueError('A ten-digit CIK and SEC accession are required')
    parsed = urlparse(source_url)
    prefix = f'/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/'
    if parsed.scheme != 'https' or parsed.hostname != 'www.sec.gov' or not parsed.path.startswith(prefix):
        raise ValueError('Source URL must identify the SEC issuer and accession')
    cutoff, available = date.fromisoformat(as_of), date.fromisoformat(filed)
    if type(max_age_days) is not int or max_age_days < 0:
        raise ValueError('max_age_days must be a nonnegative integer')
    result = dict(schema_version='sec-filing-share-candidates-v1', cik=cik,
                  status='UNAVAILABLE', permitted_for_valuation=False,
                  aggregate_outstanding_shares=None, facts=[], rejected_reasons=[],
                  source=dict(url=source_url, accession=accession, filed=filed,
                              sha256=hashlib.sha256(raw).hexdigest(),
                              availability_policy='DATE_ONLY_END_OF_DAY_UTC', as_of=as_of))
    if available > cutoff:
        result['status'] = 'NOT_YET_AVAILABLE'
        return result
    if len(raw) > 30_000_000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        result['status'] = 'UNSUPPORTED_DOCUMENT'
        return result
    try:
        namespaces = dict(value for _, value in ET.iterparse(io.BytesIO(raw), events=('start-ns',)))
        root = ET.fromstring(raw)
    except ET.ParseError:
        result['status'] = 'UNSUPPORTED_DOCUMENT'
        return result
    contexts = {e.get('id'): e for e in root.iter(f'{{{XBRLI}}}context')}
    units = {e.get('id'): e for e in root.iter(f'{{{XBRLI}}}unit')}
    reasons = set()
    for element in root.iter():
        concept = element.get('name', '') if element.tag == f'{{{IX}}}nonFraction' else element.tag
        name = local(concept)
        expanded = concept
        if element.tag == f'{{{IX}}}nonFraction':
            prefix, _, suffix = concept.partition(':')
            expanded = '{' + namespaces.get(prefix, '') + '}' + suffix
            if element.get('format') and local(element.get('format')) not in ('num-dot-decimal', 'numdotdecimal'):
                reasons.add('UNSUPPORTED_NUMERIC_TRANSFORM')
                continue
        if name not in CONCEPTS:
            continue
        # A custom taxonomy with a familiar local name is not a standard share concept.
        standard = (expanded.startswith('{http://xbrl.sec.gov/dei/') or
                    expanded.startswith('{http://fasb.org/us-gaap/'))
        if not standard:
            reasons.add('UNSUPPORTED_TAXONOMY')
            continue
        context = contexts.get(element.get('contextRef'))
        if context is None:
            reasons.add('MISSING_CONTEXT')
            continue
        identifier = context.find(f'{{{XBRLI}}}entity/{{{XBRLI}}}identifier')
        if (identifier is None or identifier.get('scheme') != 'http://www.sec.gov/CIK'
                or (identifier.text or '').strip().zfill(10) != cik):
            reasons.add('ISSUER_MISMATCH')
            continue
        instant = context.find(f'{{{XBRLI}}}period/{{{XBRLI}}}instant')
        try:
            end = date.fromisoformat(instant.text) if instant is not None else None
        except (ValueError, TypeError):
            end = None
        if end is None:
            reasons.add('NOT_AN_INSTANT')
            continue
        if end > cutoff or end > available:
            reasons.add('FUTURE_OBSERVATION')
            continue
        if (cutoff - end).days > max_age_days:
            reasons.add('STALE_OBSERVATION')
            continue
        unit = units.get(element.get('unitRef'))
        measures = [] if unit is None else [e.text for e in unit.iter(f'{{{XBRLI}}}measure')]
        if (unit is None or unit.find(f'{{{XBRLI}}}divide') is not None or len(measures) != 1
                or local(measures[0] or '') != 'shares'):
            reasons.add('UNSUPPORTED_UNIT')
            continue
        try:
            value = Decimal(''.join(element.itertext()).replace(',', '').strip())
            scale = int(element.get('scale', '0'))
            if abs(scale) > 15:
                raise ValueError('scale')
            value *= Decimal(10) ** scale
            if element.get('sign') == '-':
                value = -value
            if not value.is_finite() or value <= 0 or value != value.to_integral_value():
                raise ValueError('shares')
        except (InvalidOperation, ValueError):
            reasons.add('INVALID_SHARE_VALUE')
            continue
        dimensions = {e.get('dimension'): ''.join(e.itertext()).strip()
                      for e in context.iter() if local(e.tag) in ('explicitMember', 'typedMember')}
        result['facts'].append(dict(concept=name, value_decimal=format(value, 'f'),
                                    unit='shares', period_end=end.isoformat(),
                                    context_id=element.get('contextRef'), dimensions=dimensions))
    result['rejected_reasons'] = sorted(reasons)
    grouped = {}
    for fact in result['facts']:
        key = (fact['period_end'], tuple(sorted(fact['dimensions'].items())))
        grouped.setdefault(key, set()).add(Decimal(fact['value_decimal']))
    if any(len(values) > 1 for values in grouped.values()):
        result['status'] = 'CONFLICTING'
    elif result['facts']:
        result['status'] = 'CANDIDATE_REQUIRES_REVIEW'
    return result
