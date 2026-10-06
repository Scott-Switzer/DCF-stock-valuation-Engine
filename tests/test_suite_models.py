import pytest
from suite_models import DDMModel, DDMAssumptions, RelativeModel, RelativeAssumptions, suite_sample


def test_ddm_matches_cuig_total_dividend_and_horizon_arithmetic():
    doc = suite_sample("ddm")
    a = DDMAssumptions([0.05, 0.08, 0.04, 0.03, 0.02], 0.07, 0.02)
    r = DDMModel(doc, a).calculate()
    dividends = []
    d = 100
    for g in a.dividend_growth_rates:
        d *= 1 + g
        dividends.append(d)
    tv = dividends[-1] * 1.02 / 0.05
    expected = (sum(d / 1.07 ** (i + 1) for i, d in enumerate(dividends)) + tv / 1.07**5) / 100
    expected12 = (sum(d / 1.07**i for i, d in enumerate(dividends) if i > 0) + tv / 1.07**4) / 100
    assert r["intrinsic_value"] == pytest.approx(expected)
    assert r["target_price_12m"] == pytest.approx(expected12)
    assert r["target_price_12m"] == pytest.approx(r["intrinsic_value"] * 1.07 - dividends[0] / 100)


@pytest.mark.parametrize("change", ["no_dividend", "g_above_ke", "nan", "wrong_currency"])
def test_ddm_rejects_invalid_assumptions_and_inputs(change):
    doc = suite_sample("ddm")
    a = DDMAssumptions([0.05] * 5, 0.07, 0.02)
    if change == "no_dividend":
        doc["base_common_dividends"] = 0
    if change == "g_above_ke":
        a.terminal_growth_rate = 0.07
    if change == "nan":
        a.dividend_growth_rates[2] = float("nan")
    if change == "wrong_currency":
        doc["market"]["currency"] = "EUR"
    with pytest.raises(ValueError):
        DDMModel(doc, a).calculate()


def test_relative_matches_cuig_forward_metrics_bridge_and_selection():
    doc = suite_sample("relative")
    a = RelativeAssumptions(["ev_revenue", "ev_ebitda", "pe"])
    r = RelativeModel(doc, a).calculate()
    values = []
    for key, metric in [("ev_revenue", "revenue"), ("ev_ebitda", "ebitda"), ("pe", "net_income")]:
        avg = sum(p["multiples"][key] for p in doc["comparables"]) / 4
        implied = avg * doc["target"]["forward"][metric]
        if key.startswith("ev_"):
            implied -= 100
        values.append(implied / 100)
    assert r["target_price_12m"] == pytest.approx(sum(values) / 3)
    assert r["intrinsic_value"] is None


def test_relative_equity_methods_do_not_deduct_debt_again():
    doc = suite_sample("relative")
    a = RelativeAssumptions(["pe"])
    original = RelativeModel(doc, a).calculate()["target_price_12m"]
    doc["bridge"]["long_term_debt"] = 500
    assert RelativeModel(doc, a).calculate()["target_price_12m"] == original


def test_financial_company_uses_equity_multiples_only():
    doc = suite_sample("relative")
    doc["company"]["sector"] = "Banking"
    with pytest.raises(ValueError):
        RelativeModel(doc, RelativeAssumptions(["ev_revenue"])).calculate()
    assert RelativeModel(doc, RelativeAssumptions(["pe", "pb"])).calculate()["target_price_12m"] > 0


def test_missing_selected_peer_multiple_never_becomes_zero():
    doc = suite_sample("relative")
    for p in doc["comparables"]:
        p["multiples"]["pe"] = None
    with pytest.raises(ValueError):
        RelativeModel(doc, RelativeAssumptions(["pe"])).calculate()


@pytest.mark.parametrize("method", ["ddm", "relative"])
@pytest.mark.parametrize(
    "change", ["future_price", "missing_shares", "nonfinite_price", "no_confirmation"]
)
def test_common_method_boundaries(method, change):
    doc = suite_sample(method)
    if change == "future_price":
        doc["market"]["price_as_of"] = "2099-01-01"
    if change == "missing_shares":
        doc["market"]["diluted_shares"] = None
    if change == "nonfinite_price":
        doc["market"]["price"] = float("inf")
    if change == "no_confirmation":
        doc["company"]["eligible"] = False
    a = DDMAssumptions([0.05] * 5, 0.07, 0.02) if method == "ddm" else RelativeAssumptions(["pe"])
    cls = DDMModel if method == "ddm" else RelativeModel
    with pytest.raises(ValueError):
        cls(doc, a).calculate()


def test_relative_negative_earnings_multiple_is_excluded_and_coverage_disclosed():
    doc = suite_sample("relative")
    doc["comparables"][0]["multiples"]["pe"] = -5
    r = RelativeModel(doc, RelativeAssumptions(["pe"])).calculate()
    row = next(x for x in r["multiples"] if x["key"] == "pe")
    assert row["count"] == 3
    assert row["mean"] == 17
    assert any("1 peer(s)" in w for w in r["warnings"])


def test_financial_company_metadata_and_confirmation_protect_enterprise_methods():
    doc = suite_sample("relative")
    doc["company"]["industry"] = "Insurance"
    with pytest.raises(ValueError):
        RelativeModel(doc, RelativeAssumptions(["ev_ebitda"])).calculate()
    r = RelativeModel(doc, RelativeAssumptions(["pe", "pb"])).calculate()
    assert all(
        row["implied_price"] is None for row in r["multiples"] if row["key"].startswith("ev_")
    )


@pytest.mark.parametrize("method", ["ddm", "relative"])
def test_provider_imports_require_information_available_by_valuation_date(method):
    doc = suite_sample(method)
    doc["source"].update(kind="api", available_at="2027-02-01")
    a = DDMAssumptions([0.05] * 5, 0.07, 0.02) if method == "ddm" else RelativeAssumptions(["pe"])
    cls = DDMModel if method == "ddm" else RelativeModel
    with pytest.raises(ValueError, match="available"):
        cls(doc, a).calculate()
    doc["source"].pop("available_at")
    with pytest.raises(ValueError, match="availability"):
        cls(doc, a).calculate()
    doc["source"]["available_at"] = "2026-02-01"
    assert cls(doc, a).calculate()["target_price_12m"] > 0
