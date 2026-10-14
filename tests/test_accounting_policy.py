"""Accounting-policy layer: source-backed normalization, never silent repair."""

import json
import unittest
from copy import deepcopy
from pathlib import Path

from accounting_policy import (
    apply_policy,
    fetch_adjustment_facts,
    provider_convention_notes,
    rou_treatment,
)
from dcf_loader import ProviderError


FIXTURE = json.loads(
    Path(__file__).parent.joinpath("fixtures/sec/adjustments-pep.json").read_text()
)


class FixtureHTTP:
    """Serve frozen companyconcept payloads by tag; 404 otherwise."""

    def get(self, url, **kwargs):
        tag = url.rsplit("/", 1)[-1].replace(".json", "")
        if tag in FIXTURE:
            return deepcopy(FIXTURE[tag])
        raise ProviderError("Data provider returned HTTP 404.")


def demo_doc():
    from dcf_loader import demo_document

    return demo_document()


class FetchTests(unittest.TestCase):
    def test_pep_impairment_facts_match_filing(self):
        periods = ["2023-12-30", "2024-12-28", "2025-12-27"]
        result = fetch_adjustment_facts("0000077476", periods, FixtureHTTP())
        intangible = {
            f["period_end"]: f["amount"] for f in result["facts"]["intangible_impairment"]
        }
        # Filed 10-K income-statement line: 927M / 33M / 1,993M.
        self.assertEqual(intangible["2023-12-30"], 927000000)
        self.assertEqual(intangible["2024-12-28"], 33000000)
        self.assertEqual(intangible["2025-12-27"], 1993000000)
        for fact in result["facts"]["intangible_impairment"]:
            self.assertEqual(fact["accession"], "0000077476-26-000007")
            self.assertEqual(fact["unit"], "USD")
        self.assertEqual(result["unavailable"], [])

    def test_missing_tag_is_unavailable_not_zero(self):
        class Empty(FixtureHTTP):
            def get(self, url, **kwargs):
                raise ProviderError("Data provider returned HTTP 404.")

        result = fetch_adjustment_facts("0000077476", ["2025-12-27"], Empty())
        self.assertEqual(result["facts"], {"intangible_impairment": [], "goodwill_impairment": []})
        self.assertEqual(len(result["unavailable"]), 2)
        # Absence must never read as a zero adjustment.
        _, ledger = apply_policy(demo_doc(), result, "normalize")
        self.assertEqual(ledger["adjustments"], [])

    def test_missing_cik_is_unavailable(self):
        result = fetch_adjustment_facts(None, ["2025-12-27"], FixtureHTTP())
        self.assertTrue(all(entry["reason"] == "CIK unavailable" for entry in result["unavailable"]))


PEP_PERIODS = ["2023-12-30", "2024-12-28", "2025-12-27"]


def pep_like_doc():
    """Demo observations re-dated to PEP's Saturday fiscal year-ends."""
    doc = demo_doc()
    for row, end in zip(doc["historical"], PEP_PERIODS):
        row["period_end"] = end
    return doc


class PolicyTests(unittest.TestCase):
    def _adjustments(self):
        return fetch_adjustment_facts("0000077476", PEP_PERIODS, FixtureHTTP())

    def test_reported_policy_changes_nothing(self):
        doc = pep_like_doc()
        before = [r["ebit"] for r in doc["historical"]]
        series, ledger = apply_policy(doc, self._adjustments(), "as_reported")
        self.assertIsNone(series)
        self.assertEqual([r["ebit"] for r in doc["historical"]], before)
        self.assertEqual(ledger["forecast_basis"], "reported_gaap")

    def test_recurrence_counts_all_three_pep_years(self):
        _, ledger = apply_policy(pep_like_doc(), self._adjustments(), "as_reported")
        # 927M, 33M and 1,993M: every loaded year carries an impairment.
        self.assertEqual(ledger["periods_with_impairment"], 3)
        self.assertIn("3 of 3", ledger["recurrence_note"])

    def test_normalize_adds_back_with_evidence(self):
        doc = pep_like_doc()
        adjusted, ledger = apply_policy(doc, self._adjustments(), "normalize")
        self.assertIsNotNone(adjusted)
        self.assertEqual(len(ledger["adjustments"]), 3)
        first = ledger["adjustments"][0]
        self.assertEqual(first["amount"], 927000000)
        self.assertEqual(
            first["adjusted_ebit"], doc["historical"][0]["ebit"] + 927000000
        )
        self.assertEqual(first["evidence"][0]["tag"], "ImpairmentOfIntangibleAssetsExcludingGoodwill")
        self.assertEqual(first["evidence"][0]["accession"], "0000077476-26-000007")
        # Source observations stay immutable.
        self.assertEqual(adjusted["historical"][0]["ebit"], doc["historical"][0]["ebit"] + 927000000)
        self.assertIn("tax", ledger["tax_note"].lower())

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            apply_policy(pep_like_doc(), self._adjustments(), "smooth")


KHC_FIXTURE = json.loads(
    Path(__file__).parent.joinpath("fixtures/sec/adjustments-khc.json").read_text()
)
KHC_PERIODS = ["2023-12-30", "2024-12-28", "2025-12-27"]


class KhcHTTP:
    def get(self, url, **kwargs):
        tag = url.rsplit("/", 1)[-1].replace(".json", "")
        if tag in KHC_FIXTURE:
            return deepcopy(KHC_FIXTURE[tag])
        raise ProviderError("Data provider returned HTTP 404.")


def khc_like_doc():
    doc = demo_doc()
    for row, end in zip(doc["historical"], KHC_PERIODS):
        row["period_end"] = end
    return doc


class SecondCompanyTests(unittest.TestCase):
    """KHC: heavy goodwill + intangible impairments, live-verified facts."""

    def test_khc_totals_combine_both_kinds(self):
        result = fetch_adjustment_facts("0001637459", KHC_PERIODS, KhcHTTP())
        _, ledger = apply_policy(khc_like_doc(), result, "normalize")
        by_end = {a["period_end"]: a["amount"] for a in ledger["adjustments"]}
        self.assertEqual(by_end["2023-12-30"], 152000000 + 510000000)
        self.assertEqual(by_end["2024-12-28"], 2031000000 + 1638000000)
        self.assertEqual(by_end["2025-12-27"], 2572000000 + 6734000000)
        kinds = {
            e["kind"]
            for a in ledger["adjustments"]
            for e in a["evidence"]
        }
        self.assertEqual(kinds, {"intangible_impairment", "goodwill_impairment"})
        self.assertEqual(ledger["periods_with_impairment"], 3)

    def test_aapl_live_filings_carry_no_impairment_facts(self):
        # Verified 2026-10-14 against data.sec.gov companyconcept: zero 10-K
        # facts for either impairment tag in FY2023-2025. The Empty path
        # (HTTP 404 -> unavailable, never zero) is that case in code.
        class Empty:
            def get(self, url, **kwargs):
                raise ProviderError("Data provider returned HTTP 404.")

        result = fetch_adjustment_facts(
            "0000320193", ["2023-09-30", "2024-09-28", "2025-09-27"], Empty()
        )
        _, ledger = apply_policy(demo_doc(), result, "normalize")
        self.assertEqual(ledger["adjustments"], [])
        self.assertEqual(ledger["periods_with_impairment"], 0)


class LeaseTests(unittest.TestCase):
    def test_rou_addback_blocked_without_bridge_liabilities(self):
        ruling = rou_treatment(demo_doc(), rou_amount=727000000)
        self.assertEqual(ruling["status"], "excluded")
        self.assertEqual(ruling["observed_rou_amortization"], 727000000)
        self.assertIn("no lease liabilities", ruling["reason"])


class ConventionTests(unittest.TestCase):
    def test_yahoo_docs_warned_incomparable(self):
        doc = demo_doc()
        doc["source"]["statement_source"] = "Yahoo"
        notes = provider_convention_notes(doc)
        self.assertEqual(len(notes), 1)
        self.assertIn("definitionally incomparable", notes[0])

    def test_sec_docs_carry_no_convention_warning(self):
        doc = demo_doc()
        doc["source"]["statement_source"] = "SEC-first"
        self.assertEqual(provider_convention_notes(doc), [])


class BriefBasisTests(unittest.TestCase):
    def test_brief_values_normalized_alternative_from_facts(self):
        from brief import build_brief

        doc = demo_doc()
        periods = [r["period_end"] for r in doc["historical"]]
        # Demo scale is revenue 1000 / ebit 200: modest charges keep margins valid.
        adjustments = {
            "facts": {
                "intangible_impairment": [
                    {
                        "period_end": periods[0],
                        "amount": 50.0,
                        "tag": "ImpairmentOfIntangibleAssetsExcludingGoodwill",
                        "accession": "0000000000-26-000001",
                        "filed": "2026-02-03",
                    },
                    {
                        "period_end": periods[2],
                        "amount": 80.0,
                        "tag": "ImpairmentOfIntangibleAssetsExcludingGoodwill",
                        "accession": "0000000000-26-000001",
                        "filed": "2026-02-03",
                    },
                ],
                "goodwill_impairment": [],
            },
            "unavailable": [],
        }
        doc["source"]["statement_source"] = "SEC-first"
        doc["source"]["accounting_adjustments"] = adjustments
        brief = build_brief(deepcopy(doc))
        basis = brief["accounting_basis"]
        self.assertEqual(basis["forecast_basis"], "reported_gaap")
        alt = basis["normalized_alternative"]
        self.assertIsNotNone(alt)
        self.assertGreater(alt["intrinsic_value"], brief["dcf"]["intrinsic_value"])
        self.assertIn("Not a truer price", alt["note"])
        self.assertTrue(basis["adjustments"])
        self.assertIn("review", basis["recurrence_note"].lower())

    def test_brief_without_facts_reports_unavailable(self):
        from brief import build_brief

        brief = build_brief(demo_doc())
        basis = brief["accounting_basis"]
        self.assertEqual(basis["forecast_basis"], "reported_gaap")
        self.assertIsNone(basis["normalized_alternative"])
        self.assertIn("cannot be valued", basis["recurrence_note"])


if __name__ == "__main__":
    unittest.main()
