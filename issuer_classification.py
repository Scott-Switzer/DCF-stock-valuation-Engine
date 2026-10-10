"""Issuer industry classification with provenance.

Resolution order: a live SEC submissions record, then this reviewed registry,
then ``unknown``. An unknown classification is never reported as a confirmed
operating company. Each reviewed entry names the primary document it came from
and that document's filing date, so the classification can be audited.

Bump ``REGISTRY_VERSION`` whenever an entry changes.
"""

REGISTRY_VERSION = 1

FINANCIAL_SIC_RANGE = range(6000, 7000)

REVIEWED = {
    "MRX": {
        "cik": "0001997464",
        "entity_name": "Marex Group plc",
        "sic": "6200",
        "description": "Security & Commodity Brokers, Dealers, Exchanges & Services",
        "entity_type": "20-F",
        "source": "SEC Form 20-F filed 2026-03-25",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/1997464/000199746426000018/"
            "0001997464-26-000018-index.htm"
        ),
        "as_of": "2026-03-25",
    },
}


def is_financial_sic(sic):
    text = str(sic or "")
    return text.isdigit() and int(text) in FINANCIAL_SIC_RANGE


def is_confirmed(record):
    """A record is confirmed when it has a SIC from SEC or the reviewed registry.

    Snapshots saved before the ``status`` field carry SEC SIC data with no status;
    those are confirmed by their SIC alone.
    """
    if not isinstance(record, dict):
        return False
    status = record.get("status")
    if status is None:
        return str(record.get("sic") or "").isdigit()
    return status == "confirmed"


def resolve_classification(ticker, sec=None):
    """Return the classification record for ``ticker``.

    ``sec`` is the SEC submissions record (``sic``, ``description``, ``entity_type``) or None.
    """
    if sec and str(sec.get("sic", "")).isdigit():
        return {
            "status": "confirmed",
            "sic": str(sec["sic"]),
            "description": sec.get("description", ""),
            "entity_type": sec.get("entity_type", ""),
            "source": "SEC submissions",
            "source_url": None,
            "as_of": None,
            "registry_version": None,
        }
    entry = REVIEWED.get(ticker)
    if entry:
        return {
            "status": "confirmed",
            "sic": entry["sic"],
            "description": entry["description"],
            "entity_type": entry["entity_type"],
            "source": entry["source"],
            "source_url": entry["source_url"],
            "as_of": entry["as_of"],
            "entity_name": entry["entity_name"],
            "cik": entry["cik"],
            "registry_version": REGISTRY_VERSION,
        }
    return {
        "status": "unknown",
        "sic": None,
        "description": "",
        "entity_type": "",
        "source": None,
        "source_url": None,
        "as_of": None,
        "registry_version": REGISTRY_VERSION,
    }


def financial_block_reason(doc):
    """Why an industrial FCFF DCF does not apply, or None.

    Independent of the noncontrolling-interest sign: a financial classification
    blocks the DCF whether or not minority interest is negative.
    """
    if not isinstance(doc, dict):
        return None
    classification = (doc.get("source") or {}).get("classification") or {}
    sic = classification.get("sic") if is_confirmed(classification) else None
    if is_financial_sic(sic) or (doc.get("company") or {}).get("is_financial") is True:
        label = f"SEC SIC {sic}" if is_financial_sic(sic) else "Financial-firm classification"
        return (
            f"{label} is a financial firm; an industrial FCFF DCF does not apply. "
            "Use P/E and P/B relative valuation or residual income."
        )
    return None
