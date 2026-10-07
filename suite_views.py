"""Method-specific pages and APIs; calculation engines have no Flask dependency."""

from copy import deepcopy
from dataclasses import asdict, fields
import csv
import io
import json
from flask import request, jsonify, render_template, Response
from dcf_code import number, DCFAssumptions
from dcf_loader import BRIDGE_FIELDS, ticker_symbol
from suite_models import (
    DDMAssumptions,
    DDMModel,
    RelativeAssumptions,
    RelativeModel,
    MULTIPLES,
    suite_sample,
    from_dcf_document,
)
from valuation_records import save_valuation
from xlsx_export import ddm_workbook, relative_workbook

TITLES = {"ddm": "Dividend discount model", "relative": "Relative valuation"}
CLAIMS = {
    "short_term_debt": "Short-term debt",
    "long_term_debt": "Long-term debt",
    "cash": "Cash & equivalents",
    "preferred_equity": "Preferred claims",
    "minority_interest": "Noncontrolling interests",
    "other_nonoperating_assets": "Other nonoperating assets",
}


def suite_assumptions(method, raw):
    cls = DDMAssumptions if method == "ddm" else RelativeAssumptions
    if not isinstance(raw, dict) or set(raw) - {f.name for f in fields(cls)}:
        raise ValueError("Provide a supported assumptions object for this method.")
    try:
        a = cls(**raw)
    except TypeError:
        raise ValueError("Missing required method assumptions.") from None
    a.validate()
    return a


def suite_form(method, doc=None):
    d = doc or suite_sample(method)
    if method == "relative" and len(d.get("comparables", [])) > 4:
        raise ValueError(
            "The browser supports four CUIG peer rows; use the JSON calculation API for larger peer sets."
        )
    f = {
        "base_document": json.dumps(d),
        "ticker": d["company"]["ticker"],
        "company_name": d["company"].get("name", ""),
        "sector": d["company"].get("sector", ""),
        "eligible": "yes" if d["company"].get("eligible") else "",
        "financial_company": "yes" if d["company"].get("is_financial") else "",
        "valuation_date": d["valuation_date"],
        "price": d["market"].get("price"),
        "price_as_of": d["market"].get("price_as_of"),
        "diluted_shares": d["market"].get("diluted_shares"),
        "shares_basis": d["market"].get("shares_basis", ""),
        "source_name": d["source"]["name"],
    }
    if method == "ddm":
        f.update(
            base_common_dividends=d.get("base_common_dividends"),
            dividend_as_of=d.get("dividend_as_of"),
            required_return=7,
            terminal_growth=2,
            future_shares="",
        )
        f.update({f"dividend_growth_{i}": 5 for i in range(5)})
    else:
        f["historical_as_of"] = d["target"]["historical_as_of"]
        f["bridge_as_of"] = d["bridge"]["as_of"]
        for key in BRIDGE_FIELDS:
            f[key] = d["bridge"].get(key)
        for period in ["historical", "forward"]:
            for _, metric in MULTIPLES.values():
                f[f"{period}_{metric}"] = d["target"][period].get(metric)
        for k in MULTIPLES:
            f[f"include_{k}"] = "yes" if k in ["ev_revenue", "ev_ebitda", "pe"] else ""
        for i in range(4):
            p = d["comparables"][i] if i < len(d["comparables"]) else {}
            for key in ["ticker", "name", "as_of", "source"]:
                f[f"peer_{key}_{i}"] = p.get(key, "")
            for key in MULTIPLES:
                f[f"peer_{key}_{i}"] = p.get("multiples", {}).get(key)
    return f


def suite_form_payload(method, form):
    try:
        doc = json.loads(form.get("base_document", "{}"))
    except (ValueError, TypeError):
        raise ValueError("Invalid source document.") from None
    if (
        not isinstance(doc, dict)
        or doc.get("schema_version") != f"{method}-financials-v1"
        or any(not isinstance(doc.get(k), dict) for k in ["company", "market", "source"])
    ):
        raise ValueError("Load this method’s sample or a matching financial document.")
    original = deepcopy(doc)
    if (
        doc["source"].get("kind") in ("api", "sec", "zion")
        or doc["source"].get("origin_kind") in ("api", "sec", "zion")
    ) and ticker_symbol(form.get("ticker")) != ticker_symbol(doc["company"].get("ticker")):
        raise ValueError(
            "Load data for the new ticker before calculating; financials cannot be reused for another security."
        )
    doc["valuation_date"] = form.get("valuation_date")
    doc["company"].update(
        ticker=ticker_symbol(form.get("ticker")),
        name=form.get("company_name", "").strip(),
        sector=form.get("sector", ""),
        eligible=form.get("eligible") == "yes",
    )
    if method == "relative" and (
        "is_financial" in doc["company"] or form.get("financial_company") == "yes"
    ):
        doc["company"]["is_financial"] = form.get("financial_company") == "yes"
    doc["market"].update(
        price=number(form.get("price"), "Market price", 0.000001),
        price_as_of=form.get("price_as_of"),
        diluted_shares=number(form.get("diluted_shares"), "Diluted shares", 0.000001),
        shares_basis=form.get("shares_basis", ""),
    )
    if method == "ddm":
        doc.update(
            base_common_dividends=number(
                form.get("base_common_dividends"), "Latest annual common dividends", 0.000001
            ),
            dividend_as_of=form.get("dividend_as_of"),
        )
        raw = {
            "dividend_growth_rates": [
                number(form.get(f"dividend_growth_{i}"), f"Year {i + 1} dividend growth") / 100
                for i in range(5)
            ],
            "required_return": number(form.get("required_return"), "Required return") / 100,
            "terminal_growth_rate": number(form.get("terminal_growth"), "Terminal growth") / 100,
        }
        if form.get("future_shares"):
            raw["future_shares"] = number(form["future_shares"], "Future diluted shares", 0.000001)
    else:
        doc["bridge"] = {k: number(form.get(k), label, 0) for k, label in CLAIMS.items()}
        doc["bridge"]["as_of"] = form.get("bridge_as_of")
        doc["target"] = {"historical_as_of": form.get("historical_as_of")}
        for period in ["historical", "forward"]:
            doc["target"][period] = {
                metric: None
                if form.get(f"{period}_{metric}") in {"", None}
                else number(form.get(f"{period}_{metric}"), f"{period} {metric}")
                for _, metric in MULTIPLES.values()
            }
        source_peers = original.get("comparables", [])
        if not isinstance(source_peers, list) or any(not isinstance(p, dict) for p in source_peers):
            raise ValueError("Each source peer must be a comparable record.")
        original_peers = {ticker_symbol(p.get("ticker")): p for p in source_peers}
        doc["comparables"] = []
        for i in range(4):
            if form.get("peer_selection") == "explicit" and form.get(f"peer_include_{i}") != "yes":
                continue
            ticker = form.get(f"peer_ticker_{i}", "").strip()
            values = {
                k: None
                if form.get(f"peer_{k}_{i}") in {"", None}
                else number(form.get(f"peer_{k}_{i}"), f"Peer {i + 1} {k}")
                for k in MULTIPLES
            }
            if not ticker and all(v is None for v in values.values()):
                continue
            doc["comparables"].append(
                {
                    **deepcopy(original_peers.get(ticker_symbol(ticker), {})),
                    "ticker": ticker_symbol(ticker),
                    "name": form.get(f"peer_name_{i}", ""),
                    "as_of": form.get(f"peer_as_of_{i}"),
                    "currency": "USD",
                    "source": form.get(f"peer_source_{i}", ""),
                    "multiples": values,
                }
            )
        raw = {"included_methods": [k for k in MULTIPLES if form.get(f"include_{k}") == "yes"]}
    if doc != original or form.get("source_name") != doc["source"]["name"]:
        doc["source"].setdefault("origin_kind", doc["source"]["kind"])
        doc["source"].update(
            kind="manual", name=form.get("source_name") or "User-entered financials"
        )
    return doc, suite_assumptions(method, raw)


def suite_payload(method):
    if request.is_json:
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict) or "financials" not in raw:
            raise ValueError("Send financials and assumptions in a JSON object.")
        return raw["financials"], suite_assumptions(method, raw.get("assumptions"))
    if request.form.get("suite_payload"):
        try:
            raw = json.loads(request.form["suite_payload"])
        except ValueError:
            raise ValueError("Invalid saved valuation payload.") from None
        if not isinstance(raw, dict) or "financials" not in raw:
            raise ValueError("Saved payload requires financials and assumptions.")
        return raw["financials"], suite_assumptions(method, raw.get("assumptions"))
    return suite_form_payload(method, request.form)


def suite_evaluate(method, doc, a):
    return (DDMModel if method == "ddm" else RelativeModel)(doc, a).calculate()


def register_suite(app):
    def page(method):
        if method not in TITLES:
            return "Not found", 404
        form = suite_form(method, suite_sample(method, blank=True))
        if request.method == "POST":
            try:
                doc, a = suite_payload(method)
                r = suite_evaluate(method, doc, a)
                r["saved_record_id"] = save_valuation(doc, a, r)
                return render_template(
                    "suite_result.html",
                    method=method,
                    title=TITLES[method],
                    r=r,
                    doc=doc,
                    payload_json=json.dumps(
                        {"financials": doc, "assumptions": asdict(a)}, allow_nan=False
                    ),
                    form_json=json.dumps(dict(request.form)),
                )
            except ValueError as e:
                return render_template(
                    "suite_form.html",
                    method=method,
                    title=TITLES[method],
                    form=dict(request.form),
                    error=str(e),
                    multiples=MULTIPLES,
                    claims=CLAIMS,
                ), 400
        return render_template(
            "suite_form.html",
            method=method,
            title=TITLES[method],
            form=form,
            multiples=MULTIPLES,
            claims=CLAIMS,
        )

    app.add_url_rule(
        "/<any(ddm,relative):method>",
        endpoint="suite_page",
        view_func=page,
        methods=["GET", "POST"],
    )

    def sample(method):
        if method not in TITLES:
            return jsonify(error="Unknown method."), 404
        doc = suite_sample(method, blank=request.args.get("blank") == "1")
        return jsonify(financials=doc, form=suite_form(method, doc))

    app.add_url_rule("/api/sample/<method>", endpoint="suite_sample", view_func=sample)

    def from_dcf(method):
        if method not in TITLES:
            return jsonify(error="Unknown method."), 404
        try:
            raw = request.get_json(silent=True)
            if not isinstance(raw, dict) or not isinstance(raw.get("assumptions"), dict):
                raise ValueError("Provide a complete DCF export.")
            try:
                a = DCFAssumptions(**raw["assumptions"])
            except TypeError:
                raise ValueError("Invalid DCF assumptions.") from None
            doc = from_dcf_document(method, raw.get("financials"), a)
            return jsonify(form=suite_form(method, doc))
        except ValueError as e:
            return jsonify(error=str(e)), 400

    app.add_url_rule(
        "/api/from-dcf/<method>", endpoint="suite_from_dcf", view_func=from_dcf, methods=["POST"]
    )

    def import_document(method):
        if method not in TITLES:
            return jsonify(error="Unknown method."), 404
        try:
            raw = request.get_json(silent=True)
            if not isinstance(raw, dict):
                raise ValueError("Import a JSON financial document or complete valuation export.")
            doc = raw.get("financials", raw)
            defaults = (
                {
                    "dividend_growth_rates": [0.05] * 5,
                    "required_return": 0.07,
                    "terminal_growth_rate": 0.02,
                }
                if method == "ddm"
                else {"included_methods": ["ev_revenue", "ev_ebitda", "pe"]}
            )
            a = suite_assumptions(method, raw.get("assumptions", defaults))
            suite_evaluate(method, doc, a)
            form = suite_form(method, doc)
            if method == "ddm":
                form.update(
                    required_return=a.required_return * 100,
                    terminal_growth=a.terminal_growth_rate * 100,
                    future_shares=a.future_shares or "",
                )
                form.update(
                    {f"dividend_growth_{i}": g * 100 for i, g in enumerate(a.dividend_growth_rates)}
                )
            else:
                form.update(
                    {f"include_{k}": "yes" if k in a.included_methods else "" for k in MULTIPLES}
                )
            return jsonify(form=form)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    app.add_url_rule(
        "/api/import/<method>", endpoint="suite_import", view_func=import_document, methods=["POST"]
    )

    def calculate(method):
        if method not in TITLES:
            return jsonify(error="Unknown method."), 404
        try:
            doc, a = suite_payload(method)
            r = suite_evaluate(method, doc, a)
            r["saved_record_id"] = save_valuation(doc, a, r)
            return jsonify(r)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    app.add_url_rule(
        "/api/calculate/<method>", endpoint="suite_calculate", view_func=calculate, methods=["POST"]
    )

    def export(method, format):
        if method not in TITLES:
            return jsonify(error="Unknown method."), 404
        try:
            doc, a = suite_payload(method)
            r = suite_evaluate(method, doc, a)
            if format == "json":
                body = json.dumps(
                    {"financials": doc, "assumptions": asdict(a), "result": r},
                    indent=2,
                    allow_nan=False,
                )
                mime = "application/json"
            elif format == "csv":
                stream = io.StringIO()
                writer = csv.writer(stream)

                def row(items):
                    writer.writerow(
                        [
                            ("'" + str(x))
                            if isinstance(x, str) and x.startswith(("=", "+", "-", "@", "\t", "\r"))
                            else x
                            for x in items
                        ]
                    )

                row(["Valuation method", method])
                row(["Ticker", doc["company"]["ticker"]])
                row(["Valuation date", doc["valuation_date"]])
                row(["Source", doc["source"]["name"]])
                row(["Intrinsic value today", r["intrinsic_value"]])
                row(["12-month target", r["target_price_12m"]])
                row(["Dated market price", r["current_price"]])
                row(["Financials JSON", json.dumps(doc, allow_nan=False)])
                row(["Assumptions JSON", json.dumps(asdict(a), allow_nan=False)])
                records = r["projections"] if method == "ddm" else r["multiples"]
                row(list(records[0]))
                for record in records:
                    row(list(record.values()))
                for w in r["warnings"] + doc["source"].get("warnings", []):
                    row(["Assumption / limitation", w])
                if method == "ddm":
                    row(["Terminal dividend value", r["terminal_value"]])
                    row(["Terminal PV today", r["pv_terminal"]])
                    row(["Terminal PV 12m", r["pv_terminal_12m"]])
                    row(["Ke / terminal growth", *r["sensitivity"]["growth_rates"]])
                    for sr in r["sensitivity"]["rows"]:
                        row([sr["rate"], *sr["values"]])
                body = stream.getvalue()
                mime = "text/csv"
            elif format == "xlsx":
                builder = ddm_workbook if method == "ddm" else relative_workbook
                body = builder(doc, asdict(a), r)
                mime = (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            else:
                raise ValueError("Choose json, csv or xlsx export.")
            return Response(
                body,
                mimetype=mime,
                headers={
                    "Content-Disposition": f'attachment; filename="{doc["company"]["ticker"]}-{method}.{format}"'
                },
            )
        except ValueError as e:
            return jsonify(error=str(e)), 400

    app.add_url_rule(
        "/export/<method>/<format>", endpoint="suite_export", view_func=export, methods=["POST"]
    )
