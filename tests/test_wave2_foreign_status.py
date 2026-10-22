import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_wave2_foreign_status import (
    candidates,
    classify,
    form_counts,
    read_checked,
)


def test_domestic_10k_is_taxonomy_compatible():
    assert classify(["10-K"]) == ("DOMESTIC_10K", "US_GAAP_COMPATIBLE")


def test_foreign_private_issuer_forms_are_not_covered():
    assert classify(["20-F"]) == ("FOREIGN_PRIVATE_ISSUER_20F", "IFRS_NOT_COVERED")
    assert classify(["40-F"]) == ("FOREIGN_PRIVATE_ISSUER_40F", "IFRS_NOT_COVERED")
    assert classify(["20-F", "40-F"]) == (
        "FOREIGN_PRIVATE_ISSUER_MIXED",
        "IFRS_NOT_COVERED",
    )


def test_mixed_domestic_and_foreign_forms_need_review():
    assert classify(["10-K", "20-F"]) == ("MIXED_ANNUAL_FORMS", "REVIEW_MIXED_TAXONOMY")


def test_fund_annual_reports_are_recognised_without_being_modelled():
    assert classify(["N-CSR"]) == (
        "INVESTMENT_COMPANY_NCSR",
        "INVESTMENT_COMPANY_NOT_MODELLED",
    )


def test_a_fund_that_also_files_a_10k_is_classified_by_its_operating_statement():
    assert classify(["10-K", "N-CSR"]) == ("DOMESTIC_10K", "US_GAAP_COMPATIBLE")


def test_no_annual_report_is_unknown_not_domestic():
    assert classify([]) == ("NO_ANNUAL_FORM_IN_WINDOW", "UNKNOWN_NO_ANNUAL_REPORT")
    assert classify(["8-K", "4"]) == ("NO_ANNUAL_FORM_IN_WINDOW", "UNKNOWN_NO_ANNUAL_REPORT")


def test_form_counts_count_only_annual_forms_across_pages():
    pages = [
        {"filings": {"recent": {"form": ["10-K", "8-K", "N-CSR", "4"]}}},
        {"filings": {"recent": {"form": ["10-K", "20-F"]}}},
    ]
    counts = form_counts(pages)
    assert counts == {"10-K": 2, "20-F": 1, "40-F": 0, "N-CSR": 1}


def test_form_counts_stops_at_the_window():
    pages = [{"filings": {"recent": {"form": ["8-K"] * 10 + ["10-K"]}}}]
    assert form_counts(pages, limit=5) == {"10-K": 0, "20-F": 0, "40-F": 0, "N-CSR": 0}


def test_checkpoint_is_resumed_by_cik(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    first = {"cik": "0000000001", "foreign_status": "DOMESTIC_10K"}
    second = {"cik": "0000000002", "foreign_status": "FOREIGN_PRIVATE_ISSUER_20F"}
    path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n")
    checked = read_checked(path)
    assert set(checked) == {"0000000001", "0000000002"}
    assert checked["0000000002"]["foreign_status"] == "FOREIGN_PRIVATE_ISSUER_20F"


ROOT = Path(__file__).parents[1]
WAVE2 = ROOT / "docs/wave2-foreign-status-2026-10-22.json"


def test_committed_wave2_covers_every_candidate_listing():
    document = json.loads(WAVE2.read_text())
    summary = document["summary"]
    assert summary["issuers"] == 3665
    assert summary["listings"] == 3828
    assert summary["errors"] == 0
    assert sum(summary["by_status"].values()) == summary["listings"]
    assert summary["ifrs_listings"] == 844
    assert summary["investment_company_listings"] == 184


def test_engine_taxonomy_agrees_with_every_classification():
    document = json.loads(WAVE2.read_text())
    expected = {
        "DOMESTIC_10K": "US_GAAP_COMPATIBLE",
        "FOREIGN_PRIVATE_ISSUER_20F": "IFRS_NOT_COVERED",
        "FOREIGN_PRIVATE_ISSUER_40F": "IFRS_NOT_COVERED",
        "FOREIGN_PRIVATE_ISSUER_MIXED": "IFRS_NOT_COVERED",
        "INVESTMENT_COMPANY_NCSR": "INVESTMENT_COMPANY_NOT_MODELLED",
        "MIXED_ANNUAL_FORMS": "REVIEW_MIXED_TAXONOMY",
        "NO_ANNUAL_FORM_IN_WINDOW": "UNKNOWN_NO_ANNUAL_REPORT",
    }
    for listing in document["listings"]:
        assert listing["engine_taxonomy"] == expected[listing["foreign_status"]]


def test_wave2_does_not_pretend_to_know_adr_status():
    document = json.loads(WAVE2.read_text())
    assert document["listings"]
    for listing in document["listings"]:
        assert listing["adr_status"] == "UNKNOWN_NOT_IN_CONTRACTS"
        assert listing["sources"]


def test_wave2_csv_carries_the_same_rows_and_the_unknown_adr_column(tmp_path):
    path = ROOT / "docs/wave2-foreign-status-2026-10-22.csv"
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) == 3828
    assert "adr_status" in reader.fieldnames
    assert {row["adr_status"] for row in rows} == {"UNKNOWN_NOT_IN_CONTRACTS"}


def test_only_wave_two_rows_are_candidates(tmp_path):
    path = tmp_path / "proposal.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["tier", "status", "ticker", "cik", "company", "exchange"]
        )
        writer.writeheader()
        writer.writerow(
            {"tier": "TIER_1_NAMED", "status": "NAMED", "ticker": "XOM", "cik": "1", "company": "X", "exchange": "NYSE"}
        )
        writer.writerow(
            {"tier": "TIER_2_WAVE", "status": "NEW", "ticker": "AAA", "cik": "2", "company": "A", "exchange": "Nasdaq"}
        )
    rows = candidates(path)
    assert [row["ticker"] for row in rows] == ["AAA"]
