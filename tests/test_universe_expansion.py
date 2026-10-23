import json
import sys

import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from propose_universe_expansion import (
    build_candidates,
    classify_instrument,
    load_sec_tickers,
    load_universe,
)


def sec_row(cik, ticker, exchange="Nasdaq", name="Fixture Corp"):
    return {"cik": str(cik).zfill(10), "company": name, "ticker": ticker, "exchange": exchange}


def test_instrument_classification_uses_only_ticker_syntax():
    assert classify_instrument("AAPL") == ("COMMON_EQUITY", "NONE")
    assert classify_instrument("BRK.A") == ("COMMON_EQUITY", "A")
    assert classify_instrument("BRK-B") == ("COMMON_EQUITY", "B")
    assert classify_instrument("AAC-WT") == ("DERIVATIVE", "NONE")
    assert classify_instrument("USB-PA") == ("PREFERRED", "NONE")
    assert classify_instrument("AACIU") == ("SUSPECT_DERIVATIVE", "NONE")
    assert classify_instrument("ABCDE") == ("COMMON_EQUITY", "NONE")


def test_named_omission_is_tier_one_and_keeps_its_cik():
    rows = [sec_row(3401, "XOM"), sec_row(1045810, "NVDA")]
    candidates, summary = build_candidates({"NVDA"}, rows)
    assert [row["ticker"] for row in candidates] == ["XOM"]
    assert candidates[0]["tier"] == "TIER_1_NAMED"
    assert candidates[0]["cik"] == "0000003401"
    assert candidates[0]["adr_status"] == "UNKNOWN_NOT_IN_CONTRACTS"
    assert summary["named_omissions_found"] == ["XOM"]


def test_share_class_of_a_covered_issuer_is_review_not_a_new_issuer():
    rows = [sec_row(1067983, "BRK.B"), sec_row(1067983, "BRK.A")]
    candidates, summary = build_candidates({"BRK.B"}, rows)
    assert [row["ticker"] for row in candidates] == ["BRK.A"]
    assert candidates[0]["status"] == "ISSUER_ALREADY_COVERED_OTHER_LISTING"
    assert candidates[0]["tier"] == "TIER_3_REVIEW"
    assert candidates[0]["other_listings"] == "BRK.B"
    assert summary["new_issuers"] == 0


def test_derivatives_preferred_and_otc_are_excluded_and_counted():
    rows = [
        sec_row(1, "AAC-WT"),
        sec_row(2, "USB-PA"),
        sec_row(3, "ABCDW"),
        sec_row(4, "OTCX", exchange="OTC"),
        sec_row(5, "GOOD"),
    ]
    candidates, summary = build_candidates(set(), rows)
    assert [row["ticker"] for row in candidates] == ["GOOD"]
    assert summary["excluded"] == {
        "DERIVATIVE": 1,
        "OTC_LISTING": 1,
        "PREFERRED": 1,
        "SUSPECT_DERIVATIVE": 1,
    }


def test_tier_one_sorts_before_waves_and_tickers_are_unique():
    rows = [
        sec_row(10, "ZZZ"),
        sec_row(11, "XOM"),
        sec_row(12, "AAA"),
        sec_row(10, "ZZZ"),
    ]
    candidates, _ = build_candidates(set(), rows)
    assert [row["ticker"] for row in candidates] == ["XOM", "AAA", "ZZZ"]
    assert len({row["ticker"] for row in candidates}) == len(candidates)


def test_same_ticker_with_conflicting_ciks_fails_closed():
    rows = [sec_row(99, "DUP"), sec_row(98, "DUP", exchange="NYSE")]
    with pytest.raises(ValueError, match="conflicting issuer identities"):
        build_candidates(set(), rows)


def test_loaders_reject_inconsistent_inputs(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"catalog": [{"symbol": "AAPL"}], "symbol_count": 2}))
    try:
        load_universe(manifest)
    except ValueError as error:
        assert "symbol_count" in str(error)
    else:
        raise AssertionError("inconsistent catalog was accepted")

    sec = tmp_path / "sec.json"
    sec.write_text(json.dumps({"fields": ["cik", "ticker"], "data": []}))
    try:
        load_sec_tickers(sec)
    except ValueError as error:
        assert "shape" in str(error)
    else:
        raise AssertionError("unexpected SEC shape was accepted")


def test_extra_listing_of_a_named_issuer_is_review_not_a_new_issuer():
    rows = [
        sec_row(1652044, "GOOG"),
        sec_row(1652044, "GOOGL"),
        sec_row(1652044, "GOOGM"),
        sec_row(1652044, "GOOGN"),
    ]
    candidates, summary = build_candidates(set(), rows)
    labelled = {row["ticker"]: (row["tier"], row["status"]) for row in candidates}
    assert labelled["GOOG"] == ("TIER_1_NAMED", "NAMED_HIGH_IMPACT_OMISSION")
    assert labelled["GOOGL"] == ("TIER_1_NAMED", "NAMED_HIGH_IMPACT_OMISSION")
    assert labelled["GOOGM"] == ("TIER_3_REVIEW", "ISSUER_NAMED_OTHER_LISTING")
    assert labelled["GOOGN"] == ("TIER_3_REVIEW", "ISSUER_NAMED_OTHER_LISTING")
    assert summary["by_tier"] == {"TIER_1_NAMED": 2, "TIER_3_REVIEW": 2}
    assert summary["new_issuers"] == 1


def test_missing_exchange_is_not_claimed_as_exchange_listed():
    candidates, summary = build_candidates(set(), [sec_row(99, "UNVERIFIED", exchange="")])
    assert candidates == []
    assert summary['excluded']['EXCHANGE_UNVERIFIED'] == 1
