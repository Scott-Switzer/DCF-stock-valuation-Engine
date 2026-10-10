"""Football-field comparison: DCF, DDM and relative targets side by side.

Loads one DCF snapshot per ticker, then derives the DDM and relative
documents from that snapshot so all three methods share identical market
inputs. Methods that cannot be computed (no dividends, no peers) are
reported as unavailable with the underlying reason instead of failing
the whole page.
"""

from copy import deepcopy
from dataclasses import asdict

from dcf_code import DCFAssumptions
from dcf_loader import ProviderError, ticker_symbol
from readiness import method_readiness, reliable_peers
from residual_income import residual_income_value
from suite_views import suite_assumptions, suite_evaluate


def baseline_dcf_assumptions(doc, wacc):
    rows = doc["historical"]

    def average(key):
        values = [r[key] / r["revenue"] for r in rows]
        return sum(values) / len(values)

    return DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=wacc,
        terminal_mode="template",
        ebit_margins=[average("ebit")] * 5,
        da_margins=[average("d_and_a")] * 5,
        capex_margins=[average("capex")] * 5,
        nwc_margins=[average("nwc")] * 5,
        tax_rates=[rows[-1]["tax_rate"]] * 5,
        net_income_margins=[average("net_income")] * 5,
        book_value_margins=[average("book_value")] * 5,
    )


def coerce_dcf_assumptions(doc, raw, wacc):
    """Validate user-supplied DCF assumptions; fall back to baselines."""
    from app import assumptions_from_json

    if not isinstance(raw, dict) or not raw:
        return baseline_dcf_assumptions(doc, wacc), False
    merged = asdict(baseline_dcf_assumptions(doc, wacc))
    merged.update({k: v for k, v in raw.items() if v is not None})
    return assumptions_from_json(merged), True


def scenario_band(doc, base, delta):
    """Bear/base/bull variant: shift growth and EBIT margins together."""
    from dataclasses import replace

    return replace(
        base,
        revenue_growth_rates=[g + delta for g in base.revenue_growth_rates],
        ebit_margins=[m + delta for m in base.ebit_margins],
    )


def football_field(ticker, asof=None, dcf_assumptions=None, snapshot=None, http=None):
    """Compare lanes for one ticker.

    ``snapshot`` is an optional dcf-financials-v1 document, such as the
    workspace's loaded financials. It is validated and reused without a
    provider load; DDM and relative lanes derive from the same document.
    """
    from auto_loading import load_method
    from app import evaluate
    from dcf_loader import parse_document

    symbol = ticker_symbol(ticker)
    if snapshot is not None:
        parse_document(snapshot, minority_may_be_negative=True)
        if snapshot["company"]["ticker"] != symbol:
            raise ValueError("Workspace snapshot ticker does not match.")
    dcf_kwargs = {"http": http}
    if snapshot is not None:
        dcf_kwargs["snapshot"] = snapshot
    bundle = load_method("dcf", symbol, asof, **dcf_kwargs)
    doc = bundle["financials"]
    costs = bundle["load_summary"].get("capital_costs", {})
    wacc = costs.get("wacc") or 0.065
    dcf_assumptions, custom = coerce_dcf_assumptions(doc, dcf_assumptions, wacc)
    lanes = []
    band_results = {}
    result = None
    try:
        result = evaluate(deepcopy(doc), deepcopy(dcf_assumptions))
        for name, delta in [("Bear", -0.02), ("Base", 0.0), ("Bull", 0.02)]:
            try:
                band_results[name] = evaluate(
                    deepcopy(doc), scenario_band(doc, deepcopy(dcf_assumptions), delta)
                )["target_price_12m"]
            except ValueError:
                band_results[name] = None
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF intrinsic (today)",
                "value": result["intrinsic_value"],
                "detail": f"WACC {result['wacc']:.1%}, g {result['terminal_growth']:.1%}",
                "warnings": result["warnings"][:2],
            }
        )
        lanes.append(
            {
                "method": "dcf",
                "label": "DCF 12-month target" + (" (your scenario)" if custom else ""),
                "value": result["target_price_12m"],
                "detail": "Scenario with year-one overrides",
                "warnings": [],
                "band": band_results,
            }
        )
    except ValueError as exc:
        lanes.append({"method": "dcf", "label": "DCF", "value": None,
                      "detail": str(exc), "warnings": []})
    try:
        ddm_bundle = load_method(
            "ddm", symbol, doc["valuation_date"], snapshot=doc, http=http
        )
        ddm_doc = ddm_bundle["financials"]
        ddm_a = suite_assumptions(
            "ddm",
            {
                "dividend_growth_rates": [0.05] * 5,
                "required_return": costs.get("cost_of_equity", 0.07),
                "terminal_growth_rate": 0.02,
            },
        )
        ddm_result = suite_evaluate("ddm", ddm_doc, ddm_a)
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM intrinsic (today)",
                "value": ddm_result["intrinsic_value"],
                "detail": "Common dividends only",
                "warnings": [],
            }
        )
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM 12-month (ex-div)",
                "value": ddm_result["target_price_12m"],
                "detail": "Excludes the first dividend",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError) as exc:
        lanes.append(
            {
                "method": "ddm",
                "label": "DDM",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    try:
        residual_readiness = method_readiness(doc)["residual"]
        if residual_readiness["state"] == "unavailable":
            raise ValueError(" ".join(residual_readiness["reasons"]))
        if result is None:
            raise ValueError("Residual income uses the DCF forecast, which is unavailable for this snapshot.")
        cost_of_equity = costs.get("cost_of_equity")
        if not isinstance(cost_of_equity, (int, float)):
            raise ValueError("Cost of equity is unavailable from the loaded capital-cost inputs.")
        dividend = (doc["source"].get("common_dividends") or {}).get("value")
        last_net_income = doc["historical"][-1]["net_income"]
        payout = 0.0
        if isinstance(dividend, (int, float)) and dividend > 0 and last_net_income > 0:
            payout = min(1.0, max(0.0, dividend / last_net_income))
        residual = residual_income_value(
            net_income=[row["Net Income"] for row in result["projections"]],
            opening_book=doc["historical"][-1]["book_value"],
            cost_of_equity=cost_of_equity,
            terminal_growth=dcf_assumptions.terminal_growth_rate,
            shares=doc["market"]["diluted_shares"],
            payout_ratio=payout,
        )
        lanes.append(
            {
                "method": "residual",
                "label": "Residual income (today)",
                "value": residual["intrinsic_value"],
                "detail": (
                    f"Cost of equity {cost_of_equity:.1%}, payout {payout:.0%}, "
                    "clean-surplus book"
                ),
                "warnings": residual["warnings"][:1],
            }
        )
    except (ValueError, KeyError, TypeError) as exc:
        lanes.append(
            {
                "method": "residual",
                "label": "Residual income",
                "value": None,
                "detail": str(exc),
                "warnings": [],
            }
        )
    rel_doc = None
    try:
        rel_bundle = load_method(
            "relative",
            symbol,
            doc["valuation_date"],
            snapshot=doc,
            forecast_assumptions=deepcopy(dcf_assumptions),
            http=http,
        )
        rel_doc = rel_bundle["financials"]
        # Financial firms and a negative noncontrolling interest block EV-based multiples only.
        ev_blocked = rel_doc["bridge"]["minority_interest"] < 0 or rel_doc["company"].get("is_financial") is True
        candidates = ["pe"] if ev_blocked else ["ev_revenue", "ev_ebitda", "pe"]
        # Unreviewed candidate peers never feed an automatic relative value.
        reviewed = reliable_peers(rel_doc["comparables"])
        included = [
            k
            for k in candidates
            if rel_doc["target"]["forward"][
                {"ev_revenue": "revenue", "ev_ebitda": "ebitda", "pe": "net_income"}[k]
            ]
            > 0
            and any(
                p["multiples"][k] is not None and p["multiples"][k] > 0 for p in reviewed
            )
        ]
        if not included:
            raise ValueError(
                "No reviewed peer multiples for this ticker. Loaded peers are unverified candidates "
                "unless confirmed on the relative page."
            )
        rel_result = suite_evaluate(
            "relative",
            dict(rel_doc, comparables=reviewed),
            suite_assumptions("relative", {"included_methods": included}),
        )
        lanes.append(
            {
                "method": "relative",
                "label": f"Relative 12-month ({len(included)} methods)",
                "value": rel_result["target_price_12m"],
                "detail": "Equal-weighted peer means",
                "warnings": [],
            }
        )
    except (ProviderError, ValueError, KeyError) as exc:
        lanes.append(
            {
                "method": "relative",
                "label": "Relative",
                "value": None,
                "detail": (str(exc) if isinstance(exc, (ProviderError, ValueError))
                             else "Peer snapshot was incomplete; reload the ticker."),
                "warnings": [],
            }
        )
    packet = _packet(
        doc, lanes, bundle, dcf_assumptions, custom, snapshot is not None, relative_doc=rel_doc
    )
    packet["drivers"] = driver_impacts(doc, dcf_assumptions)
    packet["method_notes"] = method_notes(doc, lanes)
    try:
        from reverse_dcf import solve

        packet["reverse"] = {
            "revenue_growth": solve(
                doc, deepcopy(dcf_assumptions), doc["market"]["price"],
                "revenue_growth",
            ),
            "ebit_margin": solve(
                doc, deepcopy(dcf_assumptions), doc["market"]["price"],
                "ebit_margin",
            ),
        }
    except ValueError as exc:
        packet["reverse"] = {"status": "unsolvable", "detail": str(exc)}
    return packet


def driver_impacts(doc, base):
    """One-at-a-time +1pt moves, ranked by per-share impact."""
    from dataclasses import replace
    from app import evaluate

    candidates = [
        ("Revenue growth (+1pt all years)",
         replace(base, revenue_growth_rates=[g + 0.01 for g in base.revenue_growth_rates])),
        ("EBIT margin (+1pt all years)",
         replace(base, ebit_margins=[m + 0.01 for m in base.ebit_margins])),
        ("WACC (+1pt)",
         replace(base, wacc_override=(base.wacc_override or 0.065) + 0.01)),
        ("Terminal growth (+1pt)",
         replace(base, terminal_growth_rate=base.terminal_growth_rate + 0.01)),
        ("Tax rate (+1pt all years)",
         replace(base, tax_rates=[t + 0.01 for t in base.tax_rates])),
    ]
    try:
        anchor = evaluate(deepcopy(doc), deepcopy(base))["intrinsic_value"]
    except ValueError:
        return []
    impacts = []
    for label, variant in candidates:
        try:
            moved = evaluate(deepcopy(doc), variant)["intrinsic_value"]
            impacts.append({"label": label, "delta": moved - anchor})
        except ValueError:
            continue
    impacts.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return impacts[:3]


def method_notes(doc, lanes):
    """Explain gaps between computed lanes and flag unsuitable methods."""
    notes = []
    by_label = {lane["label"]: lane["value"] for lane in lanes}
    dcf = by_label.get("DCF intrinsic (today)")
    ddm = by_label.get("DDM intrinsic (today)")
    if isinstance(dcf, (int, float)) and isinstance(ddm, (int, float)) and dcf:
        gap = (ddm - dcf) / abs(dcf)
        if abs(gap) > 0.25:
            notes.append(
                f"DDM sits {gap:+.0%} from DCF: dividends capture only part of "
                "the cash the firm generates. Trust DCF when retention funds "
                "growth; trust DDM when payouts are the sustainable distribution."
            )
    text = " ".join(
        str(doc["company"].get(k, "")) for k in ("sector", "industry", "security_type")
    ).lower()
    financial = any(
        t in text for t in ("bank", "insurance", "financial service", "reit")
    ) or doc["company"].get("is_financial") is True
    if financial:
        notes.append(
            "This looks like a financial or real-estate issuer: enterprise-value "
            "methods mislead here. Use equity multiples (P/E, P/B) on the "
            "relative page instead of DCF."
        )
    dividend = doc["source"].get("common_dividends", {})
    if (dividend.get("value") or 0) <= 0 and any(
        lane["method"] == "ddm" and lane["value"] is None for lane in lanes
    ):
        notes.append(
            "No verified common dividend in this snapshot, so DDM is parked. "
            "Use DCF or relative valuation for non-payers."
        )
    return notes


def _packet(doc, lanes, bundle, assumptions, custom, reused, relative_doc=None):
    """Response packet. ``assumptions`` are the effective values the lanes used."""
    values = [lane["value"] for lane in lanes
              if isinstance(lane["value"], (int, float))]
    peak = max(values + [doc["market"]["price"], 0.01])
    for lane in lanes:
        lane["share"] = lane["value"] / peak if isinstance(lane["value"], (int, float)) else 0
        if isinstance(lane["value"], (int, float)):
            lane["upside"] = lane["value"] / doc["market"]["price"] - 1
        else:
            lane["upside"] = None
    return {
        "custom": custom,
        "assumptions_source": "workspace" if custom else "baseline",
        "snapshot_reused": reused,
        "ticker": doc["company"]["ticker"],
        "company_name": doc["company"]["name"],
        "valuation_date": doc["valuation_date"],
        "market_price": doc["market"]["price"],
        "price_as_of": doc["market"]["price_as_of"],
        "source": doc["source"]["name"],
        "is_demo": doc["source"]["kind"] == "synthetic"
        or doc["source"].get("origin_kind") == "synthetic",
        "lanes": lanes,
        "readiness": method_readiness(doc, relative_doc=relative_doc),
        "load_summary": bundle["load_summary"],
        "assumptions": asdict(assumptions),
    }
