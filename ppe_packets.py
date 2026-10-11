"""Public SEC-only compact packets built from immutable PPE releases."""

from copy import deepcopy
from datetime import date, datetime, timezone
import math
import re
from dcf_loader import HISTORY_FIELDS, BRIDGE_FIELDS, TAGS, DURATION, ProviderError, ticker_symbol

SCHEMA = "ppe-valuation-packet-v1"
CANONICAL = {
    "revenue": "revenue",
    "ebit": "operating_income",
    "net_income": "net_income",
    "book_value": "shareholders_equity",
    "cash": "cash",
    "total_debt": "total_debt",
}
SEC_TAGS = {
    **TAGS,
    "book_value": ["StockholdersEquity"],
    "common_dividends": ["PaymentsOfDividendsCommonStock"],
    "interest_expense": ["InterestExpense", "InterestAndDebtExpense"],
}
SEC_TAGS["short_term_borrowings"] = ["ShortTermBorrowings", "CommercialPaper"]
DURATIONS = DURATION | {"common_dividends", "interest_expense"}


def _number(value):
    if isinstance(value, bool):
        raise ProviderError("Invalid packet number.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ProviderError("Invalid packet number.") from None
    if not math.isfinite(value):
        raise ProviderError("Invalid packet number.")
    return value


def _annual(start, end):
    try:
        return 330 <= (date.fromisoformat(end) - date.fromisoformat(start)).days <= 400
    except (TypeError, ValueError):
        return False


def _field(value, end, available, unit, provenance):
    return {
        "value": _number(value),
        "period_end": end,
        "available_at": available,
        "unit": unit,
        "provenance": provenance,
    }


def _sec(facts, metric, end, cutoff, source):
    unit = "shares" if metric == "diluted_shares" else "USD"
    for tag in SEC_TAGS.get(metric, []):
        candidates = []
        for r in (
            facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get(unit, [])
        ):
            if (
                r.get("end") != end
                or r.get("form") not in {"10-K", "10-K/A"}
                or r.get("filed", "9999") > cutoff
            ):
                continue
            if metric in DURATIONS and not _annual(r.get("start"), end):
                continue
            if metric not in DURATIONS and r.get("start"):
                continue
            candidates.append(r)
        if candidates:
            latest = max(r["filed"] for r in candidates)
            top = [r for r in candidates if r["filed"] == latest]
            if len({_number(r["val"]) for r in top}) != 1:
                raise ProviderError(f"Conflicting SEC {metric} facts for {end}.")
            r = top[0]
            return _field(
                r["val"],
                end,
                r["filed"],
                unit,
                {
                    **source,
                    "provider": "SEC companyfacts",
                    "tag": tag,
                    "accession": r.get("accn"),
                    "period_start": r.get("start"),
                    "filing_date": r["filed"],
                },
            )
    return None


def _derived(value, components, formula, unit="USD"):
    return _field(
        value,
        components[0]["period_end"],
        max(x["available_at"] for x in components),
        unit,
        {"provider": "PPE SEC-derived", "formula": formula, "components": components},
    )


def build_packet(ticker, cik, rows, facts, cutoff, source):
    ticker = ticker_symbol(ticker)
    date.fromisoformat(cutoff)
    if facts and str(facts.get("cik", "")).zfill(10) != cik:
        raise ProviderError("SEC issuer mismatch.")
    groups = {}
    inverse = {v: k for k, v in CANONICAL.items()}
    for row in rows:
        metric = inverse.get(row.get("metric_id"))
        if not metric or row.get("source_id") != "SEC" or row.get("period_type") != "annual":
            continue
        if row.get("quality_status") not in {"REPORTED", "CALCULATED", "VERIFIED"}:
            continue
        entity = row.get("entity_id")
        if entity:
            identity = re.match(r"entity:sec:cik:([0-9]{10})(?:$|[:_])", entity)
            if not identity or identity.group(1) != cik:
                raise ProviderError("PPE observation issuer mismatch.")
        end = row.get("period_end")
        available = row.get("available_at", "")
        if not available or not end or end > cutoff or available[:10] > cutoff:
            continue
        if metric in {"revenue", "ebit", "net_income"}:
            if not _annual(row.get("period_start"), end):
                continue
        elif row.get("period_start") not in {None, "", end}:
            continue
        groups.setdefault(end, {}).setdefault(metric, []).append(row)
    ends = sorted(k for k, v in groups.items() if v.get("revenue"))[-3:]
    if not ends:
        raise ProviderError("No eligible annual PPE revenue.")
    selected = {}
    for end in ends:
        selected[end] = {}
        for metric, candidates in groups[end].items():
            latest = max(r["available_at"] for r in candidates)
            top = [r for r in candidates if r["available_at"] == latest]
            if any(r.get("unit") != "USD" for r in top):
                raise ProviderError(f"Unexpected PPE unit for {metric}.")
            if len({_number(r.get("value_decimal", r.get("value"))) for r in top}) != 1:
                raise ProviderError(f"Conflicting PPE {metric} observations for {end}.")
            row = top[0]
            selected[end][metric] = _field(
                row.get("value_decimal", row.get("value")),
                end,
                latest,
                "USD",
                {
                    **source,
                    "provider": "PPE SEC canonical",
                    "accession": row.get("source_record_id"),
                    "evidence_id": row.get("evidence_id"),
                    "period_start": row.get("period_start"),
                    "quality_status": row.get("quality_status"),
                },
            )
    groups = selected
    historical = []
    dividends = []
    bridges = {}
    shares = None
    interest = None
    facts = facts or {}
    sec_source = source.get("sec_source", {})
    for end in ends:
        g = groups[end]
        f = {
            k: g.get(k) or _sec(facts, k, end, cutoff, sec_source)
            for k in HISTORY_FIELDS
            if k not in {"tax_rate", "nwc"}
        }
        values = {
            k: _sec(facts, k, end, cutoff, sec_source)
            for k in [
                "current_assets",
                "current_liabilities",
                "cash",
                "short_term_debt",
                "current_maturities",
                "short_term_borrowings",
                "long_term_debt",
                "tax_expense",
                "pretax_income",
                "diluted_shares",
                "common_dividends",
                "interest_expense",
            ]
        }
        if (
            not values["short_term_debt"]
            and values["current_maturities"]
            and values["short_term_borrowings"]
        ):
            c = [values["current_maturities"], values["short_term_borrowings"]]
            values["short_term_debt"] = _derived(
                sum(x["value"] for x in c),
                c,
                "current long-term debt + short-term borrowings/commercial paper",
            )
        nwc = [
            values[k] for k in ["current_assets", "cash", "current_liabilities", "short_term_debt"]
        ]
        f["nwc"] = (
            _derived(
                nwc[0]["value"] - nwc[1]["value"] - nwc[2]["value"] + nwc[3]["value"],
                nwc,
                "(current assets - cash) - (current liabilities - current interest-bearing debt)",
            )
            if all(nwc)
            else None
        )
        tax = [values[k] for k in ["tax_expense", "pretax_income"]]
        f["tax_rate"] = (
            _derived(
                tax[0]["value"] / tax[1]["value"], tax, "income tax expense / pretax income", "pure"
            )
            if all(tax) and tax[1]["value"]
            else None
        )
        if f.get("capex"):
            f["capex"]["value"] = abs(f["capex"]["value"])
        f["diluted_shares"] = values["diluted_shares"]
        historical.append({"period_end": end, "fields": f})
        if values["common_dividends"]:
            dividends.append(values["common_dividends"])
        bridges = {k: g.get(k) or _sec(facts, k, end, cutoff, sec_source) for k in BRIDGE_FIELDS}
        bridges["short_term_debt"] = values["short_term_debt"]
        shares = values["diluted_shares"]
        interest = values["interest_expense"]
    packet = {
        "schema_version": SCHEMA,
        "ticker": ticker,
        "cik": cik,
        "cutoff_date": cutoff,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "historical": historical,
        "bridge": bridges,
        "diluted_shares": shares,
        "interest_expense": interest,
        "dividends": dividends,
    }
    validate_packet(packet, ticker, cutoff)
    return packet


def _date(value, *, timestamp=False):
    try:
        if not isinstance(value, str):
            raise ValueError()
        parsed = (
            datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            if timestamp and len(value) > 10
            else date.fromisoformat(value)
        )
        if value[:10] != parsed.isoformat():
            raise ValueError()
        return parsed
    except (TypeError, ValueError):
        raise ProviderError("Invalid PPE observation date.") from None


def validate_packet(packet, ticker, asof):
    if (
        not isinstance(packet, dict)
        or packet.get("schema_version") != SCHEMA
        or packet.get("ticker") != ticker
    ):
        raise ProviderError("PPE packet identity/schema mismatch.")
    cutoff = _date(packet.get("cutoff_date"))
    requested = _date(asof)
    if cutoff > requested:
        raise ProviderError("PPE packet was selected after this valuation cutoff.")
    if not isinstance(packet.get("source"), dict):
        raise ProviderError("Invalid PPE source.")
    history = packet.get("historical")
    if not isinstance(history, list) or not 1 <= len(history) <= 3:
        raise ProviderError("Invalid PPE annual coverage.")

    def field(f, metric, end):
        if f is None:
            return
        if not isinstance(f, dict):
            raise ProviderError("Invalid PPE field shape.")
        if not isinstance(f.get("value"), (int, float)):
            raise ProviderError("Invalid PPE numeric field type.")
        value = _number(f.get("value"))
        expected = (
            "shares" if metric == "diluted_shares" else "pure" if metric == "tax_rate" else "USD"
        )
        if f.get("unit") != expected or not isinstance(f.get("provenance"), dict):
            raise ProviderError("Invalid PPE field provenance/unit.")
        period = _date(f.get("period_end"))
        available = _date(f.get("available_at"), timestamp=True)
        if period != end or period > cutoff or available > cutoff or available < period:
            raise ProviderError("PPE observation unavailable or period mismatched at cutoff.")
        if metric == "diluted_shares" and value <= 0:
            raise ProviderError("Invalid PPE diluted shares.")

    ends = []
    for row in history:
        if not isinstance(row, dict) or not isinstance(row.get("fields"), dict):
            raise ProviderError("Invalid PPE historical row.")
        end = _date(row.get("period_end"))
        if ends and not 330 <= (end - ends[-1]).days <= 400:
            raise ProviderError("PPE annual periods must be chronological and unique.")
        ends.append(end)
        if set(row["fields"]) - (set(HISTORY_FIELDS) | {"diluted_shares"}):
            raise ProviderError("Unknown PPE historical field.")
        if not row["fields"].get("revenue"):
            raise ProviderError("Missing PPE revenue.")
        for metric, f in row["fields"].items():
            field(f, metric, end)
    bridge = packet.get("bridge")
    if not isinstance(bridge, dict) or set(bridge) - set(BRIDGE_FIELDS):
        raise ProviderError("Invalid PPE bridge.")
    for metric, f in bridge.items():
        field(f, metric, ends[-1])
    field(packet.get("diluted_shares"), "diluted_shares", ends[-1])
    field(packet.get("interest_expense"), "interest_expense", ends[-1])
    dividends = packet.get("dividends")
    if not isinstance(dividends, list) or len(dividends) > 3:
        raise ProviderError("Invalid PPE dividend coverage.")
    previous = None
    for f in dividends:
        if not isinstance(f, dict):
            raise ProviderError("Invalid PPE dividend field.")
        end = _date(f.get("period_end"))
        if end not in ends or (previous and end <= previous):
            raise ProviderError("Invalid PPE dividend periods.")
        field(f, "common_dividends", end)
        previous = end
    return packet


def apply_packet(document, packet, asof):
    validate_packet(packet, document["company"]["ticker"], asof)
    doc = deepcopy(document)
    coverage = []
    fallback = doc["source"].get("name", "existing source")

    def fallback_period(path):
        if path.startswith("historical."):
            return path.split(".")[1]
        if path.startswith("bridge."):
            return document["bridge"].get("as_of")
        if path.startswith("market.price"):
            return document["market"].get("price_as_of")
        if path == "common_dividends":
            return document["source"].get("common_dividends", {}).get("period_end")
        if path == "common_book_equity":
            return document["source"].get("common_book_equity", {}).get("period_end")
        return document["historical"][-1]["period_end"]

    def choose(path, old, f):
        coverage.append(
            {
                "field": path,
                "status": "PPE" if f else "fallback",
                "provider": f["provenance"].get("provider", "PPE") if f else fallback,
                "period_end": f["period_end"] if f else fallback_period(path),
                "available_at": f["available_at"] if f else document["source"].get("available_at"),
                "value": f["value"] if f else old,
                "provenance": f["provenance"] if f else {},
            }
        )
        return f["value"] if f else old

    matched = []
    for row in doc["historical"]:
        candidates = [
            x
            for x in packet["historical"]
            if abs(
                (date.fromisoformat(x["period_end"]) - date.fromisoformat(row["period_end"])).days
            )
            <= 7
        ]
        p = candidates[0] if len(candidates) == 1 else None
        if p:
            matched.append(p)
        row.setdefault("provenance", {})
        original_end = row["period_end"]
        used_fields = {}
        for key in HISTORY_FIELDS:
            # The canonical metric and NetIncomeLoss/ProfitLoss do not verify
            # income available to common shareholders (preferred dividends).
            f = p["fields"].get(key) if p and key != "net_income" else None
            row[key] = choose(f"historical.{original_end}.{key}", row.get(key), f)
            if f:
                used_fields[key] = f
                row["provenance"][key] = {
                    **f["provenance"],
                    "period_end": f["period_end"],
                    "available_at": f["available_at"],
                }
        if p and len(used_fields) == len(HISTORY_FIELDS):
            row["period_end"] = p["period_end"]
            row["available_at"] = max(p["fields"][k]["available_at"] for k in HISTORY_FIELDS)
        # Partial fiscal-year matches retain exact dates in each field's provenance.
    latest = packet["historical"][-1]["period_end"]
    aligned = bool(
        any(p["period_end"] == latest for p in matched)
        and abs(
            (
                date.fromisoformat(doc["historical"][-1]["period_end"]) - date.fromisoformat(latest)
            ).days
        )
        <= 7
        and abs((date.fromisoformat(doc["bridge"]["as_of"]) - date.fromisoformat(latest)).days) <= 7
    )
    for key in BRIDGE_FIELDS:
        f = packet["bridge"].get(key) if aligned else None
        doc["bridge"][key] = choose("bridge." + key, doc["bridge"].get(key), f)
        if f:
            doc["source"].setdefault("bridge_provenance", {})[key] = f
    shares = packet.get("diluted_shares") if aligned else None
    doc["market"]["diluted_shares"] = choose(
        "market.diluted_shares", doc["market"].get("diluted_shares"), shares
    )
    if shares:
        doc["market"]["shares_basis"] = (
            "SEC annual weighted-average diluted shares via PPE; " + shares["period_end"]
        )
    dividends = packet.get("dividends", [])
    existing = doc["source"].get("common_dividends", {})
    if aligned and dividends and dividends[-1]["period_end"] == latest:
        d = dividends[-1]
        existing.update(
            value=d["value"],
            period_end=latest,
            unit="USD",
            provenance=d,
            per_share=d["value"] / doc["market"]["diluted_shares"],
        )
        existing["historical"] = [
            {
                "period_end": x["period_end"],
                "value": x["value"],
                "shares": next(
                    (
                        (row["fields"].get("diluted_shares") or {}).get("value")
                        for row in packet["historical"]
                        if row["period_end"] == x["period_end"]
                    ),
                    None,
                ),
            }
            for x in dividends
        ]
        doc["source"]["common_dividends"] = existing
    choose(
        "common_dividends",
        existing.get("value"),
        dividends[-1] if aligned and dividends and dividends[-1]["period_end"] == latest else None,
    )
    choose("common_book_equity", doc["source"].get("common_book_equity", {}).get("value"), None)
    for key in ["price", "price_as_of"]:
        choose("market." + key, doc["market"].get(key), None)
    costs = doc["source"].get("capital_costs", {})
    if costs:
        fallback_interest = (
            costs["reported_cost_of_debt"] * costs.get("debt", 0)
            if costs.get("reported_cost_of_debt") is not None
            else None
        )
        debt = doc["bridge"]["short_term_debt"] + doc["bridge"]["long_term_debt"]
        costs.update(
            debt=debt,
            debt_book_value=debt,
            tax_rate=doc["historical"][-1]["tax_rate"],
        )
        interest = packet.get("interest_expense") if aligned else None
        if interest and debt > 0:
            costs["reported_cost_of_debt"] = interest["value"] / debt
        elif fallback_interest is not None and debt > 0:
            costs["reported_cost_of_debt"] = fallback_interest / debt
            costs["debt_cost_basis"] = (
                "Fallback annual interest expense / merged split debt; review field sources"
            )
        else:
            costs["reported_cost_of_debt"] = None
        if interest and debt > 0:
            costs["debt_cost_basis"] = (
                "SEC annual interest expense / dated split debt; field sources retained in PPE coverage"
            )
        if "risk_free_rate" in costs:
            choose("capital_costs.risk_free_rate", costs["risk_free_rate"], None)
        if "beta" in costs:
            choose("capital_costs.beta", costs["beta"], None)
    doc["source"].update(
        kind="api",
        name="PPE / SEC financials + labeled market fallbacks"
        if any(x["status"] == "PPE" for x in coverage)
        else fallback + " (PPE fiscal periods unmatched)",
        ppe_release=packet["source"],
        ppe_cutoff=packet["cutoff_date"],
        field_coverage=coverage,
    )
    doc["source"].setdefault("warnings", []).append(
        "PPE annual periods match the baseline fiscal end within seven days; actual observation dates and fallback sources are retained per field. Missing PPE fields and common-stockholder income use the labeled baseline source. Ordinary-share market equity remains the WACC weight basis; diluted weighted-average shares are used for per-share valuation."
    )
    return doc


def enrich_packet(previous, candidate, asof):
    """Preserve same-period published evidence when a supplement is absent/older."""
    validate_packet(previous, candidate['ticker'], asof)
    validate_packet(candidate, candidate['ticker'], asof)
    if previous.get('cik') != candidate.get('cik'):
        raise ProviderError('PPE enrichment issuer mismatch.')
    result = deepcopy(candidate)

    def choose(old, new):
        if not old or (new and old['period_end'] != new['period_end']):
            return new
        if not new or old['available_at'][:10] > new['available_at'][:10]:
            return deepcopy(old)
        return new

    prior = {row['period_end']: row for row in previous['historical']}
    for row in result['historical']:
        old = prior.get(row['period_end'], {}).get('fields', {})
        row['fields'] = {k: choose(old.get(k), v) for k, v in row['fields'].items()}
    if previous['historical'][-1]['period_end'] == result['historical'][-1]['period_end']:
        result['bridge'] = {k: choose(previous['bridge'].get(k), v) for k, v in result['bridge'].items()}
        for key in ['diluted_shares', 'interest_expense']:
            result[key] = choose(previous.get(key), result.get(key))
    dividends = {row['period_end']: row for row in previous['dividends']}
    incoming = {row['period_end']: row for row in result['dividends']}
    result['dividends'] = [value for row in result['historical']
        if (value := choose(dividends.get(row['period_end']), incoming.get(row['period_end']))) is not None]
    return validate_packet(result, result['ticker'], asof)


def supplement_statement_facts(facts, ends, packet, ticker, asof):
    """Fill statement gaps before baseline validation, preserving SEC provenance.

    This is an adapter into the statement assembler's metric vocabulary. It never
    labels SEC evidence as Yahoo or treats general net income as common income.
    """
    validate_packet(packet, ticker, asof)
    result = deepcopy(facts)
    mapping = {'revenue': 'TotalRevenue', 'ebit': 'OperatingIncome',
        'book_value': 'StockholdersEquity', 'capex': 'CapitalExpenditure',
        'd_and_a': 'ReconciledDepreciation', 'nwc': 'PPEOperatingNWC',
        'tax_rate': 'PPEEffectiveTaxRate', 'diluted_shares': 'DilutedAverageShares'}
    latest = packet['historical'][-1]['period_end']
    for end in ends:
        matches = [row for row in packet['historical']
            if abs((date.fromisoformat(row['period_end']) - date.fromisoformat(end)).days) <= 7]
        if len(matches) != 1:
            continue
        row = matches[0]
        fields = {target: row['fields'].get(source) for source, target in mapping.items()}
        if row['period_end'] == latest:
            fields.update({target: packet['bridge'].get(source) for source, target in {
                'short_term_debt': 'CurrentDebt', 'long_term_debt': 'LongTermDebt',
                'cash': 'CashAndCashEquivalents', 'preferred_equity': 'PreferredStockEquity',
                'minority_interest': 'MinorityInterest'}.items()})
            fields['InterestExpense'] = packet.get('interest_expense')
        fields['CommonStockDividendPaid'] = next((d for d in packet['dividends']
            if d['period_end'] == row['period_end']), None)
        for metric, field in fields.items():
            if field is not None and (end, metric) not in result:
                result[end, metric] = (field['value'], {
                    **field['provenance'], 'period_end': field['period_end'],
                    'available_at': field['available_at'], 'unit': field['unit'],
                    'value': field['value'], 'assembly_metric': metric,
                    'basis': 'Published PPE/SEC statement supplement'})
    return result
