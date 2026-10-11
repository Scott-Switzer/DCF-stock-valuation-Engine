"""Status-only connection. No private dataset paths or records reach this app."""
import json
import time
from datetime import datetime

SOURCES = {
    "financial": ("Financial market and SEC datasets", "Approved SEC valuation packets feed autofill. Other datasets retain their own source definitions."),
    "research": ("Private research and WRDS datasets", "Connected for private research. These records are not redistributed through this app."),
    "filings": ("SEC filing intelligence", "Filing documents and extraction evidence. Not yet mapped into valuation inputs."),
    "lakehouse": ("Research lakehouse", "Private analytical tables. Requires a compatible query engine; not mapped into valuation inputs."),
}
STATES = {"READABLE", "EMPTY", "UNAVAILABLE", "NOT_CONFIGURED", "CONFIGURED"}


def sanitize_catalog(document):
    if not isinstance(document, dict) or document.get("schema_version") != "zion-dataset-catalog-v1":
        raise ValueError("Unsupported dataset status.")
    rows = document.get("sources")
    if not isinstance(rows, list) or len(rows) != len(SOURCES):
        raise ValueError("Incomplete dataset status.")
    states = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("id") not in SOURCES or row["id"] in states or row.get("connectivity") not in STATES:
            raise ValueError("Invalid dataset status.")
        states[row["id"]] = row["connectivity"]
    checked = document.get("checked_at")
    if not isinstance(checked, str) or len(checked) > 40:
        raise ValueError("Missing check date.")
    datetime.fromisoformat(checked.replace("Z", "+00:00"))
    return {"checked_at": checked, "sources": [
        {"id": key, "name": name, "note": note, "connectivity": states[key]}
        for key, (name, note) in SOURCES.items()
    ]}


def _fetch(service):
    from js import Request
    from ppe_provider import _wait
    deadline = time.monotonic() + 2
    response = _wait(service.fetch(Request.new("https://zion.internal/v1/datasets/status")), deadline)
    if response.status != 200:
        raise ValueError("Dataset status unavailable.")
    raw = str(_wait(response.text(), deadline))
    if len(raw.encode()) > 16384:
        raise ValueError("Dataset status exceeds budget.")
    return sanitize_catalog(json.loads(raw))


def load_catalog():
    from flask import request
    service = getattr(request.environ.get("workers.env"), "ZION_DATASET_CATALOG", None)
    if service is not None:
        try:
            return {"configured": True, **_fetch(service)}
        except Exception:
            state = "UNAVAILABLE"
    else:
        state = "NOT_CONFIGURED"
    return {"configured": service is not None, "checked_at": None, "sources": [
        {"id": key, "name": name, "note": note, "connectivity": state}
        for key, (name, note) in SOURCES.items()
    ]}
