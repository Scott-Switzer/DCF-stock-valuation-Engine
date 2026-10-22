"""Verify model inputs against the one serving snapshot; never relabel live inputs."""
import re
import time
from datetime import date


def read_snapshot(env):
    from js import Request, Object
    from pyodide.ffi import to_js
    from ppe_provider import _wait
    binding = getattr(env, 'FINANCIAL_DATA', None)
    token = getattr(env, 'FINANCIAL_DATA_TOKEN', '')
    if binding is None or not token:
        raise ValueError('BUNDLE_UNAVAILABLE')
    deadline = time.monotonic() + 15
    response = _wait(binding.fetch(Request.new('https://financial.internal/snapshot', to_js(
        {'headers': {'Authorization': 'Bearer ' + token}}, dict_converter=Object.fromEntries))), deadline)
    if response.status != 200:
        raise ValueError('BUNDLE_UNAVAILABLE')
    import json
    raw = str(_wait(response.text(), deadline))
    if len(raw.encode()) > 131072:
        raise ValueError('BUNDLE_UNAVAILABLE')
    value = json.loads(raw)
    if not re.fullmatch(r'[a-f0-9]{64}', value.get('bundle_id', '')) or not value.get('source_releases'):
        raise ValueError('BUNDLE_UNAVAILABLE')
    return value


def _digest(value):
    import hashlib
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return None
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        return None


def stamp_model_result(result, snapshot):
    if result.get('bundle_id', snapshot['bundle_id']) != snapshot['bundle_id']:
        raise ValueError('RELEASE_MISMATCH')
    financials = result.get('financials') or {}
    source = financials.get('source') or {}
    # Preserve source release IDs. A receipt for live inputs is an observation
    # identity, not a fabricated provider release or a new stored-data bundle.
    inputs = {'financials': financials, 'form': result.get('form'), 'assumptions': result.get('assumptions')}
    receipt = _digest({'schema_version': 'zion-model-inputs-v1', 'bundle_id': snapshot['bundle_id'], 'inputs': inputs})
    dates = [_date(r.get('period_end')) for r in financials.get('historical', [])]
    dates.append(_date(financials.get('market', {}).get('price_as_of')))
    dates = [d for d in dates if d]
    coverage = source.get('field_coverage') or source.get('coverage') or []
    outside = []
    for row in coverage:
        release = (row.get('provenance') or {}).get('release_id')
        if release and release in snapshot['source_releases'].values():
            continue
        outside.append({'field': row.get('field'), 'provider': row.get('provider') or source.get('name') or 'unreported',
                        'data_as_of': _date(row.get('period_end')), 'observation_id': _digest(row),
                        'source_release_id': release})
    # Field coverage describes statement overrides, not necessarily live market
    # or capital-cost inputs. Keep an explicit document-level receipt as well.
    outside.append({'field': 'financials', 'provider': source.get('name') or 'unreported',
                        'data_as_of': max(dates, default=None), 'observation_id': _digest(financials),
                        'source_release_id': None})
    for field in ('form', 'assumptions'):
        if result.get(field) is not None:
            outside.append({'field': field, 'provider': 'existing_model_editable_assumptions',
                            'data_as_of': None, 'observation_id': _digest(result[field]), 'source_release_id': None})
    warnings = list(result.get('warnings') or [])
    if outside:
        warnings.append('Some model inputs are outside the stored-data bundle. input_snapshot_id identifies the returned financials and editable starting assumptions; source dates differ and unknown dates remain null.')
    return {**result, 'bundle_id': snapshot['bundle_id'], 'data_as_of': max(dates, default=None),
            'source_releases': snapshot['source_releases'], 'input_snapshot_id': receipt,
            'input_provenance': {'schema_version': 'zion-model-inputs-v1', 'stored_bundle_id': snapshot['bundle_id'],
                                 'scope': 'returned_financials_and_starting_assumptions', 'outside_bundle': outside},
            'warnings': warnings}
