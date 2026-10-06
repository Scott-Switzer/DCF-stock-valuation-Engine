import pytest
from dcf_loader import (
    sec_fact,
    load_sec,
    zion_document,
    parse_document,
    JsonHTTP,
    ProviderError,
    TAGS,
)


def sec_payload():
    facts = {"facts": {"us-gaap": {}}}
    for metric, tags in TAGS.items():
        values = []
        for year in [2023, 2024, 2025]:
            val = {
                "revenue": 1000,
                "ebit": 200,
                "net_income": 150,
                "capex": 50,
                "d_and_a": 30,
                "current_assets": 300,
                "current_liabilities": 150,
                "cash": 100,
                "short_term_debt": 50,
                "current_maturities": 50,
                "short_term_borrowings": 0,
                "long_term_debt": 150,
                "total_assets": 1000,
                "total_liabilities": 500,
                "tax_expense": 50,
                "pretax_income": 200,
                "diluted_shares": 100,
                "preferred_equity": 0,
                "minority_interest": 0,
            }[metric]
            row = {
                "end": f"{year}-12-31",
                "filed": f"{year + 1}-02-01",
                "form": "10-K",
                "val": val,
                "accn": f"0001-{year}",
            }
            if metric in {
                "revenue",
                "ebit",
                "net_income",
                "d_and_a",
                "capex",
                "tax_expense",
                "pretax_income",
                "diluted_shares",
            }:
                row["start"] = f"{year}-01-01"
            values.append(row)
        facts["facts"]["us-gaap"][tags[0]] = {
            "units": {"shares" if metric == "diluted_shares" else "USD": values}
        }
    return facts


def test_sec_periods_reject_quarterly_and_lookahead_facts():
    facts = sec_payload()
    tag = TAGS["revenue"][0]
    facts["facts"]["us-gaap"][tag]["units"]["USD"] += [
        {
            "start": "2025-10-01",
            "end": "2025-12-31",
            "filed": "2026-03-01",
            "form": "10-K",
            "val": 999,
        },
        {
            "start": "2025-01-01",
            "end": "2025-12-31",
            "filed": "2027-03-01",
            "form": "10-K/A",
            "val": 888,
        },
    ]
    value, provenance = sec_fact(facts, "revenue", "2025-12-31", "2026-10-06")
    assert value == 1000
    assert provenance["filed"] == "2026-02-01"


def test_sec_load_produces_aligned_history_and_real_split_debt(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Client test@example.com")

    class HTTP:
        def get(self, url, **kw):
            if "company_tickers" in url:
                return {"0": {"ticker": "TEST", "cik_str": 123, "title": "Test Operating Company"}}
            return sec_payload()

    doc = load_sec("TEST", "2026-10-06", HTTP())
    assert [row["period_end"] for row in doc["historical"]] == [
        "2023-12-31",
        "2024-12-31",
        "2025-12-31",
    ]
    assert doc["bridge"]["short_term_debt"] == 50 and doc["bridge"]["long_term_debt"] == 150
    assert doc["historical"][-1]["nwc"] == 100 and doc["historical"][-1]["tax_rate"] == 0.25
    assert doc["market"]["price"] is None
    doc["company"]["eligible"] = True
    doc["market"]["price"] = 20
    doc["bridge"]["other_nonoperating_assets"] = 0
    parse_document(doc).validate()


def test_sec_missing_capex_remains_missing(monkeypatch):
    facts = sec_payload()
    del facts["facts"]["us-gaap"][TAGS["capex"][0]]
    assert sec_fact(facts, "capex", "2025-12-31", "2026-10-06") == (None, None)


def test_sec_same_filing_conflict_does_not_pick_arbitrary_value():
    facts = sec_payload()
    rows = facts["facts"]["us-gaap"][TAGS["revenue"][0]]["units"]["USD"]
    rows.append({**rows[-1], "val": 999})
    with pytest.raises(ProviderError, match="Ambiguous"):
        sec_fact(facts, "revenue", "2025-12-31", "2026-10-06")


def zion_packet():
    metrics = {
        "revenue": 1000,
        "operating_income": 200,
        "net_income": 150,
        "capital_expenditures": -50,
        "depreciation_and_amortization": 30,
        "net_working_capital": 100,
        "shareholders_equity": 500,
        "effective_tax_rate": 0.25,
        "short_term_debt": 50,
        "current_maturities": 50,
        "short_term_borrowings": 0,
        "long_term_debt": 150,
        "cash_and_cash_equivalents": 100,
        "preferred_equity": 0,
        "minority_interest": 0,
        "other_nonoperating_assets": 0,
        "weighted_average_diluted_shares": 100,
    }
    annual = []
    for year in [2023, 2024, 2025]:
        for key, value in metrics.items():
            unit = (
                "pure"
                if key == "effective_tax_rate"
                else "shares"
                if key == "weighted_average_diluted_shares"
                else "USD"
            )
            annual.append(
                {
                    "metric_id": key,
                    "period_end": f"{year}-12-31",
                    "period_type": "annual",
                    "value_decimal": str(value),
                    "unit": unit,
                    "available_at": f"{year + 1}-02-01T00:00:00Z",
                    "observation_id": f"{key}-{year}",
                    "provenance": {"serving_release_id": "release-one"},
                }
            )
    return {
        "symbol": "TEST",
        "status": "AVAILABLE",
        "identity": {"canonical": {"entity_id": "test-entity"}},
        "releases": {"fundamentals": "release-one"},
        "fundamentals": {"status": "AVAILABLE", "annual": annual},
        "prices": {
            "latest": {
                "status": "AVAILABLE",
                "observation": {"session_date": "2026-10-05", "close": "20", "unit": "USD/share"},
            }
        },
        "request_id": "test-request",
    }


def test_zion_retains_provenance_and_normalizes_capex_outflow():
    doc = zion_document(zion_packet(), "TEST", "2026-10-06")
    assert doc["historical"][-1]["capex"] == 50
    assert doc["source"]["releases"]["fundamentals"] == "release-one"
    assert doc["historical"][-1]["provenance"]["revenue"]["observation_id"] == "revenue-2025"
    assert doc["market"]["price"] == 20
    doc["company"]["eligible"] = True
    parse_document(doc).validate()


def test_zion_currency_is_not_silently_converted():
    packet = zion_packet()
    packet["fundamentals"]["annual"][0]["unit"] = "EUR"
    with pytest.raises(ProviderError, match="unit"):
        zion_document(packet, "TEST", "2026-10-06")


def test_zion_conflicting_revisions_require_review():
    packet = zion_packet()
    rows = packet["fundamentals"]["annual"]
    rows.append({**rows[0], "value_decimal": "999"})
    with pytest.raises(ProviderError, match="conflicting"):
        zion_document(packet, "TEST", "2026-10-06")


def test_http_retries_rate_limit_and_does_not_log_credentials(tmp_path):
    from storage import Store

    class Response:
        def __init__(self, status):
            self.status_code = status

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def iter_content(self, _):
            yield b'{"value":123}'

    class Session:
        def __init__(self):
            self.statuses = iter([429, 200])

        def get(self, *args, **kwargs):
            return Response(next(self.statuses))

    http = JsonHTTP(session=Session(), store=Store(str(tmp_path / "cache.sqlite3")))
    assert http.get("https://example.com") == {"value": 123}


def test_http_deadline_returns_actionable_error(tmp_path):
    from storage import Store

    http = JsonHTTP(budget=-1, store=Store(str(tmp_path / "cache.sqlite3")))
    with pytest.raises(ProviderError, match="deadline"):
        http.get("https://example.com")


def test_sec_current_maturities_and_short_borrowings_are_added():
    facts = sec_payload()
    us = facts["facts"]["us-gaap"]
    us.pop("DebtCurrent", None)
    us["LongTermDebtCurrent"] = {
        "units": {"USD": [{"end": "2025-12-31", "filed": "2026-02-01", "form": "10-K", "val": 50}]}
    }
    us["ShortTermBorrowings"] = {
        "units": {"USD": [{"end": "2025-12-31", "filed": "2026-02-01", "form": "10-K", "val": 25}]}
    }
    assert sec_fact(facts, "short_term_debt", "2025-12-31", "2026-10-06")[0] == 75


@pytest.mark.parametrize("change", ["unavailable", "quarterly", "price_currency_missing"])
def test_zion_does_not_certify_unavailable_or_wrong_period_data(change):
    packet = zion_packet()
    if change == "unavailable":
        packet["fundamentals"]["status"] = "UNAVAILABLE"
    if change == "quarterly":
        for obs in packet["fundamentals"]["annual"]:
            obs["period_type"] = "quarterly"
    if change == "price_currency_missing":
        del packet["prices"]["latest"]["observation"]["unit"]
        assert zion_document(packet, "TEST", "2026-10-06")["market"]["price"] is None
    else:
        with pytest.raises(ProviderError):
            zion_document(packet, "TEST", "2026-10-06")


def test_sec_repeated_filings_scan_unique_periods_only(monkeypatch):
    import dcf_loader
    from collections import Counter

    monkeypatch.setenv("EDGAR_IDENTITY", "Test Client test@example.com")
    facts = sec_payload()
    revenue = facts["facts"]["us-gaap"][TAGS["revenue"][0]]["units"]["USD"]
    revenue *= 100
    calls = Counter()
    original = dcf_loader.sec_fact

    def counted(facts, metric, end, asof):
        calls[metric, end] += 1
        return original(facts, metric, end, asof)

    monkeypatch.setattr(dcf_loader, "sec_fact", counted)

    class HTTP:
        def get(self, url, **kwargs):
            return (
                {"0": {"ticker": "TEST", "cik_str": 123, "title": "Test"}}
                if "company_tickers" in url
                else facts
            )

    doc = load_sec("TEST", "2026-10-06", HTTP())
    assert len(doc["historical"]) == 3
    assert all(calls["revenue", end] <= 2 for end in ("2023-12-31", "2024-12-31", "2025-12-31"))
