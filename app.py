"""Flask views and a stateless valuation API. Secrets stay in provider configuration."""

from copy import deepcopy
from dataclasses import asdict, fields, replace
from datetime import datetime, timezone
from functools import lru_cache
import csv
import io
import json
import logging
import math
import os
import re
import time
from pathlib import Path
from flask import Flask, Response, jsonify, redirect, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from dcf_code import DCFModel, DCFAssumptions, number
from dcf_loader import (
    BRIDGE_FIELDS,
    HISTORY_FIELDS,
    ProviderError,
    demo_document,
    iso_date,
    load_document,
    parse_document,
    ticker_symbol,
)
from storage import Store
from valuation_records import save_valuation
from xlsx_export import dcf_workbook
from compare import football_field
import library
from owner_benchmark_access import install_owner_benchmark_access, require_owner_benchmark_access

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1_000_000
install_owner_benchmark_access(app, lambda name: provider_value(name))
# Explicitly opt in only when the host controls the complete proxy chain.
proxy_hops = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))
if proxy_hops:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_hops, x_proto=proxy_hops)

DRIVERS = {
    "growth": "revenue_growth_rates",
    "ebit_margin": "ebit_margins",
    "da_margin": "da_margins",
    "capex_margin": "capex_margins",
    "nwc_margin": "nwc_margins",
    "tax_rate": "tax_rates",
    "net_income_margin": "net_income_margins",
    "book_value_margin": "book_value_margins",
}
DRIVER_LABELS = {
    "growth": "Revenue growth",
    "ebit_margin": "EBIT margin",
    "da_margin": "D&A / revenue",
    "capex_margin": "CapEx / revenue",
    "nwc_margin": "NWC / revenue",
    "tax_rate": "Effective tax rate",
    "net_income_margin": "Net income / revenue",
    "book_value_margin": "Book value / revenue",
}
HISTORY_LABELS = {
    "revenue": "Revenue",
    "ebit": "EBIT",
    "net_income": "Net income",
    "capex": "Capital expenditures",
    "d_and_a": "Depreciation & amortization",
    "nwc": "Operating net working capital",
    "book_value": "Book value",
    "tax_rate": "Effective tax rate (%)",
}
BRIDGE_LABELS = {
    "short_term_debt": "Short-term debt",
    "long_term_debt": "Long-term debt",
    "cash": "Cash & equivalents",
    "preferred_equity": "Preferred claims",
    "minority_interest": "Noncontrolling interests",
    "other_nonoperating_assets": "Other nonoperating assets",
}
FUTURE_LABELS = {
    "future_debt": "Total debt in 12 months",
    "future_cash": "Cash in 12 months",
    "future_shares": "Diluted shares in 12 months",
    "future_preferred": "Preferred claims in 12 months",
    "future_minority": "Noncontrolling interests in 12 months",
    "future_other_assets": "Other nonoperating assets in 12 months",
}


def validate_ticker(ticker):
    return ticker_symbol(ticker)


def validate_growth_rate(val, min_val=-0.5, max_val=1.0, default=None):
    return number(val, "Growth rate", min_val, max_val)


def assumptions_from_json(raw):
    if not isinstance(raw, dict):
        raise ValueError("Assumptions must be a JSON object.")
    allowed = {f.name for f in fields(DCFAssumptions)}
    if set(raw) - allowed:
        raise ValueError("Unknown assumption fields: " + ", ".join(sorted(set(raw) - allowed)))
    try:
        a = DCFAssumptions(**raw)
    except TypeError:
        raise ValueError("Provide five revenue growth rates and a terminal growth rate.") from None
    a.validate()
    return a


def effective_dcf_assumptions(doc, raw):
    """Resolve explicit recalculated mode consistently at every input boundary."""
    validated = assumptions_from_json(raw)
    if raw.get("wacc_mode") != "recalculated":
        return validated
    from compare import coerce_dcf_assumptions

    costs = (doc.get("source") or {}).get("capital_costs") or {}
    resolved, _ = coerce_dcf_assumptions(
        doc, raw, validated.wacc_override or costs.get("wacc") or 0.065, costs=costs
    )
    return resolved


def default_form(doc):
    d = deepcopy(doc)
    from compare import coerce_dcf_assumptions

    costs = (d.get("source") or {}).get("capital_costs") or {}
    try:
        baseline, _ = coerce_dcf_assumptions(d, None, costs.get("wacc") or 0.065, costs=costs)
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        baseline = None  # Partial/manual documents must remain editable.
    company = d["company"]
    market = d["market"]
    bridge = d["bridge"]
    form = {
        "base_document": json.dumps(d),
        "ticker": company["ticker"],
        "company_name": company.get("name", ""),
        "sector": company.get("sector", ""),
        "eligible": "yes" if company.get("eligible") else "",
        "valuation_date": d["valuation_date"],
        "price": market.get("price"),
        "price_as_of": market.get("price_as_of"),
        "diluted_shares": market.get("diluted_shares"),
        "shares_basis": market.get("shares_basis", ""),
        "bridge_as_of": bridge.get("as_of"),
        "mode": "sample" if d["source"]["kind"] == "synthetic" else "manual",
        "wacc": (baseline.wacc_override if baseline else costs.get("wacc") or 0.065) * 100,
        "wacc_mode": "recalculated",
        "shield_override": "",
        "terminal_growth": 2.0,
        "terminal_mode": "template",
        "terminal_roic": 10.0,
    }
    for k in BRIDGE_FIELDS:
        form[k] = bridge.get(k)
    for i, row in enumerate(d["historical"]):
        form[f"period_{i}"] = row["period_end"]
        for k in HISTORY_FIELDS:
            form[f"h_{k}_{i}"] = (
                None if row.get(k) is None else row[k] * (100 if k == "tax_rate" else 1)
            )
    valid = bool(d["historical"]) and all(r.get("revenue") not in {None, 0} for r in d["historical"])
    for key in DRIVERS:
        value = None
        if key == "growth":
            value = 5.0
        elif key == "tax_rate":
            value = d["historical"][-1].get("tax_rate")
        elif valid:
            history = {
                "ebit_margin": "ebit",
                "da_margin": "d_and_a",
                "capex_margin": "capex",
                "nwc_margin": "nwc",
                "net_income_margin": "net_income",
                "book_value_margin": "book_value",
            }[key]
            if all(r.get(history) is not None for r in d["historical"]):
                value = sum(r[history] / r["revenue"] for r in d["historical"]) / len(d["historical"])
        for i in range(5):
            form[f"{key}_{i}"] = (
                value if key == "growth" or value is None else value * 100
            )
    if baseline is not None:
        for key, field in DRIVERS.items():
            for i, value in enumerate(getattr(baseline, field)):
                form[f"{key}_{i}"] = value * 100
    for k in FUTURE_LABELS:
        form[k] = ""
    return form


def form_payload(form):
    try:
        doc = json.loads(form.get("base_document", "{}"))
    except (ValueError, TypeError):
        raise ValueError("Financial source document is invalid.") from None
    if not isinstance(doc, dict) or doc.get("schema_version") != "dcf-financials-v1":
        raise ValueError("Load a sample or a financial document first.")
    if (
        any(not isinstance(doc.get(k), dict) for k in ["company", "market", "bridge", "source"])
        or not isinstance(doc.get("historical"), list)
        or len(doc["historical"]) != 3
        or any(
            not isinstance(r, dict)
            or "period_end" not in r
            or not isinstance(r.get("provenance", {}), dict)
            for r in doc["historical"]
        )
    ):
        raise ValueError(
            "Financial document requires company, market, bridge, source and three fiscal records."
        )
    original = deepcopy(doc)
    doc["valuation_date"] = form.get("valuation_date")
    doc["company"].update(
        ticker=ticker_symbol(form.get("ticker")),
        name=form.get("company_name", "").strip(),
        sector=form.get("sector", ""),
        eligible=form.get("eligible") == "yes",
    )
    doc["market"].update(
        price=number(form.get("price"), "Current price", 0),
        price_as_of=form.get("price_as_of"),
        diluted_shares=number(form.get("diluted_shares"), "Diluted shares", 0),
        shares_basis=form.get("shares_basis", ""),
    )
    doc["bridge"].update({k: number(form.get(k), BRIDGE_LABELS[k], 0) for k in BRIDGE_FIELDS})
    doc["bridge"]["as_of"] = form.get("bridge_as_of")
    changes = []
    for i, row in enumerate(doc["historical"]):
        row["period_end"] = form.get(f"period_{i}")
        for k in HISTORY_FIELDS:
            val = number(form.get(f"h_{k}_{i}"), f"{row['period_end']} {k}") / (
                100 if k == "tax_rate" else 1
            )
            prior = original["historical"][i].get(k)
            if isinstance(prior, (int, float)) and math.isclose(
                val, prior, rel_tol=1e-14, abs_tol=0
            ):
                val = prior
            if val != prior:
                changes.append(f"{row['period_end']}: {k}")
                row.setdefault("provenance", {})[k] = {"source": "User override"}
            row[k] = val
        if row["period_end"] != original["historical"][i]["period_end"]:
            row["provenance"] = {}
            row["available_at"] = doc["valuation_date"]
            changes.append(f"Fiscal period {i + 1} changed manually")
    for section in ["company", "market", "bridge"]:
        for k, v in doc[section].items():
            if v != original[section].get(k):
                changes.append(f"{section}: {k}")
    doc["source"]["manual_overrides"] = changes
    if form.get("mode") == "manual":
        doc["source"].setdefault("origin_kind", doc["source"].get("kind"))
        doc["source"].update(
            kind="manual", name=form.get("source_name") or "User-entered financials"
        )
    elif doc["company"]["ticker"] != original["company"]["ticker"]:
        raise ValueError(
            "Load data for the new ticker or select manual mode. Financials cannot be reused for a different security."
        )
    form_wacc = number(form.get("wacc"), "WACC") / 100
    a = {
        "revenue_growth_rates": [
            number(form.get(f"growth_{i}"), f"Year {i + 1} growth") / 100 for i in range(5)
        ],
        "terminal_growth_rate": number(form.get("terminal_growth"), "Terminal growth") / 100,
        "wacc_override": form_wacc,
        "terminal_mode": form.get("terminal_mode", "template"),
    }
    base_costs = (original.get("source") or {}).get("capital_costs") or {}
    for key, name in DRIVERS.items():
        if key != "growth":
            a[name] = [
                number(form.get(f"{key}_{i}"), f"{DRIVER_LABELS[key]} year {i + 1}") / 100
                for i in range(5)
            ]
    # Preserve exact baseline floats through percent display/parse round trips.
    # Only numerically identical input text receives this restoration.
    from compare import baseline_dcf_assumptions
    try:
        baseline = baseline_dcf_assumptions(original, form_wacc)
        for key, field in DRIVERS.items():
            values = getattr(baseline, field)
            for i, value in enumerate(values):
                if number(form.get(f"{key}_{i}"), key) == value * 100:
                    a[field][i] = value
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        pass
    # WACC regime is an explicit user choice, never inferred: recalculated
    # recomputes the override from the frozen market inputs with the
    # selected shield (explicit shield override beats forecast tax); fixed
    # deliberately holds the entered WACC for sensitivity analysis.
    wacc_mode = (form.get("wacc_mode") or "recalculated").strip()
    if wacc_mode not in ("recalculated", "fixed"):
        raise ValueError("WACC mode must be recalculated or fixed.")
    a["wacc_mode"] = wacc_mode
    shield_raw = form.get("shield_override")
    shield_override = None
    if shield_raw not in ("", None):
        shield_override = number(shield_raw, "Interest tax shield rate (%)", 0, 100) / 100
    new_tax = a.get("tax_rates", [None])[0] if isinstance(a.get("tax_rates"), list) else None
    shield = shield_override if shield_override is not None else new_tax
    a["interest_tax_shield_rate"] = shield_override
    if wacc_mode == "recalculated":
        from compare import recalculated_wacc

        if not isinstance(shield, (int, float)):
            raise ValueError("A forecast tax rate is required to recalculate WACC.")
        try:
            recalc = recalculated_wacc(base_costs, shield)
            a["wacc_override"] = recalc
            changes.append(
                f"WACC recalculated {form_wacc:.2%} -> {recalc:.2%} with the "
                f"{shield:.2%} tax shield ({'explicit shield override' if shield_override is not None else 'coherent with forecast'}; recalculated mode)"
            )
        except ValueError:
            changes.append(
                "WACC held at the entered rate while forecast tax varies "
                "(cost components unavailable for recalculation)"
            )
    else:
        changes.append(
            f"WACC manually fixed at {form_wacc:.2%} while cash-flow taxes use "
            f"{shield:.2%} ({'explicit shield override' if shield_override is not None else 'coherent with forecast'}; fixed mode)"
            if isinstance(shield, (int, float))
            else f"WACC manually fixed at {form_wacc:.2%} (fixed mode)"
        )
    if a["terminal_mode"] == "normalized":
        a["terminal_roic"] = number(form.get("terminal_roic"), "Terminal ROIC") / 100
    for k in FUTURE_LABELS:
        value = form.get(k)
        if value not in {"", None}:
            a[k] = number(value, FUTURE_LABELS[k], 0)
    return doc, assumptions_from_json(a)


def evaluate(doc, a):
    from issuer_classification import financial_block_reason

    blocked = financial_block_reason(doc)
    if blocked:
        raise ValueError(blocked)
    d = parse_document(doc)
    model = DCFModel(d, a)
    result = model.calculate()
    result["method"] = "dcf"
    result["model_version"] = "cuig-dcf-v1"
    if isinstance(doc.get("source"), dict) and "bottom_up_capm" in doc["source"]:
        result["bottom_up_capm"] = deepcopy(doc["source"]["bottom_up_capm"])
    if isinstance(doc.get("source"), dict) and "benchmark_assumptions" in doc["source"]:
        result["benchmark_assumptions"] = deepcopy(doc["source"]["benchmark_assumptions"])
    growths, matrix = model.generate_sensitivity_table()
    result["sensitivity"] = {
        "growth_rates": growths,
        "rows": [{"wacc": w, "values": row} for w, row in matrix],
    }
    scenarios = []
    for name, delta in [("Bear", -0.02), ("Base", 0), ("Bull", 0.02)]:
        if not delta:
            scenarios.append(
                {
                    "name": name,
                    "intrinsic_value": result["intrinsic_value"],
                    "target_price_12m": result["target_price_12m"],
                }
            )
            continue
        margins = model.drivers["ebit"]
        forecast = replace(
            a,
            revenue_growth_rates=[g + delta for g in a.revenue_growth_rates],
            ebit_margins=[m + delta for m in margins],
            wacc_override=model.wacc - delta / 2,
        )
        try:
            r = DCFModel(deepcopy(d), forecast).calculate()
            scenarios.append(
                {
                    "name": name,
                    "intrinsic_value": r["intrinsic_value"],
                    "target_price_12m": r["target_price_12m"],
                }
            )
        except ValueError:
            scenarios.append({"name": name, "intrinsic_value": None, "target_price_12m": None})
    result["scenarios"] = scenarios
    result["current_price"] = d.stock_price
    result["upside"] = result["intrinsic_value"] / d.stock_price - 1
    result["upside_12m"] = result["target_price_12m"] / d.stock_price - 1
    result["assumptions"] = asdict(a)
    return result


def payload():
    if request.is_json:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a JSON object.")
        if "financials" not in raw:
            raise ValueError("Provide a financials document.")
        doc = deepcopy(raw['financials'])
        assumptions = raw.get('assumptions')
        if not isinstance(assumptions, dict):
            raise ValueError('Assumptions must be a JSON object.')
        assumptions = deepcopy(assumptions)
        if raw.get('benchmark_selections'):
            from valuation_benchmarks import apply_benchmarks
            selected = resolve_benchmark_selections(raw['benchmark_selections'], doc['valuation_date'])
            if 'wacc_override' in selected and assumptions.get('wacc_mode') == 'recalculated':
                raise ValueError('Choose benchmark WACC or recalculated WACC, not both.')
            assumptions = apply_benchmarks(assumptions, selected)
            doc['source']['benchmark_assumptions'] = assumptions.pop('benchmark_sources')
        if raw.get('bottom_up_beta'):
            if (isinstance(raw['bottom_up_beta'], dict)
                    and raw['bottom_up_beta'].get('propagate_to_wacc') is True
                    and assumptions.get('wacc_mode') == 'recalculated'):
                raise ValueError('Choose bottom-up CAPM WACC or recalculated WACC, not both.')
            capm_res = resolve_bottom_up_beta_payload(raw['bottom_up_beta'], doc, assumptions)
            doc['source']['bottom_up_capm'] = capm_res
        return doc, effective_dcf_assumptions(doc, assumptions)
    return form_payload(request.form)


def rate_limit_response():
    message = "Too many requests. Try again in one minute."
    if request.path in {"/ddm", "/relative"} and not request.is_json:
        from suite_views import TITLES, CLAIMS, MULTIPLES

        method = request.path[1:]
        response = app.make_response(
            (
                render_template(
                    "suite_form.html",
                    method=method,
                    title=TITLES[method],
                    form=dict(request.form),
                    error=message,
                    multiples=MULTIPLES,
                    claims=CLAIMS,
                ),
                429,
            )
        )
    elif request.path == "/" and not request.is_json:
        response = app.make_response(render_inputs(dict(request.form), message, 429))
    elif request.path == "/compare" and not request.is_json:
        response = app.make_response(
            (
                render_template(
                    "compare.html",
                    ticker=dict(request.form).get("ticker", ""),
                    packet=None,
                    history=[],
                    error=message,
                ),
                429,
            )
        )
    else:
        response = jsonify(error=message)
        response.status_code = 429
    response.headers["Retry-After"] = "60"
    return response


@app.before_request
def assign_library_identity():
    from library import ensure_identity

    ensure_identity()


COOKIE_WRITE_PATHS = ("/api/research", "/api/templates", "/api/share", "/api/watchlist", "/api/account", "/account", "/api/equity-claims")


@app.before_request
def reject_cross_site_cookie_writes():
    """Defense in depth beside SameSite=Lax: cookie-bearing writes must be same-origin."""
    from library import same_origin_request

    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.path.startswith(
        COOKIE_WRITE_PATHS
    ):
        if not same_origin_request():
            return jsonify(error="Cross-site writes are not allowed."), 403
    return None


@app.before_request
def limit_expensive_work():
    preview_request = request.method == "POST" and request.path.startswith("/api/preview/")
    mcp_request = request.method == "POST" and request.path == "/mcp"
    mutation = request.method in {"POST", "PUT", "PATCH", "DELETE"}
    reference_request = request.method == "GET" and (
        request.path.startswith(("/api/references/", "/api/guidance/", "/api/company/", "/api/providers", "/api/diag/", "/coverage/"))
        or (request.path.startswith("/research/") and request.path.endswith("/export/xlsx"))
    )
    if app.config.get("CLOUDFLARE"):
        import hashlib
        import hmac
        from pyodide.ffi import run_sync

        env = request.environ["workers.env"]
        ip = request.headers.get("CF-Connecting-IP", "unknown")
        client_hash = hmac.new(
            str(env.RECORD_SALT).encode(),
            f"{datetime.now(timezone.utc).date()}:{ip}".encode(),
            hashlib.sha256,
        ).hexdigest()
        request.environ["dcf.client_hash"] = client_hash
        if mutation or reference_request or mcp_request:
            # Edge-local abuse protection keeps interactive previews off D1.
            binding = (
                env.MCP_LIMIT
                if mcp_request
                else env.PREVIEW_LIMIT
                if preview_request
                else env.REFERENCE_LIMIT
                if reference_request
                else env.WRITE_LIMIT
            )
            from pyodide.ffi import to_js
            from js import Object

            result = run_sync(
                binding.limit(
                    to_js({"key": "dcf:" + client_hash}, dict_converter=Object.fromEntries)
                )
            )
            if not result.success:
                return rate_limit_response()
        return None
    if mcp_request:
        if not Store(app.config.get("STATE_PATH")).allow(
            f"{request.remote_addr}:mcp", maximum=60
        ):
            return rate_limit_response()
        return None
    if preview_request:
        if not Store(app.config.get("STATE_PATH")).allow(
            f"{request.remote_addr}:preview", maximum=120
        ):
            return rate_limit_response()
        return None
    if reference_request:
        if not Store(app.config.get("STATE_PATH")).allow(
            f"{request.remote_addr}:references", maximum=20
        ):
            return rate_limit_response()
        return None
    if request.path == "/watchlist" and request.method == "GET":
        if app.config.get("CLOUDFLARE"):
            from pyodide.ffi import run_sync, to_js
            from js import Object
            from library import caller_hash

            result = run_sync(
                request.environ["workers.env"].WRITE_LIMIT.limit(
                    to_js({"key": "dcf:" + caller_hash()}, dict_converter=Object.fromEntries)
                )
            )
            if not result.success:
                return rate_limit_response()
            return None
        from library import caller_hash

        if not Store(app.config.get("STATE_PATH")).allow(
            f"{caller_hash()}:watchlist", maximum=10
        ):
            return rate_limit_response()
        return None
    if request.method == "POST" and (
        request.path in {"/", "/ddm", "/relative", "/compare"}
        or request.path.startswith(
            (
                "/api/financials",
                "/api/load/",
                "/api/assemble/",
                "/api/peer",
                "/api/calculate",
                "/api/capm/",
                "/api/compare",
                "/api/reverse",
                "/mcp",
                "/api/share",
                "/api/templates",
                "/api/research",
                "/api/watchlist",
                "/api/account",
                "/account/",
                "/export/",
                "/api/equity-claims",
            )
        )
    ):
        if not Store(app.config.get("STATE_PATH")).allow(
            f"{request.remote_addr}:{request.path}", maximum=10
        ):
            return rate_limit_response()


@app.after_request
def security_headers(response):
    if request.path.startswith(("/api/research", "/research")):
        response.headers["Cache-Control"] = "private, no-store"
    # User-scope and bearer-token pages must never sit in edge cache.
    # Heuristic edge caching keys on URL alone: a cached Set-Cookie would
    # fixate one browser library identity onto other users, a cached
    # /watchlist page would leak one user's library, and a cached /v/<token>
    # page would stay accessible after the shared link is revoked.
    if request.path == "/" or request.path.startswith(
        ("/compare", "/watchlist", "/v/", "/providers", "/coverage/", "/account")
    ):
        response.headers["Cache-Control"] = "private, no-store"
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN" if request.args.get("embedded") == "1" else "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors "
            + ("'self'" if request.args.get("embedded") == "1" else "'none'")
            + "; base-uri 'self'; form-action 'self'",
        }
    )
    if (
        request.method == "GET"
        and response.status_code == 200
        and request.path.startswith(
            (
                "/api/sample",
                "/api/search",
                "/api/tickers",
                "/api/guidance/",
                "/api/references/",
                "/api/company/",
            )
        )
    ):
        # Public provider reference data is already TTL-cached server-side;
        # a short edge TTL absorbs repeat ticker lookups without stale risk.
        # /api/company packet bodies are digest-verified immutable objects;
        # the ticker pointer can lag a new release by at most the edge TTL.
        response.headers["Cache-Control"] = (
            "public, max-age=300, stale-while-revalidate=600"
        )
    elif request.path.startswith(("/api/", "/export/")) or request.method == "POST":
        response.headers["Cache-Control"] = "no-store"
    from library import persist_identity

    persist_identity(response)
    # Identity minting happens above, after the earlier header branches.
    # A response carrying Set-Cookie must never be publicly edge-cached:
    # a cached Set-Cookie would fixate one browser identity onto others.
    if "Set-Cookie" in response.headers and response.headers.get(
        "Cache-Control", ""
    ).startswith("public"):
        response.headers["Cache-Control"] = "private, no-store"
    return response


def live_form():
    doc = load_document("manual", "AAPL", datetime.now(timezone.utc).date().isoformat())
    doc["company"].update(ticker="", name="")
    form = default_form(doc)
    form.update(ticker="", mode="auto", equity_risk_premium=5, credit_spread=1.5)
    return form


def render_inputs(form=None, error=None, status=200):
    return render_template(
        "index.html",
        form=form or live_form(),
        error=error,
        history_fields=HISTORY_FIELDS,
        history_labels=HISTORY_LABELS,
        drivers=DRIVERS,
        driver_labels=DRIVER_LABELS,
        bridge_labels=BRIDGE_LABELS,
        future_labels=FUTURE_LABELS,
    ), status


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return (
            render_inputs()
            if request.args.get("embedded") == "1"
            else render_template("workspace.html")
        )
    try:
        doc, a = payload()
        r = evaluate(doc, a)
        r["saved_record_id"] = save_valuation(doc, a, r)
        return render_template(
            "result.html",
            r=r,
            doc=doc,
            payload_json=json.dumps({"financials": doc, "assumptions": asdict(a)}, allow_nan=False),
            history_fields=HISTORY_FIELDS,
            history_labels=HISTORY_LABELS,
            bridge_labels=BRIDGE_LABELS,
            form_json=json.dumps(dict(request.form)),
        )
    except ValueError as e:
        return render_inputs(dict(request.form), str(e), 400)
    except Exception:
        logger.error("Unexpected valuation failure", exc_info=True)
        return render_inputs(
            dict(request.form),
            "The valuation could not be completed. Please review the inputs.",
            500,
        )


@app.route("/compare", methods=["GET", "POST"])
def compare_methods():
    if request.method == "GET":
        return render_template(
            "compare.html", ticker="", packet=None, history=[], error=None
        )
    try:
        posted_assumptions = None
        if request.form.get("assumptions"):
            try:
                posted_assumptions = json.loads(request.form["assumptions"])
            except ValueError:
                raise ValueError("Workspace assumptions were invalid.") from None
        posted_snapshot = None
        if request.form.get("base_document"):
            try:
                posted_snapshot = json.loads(request.form["base_document"])
            except ValueError:
                raise ValueError("Workspace financial snapshot was invalid.") from None
        packet = football_field(
            (request.form.get("ticker") or "").strip(),
            datetime.now(timezone.utc).date().isoformat(),
            dcf_assumptions=posted_assumptions,
            snapshot=posted_snapshot,
        )
        market_share = packet["market_price"] / max(
            [lane["value"] for lane in packet["lanes"]
             if isinstance(lane["value"], (int, float))] + [packet["market_price"]]
        )
        return render_template(
            "compare.html",
            ticker=packet["ticker"],
            packet=packet,
            market_share=market_share,
            history=library.history(packet["ticker"], 10),
            error=None,
        )
    except (ValueError, ProviderError) as e:
        return render_template(
            "compare.html",
            ticker=(request.form.get("ticker") or "").strip().upper(),
            packet=None,
            history=[],
            error=str(e),
        ), 400 if isinstance(e, ValueError) else 503


BATCH_BUDGET_SECONDS = 20


@app.post("/api/compare/batch")
def compare_batch_api():
    """Football-field summaries for up to 8 tickers in one call."""
    from dcf_loader import ProviderError, ticker_symbol

    raw = request.get_json(silent=True)
    if not isinstance(raw, dict):
        return jsonify(error="Send a JSON object with a tickers array."), 400
    tickers = raw.get("tickers")
    if not isinstance(tickers, list) or not 1 <= len(tickers) <= 8:
        return jsonify(error="Send 1 to 8 tickers."), 400
    from dcf_loader import JsonHTTP

    asof = datetime.now(timezone.utc).date().isoformat()
    # One deadline for the whole batch: later tickers wait for budget, not for
    # every provider call. Repeated tickers reuse the first result.
    http = JsonHTTP(budget=BATCH_BUDGET_SECONDS)
    computed = {}
    results = []
    for entry in tickers:
        try:
            symbol = ticker_symbol(entry)
        except ValueError as e:
            results.append({"ticker": str(entry)[:12], "status": "error", "error": str(e)})
            continue
        if symbol in computed:
            results.append(dict(computed[symbol]))
            continue
        if http.expired():
            outcome = {
                "ticker": symbol,
                "status": "not_started",
                "error": "Not computed: the batch deadline was reached first.",
            }
        else:
            try:
                packet = football_field(symbol, asof, http=http)
            except (ProviderError, ValueError, KeyError) as e:
                status = "timed_out" if http.expired() else "error"
                outcome = {"ticker": symbol, "status": status, "error": str(e)}
            else:
                outcome = {
                    "ticker": packet["ticker"],
                    # A deadline hit inside this ticker leaves some lanes unavailable.
                    "status": "partial" if http.timed_out else "complete",
                    "company_name": packet.get("company_name"),
                    "market_price": packet.get("market_price"),
                    "lanes": [
                        {"label": lane["label"], "value": lane["value"],
                         "upside": lane.get("upside")}
                        for lane in packet["lanes"]
                    ],
                }
        computed[symbol] = outcome
        results.append(dict(outcome))
    return jsonify(asof=asof, results=results)


@app.post("/api/compare")
def compare_api():
    """Football field from the workspace's live snapshot and assumptions."""
    try:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a ticker and the workspace DCF assumptions.")
        packet = football_field(
            raw.get("ticker"),
            datetime.now(timezone.utc).date().isoformat(),
            dcf_assumptions=raw.get("assumptions"),
            snapshot=raw.get("snapshot"),
        )
        return jsonify(packet)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except ProviderError as e:
        return jsonify(error=str(e)), 503


@app.route("/mcp", methods=["GET", "POST", "DELETE"])
def mcp_endpoint():
    """Model Context Protocol endpoint (2026-07-28 stateless and 2025-06-18 legacy)."""
    from mcp import serve

    if request.method != "POST":
        response = jsonify(error="POST a JSON-RPC 2.0 message to use the MCP tools.")
        response.status_code = 405
        response.headers["Allow"] = "POST"
        return response
    raw = request.get_json(silent=True, force=True)
    if isinstance(raw, list):
        # JSON-RPC batches were removed in MCP 2025-06-18; reject explicitly.
        return jsonify(error="JSON-RPC batch requests are not supported."), 400
    headers = {k.lower(): v for k, v in request.headers.items()}
    allowed = (provider_value("MCP_ALLOWED_ORIGINS") or "").split(",")
    status, body = serve(
        raw,
        headers,
        origin=request.headers.get("Origin"),
        host_origin=request.host_url.rstrip("/"),
        allowed_origins=allowed,
    )
    if body is None:
        return ("", 202)
    response = jsonify(body)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/reverse")
def reverse_api():
    """Implied growth/margin for the market price, holding the rest fixed."""
    try:
        from reverse_dcf import solve

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send financials, assumptions and a market price.")
        doc, a = raw.get("financials"), assumptions_from_json(raw.get("assumptions"))
        from dcf_loader import parse_document

        parse_document(doc)
        price = raw.get("market_price")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError("A positive market price is required.") from None
        return jsonify(
            {
                "revenue_growth": solve(doc, a, price, "revenue_growth"),
                "ebit_margin": solve(doc, a, price, "ebit_margin"),
            }
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.post("/api/calculate")
def calculate_api():
    try:
        doc, a = payload()
        r = evaluate(doc, a)
        r["saved_record_id"] = save_valuation(doc, a, r)
        return jsonify(r)
    except ValueError as e:
        return jsonify(error=str(e)), 400


def resolve_benchmark_selections(selections, valuation_date, *, max_selections=4):
    """Resolve explicit benchmark selections through the canonical Zion interface
    ('source': 'zion', preferred when configured) or the standalone release loader
    ('source': 'release', the default — existing behavior is unchanged)."""
    require_owner_benchmark_access(provider_value)
    from valuation_benchmarks import load_benchmark
    if not isinstance(selections, dict) or not 1 <= len(selections) <= max_selections:
        raise ValueError(f'Select one to {max_selections} explicit benchmark inputs.')
    result = {}
    for target, selection in selections.items():
        if (not isinstance(selection, dict)
                or not {'release_id','subject','measure','mode'} <= set(selection)
                or not set(selection) <= {'release_id','subject','measure','mode','source','dataset_id'}):
            raise ValueError('Select exact release, subject, measure and current/historical mode.')
        mode = selection['mode']
        if mode not in {'current','historical'}:
            raise ValueError('Unknown benchmark selection mode.')
        if mode == 'current' and valuation_date != datetime.now(timezone.utc).date().isoformat():
            raise ValueError('Current benchmark selection cannot be backdated.')
        source = selection.get('source', 'release')
        if source == 'zion':
            from zion_benchmark_provider import fetch_benchmark_row
            from zion_equity_claims_service import (BENCHMARK_BINDING_NAME, BINDING_ORIGIN,
                                                    ServiceBindingHTTP, service_binding)
            base = provider_value('ZION_BENCHMARK_BASE_URL') or provider_value('ZION_HISTORY_BASE_URL')
            token = provider_value('ZION_BENCHMARK_TOKEN') or provider_value('ZION_HISTORY_TOKEN')
            binding = service_binding(BENCHMARK_BINDING_NAME)
            if binding is not None:
                # The benchmark Worker is a sibling in this account, and a Worker's subrequest
                # to another Worker's public hostname on the same zone is refused by the edge
                # with a plain-text `error code: 1042`. The binding is therefore the only
                # transport that reaches it; the bearer credential below is still the one the
                # private route verifies, and the host is ignored by the binding.
                http = ServiceBindingHTTP(binding)
                base = base or BINDING_ORIGIN
            else:
                import requests

                http = requests
            if not base or not token:
                raise ValueError('Zion benchmark provider is not configured in this runtime.')
            result[target] = fetch_benchmark_row(
                base=base, token=token, subject=selection['subject'],
                measure=selection['measure'], release_id=selection['release_id'],
                mode=mode, valuation_date=valuation_date, http=http,
                dataset_id=selection.get('dataset_id'))
        elif source == 'release':
            root = provider_value('DAMODARAN_RELEASE_ROOT')
            if not root:
                raise ValueError('Damodaran releases are not configured in this runtime.')
            try:
                result[target] = load_benchmark(root, selection['release_id'], selection['subject'], selection['measure'],
                                                as_of=valuation_date if mode == 'historical' else None)
            except (OSError, KeyError) as exc:
                raise ValueError('Selected benchmark release is unavailable.') from exc
        else:
            raise ValueError('Unknown benchmark source.')
    return result


def resolve_bottom_up_beta_payload(spec, doc, assumptions=None):
    """Resolve benchmark selections inside a bottom_up_beta specification, compute
    relevered beta, CAPM cost of equity, and optionally propagate WACC into assumptions."""
    from bottom_up_capm import compute_bottom_up_capm

    if not isinstance(spec, dict):
        raise ValueError("bottom_up_beta must be a JSON object.")
    val_date = doc.get("valuation_date") or datetime.now(timezone.utc).date().isoformat()
    selections_to_resolve = {}
    for key in (
        "beta_benchmark",
        "erp_benchmark",
        "crp_benchmark",
        "cash_benchmark",
        "cost_of_debt_benchmark",
        "tax_benchmark",
    ):
        val = spec.get(key)
        if isinstance(val, dict) and "value_decimal" not in val:
            selections_to_resolve[key] = val
    resolved = (
        resolve_benchmark_selections(selections_to_resolve, val_date, max_selections=6)
        if selections_to_resolve
        else {}
    )
    merged_spec = deepcopy(spec)
    if "tax_benchmark" in resolved:
        merged_spec["tax_benchmark"] = resolved["tax_benchmark"]
    capm_result = compute_bottom_up_capm(
        doc,
        merged_spec,
        beta_benchmark=resolved.get("beta_benchmark") or spec.get("beta_benchmark"),
        erp_benchmark=resolved.get("erp_benchmark") or spec.get("erp_benchmark"),
        crp_benchmark=resolved.get("crp_benchmark") or spec.get("crp_benchmark"),
        cash_benchmark=resolved.get("cash_benchmark") or spec.get("cash_benchmark"),
        cost_of_debt_benchmark=resolved.get("cost_of_debt_benchmark") or spec.get("cost_of_debt_benchmark"),
    )
    if spec.get("propagate_to_wacc") is True and isinstance(assumptions, dict):
        if assumptions.get("wacc_override") is not None:
            raise ValueError(
                "Conflicting explicit assumption: wacc_override is already set; "
                "cannot propagate bottom-up CAPM WACC simultaneously."
            )
        wacc_build = capm_result.get("wacc_build") or {}
        if wacc_build.get("wacc") is None:
            raise ValueError("Bottom-up WACC could not be computed for propagation.")
        assumptions["wacc_override"] = wacc_build["wacc"]
    return capm_result


@app.post("/api/capm/preview")
def capm_preview_api():
    """Preview bottom-up beta, CAPM cost of equity, and optional WACC build with lineage."""
    try:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict) or not isinstance(raw.get("financials"), dict):
            raise ValueError("Send financials and bottom_up_beta specification.")
        doc = deepcopy(raw["financials"])
        parse_document(doc)
        res = resolve_bottom_up_beta_payload(raw.get("bottom_up_beta"), doc)
        return jsonify(res)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.get('/api/assumptions/damodaran/<release>')
def damodaran_assumption_api(release):
    try:
        selected = resolve_benchmark_selections({'selected':{
            'release_id':release,'subject':request.args.get('subject'),'measure':request.args.get('measure'),
            'mode':request.args.get('mode','historical')}},
            request.args.get('as_of',datetime.now(timezone.utc).date().isoformat()))
        response = jsonify(selected['selected'])
        response.headers['Cache-Control'] = 'no-store'
        return response
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400


@app.post('/api/calculate/fcfe')
def calculate_fcfe_api():
    """Selectable FCFE equity valuation: equity cash flow discounted at the cost of equity.

    Shares the exact DCF forecast drivers with the FCFF lane; the value basis is
    equity, so no net-debt bridge is applied. Financing policy (net borrowing) is
    explicit and never inferred from history.
    """
    try:
        from fcfe_valuation import fcfe_value

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError('Send financials, assumptions and explicit FCFE inputs.')
        doc, a = payload()
        d = parse_document(doc, minority_may_be_negative=True)
        projections = DCFModel(d, a).forecast_cash_flows()
        costs = (doc.get('source') or {}).get('capital_costs') or {}
        ke = raw.get('cost_of_equity', costs.get('cost_of_equity'))
        result = fcfe_value(
            projections,
            cost_of_equity=ke,
            terminal_growth=a.terminal_growth_rate,
            shares=d.shares_outstanding,
            net_borrowing=raw.get('net_borrowing'),
            market_price=d.stock_price,
        )
        result['assumptions'] = asdict(a)
        result['cost_of_equity_source'] = (
            raw.get('cost_of_equity_source', 'explicit')
            if 'cost_of_equity' in raw
            else 'snapshot_capital_costs'
        )
        result['model_limitations'] = [
            'FCFE depends on an explicit financing policy; changing net borrowing changes equity value.',
            'The terminal value applies Gordon growth to final-year FCFE and is unstable near cost of equity.',
            'Equity value from FCFE is not comparable line-for-line with enterprise values from FCFF.',
        ]
        return jsonify(result)
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400


@app.post('/api/calculate/apv')
def calculate_apv_api():
    """Adjusted Present Value: unlevered firm value + PV(tax shields) - PV(distress costs).

    All financing assumptions are explicit. The shield discount convention is
    required because the risk of tax shields depends on the financing policy.
    Distress costs enter only through explicit scenarios; without them the result
    is labeled DISTRESS_EXCLUDED_BY_ASSUMPTION rather than implied complete.
    """
    try:
        from apv_valuation import apv_value

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError('Send financials, assumptions and explicit APV inputs.')
        doc, a = payload()
        d = parse_document(doc, minority_may_be_negative=True)
        projections = DCFModel(d, a).forecast_cash_flows()
        costs = (doc.get('source') or {}).get('capital_costs') or {}
        rho_u = raw.get('unlevered_cost_of_capital', costs.get('unlevered_cost_of_capital'))
        if rho_u is None:
            raise ValueError(
                'An explicit unlevered_cost_of_capital is required; APV never silently '
                'substitutes WACC for the unlevered discount rate.'
            )
        result = apv_value(
            projections,
            unlevered_cost_of_capital=rho_u,
            terminal_growth=a.terminal_growth_rate,
            tax_rate=(a.tax_rates or [d.effective_tax_rate[-1]])[-1],
            debt_schedule=raw.get('debt_schedule'),
            cost_of_debt=raw.get('cost_of_debt'),
            shield_discount_convention=raw.get('shield_discount_convention'),
            terminal_shield_policy=raw.get('terminal_shield_policy', 'debt_repaid'),
            distress_scenarios=raw.get('distress_scenarios'),
        )
        result['assumptions'] = asdict(a)
        result['model_limitations'] = [
            'APV values the operating firm (enterprise basis); the equity bridge is applied separately.',
            'Tax shields depend on the debt schedule and usable deductions; limited taxable income defers deductions.',
            'Distress costs require explicit scenarios; without them the APV is incomplete by assumption.',
        ]
        return jsonify(result)
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400


@app.post('/api/calculate/bank-excess-return')
def calculate_bank_excess_return_api():
    """Bank / financial-institution equity valuation via excess returns over book capital.

    Dedicated lane for financial firms: no FCFF/WACC enterprise machinery, no
    fabricated FDIC fields. Credit provisions enter only as explicit schedules;
    regulatory capital constraints and metadata are carried, never imputed.
    """
    try:
        from bank_excess_return import bank_excess_return_value

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict) or not isinstance(raw.get("financials"), dict):
            raise ValueError('Send financials and explicit bank excess-return inputs.')
        doc = deepcopy(raw["financials"])
        # Financial firms are this lane's domain: skip the FCFF operating gate
        # while keeping every structural, currency and provenance check.
        parse_document(doc, minority_may_be_negative=True, allow_financial=True)
        costs = (doc.get('source') or {}).get('capital_costs') or {}
        ke = raw.get('cost_of_equity', costs.get('cost_of_equity'))
        if ke is None:
            raise ValueError(
                'A cost of equity is required for equity excess returns; it is never '
                'substituted from WACC.'
            )
        result = bank_excess_return_value(
            raw.get('net_income'),
            opening_book=(raw.get('opening_book')
                          if raw.get('opening_book') is not None
                          else doc['historical'][-1]['book_value']),
            cost_of_equity=ke,
            terminal_growth=raw.get('terminal_growth', 0.02),
            shares=doc['market']['diluted_shares'],
            payout_ratio=raw.get('payout_ratio', 0.0),
            equity_basis=raw.get('equity_basis', 'TANGIBLE_COMMON'),
            intangible_assets=raw.get('intangible_assets'),
            credit_provision_drag=raw.get('credit_provision_drag'),
            minimum_retention=raw.get('minimum_retention'),
            regulatory_capital=raw.get('regulatory_capital'),
            allow_unsustainable_terminal_growth=raw.get('allow_unsustainable_terminal_growth', False),
        )
        result['cost_of_equity_source'] = (
            raw.get('cost_of_equity_source', 'explicit')
            if 'cost_of_equity' in raw
            else 'snapshot_capital_costs'
        )
        result['model_limitations'] = [
            'Equity excess returns require clean surplus and a positive tangible book base.',
            'Stock issuance, buybacks and preferred actions are outside the forecast horizon.',
            'FDIC provision-for-credit-losses data is unavailable in the verified pilot and is never imputed.',
        ]
        return jsonify(result)
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400


@app.post('/api/calculate/enterprise')
def calculate_enterprise_api():
    from enterprise_valuation import value_enterprise
    try:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError('Send financials, valuation_date and explicit assumptions.')
        selected = resolve_benchmark_selections(raw.get('benchmark_selections'), raw.get('valuation_date'))
        result = value_enterprise(raw['financials'], selected, raw['revenue_growth_rates'],
                                 raw['terminal_growth'], raw['terminal_roic'],
                                 valuation_date=raw['valuation_date'], suitable=raw.get('suitable'),
                                 evidence_secret=provider_value('ZION_HISTORY_TOKEN'))
        return jsonify(result)
    except (ValueError, KeyError, TypeError, ProviderError) as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/company/<ticker>")
def company_packet(ticker):
    """Public SEC-derived financial packet; no warehouse prices or raw objects."""
    from ppe_provider import load_packet

    try:
        packet = load_packet(ticker, request.args.get("as_of"))
        if packet is None:
            return jsonify(error="No published PPE valuation packet for this ticker."), 404
        return jsonify(packet)
    except (ProviderError, ValueError) as exc:
        return jsonify(error=str(exc)), 503 if isinstance(exc, ProviderError) else 400


def server_timing(started, stages=None):
    """Build a Server-Timing header from measured stages; bodies and cache policy are unchanged."""
    parts = [
        f"{name};dur={round(seconds * 1000, 1)}"
        for name, seconds in (stages or {}).items()
        if isinstance(seconds, (int, float))
    ]
    parts.append(f"flask;dur={round((time.monotonic() - started) * 1000, 1)}")
    return ", ".join(parts)


@app.post("/api/preview/<method>")
def preview_api(method):
    started = time.monotonic()
    if method not in {"dcf", "ddm", "relative"}:
        return jsonify(error="Unknown method."), 404
    try:
        from suite_views import suite_payload, suite_evaluate

        doc, a = payload() if method == "dcf" else suite_payload(method)
        result = evaluate(doc, a) if method == "dcf" else suite_evaluate(method, doc, a)
        result["input_financials"] = doc
        response = jsonify(result)
        response.headers["Server-Timing"] = server_timing(started)
        return response
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/assemble/<method>")
def assemble_api(method):
    try:
        from auto_loading import load_method

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict) or not isinstance(raw.get("financials"), dict):
            raise ValueError("Provide a loaded company snapshot.")
        doc = raw["financials"]
        parse_document(doc, minority_may_be_negative=method in {"ddm", "relative"})
        bundle = load_method(
            method,
            doc["company"]["ticker"],
            snapshot=doc,
            forecast_assumptions=assumptions_from_json(raw["assumptions"])
            if "assumptions" in raw
            else None,
        )
        # Same wire dedup as /api/load/<method>: financials travel once;
        # the browser rebuilds form.base_document from them at intake.
        if isinstance(bundle.get("form"), dict):
            bundle["form"].pop("base_document", None)
        return jsonify(bundle)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.post("/api/brief")
def brief_api():
    """Instant Investment Research Brief for an already-loaded snapshot.

    No provider calls: the snapshot's financials plus baseline (or posted)
    assumptions feed the same evaluate/reverse-DCF machinery as the
    workspace. Financial firms get a blocked brief with the reason."""
    started = time.monotonic()
    try:
        from brief import build_brief
        from compare import coerce_dcf_assumptions

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict) or not isinstance(raw.get("financials"), dict):
            raise ValueError("Provide a loaded company snapshot.")
        if "assumptions" in raw:
            coerce_dcf_assumptions(raw["financials"], raw["assumptions"], 0.065)
        response = jsonify(build_brief(raw["financials"], raw.get("assumptions")))
        response.headers["Server-Timing"] = server_timing(started)
        return response
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.post("/api/peer")
def peer_api():
    try:
        from auto_loading import relative_metrics
        from yahoo_provider import load_company_metrics
        from dcf_loader import JsonHTTP

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Provide a peer ticker.")
        symbol = ticker_symbol(raw.get("ticker"))
        asof = datetime.now(timezone.utc).date().isoformat()
        from ppe_provider import prefer_ppe

        http = JsonHTTP(budget=12)
        doc = prefer_ppe(load_company_metrics(symbol, asof, http), symbol, asof, deadline=http.deadline)
        return jsonify(
            ticker=symbol,
            name=doc["company"]["name"],
            as_of=doc["market"]["price_as_of"],
            available_at=asof,
            currency="USD",
            source=doc["source"]["name"],
            multiples=relative_metrics(doc),
            denominator_basis="latest_annual",
            financial_period_end=doc["historical"][-1]["period_end"],
            provenance={
                "financials": doc["historical"][-1],
                "bridge": doc["bridge"],
                "market": doc["market"],
                "common_book_equity": doc["source"]["common_book_equity"],
            },
        )
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/guidance/<ticker>")
def guidance_api(ticker):
    try:
        from guidance import load_guidance

        return jsonify(load_guidance(ticker))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/diag/concurrency")
def diag_concurrency_api():
    """Staging-only prototype: sequential vs overlapped provider I/O.

    Fetches three independent inputs (external market reference, the R2
    valuation pointer, the private packet service) once sequentially and once
    overlapped via a single asyncio.gather bridge, and reports both walls.
    Never enabled outside the staging environment; removed if unjustified.
    """
    try:
        from flask import current_app, has_request_context

        staging = (
            has_request_context()
            and current_app.config.get("CLOUDFLARE")
            and getattr(request.environ.get("workers.env"), "DEPLOY_ENVIRONMENT", "") == "staging"
        )
        if not staging:
            return jsonify(error="Diagnostics are staging-only."), 404
        import asyncio
        import time as _time
        from pyodide.ffi import run_sync
        from workers import fetch as js_fetch

        env = request.environ["workers.env"]

        async def one_external():
            response = await js_fetch(
                "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d",
                headers={"User-Agent": "staging-concurrency-probe"},
            )
            body = await response.text()
            return ("external", response.status, len(body))

        async def one_pointer():
            obj = await env.PPE_DATA.get("control/valuation/CURRENT.json")
            body = await obj.text()
            return ("r2_pointer", 200, len(body))

        async def one_service():
            from js import Request

            response = await env.ZION_VALUATIONS.fetch(
                Request.new("https://zion.internal/v1/valuation/company/PEP?as_of=2026-10-14")
            )
            body = await response.text()
            return ("service", response.status, len(body))

        async def overlapped():
            return await asyncio.gather(one_external(), one_pointer(), one_service())

        started = _time.monotonic()
        sequential = [run_sync(one_external()), run_sync(one_pointer()), run_sync(one_service())]
        sequential_ms = round((_time.monotonic() - started) * 1000, 1)
        started = _time.monotonic()
        try:
            concurrent = run_sync(overlapped())
        except Exception as exc:
            return jsonify(mode="concurrent_unsupported", detail=str(exc)[:200], sequential_ms=sequential_ms)
        concurrent_ms = round((_time.monotonic() - started) * 1000, 1)
        return jsonify(
            sequential_ms=sequential_ms,
            concurrent_ms=concurrent_ms,
            sequential=[{name: (status, size)} for name, status, size in sequential],
            concurrent=[{name: (status, size)} for name, status, size in concurrent],
        )
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/references/<ticker>")
def analyst_references_api(ticker):
    try:
        from decision_support import load_analysts

        return jsonify(load_analysts(ticker))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.get("/coverage/<ticker>")
def company_coverage_page(ticker):
    try:
        from company_packets import load_company_packet
        from financial_qa import QA_UNIVERSE
        return render_template("company_coverage.html", packet=load_company_packet(ticker), universe=QA_UNIVERSE)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/company/<ticker>/packet")
def company_packet_api(ticker):
    try:
        from company_packets import load_company_packet
        if set(request.args) - {"as_of"} or any(len(request.args.getlist(k)) != 1 for k in request.args):
            raise ValueError("Only one optional as_of date is supported.")
        response = jsonify(load_company_packet(ticker, request.args.get("as_of")))
        response.headers["Cache-Control"] = "no-store"
        return response
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


def _validated_tax_override(value):
    """Explicit forecast-tax override from API input: five rates in 0-1 or None."""
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or len(value) != 5
        or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 1 for v in value)
    ):
        raise ValueError("tax_override must be five rates between 0 and 1.")
    return [float(v) for v in value]


def _validated_tax_scenario(value):
    """Normalized tax scenario from API input: validated shape, labeled evidence."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("tax_scenario must be an object with rates and evidence.")
    rates = value.get("rates")
    if (
        not isinstance(rates, list)
        or len(rates) != 5
        or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 1 for v in rates)
    ):
        raise ValueError("tax_scenario.rates must be five rates between 0 and 1.")
    evidence = value.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("tax_scenario.evidence must be an object.")
    filing = evidence.get("filing")
    period = evidence.get("period_end")
    if not isinstance(filing, str) or not filing.strip() or not isinstance(period, str) or not period.strip():
        raise ValueError("tax_scenario.evidence needs a filing citation and period end.")
    for key, entry in evidence.items():
        if not isinstance(entry, (str, int, float, bool)) and entry is not None:
            raise ValueError("tax_scenario.evidence values must be JSON scalars.")
    return {"rates": [float(v) for v in rates], "evidence": dict(evidence)}


@app.post("/api/load/<method>")
def load_company_api(method):
    started = time.monotonic()
    try:
        from company_packets import load_cached_method as load_method

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a ticker and valuation date in a JSON object.")
        result = load_method(
            method,
            raw.get("ticker"),
            raw.get("valuation_date"),
            raw.get("equity_risk_premium", 0.05),
            raw.get("credit_spread", 0.015),
            tax_override=_validated_tax_override(raw.get("tax_override")),
            tax_scenario=_validated_tax_scenario(raw.get("tax_scenario")),
        )
        summary = result.get("load_summary", {})
        # The wire bundle carries financials once: drop the JSON-serialized
        # duplicate from the form. The browser reconstructs
        # form.base_document from financials before iframe/compare use.
        # Server caches, saved submissions and manual flows keep the field.
        if isinstance(result.get("form"), dict):
            result["form"].pop("base_document", None)
        # Stage durations describe a fresh build only; a HIT must not replay the original build's timings.
        built_now = summary.get("assembly_cache", {}).get("state") == "MISS"
        serializing = time.monotonic()
        response = jsonify(result)
        stages = summary.get("stage_seconds") if built_now else dict(summary.get("hit_breakdown") or {})
        if not built_now:
            stages["response_json"] = round(time.monotonic() - serializing, 4)
        response.headers["Server-Timing"] = server_timing(started, stages)
        return response
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except ProviderError as e:
        return jsonify(error=str(e)), 503


@app.post("/api/financials")
def financials_api():
    try:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a JSON object.")
        asof = raw.get("valuation_date", datetime.now(timezone.utc).date().isoformat())
        iso_date(asof, "Valuation date")
        if asof > datetime.now(timezone.utc).date().isoformat():
            raise ValueError("Valuation date cannot be in the future.")
        if raw.get("provider") in {"auto", "yahoo"}:
            from auto_loading import load_method

            return jsonify(load_method("dcf", raw.get("ticker"), asof))
        if raw.get("provider") == "zion_history":
            doc = load_document('zion_history', raw.get('ticker'), asof,
                                cik=raw.get('cik'), expected_release_id=raw.get('expected_release_id'))
        else:
            doc = load_document(raw.get("provider"), raw.get("ticker"), asof)
        return jsonify(financials=doc, form=default_form(doc))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except ProviderError as e:
        return jsonify(error=str(e)), 503


@lru_cache(maxsize=1)
def tickers():
    if app.config.get("CLOUDFLARE"):
        from embedded_assets import ASSETS

        text = ASSETS["static/js/tickers.js"]
    else:
        text = (Path(__file__).parent / "static/js/tickers.js").read_text()
    array = text[text.index("[") : text.rindex("]") + 1]
    array = re.sub(r"([,{]\s*)(s|n):", r'\1"\2":', array)
    array = re.sub(r",\s*]", "]", array)
    raw = json.loads(array)
    return [{"symbol": r["s"], "shortname": r["n"]} for r in raw]


@app.get("/api/search")
@app.get("/api/tickers")
def search():
    query = request.args.get("q", "").strip().upper()[:50]
    if not query:
        return jsonify([])
    try:
        limit = int(request.args.get("limit", "12"))
    except ValueError:
        return jsonify(error="Search limit must be an integer."), 400
    limit = max(1, min(20, limit))
    candidates = [r for r in tickers() if query in r["symbol"] or query in r["shortname"].upper()]
    candidates.sort(
        key=lambda r: (r["symbol"] != query, not r["symbol"].startswith(query), r["symbol"])
    )
    return jsonify(candidates[:limit])


@app.get("/api/sample")
def sample():
    return jsonify(demo_document())


@app.post("/export/<format>")
def export(format):
    try:
        if request.is_json:
            doc, a = payload()
        else:
            raw = json.loads(request.form.get("payload", "null"))
            if not isinstance(raw, dict):
                raise ValueError("Export requires a valuation payload.")
            doc = raw.get("financials")
            a = effective_dcf_assumptions(doc, raw.get("assumptions"))
        result = evaluate(doc, a)
        if format == "json":
            body = json.dumps(
                {"financials": doc, "assumptions": asdict(a), "result": result},
                indent=2,
                allow_nan=False,
            )
            mime = "application/json"
        elif format == "xlsx":
            body = dcf_workbook(doc, asdict(a), result)
            mime = (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        elif format == "csv":
            stream = io.StringIO()
            writer = csv.writer(stream)

            def safe(v):
                return (
                    "'" + v
                    if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r"))
                    else v
                )

            def row(values):
                writer.writerow([safe(v) for v in values])

            row(["DCF Valuation Engine", "CUIG convention", doc["source"]["name"]])
            row(["Valuation date", doc["valuation_date"]])
            row(
                ["Company", doc["company"]["name"], doc["company"]["ticker"], "USD, absolute units"]
            )
            row(["Source kind", doc["source"]["kind"]])
            row(["Price as of", doc["market"]["price_as_of"]])
            row(["Diluted shares basis", doc["market"].get("shares_basis")])
            for key in [
                "intrinsic_value",
                "target_price_12m",
                "wacc",
                "terminal_growth",
                "enterprise_value",
                "equity_value",
                "enterprise_value_12m",
                "equity_value_12m",
                "terminal_value_share",
            ]:
                row([key, result[key]])
            row([])
            row(["Historical"] + list(HISTORY_FIELDS))
            for h in doc["historical"]:
                row([h["period_end"]] + [h[k] for k in HISTORY_FIELDS])
            row([])
            row(["Current bridge"])
            for key in BRIDGE_FIELDS:
                row([key, doc["bridge"][key]])
            row([])
            row(["12-month bridge"])
            for key, val in result["future_bridge"].items():
                row([key, val])
            row([])
            row(["Assumptions (decimal rates)"])
            for key, val in asdict(a).items():
                row([key, json.dumps(val) if isinstance(val, list) else val])
            row([])
            keys = list(result["projections"][0])
            row(keys)
            for forecast in result["projections"]:
                row([forecast[k] for k in keys])
            row([])
            row(["Sensitivity WACC / terminal growth"] + result["sensitivity"]["growth_rates"])
            for sens in result["sensitivity"]["rows"]:
                row([sens["wacc"]] + ["N/A" if x is None else x for x in sens["values"]])
            row([])
            row(["Scenario", "Intrinsic value", "12-month target"])
            for s in result["scenarios"]:
                row([s["name"], s["intrinsic_value"], s["target_price_12m"]])
            row([])
            row(["Source provenance JSON", json.dumps(doc["source"])])
            for h in doc["historical"]:
                row([h["period_end"], "Fact provenance", json.dumps(h.get("provenance", {}))])
            for warning in result["warnings"] + doc["source"].get("warnings", []):
                row(["Assumption / limitation", warning])
            body = stream.getvalue()
            mime = "text/csv"
        else:
            return jsonify(error="Choose json, csv or xlsx export."), 400
        return Response(
            body,
            mimetype=mime,
            headers={
                "Content-Disposition": f'attachment; filename="{doc["company"]["ticker"]}-dcf.{format}"'
            },
        )
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400


@app.route("/api/templates", methods=["GET", "POST"])
def template_library():
    try:
        if request.method == "GET":
            return jsonify(library.list_templates(request.args.get("method")))
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a template name, method and assumptions.")
        identity = library.save_template(
            raw.get("name"), raw.get("method"), raw.get("assumptions")
        )
        return jsonify(id=identity)
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.delete("/api/templates/<identity>")
def delete_library_template(identity):
    library.delete_template(identity)
    return jsonify(deleted=True)


@app.get("/api/history")
def valuation_history():
    return jsonify(
        library.history(
            (request.args.get("ticker") or "").strip().upper() or None,
            request.args.get("limit", 20),
        )
    )


@app.post("/api/share")
def share_valuation():
    try:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a valuation id to share.")
        token = library.create_share(
            raw.get("valuation_id"), raw.get("expires_in_days")
        )
        return jsonify(token=token, url=f"/v/{token}")
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.get("/api/shares")
def list_shares_api():
    try:
        offset = int(request.args.get("offset", "0"))
        if not 0 <= offset <= 9223372036854775807:
            raise ValueError
    except ValueError:
        return jsonify(error="Share offset must be a nonnegative integer."), 400
    return jsonify(library.list_shares(offset))


@app.delete("/api/share/<token>")
def revoke_share_api(token):
    try:
        library.revoke_share(token)
        return jsonify(revoked=True)
    except ValueError as e:
        return jsonify(error=str(e)), 404


@app.get("/v/<token>")
def shared_view(token):
    bundle = library.shared_valuation(token)
    if bundle is None:
        return render_template(
            "compare.html",
            ticker="",
            packet=None,
            error="This shared link is unknown, expired or revoked.",
        ), 404
    doc, result = bundle["financials"], bundle["result"]
    result["saved_record_id"] = None
    payload = json.dumps(
        {"financials": doc, "assumptions": bundle["assumptions"]}, allow_nan=False
    )
    if result.get("method") == "relative":
        from suite_models import MULTIPLES
        from suite_views import CLAIMS

        return render_template(
            "suite_result.html",
            method="relative",
            title="Relative valuation",
            r=result,
            doc=doc,
            payload_json=payload,
            form_json="{}",
            multiples=MULTIPLES,
            claims=CLAIMS,
            shared=True,
        )
    if result.get("method") == "ddm":
        from suite_models import MULTIPLES
        from suite_views import CLAIMS

        return render_template(
            "suite_result.html",
            method="ddm",
            title="Dividend discount model",
            r=result,
            doc=doc,
            payload_json=payload,
            form_json="{}",
            multiples=MULTIPLES,
            claims=CLAIMS,
            shared=True,
        )
    return render_template(
        "result.html",
        r=result,
        doc=doc,
        payload_json=payload,
        history_fields=HISTORY_FIELDS,
        history_labels=HISTORY_LABELS,
        bridge_labels=BRIDGE_LABELS,
        form_json="{}",
        shared=True,
    )


@app.route("/api/watchlist", methods=["GET", "POST", "DELETE"])
def watchlist_api():
    try:
        if request.method == "GET":
            return jsonify(library.list_watch())
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a ticker, target and direction.")
        if request.method == "DELETE":
            library.remove_watch(raw.get("ticker"))
            return jsonify(deleted=True)
        symbol = library.set_watch(raw.get("ticker"), raw.get("target"), raw.get("direction"))
        return jsonify(ticker=symbol)
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.get("/watchlist")
def watchlist_page():
    return render_template("watchlist.html", states=library.check_watch())


@app.get("/health")
def health():
    release = {"commit": "local", "tracked_dirty": True}
    if app.config.get("CLOUDFLARE"):
        from embedded_assets import BUILD

        release = BUILD
    return jsonify(status="healthy", model="cuig-dcf-v1", release=release)


@app.get("/ready")
def ready():
    try:
        if app.config.get("CLOUDFLARE"):
            from pyodide.ffi import run_sync

            run_sync(
                request.environ["workers.env"].DB.prepare("SELECT id FROM valuations LIMIT 1").all()
            )
        else:
            Store(app.config.get("STATE_PATH"))
        parse_document(demo_document())
        return jsonify(
            status="ready",
            sample=True,
            sec_configured="@"
            in (
                str(getattr(request.environ.get("workers.env"), "EDGAR_IDENTITY", ""))
                if app.config.get("CLOUDFLARE")
                else os.getenv("EDGAR_IDENTITY", "")
            ),
            ppe_binding_configured=bool(
                getattr(request.environ.get("workers.env"), "PPE_DATA", None)
            )
            if app.config.get("CLOUDFLARE")
            else False,
            zion_valuation_configured=bool(getattr(request.environ.get("workers.env"), "ZION_VALUATIONS", None)),
            zion_configured=bool(provider_value("ZION_API_BASE_URL")),
            custom_api_configured=bool(provider_value("DCF_API_BASE_URL")),
        )
    except Exception:
        return jsonify(status="unavailable"), 503


def provider_value(name):
    """Server-side provider config that works locally and on Cloudflare."""
    if app.config.get("CLOUDFLARE"):
        try:
            from flask import has_request_context

            if has_request_context():
                return str(getattr(request.environ.get("workers.env"), name, ""))
        except Exception:
            pass
    return os.getenv(name, "")


@app.get("/api/providers")
def providers():
    """Public provider status: which adapters are configured, without secrets."""
    zion_base = provider_value("ZION_API_BASE_URL").rstrip("/")
    api_base = provider_value("DCF_API_BASE_URL").rstrip("/")
    return jsonify(
        providers={
            "zion_history": {
                "configured": bool(provider_value('ZION_HISTORY_TOKEN') and (
                    provider_value('ZION_HISTORY_BASE_URL')
                    or getattr(request.environ.get('workers.env'), 'ZION_FINANCIAL_QUERY', None))),
                "label": "Zion native SEC financial history",
                "kind": "private_financial_history",
                "note": "Explicit CIK and historical cutoff required; missing DCF fields remain incomplete.",
            },
            "zion_benchmarks": {
                "configured": bool(
                    (provider_value('ZION_BENCHMARK_BASE_URL') or provider_value('ZION_HISTORY_BASE_URL'))
                    and (provider_value('ZION_BENCHMARK_TOKEN') or provider_value('ZION_HISTORY_TOKEN'))
                ),
                "label": "Zion DDFI benchmark context",
                "kind": "private_benchmark_reference",
                "note": "Immutable industry/country benchmark reference estimates; explicit release pinning required; never substitutes for issuer facts.",
            },
            "auto": {"configured": True, "label": "Automatic company data"},
            "zion_valuation": {
                "configured": bool(getattr(request.environ.get("workers.env"), "ZION_VALUATIONS", None)),
                "label": "Zion compact valuation data",
                "kind": "private_service_binding",
                "note": "Published SEC financials from Cloudflare; per-field dates and fallbacks retained. Configuration does not certify ticker coverage or freshness.",
            },
            "sample": {"configured": True, "label": "Offline example"},
            "manual": {"configured": True, "label": "Manual financials"},
            "sec": {"configured": True, "label": "SEC company facts"},
            "zion": {
                "configured": bool(zion_base),
                "label": "Custom company API (Zion-compatible)",
                "kind": "custom_private_api",
                "note": (
                    "A private Zion-compatible company API. Not a public product: "
                    "configure ZION_API_BASE_URL as an HTTPS base URL plus optional "
                    "ZION_API_TOKEN on the server. Unconfigured deployments return HTTP 503."
                ),
            },
            "api": {
                "configured": bool(api_base),
                "label": "Configured financial API",
                "note": "Server-side DCF_API_BASE_URL plus optional DCF_API_TOKEN.",
            },
        }
    )


@app.get("/api/providers/datasets")
def dataset_status():
    from dataset_catalog import load_catalog
    response = jsonify(load_catalog())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/providers")
def providers_page():
    """Server-rendered provider status; no secrets are exposed."""
    from dataset_catalog import load_catalog
    return render_template(
        "providers.html",
        dataset_catalog=load_catalog(),
        zion_valuation_configured=bool(getattr(request.environ.get("workers.env"), "ZION_VALUATIONS", None)),
        zion_configured=bool(provider_value("ZION_API_BASE_URL")),
        custom_api_configured=bool(provider_value("DCF_API_BASE_URL")),
    )


@app.get("/.well-known/mcp.json")
def mcp_manifest():
    """MCP discovery manifest so LLM clients can find the tools endpoint."""
    from mcp import PROTOCOL_VERSION, SERVER_INFO, TOOLS

    return jsonify(
        name=SERVER_INFO["name"],
        version=SERVER_INFO["version"],
        protocolVersion=PROTOCOL_VERSION,
        endpoint="/mcp",
        transport="streamable-http",
        tools=TOOLS,
    )


def _account_form_or_json():
    if request.is_json:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    return request.form.to_dict()


def _account_action(action, *, html):
    """Shared signup/login/logout for JSON clients and the /account form."""
    import accounts

    if action == "password" and accounts.current_user() is None:
        message = "Sign in to change your password."
        if html:
            response = app.make_response((render_template("account.html", user=None, error=message), 401))
        else:
            response = jsonify(error=message)
            response.status_code = 401
        response.headers["Cache-Control"] = "private, no-store"
        return response

    anonymous = library.anonymous_hash()
    token = None
    email = None
    try:
        if action == "logout":
            accounts.end_session()
        elif action == "password":
            data = _account_form_or_json()
            accounts.change_password(
                accounts.current_user()["id"],
                data.get("current_password"),
                data.get("new_password"),
            )
        else:
            data = _account_form_or_json()
            if action == "signup":
                user_id, email = accounts.signup(data.get("email"), data.get("password"), anonymous)
            else:
                user_id, email = accounts.login(data.get("email"), data.get("password"), anonymous)
            token = accounts.start_session(user_id)
    except ValueError as exc:
        if html:
            response = app.make_response((
                render_template("account.html", user=accounts.current_user(), error=str(exc)),
                400,
            ))
        else:
            response = jsonify(error=str(exc))
            response.status_code = 400
        response.headers["Cache-Control"] = "private, no-store"
        return response
    if html:
        response = redirect("/account", code=303)
    elif action == "logout":
        response = jsonify(signed_in=False)
    elif action == "password":
        if html:
            response = redirect("/account", code=303)
        else:
            response = jsonify(changed=True, signed_in=True)
    else:
        response = jsonify(email=email, signed_in=True)
    if token:
        accounts.set_session_cookie(response, token)
    if action == "logout":
        accounts.clear_session_cookie(response)
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.get("/account")
def account_page():
    import accounts

    response = app.make_response(render_template("account.html", user=accounts.current_user(), error=None))
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.post("/account/signup")
def account_signup_form():
    return _account_action("signup", html=True)


@app.post("/account/login")
def account_login_form():
    return _account_action("login", html=True)


@app.post("/account/logout")
def account_logout_form():
    return _account_action("logout", html=True)


@app.post("/account/password")
def account_password_form():
    return _account_action("password", html=True)


@app.post("/api/account/password")
def account_password_api():
    return _account_action("password", html=False)


@app.post("/api/account/signup")
def account_signup_api():
    return _account_action("signup", html=False)


@app.post("/api/account/login")
def account_login_api():
    return _account_action("login", html=False)


@app.post("/api/account/logout")
def account_logout_api():
    return _account_action("logout", html=False)


@app.get("/api/account/me")
def account_me():
    import accounts

    user = accounts.current_user()
    if user is None:
        response = jsonify(error="Sign in to view your account.")
        response.status_code = 401
    else:
        response = jsonify(email=user["email"], created_at=user["created_at"])
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Input exceeds the 1 MB limit."), 413


@app.errorhandler(500)
def internal_error(_):
    return jsonify(error="The request could not be completed."), 500


@app.context_processor
def deployment_context():
    return {"public_storage": bool(app.config.get("CLOUDFLARE"))}


@app.get("/privacy")
def privacy():
    return render_template("privacy.html")


@lru_cache(maxsize=32)
def asset_version(filename):
    """Content fingerprints cache public code across requests without stale releases."""
    import hashlib

    if app.config.get("CLOUDFLARE"):
        from embedded_assets import ASSETS

        content = ASSETS.get("static/" + filename, "").encode()
    else:
        content = (Path(app.static_folder) / filename).read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


@app.url_defaults
def version_static_urls(endpoint, values):
    if endpoint in {"static", "edge_static"} and "filename" in values:
        values.setdefault("v", asset_version(values["filename"]))


@app.get("/static/<path:filename>", endpoint="edge_static")
def edge_static(filename):
    if not app.config.get("CLOUDFLARE"):
        return app.send_static_file(filename)
    from embedded_assets import ASSETS
    import mimetypes

    key = f"static/{filename}"
    if key not in ASSETS:
        return "Not found", 404
    response = Response(ASSETS[key], mimetype=mimetypes.guess_type(filename)[0] or "text/plain")
    response.headers["Cache-Control"] = (
        "public, max-age=31536000, immutable"
        if request.args.get("v") == asset_version(filename)
        else "no-cache"
    )
    return response


app.view_functions["static"] = edge_static


from suite_views import register_suite

register_suite(app)

from research import register_research

register_research(app)

from zion_equity_claims_service import register_equity_claims

register_equity_claims(app)


from research_screen import register_screen

register_screen(app)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
