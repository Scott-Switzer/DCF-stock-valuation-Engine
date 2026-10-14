"""Three clearly defined PEP valuations on one frozen input set.

Freezes market price, valuation date, share count, WACC and forecast horizon
so that remaining differences isolate accounting definitions:

  A. Reported-GAAP basis: SEC-first observations as disclosed.
  B. Normalized-operating basis: A plus source-backed impairment add-backs
     (accounting_policy.normalize); assumes no recurrence, flagged.
  C. Provider-derived basis: Yahoo conventions as served (EBIT ex-impairment,
     D&A incl. operating-lease ROU amortization), explicitly labeled.

Writes docs/pep-three-bases.md and docs/pep-three-bases.json. Usage:

  .venv/bin/python scripts/pep_three_bases.py \
      --sec-doc /tmp/pep/staging.json --yahoo-doc /tmp/pep/prod.json
"""

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FROZEN = {
    "valuation_date": "2026-10-14",
    "price": 128.55,  # midpoint of the two same-day quotes, disclosed
    "price_note": "Midpoint of same-day Yahoo quotes 128.495 / 128.60; "
    "held fixed to isolate statement-definition effects.",
    "shares": 1373000000.0,
    "wacc": 0.0572,
    "wacc_note": "Held fixed (rounding of both live WACCs) to isolate "
    "accounting effects; live WACCs differ by 0.4bp from quote timing.",
    "revenue_growth": 0.05,
    "terminal_growth": 0.02,
    "horizon_years": 5,
}


def freeze(doc, label):
    from compare import coerce_dcf_assumptions

    doc = deepcopy(doc)
    doc["valuation_date"] = FROZEN["valuation_date"]
    doc["market"]["price"] = FROZEN["price"]
    doc["market"]["price_as_of"] = FROZEN["valuation_date"]
    doc["market"]["diluted_shares"] = FROZEN["shares"]
    assumptions, _ = coerce_dcf_assumptions(doc, None, FROZEN["wacc"])
    assumptions = assumptions.__class__(
        **{
            **assumptions.__dict__,
            "revenue_growth_rates": [FROZEN["revenue_growth"]] * 5,
            "terminal_growth_rate": FROZEN["terminal_growth"],
        }
    )
    from app import evaluate

    result = evaluate(deepcopy(doc), assumptions)
    return doc, assumptions, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sec-doc", required=True)
    parser.add_argument("--yahoo-doc", required=True)
    parser.add_argument("--facts", default=None)
    args = parser.parse_args()

    from accounting_policy import apply_policy

    sec = json.load(open(args.sec_doc))["financials"]
    yahoo = json.load(open(args.yahoo_doc))["financials"]

    doc_a, assump_a, res_a = freeze(sec, "A")

    if args.facts:
        adjustments = json.load(open(args.facts))
    else:
        adjustments = {"facts": {}, "unavailable": []}
    doc_b_raw, ledger = apply_policy(deepcopy(sec), adjustments, "normalize")
    if doc_b_raw is None:
        raise SystemExit("No impairment facts: normalized basis unavailable.")
    doc_b, assump_b, res_b = freeze(doc_b_raw, "B")

    doc_c, assump_c, res_c = freeze(yahoo, "C")

    out = {
        "frozen": FROZEN,
        "bases": {},
        "bridge": {},
        "ledger": ledger,
    }
    for name, doc, assump, res in (
        ("A_reported_gaap", doc_a, assump_a, res_a),
        ("B_normalized_operating", doc_b, assump_b, res_b),
        ("C_provider_yahoo", doc_c, assump_c, res_c),
    ):
        out["bases"][name] = {
            "historical": [
                {
                    k: row.get(k)
                    for k in (
                        "period_end",
                        "revenue",
                        "ebit",
                        "net_income",
                        "d_and_a",
                        "capex",
                        "nwc",
                    )
                }
                for row in doc["historical"]
            ],
            "assumption_means": {
                "ebit_margin": sum(assump.ebit_margins) / 5,
                "da_margin": sum(assump.da_margins) / 5,
            },
            "forecast": [
                {k: row[k] for k in ("Year", "Revenue", "EBIT", "NOPAT", "D&A", "UFCF")}
                for row in res["projections"]
            ],
            "terminal_value": res["terminal_value"],
            "terminal_flow": res["terminal_fcff"],
            "enterprise_value": res["enterprise_value"],
            "equity_value": res["equity_value"],
            "intrinsic_value": res["intrinsic_value"],
            "target_price_12m": res["target_price_12m"],
        }
    out["bridge"] = {
        "A_to_B_normalization_effect": res_b["intrinsic_value"] - res_a["intrinsic_value"],
        "A_to_C_provider_convention_effect": res_c["intrinsic_value"]
        - res_a["intrinsic_value"],
        "note": "Single-factor sequential bridge from A with a defined order "
        "(impairment normalization, then provider conventions); interaction "
        "between EBIT and D&A conventions lives inside the A_to_C leg.",
    }
    root = Path(__file__).resolve().parent.parent
    (root / "docs" / "pep-three-bases.json").write_text(json.dumps(out, indent=1) + "\n")

    lines = [
        "# PEP three-basis valuation (frozen inputs, 2026-10-14)",
        "",
        f"Frozen: price ${FROZEN['price']:.2f} ({FROZEN['price_note']})",
        f"shares {FROZEN['shares']:,.0f}; WACC {FROZEN['wacc']:.4f} ({FROZEN['wacc_note']})",
        "growth 5%, terminal 2%, 5-year horizon. None of these is a true price:",
        "each is the model output of a stated accounting convention.",
        "",
        "| Basis | EBIT convention | D&A convention | Intrinsic | 12m target |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, label, ebit, dna in (
        ("A_reported_gaap", "A reported-GAAP", "GAAP operating profit", "ordinary cash-flow D&A"),
        ("B_normalized_operating", "B normalized", "pre-impairment (add-back, flagged)", "ordinary cash-flow D&A"),
        ("C_provider_yahoo", "C provider", "Yahoo ex-impairment OperatingIncome", "Yahoo incl. operating-lease ROU amortization"),
    ):
        b = out["bases"][name]
        lines.append(
            f"| {label} | {ebit} | {dna} | ${b['intrinsic_value']:,.2f} | ${b['target_price_12m']:,.2f} |"
        )
    lines += [
        "",
        f"A→B normalization effect: ${out['bridge']['A_to_B_normalization_effect']:+,.2f}/share.",
        f"A→C provider-convention effect: ${out['bridge']['A_to_C_provider_convention_effect']:+,.2f}/share.",
        "",
        "## Historical inputs (USD)",
        "",
    ]
    for name in ("A_reported_gaap", "B_normalized_operating", "C_provider_yahoo"):
        lines.append(f"### {name}")
        for row in out["bases"][name]["historical"]:
            lines.append(
                f"- {row['period_end']}: revenue ${row['revenue']:,.0f}, EBIT ${row['ebit']:,.0f}, "
                f"net ${row['net_income']:,.0f}, D&A ${row['d_and_a']:,.0f}, capex ${row['capex']:,.0f}"
            )
    lines += ["", "## Adjustment ledger (B only)", ""]
    for adj in ledger["adjustments"]:
        ev = ", ".join(f"{e['tag']} {e['accession']}" for e in adj["evidence"])
        lines.append(
            f"- {adj['period_end']}: +${adj['amount']:,.0f} impairment add-back ({ev})"
        )
    lines += ["", ledger["recurrence_note"], "", ledger.get("tax_note", ""), ""]
    (root / "docs" / "pep-three-bases.md").write_text("\n".join(lines))
    for name in ("A_reported_gaap", "B_normalized_operating", "C_provider_yahoo"):
        print(name, round(out["bases"][name]["intrinsic_value"], 2))
    print("bridge A->B", round(out["bridge"]["A_to_B_normalization_effect"], 2))
    print("bridge A->C", round(out["bridge"]["A_to_C_provider_convention_effect"], 2))


if __name__ == "__main__":
    main()
