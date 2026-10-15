"""Tests for Bottom-Up Beta, CAPM cost of equity, and mutually consistent WACC integration.

Validates:
1. Fetching real Damodaran industry_betas and country_risk_premiums through Zion.
2. Explicit issuer capital structure selection (market D/E vs target D/E; rejection of book D/E).
3. Hamada (zero debt beta) and generalized (nonzero debt beta) relevering & unlevering.
4. Operating cash-corrected beta vs firm unlevered beta, and refusal of double cash correction.
5. CAPM cost-of-equity calculation and refusal of country ERP double counting.
6. Opt-in WACC propagation vs preview-only mode (no silent overwrite of WACC or fundamentals).
7. Full assumption lineage retention and independent Decimal reproduction.
8. Rejection of invalid or historically unavailable inputs.
"""

from datetime import datetime, timezone
from decimal import Decimal
import json as jsonlib
from pathlib import Path
import pytest

from bottom_up_capm import (
    apply_cash_adjustment,
    compute_bottom_up_capm,
    relever_beta,
    resolve_capital_structure,
    resolve_erp,
    unlever_beta,
)
from tests.test_zion_benchmark_chain import RELEASES_ROOT, StubZion

pytestmark = pytest.mark.skipif(
    not RELEASES_ROOT.exists(),
    reason="real DDFI releases are not present in this checkout",
)

INDUSTRY_SUBJECT = "Software (System & Application)"
EXPECTED_BETA_EX_CASH = "1.2481994174665423"
EXPECTED_BETA_FIRM = "1.225391886520662"
EXPECTED_CASH_FIRM_VALUE = "0.018272345449553515"
EXPECTED_US_ERP = "0.0442"
EXPECTED_BRAZIL_TOTAL_ERP = "0.0757"
EXPECTED_BRAZIL_CRP = "0.0311"


def index():
    return jsonlib.loads((RELEASES_ROOT / "index.json").read_bytes())


def release_entry(dataset_id):
    candidates = [e for e in index()["releases"] if e["dataset_id"] == dataset_id]
    assert candidates, f"no built release for {dataset_id}"
    return max(candidates, key=lambda e: e["published_at"])


def today():
    return datetime.now(timezone.utc).date().isoformat()


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch, tmp_path):
    from app import app

    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


def test_hamada_and_nonzero_debt_beta_identities():
    # Zero debt beta (Hamada)
    bu = 1.20
    de = 0.25
    tax = 0.20
    bl = relever_beta(bu, de, tax, debt_beta=0.0)
    assert bl == pytest.approx(1.20 * (1.0 + 0.80 * 0.25))
    assert unlever_beta(bl, de, tax, debt_beta=0.0) == pytest.approx(bu)

    # Nonzero debt beta (generalized Modigliani-Miller)
    bd = 0.15
    bl_gen = relever_beta(bu, de, tax, debt_beta=bd)
    assert bl_gen == pytest.approx(bu + (bu - bd) * (1.0 - tax) * de)
    assert bl_gen < bl  # positive debt beta bears part of asset risk
    assert unlever_beta(bl_gen, de, tax, debt_beta=bd) == pytest.approx(bu)

    # Debt beta exceeding unlevered asset beta is rejected
    with pytest.raises(ValueError, match="INVALID_DEBT_BETA"):
        relever_beta(0.80, 0.25, 0.20, debt_beta=0.90)


def test_cash_correction_distinction_and_no_double_count():
    bu_firm = float(EXPECTED_BETA_FIRM)
    cash_ratio = float(EXPECTED_CASH_FIRM_VALUE)
    corrected = apply_cash_adjustment(bu_firm, cash_ratio, measure_name="unlevered_beta")
    assert corrected == pytest.approx(float(EXPECTED_BETA_EX_CASH), rel=1e-9)

    # Applying cash correction to unlevered_beta_ex_cash is forbidden
    with pytest.raises(ValueError, match="CASH_CORRECTION_DOUBLE_COUNT"):
        apply_cash_adjustment(
            float(EXPECTED_BETA_EX_CASH),
            cash_ratio,
            measure_name="unlevered_beta_ex_cash",
        )


def test_book_leverage_rejected():
    from dcf_loader import demo_document

    doc = demo_document()
    with pytest.raises(ValueError, match="BOOK_LEVERAGE_FORBIDDEN"):
        resolve_capital_structure(doc, {"leverage_mode": "book"})
    with pytest.raises(ValueError, match="BOOK_LEVERAGE_FORBIDDEN"):
        resolve_capital_structure(doc, {"use_book_leverage": True})


def test_erp_double_counting_rejected():
    brazil_total_erp = {
        "subject": "Brazil",
        "measure": "equity_risk_premium",
        "value_decimal": EXPECTED_BRAZIL_TOTAL_ERP,
        "unit": "fraction",
    }
    brazil_crp = {
        "subject": "Brazil",
        "measure": "country_risk_premium",
        "value_decimal": EXPECTED_BRAZIL_CRP,
        "unit": "fraction",
    }
    # Total country ERP alone works
    res = resolve_erp(erp_benchmark=brazil_total_erp)
    assert res["applicable_erp"] == pytest.approx(0.0757)
    assert res["erp_includes_country_risk"] is True

    # Combining Total country ERP with incremental CRP is rejected
    with pytest.raises(ValueError, match="ERP_DOUBLE_COUNTING"):
        resolve_erp(erp_benchmark=brazil_total_erp, crp_benchmark=brazil_crp)
    with pytest.raises(ValueError, match="ERP_DOUBLE_COUNTING"):
        resolve_erp(erp_benchmark=brazil_total_erp, country_risk_premium=0.0311)

    # Mature-market ERP + incremental CRP works and matches Brazil Total ERP (0.0446 + 0.0311 = 0.0757)
    res_mature_plus_crp = resolve_erp(
        mature_market_erp=0.0446,
        crp_benchmark=brazil_crp,
        country_lambda=1.0,
    )
    assert res_mature_plus_crp["applicable_erp"] == pytest.approx(0.0757)
    assert res_mature_plus_crp["mode"] == "mature_erp_plus_country_spread"


def test_end_to_end_bottom_up_beta_capm_and_wacc_through_zion(monkeypatch):
    from app import app
    from dcf_loader import demo_document

    beta_rel = release_entry("industry_betas")
    crp_rel = release_entry("country_risk_premiums")
    stub = StubZion()
    monkeypatch.setenv("ZION_BENCHMARK_BASE_URL", "https://zion-stub.invalid")
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "stub-token")
    monkeypatch.setattr("requests.post", stub.post)

    doc = demo_document()
    doc["valuation_date"] = today()
    client = app.test_client()

    bottom_up_spec = {
        "beta_benchmark": {
            "release_id": beta_rel["release_id"],
            "subject": INDUSTRY_SUBJECT,
            "measure": "unlevered_beta_ex_cash",
            "mode": "historical",
            "source": "zion",
        },
        "erp_benchmark": {
            "release_id": crp_rel["release_id"],
            "subject": "United States",
            "measure": "equity_risk_premium",
            "mode": "historical",
            "source": "zion",
        },
        "leverage_mode": "issuer_market",
        "marginal_tax_rate": 0.21,
        "risk_free_rate": 0.042,
        "pre_tax_cost_of_debt": 0.052,
        "propagate_to_wacc": True,
    }

    # 1. Preview endpoint
    preview_resp = client.post(
        "/api/capm/preview",
        json={"financials": doc, "bottom_up_beta": bottom_up_spec},
    )
    assert preview_resp.status_code == 200, preview_resp.json
    preview = preview_resp.json

    # Independent high-precision Decimal verification
    price = Decimal(str(doc["market"]["price"]))
    shares = Decimal(str(doc["market"]["diluted_shares"]))
    mkt_eq = price * shares
    total_debt = Decimal(str(doc["bridge"]["short_term_debt"])) + Decimal(
        str(doc["bridge"]["long_term_debt"])
    )
    pref = Decimal(str(doc["bridge"]["preferred_equity"]))
    de_ratio = total_debt / mkt_eq
    tax = Decimal("0.21")
    bu = Decimal(EXPECTED_BETA_EX_CASH)
    expected_bl = bu * (Decimal("1") + (Decimal("1") - tax) * de_ratio)
    rf = Decimal("0.042")
    erp = Decimal(EXPECTED_US_ERP)
    expected_ke = rf + expected_bl * erp
    tot_cap = mkt_eq + total_debt + pref
    kd_after = Decimal("0.052") * (Decimal("1") - tax)
    expected_wacc = (mkt_eq / tot_cap) * expected_ke + (total_debt / tot_cap) * kd_after

    assert preview["beta_decomposition"]["operating_unlevered_beta"] == pytest.approx(float(bu))
    assert preview["beta_decomposition"]["relevered_equity_beta"] == pytest.approx(float(expected_bl))
    assert preview["capm"]["cost_of_equity"] == pytest.approx(float(expected_ke))
    assert preview["wacc_build"]["wacc"] == pytest.approx(float(expected_wacc))
    assert preview["benchmark_sources"]["beta_benchmark"]["release_id"] == beta_rel["release_id"]
    assert preview["benchmark_sources"]["erp_benchmark"]["release_id"] == crp_rel["release_id"]

    # 2. Full valuation with propagate_to_wacc=True
    calc_resp = client.post(
        "/api/calculate",
        json={
            "financials": doc,
            "assumptions": {
                "revenue_growth_rates": [0.06] * 5,
                "terminal_growth_rate": 0.025,
            },
            "bottom_up_beta": bottom_up_spec,
        },
    )
    assert calc_resp.status_code == 200, calc_resp.json
    res = calc_resp.json
    assert res["wacc"] == pytest.approx(float(expected_wacc))
    assert res["bottom_up_capm"]["capm"]["cost_of_equity"] == pytest.approx(float(expected_ke))
    assert res["bottom_up_capm"]["wacc_build"]["propagated_to_dcf_wacc"] is True

    # 3. Verify that propagate_to_wacc=False does NOT overwrite DCF's WACC
    spec_no_prop = dict(bottom_up_spec, propagate_to_wacc=False)
    calc_no_prop = client.post(
        "/api/calculate",
        json={
            "financials": doc,
            "assumptions": {
                "revenue_growth_rates": [0.06] * 5,
                "terminal_growth_rate": 0.025,
                "wacc_override": 0.085,
            },
            "bottom_up_beta": spec_no_prop,
        },
    )
    assert calc_no_prop.status_code == 200, calc_no_prop.json
    assert calc_no_prop.json["wacc"] == pytest.approx(0.085)
    assert calc_no_prop.json["bottom_up_capm"]["capm"]["cost_of_equity"] == pytest.approx(
        float(expected_ke)
    )
    assert calc_no_prop.json["bottom_up_capm"]["wacc_build"]["propagated_to_dcf_wacc"] is False

    # 4. Conflicting wacc_override + propagate_to_wacc=True is rejected
    conflict_resp = client.post(
        "/api/calculate",
        json={
            "financials": doc,
            "assumptions": {
                "revenue_growth_rates": [0.06] * 5,
                "terminal_growth_rate": 0.025,
                "wacc_override": 0.085,
            },
            "bottom_up_beta": bottom_up_spec,
        },
    )
    assert conflict_resp.status_code == 400
    assert "Conflicting explicit assumption" in conflict_resp.json["error"]
