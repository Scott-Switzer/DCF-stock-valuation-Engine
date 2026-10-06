"""Private research records; no IP addresses, names or request headers are stored."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import uuid

MODEL_VERSION = "cuig-dcf-v1"
INSERT_SQL = """INSERT OR IGNORE INTO valuations
(id,created_at,model_version,ticker,valuation_date,source_kind,is_demo,intrinsic_value,
target_price_12m,market_price,upside,assumptions_json,financials_json,result_json,client_hash,input_hash)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


def record_values(doc, assumptions, result, client_hash):
    inputs = json.dumps(
        {"financials": doc, "assumptions": asdict(assumptions)}, sort_keys=True, allow_nan=False
    )
    stored_result = deepcopy(result)
    # Financials/source are already saved once in financials_json.
    stored_result["metadata"].pop("document", None)
    stored_result["metadata"].pop("source", None)
    values = (
        str(uuid.uuid4()),
        datetime.now(timezone.utc).isoformat(),
        MODEL_VERSION,
        doc["company"]["ticker"],
        doc["valuation_date"],
        doc["source"]["kind"],
        int(result["metadata"]["is_demo"]),
        result["intrinsic_value"],
        result["target_price_12m"],
        result["current_price"],
        result["upside"],
        json.dumps(asdict(assumptions), allow_nan=False),
        json.dumps(doc, allow_nan=False),
        json.dumps(stored_result, allow_nan=False),
        client_hash,
        hashlib.sha256(inputs.encode()).hexdigest(),
    )
    if sum(len(v.encode()) for v in values if isinstance(v, str)) > 1_800_000:
        raise ValueError(
            "Submitted source metadata is too large to save. Reduce the financial document."
        )
    return values


def save_valuation(doc, assumptions, result):
    from flask import request, current_app

    if not current_app.config.get("CLOUDFLARE"):
        return None
    from pyodide.ffi import run_sync

    values = record_values(doc, assumptions, result, request.environ["dcf.client_hash"])
    db = request.environ["workers.env"].DB
    run_sync(db.prepare(INSERT_SQL).bind(*values).run())
    row = run_sync(
        db.prepare("SELECT id FROM valuations WHERE client_hash=? AND input_hash=?")
        .bind(values[-2], values[-1])
        .first()
    )
    return row.id
