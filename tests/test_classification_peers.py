"""Classification provenance, the financial-firm DCF block, and the unverified-peer guardrail."""

from copy import deepcopy

import pytest

from decision_support import peer_review_status
from dcf_loader import demo_document
from issuer_classification import (
    REGISTRY_VERSION,
    financial_block_reason,
    is_confirmed,
    resolve_classification,
)
from readiness import method_readiness, reliable_peers

MRX_SIC = "6200"


def mrx_document(minority_interest):
    doc = deepcopy(demo_document())
    doc["company"]["ticker"] = "MRX"
    doc["source"]["classification"] = resolve_classification("MRX")
    doc["company"]["is_financial"] = True
    doc["bridge"]["minority_interest"] = minority_interest
    return doc


def reviewed_peers(doc):
    doc["comparables"] = [
        {"ticker": "AAA", "multiples": {"pe": 12.0, "ev_ebitda": 9.0}, "review_status": "reviewed"},
        {"ticker": "BBB", "multiples": {"pe": 14.0, "ev_ebitda": 10.0}, "review_status": "reviewed"},
    ]
    return doc


def test_mrx_registry_entry_keeps_provenance_and_is_confirmed():
    record = resolve_classification("MRX")
    assert record["status"] == "confirmed"
    assert record["sic"] == MRX_SIC
    assert record["as_of"] == "2026-03-25"
    assert record["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/1997464/")
    assert record["cik"] == "0001997464"
    assert record["registry_version"] == REGISTRY_VERSION


def test_sec_record_takes_precedence_over_registry():
    record = resolve_classification("MRX", {"sic": "6200", "description": "Brokers"})
    assert record["source"] == "SEC submissions"
    assert record["source_url"] is None


def test_unknown_classification_is_never_confirmed():
    record = resolve_classification("ZZZZ")
    assert record["status"] == "unknown"
    assert record["sic"] is None
    assert not is_confirmed(record)
    assert financial_block_reason({"source": {"classification": record}}) is None


def test_unknown_record_marks_dcf_unconfirmed_but_absent_record_does_not():
    doc = demo_document()
    doc["source"]["classification"] = resolve_classification("ZZZZ")
    dcf = method_readiness(doc)["dcf"]
    assert dcf["state"] == "fallback"
    assert "classification_unconfirmed" in dcf["codes"]

    assert method_readiness(demo_document())["dcf"]["state"] == "sufficient"


def test_legacy_sec_record_without_status_still_counts_as_confirmed():
    assert is_confirmed({"sic": "6022", "description": "State commercial banks"})


@pytest.mark.parametrize("minority", [200000.0, -200000.0])
def test_mrx_dcf_is_blocked_regardless_of_minority_sign(minority):
    dcf = method_readiness(mrx_document(minority))["dcf"]
    assert dcf["state"] == "unavailable"
    assert "financial_firm_enterprise_model" in dcf["codes"]
    if minority < 0:
        assert "negative_minority_interest" in dcf["codes"]


@pytest.mark.parametrize("minority", [200000.0, -200000.0])
def test_mrx_dcf_evaluation_refuses_to_run(minority):
    from app import evaluate
    from dcf_code import DCFAssumptions

    doc = mrx_document(minority)
    assessment = DCFAssumptions(
        revenue_growth_rates=[0.05] * 5, terminal_growth_rate=0.02, wacc_override=0.065
    )
    with pytest.raises(ValueError, match="financial firm"):
        evaluate(doc, assessment)


def test_financial_block_reason_reads_sic_even_without_company_flag():
    doc = demo_document()
    doc["source"]["classification"] = {"sic": "6022", "description": "Banks"}
    assert "SEC SIC 6022" in financial_block_reason(doc)


@pytest.mark.parametrize("minority", [200000.0, -200000.0])
def test_equity_methods_stay_eligible_for_financial_firm_with_reviewed_peers(minority):
    doc = mrx_document(minority)
    relative = reviewed_peers(deepcopy(doc))
    states = method_readiness(doc, relative_doc=relative)
    assert states["relative"]["state"] != "unavailable"
    assert "unverified_peers_only" not in states["relative"]["codes"]
    if minority < 0:
        assert "negative_minority_ev_blocked" in states["relative"]["codes"]


def test_peer_review_status_marks_fit_and_size_outliers():
    assert peer_review_status({"fit_label": "Industry and product fit", "caveats": []}) == "reviewed"
    assert peer_review_status({"fit_label": "Business fit unverified", "caveats": []}) == "candidate"
    assert (
        peer_review_status(
            {
                "fit_label": "Industry and product fit",
                "caveats": ["Material size mismatch; market equity outside 0.25–4× target."],
            }
        )
        == "excluded"
    )


def test_candidate_only_peers_make_relative_unavailable_and_name_them():
    doc = mrx_document(200000.0)
    doc["comparables"] = [
        {"ticker": "TECH", "multiples": {"pe": 62.6}, "review_status": "candidate"},
    ]
    relative = method_readiness(doc)["relative"]
    assert relative["state"] == "unavailable"
    assert "unverified_peers_only" in relative["codes"]
    assert "TECH" in " ".join(relative["reasons"])


def test_reliable_peers_drop_candidates_and_excluded_but_keep_manual_rows():
    peers = [
        {"ticker": "A", "multiples": {"pe": 1.0}, "review_status": "reviewed"},
        {"ticker": "B", "multiples": {"pe": 1.0}, "review_status": "candidate"},
        {"ticker": "C", "multiples": {"pe": 1.0}, "review_status": "excluded"},
        {"ticker": "D", "multiples": {"pe": 1.0}},
    ]
    assert [p["ticker"] for p in reliable_peers(peers)] == ["A", "D"]


def test_standalone_relative_form_requires_candidate_peer_selection():
    from suite_models import suite_sample
    from suite_views import suite_form, suite_form_payload
    from werkzeug.datastructures import MultiDict

    doc = suite_sample("relative")
    for i, peer in enumerate(doc["comparables"]):
        peer["review_status"] = "reviewed" if i == 0 else "candidate"
    form = suite_form("relative", doc)
    selected, _ = suite_form_payload("relative", MultiDict(form))
    assert len(selected["comparables"]) == 1
    form["peer_include_1"] = "yes"
    selected, _ = suite_form_payload("relative", MultiDict(form))
    assert len(selected["comparables"]) == 2
    assert selected["comparables"][1]["review_status"] == "user_confirmed"
