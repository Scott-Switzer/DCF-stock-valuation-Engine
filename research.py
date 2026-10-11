"""Private immutable research revisions, computed by the existing valuation engines."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import uuid

from flask import Response, jsonify, render_template, request

import library
from dcf_loader import ticker_symbol
from valuation_records import normalized_inputs

THESIS_FIELDS = {
    "business": "Business overview", "thesis": "Investment thesis",
    "catalysts": "Bull-case catalysts", "risks": "Bear-case risks",
    "competition": "Industry and competition", "assumptions": "Assumption rationale",
    "questions": "Questions for further research", "evidence": "Evidence and sources",
    "market_disagreement": "Why might the market disagree?",
}
SUMMARY_COLUMNS = "id,created_at,parent_id,title,ticker,method,scenario_name,financial_hash,market_price,target_price"


def text(value, label, maximum):
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{label} must be text up to {maximum} characters.")
    return value.strip()


def get_research(identity):
    rows = library._fetchall(
        f"SELECT {SUMMARY_COLUMNS},snapshot_json FROM research_documents WHERE id=? AND client_hash=?",
        (identity, library.caller_hash()),
    )
    if not rows:
        return None
    row = rows[0]
    row["snapshot"] = json.loads(row.pop("snapshot_json"))
    return row


def list_research(ticker=None, financial_hash=None):
    sql = f"SELECT {SUMMARY_COLUMNS} FROM research_documents WHERE client_hash=?"
    params = [library.caller_hash()]
    if ticker:
        sql += " AND ticker=?"
        params.append(ticker_symbol(ticker))
    if financial_hash:
        sql += " AND financial_hash=?"
        params.append(financial_hash)
    sql += " ORDER BY created_at DESC,id DESC LIMIT 50"
    return library._fetchall(sql, tuple(params))


def save_research(raw):
    from app import assumptions_from_json, evaluate
    from suite_views import suite_assumptions, suite_evaluate

    if not isinstance(raw, dict):
        raise ValueError("Send a research object.")
    title = text(raw.get("title"), "Title", 100)
    if not title:
        raise ValueError("Name this research snapshot.")
    scenario = text(raw.get("scenario_name", "Base"), "Scenario name", 60)
    if not scenario:
        raise ValueError("Name this scenario.")
    notes = raw.get("thesis", {})
    if not isinstance(notes, dict) or set(notes) - THESIS_FIELDS.keys():
        raise ValueError("Provide supported research sections.")
    notes = {key: text(notes.get(key, ""), label, 4000) for key, label in THESIS_FIELDS.items()}
    method = raw.get("method")
    if method not in {"dcf", "ddm", "relative"}:
        raise ValueError("Choose a supported research valuation method.")
    doc = deepcopy(raw.get("financials"))
    if not isinstance(doc, dict):
        raise ValueError("Research needs an exact financial snapshot.")
    assumptions = (assumptions_from_json(raw.get("assumptions")) if method == "dcf"
                   else suite_assumptions(method, raw.get("assumptions")))
    # Caller-provided results are never trusted. No provider refresh changes the snapshot.
    result = evaluate(doc, assumptions) if method == "dcf" else suite_evaluate(method, doc, assumptions)
    parent = raw.get("parent_id")
    if parent is not None:
        if not isinstance(parent, str):
            raise ValueError("Revision reference must be text.")
        previous = get_research(parent)
        if not previous or previous["ticker"] != doc["company"]["ticker"] or previous["method"] != method:
            raise ValueError("Revision must reference your research for this company and method.")
    stored_result = deepcopy(result)
    stored_result.get("metadata", {}).pop("document", None)
    stored_result.get("metadata", {}).pop("source", None)
    snapshot = {"schema_version": "investment-research-v1", "method": method,
                "financials": doc, "assumptions": asdict(assumptions),
                "result": stored_result, "thesis": notes,
                "interpretation": "User-written research. Sources and conclusions are not independently verified. Model values are scenarios, not price predictions."}
    encoded = json.dumps(snapshot, allow_nan=False)
    if len(encoded.encode()) > 1_500_000:
        raise ValueError("Research snapshot is too large; reduce source metadata.")
    financial_hash = hashlib.sha256(json.dumps(normalized_inputs(doc), sort_keys=True, allow_nan=False).encode()).hexdigest()
    identity, created = str(uuid.uuid4()), library.now()
    library._run(
        "INSERT INTO research_documents (id,client_hash,created_at,parent_id,title,ticker,method,scenario_name,financial_hash,market_price,target_price,snapshot_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (identity, library.caller_hash(), created, parent, title, doc["company"]["ticker"], method,
         scenario, financial_hash, result["current_price"], result["target_price_12m"], encoded),
    )
    return get_research(identity)


def register_research(app):
    @app.route("/api/research", methods=["GET", "POST"])
    def research_api():
        try:
            if request.method == "GET":
                return jsonify(list_research(request.args.get("ticker")))
            return jsonify(save_research(request.get_json(silent=True))), 201
        except (ValueError, TypeError) as exc:
            return jsonify(error=str(exc)), 400

    @app.get("/api/research/<identity>")
    def research_detail_api(identity):
        record = get_research(identity)
        return jsonify(record) if record else (jsonify(error="Research not found."), 404)

    @app.get("/research")
    def research_library():
        return render_template("research_library.html", rows=list_research())

    @app.get("/research/<identity>")
    def research_page(identity):
        record = get_research(identity)
        if not record:
            return "Research not found.", 404
        cases = list_research(financial_hash=record["financial_hash"])
        return render_template("research.html", research=record, sections=THESIS_FIELDS, cases=cases)

    @app.get("/research/<identity>/export/<format>")
    def research_export(identity, format):
        record = get_research(identity)
        if not record:
            return jsonify(error="Research not found."), 404
        if format == "json":
            response = jsonify(record)
        elif format == "xlsx":
            from xlsx_export import dcf_workbook, ddm_workbook, relative_workbook

            snapshot = record["snapshot"]
            builder = {"dcf": dcf_workbook, "ddm": ddm_workbook, "relative": relative_workbook}[record["method"]]
            response = Response(builder(snapshot["financials"], snapshot["assumptions"], snapshot["result"]),
                                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            return jsonify(error="Choose JSON or model XLSX."), 404
        response.headers["Content-Disposition"] = f'attachment; filename="{record["ticker"]}-research-{record["id"]}.{format}"'
        return response
