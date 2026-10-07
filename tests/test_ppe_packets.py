from copy import deepcopy
import pytest
from dcf_loader import demo_document, ProviderError
from ppe_packets import build_packet, apply_packet, validate_packet


def observation(
    metric, value, end="2025-09-27", start="2024-09-29", available="2025-10-31", unit="USD"
):
    return dict(
        metric_id=metric,
        value=value,
        period_start=start,
        period_end=end,
        period_type="annual",
        available_at=available,
        unit=unit,
        source_id="SEC",
        source_record_id="filing",
        quality_status="VERIFIED",
    )


def packet():
    rows = [
        observation(
            "revenue",
            100 + i * 10,
            end=f"{y}-09-27",
            start=f"{y - 1}-09-29",
            available=f"{y}-10-31",
        )
        for i, y in enumerate([2023, 2024, 2025])
    ]
    rows += [observation("operating_income", 30)]
    return build_packet(
        "AAPL",
        "0000320193",
        rows,
        None,
        "2026-10-07",
        {"release_id": "fixture-release", "artifact": "fixture-public-sec", "sha256": "a" * 64},
    )


def test_packet_selects_three_actual_annual_periods_and_provenance():
    p = packet()
    assert len(p["historical"]) == 3
    assert p["historical"][-1]["fields"]["ebit"]["value"] == 30
    assert p["historical"][-1]["fields"]["capex"] is None
    assert p["historical"][-1]["fields"]["revenue"]["provenance"]["release_id"] == "fixture-release"


def test_future_and_quarterly_facts_do_not_replace_annual_revenue():
    rows = [
        observation("revenue", 100),
        observation("revenue", 999, available="2027-01-01"),
        observation("revenue", 888, start="2025-07-01"),
    ]
    p = build_packet("AAPL", "0000320193", rows, None, "2026-10-07", {})
    assert p["historical"][-1]["fields"]["revenue"]["value"] == 100


def test_conflicting_revision_is_rejected():
    with pytest.raises(ProviderError, match="Conflicting"):
        build_packet(
            "AAPL",
            "0000320193",
            [observation("revenue", 100), observation("revenue", 101)],
            None,
            "2026-10-07",
            {},
        )


def test_sec_annual_cash_flow_and_tax_supplement():
    facts = {"cik": 320193, "facts": {"us-gaap": {}}}
    for tag, value in [
        ("PaymentsToAcquirePropertyPlantAndEquipment", 9),
        ("DepreciationDepletionAndAmortization", 4),
        ("IncomeTaxExpenseBenefit", 6),
        (
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            30,
        ),
        ("PaymentsOfDividendsCommonStock", 2),
    ]:
        facts["facts"]["us-gaap"][tag] = {
            "units": {
                "USD": [
                    {
                        "val": value,
                        "start": "2024-09-29",
                        "end": "2025-09-27",
                        "filed": "2025-10-31",
                        "form": "10-K",
                        "accn": "test",
                    }
                ]
            }
        }
    p = build_packet("AAPL", "0000320193", [observation("revenue", 100)], facts, "2026-10-07", {})
    f = p["historical"][-1]["fields"]
    assert f["tax_rate"]["value"] == 0.2
    assert f["capex"]["value"] == 9
    assert p["dividends"][-1]["value"] == 2


def test_bad_units_and_wrong_issuer_rejected():
    with pytest.raises(ProviderError):
        build_packet(
            "AAPL", "0000320193", [observation("revenue", 100, unit="EUR")], None, "2026-10-07", {}
        )
    with pytest.raises(ProviderError):
        build_packet(
            "AAPL", "0000320193", [observation("revenue", 100)], {"cik": 1}, "2026-10-07", {}
        )


def test_overlay_preserves_missing_fallback_and_labels_every_field():
    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    p = packet()
    # Exact aligned fiscal periods; unrelated period must not be overwritten.
    for row, h in zip(d["historical"], p["historical"]):
        row["period_end"] = h["period_end"]
    original = deepcopy(d)
    updated = apply_packet(d, p, "2026-10-07")
    assert updated["historical"][-1]["ebit"] == 30
    assert updated["historical"][-1]["capex"] == original["historical"][-1]["capex"]
    statuses = {x["status"] for x in updated["source"]["field_coverage"]}
    assert {"PPE", "fallback"} <= statuses
    assert d == original


def test_future_packet_not_used_and_symbol_mismatch_rejected():
    with pytest.raises(ProviderError):
        apply_packet(demo_document(), packet(), "2024-01-01")
    p = packet()
    p["ticker"] = "MSFT"
    with pytest.raises(ProviderError):
        apply_packet(demo_document(), p, "2026-10-07")


def test_invalid_packet_not_served():
    p = packet()
    p["historical"][-1]["fields"]["revenue"]["value"] = float("nan")
    with pytest.raises(ProviderError):
        validate_packet(p, "AAPL", "2026-10-07")


def test_overlay_remains_a_valid_valuation_document():
    from dcf_loader import parse_document

    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    d["valuation_date"] = "2026-10-07"
    p = packet()
    for row, h in zip(d["historical"], p["historical"]):
        row["period_end"] = h["period_end"]
    d["bridge"]["as_of"] = p["historical"][-1]["period_end"]
    d["source"]["available_at"] = "2026-10-07"
    for row in d["historical"]:
        row["available_at"] = "2026-10-07"
    assert parse_document(apply_packet(d, p, "2026-10-07"))


@pytest.mark.parametrize("mutation", ["unit", "date", "period", "shape", "order"])
def test_packet_rejects_malformed_observations(mutation):
    p = packet()
    f = p["historical"][-1]["fields"]["revenue"]
    if mutation == "unit":
        f["unit"] = "shares"
    elif mutation == "date":
        f["available_at"] = "2025-99-31"
    elif mutation == "period":
        f["period_end"] = "2024-09-27"
    elif mutation == "shape":
        p["historical"][-1]["fields"] = []
    else:
        p["historical"].reverse()
    with pytest.raises(ProviderError):
        validate_packet(p, "AAPL", "2026-10-07")


def test_dividend_overlay_with_missing_sec_shares_keeps_missing_history():
    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    p = packet()
    for row, h in zip(d["historical"], p["historical"]):
        row["period_end"] = h["period_end"]
    d["bridge"]["as_of"] = p["historical"][-1]["period_end"]
    f = deepcopy(p["historical"][-1]["fields"]["revenue"])
    f["value"] = 2
    p["dividends"] = [f]
    updated = apply_packet(d, p, "2026-10-07")
    assert updated["source"]["common_dividends"]["historical"][0]["shares"] is None
    assert updated["market"]["diluted_shares"] == d["market"]["diluted_shares"]


def test_untrusted_quality_and_wrong_canonical_issuer_are_rejected():
    row = observation("revenue", 100)
    row["quality_status"] = "REJECTED"
    with pytest.raises(ProviderError, match="eligible"):
        build_packet("AAPL", "0000320193", [row], None, "2026-10-07", {})
    row["quality_status"] = "REPORTED"
    row["entity_id"] = "entity:sec:cik:0000789019"
    with pytest.raises(ProviderError, match="issuer"):
        build_packet("AAPL", "0000320193", [row], None, "2026-10-07", {})


def test_superseded_conflicts_do_not_poison_latest_revision():
    rows = [
        observation("revenue", 100),
        observation("revenue", 101),
        observation("revenue", 120, available="2026-01-01"),
    ]
    p = build_packet("AAPL", "0000320193", rows, None, "2026-10-07", {})
    assert p["historical"][-1]["fields"]["revenue"]["value"] == 120


def test_conflicts_outside_packet_periods_do_not_poison_current_packet():
    rows = [
        observation(
            "revenue", 100, end=f"{y}-09-27", start=f"{y - 1}-09-29", available=f"{y}-10-31"
        )
        for y in [2020, 2023, 2024, 2025]
    ]
    rows.append(
        observation("revenue", 101, end="2020-09-27", start="2019-09-29", available="2020-10-31")
    )
    p = build_packet("AAPL", "0000320193", rows, None, "2026-10-07", {})
    assert [r["period_end"] for r in p["historical"]] == ["2023-09-27", "2024-09-27", "2025-09-27"]
