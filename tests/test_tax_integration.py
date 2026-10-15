"""Live tax-policy integration: packet -> doc -> policy -> assumptions -> brief.

Covers the route: SEC-first loads record reported-vs-forecast tax position
and accept explicit policies; PPE merges honor a selected policy; Yahoo
retains the signed filed ratio beside its normalized fallback; compare
resolves baseline tax through the policy with recalculated vs fixed WACC
modes; the brief surfaces the basis; the workspace recomputes a stale WACC.
"""

import sys
from copy import deepcopy
from unittest.mock import patch

import pytest

sys.path.insert(0, "tests")

from test_sec_first import MockHTTP, full_packet  # noqa: E402
from test_yahoo_provider import MockHTTP as YahooHTTP, TODAY as YAHOO_TODAY  # noqa: E402


def test_sec_first_load_records_tax_policy():
    from sec_first import load_sec_first

    packet = full_packet()
    for row, tax in zip(packet["historical"], [0.22, -0.153, 0.358]):
        row["fields"]["tax_rate"]["value"] = tax
    doc = load_sec_first("TEST", packet["cutoff_date"], MockHTTP(), packet)
    policy = doc["source"]["tax_policy"]
    assert [entry["rate"] for entry in policy["reported"]] == [0.22, -0.153, 0.358]
    # Default resolves from the valid latest year despite the middle negative.
    assert policy["selected"]["basis"] == "latest_reported"
    assert policy["selected"]["rates"] == [0.358] * 5
    assert policy["explicit"] is False
    # Signed history is untouched.
    assert [row["tax_rate"] for row in doc["historical"]] == [0.22, -0.153, 0.358]


def test_sec_first_load_accepts_explicit_scenario():
    from dcf_loader import ProviderError
    from sec_first import load_sec_first

    packet = full_packet()
    for row, tax in zip(packet["historical"], [0.22, -0.153, 2.0]):
        row["fields"]["tax_rate"]["value"] = tax
    scenario = {
        "rates": [0.231] * 5,
        "evidence": {"filing": "f", "period_end": "2024-12-31"},
    }
    # Latest default is unusable, so the bare load refuses with the fix named.
    with pytest.raises(ProviderError, match="tax_forecast_assumption_required"):
        load_sec_first("TEST", packet["cutoff_date"], MockHTTP(), packet)
    doc = load_sec_first(
        "TEST", packet["cutoff_date"], MockHTTP(), packet, tax_scenario=scenario
    )
    assert doc["source"]["tax_policy"]["selected"]["basis"] == "normalized_scenario"
    assert doc["source"]["tax_policy"]["explicit"] is True
    assert doc["historical"][-1]["tax_rate"] == 2.0
    with pytest.raises(ProviderError):
        load_sec_first(
            "TEST", packet["cutoff_date"], MockHTTP(), packet,
            tax_override=[0.25] * 4,
        )


def test_prefer_ppe_honors_explicit_policy():
    from dcf_loader import demo_document
    from ppe_provider import prefer_ppe
    from tax_policy import TaxPolicyError, resolve_forecast_tax

    import ppe_provider

    baseline = demo_document()
    candidate = deepcopy(baseline)
    candidate["historical"][1]["tax_rate"] = -0.153
    scenario = {
        "rates": [0.231] * 5,
        "evidence": {"filing": "f", "period_end": "2024-12-31"},
    }
    with (
        patch.object(ppe_provider, "load_packet", return_value={"published": True}),
        patch("ppe_packets.apply_packet", return_value=candidate),
    ):
        # Latest default is valid: the middle negative never blocks.
        merged = prefer_ppe(deepcopy(baseline), "DEMO", baseline["valuation_date"])
        assert merged["source"]["tax_policy"]["selected"]["basis"] == "latest_reported"
        # An explicit scenario is recorded without touching history.
        merged = prefer_ppe(
            deepcopy(baseline), "DEMO", baseline["valuation_date"],
            tax_scenario=scenario,
        )
        assert merged["source"]["tax_policy"]["selected"]["basis"] == "normalized_scenario"
        assert merged["historical"][1]["tax_rate"] == -0.153
        # An unresolvable candidate keeps the explicit baseline.
        bad = deepcopy(baseline)
        bad["historical"][-1]["tax_rate"] = 2.0
        with patch("ppe_packets.apply_packet", return_value=bad):
            kept = prefer_ppe(deepcopy(baseline), "DEMO", baseline["valuation_date"])
        assert kept["historical"][-1]["tax_rate"] == baseline["historical"][-1]["tax_rate"]
    with pytest.raises(TaxPolicyError):
        resolve_forecast_tax([0.22, 2.0])


def test_yahoo_retains_filed_ratio_beside_fallback():
    from yahoo_provider import load_yahoo

    http = YahooHTTP()
    provision = next(
        b for b in http.financials["timeseries"]["result"] if "annualTaxProvision" in b
    )
    provision["annualTaxProvision"][-1]["reportedValue"]["raw"] = -40
    http.financials["timeseries"]["result"].append(
        {
            "annualTaxRateForCalcs": [
                {
                    "asOfDate": http.ends[-1],
                    "periodType": "12M",
                    "currencyCode": "USD",
                    "reportedValue": {"raw": 0.18},
                }
            ]
        }
    )
    doc = load_yahoo("TEST", YAHOO_TODAY, http)
    last = doc["historical"][-1]
    assert last["tax_rate"] == 0.18
    # The filed ratio is the signed provision/pretax observation, preserved.
    assert last["reported_tax_rate"] == pytest.approx(-0.25)
    assert last["reported_tax_rate"] < 0
    assert last["provenance"]["tax_rate"]["basis"] == "Yahoo normalized TaxRateForCalcs fallback"
    policy = doc["source"]["tax_policy"]
    assert policy["reported"][-1]["filed_ratio"] == last["reported_tax_rate"]
    assert policy["selected"]["basis"] == "latest_reported"


def _frozen_doc(tax_history=(0.22, 0.24, 0.25)):
    rows = []
    for i, (end, tax) in enumerate(zip(("2023-12-31", "2024-12-31", "2025-12-31"), tax_history)):
        rows.append(
            {
                "period_end": end,
                "revenue": 100.0 + i * 10,
                "ebit": 20.0,
                "d_and_a": 5.0,
                "capex": 6.0,
                "nwc": 4.0,
                "net_income": 10.0,
                "book_value": 50.0,
                "tax_rate": tax,
            }
        )
    return {
        "schema_version": "dcf-financials-v1",
        "company": {"ticker": "TEST"},
        "market": {},
        "bridge": {},
        "historical": rows,
        "source": {
            "capital_costs": {
                "market_equity_value": 1000.0,
                "debt": 500.0,
                "cost_of_equity": 0.09,
                "cost_of_debt": 0.05,
                "tax_rate": 0.25,
                "wacc": (1000 * 0.09 + 500 * 0.05 * 0.75) / 1500,
            }
        },
    }


def test_baseline_honors_doc_selected_policy():
    from compare import baseline_dcf_assumptions, resolve_tax_rates

    doc = _frozen_doc()
    rates, basis = resolve_tax_rates(doc)
    assert rates == [0.25] * 5 and basis == "latest_reported"
    doc["source"]["tax_policy"] = {
        "selected": {"basis": "normalized_scenario", "rates": [0.231] * 5, "evidence": {}}
    }
    rates, basis = resolve_tax_rates(doc)
    assert rates == [0.231] * 5 and basis == "normalized_scenario"
    assert baseline_dcf_assumptions(doc, 0.065).tax_rates == [0.231] * 5
    # An unresolvable default names the requirement instead of inventing a rate.
    bad = _frozen_doc((0.22, 0.24, 2.0))
    with pytest.raises(ValueError, match="explicit"):
        resolve_tax_rates(bad)


def test_wacc_modes_frozen_regression():
    from compare import coerce_dcf_assumptions, recalculated_wacc, wacc_basis_note

    doc = _frozen_doc()
    costs = doc["source"]["capital_costs"]
    loaded = costs["wacc"]
    # Recalculation reproduces the loaded rate exactly with an unchanged shield.
    assert recalculated_wacc(costs, 0.25) == pytest.approx(loaded)
    base, custom = coerce_dcf_assumptions(doc, None, loaded, costs=costs)
    assert custom is False
    assert base.wacc_override == pytest.approx(loaded)
    assert "Recalculated" in wacc_basis_note(doc, base, costs, "recalculated")
    fixed, _ = coerce_dcf_assumptions(doc, None, loaded, costs=costs, wacc_mode="fixed")
    assert fixed.wacc_override == pytest.approx(loaded)
    assert "Fixed-WACC" in wacc_basis_note(doc, fixed, costs, "fixed")
    # An edited forecast tax recomputes the shield; fixed mode holds the load.
    raw = {"tax_rates": [0.10] * 5}
    recalc, custom = coerce_dcf_assumptions(doc, raw, loaded, costs=costs)
    assert custom is True
    assert recalc.wacc_override == pytest.approx(recalculated_wacc(costs, 0.10))
    assert recalc.wacc_override != pytest.approx(loaded)
    held, _ = coerce_dcf_assumptions(doc, raw, loaded, costs=costs, wacc_mode="fixed")
    assert held.wacc_override == pytest.approx(loaded)
    assert "Fixed-WACC" in wacc_basis_note(doc, held, costs, "fixed")
    # An explicit caller wacc_override is the caller's fixed rate, kept as-is.
    explicit, _ = coerce_dcf_assumptions(
        doc, {"tax_rates": [0.10] * 5, "wacc_override": 0.07}, loaded, costs=costs
    )
    assert explicit.wacc_override == pytest.approx(0.07)


def test_wacc_modes_end_to_end_frozen_values():
    from compare import coerce_dcf_assumptions
    from dcf_code import DCFModel, FinancialData

    doc = _frozen_doc()
    costs = doc["source"]["capital_costs"]
    loaded = costs["wacc"]
    data = FinancialData(
        years=["2023", "2024", "2025"],
        revenue=[100.0, 110.0, 121.0],
        ebit=[20.0, 22.0, 24.0],
        ebitda=[25.0, 27.0, 29.0],
        net_income=[10.0, 11.0, 12.0],
        effective_tax_rate=[0.22, 0.24, 0.25],
        interest_expense=[2.0, 2.0, 2.5],
        current_assets=[50.0, 55.0, 60.0],
        current_liabilities=[30.0, 32.0, 35.0],
        cash_and_equivalents=[10.0, 10.0, 10.0],
        short_term_debt=[5.0, 5.0, 5.0],
        long_term_debt=[20.0, 20.0, 20.0],
        total_debt=[25.0, 25.0, 25.0],
        total_assets=[100.0, 110.0, 120.0],
        total_liabilities=[60.0, 65.0, 70.0],
        property_plant_equipment_net=[30.0, 30.0, 30.0],
        preferred_equity=[0.0, 0.0, 0.0],
        d_and_a=[5.0, 5.0, 5.0],
        capex=[6.0, 6.0, 6.0],
        preferred_dividends=[0.0, 0.0, 0.0],
        shares_outstanding=10.0,
        beta=1.0,
        stock_price=50.0,
        market_cap=500.0,
        risk_free_rate=0.04,
        market_return_rate=0.09,
    )
    recalc_a, _ = coerce_dcf_assumptions(doc, None, loaded, costs=costs)
    fixed_a, _ = coerce_dcf_assumptions(doc, None, loaded, costs=costs, wacc_mode="fixed")
    recalc_r = DCFModel(deepcopy(data), recalc_a).calculate()
    fixed_r = DCFModel(deepcopy(data), fixed_a).calculate()
    for key in ("intrinsic_value", "enterprise_value", "equity_value", "target_price_12m"):
        assert recalc_r[key] == pytest.approx(fixed_r[key])
    assert [row["UFCF"] for row in recalc_r["projections"]] == pytest.approx(
        [row["UFCF"] for row in fixed_r["projections"]]
    )
    # Edited tax: fixed holds the loaded discount rate while FCFF moves.
    raw = {"tax_rates": [0.10] * 5}
    recalc_b, _ = coerce_dcf_assumptions(doc, raw, loaded, costs=costs)
    fixed_b, _ = coerce_dcf_assumptions(doc, raw, loaded, costs=costs, wacc_mode="fixed")
    recalc_rb = DCFModel(deepcopy(data), recalc_b).calculate()
    fixed_rb = DCFModel(deepcopy(data), fixed_b).calculate()
    assert fixed_rb["wacc"] == pytest.approx(loaded)
    assert recalc_rb["wacc"] != pytest.approx(loaded)
    assert [row["UFCF"] for row in recalc_rb["projections"]] == pytest.approx(
        [row["UFCF"] for row in fixed_rb["projections"]]
    )


def test_brief_surfaces_tax_and_wacc_basis():
    from brief import build_brief
    from dcf_loader import demo_document

    doc = demo_document()
    brief = build_brief(deepcopy(doc))
    assumptions = brief["assumptions"]
    assert assumptions["forecast_tax_rates"]
    assert assumptions["reported_tax_rates"]
    assert len(assumptions["reported_tax_rates"]) == 3
    assert "wacc_basis" in assumptions and assumptions["wacc_basis"]


def test_api_tax_selection_bypasses_shared_cache(monkeypatch):
    from app import app
    import auto_loading

    seen = {}

    def fake_loader(method, ticker, asof=None, *args, **kwargs):
        seen.update(kwargs)
        return {
            "financials": {"company": {"ticker": ticker}},
            "form": {},
            "load_summary": {},
        }

    monkeypatch.setattr(auto_loading, "load_method", fake_loader)
    client = app.test_client()
    scenario = {
        "rates": [0.231] * 5,
        "evidence": {"filing": "f", "period_end": "2024-12-31"},
    }
    response = client.post(
        "/api/load/dcf", json={"ticker": "ABBV", "tax_scenario": scenario}
    )
    assert response.status_code == 200, response.get_json()
    assert seen.get("tax_scenario") == scenario
    assert response.get_json()["load_summary"]["assembly_cache"]["state"] == "BYPASSED"
    # Malformed selections are 400s, never cached or loaded.
    bad = client.post(
        "/api/load/dcf", json={"ticker": "ABBV", "tax_override": [0.25] * 4}
    )
    assert bad.status_code == 400
    bad2 = client.post(
        "/api/load/dcf",
        json={"ticker": "ABBV", "tax_scenario": {"rates": [0.2] * 5}},
    )
    assert bad2.status_code == 400


def test_explicit_selection_applies_over_yahoo_default_policy(monkeypatch):
    import auto_loading
    from test_yahoo_provider import MockHTTP as YahooHTTP, TODAY as YAHOO_TODAY

    from yahoo_provider import load_yahoo

    http = YahooHTTP()
    doc = load_yahoo("TEST", YAHOO_TODAY, http)
    assert doc["source"]["tax_policy"]["explicit"] is False

    def fake_yahoo(ticker, asof, *args, **kwargs):
        from copy import deepcopy

        return deepcopy(doc)

    monkeypatch.setattr(auto_loading, "load_yahoo", fake_yahoo)
    monkeypatch.setattr(auto_loading, "company_classification", lambda ticker, http: None)
    import issuer_classification

    monkeypatch.setattr(
        issuer_classification, "resolve_classification",
        lambda ticker, sec: {"status": "unconfirmed", "sic": "", "description": "",
                             "source": "test", "source_url": "", "registry_version": ""},
    )
    bundle = auto_loading.load_method(
        "dcf", "TEST", YAHOO_TODAY, http=http,
        tax_scenario={"rates": [0.231] * 5,
                      "evidence": {"filing": "f", "period_end": "2024-12-31"}},
    )
    policy = bundle["financials"]["source"]["tax_policy"]
    assert policy["explicit"] is True
    assert policy["selected"]["basis"] == "normalized_scenario"
    assert policy["selected"]["rates"] == [0.231] * 5
    # Reported history is preserved, not overwritten by the scenario.
    assert [r["rate"] for r in policy["reported"]] == [
        r["tax_rate"] for r in doc["historical"]
    ]


def test_scenario_verification_labels_citation_quality():
    from tax_policy import document_tax_policy

    rows = [
        {"period_end": "2024-12-31", "tax_rate": -0.153,
         "provenance": {"tax_rate": {"accession": "0001551152-25-000020"}}},
        {"period_end": "2025-12-31", "tax_rate": 0.358,
         "provenance": {"tax_rate": {"accession": "0001551152-26-000007"}}},
    ]
    matched = document_tax_policy(
        rows,
        scenario={
            "rates": [0.231] * 5,
            "evidence": {
                "filing": "abbv_fy2024_10k",
                "period_end": "2024-12-31",
                "accession": "0001551152-25-000020",
            },
        },
    )
    assert matched["selected"]["evidence"]["verification"] == "packet_accession_matched"
    # An arbitrary filing string with no accession match stays unverified.
    cited = document_tax_policy(
        rows,
        scenario={
            "rates": [0.231] * 5,
            "evidence": {"filing": "someone-says-so", "period_end": "2024-12-31"},
        },
    )
    assert cited["selected"]["evidence"]["verification"] == "unverified_citation"
    assert cited["selected"]["basis"] == "normalized_scenario"
    override = document_tax_policy(rows, user_override=[0.25] * 5)
    assert override["selected"]["evidence"]["verification"] == "user_assumption"
    default = document_tax_policy(rows[1:])
    assert default["selected"]["evidence"]["verification"] == "not_applicable_default"


def test_equal_wacc_under_both_selected_regimes():
    from compare import coerce_dcf_assumptions, wacc_basis_note

    doc = _frozen_doc()
    costs = doc["source"]["capital_costs"]
    loaded = costs["wacc"]
    recalc, _ = coerce_dcf_assumptions(doc, None, loaded, costs=costs)
    fixed, _ = coerce_dcf_assumptions(
        doc, {"wacc_mode": "fixed"}, loaded, costs=costs, wacc_mode="recalculated"
    )
    # Same numbers, different explicitly selected regimes.
    assert recalc.wacc_override == pytest.approx(fixed.wacc_override)
    assert recalc.wacc_mode == "recalculated" and fixed.wacc_mode == "fixed"
    assert "Recalculated" in wacc_basis_note(doc, recalc, costs, "recalculated")
    assert "Fixed-WACC" in wacc_basis_note(doc, fixed, costs, "fixed")
    # The mode survives an assumptions round-trip (saves/exports/reloads).
    from app import assumptions_from_json
    from dataclasses import asdict

    assert assumptions_from_json(asdict(fixed)).wacc_mode == "fixed"


def _workspace_doc():
    doc = _frozen_doc()
    doc.update(
        valuation_date="2026-10-15",
        units="absolute",
        company={"ticker": "TEST", "name": "Test Inc", "sector": "", "eligible": True,
                  "currency": "USD"},
        market={"price": 50.0, "price_as_of": "2026-10-15", "diluted_shares": 10.0,
                "shares_basis": "test", "currency": "USD"},
        bridge={"short_term_debt": 5.0, "long_term_debt": 20.0, "cash": 10.0,
                "preferred_equity": 0.0, "minority_interest": 0.0,
                "other_nonoperating_assets": 0.0, "as_of": "2025-12-31"},
    )
    doc["source"].update(kind="test", name="test")
    for row in doc["historical"]:
        row["available_at"] = "2026-01-01"
        row["provenance"] = {}
    return doc


def test_workspace_recomputes_stale_wacc_on_tax_edit():
    from app import default_form, form_payload

    doc = _workspace_doc()
    costs = doc["source"]["capital_costs"]
    form = default_form(doc)
    latest_pct = doc["historical"][-1]["tax_rate"] * 100
    for i in range(5):
        form[f"tax_rate_{i}"] = latest_pct + 5.0
    updated, assumptions = form_payload(form)
    assert assumptions.wacc_override != pytest.approx(costs["wacc"])
    assert any("recalculated" in change for change in updated["source"]["manual_overrides"])
    # Fixed mode holds the entered WACC explicitly (the regime is chosen,
    # never inferred from the number).
    form2 = default_form(doc)
    form2["wacc"] = costs["wacc"] * 100 + 1.0
    form2["wacc_mode"] = "fixed"
    updated2, assumptions2 = form_payload(form2)
    assert assumptions2.wacc_override == pytest.approx(costs["wacc"] + 0.01)
    assert assumptions2.wacc_mode == "fixed"
    assert any("fixed" in change for change in updated2["source"]["manual_overrides"])
    # Recalculated mode recomputes even when the WACC field was edited.
    form3 = default_form(doc)
    form3["wacc"] = costs["wacc"] * 100 + 1.0
    form3["wacc_mode"] = "recalculated"
    updated3, assumptions3 = form_payload(form3)
    assert assumptions3.wacc_override == pytest.approx(costs["wacc"])
    assert any("recalculated" in change for change in updated3["source"]["manual_overrides"])
    # A separate shield override beats the forecast tax for the debt shield.
    form4 = default_form(doc)
    form4["shield_override"] = 15.0
    form4["wacc_mode"] = "recalculated"
    updated4, assumptions4 = form_payload(form4)
    assert assumptions4.interest_tax_shield_rate == pytest.approx(0.15)
    from compare import recalculated_wacc

    assert assumptions4.wacc_override == pytest.approx(
        recalculated_wacc(costs, 0.15)
    )
    with pytest.raises(ValueError, match="WACC mode"):
        bad = default_form(doc)
        bad["wacc_mode"] = "inferred"
        form_payload(bad)
