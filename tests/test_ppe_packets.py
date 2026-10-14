import json
from copy import deepcopy
from pathlib import Path
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


def _tag_facts(end, start, filed, accn, pairs):
    facts = {"cik": 320193, "facts": {"us-gaap": {}}}
    for tag, value in pairs:
        facts["facts"]["us-gaap"][tag] = {
            "units": {
                "USD": [
                    {
                        "val": value,
                        "start": start,
                        "end": end,
                        "filed": filed,
                        "form": "10-K",
                        "accn": accn,
                    }
                ]
            }
        }
    return facts


def test_conflicting_net_income_resolves_to_parent_tag():
    accn = "0000320193-25-000001"
    rows = [
        observation("revenue", 100),
        dict(observation("net_income", 4863), source_record_id=accn),
        dict(observation("net_income", 4873), source_record_id=accn),
    ]
    facts = _tag_facts(
        "2025-09-27",
        "2024-09-29",
        "2025-10-31",
        accn,
        [("NetIncomeLoss", 4863), ("ProfitLoss", 4873)],
    )
    p = build_packet("AAPL", "0000320193", rows, facts, "2026-10-07", {})
    field = p["historical"][-1]["fields"]["net_income"]
    assert field["value"] == 4863
    assert field["provenance"]["superseded_canonical_values"] == [4873]


def test_conflicting_revenue_resolves_by_tag_priority():
    accn = "0000320193-25-000001"
    rows = [
        dict(observation("revenue", 196913), source_record_id=accn),
        dict(observation("revenue", 200949), source_record_id=accn),
    ]
    facts = _tag_facts(
        "2025-09-27",
        "2024-09-29",
        "2025-10-31",
        accn,
        [
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 196913),
            ("Revenues", 200949),
        ],
    )
    p = build_packet("AAPL", "0000320193", rows, facts, "2026-10-07", {})
    assert p["historical"][-1]["fields"]["revenue"]["value"] == 196913


def test_conflict_with_unmatched_facts_is_rejected():
    accn = "0000320193-25-000001"
    rows = [
        observation("revenue", 100),
        dict(observation("net_income", 4863), source_record_id=accn),
        dict(observation("net_income", 4874), source_record_id=accn),
    ]
    facts = _tag_facts(
        "2025-09-27",
        "2024-09-29",
        "2025-10-31",
        accn,
        [("NetIncomeLoss", 4860), ("ProfitLoss", 4873)],
    )
    with pytest.raises(ProviderError, match="Conflicting"):
        build_packet("AAPL", "0000320193", rows, facts, "2026-10-07", {})


def test_productive_assets_capex_and_accretion_d_and_a_tags_map():
    p = build_with(
        PaymentsToAcquireProductiveAssets=[annual_fact(42)],
        DepreciationAmortizationAndAccretionNet=[annual_fact(13)],
    )
    f = p["historical"][-1]["fields"]
    assert f["capex"]["value"] == 42
    assert f["d_and_a"]["value"] == 13
    assert f["capex"]["provenance"]["tag"] == "PaymentsToAcquireProductiveAssets"


def test_preferred_equity_derives_from_reported_equity_subtotals():
    p = build_with(
        StockholdersEquity=[
            dict(annual_fact(400), start=None),
            dict(annual_fact(400), start=None),
            dict(annual_fact(400), start=None),
        ],
        CommonStockEquity=[dict(annual_fact(400), start=None)],
    )
    bridge = p["bridge"]["preferred_equity"]
    assert bridge["value"] == 0
    assert bridge["provenance"]["formula"] == "stockholders equity minus common equity"


def test_preferred_derivation_rejects_mismatched_filings():
    p = build_with(
        StockholdersEquity=[dict(annual_fact(400), start=None, accn="A")],
        CommonStockEquity=[dict(annual_fact(400), start=None, accn="B")],
    )
    assert p["bridge"]["preferred_equity"] is None


def test_consolidated_only_conflict_value_is_rejected_when_parent_differs():
    accn = "0000320193-25-000001"
    rows = [
        observation("revenue", 100),
        dict(observation("net_income", 4873), source_record_id=accn),
        dict(observation("net_income", 4874), source_record_id=accn),
    ]
    facts = _tag_facts(
        "2025-09-27",
        "2024-09-29",
        "2025-10-31",
        accn,
        [("NetIncomeLoss", 4863), ("ProfitLoss", 4873)],
    )
    with pytest.raises(ProviderError, match="Conflicting"):
        build_packet("AAPL", "0000320193", rows, facts, "2026-10-07", {})


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


def test_served_numeric_strings_are_rejected():
    p = packet()
    p["historical"][-1]["fields"]["revenue"]["value"] = "120"
    with pytest.raises(ProviderError, match="numeric"):
        validate_packet(p, "AAPL", "2026-10-07")


def test_overlay_retains_common_earnings_for_pe_and_ordinary_market_equity_for_wacc():
    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    p = packet()
    for row, h in zip(d["historical"], p["historical"]):
        row["period_end"] = h["period_end"]
    d["bridge"]["as_of"] = p["historical"][-1]["period_end"]
    f = deepcopy(p["historical"][-1]["fields"]["revenue"])
    f["value"] = 999
    p["historical"][-1]["fields"]["net_income"] = f
    shares = deepcopy(f)
    shares.update(value=200, unit="shares")
    p["diluted_shares"] = shares
    d["source"]["capital_costs"] = {
        "market_equity_value": 5000,
        "equity_market_value": 5000,
        "equity_shares_as_of": "2025-09-30",
        "debt": 200,
        "reported_cost_of_debt": 0.04,
    }
    updated = apply_packet(d, p, "2026-10-07")
    assert updated["historical"][-1]["net_income"] == d["historical"][-1]["net_income"]
    assert updated["market"]["diluted_shares"] == 200
    assert updated["source"]["capital_costs"]["market_equity_value"] == 5000
    assert updated["source"]["capital_costs"]["equity_market_value"] == 5000
    assert updated["source"]["capital_costs"]["equity_shares_as_of"] == "2025-09-30"


def test_enrichment_preserves_missing_dividends_and_newer_same_period_fields():
    from ppe_packets import enrich_packet
    old = packet()
    end = old['historical'][-1]['period_end']
    dividend = {'value': 3, 'period_end': end, 'available_at': '2026-01-01', 'unit': 'USD', 'provenance': {'provider': 'SEC'}}
    old['dividends'] = [dividend]
    old['historical'][-1]['fields']['ebit']['available_at'] = '2026-01-01'
    new = packet()
    new['historical'][-1]['fields']['ebit']['value'] = 999
    result = enrich_packet(old, new, '2026-10-10')
    assert result['dividends'] == [dividend]
    assert result['historical'][-1]['fields']['ebit']['value'] == 30
    assert new['dividends'] == []


def test_enrichment_does_not_carry_bridge_across_fiscal_periods():
    from ppe_packets import enrich_packet
    old = packet()
    new = packet()
    # Different issuer must fail before any evidence can be mixed.
    new['cik'] = '0000789019'
    with pytest.raises(ProviderError, match='issuer'):
        enrich_packet(old, new, '2026-10-10')


def test_cloud_statement_gaps_preserve_source_and_do_not_invent_common_income():
    from ppe_packets import supplement_statement_facts
    p = packet()
    old = {('2025-09-30', 'TotalRevenue'): (999, {'provider': 'baseline'})}
    result = supplement_statement_facts(old, ['2025-09-30'], p, 'AAPL', '2026-10-10')
    assert result['2025-09-30', 'OperatingIncome'][0] == 30
    assert result['2025-09-30', 'OperatingIncome'][1]['period_end'] == '2025-09-27'
    assert result['2025-09-30', 'OperatingIncome'][1]['provider'] == 'PPE SEC canonical'
    assert result['2025-09-30', 'TotalRevenue'][0] == 999
    assert ('2025-09-30', 'NetIncomeCommonStockholders') not in result
    assert ('2025-09-30', 'OperatingIncome') not in old


def test_unsupported_reported_tax_ratio_does_not_discard_other_sec_fields():
    p = packet()
    doc = demo_document()
    doc['company']['ticker'] = 'AAPL'
    doc['valuation_date'] = '2026-10-10'
    for row, source_row in zip(doc['historical'], p['historical']):
        row['period_end'] = source_row['period_end']
    doc['bridge']['as_of'] = p['historical'][-1]['period_end']
    baseline_tax = doc['historical'][-1]['tax_rate']
    p['historical'][-1]['fields']['tax_rate'] = {'value': -0.25,
        'period_end': p['historical'][-1]['period_end'], 'available_at': '2026-01-01',
        'unit': 'pure', 'provenance': {'provider': 'SEC companyfacts'}}
    result = apply_packet(doc, p, '2026-10-10')
    assert result['historical'][-1]['ebit'] == 30
    assert result['historical'][-1]['tax_rate'] == baseline_tax
    coverage = next(r for r in result['source']['field_coverage'] if r['field'].endswith('2025-09-27.tax_rate'))
    assert coverage['status'] == 'fallback'
    assert coverage['excluded_ppe_observation']['value'] == -0.25
    assert any('reported tax ratio' in w for w in result['source']['warnings'])


def test_enrichment_rejects_conflicting_values_at_same_availability_date():
    from ppe_packets import enrich_packet
    old, new = packet(), packet()
    new['historical'][-1]['fields']['ebit']['value'] = 999
    with pytest.raises(ProviderError, match='Conflicting published'):
        enrich_packet(old, new, '2026-10-10')


# --- Net income available to common shareholders (basic EPS numerator) ---


def annual_fact(value, filed="2025-10-31", form="10-K", accn="test", start="2024-09-29", end="2025-09-27"):
    return {"val": value, "start": start, "end": end, "filed": filed, "form": form, "accn": accn}


def sec_facts(cik=320193, **tags):
    return {"cik": cik, "facts": {"us-gaap": {t: {"units": {"USD": rows}} for t, rows in tags.items()}}}


def three_year_rows():
    return [
        observation(
            "revenue", 100 + i * 10, end=f"{y}-09-27", start=f"{y - 1}-09-29", available=f"{y}-10-31"
        )
        for i, y in enumerate([2023, 2024, 2025])
    ]


def build_with(cik=320193, **tags):
    return build_packet(
        "AAPL", "0000320193", three_year_rows(), sec_facts(cik=cik, **tags), "2026-10-07", {}
    )


def aligned_doc(p):
    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    d["valuation_date"] = "2026-10-10"
    for row, h in zip(d["historical"], p["historical"]):
        row["period_end"] = h["period_end"]
    d["bridge"]["as_of"] = p["historical"][-1]["period_end"]
    return d


def test_direct_basic_common_income_is_sourced_from_its_own_tag():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(150)],
        PreferredStockDividendsIncomeStatementImpact=[annual_fact(30)],
    )
    assert len(p["common_income"]) == 1
    assert p["common_income"][0]["value"] == 120
    assert p["common_income"][0]["period_end"] == "2025-09-27"
    assert "NetIncomeLossAvailableToCommonStockholdersBasic" in json.dumps(p["common_income"][0])


def test_consolidated_or_derived_income_never_becomes_common_income():
    # ProfitLoss includes noncontrolling interests; NetIncomeLoss is not the basic EPS numerator.
    assert build_with(ProfitLoss=[annual_fact(150)])["common_income"] == []
    assert build_with(NetIncomeLoss=[annual_fact(150)])["common_income"] == []
    # Preferred dividends alone do not establish common-shareholder income.
    assert build_with(PreferredStockDividendsIncomeStatementImpact=[annual_fact(10)])["common_income"] == []


def test_quarterly_common_income_is_ignored():
    quarter = annual_fact(40, start="2025-07-01", end="2025-09-27")
    assert build_with(NetIncomeLossAvailableToCommonStockholdersBasic=[quarter])["common_income"] == []


def test_unexplained_residual_rejects_direct_common_income():
    # Parent 150 vs direct 120 leaves 30 with no reported component: never forced into a match.
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(150)],
    )
    assert p["common_income"] == []


def test_components_from_another_filing_do_not_explain_residual():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120, accn="A")],
        NetIncomeLoss=[annual_fact(150, accn="A")],
        PreferredStockDividendsIncomeStatementImpact=[annual_fact(30, accn="B")],
    )
    assert p["common_income"] == []


def test_consolidated_parent_and_nci_explain_residual():
    # Caterpillar pattern: consolidated ProfitLoss parent, no NetIncomeLoss tag;
    # the same-filing NCI attribution bridges parent to the direct tag.
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(10335)],
        ProfitLoss=[annual_fact(10332)],
        NetIncomeLossAttributableToNoncontrollingInterest=[annual_fact(-3)],
    )
    assert len(p["common_income"]) == 1
    assert p["common_income"][0]["value"] == 10335
    assert p["common_income"][0]["provenance"]["bridge"] == "explained_by_nci_income"


def _adjustment_packet(**overrides):
    base = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
        OperatingIncomeLoss=[annual_fact(40)],
    )
    adj = base.get("adjustment_facts", {})
    if "ebit_probe" in overrides:
        adj.setdefault("ebit_facts", []).append(overrides.pop("ebit_probe"))
    adj.update(overrides)
    base["adjustment_facts"] = adj
    return base


def test_adjustment_evidence_rejects_wrong_issuer_bad_unit_and_taxonomy():
    p = _adjustment_packet(cik="0000000000")
    with pytest.raises(ProviderError, match="issuer mismatch"):
        validate_packet(p, "AAPL", "2026-10-07")
    # Two combined supplements with missing identifiers must never agree
    # with each other by default.
    p = _adjustment_packet()
    del p["adjustment_facts"]["cik"]
    p["cik"] = None
    with pytest.raises(ProviderError, match="issuer mismatch"):
        validate_packet(p, "AAPL", "2026-10-07")
    p = _adjustment_packet(taxonomy="ifrs-full")
    with pytest.raises(ProviderError, match="taxonomy"):
        validate_packet(p, "AAPL", "2026-10-07")
    p = _adjustment_packet()
    p["adjustment_facts"]["ebit_facts"][0]["unit"] = "EUR"
    with pytest.raises(ProviderError, match="not USD"):
        validate_packet(p, "AAPL", "2026-10-07")


def test_adjustment_evidence_rejects_bad_duration_dates_and_post_cutoff():
    p = _adjustment_packet()
    p["adjustment_facts"]["ebit_facts"][0]["period_start"] = "2025-07-01"
    with pytest.raises(ProviderError, match="not annual duration"):
        validate_packet(p, "AAPL", "2026-10-07")
    p = _adjustment_packet()
    p["adjustment_facts"]["ebit_facts"][0]["filed"] = "not-a-date"
    with pytest.raises(ProviderError, match="missing/invalid dates"):
        validate_packet(p, "AAPL", "2026-10-07")
    p = _adjustment_packet()
    p["adjustment_facts"]["ebit_facts"][0]["filed"] = "2026-11-01"
    with pytest.raises(ProviderError, match="after cutoff"):
        validate_packet(p, "AAPL", "2026-10-07")
    p = _adjustment_packet()
    p["adjustment_facts"]["ebit_facts"][0]["accession"] = ""
    with pytest.raises(ProviderError, match="receipt missing"):
        validate_packet(p, "AAPL", "2026-10-07")


def test_adjustment_evidence_rejects_contradictory_filing_context():
    from accounting_policy import build_adjustment_facts_from_companyfacts

    combined = {"cik": 320193, "facts": {"us-gaap": {}}}
    for tag, accn in (
        ("ImpairmentOfIntangibleAssetsExcludingGoodwill", "A"),
        ("OperatingIncomeLoss", "B"),
    ):
        combined["facts"]["us-gaap"][tag] = {
            "units": {"USD": [dict(annual_fact(10, accn=accn), tag=tag)]}
        }
    # The offline builder accepts per-tag facts; the packet boundary rejects
    # pairing an EBIT fact with another filing's adjustments.
    facts = build_adjustment_facts_from_companyfacts(
        "0000320193", ["2025-09-27"], combined, "2026-10-07"
    )
    assert facts["ebit_facts"] and facts["facts"]["intangible_impairment"]
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
    )
    p["adjustment_facts"] = facts
    with pytest.raises(ProviderError, match="contradicts"):
        validate_packet(p, "AAPL", "2026-10-07")


def test_nci_from_another_filing_does_not_explain_residual():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(10335, accn="A")],
        ProfitLoss=[annual_fact(10332, accn="A")],
        NetIncomeLossAttributableToNoncontrollingInterest=[annual_fact(-3, accn="B")],
    )
    assert p["common_income"] == []


def test_two_reported_components_explain_residual_exactly():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(150)],
        PreferredStockDividendsIncomeStatementImpact=[annual_fact(10)],
        ParticipatingSecuritiesDistributedAndUndistributedEarningsLossBasic=[annual_fact(20)],
    )
    row = p["common_income"][0]
    assert row["value"] == 120
    assert (
        row["provenance"]["bridge"]
        == "explained_by_preferred_dividends_plus_participating_securities"
    )


def test_validate_rejects_common_income_without_accepted_bridge():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
    )
    assert p["common_income"]
    p["common_income"][0]["provenance"]["bridge"] = "unexplained_residual"
    with pytest.raises(ProviderError, match="not verified"):
        validate_packet(p, "AAPL", "2026-10-07")


def test_amendment_after_cutoff_ignored_and_latest_amendment_used():
    rows = [
        annual_fact(120, filed="2025-10-31", accn="orig"),
        annual_fact(125, filed="2026-01-15", form="10-K/A", accn="amend"),
        annual_fact(999, filed="2026-11-01", form="10-K/A", accn="late"),
    ]
    p = build_with(NetIncomeLossAvailableToCommonStockholdersBasic=rows, NetIncomeLoss=rows)
    assert p["common_income"][0]["value"] == 125


def test_conflicting_common_income_facts_in_one_filing_are_rejected():
    rows = [annual_fact(120, accn="same"), annual_fact(121, accn="same")]
    with pytest.raises(ProviderError, match="Conflicting"):
        build_with(NetIncomeLossAvailableToCommonStockholdersBasic=rows)


def test_negative_common_income_is_preserved():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(-45)],
        NetIncomeLoss=[annual_fact(-45)],
    )
    assert p["common_income"][0]["value"] == -45


def test_common_income_with_wrong_cik_is_rejected():
    with pytest.raises(ProviderError):
        build_with(cik=1, NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)])


def test_apply_uses_direct_common_income_and_not_consolidated_income():
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(150)],
        PreferredStockDividendsIncomeStatementImpact=[annual_fact(30)],
    )
    d = aligned_doc(p)
    baseline = d["historical"][-1]["net_income"]
    updated = apply_packet(d, p, "2026-10-10")
    assert updated["historical"][-1]["net_income"] == 120

    q = build_with(ProfitLoss=[annual_fact(150)], NetIncomeLoss=[annual_fact(150)])
    kept = apply_packet(aligned_doc(q), q, "2026-10-10")
    assert kept["historical"][-1]["net_income"] == baseline


def test_enrichment_carries_common_income_and_accepts_legacy_packets():
    from ppe_packets import enrich_packet
    ci = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
    )["common_income"][0]
    old = packet()
    old["common_income"] = deepcopy([ci])
    assert enrich_packet(old, packet(), "2026-10-10")["common_income"] == [ci]
    legacy = packet()
    legacy.pop("common_income")
    new = packet()
    new["common_income"] = deepcopy([ci])
    assert enrich_packet(legacy, new, "2026-10-10")["common_income"] == [ci]


def test_supplement_fills_only_direct_common_income_gap():
    from ppe_packets import supplement_statement_facts
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
    )
    old = {("2025-09-30", "TotalRevenue"): (999, {"provider": "baseline"})}
    result = supplement_statement_facts(old, ["2025-09-30"], p, "AAPL", "2026-10-10")
    assert result["2025-09-30", "NetIncomeCommonStockholders"][0] == 120
    assert result["2025-09-30", "NetIncomeCommonStockholders"][1]["period_end"] == "2025-09-27"
    assert result["2025-09-30", "TotalRevenue"][0] == 999
    empty = supplement_statement_facts({}, ["2025-09-30"], build_with(), "AAPL", "2026-10-10")
    assert ("2025-09-30", "NetIncomeCommonStockholders") not in empty


def test_validate_accepts_missing_common_income_and_rejects_misaligned_periods():
    p = packet()
    p.pop("common_income")
    assert validate_packet(p, "AAPL", "2026-10-07") is p
    bad = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(120)],
        NetIncomeLoss=[annual_fact(120)],
    )
    bad["common_income"][0]["period_end"] = "2024-09-28"
    with pytest.raises(ProviderError, match="common income periods"):
        validate_packet(bad, "AAPL", "2026-10-07")


# --- Real SEC companyfacts (10-K-only subsets committed under tests/fixtures/sec) ---

REAL_FACTS = Path(__file__).parent / "fixtures" / "sec" / "common-income"
JPM_BRIDGE = "explained_by_preferred_stock_plus_participating_securities"


def real_packet(ticker, cik, years):
    facts = json.loads((REAL_FACTS / f"{ticker}.json").read_text())
    rows = [
        observation(
            "revenue", 1000 + i, end=f"{y}-12-31", start=f"{y - 1}-12-31", available=f"{y + 1}-03-01"
        )
        for i, y in enumerate(years)
    ]
    return build_packet(ticker, cik, rows, facts, "2026-10-07", {})


def real_doc(p):
    d = aligned_doc(p)
    d["company"]["ticker"] = p["ticker"]
    return d


def test_real_jpm_common_income_is_bridged_to_its_own_filing():
    p = real_packet("JPM", "0000019617", [2023, 2024, 2025])
    ci = p["common_income"]
    assert [r["period_end"] for r in ci] == ["2023-12-31", "2024-12-31", "2025-12-31"]
    assert [r["value"] for r in ci] == [47760000000, 56868000000, 55681000000]
    assert {r["provenance"]["bridge"] for r in ci} == {JPM_BRIDGE}
    assert {r["provenance"]["accession"] for r in ci} == {"0001628280-26-008131"}


def test_real_jpm_2009_2011_bridges_three_distinct_components_and_rejects_early_cutoff():
    # At the 2026-10-07 cutoff, the latest 10-K carrying 2009 (accession 0000019617-12-000163,
    # filed 2012-02-29) discloses preferred stock (1,327M), participating securities (515M),
    # and preferred redemption premium (1,112M), which bridge 11,728M - 8,774M = 2,954M.
    p = real_packet("JPM", "0000019617", [2009, 2010, 2011])
    ci = p["common_income"]
    assert [r["period_end"] for r in ci] == ["2009-12-31", "2010-12-31", "2011-12-31"]
    assert [r["value"] for r in ci] == [8774000000, 15764000000, 17568000000]
    assert ci[0]["provenance"]["bridge"] == (
        "explained_by_preferred_stock_plus_participating_securities_alt_plus_preferred_redemption_premium"
    )
    assert {r["provenance"]["accession"] for r in ci} == {
        "0000019617-12-000163",
        "0000019617-13-000221",
        "0000019617-14-000289",
    }
    # At the original 2009 filing cutoff (2010-03-01), accession 0000950123-10-016029 lacks
    # the tagged preferred and participating adjustments, so the gate fails closed.
    facts = json.loads((REAL_FACTS / "JPM.json").read_text())
    early = build_packet(
        "JPM",
        "0000019617",
        [observation("revenue", 1000, end="2009-12-31", start="2009-01-01", available="2010-02-24")],
        facts,
        "2010-03-01",
        {},
    )
    assert early["common_income"] == []


def test_synonymous_preferred_tags_are_never_summed_to_explain_residual():
    # Two tags from the same economic category (preferred_dividends and preferred_stock)
    # must never be summed together to match a residual.
    p = build_with(
        NetIncomeLossAvailableToCommonStockholdersBasic=[annual_fact(90)],
        NetIncomeLoss=[annual_fact(150)],
        PreferredStockDividendsIncomeStatementImpact=[annual_fact(30)],
        DividendsPreferredStock=[annual_fact(30)],
    )
    assert p["common_income"] == []


def test_sec_user_agent_rejects_placeholder_email(monkeypatch):
    from scripts.reconcile_common_income import sec_user_agent

    monkeypatch.setenv("EDGAR_IDENTITY", "Test User contact@example.com")
    with pytest.raises(ProviderError, match="truthful SEC User-Agent"):
        sec_user_agent()
    monkeypatch.setenv("EDGAR_IDENTITY", "Scott Switzer scswitzer@chapman.edu")
    assert sec_user_agent() == "Scott Switzer scswitzer@chapman.edu"


def test_real_bac_and_gs_preferred_reconciliations_are_accepted():
    bac = real_packet("BAC", "0000070858", [2023, 2024, 2025])
    assert [r["value"] for r in bac["common_income"]] == [24656000000, 25344000000, 29055000000]
    assert {r["provenance"]["accession"] for r in bac["common_income"]} == {"0000070858-26-000157"}
    gs = real_packet("GS", "0000886982", [2023, 2024, 2025])
    assert [r["value"] for r in gs["common_income"]] == [7907000000, 13525000000, 16300000000]
    assert {r["provenance"]["bridge"] for r in gs["common_income"]} == {
        "explained_by_preferred_dividends"
    }


def test_real_citigroup_unexplained_residual_is_never_published():
    p = real_packet("C", "0000831001", [2023, 2024, 2025])
    assert p["common_income"] == []
    assert validate_packet(p, "C", "2026-10-07") is p


@pytest.mark.parametrize(
    "ticker,cik",
    [("AAPL", "0000320193"), ("KO", "0000021344"), ("MSFT", "0000789019"), ("XOM", "0000034088")],
)
def test_real_issuers_without_common_basic_tag_abstain(ticker, cik):
    p = real_packet(ticker, cik, [2023, 2024, 2025])
    assert p["common_income"] == []
    assert validate_packet(p, ticker, "2026-10-07") is p


def instant_fact(value, filed="2025-10-31", form="10-K", accn="test", end="2025-09-27"):
    return {"val": value, "end": end, "filed": filed, "form": form, "accn": accn}


def buildup_facts(end="2025-09-27", accn="test", **overrides):
    legs = {
        "StockholdersEquity": 18503,
        "CommonStockValue": 23,
        "AdditionalPaidInCapitalCommonStock": 4261,
        "RetainedEarningsAccumulatedDeficit": 70035,
        "AccumulatedOtherComprehensiveIncomeLossNetOfTax": -15534,
        "TreasuryStockValue": 40282,
    }
    legs.update(overrides)
    return sec_facts(
        **{tag: [instant_fact(value, accn=accn, end=end)] for tag, value in legs.items()}
    )


def test_preferred_from_common_buildup_reports_zero_with_filing_provenance():
    from ppe_packets import _sec_preferred_from_common_buildup

    field = _sec_preferred_from_common_buildup(buildup_facts(), "2025-09-27", "2026-10-07", {})
    assert field["value"] == 0.0
    assert field["provenance"]["accession"] == "test"
    assert "treasury stock" in field["provenance"]["formula"]


def test_preferred_from_common_buildup_reports_a_positive_residual():
    from ppe_packets import _sec_preferred_from_common_buildup

    field = _sec_preferred_from_common_buildup(
        buildup_facts(StockholdersEquity=18544), "2025-09-27", "2026-10-07", {}
    )
    assert field["value"] == 41.0


def test_preferred_from_common_buildup_rejects_split_filings():
    from ppe_packets import _sec_preferred_from_common_buildup

    facts = buildup_facts()
    facts["facts"]["us-gaap"]["TreasuryStockValue"]["units"]["USD"][0]["accn"] = "other"
    assert (
        _sec_preferred_from_common_buildup(facts, "2025-09-27", "2026-10-07", {}) is None
    )


def test_preferred_from_common_buildup_rejects_negative_residual_and_missing_legs():
    from ppe_packets import _sec_preferred_from_common_buildup

    assert (
        _sec_preferred_from_common_buildup(
            buildup_facts(StockholdersEquity=18000), "2025-09-27", "2026-10-07", {}
        )
        is None
    )
    facts = buildup_facts()
    del facts["facts"]["us-gaap"]["TreasuryStockValue"]
    assert (
        _sec_preferred_from_common_buildup(facts, "2025-09-27", "2026-10-07", {}) is None
    )


def test_preferred_buildup_accepts_combined_common_and_total_equity_legs():
    # Caterpillar pattern: no standalone StockholdersEquity, CommonStockValue
    # or APIC tags; SE derives as total including NCI less filed NCI (zero)
    # and common uses the combined tag. 2025-12-31 identities in one filing:
    # 21318 - 0 - (7181 + 65448 - 1772 - 49539) = 0.
    from ppe_packets import _sec_preferred_from_common_buildup

    legs = {
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": 21318,
        "MinorityInterest": 0,
        "CommonStocksIncludingAdditionalPaidInCapital": 7181,
        "RetainedEarningsAccumulatedDeficit": 65448,
        "AccumulatedOtherComprehensiveIncomeLossNetOfTax": -1772,
        "TreasuryStockValue": 49539,
    }
    facts = sec_facts(
        **{tag: [instant_fact(value)] for tag, value in legs.items()}
    )
    field = _sec_preferred_from_common_buildup(facts, "2025-09-27", "2026-10-07", {})
    assert field["value"] == 0.0
    assert field["provenance"]["accession"] == "test"
    assert "CommonStocksIncludingAdditionalPaidInCapital" in field["provenance"]["part_tags"]


def test_preferred_buildup_rejects_split_variant_filings():
    from ppe_packets import _sec_preferred_from_common_buildup

    legs = {
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": 21318,
        "MinorityInterest": 0,
        "CommonStocksIncludingAdditionalPaidInCapital": 7181,
        "RetainedEarningsAccumulatedDeficit": 65448,
        "AccumulatedOtherComprehensiveIncomeLossNetOfTax": -1772,
        "TreasuryStockValue": 49539,
    }
    facts = sec_facts(
        **{tag: [instant_fact(value)] for tag, value in legs.items()}
    )
    facts["facts"]["us-gaap"]["MinorityInterest"]["units"]["USD"][0]["accn"] = "other"
    assert _sec_preferred_from_common_buildup(facts, "2025-09-27", "2026-10-07", {}) is None


def test_short_term_debt_accepts_maturity_schedule_variant():
    # Caterpillar pattern: no LongTermDebtCurrent tag; current maturities come
    # from the disclosed next-twelve-months repayment schedule.
    p = build_with(
        ShortTermBorrowings=[instant_fact(5514)],
        LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths=[instant_fact(7120)],
    )
    debt = p["bridge"]["short_term_debt"]
    assert debt["value"] == 5514 + 7120


def test_packet_bridge_uses_common_buildup_when_common_equity_tag_is_absent():
    merged = {"cik": 320193, "facts": {"us-gaap": {}}}
    for end in ("2023-09-27", "2024-09-27", "2025-09-27"):
        for tag, rows in buildup_facts(end=end)["facts"]["us-gaap"].items():
            merged["facts"]["us-gaap"].setdefault(tag, {"units": {"USD": []}})["units"][
                "USD"
            ].extend(rows["units"]["USD"])
    p = build_packet(
        "AAPL", "0000320193", three_year_rows(), merged, "2026-10-07", {}
    )
    assert p["bridge"]["preferred_equity"]["value"] == 0.0
    assert "treasury stock" in p["bridge"]["preferred_equity"]["provenance"]["formula"]


def test_real_jpm_common_income_flows_to_model_and_supplement():
    from ppe_packets import supplement_statement_facts
    p = real_packet("JPM", "0000019617", [2023, 2024, 2025])
    updated = apply_packet(real_doc(p), p, "2026-10-10")
    assert updated["historical"][-1]["net_income"] == 55681000000
    result = supplement_statement_facts({}, ["2025-12-31"], p, "JPM", "2026-10-10")
    assert result["2025-12-31", "NetIncomeCommonStockholders"][0] == 55681000000
    assert result["2025-12-31", "NetIncomeCommonStockholders"][1]["period_end"] == "2025-12-31"
