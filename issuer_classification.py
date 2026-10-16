"""Issuer industry classification with provenance.

Resolution order: this reviewed registry, then a live SEC submissions record,
then ``unknown``. Registry entries cite the exact 10-K/20-F they were read
from (CIK, accession filing date, index URL), so each classification can be
audited without another network call. An unknown classification is never
reported as a confirmed operating company.

Refresh policy: re-verify every entry against SEC submissions and bump
``REGISTRY_VERSION`` whenever an entry changes or a new 10-K supersedes the
cited filing. SIC assignments are stable year to year; the cited filing date
bounds any staleness.
"""

REGISTRY_VERSION = 2

FINANCIAL_SIC_RANGE = range(6000, 7000)

REVIEWED = {
    "AAPL": {
        "cik": "0000320193",
        "entity_name": "Apple Inc.",
        "sic": "3571",
        "description": "Electronic Computers",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2025-10-31",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/"
            "000032019325000079-index.htm"
        ),
        "as_of": "2025-10-31",
    },
    "MSFT": {
        "cik": "0000789019",
        "entity_name": "MICROSOFT CORP",
        "sic": "7372",
        "description": "Services-Prepackaged Software",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-07-29",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/"
            "000119312526323660-index.htm"
        ),
        "as_of": "2026-07-29",
    },
    "PEP": {
        "cik": "0000077476",
        "entity_name": "PEPSICO INC",
        "sic": "2080",
        "description": "Beverages",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-03",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/"
            "000007747626000007-index.htm"
        ),
        "as_of": "2026-02-03",
    },
    "KO": {
        "cik": "0000021344",
        "entity_name": "COCA COLA CO",
        "sic": "2080",
        "description": "Beverages",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-20",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/"
            "000162828026010047-index.htm"
        ),
        "as_of": "2026-02-20",
    },
    "WMT": {
        "cik": "0000104169",
        "entity_name": "Walmart Inc.",
        "sic": "5331",
        "description": "Retail-Variety Stores",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-03-13",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/"
            "000010416926000055-index.htm"
        ),
        "as_of": "2026-03-13",
    },
    "CVX": {
        "cik": "0000093410",
        "entity_name": "CHEVRON CORP",
        "sic": "2911",
        "description": "Petroleum Refining",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-24",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/93410/000009341026000078/"
            "000009341026000078-index.htm"
        ),
        "as_of": "2026-02-24",
    },
    "JNJ": {
        "cik": "0000200406",
        "entity_name": "JOHNSON & JOHNSON",
        "sic": "2834",
        "description": "Pharmaceutical Preparations",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-11",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/"
            "000020040626000016-index.htm"
        ),
        "as_of": "2026-02-11",
    },
    "NVDA": {
        "cik": "0001045810",
        "entity_name": "NVIDIA CORP",
        "sic": "3674",
        "description": "Semiconductors & Related Devices",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-25",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/"
            "000104581026000021-index.htm"
        ),
        "as_of": "2026-02-25",
    },
    "AMD": {
        "cik": "0000002488",
        "entity_name": "ADVANCED MICRO DEVICES INC",
        "sic": "3674",
        "description": "Semiconductors & Related Devices",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-04",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/"
            "000000248826000018-index.htm"
        ),
        "as_of": "2026-02-04",
    },
    "GOOGL": {
        "cik": "0001652044",
        "entity_name": "Alphabet Inc.",
        "sic": "7370",
        "description": "Services-Computer Programming, Data Processing, Etc.",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-02-05",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/"
            "000165204426000018-index.htm"
        ),
        "as_of": "2026-02-05",
    },
    "META": {
        "cik": "0001326801",
        "entity_name": "Meta Platforms, Inc.",
        "sic": "7370",
        "description": "Services-Computer Programming, Data Processing, Etc.",
        "entity_type": "operating",
        "source": "SEC Form 10-K filed 2026-01-29",
        "source_url": (
            "https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/"
            "000162828026003942-index.htm"
        ),
        "as_of": "2026-01-29",
    },
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



def reviewed_identity(ticker, packet_cik, asof):
    """Reuse cited name/CIK only for the already-validated packet identity.

    This is metadata reuse, not a financial cache or a new eligibility gate.
    Unsupported, undated or future registry entries retain the live lookup.
    """
    from datetime import date

    entry = REVIEWED.get(ticker)
    if not entry or entry.get("cik") != packet_cik:
        return None
    if not entry.get("entity_name") or not entry.get("source_url"):
        return None
    try:
        if date.fromisoformat(entry["as_of"]) > date.fromisoformat(asof):
            return None
    except (KeyError, ValueError, TypeError):
        return None
    return entry["entity_name"], entry["cik"]


def registry_record(ticker):
    """Reviewed classification for ``ticker`` without a network call, or None.

    Returns the SEC-submissions-shaped record (sic, description, entity_type)
    with the registry as its labeled source, so callers treat it exactly like
    a live lookup for resolution purposes.
    """
    entry = REVIEWED.get(ticker)
    if not entry or not str(entry.get("sic", "")).isdigit():
        return None
    return {
        "sic": entry["sic"],
        "description": entry.get("description", ""),
        "entity_type": entry.get("entity_type", ""),
        "source": entry.get("source", "reviewed classification registry"),
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
