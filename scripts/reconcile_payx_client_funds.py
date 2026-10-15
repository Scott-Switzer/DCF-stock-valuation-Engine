"""Reconcile Paychex client funds against the SEC-first packet inputs.

Reads no bulk data: every filed balance-sheet line below was transcribed from
the original Form 10-K filings (see SOURCES) and is pinned by the companion
tests. Method A is the current packet derivation; B2 is the fully
filing-supported fiduciary carve-out; B1/B3 are sensitivities that show why an
asymmetric PEO-cash removal is an error and why a symmetric one needs an
undisclosed liability split.

With one frozen assumption set, the script replicates the live staging DCF
(Method A must match the staging load to the cent) and bridges every changed
input, annual FCFF, terminal value, equity value and per-share intrinsic for
each variant. Writes find/outputs/company-packets/payx-client-funds.json.

Usage: PYTHONPATH=. .venv/bin/python scripts/reconcile_payx_client_funds.py
"""

import json
from pathlib import Path

M = 1_000_000

# Filed Consolidated Balance Sheets, USD millions. FY2026 10-K accession
# 0001193125-26-307785 (filed 2026-07-17) carries FY2026 + FY2025; FY2024 10-K
# accession 0000950170-24-082958 (filed 2024-07-11) carries FY2024 (+FY2023).
FILED = {
    "2024-05-31": {
        "cash": 1468.9, "peo_in_cash": 171.7, "funds_held": 3706.2,
        "current_assets": 7251.5, "client_obligations": 3868.7,
        "current_liab": 5309.1, "debt_in_cl": 18.7,
    },
    "2025-05-31": {
        "cash": 1628.6, "peo_in_cash": 179.8, "funds_held": 4813.3,
        "current_assets": 8916.5, "client_obligations": 4867.0,
        "current_liab": 6956.3, "debt_in_cl": 418.4,
    },
    "2026-05-31": {
        "cash": 1088.2, "peo_in_cash": 217.7, "funds_held": 4832.2,
        "current_assets": 8613.3, "client_obligations": 4884.6,
        "current_liab": 6840.6, "debt_in_cl": 0.0,
    },
}

# Frozen model inputs: packet history + the live staging assumption set
# recorded 2026-10-15 (growth 5% x5, 3-yr mean margins, latest tax, live
# WACC). The market price only scales upside, never intrinsic.
HISTORY = {
    "revenue": [5132.0, 5410.0, 6301.1],
    "ebit": [2174.1, 2207.7, 2510.5],
    "d_and_a": [176.5, 209.5, 442.6],
    "capex": [161.4, 191.8, 234.9],
}
FROZEN = {
    "growth": [0.05] * 5,
    "tax": 0.23834869531351421,
    "wacc": 0.08647277957862222,
    "terminal_g": 0.02,
    "shares": 360.0,
    "debt": 4556.1,
}
ENDS = ["2024-05-31", "2025-05-31", "2026-05-31"]


def nwc_a(end):
    f = FILED[end]
    return (f["current_assets"] - f["cash"]) - (f["current_liab"] - f["debt_in_cl"])


def nwc_b2(end):
    # Operating NWC excluding the fiduciary pair (both legs filed line items).
    f = FILED[end]
    return (f["current_assets"] - f["cash"] - f["funds_held"]) - (
        f["current_liab"] - f["client_obligations"] - f["debt_in_cl"]
    )


def run_dcf(nwc_hist, cash):
    rev = HISTORY["revenue"]
    ebit_m = sum(e / r for e, r in zip(HISTORY["ebit"], rev)) / 3
    da_m = sum(d / r for d, r in zip(HISTORY["d_and_a"], rev)) / 3
    capex_m = sum(c / r for c, r in zip(HISTORY["capex"], rev)) / 3
    nwc_m = sum(n / r for n, r in zip(nwc_hist, rev)) / 3
    wacc, tax = FROZEN["wacc"], FROZEN["tax"]
    flows, pv_sum, prev_nwc, r = [], 0.0, nwc_hist[-1], rev[-1]
    for g in FROZEN["growth"]:
        r *= 1 + g
        ebit, da, capex = r * ebit_m, r * da_m, r * capex_m
        nwc = r * nwc_m
        dnwc = nwc - prev_nwc
        prev_nwc = nwc
        ufcf = ebit * (1 - tax) + da - capex - dnwc
        flows.append(
            {"revenue": r, "ebit": ebit, "nwc": nwc, "change_nwc": dnwc, "ufcf": ufcf}
        )
    for i, fl in enumerate(flows):
        pv_sum += fl["ufcf"] / (1 + wacc) ** (i + 1)
    tv = flows[-1]["ufcf"] * (1 + FROZEN["terminal_g"]) / (wacc - FROZEN["terminal_g"])
    ev = pv_sum + tv / (1 + wacc) ** 5
    equity = ev - FROZEN["debt"] * M / M + cash - 0 - 0
    intrinsic = equity / FROZEN["shares"]
    return {
        "nwc_margin": nwc_m,
        "flows": flows,
        "pv_stage1": pv_sum,
        "terminal_value": tv,
        "enterprise_value": ev,
        "equity_value": equity,
        "intrinsic": intrinsic,
    }


def main():
    nwc_hist_a = [nwc_a(e) for e in ENDS]
    assert [round(v, 1) for v in nwc_hist_a] == [492.2, 750.0, 684.5], nwc_hist_a
    nwc_hist_b2 = [nwc_b2(e) for e in ENDS]
    assert [round(v, 1) for v in nwc_hist_b2] == [654.7, 803.7, 736.9], nwc_hist_b2
    f26 = FILED["2026-05-31"]
    # No-double-count identity: client balances enter once, net, inside NWC;
    # the bridge carries plain reported cash only.
    net_client_2026 = f26["funds_held"] - f26["client_obligations"]
    assert round(nwc_hist_a[2] - nwc_hist_b2[2], 1) == round(net_client_2026, 1)
    assert round(f26["cash"] + nwc_hist_a[2], 1) == round(
        f26["current_assets"] - f26["current_liab"] + f26["debt_in_cl"], 1
    )

    # Live staging reference (PAYX load 2026-10-15, price 110.78): the frozen
    # harness must replicate it before any variant is trusted.
    live = {
        "intrinsic": 88.01403475349672,
        "equity_value": 31685052511.25882,
        "enterprise_value": 35152952511.25882,
        "terminal_value": 39478898880.81454,
    }
    nwc_hist_a = [round(v, 1) for v in nwc_hist_a]
    nwc_hist_b2 = [round(v, 1) for v in nwc_hist_b2]
    variants = {
        # A: current staging methodology (retained).
        "A_current": {"nwc": nwc_hist_a, "cash": f26["cash"]},
        # B2: symmetric fiduciary carve-out, both legs filed (forecast-only effect).
        "B2_ex_fiduciary": {"nwc": nwc_hist_b2, "cash": f26["cash"]},
        # B1: asymmetric PEO-cash removal (rejected: fabricates a claim).
        "B1_cash_only_SENSITIVITY_REJECTED": {
            "nwc": nwc_hist_a, "cash": f26["cash"] - f26["peo_in_cash"]
        },
        # B3: symmetric PEO carve-out assuming the float's offset sits in
        # operating CL (undisclosed split: sensitivity only, not packet input).
        "B3_peo_symmetric_SENSITIVITY": {
            "nwc": [b + FILED[e]["peo_in_cash"] for b, e in zip(nwc_hist_b2, ENDS)],
            "cash": f26["cash"] - f26["peo_in_cash"],
        },
    }
    results = {name: run_dcf(v["nwc"], v["cash"]) for name, v in variants.items()}
    rep = results["A_current"]
    for key in live:
        # Harness works in USD millions (intrinsic is already per-share).
        got = rep[key] * M if key != "intrinsic" else rep[key]
        assert abs(got - live[key]) / live[key] < 1e-9, (key, got, live[key])

    out = {
        "generated_at": "2026-10-15",
        "filed_millions": FILED,
        "sources": {
            "fy2026_10k": {
                "accession": "0001193125-26-307785",
                "filed": "2026-07-17",
                "url": "https://www.sec.gov/Archives/edgar/data/723531/0001193125-26-307785/payx-20260531.htm",
                "filing_sha256": "c2112792d0e7be7e7c979e50a6e3e844db1fde6c2729d9f9f24fb89cf96a2ab0",
                "covers": ["2026-05-31", "2025-05-31"],
            },
            "fy2024_10k": {
                "accession": "0000950170-24-082958",
                "filed": "2024-07-11",
                "url": "https://www.sec.gov/Archives/edgar/data/723531/000095017024082958/payx-20240531.htm",
                "covers": ["2024-05-31"],
            },
        },
        "frozen_inputs": {"history": HISTORY, **FROZEN},
        "live_staging_reference": dict(
            live, price=110.78, wacc_basis="dated Treasury + 1.5pp spread; beta 0.7946"
        ),
        "methods": {
            "A_current": {
                "nwc": nwc_hist_a, "cash": f26["cash"], "verdict": "retained",
            },
            "B2_ex_fiduciary": {
                "nwc": nwc_hist_b2, "cash": f26["cash"], "verdict": "documented alternative",
            },
        },
        "valuation_bridge": {
            name: {
                "nwc_margin": r["nwc_margin"],
                "annual_ufcf_usd": [fl["ufcf"] * M for fl in r["flows"]],
                "pv_stage1_usd": r["pv_stage1"] * M,
                "terminal_value_usd": r["terminal_value"] * M,
                "enterprise_value_usd": r["enterprise_value"] * M,
                "equity_value_usd": r["equity_value"] * M,
                "intrinsic": r["intrinsic"],
                "delta_intrinsic_vs_A": r["intrinsic"] - rep["intrinsic"],
            }
            for name, r in results.items()
        },
        "conclusion": (
            "Method A retained: companyfacts carries no ClientFundObligations "
            "(payx: extension) or PEO-float concept, so no reusable XBRL mapping "
            "exists; B1 is an asymmetric error (-217.7M cash with no liability "
            "relief); B2/B3 are level-neutral by the cash+NWC=CA-CL+debt identity "
            "and move only NWC-margin forecasts. MD&A supports operating "
            "treatment of the PEO float (settled through corporate cash)."
        ),
    }
    dest = Path("find/outputs/company-packets/payx-client-funds.json")
    dest.write_text(json.dumps(out, indent=1) + "\n")
    a, b2 = results["A_current"], results["B2_ex_fiduciary"]
    b1, b3 = results["B1_cash_only_SENSITIVITY_REJECTED"], results["B3_peo_symmetric_SENSITIVITY"]
    print(f"A  intrinsic {a['intrinsic']:.4f} (replicates live {live['intrinsic']:.4f})")
    print(f"B2 intrinsic {b2['intrinsic']:.4f}  delta {b2['intrinsic']-a['intrinsic']:+.4f}/sh")
    print(f"B1 intrinsic {b1['intrinsic']:.4f}  delta {b1['intrinsic']-a['intrinsic']:+.4f}/sh (REJECTED asymmetric)")
    print(f"B3 intrinsic {b3['intrinsic']:.4f}  delta {b3['intrinsic']-a['intrinsic']:+.4f}/sh (sensitivity)")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
