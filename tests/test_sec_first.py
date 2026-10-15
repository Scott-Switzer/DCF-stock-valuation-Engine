import copy
from datetime import datetime, timezone, timedelta

import pytest

from dcf_loader import ProviderError
from ppe_packets import build_packet
from sec_first import eligibility_gate, load_sec_first, valuation_readiness

TODAY = datetime.now(timezone.utc).date().isoformat()
ENDS = ["2023-09-27", "2024-09-27", "2025-09-27"]
STARTS = ["2022-09-29", "2023-09-29", "2024-09-29"]
ACCN = "0000000001-25-000001"


def observation(metric, value, i, available="2026-01-15"):
    return dict(
        metric_id=metric,
        value=value,
        period_start=STARTS[i],
        period_end=ENDS[i],
        period_type="annual",
        available_at=available,
        unit="USD",
        source_id="SEC",
        source_record_id=ACCN,
        quality_status="VERIFIED",
    )


def tag_rows(tag, values, unit="USD", instant=False):
    rows = []
    for i, value in enumerate(values):
        row = {
            "val": value,
            "end": ENDS[i],
            "filed": "2026-01-15",
            "form": "10-K",
            "accn": ACCN,
        }
        if not instant:
            row["start"] = STARTS[i]
        rows.append(row)
    return {tag: {"units": {unit: rows}}}


def full_facts(without=()):
    tags = {}
    tags.update(tag_rows("NetIncomeLoss", [110, 120, 130]))
    tags.update(
        tag_rows("NetIncomeLossAvailableToCommonStockholdersBasic", [110, 120, 130])
    )
    tags.update(tag_rows("PaymentsToAcquirePropertyPlantAndEquipment", [9, 9, 9]))
    tags.update(tag_rows("DepreciationDepletionAndAmortization", [4, 4, 4]))
    tags.update(tag_rows("IncomeTaxExpenseBenefit", [6, 6, 6]))
    tags.update(
        tag_rows(
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            [30, 30, 30],
        )
    )
    tags.update(tag_rows("OperatingIncomeLoss", [20, 20, 20]))
    tags.update(tag_rows("StockholdersEquity", [400, 400, 400], instant=True))
    tags.update(tag_rows("AssetsCurrent", [300, 300, 300], instant=True))
    tags.update(tag_rows("LiabilitiesCurrent", [150, 150, 150], instant=True))
    tags.update(
        tag_rows("CashAndCashEquivalentsAtCarryingValue", [100, 100, 100], instant=True)
    )
    tags.update(tag_rows("DebtCurrent", [20, 20, 20], instant=True))
    tags.update(tag_rows("LongTermDebtNoncurrent", [80, 80, 80], instant=True))
    tags.update(tag_rows("PreferredStockValue", [0, 0, 0], instant=True))
    tags.update(tag_rows("MinorityInterest", [0, 0, 0], instant=True))
    tags.update(
        tag_rows(
            "WeightedAverageNumberOfDilutedSharesOutstanding", [10, 10, 10], unit="shares"
        )
    )
    tags.update(tag_rows("PaymentsOfDividendsCommonStock", [2, 2, 2]))
    tags.update(tag_rows("InterestExpense", [5, 5, 5]))
    for name in without:
        tags.pop(name, None)
    return {"cik": 1, "facts": {"us-gaap": tags}}


def full_packet(**kwargs):
    rows = []
    for i in range(3):
        rows.append(observation("revenue", 100 + i * 10, i))
    facts = full_facts(**kwargs)
    return build_packet("TEST", "0000000001", rows, facts, TODAY, {})


def chart_fixture(symbol):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(weeks=150)
    prices, timestamps = [], []
    value = 100.0
    for i in range(150):
        value *= 1 + (0.01 if i % 2 else -0.006)
        prices.append(value)
        timestamps.append(int((start + timedelta(weeks=i)).timestamp()))
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": symbol,
                        "instrumentType": "EQUITY",
                        "currency": "USD",
                        "regularMarketPrice": 4 if symbol == "^TNX" else 50,
                        "regularMarketTime": int(today.timestamp()),
                    },
                    "timestamp": timestamps,
                    "indicators": {"adjclose": [{"adjclose": prices}]},
                }
            ]
        }
    }


class MockHTTP:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if "/timeseries/" in url:
            raise AssertionError("Yahoo annual-statement request must be skipped")
        if "company_tickers" in url:
            return {"0": {"ticker": "TEST", "cik_str": 1, "title": "Test Inc"}}
        return copy.deepcopy(chart_fixture(url.rsplit("/", 1)[-1].replace("%5E", "^")))


def test_gate_accepts_complete_packet():
    gate = eligibility_gate(full_packet(), "TEST", TODAY)
    assert gate == {"eligible": True, "reasons": [], "coverage": gate["coverage"]}


def test_gate_reasons_name_missing_field_and_period():
    gate = eligibility_gate(full_packet(without=("MinorityInterest",)), "TEST", TODAY)
    assert not gate["eligible"]
    assert "missing_bridge_minority_interest" in gate["reasons"]


def test_gate_rejects_unbridged_common_income():
    facts = full_facts()
    facts["facts"]["us-gaap"].pop("NetIncomeLossAvailableToCommonStockholdersBasic")
    rows = [observation("revenue", 100 + i * 10, i) for i in range(3)]
    packet = build_packet("TEST", "0000000001", rows, facts, TODAY, {})
    gate = eligibility_gate(packet, "TEST", TODAY)
    assert not gate["eligible"]
    assert any(r.startswith("missing_common_income_") for r in gate["reasons"])


def test_readiness_distinguishes_packet_from_valuation():
    ready = valuation_readiness(full_packet(), "TEST", TODAY)
    assert ready["valuation_ready"] is True
    assert all(v["met"] for v in ready["states"].values())


def test_readiness_blocks_before_inputs_complete():
    blocked = valuation_readiness(None, "TEST", TODAY)
    assert blocked["valuation_ready"] is False
    assert blocked["states"]["PACKET_BUILT"]["met"] is False
    gate_blocked = valuation_readiness(
        full_packet(without=("MinorityInterest",)), "TEST", TODAY
    )
    assert gate_blocked["valuation_ready"] is False
    assert gate_blocked["states"]["PACKET_BUILT"]["met"] is True
    assert gate_blocked["states"]["INPUTS_COMPLETE"]["met"] is False
    assert "missing_bridge_minority_interest" in gate_blocked["states"]["INPUTS_COMPLETE"]["reason"]


def test_readiness_requires_priced_preferred_claims():
    facts = full_facts()
    rows = facts["facts"]["us-gaap"]["PreferredStockValue"]["units"]["USD"]
    for row in rows:
        row["val"] = 100
    packet = build_packet("TEST", "0000000001",
        [observation("revenue", 100 + i * 10, i) for i in range(3)], facts, TODAY, {})
    assert eligibility_gate(packet, "TEST", TODAY)["eligible"] is True
    blocked = valuation_readiness(packet, "TEST", TODAY)
    assert blocked["valuation_ready"] is False
    assert blocked["states"]["CAPITAL_COSTS_AVAILABLE"]["met"] is False
    priced = valuation_readiness(packet, "TEST", TODAY, preferred_cost=0.06)
    assert priced["states"]["CAPITAL_COSTS_AVAILABLE"]["met"] is True


def test_gate_rejects_absent_packet_and_bad_contract():
    assert eligibility_gate(None, "TEST", TODAY)["reasons"] == ["no_ppe_packet"]
    gate = eligibility_gate(full_packet(), "OTHER", TODAY)
    assert not gate["eligible"]
    assert gate["reasons"][0].startswith("packet_contract_invalid")


def test_loader_builds_valid_document_without_statement_request():
    http = MockHTTP()
    doc = load_sec_first("TEST", TODAY, http, full_packet())
    assert not any("/timeseries/" in url for url in http.calls)
    assert [r["period_end"] for r in doc["historical"]] == ENDS
    assert [r["net_income"] for r in doc["historical"]] == [110, 120, 130]
    assert doc["source"]["statement_source"] == "SEC-first"
    assert doc["market"]["price"] == 50
    assert doc["source"]["common_book_equity"]["value"] == doc["historical"][-1][
        "book_value"
    ]
    assert doc["source"]["capital_costs"]["wacc"] is not None
    assert doc["company"]["name"] == "Test Inc"


def test_loader_reports_gate_failure_instead_of_building():
    http = MockHTTP()
    packet = full_packet(without=("MinorityInterest",))
    with pytest.raises(ProviderError, match="missing_bridge_minority_interest"):
        load_sec_first("TEST", TODAY, http, packet)


def test_dcf_load_uses_sec_first_and_records_gate(monkeypatch):
    import auto_loading
    import ppe_provider

    http = MockHTTP()
    monkeypatch.setattr(ppe_provider, "load_packet", lambda *a, **k: full_packet())
    bundle = auto_loading.load_method("dcf", "TEST", TODAY, http=http)
    assert not any("/timeseries/" in url for url in http.calls)
    assert bundle["financials"]["source"]["statement_source"] == "SEC-first"
    assert bundle["financials"]["source"]["sec_first_gate"]["eligible"] is True
    assert bundle["load_summary"]["stage_seconds"].get("sec_first") is not None
