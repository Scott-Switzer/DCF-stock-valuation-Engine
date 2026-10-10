"""A reported negative noncontrolling interest is method-specific.

FCFF DCF and EV-based multiples depend on the equity bridge, so they stay strict.
P/E and P/B do not use the bridge, so they accept the reported value unchanged.
"""

from copy import deepcopy

import pytest

from app import evaluate
from dcf_code import DCFAssumptions
from dcf_loader import demo_document, parse_document
from readiness import method_readiness
from suite_models import RelativeAssumptions, suite_sample
from suite_views import suite_evaluate

NEGATIVE_NCI = -200000.0


def sample_relative():
    return suite_sample("relative")


def with_negative_minority(doc):
    doc = deepcopy(doc)
    doc["bridge"]["minority_interest"] = NEGATIVE_NCI
    return doc


def dcf_assumptions():
    return DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=0.08,
        terminal_mode="template",
    )


def test_default_parse_rejects_negative_minority_for_dcf():
    with pytest.raises(ValueError, match="minority_interest must be at least 0"):
        parse_document(with_negative_minority(demo_document()))


def test_equity_only_parse_keeps_negative_minority_unchanged():
    doc = with_negative_minority(demo_document())
    fd = parse_document(doc, minority_may_be_negative=True)
    assert fd.minority_interest == NEGATIVE_NCI
    assert doc["bridge"]["minority_interest"] == NEGATIVE_NCI


def test_dcf_evaluation_stays_strict_with_negative_minority():
    with pytest.raises(ValueError, match="minority_interest must be at least 0"):
        evaluate(with_negative_minority(demo_document()), dcf_assumptions())


def test_pe_and_pb_accept_negative_minority_unchanged():
    doc = with_negative_minority(sample_relative())
    result = suite_evaluate("relative", doc, RelativeAssumptions(["pe", "pb"]))
    assert result["target_price_12m"] is not None
    assert doc["bridge"]["minority_interest"] == NEGATIVE_NCI


def test_ev_based_multiples_reject_negative_minority():
    doc = with_negative_minority(sample_relative())
    with pytest.raises(ValueError, match="minority_interest must be at least 0"):
        suite_evaluate("relative", doc, RelativeAssumptions(["ev_ebitda"]))


def test_readiness_blocks_dcf_but_keeps_equity_multiples_available():
    readiness = method_readiness(with_negative_minority(demo_document()))
    assert readiness["dcf"]["state"] == "unavailable"
    assert "negative_minority_interest" in readiness["dcf"]["codes"]
    assert "negative_minority_ev_blocked" in readiness["relative"]["codes"]
    assert "P/E and P/B remain available" in " ".join(readiness["relative"]["reasons"])


def test_relative_assembly_accepts_signed_minority_snapshot(monkeypatch):
    from app import app
    from dcf_loader import demo_document
    import auto_loading

    doc = demo_document()
    doc["bridge"]["minority_interest"] = -0.2
    monkeypatch.setattr(auto_loading, "load_method", lambda *args, **kwargs: {"assembled": True})
    response = app.test_client().post("/api/assemble/relative", json={"financials": doc})
    assert response.status_code == 200
    assert response.get_json()["assembled"] is True
