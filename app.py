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
from pathlib import Path
from flask import Flask, Response, jsonify, render_template, request
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

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1_000_000
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


def default_form(doc):
    d = deepcopy(doc)
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
        "wacc": (d["source"].get("capital_costs", {}).get("wacc") or 0.065) * 100,
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
    valid = all(r.get("revenue") not in {None, 0} for r in d["historical"])
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
                value = sum(r[history] / r["revenue"] for r in d["historical"]) / 3
        for i in range(5):
            form[f"{key}_{i}"] = (
                value if key == "growth" or value is None else round(value * 100, 6)
            )
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
    a = {
        "revenue_growth_rates": [
            number(form.get(f"growth_{i}"), f"Year {i + 1} growth") / 100 for i in range(5)
        ],
        "terminal_growth_rate": number(form.get("terminal_growth"), "Terminal growth") / 100,
        "wacc_override": number(form.get("wacc"), "WACC") / 100,
        "terminal_mode": form.get("terminal_mode", "template"),
    }
    for key, name in DRIVERS.items():
        if key != "growth":
            a[name] = [
                number(form.get(f"{key}_{i}"), f"{DRIVER_LABELS[key]} year {i + 1}") / 100
                for i in range(5)
            ]
    if a["terminal_mode"] == "normalized":
        a["terminal_roic"] = number(form.get("terminal_roic"), "Terminal ROIC") / 100
    for k in FUTURE_LABELS:
        value = form.get(k)
        if value not in {"", None}:
            a[k] = number(value, FUTURE_LABELS[k], 0)
    return doc, assumptions_from_json(a)


def evaluate(doc, a):
    d = parse_document(doc)
    model = DCFModel(d, a)
    result = model.calculate()
    result["method"] = "dcf"
    result["model_version"] = "cuig-dcf-v1"
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
        return raw["financials"], assumptions_from_json(raw.get("assumptions"))
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
    else:
        response = jsonify(error=message)
        response.status_code = 429
    response.headers["Retry-After"] = "60"
    return response


@app.before_request
def limit_expensive_work():
    if app.config.get("CLOUDFLARE"):
        import hashlib
        import hmac
        import time
        from pyodide.ffi import run_sync

        env = request.environ["workers.env"]
        ip = request.headers.get("CF-Connecting-IP", "unknown")
        client_hash = hmac.new(
            str(env.RECORD_SALT).encode(),
            f"{datetime.now(timezone.utc).date()}:{ip}".encode(),
            hashlib.sha256,
        ).hexdigest()
        request.environ["dcf.client_hash"] = client_hash
        if request.method == "POST":
            now = int(time.time())
            key = f"{client_hash}:{now // 60}"
            row = run_sync(
                env.DB.prepare(
                    "INSERT INTO request_limits(key,count,reset) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count"
                )
                .bind(key, now + 120)
                .first()
            )
            if row.count > 10:
                return rate_limit_response()
            run_sync(env.DB.prepare("DELETE FROM request_limits WHERE reset<?").bind(now).run())
        return None
    if request.method == "POST" and (
        request.path in {"/", "/ddm", "/relative"}
        or request.path.startswith(("/api/financials", "/api/load/", "/api/calculate", "/export/"))
    ):
        if not Store(app.config.get("STATE_PATH")).allow(
            f"{request.remote_addr}:{request.path}", maximum=10
        ):
            return rate_limit_response()


@app.after_request
def security_headers(response):
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        }
    )
    if request.path.startswith(("/api/", "/export/")) or request.method == "POST":
        response.headers["Cache-Control"] = "no-store"
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
        return render_inputs()
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


@app.post("/api/calculate")
def calculate_api():
    try:
        doc, a = payload()
        r = evaluate(doc, a)
        r["saved_record_id"] = save_valuation(doc, a, r)
        return jsonify(r)
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.get("/api/references/<ticker>")
def analyst_references_api(ticker):
    try:
        from decision_support import load_analysts
        return jsonify(load_analysts(ticker))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except ProviderError as exc:
        return jsonify(error=str(exc)), 503


@app.post("/api/load/<method>")
def load_company_api(method):
    try:
        from auto_loading import load_method

        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            raise ValueError("Send a ticker and valuation date in a JSON object.")
        return jsonify(
            load_method(
                method,
                raw.get("ticker"),
                raw.get("valuation_date"),
                raw.get("equity_risk_premium", 0.05),
                raw.get("credit_spread", 0.015),
            )
        )
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
            a = assumptions_from_json(raw.get("assumptions"))
        result = evaluate(doc, a)
        if format == "json":
            body = json.dumps(
                {"financials": doc, "assumptions": asdict(a), "result": result},
                indent=2,
                allow_nan=False,
            )
            mime = "application/json"
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
            return jsonify(error="Choose json or csv export."), 400
        return Response(
            body,
            mimetype=mime,
            headers={
                "Content-Disposition": f'attachment; filename="{doc["company"]["ticker"]}-dcf.{format}"'
            },
        )
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400


@app.get("/health")
def health():
    return jsonify(status="healthy", model="cuig-dcf-v1")


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
            zion_configured=bool(os.getenv("ZION_API_BASE_URL")),
            custom_api_configured=bool(os.getenv("DCF_API_BASE_URL")),
        )
    except Exception:
        return jsonify(status="unavailable"), 503


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


@app.get("/static/<path:filename>", endpoint="edge_static")
def edge_static(filename):
    if not app.config.get("CLOUDFLARE"):
        return app.send_static_file(filename)
    from embedded_assets import ASSETS
    import mimetypes

    key = f"static/{filename}"
    if key not in ASSETS:
        return "Not found", 404
    return Response(ASSETS[key], mimetype=mimetypes.guess_type(filename)[0] or "text/plain")


app.view_functions["static"] = edge_static


from suite_views import register_suite

register_suite(app)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
