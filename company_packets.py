"""Dated company packets and explicit coverage, without new provider acquisition."""
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
import time
from urllib.parse import quote

from dcf_loader import ProviderError, ticker_symbol
from financial_qa import audit_snapshot

VERSION = 'company-packet-v1'
TTL = 300
MAX_BYTES = 524288


def today():
    return datetime.now(timezone.utc).date().isoformat()


def valuation_date(value):
    value = value or today()
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value or value > today():
        raise ValueError('Use a valid valuation date no later than today.')
    return value


def _key(method, ticker, asof):
    try:
        from embedded_assets import BUILD
        revision = BUILD['commit']
    except (ImportError, KeyError):
        revision = 'local'
    return f'{VERSION}:{revision}:{method}:{ticker}:{asof}'


def _digest(bundle):
    raw = json.dumps(bundle, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(raw.encode()) > MAX_BYTES:
        raise ValueError('Company packet exceeds cache budget.')
    return hashlib.sha256(raw.encode()).hexdigest()


def load_cached_method(method, ticker, asof=None, equity_risk_premium=0.05,
                       credit_spread=0.015, *, store=None, loader=None, clock=time.time):
    """Cache only default automatic loads. Never cache user snapshots or valuations."""
    from auto_loading import load_method
    from flask import current_app, has_request_context
    loader = loader or load_method
    ticker, asof = ticker_symbol(ticker), valuation_date(asof)
    if method not in {'dcf', 'ddm', 'relative'}:
        raise ValueError('Choose DCF, DDM or relative valuation.')
    args = (method, ticker, asof, equity_risk_premium, credit_spread)
    if equity_risk_premium != 0.05 or credit_spread != 0.015:
        return loader(*args)
    if store is None:
        if not has_request_context() or not current_app.config.get('CLOUDFLARE'):
            return loader(*args)
        from provider_cache import EdgeStore
        store = EdgeStore()
    started = time.monotonic()
    key = _key(method, ticker, asof)
    try:
        cached = store.get(key)
        if (isinstance(cached, dict) and 0 <= clock() - cached['created_at'] < TTL
                and cached['sha256'] == _digest(cached['bundle'])
                and cached['bundle']['financials']['company']['ticker'] == ticker
                and cached['bundle']['financials']['valuation_date'] == asof):
            result = deepcopy(cached['bundle'])
            summary = result.setdefault('load_summary', {})
            summary['original_assembly_seconds'] = summary.get('elapsed_seconds')
            summary['elapsed_seconds'] = round(time.monotonic() - started, 3)
            summary['assembly_cache'] = {
                'state': 'HIT', 'age_seconds': round(clock() - cached['created_at'], 3),
                'ttl_seconds': TTL, 'built_at': cached['built_at'],
                'note': 'Original financial observation dates retained; not a live quote guarantee.',
            }
            return result
    except Exception:
        pass  # Corrupt/unavailable cache never becomes financial evidence.
    result = loader(*args)  # Failures are not cached.
    created = clock()
    built = datetime.fromtimestamp(created, timezone.utc).isoformat()
    try:
        store.set(key, {'bundle': deepcopy(result), 'created_at': created,
                        'built_at': built, 'sha256': _digest(result)}, TTL)
    except Exception:
        pass
    result.setdefault('load_summary', {})['assembly_cache'] = {
        'state': 'MISS', 'age_seconds': 0, 'ttl_seconds': TTL, 'built_at': built,
        'note': 'Original financial observation dates retained; not a live quote guarantee.',
    }
    return result


def age_status(value, asof, maximum):
    if not value:
        return {'status': 'UNKNOWN', 'age_days': None}
    try:
        age = (date.fromisoformat(asof) - date.fromisoformat(str(value)[:10])).days
    except ValueError:
        return {'status': 'INVALID_DATE', 'age_days': None}
    return {'status': 'FUTURE' if age < 0 else 'STALE' if age > maximum else 'WITHIN_POLICY', 'age_days': age}


def assemble_packet(bundle, *, ticker=None, asof=None, analysts=None, error=None):
    """Pure assembly: no network, no repair, no inferred observation availability."""
    asof = valuation_date(asof or (bundle or {}).get('financials', {}).get('valuation_date'))
    ticker = ticker_symbol(ticker or bundle['financials']['company']['ticker'])
    base = {'schema_version': VERSION, 'ticker': ticker, 'valuation_date': asof,
            'assembled_at': datetime.now(timezone.utc).isoformat(),
            'point_in_time': 'NOT_ESTABLISHED', 'independent_source_verification': 'NOT_ESTABLISHED'}
    unmapped = [{'dataset': name, 'discovered': True, 'readable': 'NOT_CHECKED_THIS_REQUEST',
                 'mapped': False, 'contract_validated': False, 'used_fields': 0,
                 'reason': 'Storage connection exists; no approved valuation mapping.'}
                for name in ('private_wrds', 'macro', 'news', 'sec_filing_corpus', 'research_lakehouse')]
    if bundle is None:
        return {**base, 'status': 'BLOCKED', 'reason': error or 'Company inputs unavailable.',
                'financials': None, 'fields': [], 'methods': {}, 'datasets': unmapped,
                'components': {'financials': 'UNAVAILABLE', 'analysts': 'NOT_REQUESTED',
                               'peer_candidates': 'NOT_ASSEMBLED', 'filing_evidence': 'NOT_ASSEMBLED'}}
    doc = deepcopy(bundle['financials'])
    if doc['company']['ticker'] != ticker or doc['valuation_date'] != asof:
        raise ValueError('Company packet identity or valuation date mismatch.')
    audit = audit_snapshot(doc)
    fields = []
    ppe = fallback = 0
    latest_period = max((r['period_end'] for r in doc.get('historical', [])), default=None)
    for receipt in audit['observations']:
        field = deepcopy(receipt)
        if field['field'] == 'market.price':
            field['unit'] = 'USD/share'
            field['provenance'] = doc.get('source', {}).get('market_observation')
        present = field['value'] is not None
        is_ppe = field['provider_status'] == 'PPE'
        ppe += int(present and is_ppe)
        fallback += int(present and not is_ppe)
        field['mapped'] = True
        field['present'] = present
        field['source_selection'] = 'PUBLISHED_SEC' if is_ppe else 'BASELINE_OR_DERIVED'
        field['freshness'] = age_status(field['period_end'], asof, 7 if field['field'] == 'market.price' else 550)
        if (field['field'].startswith('historical.') and field['period_end']
                and latest_period and field['period_end'] < latest_period
                and field['freshness']['status'] not in {'FUTURE', 'INVALID_DATE'}):
            field['freshness']['status'] = 'HISTORICAL'
        fields.append(field)
    # Candidates are suggestions only; do not fetch peers to construct a core packet.
    from auto_loading import starter_peers
    class NoNetwork:
        def get(self, *args, **kwargs):
            raise ProviderError('Optional upstream lookup omitted during packet assembly.')
    peer_label, peers = starter_peers(ticker, NoNetwork())
    analyst_status = 'NOT_CACHED'
    if analysts is not None:
        if (not isinstance(analysts, dict) or analysts.get('ticker', ticker) != ticker
                or analysts.get('source_url') != f'https://finance.yahoo.com/quote/{quote(ticker, safe="")}/analysis/'
                or analysts.get('currency') != 'USD'
                or age_status(analysts.get('retrieved_at'), asof, 1)['status'] != 'WITHIN_POLICY'
                or 'error' in analysts):
            analysts = None
        else:
            analyst_status = 'CACHED_REFERENCE_NOT_FORECAST'
    evidence = []
    for field in fields:
        p = field.get('provenance') or {}
        if isinstance(p, dict) and p.get('accession'):
            item = {'accession': p['accession'], 'available_at': field['available_at'],
                    'source': p.get('provider'), 'source_url': (p.get('sec_source') or {}).get('url')}
            if item not in evidence:
                evidence.append(item)
    return {**base, 'status': audit['status'], 'financials': doc, 'fields': fields,
            'methods': audit['methods'], 'issues': audit['issues'],
            'cache': deepcopy(bundle.get('load_summary', {}).get('assembly_cache')),
            'components': {'financials': 'ASSEMBLED', 'analysts': analyst_status,
                           'peer_candidates': 'FOUR_UNREVIEWED_CANDIDATES',
                           'filing_evidence': 'FACT_PROVENANCE' if evidence else 'NOT_AVAILABLE'},
            'analyst_reference': deepcopy(analysts),
            'peer_candidates': {'tickers': peers, 'basis': peer_label, 'reviewed': False},
            'filing_evidence': evidence,
            'datasets': [
                {'dataset': 'published_sec_packets', 'discovered': True, 'readable': bool(ppe),
                 'mapped': True, 'contract_validated': audit['status'] != 'FAIL', 'used_fields': ppe},
                {'dataset': 'baseline_market_and_statements', 'discovered': True, 'readable': True,
                 'mapped': True, 'contract_validated': audit['status'] != 'FAIL', 'used_fields': fallback},
                *unmapped],
            'selection_policy': 'Existing published SEC overlay policy; retain labeled baseline for unsupported or excluded fields. No additional source conflicts resolved by this wrapper.'}


def load_company_packet(ticker, asof=None):
    ticker, asof = ticker_symbol(ticker), valuation_date(asof)
    try:
        bundle = load_cached_method('dcf', ticker, asof)
    except ProviderError as exc:
        return assemble_packet(None, ticker=ticker, asof=asof, error=str(exc))
    analysts = None
    try:
        from dcf_loader import JsonHTTP
        analysts = JsonHTTP().store.get(f'yahoo-analyst-references-v3-{ticker}')
    except Exception:
        pass
    return assemble_packet(bundle, ticker=ticker, asof=asof, analysts=analysts)
