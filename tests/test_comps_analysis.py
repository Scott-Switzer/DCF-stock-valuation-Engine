from dataclasses import asdict
from datetime import date, timedelta
import json

import formulas
import pytest

from app import app
from readiness import method_readiness
from dcf_loader import demo_document
from suite_models import RelativeAssumptions, RelativeModel, suite_sample
from suite_views import suite_form, suite_form_payload
from xlsx_export import relative_workbook


def calculate(doc=None, basis="cuig_forward"):
    return RelativeModel(doc or suite_sample("relative"), RelativeAssumptions(["pe"], basis)).calculate()


def test_distribution_retains_outlier_and_explains_mean_and_median():
    doc = suite_sample("relative")
    for peer, multiple in zip(doc["comparables"], [10, 11, 12, 1000]):
        peer.update(denominator_basis="latest_annual", financial_period_end="2025-12-31")
        peer["multiples"]["pe"] = multiple
    result = calculate(doc)
    row = next(r for r in result["multiples"] if r["key"] == "pe")
    assert row["mean"] == 258.25
    assert row["median"] == 11.5
    assert row["outlier_count"] == 1
    assert row["distribution"][-1]["outlier"] is True
    assert all(p["weight"] == 0.25 and p["included"] for p in row["distribution"])
    assert row["implied_price"] == pytest.approx(sum(p["implied_price"] for p in row["distribution"]) / 4)
    assert row["median_implied_price"] == pytest.approx(11.5 * doc["target"]["forward"]["net_income"] / doc["market"]["diluted_shares"])
    assert any("not a matched forward" in w for w in result["warnings"])


def test_candidate_and_invalid_multiple_have_explicit_exclusions():
    doc = suite_sample("relative")
    doc["comparables"][0]["review_status"] = "candidate"
    doc["comparables"][1]["multiples"]["pe"] = -5
    row = next(r for r in calculate(doc)["multiples"] if r["key"] == "pe")
    assert row["count"] == 2
    assert [p["weight"] for p in row["distribution"]] == [0, 0, 0.5, 0.5]
    assert all(p["exclusion_reason"] for p in row["distribution"][:2])
    assert row["outlier_count"] == 0


def test_raw_contributions_reconcile_before_equity_floor():
    doc = suite_sample("relative")
    doc["bridge"]["short_term_debt"] = 1000
    doc["comparables"][0]["multiples"]["ev_revenue"] = 0.1
    result = RelativeModel(doc, RelativeAssumptions(["ev_revenue"])).calculate()
    row = next(r for r in result["multiples"] if r["key"] == "ev_revenue")
    assert row["distribution"][0]["raw_implied_price"] < 0
    assert sum(p["raw_price_contribution"] for p in row["distribution"]) == pytest.approx(row["raw_implied_price"])


def test_api_does_not_value_an_unreviewed_candidate_only_peer_set():
    doc = suite_sample("relative")
    for peer in doc["comparables"]:
        peer["review_status"] = "candidate"
    response = app.test_client().post("/api/preview/relative", json={"financials": doc, "assumptions": {"included_methods": ["pe"]}})
    assert response.status_code == 400


@pytest.mark.parametrize("basis", ["latest_annual", "unspecified"])
def test_matched_forward_rejects_historical_and_unknown_peer_bases(basis):
    doc = suite_sample("relative")
    for p in doc["comparables"]:
        p["denominator_basis"] = basis
    with pytest.raises(ValueError, match="documented forward-year-one"):
        calculate(doc, "matched_forward")


def test_matched_forward_requires_future_period_and_preserves_numbers():
    doc = suite_sample("relative")
    expected = calculate(doc)["target_price_12m"]
    for p in doc["comparables"]:
        p.update(denominator_basis="forward_year_one", financial_period_end="2027-12-31")
    assert calculate(doc, "matched_forward")["target_price_12m"] == expected
    doc["comparables"][0]["financial_period_end"] = "2025-12-31"
    with pytest.raises(ValueError, match="after the valuation date"):
        calculate(doc, "matched_forward")


@pytest.mark.parametrize("basis", [[], {}, "TTM-assumed"])
def test_invalid_basis_is_validation_error(basis):
    response = app.test_client().post("/api/preview/relative", json={"financials": suite_sample("relative"), "assumptions": {"included_methods": ["pe"], "valuation_basis": basis}})
    assert response.status_code == 400


def test_locked_peer_basis_survives_form_submission_and_import():
    doc = suite_sample("relative")
    doc["valuation_date"] = date.today().isoformat()
    for peer in doc["comparables"]:
        peer.update(denominator_basis="forward_year_one", financial_period_end=(date.today() + timedelta(days=365)).isoformat())
    form = suite_form("relative", doc)
    form.update(valuation_basis="matched_forward", include_ev_revenue="", include_ev_ebitda="", include_pe="yes")
    for i in range(4):
        del form[f"peer_basis_{i}"]  # Disabled sourced select is omitted by FormData.
    got, assumptions = suite_form_payload("relative", form)
    assert all(p["denominator_basis"] == "forward_year_one" for p in got["comparables"])
    assert assumptions.valuation_basis == "matched_forward"
    response = app.test_client().post("/api/import/relative", json={"financials": doc, "assumptions": asdict(assumptions)})
    assert response.status_code == 200
    assert response.get_json()["form"]["valuation_basis"] == "matched_forward"


def test_explicitly_cleared_estimate_date_is_not_restored():
    doc = suite_sample("relative")
    for peer in doc["comparables"]:
        peer.update(denominator_basis="forward_year_one", financial_period_end="2027-12-31")
    form = suite_form("relative", doc)
    form.update(valuation_basis="matched_forward", include_ev_revenue="", include_ev_ebitda="", include_pe="yes")
    form["peer_period_0"] = ""
    restored, assumptions = suite_form_payload("relative", form)
    assert restored["comparables"][0]["financial_period_end"] == ""
    with pytest.raises(ValueError, match="Forward peer estimate period"):
        RelativeModel(restored, assumptions).calculate()


def test_financial_firm_has_no_ev_contributions_and_pb_readiness_is_supported():
    doc = suite_sample("relative")
    doc["source"]["classification"] = {"status": "confirmed", "sic": "6200"}
    result = calculate(doc)
    for row in result["multiples"]:
        if row["key"].startswith("ev_"):
            assert row["count"] == 0
            assert all(p["weight"] == 0 and p["exclusion_reason"] for p in row["distribution"])
    snapshot = demo_document()
    snapshot["source"]["classification"] = {"status": "confirmed", "sic": "6200"}
    snapshot["comparables"] = [{"ticker": "PEER", "multiples": {"pb": 2}}]
    assert method_readiness(snapshot)["relative"]["state"] != "unavailable"


def test_workbook_excludes_unreviewed_peers_and_matches_live_result(tmp_path):
    doc = suite_sample("relative")
    doc["comparables"][0]["review_status"] = "candidate"
    assumptions = RelativeAssumptions(["pe"])
    result = RelativeModel(doc, assumptions).calculate()
    path = tmp_path / "comps.xlsx"
    path.write_bytes(relative_workbook(doc, asdict(assumptions), result))
    model = formulas.ExcelModel().loads(str(path)).finish()
    key = f"'[{path.name}]MODEL'!B9"
    value = float(model.calculate(outputs=[key])[key].value[0][0])
    assert value == pytest.approx(result["target_price_12m"], rel=1e-9)
    assert json.dumps(result, allow_nan=False)
