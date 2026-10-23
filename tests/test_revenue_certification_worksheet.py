import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_revenue_certification_worksheet import (
    annual_facts,
    open_questions,
    pick_year_variants,
    propose_mapping,
)

ROOT = Path(__file__).parents[1]
WORKSHEET = ROOT / "docs/revenue-certification-2026-10-22.json"


def fact(value, end="2025-12-31", start="2025-01-01", form="10-K", fp="FY", filed="2026-02-01", accn="a-25-1"):
    return {
        "start": start,
        "end": end,
        "val": value,
        "form": form,
        "fp": fp,
        "filed": filed,
        "accn": accn,
    }


def payload(**tags):
    return {"facts": {"us-gaap": {tag: {"units": {"USD": rows}} for tag, rows in tags.items()}}}


def test_annual_facts_keeps_only_10k_fiscal_years():
    data = payload(
        Revenues=[
            fact(100),
            fact(90, form="10-Q", fp="Q4"),
            fact(80, start="2025-03-01", end="2025-12-31", accn="short"),
        ]
    )
    rows = annual_facts(data, "Revenues", since="2016-01-01")
    assert [row["value"] for row in rows] == ["100"]
    assert rows[0]["form"] == "10-K"


def test_annual_facts_applies_the_window():
    data = payload(Revenues=[fact(100, end="2010-12-31", start="2010-01-01")])
    assert annual_facts(data, "Revenues", since="2016-01-01") == []


def test_latest_filing_wins_and_a_restatement_is_reported():
    rows = [
        {
            "end": "2023-12-31",
            "value": "67954000000",
            "filed": "2024-02-02",
            "accession": "0000040545-24-000027",
            "form": "10-K",
        },
        {
            "end": "2023-12-31",
            "value": "35348000000",
            "filed": "2025-02-03",
            "accession": "0000040545-25-000015",
            "form": "10-K",
        },
    ]
    latest, variants, conflicts = pick_year_variants(rows)
    assert latest["value"] == "35348000000"
    assert len(variants) == 2
    assert len(conflicts) == 1
    assert "0000040545-24-000027" in conflicts[0]
    assert "0000040545-25-000015" in conflicts[0]


def test_a_single_filing_has_no_conflict():
    latest, _, conflicts = pick_year_variants(
        [{"end": "2025-12-31", "value": "1", "filed": "2026-01-01", "accession": "x", "form": "10-K"}]
    )
    assert latest["value"] == "1"
    assert conflicts == []


def empty_concepts():
    return {
        tag: []
        for tag in (
            "Revenues",
            "RevenuesNetOfInterestExpense",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "PremiumsEarnedNet",
            "InterestAndDividendIncomeOperating",
            "PolicyholderBenefitsAndClaimsIncurredNet",
            "LoansAndLeasesReceivableNetReportedAmount",
        )
    }


def test_net_of_interest_revenue_proposes_a_bank_family():
    extract = {"entity_name": "Fixture Bank", "concepts": empty_concepts()}
    extract["concepts"]["RevenuesNetOfInterestExpense"] = [
        {"end": "2025-12-31", "value": "100", "filed": "2026-01-01", "accession": "a", "form": "10-K"}
    ]
    mapping = propose_mapping(extract, ["2025-12-31"], current_evidence=[])
    assert mapping["statement_family"] == "BANK_NET_REVENUE"
    assert mapping["primary_concept"] == "RevenuesNetOfInterestExpense"
    assert mapping["status"] == "PROPOSED_NOT_CERTIFIED"


def test_premiums_propose_an_insurer_total_with_a_component():
    extract = {"entity_name": "Fixture Insurer", "concepts": empty_concepts()}
    for tag in ("Revenues", "PremiumsEarnedNet"):
        extract["concepts"][tag] = [
            {"end": "2025-12-31", "value": "100", "filed": "2026-01-01", "accession": "a", "form": "10-K"}
        ]
    mapping = propose_mapping(extract, ["2025-12-31"], current_evidence=["PremiumsEarnedNet"])
    assert mapping["statement_family"] == "INSURER_TOTAL_REVENUE"
    assert mapping["primary_concept"] == "Revenues"
    assert mapping["component_concept"] == "PremiumsEarnedNet"


def test_current_lending_evidence_with_total_revenues_proposes_a_bank_total():
    extract = {"entity_name": "Fixture Bank", "concepts": empty_concepts()}
    extract["concepts"]["Revenues"] = [
        {"end": "2025-12-31", "value": "100", "filed": "2026-01-01", "accession": "a", "form": "10-K"}
    ]
    mapping = propose_mapping(extract, ["2025-12-31"], current_evidence=["InterestAndDividendIncomeOperating"])
    assert mapping["statement_family"] == "BANK_TOTAL_REVENUE"
    assert mapping["primary_concept"] == "Revenues"


def test_investment_bank_with_both_concepts_equal_is_not_flagged_as_a_conflict():
    mapping = {
        "statement_family": "BANK_NET_REVENUE",
        "candidate_concepts_with_values": ["Revenues", "RevenuesNetOfInterestExpense"],
        "candidate_values": {"Revenues": "100", "RevenuesNetOfInterestExpense": "100"},
        "single_candidate": False,
        "latest_period": "2025-12-31",
    }
    questions = open_questions(mapping, [], [], has_conflicts=False)
    assert not any("values differ" in question for question in questions)


def test_conflicting_values_add_a_specific_question():
    mapping = {
        "statement_family": "BANK_NET_REVENUE",
        "candidate_concepts_with_values": ["Revenues", "RevenuesNetOfInterestExpense"],
        "candidate_values": {"Revenues": "120", "RevenuesNetOfInterestExpense": "100"},
        "single_candidate": False,
        "latest_period": "2025-12-31",
    }
    questions = open_questions(mapping, [], [], has_conflicts=False)
    assert any("values differ" in question for question in questions)


def test_committed_worksheet_keeps_every_mapping_uncertified():
    document = json.loads(WORKSHEET.read_text())
    assert {issuer["ticker"] for issuer in document["issuers"]} == {"GE", "ALL", "C", "GS", "JPM"}
    for issuer in document["issuers"]:
        mapping = issuer["proposed_mapping"]
        assert mapping["status"] == "PROPOSED_NOT_CERTIFIED"
        assert mapping["latest_primary_value"]
        assert mapping["certification_required"]
    assert {issuer["ticker"]: issuer["proposed_mapping"]["statement_family"] for issuer in document["issuers"]} == {
        "GE": "GENERAL_TOTAL_REVENUE",
        "ALL": "INSURER_TOTAL_REVENUE",
        "C": "BANK_TOTAL_REVENUE",
        "GS": "BANK_NET_REVENUE",
        "JPM": "BANK_NET_REVENUE",
    }


def test_committed_worksheet_preserves_the_ge_restatement():
    document = json.loads(WORKSHEET.read_text())
    ge = next(issuer for issuer in document["issuers"] if issuer["ticker"] == "GE")
    conflict = next(row["conflicts"][0] for row in ge["per_period"] if row["conflicts"])
    assert "67954000000" in conflict
    assert "35348000000" in conflict
    assert ge["evidence_historical_only"] == []


def test_committed_worksheet_records_current_insurer_and_bank_evidence():
    document = json.loads(WORKSHEET.read_text())
    by_ticker = {issuer["ticker"]: issuer for issuer in document["issuers"]}
    assert "PremiumsEarnedNet" in by_ticker["ALL"]["evidence_in_latest_period"]
    assert "InterestAndDividendIncomeOperating" in by_ticker["C"]["evidence_in_latest_period"]
    assert by_ticker["JPM"]["proposed_mapping"]["candidate_values"]["Revenues"] == (
        by_ticker["JPM"]["proposed_mapping"]["candidate_values"]["RevenuesNetOfInterestExpense"]
    )
