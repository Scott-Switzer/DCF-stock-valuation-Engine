"""Bounded consumer of Zion's published readiness index, inside the existing DCF app."""
from copy import deepcopy
from datetime import date
import re

from dcf_loader import ProviderError, load_document, provider_setting, ticker_symbol

# Existing published benchmark references used by the verified integration scenarios.
# These are explicit selectable references, never company observations or forecast defaults.
BENCHMARK_REFERENCES = {
    'wacc': {'release_id': '11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9', 'measure': 'wacc'},
    'tax_rate': {'release_id': '11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9', 'measure': 'tax_rate'},
    'sales_capital': {'release_id': 'bcd291a646f52393ae5e6b539cfd3936e08aba566f7e34fc39448d81ca7f816c', 'measure': 'sales_to_invested_capital'},
}

ALLOWED = {'method', 'sector', 'missing', 'share_absence', 'cik', 'limit', 'cursor',
           'expected_index_id', 'flag', 'status'}


def load_screen(query, *, http=None, token=None, base=None):
    if set(query) - ALLOWED:
        raise ValueError('Unsupported screening parameter')
    params = dict(query)
    try:
        limit = int(params.get('limit', '25'))
    except (ValueError, TypeError):
        raise ValueError('Screen limit must be an integer from 1 to 500') from None
    if not 1 <= limit <= 500:
        raise ValueError('Screen limit must be an integer from 1 to 500')
    for key in ('expected_index_id',):
        if key in params and not re.fullmatch(r'[0-9a-f]{64}', params[key]):
            raise ValueError('Invalid index pin')
    if 'cik' in params and not re.fullmatch(r'\d{10}', params['cik']):
        raise ValueError('Explicit ten-digit CIK required')
    params.update(limit=str(limit), recipient='human_research')
    token = token or provider_setting('ZION_HISTORY_TOKEN')
    if not token:
        raise ProviderError('Readiness screening is not configured')
    if http is None:
        from dcf_loader import zion_history_endpoint
        http, base = zion_history_endpoint()
    if not base:
        raise ProviderError('Readiness screening origin is not configured')
    try:
        response = http.get(base.rstrip('/') + '/private/v1/readiness/screen',
                            headers={'Authorization': 'Bearer ' + token}, params=params)
        if isinstance(response, dict):
            page = response
        else:
            if response.status_code != 200:
                raise ProviderError('Readiness source refused request: HTTP ' + str(response.status_code))
            page = response.json()
        import json
        if len(json.dumps(page, allow_nan=False).encode()) > 2_000_000:
            raise ProviderError('Readiness response exceeds budget')
    except ProviderError:
        raise
    except Exception:
        raise ProviderError('Readiness transport unavailable') from None
    if not isinstance(page, dict) or page.get('schema_version') != 'zion-readiness-screen-index-v1':
        raise ProviderError('Unsupported readiness contract')
    for key in ('index_id', 'release_id', 'engine_release_id', 'record_manifest_sha256'):
        # Older fixtures omit the manifest digest; production index responses carry it.
        if key == 'record_manifest_sha256' and key not in page:
            continue
        if not re.fullmatch(r'[0-9a-f]{64}', str(page.get(key, ''))):
            raise ProviderError('Invalid readiness source pin')
    if params.get('expected_index_id', page['index_id']) != page['index_id']:
        raise ProviderError('Readiness index changed')
    try:
        date.fromisoformat(page['archive_cutoff'])
    except (ValueError, KeyError, TypeError):
        raise ProviderError('Readiness cutoff unavailable') from None
    matches = page.get('matches')
    if not isinstance(matches, list) or len(matches) > limit:
        raise ProviderError('Invalid readiness page')
    seen = set()
    for item in matches:
        cik = item.get('cik') if isinstance(item, dict) else None
        if not isinstance(cik, str) or not re.fullmatch(r'\d{10}', cik) or cik in seen:
            raise ProviderError('Duplicate or invalid readiness issuer')
        if params.get('cik', cik) != cik:
            raise ProviderError('Readiness issuer mismatch')
        seen.add(cik)
        item['valuation_blockers'] = list(item.get('missing') or []) + [
            'EXPLICIT_TICKER_REQUIRED', 'DATED_ASSUMPTIONS_REQUIRED']
    return page


def issuer_identity(symbol, cik, asof, *, http=None):
    """Verify an issuer alias without promoting current metadata into historical security data."""
    from issuer_classification import REVIEWED, reviewed_identity
    reviewed = reviewed_identity(symbol, cik, asof)
    if reviewed:
        return dict(status='DATED_REVIEWED_ISSUER_ALIAS', cik=cik, ticker=symbol,
                    name=reviewed[0], historical_security_eligible=False,
                    qualification='ISSUER_IDENTITY_ONLY;NO_DATED_PRICE_OR_SHARE_CLASS_JOIN')
    if symbol in REVIEWED and REVIEWED[symbol]['cik'] != cik:
        return None
    from dcf_loader import JsonHTTP
    import hashlib
    import json
    from datetime import datetime, timezone
    transport = http or JsonHTTP()
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    doc = transport.get(url, headers={'User-Agent': provider_setting('EDGAR_IDENTITY') or
                         'Zion Financial Research scswitzer@chapman.edu'},
                         ttl=3600, cache_key='screen-issuer-' + cik)
    if (not isinstance(doc, dict) or str(doc.get('cik')).zfill(10) != cik
            or symbol not in [str(value).replace('.', '-') for value in doc.get('tickers', [])]):
        return None
    return dict(status='CURRENT_SEC_ALIAS_ONLY', cik=cik, ticker=symbol, name=doc.get('name'),
                historical_security_eligible=False, source_url=url,
                checked_at_utc=datetime.now(timezone.utc).isoformat(),
                canonical_json_sha256=hashlib.sha256(json.dumps(doc, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest(),
                qualification='CURRENT_METADATA_NOT_HISTORICAL;ISSUER_FACTS_ONLY;NO_SECURITY_PRICE_JOIN')


def authorized():
    from accounts import current_user
    return current_user() is not None


def register_screen(app):
    from flask import jsonify, render_template, request

    @app.get('/screen')
    def company_screen():
        return render_template('screen.html', signed_in=authorized())

    @app.get('/api/research-screen')
    def screen_api():
        if not authorized():
            return jsonify(error='Sign in to use private research screening'), 401
        try:
            if any(len(request.args.getlist(key)) != 1 for key in request.args):
                raise ValueError('Repeated parameters are not supported')
            return jsonify(load_screen(request.args.to_dict()))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except ProviderError as exc:
            return jsonify(error=str(exc)), 503

    @app.post('/api/research-screen/prepare')
    def prepare_screen():
        if not authorized():
            return jsonify(error='Sign in to use private research screening'), 401
        try:
            raw = request.get_json(silent=True)
            if not isinstance(raw, dict) or not raw.get('expected_index_id'):
                raise ValueError('Select a pinned screening row first')
            symbol = ticker_symbol(raw.get('ticker'))
            page = load_screen({'cik': raw.get('cik'), 'expected_index_id': raw['expected_index_id']})
            if len(page['matches']) != 1 or page['matches'][0]['cik'] != raw.get('cik'):
                return jsonify(error='Screen issuer mismatch'), 409
            row = page['matches'][0]
            identity = issuer_identity(symbol, row['cik'], page['archive_cutoff'])
            if identity is None:
                return jsonify(error='SEC_ISSUER_ALIAS_MISMATCH',
                               cik=row['cik'], ticker=symbol), 409
            if 'operating_dcf' not in row.get('methods', []):
                return jsonify(error='OPERATING_DCF_INPUTS_UNAVAILABLE',
                               blockers=row.get('missing', [])), 422
            doc = load_document('zion_history', symbol, page['archive_cutoff'], cik=row['cik'],
                                expected_release_id=page['engine_release_id'])
            blockers = list(row.get('missing') or [])
            history = doc.get('historical') or []
            latest = history[-1] if history else {}
            if latest.get('revenue') is None:
                blockers.append('MISSING_LATEST_REVENUE')
            if latest.get('ebit') is None:
                blockers.append('MISSING_LATEST_OPERATING_INCOME')
            blockers.append('DATED_ASSUMPTIONS_REQUIRED')
            return jsonify(financials=doc, screening=deepcopy(page), issuer_identity=identity,
                           valuation_blockers=blockers,
                           source_missing_fields=(doc.get('source') or {}).get('missing_fields', {}),
                           calculate_endpoint='/api/calculate/enterprise',
                           benchmark_references=deepcopy(BENCHMARK_REFERENCES),
                           equity_bridge_endpoint='/api/equity-claims/bridge',
                           equity_bridge_status='REQUIRES_MATCHING_CLAIMS_ENGINE_RELEASE',
                           request_template=dict(ticker=symbol, cik=row['cik'],
                               source_asof=page['archive_cutoff'], financials=doc,
                               expected_release_id=page['engine_release_id'],
                               valuation_date=None, benchmark_selections=None,
                               revenue_growth_rates=None, terminal_growth=None,
                               terminal_roic=None, suitable=None))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except ProviderError as exc:
            return jsonify(error=str(exc)), 503
