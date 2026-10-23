import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_identity_receipts import (
    ReceiptError,
    extract_cover_classes,
    normalize_ticker,
    statement_family,
    ticker_class,
    verify_succession,
)

ROOT = Path(__file__).parents[1]
RECEIPTS = ROOT / "docs/identity-receipts-2026-10-22.json"


def filing(form, accession, date="2026-01-01", document="doc.htm", period="2025-12-31"):
    return {
        "form": form,
        "accession": accession,
        "filing_date": date,
        "document": document,
        "period": period,
        "items": "",
    }


def test_statement_family_comes_from_the_annual_form_only():
    assert statement_family(["10-K", "8-K", "4"])["family"] == "DOMESTIC_10K"
    assert statement_family(["20-F", "6-K"])["family"] == "FOREIGN_PRIVATE_ISSUER"
    assert statement_family(["40-F"])["family"] == "FOREIGN_PRIVATE_ISSUER"
    assert statement_family(["8-K", "4"])["family"] == "NO_ANNUAL_REPORT_FOUND"
    mixed = statement_family(["10-K", "20-F"])
    assert mixed["family"] == "AMBIGUOUS_MIXED_FORMS"
    assert mixed["counts"] == {"10-K": 1, "20-F": 1, "40-F": 0}


def test_ticker_class_uses_only_the_suffix():
    assert ticker_class("BRK-A") == "A"
    assert ticker_class("GOOGL") == "UNMARKED"


def test_ticker_notation_normalizes_across_filings():
    assert normalize_ticker("BRK-A") == normalize_ticker("BRK.A") == normalize_ticker("BRK/A")
    assert normalize_ticker("ORCL") == "ORCL"
    assert normalize_ticker("ORCL-PD") != normalize_ticker("ORCL")


def test_cover_columns_pair_each_symbol_with_its_own_class():
    # Berkshire prints every title, then every symbol; the bond rows must not
    # shift the class assignment.
    document = """
    <table>
      <tr>
        <td>
          <p>Class A Common Stock</p><p>Class B Common Stock</p>
          <p>1.125% Senior Notes due 2027</p><p>2.625% Senior Notes due 2059</p>
        </td><td></td>
        <td>
          <p>BRK.A</p><p>BRK.B</p><p>BRK27</p><p>BRK59</p>
        </td><td></td>
        <td>
          <p>New York Stock Exchange</p><p>New York Stock Exchange</p>
          <p>New York Stock Exchange</p><p>New York Stock Exchange</p>
        </td>
      </tr>
    </table>
    """
    mappings = extract_cover_classes(document, "Class A Common Stock Class B Common Stock BRK.A BRK.B", ["BRK-A", "BRK-B"])
    assert mappings["BRK-A"]["class_title"] == "Class A Common Stock"
    assert mappings["BRK-A"]["method"] == "cover_table_columns"
    assert mappings["BRK-B"]["class_title"] == "Class B Common Stock"


def test_cover_adjacency_resolves_a_single_row_per_class():
    document = """
    <table><tr>
      <td><p>Class A Common Stock, $0.001 par value</p></td>
      <td><p>GOOGL</p></td>
      <td><p>Nasdaq Stock Market LLC</p></td>
    </tr></table>
    """
    text = "Securities registered pursuant to Section 12(b): Class A Common Stock, $0.001 par value GOOGL Nasdaq"
    mappings = extract_cover_classes(document, text, ["GOOGL"])
    assert mappings["GOOGL"]["class_title"] == "Class A Common Stock, $0.001 par value"
    assert mappings["GOOGL"]["letter"] == "A"


def test_a_symbol_only_in_xbrl_metadata_does_not_shadow_the_cover_page():
    # ORCL occurs first inside the XBRL header, where no class title precedes it.
    document = "<table><tr><td><p>Common Stock, par value $0.01 per share</p></td><td><p>ORCL</p></td></tr></table>"
    text = "10-K false FY 0001341439 ORCL 2025 Securities registered Common Stock, par value $0.01 per share ORCL"
    mappings = extract_cover_classes(document, text, ["ORCL"])
    assert mappings["ORCL"]["class_title"] == "Common Stock, par value $0.01 per share"


def test_an_unstated_class_stays_unresolved():
    mappings = extract_cover_classes("<table></table>", "nothing useful here", ["V"])
    assert mappings["V"] == {"class_title": None, "excerpt": "", "method": "not_found"}


def succession_fixture():
    successor = {
        "cik": "0002115436",
        "name": "ExxonMobil Holdings Corp",
        "filings": [filing("8-K12B", "0001193125-26-291990", "2026-07-01")],
    }
    predecessor = {
        "cik": "0000034088",
        "name": "EXXON MOBIL CORP",
        "filings": [
            filing("10-K", "0000034088-26-000045", "2026-02-18"),
            filing("10-Q", "0000034088-26-000093", "2026-08-03"),
        ],
    }
    edge = {
        "accession": "0001193125-26-291990",
        "filed": "2026-07-01",
        "document_url": "https://www.sec.gov/Archives/edgar/data/2115436/000119312526291990/d71068d8k12b.htm",
        "document_sha256": "a" * 64,
        "excerpt": (
            "On July 1, 2026, Exxon Mobil Corporation, a New Jersey corporation and the "
            "predecessor registrant, completed its redomiciliation. This report establishes "
            "ExxonMobil Holdings Corporation as the successor registrant of ExxonMobil's common stock."
        ),
    }
    return successor, predecessor, edge


def test_verified_succession_records_the_shared_accession():
    successor, predecessor, edge = succession_fixture()
    result = verify_succession(successor, predecessor, edge)
    assert result["verified"] is True
    assert result["predecessor_cik"] == "0000034088"
    assert result["shared_accessions"] == []
    assert result["document_sha256"] == "a" * 64


def test_succession_without_the_registration_accession_is_rejected():
    successor, predecessor, edge = succession_fixture()
    successor["filings"] = [filing("8-K", "0002115436-26-000013", "2026-10-16")]
    with pytest.raises(ReceiptError, match="8-K12B"):
        verify_succession(successor, predecessor, edge)


def test_succession_note_must_name_the_predecessor():
    successor, predecessor, edge = succession_fixture()
    edge["excerpt"] = "This report establishes ExxonMobil Holdings Corporation as the successor registrant."
    with pytest.raises(ReceiptError, match="predecessor"):
        verify_succession(successor, predecessor, edge)


def test_succession_note_must_say_successor_registrant():
    successor, predecessor, edge = succession_fixture()
    edge["excerpt"] = "Exxon Mobil Corporation completed a redomiciliation merger on July 1, 2026."
    with pytest.raises(ReceiptError, match="successor registrant"):
        verify_succession(successor, predecessor, edge)


def test_committed_receipts_cover_every_named_listing():
    document = json.loads(RECEIPTS.read_text())
    tickers = {row["ticker"] for row in document["listings"]}
    assert len(tickers) == 14
    assert document["unresolved_share_classes"] == []
    assert len(document["issuers"]) == 12


def test_committed_receipts_resolve_share_classes_from_the_cover_page():
    document = json.loads(RECEIPTS.read_text())
    by_ticker = {row["ticker"]: row for row in document["listings"]}
    assert by_ticker["GOOG"]["share_class"]["class_title"].startswith("Class C")
    assert by_ticker["GOOGL"]["share_class"]["class_title"].startswith("Class A")
    assert by_ticker["BRK-A"]["share_class"]["class_title"] == "Class A Common Stock"
    assert by_ticker["BRK-B"]["share_class"]["class_title"] == "Class B Common Stock"
    for row in document["listings"]:
        assert row["share_class"]["source"] == "annual_report_cover_page"
        assert row["share_class"]["document_sha256"]


def test_committed_receipts_record_the_exxon_entity_transition():
    document = json.loads(RECEIPTS.read_text())
    xom = next(row for row in document["listings"] if row["ticker"] == "XOM")
    assert xom["cik"] == "0002115436"
    assert xom["statement_family"]["family"] == "NO_ANNUAL_REPORT_FOUND"
    succession = xom["succession"]
    assert succession["verified"] is True
    assert succession["predecessor_cik"] == "0000034088"
    assert succession["predecessor_latest_annual_report"]["form"] == "10-K"
    assert succession["predecessor_latest_annual_report"]["period"] == "2025-12-31"
    assert "Exxon Mobil Corporation" in succession["excerpt"]
