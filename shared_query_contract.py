"""Validate source stamps at consumer boundaries without minting bundle identities."""
from datetime import date
import re


def validate_shared_answer(value, expected_bundle=None):
    """Preserve a valid answer; reject missing provenance or a stale caller pin."""
    if not isinstance(value, dict):
        raise ValueError('BUNDLE_UNAVAILABLE')
    bundle = value.get('bundle_id')
    sources = value.get('source_releases')
    if (not isinstance(bundle, str) or not re.fullmatch(r'[a-f0-9]{64}', bundle)
            or not isinstance(sources, dict) or not sources
            or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v
                   for k, v in sources.items()) or 'data_as_of' not in value):
        raise ValueError('BUNDLE_UNAVAILABLE')
    observed = value['data_as_of']
    if observed is not None:
        try:
            if not isinstance(observed, str) or date.fromisoformat(observed).isoformat() != observed:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('BUNDLE_UNAVAILABLE') from None
    if expected_bundle is not None and bundle != expected_bundle:
        raise ValueError('RELEASE_MISMATCH')
    return value
