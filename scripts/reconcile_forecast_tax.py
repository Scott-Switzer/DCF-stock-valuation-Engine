"""Frozen forecast-tax reconciliation for ABBV and AEP.

Transcribed filing histories and ETR reconciliations (see SOURCES) are
checked with tax_policy.build_tax_reconciliation, then run through the real
dcf_code.DCFModel under one frozen market-input set per company. Scenarios:

- OLD: pre-policy baseline behavior (refuses: negative history invalid).
- BASE: new default, latest reported rate reused (in-bounds only).
- NORM: filing-supported recurring-only normalized scenario (explicit).
- USER: illustrative explicit user override (explicit).

All non-tax inputs are identical across a company's scenarios, so every
delta is tax-driven by construction. Market inputs are frozen and labeled
illustrative; only deltas are meaningful, never the levels.

Writes find/outputs/forecast-tax/abbv-aep-evidence.json.

Usage: PYTHONPATH=. .venv/bin/python scripts/reconcile_forecast_tax.py
"""

import json
from pathlib import Path

from dcf_code import DCFModel, FinancialData, DCFAssumptions
from tax_policy import (
    build_tax_reconciliation,
    resolve_forecast_tax,
    shield_rate,
)

M = 1_000_000

SOURCES = {
    "abbv_fy2024_10k": {
        "accession": "0001551152-25-000020",
        "filed": "2025-02-14",
        "url": "https://www.sec.gov/Archives/edgar/data/1551152/000155115225000020/abbv-20241231.htm",
        "filing_sha256": "8ff44940f8c6efa94031f627113db1b106e3a2de037cbaf8e95e377783ae789e",
    },
    "abbv_fy2025_10k": {
        "accession": "0001551152-26-000008",
        "filed": "2026-02-20",
        "url": "https://www.sec.gov/Archives/edgar/data/1551152/000155115226000008/abbv-20251231.htm",
        "filing_sha256": "fd69830b16258e5db9377f96dcbfc25c18f9dc4b096dca5c36aaf810353432a8",
    },
    "aep_fy2024_10k": {
        "accession": "0000004904-25-000027",
        "filed": "2025-02-13",
        "url": "https://www.sec.gov/Archives/edgar/data/4904/000000490425000027/aep-20241231.htm",
        "filing_sha256": "248ebe498c860cd4f768e28ce24cf444f8c715d7d16a5020cff15c5f785e1243",
    },
    "aep_fy2025_10k": {
        "accession": "0000004904-26-000013",
        "filed": "2026-02-12",
        "url": "https://www.sec.gov/Archives/edgar/data/4904/000000490426000013/aep-20251231.htm",
        "filing_sha256": "5b621624907d2bc9b319d9a2a6be9054eb3bf66678492fe8e92ff101fac8bedf",
    },
}

# Filed histories, USD millions (balance-sheet/cash-flow lines transcribed
# from the 10-Ks above; income-statement lines cross-checked to companyfacts).
HISTORY = {
    "ABBV": {
        "ends": ["2023-12-31", "2024-12-31", "2025-12-31"],
        "revenue": [54318.0, 56334.0, 61160.0],
        "ebit": [12757.0, 9137.0, 15075.0],
        "d_and_a": [8698.0, 8386.0, 8139.0],
        "capex": [777.0, 974.0, 1214.0],
        "current_assets": [33002.0, 25582.0, 29062.0],
        "cash": [12814.0, 5524.0, 5229.0],
        "current_liab": [37841.0, 38749.0, 43289.0],
        "short_term_debt": [7191.0, 6804.0, 8555.0],
        "long_term_debt": [52194.0, 60340.0, 58941.0],
        "interest": [2224.0, 2808.0, 2893.0],
        "tax_expense": [1377.0, -570.0, 2364.0],
        "pretax": [6250.0, 3716.0, 6597.0],
        "net_income_common": [4820.0, 4238.0, 4186.0],
        "total_assets": [134711.0, 135161.0, 133960.0],
        "total_liab": [124351.0, 131836.0, 137230.0],
        "shares": 1773.0,
    },
    "AEP": {
        "ends": ["2023-12-31", "2024-12-31", "2025-12-31"],
        "revenue": [18982.0, 19721.0, 21876.0],
        "ebit": [3556.0, 4304.0, 5319.0],
        "d_and_a": [2927.5, 3149.0, 3325.0],
        "capex": [7378.0, 7631.0, 8453.0],
        "current_assets": [6082.1, 5789.0, 6052.0],
        "cash": [330.1, 203.0, 197.0],
        "current_liab": [11583.6, 13009.3, 13314.0],
        "short_term_debt": [5320.7, 5859.0, 4702.0],
        "long_term_debt": [37652.7, 39308.0, 44128.0],
        "interest": [1807.0, 1863.0, 2026.0],
        "tax_expense": [55.0, -39.2, 129.0],
        "pretax": [2265.8, 2935.2, 3825.0],
        "net_income_common": [2208.0, 2967.0, 3580.0],
        "total_assets": [96684.0, 103078.0, 114460.0],
        "total_liab": [71355.6, 76054.0, 82204.0],
        "shares": 537.5,
    },
}

# Filed ETR reconciliations: (label, effect_pp, recurring, note).
RECONCILIATIONS = {
    "ABBV_2024": {
        "statutory": 0.21,
        "reported": -570.0 / 3716.0,
        "filing": "abbv_fy2024_10k",
        "period_end": "2024-12-31",
        "components": [
            ("Foreign operations", 7.6, True, "jurisdiction mix; varies"),
            ("U.S. tax credits", -5.4, True, "R&D/incentive credits"),
            ("Stock-based compensation", -1.2, True, "excess benefits"),
            ("Non-deductible expenses", 1.1, True, "meals, penalties, comp limits"),
            ("Tax law changes and structuring", -0.3, False, "one-time structuring"),
            ("Tax audits, settlements and reserves", -51.4, False, "IRS exams closed, reserve releases"),
            ("Acquisition costs", 13.4, False, "ImmunoGen/Cerevel deal costs"),
            ("All other, net", -0.1, False, "residual"),
        ],
    },
    "AEP_2024": {
        "statutory": 0.21,
        "reported": -39.2 / 2935.2,
        "filing": "aep_fy2024_10k",
        "period_end": "2024-12-31",
        "components": [
            ("Origination flow-through reversal", 0.7, True, "regulator-required flow-through"),
            ("Investment tax credit amortization", -2.0, True, "deferral methodology, declines with assets"),
            ("Production tax credits", -7.3, True, "earned as wind MWh produced; IRA visibility, output varies"),
            ("State/local, net", 0.6, True, "primarily Ohio local"),
            ("Removal costs", -0.5, True, "utility cost-of-removal"),
            ("AFUDC equity", -1.6, True, "non-taxable equity allowance; non-cash"),
            ("Tax reform excess ADIT reversal", -3.1, True, "TCJA excess returned via rates; declining balance"),
            ("Remeasurement of excess ADIT", -8.9, False, "Arkansas/Michigan + NOLC PLRs; discrete"),
            ("Other", -0.2, False, "residual"),
        ],
    },
    # FY2025 corroboration: discrete items dominate in BOTH directions, so no
    # single FY2025-based recurring rate is stable. The adopted scenario stays
    # FY2024-based; FY2025 is encoded here to pin that claim, not to average.
    # Filed pp from the FY2025 10-K (Exhibit 13, Income Taxes note, p.57).
    "ABBV_2025": {
        "statutory": 0.21,
        "reported": 2364.0 / 6597.0,
        "filing": "abbv_fy2025_10k",
        "period_end": "2025-12-31",
        "components": [
            ("Puerto Rico earnings differential", 21.6, True, "jurisdiction mix; varies with PR share"),
            ("Puerto Rico industrial development income", -45.3, False, "one-time benefit; pairs with elevated differential"),
            ("Other Puerto Rico provisions", -0.3, True, "routine PR true-ups"),
            ("Bermuda operations", 1.6, True, "jurisdiction mix"),
            ("Bermuda valuation allowance", 4.3, False, "loss DTA realizability; uncertain"),
            ("Other Bermuda", -0.2, True, "routine"),
            ("Ireland operations", -1.7, True, "jurisdiction mix"),
            ("Ireland NOL benefit", 1.5, True, "recognized loss benefit"),
            ("Other Ireland", -0.1, True, "routine"),
            ("Malta operations", -1.8, True, "jurisdiction mix"),
            ("Equity compensation", -1.9, True, "excess benefits"),
            ("Non-deductible expenses", 3.7, True, "deal and comp limits"),
            ("Other provision", 0.5, True, "routine"),
            ("Other provision true-up", 1.4, True, "routine"),
            ("GILTI inclusion", 16.9, False, "elevated foreign inclusion; corroborate structural level"),
            ("Branch operations", -2.3, True, "routine"),
            ("Other foreign", 1.5, True, "routine"),
            ("U.S. tax credits", -2.2, True, "R&D/incentive credits"),
            ("UTB change", 9.9, False, "uncertain-position reserve build"),
            ("Valuation allowance change", -1.4, False, "DTA realizability; uncertain"),
            ("Acquisition-related", 9.8, False, "deal costs"),
            ("Other, net", -0.7, False, "residual"),
        ],
    },
    # AEP FY2025 (10-K p.210): reported 129/3825 = 3.37%. The ONLY discrete
    # item is excess-ADIT remeasurement (-10.01pp); everything else recurs in
    # kind (credits vary with output, but the mechanism recurs). So the
    # recurring-equivalent is 3.37 + 10.01 = 13.38 ~= 13.4% -- NOT 13.0%.
    # (An earlier draft wrote 13.0%; the filed bridge supports 13.4%.)
    "AEP_2025": {
        "statutory": 0.21,
        "reported": 129.0 / 3825.0,
        "filing": "aep_fy2025_10k",
        "period_end": "2025-12-31",
        "components": [
            ("State and local, net", 0.81, True, "primarily Ohio local"),
            ("Production tax credits", -6.38, True, "earned as wind MWh produced; output varies"),
            ("Investment tax credit amortization", -0.08, True, "deferral methodology"),
            ("Other credits", -0.10, True, "routine credits"),
            ("UTB change", 0.08, True, "routine reserve true-up"),
            ("Origination flow-through reversal", 0.47, True, "regulator-required flow-through"),
            ("Tax reform excess ADIT reversal", -1.62, True, "TCJA excess returned via rates; declining"),
            ("Remeasurement of excess ADIT", -10.01, False, "Oklahoma + NOLC PLRs; discrete"),
            ("AFUDC equity", -1.07, True, "non-taxable equity allowance; non-cash"),
            ("Other", 0.29, True, "routine residual"),
        ],
    },
}

# Normalized scenarios adopted explicitly for the frozen runs (evidence, not claims).
SCENARIOS = {
    "ABBV": {"rate": 0.231, "label": "FY2024 recurring-only bridge (21.0+7.6-5.4-1.2+1.1); FY2025 discrete items dominate both ways (-45.3 benefit vs +21.6/+16.9/+9.9/+9.8 charges), so no FY2025-based rate is stable"},
    "AEP": {"rate": 0.078, "label": "FY2024 recurring-only bridge; FY2025 recurring-equivalent 13.4% (3.37 reported + 10.01 discrete remeasurement) shows credit variability"},
}
USER_OVERRIDE = {"ABBV": [0.25] * 5, "AEP": [0.12] * 5}

# Frozen illustrative market inputs (identical across a company's scenarios).
MARKET = {
    "ABBV": {"beta": 0.45, "rf": 0.045, "erp": 0.05, "spread": 0.015},
    "AEP": {"beta": 0.55, "rf": 0.045, "erp": 0.05, "spread": 0.015},
}


def build_data(ticker):
    h = HISTORY[ticker]
    nwc = [
        (ca - c) - (cl - std)
        for ca, c, cl, std in zip(
            h["current_assets"], h["cash"], h["current_liab"], h["short_term_debt"]
        )
    ]
    etr = [e / p for e, p in zip(h["tax_expense"], h["pretax"])]
    total_debt = [s + l for s, l in zip(h["short_term_debt"], h["long_term_debt"])]
    mkt = MARKET[ticker]
    return (
        FinancialData(
            years=h["ends"],
            revenue=h["revenue"],
            ebit=h["ebit"],
            ebitda=[a + b for a, b in zip(h["ebit"], h["d_and_a"])],
            net_income=h["net_income_common"],
            effective_tax_rate=etr,
            interest_expense=h["interest"],
            current_assets=h["current_assets"],
            current_liabilities=h["current_liab"],
            cash_and_equivalents=h["cash"],
            short_term_debt=h["short_term_debt"],
            long_term_debt=h["long_term_debt"],
            total_debt=total_debt,
            total_assets=h["total_assets"],
            total_liabilities=h["total_liab"],
            property_plant_equipment_net=[0.0, 0.0, 0.0],
            preferred_equity=[0.0, 0.0, 0.0],
            d_and_a=h["d_and_a"],
            capex=h["capex"],
            preferred_dividends=[0.0, 0.0, 0.0],
            shares_outstanding=h["shares"],
            beta=mkt["beta"],
            stock_price=100.0,
            market_cap=100.0 * h["shares"],
            risk_free_rate=mkt["rf"],
            market_return_rate=mkt["rf"] + mkt["erp"],
        ),
        {"nwc": nwc, "etr": etr, "total_debt": total_debt},
    )


def run_variant(ticker, data, tax_rates, basis):
    model = DCFModel(
        data,
        DCFAssumptions(
            revenue_growth_rates=[0.05] * 5,
            terminal_growth_rate=0.02,
            tax_rates=tax_rates,
        ),
    )
    policy = {"rates": tax_rates, "basis": basis}
    # Stage separately: flows and WACC always resolve; a terminal value may
    # not exist under this industrial template (AEP: regulated capex
    # structurally exceeds operating cash flow). That refusal is a finding,
    # not a failure to report.
    flows = model.forecast_cash_flows()
    wacc = model.calculate_wacc()
    variant = {
        "basis": basis,
        "forecast_tax": tax_rates[0],
        "shield": shield_rate(policy),
        "wacc": wacc,
        "annual_fcff": [row["UFCF"] for row in flows],
        "annual_nopat": [row["NOPAT"] for row in flows],
    }
    try:
        result = model.calculate()
        variant.update(
            pv_stage1=result["stage1_pv"],
            terminal_value=result["terminal_value"],
            enterprise_value=result["enterprise_value"],
            equity_value=result["equity_value"],
            intrinsic=result["intrinsic_value"],
        )
    except ValueError as exc:
        variant.update(intrinsic=None, terminal_unavailable=str(exc))
    return variant


def build_recon(key):
    spec = RECONCILIATIONS[key]
    return build_tax_reconciliation(
        spec["statutory"],
        [
            {"label": label, "effect_pp": pp, "recurring": rec, "note": note}
            for label, pp, rec, note in spec["components"]
        ],
        spec["reported"],
        spec["filing"],
        spec["period_end"],
    )


def main():
    out = {"sources": SOURCES, "histories": HISTORY, "companies": {}}
    for ticker in ("ABBV", "AEP"):
        spec = RECONCILIATIONS[f"{ticker}_2024"]
        recon = build_recon(f"{ticker}_2024")
        recon25 = build_recon(f"{ticker}_2025")
        data, derived = build_data(ticker)
        etr = derived["etr"]
        # OLD behavior: negative history invalidates the statement.
        old_refusal = (
            "Historical tax rate needs normalization to a rate between 0 and 100%."
            if any(not 0 <= t <= 1 for t in etr)
            else None
        )
        base = resolve_forecast_tax(etr)
        scen = SCENARIOS[ticker]
        norm = resolve_forecast_tax(
            etr,
            scenario={
                "rates": [scen["rate"]] * 5,
                "evidence": {
                    "filing": spec["filing"],
                    "period_end": spec["period_end"],
                    "label": scen["label"],
                    "recurring_only_rate": recon["recurring_only_rate"],
                },
            },
        )
        user = resolve_forecast_tax(etr, user_override=USER_OVERRIDE[ticker])
        variants = {
            "OLD_refused": {"error": old_refusal},
            "BASE_latest_reported": run_variant(ticker, data, base["rates"], base["basis"]),
            "NORM_recurring_only": run_variant(ticker, data, norm["rates"], norm["basis"]),
            "USER_override": run_variant(ticker, data, user["rates"], user["basis"]),
        }
        base_iv = variants["BASE_latest_reported"]["intrinsic"]
        for name, variant in variants.items():
            if variant.get("intrinsic") is not None and base_iv is not None:
                variant["delta_vs_BASE"] = variant["intrinsic"] - base_iv
        company = {
            "reconciliation": recon,
            "reconciliation_2025": recon25,
            "derived": derived,
            "normalized_scenario": scen,
            "user_override": USER_OVERRIDE[ticker],
            "variants": variants,
        }
        if ticker == "ABBV":
            # Sensitivity: FY2025 recurring-only under the adopted flags, and
            # with the whole PR pair treated as one-time (differential moved
            # to discrete alongside the industrial benefit).
            pr_pair = sum(
                c["effect_pp"]
                for c in recon25["components"]
                if "Puerto Rico" in c["label"] and c["recurring"]
            )
            company["fy2025_recurring_sensitivity"] = {
                "adopted_flags": recon25["recurring_only_rate"],
                "pr_pair_discrete": recon25["recurring_only_rate"] - pr_pair / 100,
                "note": "discrete dominates both ways; neither FY2025 point is adopted",
            }
        out["companies"][ticker] = company
        fmt = lambda v: f"{v:.2f}" if v is not None else "n/a (template refusal)"
        b, n, u = (variants[k]["intrinsic"] for k in ("BASE_latest_reported", "NORM_recurring_only", "USER_override"))
        print(f"{ticker}: OLD refused ({any(not 0 <= t <= 1 for t in etr)}); BASE {fmt(b)} NORM {fmt(n)} USER {fmt(u)}")
    dest = Path("find/outputs/forecast-tax/abbv-aep-evidence.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
