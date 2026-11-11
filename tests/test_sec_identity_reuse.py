"""Packet identity reuse must not change financial inputs or relax identity.

The SEC-first loader never fetches the SEC ticker directory: identity comes
from the reviewed registry when it matches the packet, and otherwise from
the packet itself (ticker as display name, packet CIK). These tests pin
that behavior and confirm the reuse changes no financial input.
"""
from copy import deepcopy
from datetime import date, timedelta

import pytest

import issuer_classification
from sec_first import load_sec_first
from test_sec_first import MockHTTP, TODAY, full_packet


@pytest.fixture
def served(monkeypatch):
    import served_market

    monkeypatch.setattr(
        served_market,
        "latest_price",
        lambda symbol, asof, **kwargs: {
            "ticker": symbol,
            "price": 50.0,
            "price_as_of": TODAY,
            "provenance": {
                "provider": "Zion serving layer price history (CRSP)",
                "release": "fixture-release",
                "permno": 1,
                "basis": "raw_observed_price",
            },
        },
    )
    monkeypatch.setattr(served_market, "served_beta", lambda symbol, asof, **kwargs: (1.0, 150))
    monkeypatch.setattr(
        served_market, "risk_free_rate", lambda asof: {"rate": 0.04, "as_of": TODAY}
    )
    return served_market


def registry_entry(**changes):
    entry = {'cik': '0000000001', 'entity_name': 'Test Inc', 'sic': '3571',
             'source_url': 'https://www.sec.gov/Archives/edgar/data/1/fixture-index.htm',
             'as_of': '2026-01-15', 'source': 'Reviewed fixture'}
    return {**entry, **changes}


def test_reviewed_identity_supplies_name_without_any_directory_lookup(monkeypatch, served):
    packet = full_packet()
    old = deepcopy(packet)
    control_http = MockHTTP()
    control = load_sec_first('TEST', TODAY, control_http, packet)
    monkeypatch.setitem(issuer_classification.REVIEWED, 'TEST', registry_entry())
    fast_http = MockHTTP()
    actual = load_sec_first('TEST', TODAY, fast_http, packet)
    # Neither path fetches the SEC directory; the loader makes no HTTP calls.
    assert not any('company_tickers' in x for x in control_http.calls)
    assert not any('company_tickers' in x for x in fast_http.calls)
    assert control_http.calls == [] and fast_http.calls == []
    assert control['company']['name'] == 'TEST'
    assert actual['company']['name'] == 'Test Inc'
    # Retrieval timestamps and the reused display name differ; every
    # financial and source field agrees.
    actual["source"].pop("retrieved_at")
    control["source"].pop("retrieved_at")
    actual_name = actual["company"].pop("name")
    control_name = control["company"].pop("name")
    assert actual == control
    assert actual_name != control_name
    assert packet == old


@pytest.mark.parametrize('changes', [
    {'cik': '0000000002'},
    {'as_of': (date.fromisoformat(TODAY) + timedelta(days=1)).isoformat()},
    {'as_of': 'not-a-date'},
    {'source_url': ''},
    {'entity_name': ''},
])
def test_unverified_or_incompatible_registry_never_triggers_a_lookup(monkeypatch, served, changes):
    monkeypatch.setitem(issuer_classification.REVIEWED, 'TEST', registry_entry(**changes))
    http = MockHTTP()
    doc = load_sec_first('TEST', TODAY, http, full_packet())
    # The incompatible entry is ignored and no directory lookup replaces it:
    # identity falls back to the packet (ticker name, packet CIK).
    assert doc['company']['name'] == 'TEST'
    assert not any('company_tickers' in x for x in http.calls)
    assert http.calls == []
