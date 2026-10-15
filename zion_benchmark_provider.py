"""Zion-backed retrieval of DDFI benchmark assumption releases.

Preferred canonical interface for benchmark assumptions when the deployment
configures Zion: the DCF engine asks Zion's private query API
(``operation: benchmark_context``) instead of reading release files from disk.
The standalone file loader in ``valuation_benchmarks.py`` remains available for
isolated testing and non-Zion deployments.

Contract guarantees enforced here (in addition to the server's):

* The response's ``ddfi_release_id`` must equal the explicitly pinned release —
  never accept a substituted vintage.
* Historical mode must report the requested cutoff and a published_at on or
  before it; no backdated look-ahead and no silent newest-release fallback.
* Every observation must carry the
  ``BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT`` classification. A missing or
  quarantined observation fails explicitly; nothing is substituted.
* The returned row keeps the full Zion release/coverage evidence so the DCF
  result can carry its benchmark lineage.
"""

from copy import deepcopy
from datetime import date
from decimal import Decimal
import re

CLASSIFICATION = 'BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT'
SCHEMA_VERSION = 'zion-private-query-v1'
MAX_RESPONSE_BYTES = 1048576

TARGET_MEASURES = {
    'wacc_override': 'wacc',
    'ebit_margins': 'operating_margin',
    'tax_rates': 'tax_rate',
    'net_income_margins': 'net_margin',
}


class BenchmarkProviderError(ValueError):
    """Typed provider failure; surfaced to API clients as an explicit error."""


def fail(message):
    raise BenchmarkProviderError('Zion benchmark: ' + message)


def _short(release_id):
    """Bounded display of a release identity for error text."""
    return release_id[:12] if isinstance(release_id, str) else str(release_id)


def _require(condition, message):
    if not condition:
        fail(message)


def fetch_benchmark_row(*, base, token, subject, measure, release_id, mode,
                        valuation_date, http, dataset_id=None):
    """Fetch one benchmark observation through Zion and map it to the
    valuation_benchmarks row shape used by apply_benchmarks()."""
    _require(isinstance(base, str) and base.strip(), 'private Zion base URL required')
    _require(isinstance(token, str) and token, 'private bearer credential required')
    _require(isinstance(subject, str) and 1 <= len(subject) <= 80, 'bounded subject required')
    _require(isinstance(measure, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', measure),
             'bounded measure name required')
    _require(isinstance(release_id, str) and re.fullmatch(r'[0-9a-f]{64}', release_id),
             'exact assumption release hash required')
    _require(mode in ('current', 'historical'), 'unknown benchmark selection mode')
    _require(isinstance(valuation_date, str), 'valuation date required')
    body = {
        'operation': 'benchmark_context',
        'release_id': release_id,
        'subject': subject,
        'measures': [measure],
    }
    if dataset_id is not None:
        body['dataset_id'] = dataset_id
    if mode == 'historical':
        body['as_of'] = valuation_date
    response = http.post(
        base.rstrip('/') + '/private/v1/query',
        headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'Zion-DCF-Native/1'},
        json=body,
    )
    status = getattr(response, 'status_code', 500)
    payload = response.json() if hasattr(response, 'json') else {}
    if status != 200:
        error = payload.get('error', {}) if isinstance(payload, dict) else {}
        code = error.get('code', 'HTTP_%d' % status)
        message = error.get('message', 'benchmark request failed')
        fail(f'{code}: {message}')
    content = getattr(response, 'content', None)
    _require(isinstance(payload, dict), 'benchmark response must be an object')
    _require(content is None or len(content) <= MAX_RESPONSE_BYTES, 'response budget exceeded')
    _require(payload.get('schema_version') == SCHEMA_VERSION,
             'benchmark response schema mismatch')
    _require(payload.get('operation') == 'benchmark_context',
             'benchmark response operation mismatch')
    release = payload.get('release')
    _require(isinstance(release, dict), 'benchmark response has no release block')
    served_release = release.get('ddfi_release_id')
    _require(served_release == release_id,
             f'release mismatch: requested {_short(release_id)}, Zion served {served_release}')
    published_at = release.get('published_at')
    _require(isinstance(published_at, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', published_at),
             'release published_at is missing')
    if mode == 'historical':
        coverage = payload.get('coverage') or {}
        _require(coverage.get('as_of') == valuation_date,
                 'historical cutoff was not honored by the server')
        _require(date.fromisoformat(published_at) <= date.fromisoformat(valuation_date),
                 'benchmark vintage would look ahead of the valuation date')
        selection_mode = 'HISTORICAL_PUBLISHED'
    else:
        selection_mode = 'CURRENT_EXPLICIT_SELECTION'
    data = payload.get('data')
    _require(isinstance(data, dict), 'benchmark response has no data block')
    observations = data.get('observations')
    _require(isinstance(observations, list) and observations, 'benchmark response has no observations')
    selected = [o for o in observations if isinstance(o, dict) and o.get('measure') == measure]
    _require(len(selected) == 1, 'benchmark response is ambiguous for the requested measure')
    observation = selected[0]
    _require(observation.get('classification') == CLASSIFICATION,
             'benchmark observation is not a classified reference estimate')
    _require(observation.get('subject') == subject, 'benchmark subject mismatch')
    _require(observation.get('value_decimal') is not None,
             f'benchmark observation {measure!r} for {subject!r} is missing or quarantined '
             f'({observation.get("missing_reason", "no value")}); explicit substitution is forbidden')
    try:
        value = Decimal(observation['value_decimal'])
    except Exception:
        fail('benchmark value is not a decimal')
    _require(value.is_finite(), 'nonfinite benchmark')
    row = {
        'subject': observation['subject'],
        'measure': observation['measure'],
        'unit': observation.get('unit'),
        'value_decimal': observation['value_decimal'],
        'classification': observation['classification'],
        'release_id': served_release,
        'dataset_id': release.get('dataset_id'),
        'region': release.get('region'),
        'source_url': release.get('source_url'),
        'published_at': published_at,
        'selection_mode': selection_mode,
        'serving_release_id': release.get('serving_release_id'),
        'provider': release.get('provider'),
        'source_sha256': release.get('source_sha256'),
        'normalized_sha256': release.get('normalized_sha256'),
        'ingested_bundle': release.get('ingested_bundle'),
        'retrieved_at': release.get('retrieved_at'),
        'stated_publication_date': release.get('stated_publication_date'),
        'rights': deepcopy(release.get('rights') or {}),
        'benchmark_evidence': {
            'via': 'zion_private_benchmark_context',
            'release': deepcopy(release),
            'coverage': deepcopy(payload.get('coverage') or {}),
            'request': {k: v for k, v in body.items()},
        },
    }
    for field in ('source_sheet', 'source_column_index', 'currency', 'derived',
                  'derivation', 'subject_type', 'subject_region'):
        if field in observation:
            row[field] = observation[field]
    return row
