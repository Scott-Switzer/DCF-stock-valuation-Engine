"""Bounded metadata reuse must not change financial inputs or relax identity."""
from copy import deepcopy
from datetime import date, timedelta

import pytest

import issuer_classification
from sec_first import load_sec_first
from test_sec_first import MockHTTP, TODAY, full_packet


def registry_entry(**changes):
    entry = {'cik': '0000000001', 'entity_name': 'Test Inc', 'sic': '3571',
             'source_url': 'https://www.sec.gov/Archives/edgar/data/1/fixture-index.htm',
             'as_of': '2026-01-15', 'source': 'Reviewed fixture'}
    return {**entry, **changes}


def test_reviewed_identity_eliminates_one_directory_lookup_without_model_changes(monkeypatch):
    packet = full_packet()
    old = deepcopy(packet)
    control_http = MockHTTP()
    control = load_sec_first('TEST', TODAY, control_http, packet)
    monkeypatch.setitem(issuer_classification.REVIEWED, 'TEST', registry_entry())
    fast_http = MockHTTP()
    actual = load_sec_first('TEST', TODAY, fast_http, packet)
    assert sum('company_tickers' in x for x in control_http.calls) == 1
    assert sum('company_tickers' in x for x in fast_http.calls) == 0
    assert len(control_http.calls) - len(fast_http.calls) == 1
    # Retrieval timestamps differ between calls; all financial/source fields agree.
    actual["source"].pop("retrieved_at")
    control["source"].pop("retrieved_at")
    assert actual == control
    assert packet == old


@pytest.mark.parametrize('changes', [
    {'cik': '0000000002'},
    {'as_of': (date.fromisoformat(TODAY) + timedelta(days=1)).isoformat()},
    {'as_of': 'not-a-date'},
    {'source_url': ''},
    {'entity_name': ''},
])
def test_unverified_or_incompatible_registry_preserves_directory_lookup(monkeypatch, changes):
    monkeypatch.setitem(issuer_classification.REVIEWED, 'TEST', registry_entry(**changes))
    http = MockHTTP()
    doc = load_sec_first('TEST', TODAY, http, full_packet())
    assert doc['company']['name'] == 'Test Inc'
    assert sum('company_tickers' in x for x in http.calls) == 1
