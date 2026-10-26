"""Consumer behavior: reject a successful but unstamped or stale source answer."""
from copy import deepcopy

import pytest

from shared_query_contract import validate_shared_answer


def answer():
    return {'bundle_id': 'a' * 64, 'source_releases': {'SEC': 'release-1'},
            'data_as_of': '2026-01-31', 'answer': 'opaque result'}


def test_matching_answer_is_preserved_without_relabeling():
    value = answer()
    assert validate_shared_answer(value, 'a' * 64) is value


def test_metadata_null_date_is_valid():
    value = {**answer(), 'data_as_of': None}
    assert validate_shared_answer(value)['data_as_of'] is None


@pytest.mark.parametrize('field', ['bundle_id', 'source_releases', 'data_as_of'])
def test_missing_provenance_fails_closed(field):
    value = answer()
    del value[field]
    with pytest.raises(ValueError, match='^BUNDLE_UNAVAILABLE$'):
        validate_shared_answer(value)


@pytest.mark.parametrize('patch', [
    {'bundle_id': 'bad'}, {'source_releases': {}}, {'source_releases': []},
    {'source_releases': {'SEC': None}}, {'source_releases': {'SEC': {'private': 'payload'}}},
    {'data_as_of': '2026-02-30'}, {'data_as_of': '2026-1-1'}, {'data_as_of': 20260101},
])
def test_invalid_provenance_fails_closed(patch):
    with pytest.raises(ValueError, match='^BUNDLE_UNAVAILABLE$'):
        validate_shared_answer({**answer(), **patch})


def test_wrong_bundle_never_relabels_source_response():
    value = answer()
    before = deepcopy(value)
    with pytest.raises(ValueError, match='^RELEASE_MISMATCH$'):
        validate_shared_answer(value, 'b' * 64)
    assert value == before
