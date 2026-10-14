"""Accounting-policy layer: filing-grade validation, evidence-based labels."""

import json
import os
import unittest
from copy import deepcopy
from pathlib import Path

# SEC requires an identifying User-Agent; the credentials-absent case is
# exercised explicitly by patching the header builder.
os.environ.setdefault("EDGAR_IDENTITY", "Test Analyst test@example.invalid")

from accounting_policy import (
    apply_policy,
    audit_adjustments,
    classify_basis,
    comparability_note,
    fetch_adjustment_facts,
    rou_treatment,
)
from dcf_loader import ProviderError

FIXTURES = Path(__file__).parent.joinpath("fixtures/sec")
PEP_FIXTURE = json.loads(FIXTURES.joinpath("adjustments-pep.json").read_text())
KHC_FIXTURE = json.loads(FIXTURES.joinpath("adjustments-khc.json").read_text())

PEP_CIK = "0000077476"
PEP_PERIODS = ["2023-12-30", "2024-12-28", "2025-12-27"]
# Filed FY2025 10-K income statement: 11,986 / 12,887 / 11,498.
PEP_OPERATING_INCOME = [11986000000.0, 12887000000.0, 11498000000.0]
PEP_CHARGES = [927000000.0, 33000000.0, 1993000000.0]
PEP_AS_OF = "2026-10-14"


class Server:
    """Serve a payload map by tag; anything else is a 404."""

    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, url, **kwargs):
        tag = url.rsplit("/", 1)[-1].replace(".json", "")
        self.calls.append(tag)
        if tag in self.payloads:
            return deepcopy(self.payloads[tag])
        raise ProviderError("Data provider returned HTTP 404.")


def pep_server():
    return Server(PEP_FIXTURE)


def khc_server():
    return Server(KHC_FIXTURE)


def demo_doc(revenue=None, ebit=None, periods=None):
    from dcf_loader import demo_document

    doc = demo_document()
    for i, row in enumerate(doc["historical"]):
        if periods:
            row["period_end"] = periods[i]
        if revenue:
            row["revenue"] = revenue[i]
        if ebit:
            row["ebit"] = ebit[i]
    return doc


def sec_doc(ebit=None):
    """PEP-shaped SEC-first snapshot: EBIT equals filed operating income."""
    doc = demo_doc(
        revenue=[91471000000.0, 91854000000.0, 93925000000.0],
        ebit=ebit or PEP_OPERATING_INCOME,
        periods=PEP_PERIODS,
    )
    doc["source"]["statement_source"] = "SEC-first"
    for row in doc["historical"]:
        row["provenance"] = {
            "ebit": {
                "provider": "PPE SEC canonical",
                "quality_status": "REPORTED",
                "accession": "0000077476-26-000007",
                "period_start": "2024-12-29",
            }
        }
    return doc


def yahoo_doc():
    """Provider snapshot: EBIT equals filed operating income plus the charges."""
    return demo_doc(
        revenue=[91471000000.0, 91854000000.0, 93925000000.0],
        ebit=[oi + ch for oi, ch in zip(PEP_OPERATING_INCOME, PEP_CHARGES)],
        periods=PEP_PERIODS,
    )


def facts(server=None, include_ebit=True):
    return fetch_adjustment_facts(
        PEP_CIK, PEP_PERIODS, server or pep_server(), as_of=PEP_AS_OF, include_ebit=include_ebit
    )


class ExtractionTests(unittest.TestCase):
    def test_validated_pep_facts(self):
        result = facts()
        intangible = {f["period_end"]: f for f in result["facts"]["intangible_impairment"]}
        self.assertEqual(intangible["2025-12-27"]["amount"], 1993000000)
        for fact in intangible.values():
            self.assertEqual(fact["accession"], "0000077476-26-000007")
            self.assertEqual(fact["form"], "10-K")
            self.assertEqual(fact["unit"], "USD")
            self.assertTrue(fact["period_start"])
            self.assertEqual(fact["filed"], "2026-02-03")
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["unavailable"], [])

    def test_wrong_issuer_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            payload["cik"] = 320193
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"], {"intangible_impairment": [], "goodwill_impairment": []})
        self.assertTrue(result["unavailable"])
        self.assertTrue(all("does not match" in u["reason"] for u in result["unavailable"]))

    def test_wrong_taxonomy_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            payload["taxonomy"] = "ifrs-full"
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])
        self.assertTrue(all("not us-gaap" in u["reason"] for u in result["unavailable"]))

    def test_wrong_currency_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            payload["units"] = {"EUR": payload["units"]["USD"]}
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])
        self.assertTrue(all("no USD unit" in u["reason"] for u in result["unavailable"]))

    def test_quarterly_duration_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        payload = payloads["ImpairmentOfIntangibleAssetsExcludingGoodwill"]
        for fact in payload["units"]["USD"]:
            fact["start"] = "2025-09-28"  # 90 days before 2025-12-27
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])
        self.assertTrue(
            any("no validated annual 10-K fact" in u["reason"] for u in result["unavailable"])
        )

    def test_missing_duration_evidence_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            for fact in payload["units"]["USD"]:
                fact.pop("start", None)
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])

    def test_later_filed_restatement_excluded_and_reported(self):
        payloads = deepcopy(PEP_FIXTURE)
        payload = payloads["ImpairmentOfIntangibleAssetsExcludingGoodwill"]
        for fact in payload["units"]["USD"]:
            if fact["end"] == "2025-12-27":
                fact["filed"] = "2026-11-01"  # after the 2026-10-14 cutoff
                fact["val"] = 111
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        ends = {f["period_end"] for f in result["facts"]["intangible_impairment"]}
        self.assertNotIn("2025-12-27", ends)
        self.assertEqual(len(result["future_restatements"]), 1)
        self.assertIn("after the valuation cutoff", result["future_restatements"][0]["reason"])

    def test_contradictory_same_date_values_rejected(self):
        payloads = deepcopy(PEP_FIXTURE)
        payload = payloads["ImpairmentOfIntangibleAssetsExcludingGoodwill"]
        source = next(f for f in payload["units"]["USD"] if f["end"] == "2025-12-27")
        payload["units"]["USD"].append({**deepcopy(source), "val": 42})
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        ends = {f["period_end"] for f in result["facts"]["intangible_impairment"]}
        self.assertNotIn("2025-12-27", ends)
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertIn("contradictory", result["conflicts"][0]["reason"])

    def test_latest_filing_wins_and_amendment_flagged(self):
        payloads = deepcopy(PEP_FIXTURE)
        payload = payloads["ImpairmentOfIntangibleAssetsExcludingGoodwill"]
        original = next(f for f in payload["units"]["USD"] if f["end"] == "2025-12-27")
        payload["units"]["USD"].append(
            {
                **deepcopy(original),
                "val": 2000000000,
                "form": "10-K/A",
                "filed": "2026-06-01",
                "accn": "0000077476-26-000099",
            }
        )
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        fact = next(
            f for f in result["facts"]["intangible_impairment"] if f["period_end"] == "2025-12-27"
        )
        self.assertEqual(fact["amount"], 2000000000)
        self.assertEqual(fact["form"], "10-K/A")
        self.assertEqual(fact["accession"], "0000077476-26-000099")
        self.assertTrue(fact["restated"])

    def test_missing_credentials_is_unavailable_not_zero(self):
        import accounting_policy

        original = accounting_policy._headers
        accounting_policy._headers = lambda: None
        try:
            result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, pep_server(), as_of=PEP_AS_OF)
        finally:
            accounting_policy._headers = original
        self.assertEqual(result["facts"]["intangible_impairment"], [])
        self.assertTrue(
            all("EDGAR_IDENTITY" in u["reason"] for u in result["unavailable"])
        )

    def test_missing_cik_is_unavailable(self):
        result = fetch_adjustment_facts(None, PEP_PERIODS, pep_server(), as_of=PEP_AS_OF)
        self.assertEqual(result["unavailable"][0]["reason"], "issuer CIK unavailable")

    def test_ebit_tag_fetched_only_when_requested(self):
        server = pep_server()
        fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, server, as_of=PEP_AS_OF, include_ebit=False)
        self.assertNotIn("OperatingIncomeLoss", server.calls)
        server = pep_server()
        fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, server, as_of=PEP_AS_OF, include_ebit=True)
        self.assertIn("OperatingIncomeLoss", server.calls)


class EbitDefinitionTests(unittest.TestCase):
    def test_sec_doc_verified_includes_charges(self):
        audit = audit_adjustments(sec_doc(), facts())
        self.assertEqual(
            audit["ebit_definition"]["classification"], "gaap_operating_income_verified"
        )
        self.assertEqual(
            {p["verdict"] for p in audit["periods"]}, {"verified_addback"}
        )

    def test_provider_doc_verified_already_excludes_charges(self):
        audit = audit_adjustments(yahoo_doc(), facts())
        self.assertEqual(
            audit["ebit_definition"]["classification"],
            "charges_already_excluded_verified",
        )
        self.assertEqual(
            {p["verdict"] for p in audit["periods"]}, {"rejected_already_excluded"}
        )
        self.assertEqual(audit["addback_total"], 0)

    def test_unrelated_ebit_is_unverified_and_blocked(self):
        doc = sec_doc(ebit=[1.0, 2.0, 3.0])
        audit = audit_adjustments(doc, facts())
        self.assertEqual(audit["ebit_definition"]["classification"], "mixed_or_unverified")
        self.assertEqual({p["verdict"] for p in audit["periods"]}, {"rejected_unverified"})

    def test_overlapping_concepts_rejected_not_double_counted(self):
        import accounting_policy

        overlap = deepcopy(accounting_policy.ADJUSTMENT_TAGS)
        overlap["goodwill_impairment"]["overlaps"] = ("intangible_impairment",)
        original = accounting_policy.ADJUSTMENT_TAGS
        accounting_policy.ADJUSTMENT_TAGS = overlap
        try:
            result = facts()
            audit = audit_adjustments(sec_doc(), result)
        finally:
            accounting_policy.ADJUSTMENT_TAGS = original
        # Periods where both concepts match are rejected; a period with a
        # single concept (no overlap) still verifies normally.
        by_period = {p["period_end"]: p["verdict"] for p in audit["periods"] if p["amount"]}
        self.assertEqual(by_period["2024-12-28"], "overlap_rejected")
        self.assertEqual(by_period["2025-12-27"], "overlap_rejected")
        self.assertEqual(by_period["2023-12-30"], "verified_addback")
        self.assertEqual(audit["addback_total"], 927000000.0)


class PolicyTests(unittest.TestCase):
    def test_reported_policy_changes_nothing(self):
        doc = sec_doc()
        before = [r["ebit"] for r in doc["historical"]]
        series, ledger = apply_policy(doc, facts(), "as_reported")
        self.assertIsNone(series)
        self.assertEqual([r["ebit"] for r in doc["historical"]], before)
        self.assertEqual(ledger["forecast_basis"], "reported_gaap")
        self.assertEqual(ledger["adjustment_status"], "not_requested")

    def test_normalize_applies_only_verified_addbacks(self):
        doc = sec_doc()
        adjusted, ledger = apply_policy(doc, facts(), "normalize")
        self.assertIsNotNone(adjusted)
        self.assertEqual(len(ledger["adjustments"]), 3)
        self.assertEqual(ledger["adjustment_status"], "applied")
        self.assertEqual(adjusted["historical"][2]["ebit"], 11498000000.0 + 1993000000.0)
        # Reported observations are untouched.
        self.assertEqual(doc["historical"][2]["ebit"], 11498000000.0)
        self.assertEqual(adjusted["source"]["accounting_policy"], "normalize")

    def test_normalize_refuses_provider_basis(self):
        adjusted, ledger = apply_policy(yahoo_doc(), facts(), "normalize")
        self.assertIsNone(adjusted)
        self.assertEqual(ledger["adjustments"], [])
        self.assertEqual(ledger["adjustment_status"], "partial_or_unverified_evidence")
        self.assertEqual(ledger["rejected_total"], sum(PEP_CHARGES))

    def test_normalize_blocked_by_overlap_conflict(self):
        import accounting_policy

        overlap = deepcopy(accounting_policy.ADJUSTMENT_TAGS)
        overlap["goodwill_impairment"]["overlaps"] = ("intangible_impairment",)
        original = accounting_policy.ADJUSTMENT_TAGS
        accounting_policy.ADJUSTMENT_TAGS = overlap
        try:
            adjusted, ledger = apply_policy(sec_doc(), facts(), "normalize")
        finally:
            accounting_policy.ADJUSTMENT_TAGS = original
        # One period verifies alone, but the overlap conflict blocks the whole
        # normalized series: no partial-period normalization.
        self.assertIsNone(adjusted)
        self.assertEqual(ledger["adjustments"], [])
        self.assertEqual(ledger["adjustment_status"], "conflicted_evidence")

    def test_missing_filing_date_rejected(self):
        from accounting_policy import fetch_adjustment_facts

        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            for fact in payload["units"]["USD"]:
                fact.pop("filed", None)
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])
        self.assertTrue(
            any("no validated annual 10-K fact" in u["reason"] for u in result["unavailable"])
        )

    def test_missing_accession_rejected(self):
        from accounting_policy import fetch_adjustment_facts

        payloads = deepcopy(PEP_FIXTURE)
        for payload in payloads.values():
            for fact in payload["units"]["USD"]:
                fact.pop("accn", None)
        result = fetch_adjustment_facts(PEP_CIK, PEP_PERIODS, Server(payloads), as_of=PEP_AS_OF)
        self.assertEqual(result["facts"]["intangible_impairment"], [])

    def test_mismatched_filing_context_blocks_tieout(self):
        from accounting_policy import audit_adjustments

        result = facts()
        for fact in result["ebit_facts"]:
            fact["accession"] = "0000000000-00-000000"
        audit = audit_adjustments(sec_doc(), result)
        self.assertEqual(
            audit["ebit_definition"]["classification"], "mixed_or_unverified"
        )
        self.assertEqual(
            {p["verdict"] for p in audit["periods"] if p["amount"]},
            {"rejected_unverified"},
        )

    def test_offline_builder_rejects_mismatched_source_cik(self):
        from accounting_policy import build_adjustment_facts_from_companyfacts

        combined = {"cik": 320193, "facts": {"us-gaap": {}}}
        result = build_adjustment_facts_from_companyfacts(
            PEP_CIK, PEP_PERIODS, combined, PEP_AS_OF
        )
        self.assertEqual(result["facts"], {"intangible_impairment": [], "goodwill_impairment": []})
        self.assertTrue(any("does not match" in u["reason"] for u in result["unavailable"]))

    def test_offline_builder_matches_live_facts(self):
        from accounting_policy import build_adjustment_facts_from_companyfacts

        live = facts()
        combined = {"facts": {"us-gaap": {}}}
        for tag, payload in PEP_FIXTURE.items():
            combined["facts"]["us-gaap"][tag] = payload
        offline = build_adjustment_facts_from_companyfacts(
            PEP_CIK, PEP_PERIODS, combined, PEP_AS_OF
        )
        self.assertEqual(
            {f["period_end"]: f["amount"] for f in offline["facts"]["intangible_impairment"]},
            {f["period_end"]: f["amount"] for f in live["facts"]["intangible_impairment"]},
        )
        self.assertEqual(
            {f["period_end"]: f["amount"] for f in offline["ebit_facts"]},
            {f["period_end"]: f["amount"] for f in live["ebit_facts"]},
        )

    def test_all_period_recurrence_flagged(self):
        _, ledger = apply_policy(sec_doc(), facts(), "as_reported")
        self.assertEqual(ledger["periods_with_impairment"], 3)
        self.assertIn("3 of 3", ledger["recurrence_note"])
        self.assertIn("scenario", ledger["recurrence_note"])

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            apply_policy(sec_doc(), facts(), "smooth")

    def test_pep_and_khc_evidence(self):
        pep = facts()
        khc = fetch_adjustment_facts(
            "0001637459", PEP_PERIODS, khc_server(), as_of=PEP_AS_OF, include_ebit=True
        )
        pep_totals = {f["period_end"]: f["amount"] for f in pep["facts"]["intangible_impairment"]}
        self.assertEqual(pep_totals["2025-12-27"], 1993000000)
        khc_by_kind = {
            kind: {f["period_end"]: f["amount"] for f in items}
            for kind, items in khc["facts"].items()
        }
        self.assertEqual(khc_by_kind["intangible_impairment"]["2025-12-27"], 2572000000)
        self.assertEqual(khc_by_kind["goodwill_impairment"]["2025-12-27"], 6734000000)
        # KHC FY2025 filed operating income is negative; the raw fact is kept.
        fact = next(f for f in khc["ebit_facts"] if f["period_end"] == "2025-12-27")
        self.assertEqual(fact["amount"], -4669000000)


class LabelTests(unittest.TestCase):
    def test_sec_doc_labeled_verified_gaap(self):
        label = classify_basis(sec_doc())
        self.assertEqual(label["label"], "reported_gaap_verified")
        self.assertIn("0000077476-26-000007", label["evidence"]["accessions"])

    def test_provider_doc_labeled_provider_defined(self):
        doc = yahoo_doc()
        doc["source"]["statement_source"] = "Yahoo"
        label = classify_basis(doc)
        self.assertEqual(label["label"], "provider_defined")
        self.assertNotIn("GAAP", label["label"])

    def test_unlabeled_doc_not_called_gaap(self):
        label = classify_basis(demo_doc())
        self.assertEqual(label["label"], "mixed_or_unverified")

    def test_normalized_snapshot_labeled(self):
        doc = sec_doc()
        doc["source"]["accounting_policy"] = "normalize"
        self.assertEqual(classify_basis(doc)["label"], "normalized_adjusted")

    def test_comparability_unverified_without_reconciliation(self):
        note = comparability_note(yahoo_doc())
        self.assertEqual(note["status"], "unverified")
        self.assertIn("unverified", note["text"])
        self.assertNotIn("incomparable", note["text"])

    def test_comparability_verified_with_reconciliation(self):
        doc = yahoo_doc()
        doc["source"]["definition_reconciliation"] = {
            "verified": True,
            "summary": "filed reconciliation attached",
            "evidence": {"accession": "0000077476-26-000007"},
        }
        note = comparability_note(doc)
        self.assertEqual(note["status"], "verified_definition_difference")
        self.assertEqual(note["evidence"]["accession"], "0000077476-26-000007")


class LeaseTests(unittest.TestCase):
    def test_rou_addback_blocked_without_bridge_liabilities(self):
        ruling = rou_treatment(demo_doc(), rou_amount=727000000)
        self.assertEqual(ruling["status"], "excluded")
        self.assertEqual(ruling["observed_rou_amortization"], 727000000)
        self.assertIn("no lease liabilities", ruling["reason"])


class BriefBasisTests(unittest.TestCase):
    def _resolved(self, doc):
        doc["source"]["accounting_adjustments"] = {**facts(), "status": "resolved"}
        return doc

    def test_brief_never_calls_provider_data_gaap(self):
        from brief import build_brief

        doc = self._resolved(yahoo_doc())
        doc["source"]["statement_source"] = "Yahoo"
        basis = build_brief(deepcopy(doc))["accounting_basis"]
        self.assertEqual(basis["basis"], "provider_defined")
        self.assertEqual(basis["forecast_basis"], "provider_defined")
        self.assertIsNone(basis["normalized_alternative"])
        self.assertEqual(len(basis["rejected_adjustments"]), 3)
        self.assertIn("already excludes", basis["rejected_adjustments"][2]["reason"])

    def test_brief_sec_basis_verified_with_scenario(self):
        from brief import build_brief

        basis = build_brief(deepcopy(self._resolved(sec_doc())))["accounting_basis"]
        self.assertEqual(basis["basis"], "reported_gaap_verified")
        self.assertEqual(basis["ebit_definition"], "gaap_operating_income_verified")
        alt = basis["normalized_alternative"]
        self.assertIsNotNone(alt)
        self.assertGreater(alt["intrinsic_value"], 0)
        self.assertIn("not a truer price", alt["note"].lower())

    def test_brief_reports_pending_evidence(self):
        from brief import build_brief

        doc = sec_doc()
        doc["source"]["accounting_adjustments"] = {
            "schema_version": "accounting-adjustments-v1",
            "status": "pending",
            "facts": {},
            "ebit_facts": [],
            "unavailable": [{"kind": "all", "tag": None, "reason": "budget exhausted"}],
            "conflicts": [],
            "future_restatements": [],
        }
        basis = build_brief(deepcopy(doc))["accounting_basis"]
        self.assertEqual(basis["basis"], "reported_gaap_verified")
        self.assertIsNone(basis["normalized_alternative"])
        self.assertIn("pending", basis["recurrence_note"])

    def test_brief_normalized_alt_uses_edited_assumptions(self):
        from dataclasses import asdict
        from brief import build_brief
        from compare import coerce_dcf_assumptions

        doc = self._resolved(sec_doc())
        base = build_brief(deepcopy(doc))["accounting_basis"]
        self.assertEqual(base["normalized_alternative"]["assumptions_basis"], "baseline")
        assumptions, _ = coerce_dcf_assumptions(deepcopy(doc), None, 0.065)
        raw = asdict(assumptions)
        raw["revenue_growth_rates"] = [0.12] * 5
        custom = build_brief(deepcopy(doc), deepcopy(raw))["accounting_basis"]
        alt = custom["normalized_alternative"]
        self.assertIsNotNone(alt)
        self.assertEqual(alt["assumptions_basis"], "custom")
        self.assertNotEqual(alt["intrinsic_value"], base["normalized_alternative"]["intrinsic_value"])

    def test_sec_basis_requires_complete_per_period_provenance(self):
        from accounting_policy import classify_basis

        doc = sec_doc()
        for row in doc["historical"]:
            row["provenance"]["ebit"].pop("accession", None)
        self.assertEqual(classify_basis(doc)["label"], "mixed_or_unverified")

    def test_brief_without_evidence_reports_unavailable(self):
        from brief import build_brief

        basis = build_brief(demo_doc())["accounting_basis"]
        self.assertEqual(basis["basis"], "mixed_or_unverified")
        self.assertIsNone(basis["normalized_alternative"])
        self.assertIn("cannot be valued", basis["recurrence_note"])


if __name__ == "__main__":
    unittest.main()
