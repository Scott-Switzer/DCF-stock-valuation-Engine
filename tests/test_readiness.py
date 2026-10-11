"""Readiness states come from real missing fields, fallback provenance and dates."""

import copy

from dcf_loader import demo_document
from readiness import PRICE_STALE_DAYS, field_status, method_readiness


def with_dividends(doc, value=50.0):
    doc["source"]["common_dividends"] = {"value": value, "period_end": "2025-12-31"}
    return doc


def with_peer(doc):
    doc["comparables"] = [{"ticker": "PEER", "multiples": {"pe": 20.0}}]
    return doc


def test_demo_dcf_is_sufficient_and_inapplicable_methods_say_why():
    states = method_readiness(demo_document())
    assert states["dcf"]["state"] == "sufficient"
    assert states["dcf"]["missing"] == [] and states["dcf"]["fallback"] == []
    assert states["ddm"]["state"] == "unavailable"
    assert "dividend" in states["ddm"]["reasons"][0]
    assert states["relative"]["state"] == "unavailable"
    assert "peers" in states["relative"]["reasons"][0].lower()


def test_missing_history_field_is_named_and_makes_method_unavailable():
    doc = demo_document()
    period = doc["historical"][-1]["period_end"]
    doc["historical"][-1]["ebit"] = None
    dcf = method_readiness(doc)["dcf"]
    assert dcf["state"] == "unavailable"
    assert f"{period} ebit" in dcf["missing"]


def test_missing_market_price_is_unavailable_for_every_method():
    doc = demo_document()
    doc["market"]["price"] = None
    states = method_readiness(doc)
    assert all(s["state"] == "unavailable" for s in states.values())
    assert "market price" in states["dcf"]["missing"]


def test_old_price_is_stale_not_sufficient():
    doc = demo_document()
    doc["market"]["price_as_of"] = "2026-09-01"
    dcf = method_readiness(doc)["dcf"]
    assert dcf["state"] == "stale"
    assert str(PRICE_STALE_DAYS) in dcf["reasons"][0]


def test_price_within_window_is_not_stale():
    doc = demo_document()
    doc["market"]["price_as_of"] = doc["valuation_date"]
    assert method_readiness(doc)["dcf"]["state"] == "sufficient"


def test_fallback_provenance_marks_the_method_that_uses_it():
    doc = demo_document()
    period = doc["historical"][-1]["period_end"]
    doc["source"]["field_coverage"] = [
        {"field": f"historical.{period}.revenue", "status": "fallback"},
        {"field": f"historical.{period}.ebit", "status": "PPE"},
    ]
    states = method_readiness(doc)
    assert states["dcf"]["state"] == "fallback"
    assert states["dcf"]["fallback"] == [f"historical.{period}.revenue"]


def test_dividend_fallback_only_affects_ddm():
    doc = with_dividends(demo_document())
    doc["source"]["field_coverage"] = [{"field": "common_dividends", "status": "fallback"}]
    states = method_readiness(doc)
    assert states["ddm"]["state"] == "fallback"
    assert states["dcf"]["state"] == "sufficient"


def test_documents_without_field_coverage_report_no_fallbacks():
    states = method_readiness(demo_document())
    assert all(s["fallback"] == [] for s in states.values())


def test_dividend_payer_and_peer_set_make_both_methods_sufficient():
    doc = with_peer(with_dividends(demo_document()))
    states = method_readiness(doc)
    assert states["ddm"]["state"] == "sufficient"
    assert states["relative"]["state"] == "sufficient"


def test_peer_without_any_usable_multiple_does_not_count():
    doc = demo_document()
    doc["comparables"] = [{"ticker": "EMPTY", "multiples": {"pe": None}}]
    assert method_readiness(doc)["relative"]["state"] == "unavailable"


def test_zero_dividend_is_treated_as_no_dividend():
    doc = with_dividends(demo_document(), value=0.0)
    assert method_readiness(doc)["ddm"]["state"] == "unavailable"


def test_readiness_does_not_mutate_the_document():
    doc = with_peer(with_dividends(demo_document()))
    before = copy.deepcopy(doc)
    method_readiness(doc)
    assert doc == before


def test_residual_income_is_sufficient_on_demo_and_blocked_by_senior_claims():
    doc = demo_document()
    doc["source"]["capital_costs"] = {"cost_of_equity": 0.07}
    assert method_readiness(doc)["residual"]["state"] == "sufficient"
    doc["bridge"]["preferred_equity"] = 5.0
    residual = method_readiness(doc)["residual"]
    assert residual["state"] == "unavailable"
    assert any("preferred" in r.lower() for r in residual["reasons"])


def test_relative_readiness_uses_the_peer_set_the_relative_lane_used():
    # The DCF snapshot carries no peers, but the relative lane loads its own
    # peer set. Readiness must describe the peers that lane actually used.
    doc = demo_document()
    relative_doc = with_peer(demo_document())
    states = method_readiness(doc, relative_doc=relative_doc)
    assert states["relative"]["state"] == "sufficient"
    assert states["relative"]["reasons"] == []


def test_compare_page_has_no_inline_styles_for_csp(monkeypatch):
    # The app's CSP is style-src 'self', which blocks style="..." attributes.
    import app as app_module
    from compare import _packet, baseline_dcf_assumptions

    doc = demo_document()
    lanes = [
        {"method": "dcf", "label": "DCF intrinsic (today)", "value": 100.0,
         "detail": "d", "warnings": []},
        {"method": "ddm", "label": "DDM", "value": None, "detail": "n/a", "warnings": []},
    ]
    packet = _packet(doc, lanes, {"load_summary": {}}, baseline_dcf_assumptions(doc, 0.065), False, False)
    monkeypatch.setattr(app_module, "football_field", lambda *args, **kwargs: packet)
    body = app_module.app.test_client().post("/compare", data={"ticker": "DEMO"}).get_data(as_text=True)
    assert 'style="' not in body
    assert 'data-width="' in body


def test_compare_page_shows_readiness_states(monkeypatch):
    import app as app_module
    from compare import _packet, baseline_dcf_assumptions

    # Offline: build the packet from the demo document instead of a live load.
    doc = demo_document()
    packet = _packet(doc, [], {"load_summary": {}}, baseline_dcf_assumptions(doc, 0.065), False, False)
    monkeypatch.setattr(app_module, "football_field", lambda *args, **kwargs: packet)
    body = app_module.app.test_client().post("/compare", data={"ticker": "DEMO"}).get_data(as_text=True)
    assert "Input readiness" in body
    assert "Sufficient inputs" in body and "Unavailable" in body


def test_missing_inputs_carry_machine_readable_codes():
    doc = demo_document()
    period = doc["historical"][-1]["period_end"]
    doc["historical"][-1]["ebit"] = None
    dcf = method_readiness(doc)["dcf"]
    assert "missing_history_ebit" in dcf["codes"]
    assert dcf["missing"] == [f"{period} ebit"]


def test_field_status_reports_missing_and_fallback_per_field():
    doc = demo_document()
    period = doc["historical"][-1]["period_end"]
    doc["historical"][-1]["ebit"] = None
    doc["source"]["field_coverage"] = [
        {"field": f"historical.{period}.revenue", "status": "fallback"}
    ]
    status = field_status(doc)
    assert status[f"historical.{period}.ebit"] == {
        "status": "missing",
        "code": "missing_history_ebit",
    }
    assert status[f"historical.{period}.revenue"]["status"] == "fallback"
    assert status["market.price"]["status"] == "present"


def test_missing_values_are_never_zero_filled():
    doc = demo_document()
    doc["market"]["diluted_shares"] = None
    assert field_status(doc)["market.diluted_shares"]["status"] == "missing"
    assert doc["market"]["diluted_shares"] is None


def test_financial_firm_blocks_industrial_dcf_but_keeps_residual_and_relative():
    doc = with_peer(demo_document())
    doc["source"]["capital_costs"] = {"cost_of_equity": 0.07}
    doc["source"]["classification"] = {"sic": "6022", "description": "State commercial banks"}
    states = method_readiness(doc)
    assert states["dcf"]["state"] == "unavailable"
    assert "financial_firm_enterprise_model" in states["dcf"]["codes"]
    assert states["residual"]["state"] == "sufficient"
    assert states["relative"]["state"] == "sufficient"


def test_unused_source_metric_is_named_when_diluted_shares_missing():
    doc = demo_document()
    doc["market"]["diluted_shares"] = None
    doc["source"]["excluded_metrics"] = {"shares_outstanding": "basic count, not diluted"}
    reasons = method_readiness(doc)["dcf"]["reasons"]
    assert any("shares_outstanding" in r and "not used" in r for r in reasons)


def test_residual_requires_explicit_cost_of_equity():
    doc = demo_document()
    doc['source'].pop('capital_costs', None)
    state = method_readiness(doc)['residual']
    assert state['state'] == 'unavailable'
    assert 'missing_cost_of_equity' in state['codes']


def test_bank_ev_only_peers_are_not_ready():
    doc = demo_document()
    doc['company']['is_financial'] = True
    doc['comparables'] = [{'ticker': 'PEER', 'multiples': {'ev_revenue': 3.0}}]
    assert method_readiness(doc)['relative']['state'] == 'unavailable'


def test_relative_requires_positive_matching_target_metric():
    from suite_models import suite_sample
    doc = demo_document()
    rel = suite_sample('relative')
    rel['target']['forward'].update(revenue=-1, ebitda=-1, ebit=-1, net_income=-1, book_value=-1)
    assert method_readiness(doc, rel)['relative']['state'] == 'unavailable'
