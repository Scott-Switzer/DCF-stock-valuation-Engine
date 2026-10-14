"""Instant Investment Research Brief: contract tests (no network)."""

import unittest
from copy import deepcopy


def demo():
    from dcf_loader import demo_document

    return demo_document()


class BuildBriefTests(unittest.TestCase):
    def test_brief_matches_evaluate_and_reverse(self):
        from brief import build_brief
        from app import evaluate
        from compare import coerce_dcf_assumptions
        from reverse_dcf import solve

        doc = demo()
        brief = build_brief(deepcopy(doc))
        self.assertEqual(brief["ticker"], doc["company"]["ticker"])
        assumptions, _ = coerce_dcf_assumptions(
            doc, None, (doc["source"].get("capital_costs", {}) or {}).get("wacc") or 0.065
        )
        expected = evaluate(deepcopy(doc), deepcopy(assumptions))
        self.assertAlmostEqual(brief["dcf"]["intrinsic_value"], expected["intrinsic_value"])
        self.assertAlmostEqual(brief["dcf"]["target_price_12m"], expected["target_price_12m"])
        self.assertAlmostEqual(brief["dcf"]["upside"], expected["upside"])
        self.assertEqual(
            [s["name"] for s in brief["scenarios"]], ["Bear", "Base", "Bull"]
        )
        for name, target in zip(["Bear", "Base", "Bull"], [s["target_price_12m"] for s in expected["scenarios"]]):
            got = next(s for s in brief["scenarios"] if s["name"] == name)
            self.assertEqual(got["target_price_12m"], target)
        for driver in ("revenue_growth", "ebit_margin"):
            solved = solve(deepcopy(doc), deepcopy(assumptions), doc["market"]["price"], driver)
            self.assertEqual(brief["market_implied"][driver]["status"], solved["status"])
            if solved["status"] == "solved":
                self.assertAlmostEqual(
                    brief["market_implied"][driver]["implied"], solved["implied"]
                )
        self.assertIn(brief["drivers"]["top"], {"discount rate (WACC)", "terminal growth", None})
        self.assertEqual(
            brief["freshness"]["period_ends"],
            [r["period_end"] for r in doc["historical"]],
        )
        self.assertTrue(brief["evidence"]["coverage_page"].endswith(f"/coverage/{brief['ticker']}"))

    def test_brief_uses_posted_assumptions(self):
        from brief import build_brief
        from compare import coerce_dcf_assumptions
        from dataclasses import asdict

        doc = demo()
        assumptions, custom = coerce_dcf_assumptions(doc, None, 0.065)
        raw = asdict(assumptions)
        raw["revenue_growth_rates"] = [0.10] * 5
        base = build_brief(deepcopy(doc))
        custom_brief = build_brief(deepcopy(doc), raw)
        self.assertTrue(custom_brief["assumptions"]["custom"])
        self.assertNotEqual(
            custom_brief["dcf"]["intrinsic_value"], base["dcf"]["intrinsic_value"]
        )
        self.assertEqual(custom_brief["assumptions"]["revenue_growth_mean"], 0.10)

    def test_analysis_fields_are_present_and_inspectable(self):
        from brief import build_brief

        brief = build_brief(demo())
        self.assertIsInstance(brief["terminal_share"], float)
        self.assertGreaterEqual(brief["terminal_share"], 0)
        self.assertLessEqual(brief["terminal_share"], 1)
        hist = brief["history_vs_baseline"]
        self.assertIsNotNone(hist["historical_revenue_cagr"])
        self.assertIsNotNone(hist["baseline_revenue_growth_mean"])
        specs = {s["name"]: s["spec"] for s in brief["scenarios"]}
        self.assertEqual(specs["Bear"]["revenue_growth_delta"], -0.02)
        self.assertEqual(specs["Bull"]["wacc_delta"], -0.01)
        self.assertEqual(specs["Base"]["ebit_margin_delta"], 0.0)

    def test_baseline_basis_label(self):
        from brief import build_brief

        brief = build_brief(demo())
        self.assertEqual(brief["basis"], "baseline")
        self.assertIn("Baseline", brief["basis_note"])

    def test_financial_firm_is_blocked_not_raised(self):
        from brief import build_brief

        doc = demo()
        doc["source"]["classification"] = {"status": "confirmed", "sic": "6021"}
        brief = build_brief(deepcopy(doc))
        self.assertIn("blocked", brief)
        self.assertIn("financial", brief["blocked"].lower())

    def test_invalid_snapshot_rejected(self):
        from brief import build_brief

        with self.assertRaises(ValueError):
            build_brief({"company": {"ticker": "X"}})


class BriefAssumptionSyncTests(unittest.TestCase):
    def test_custom_brief_matches_preview_accepted_state(self):
        # The live-sync contract: /api/brief fed the preview's accepted
        # financials + assumptions reproduces the preview's own figures.
        from dataclasses import asdict
        from app import evaluate
        from brief import build_brief
        from compare import coerce_dcf_assumptions

        doc = demo()
        wacc = (doc["source"].get("capital_costs", {}) or {}).get("wacc") or 0.065
        assumptions, _ = coerce_dcf_assumptions(doc, None, wacc)
        raw = asdict(assumptions)
        raw["revenue_growth_rates"] = [0.07] * 5
        raw["ebit_margins"] = [0.22] * 5
        accepted, _ = coerce_dcf_assumptions(deepcopy(doc), deepcopy(raw), wacc)
        expected = evaluate(deepcopy(doc), deepcopy(accepted))
        brief = build_brief(deepcopy(doc), asdict(accepted))
        self.assertEqual(brief["basis"], "custom")
        self.assertTrue(brief["assumptions"]["custom"])
        self.assertAlmostEqual(brief["dcf"]["intrinsic_value"], expected["intrinsic_value"])
        self.assertAlmostEqual(brief["dcf"]["target_price_12m"], expected["target_price_12m"])
        self.assertAlmostEqual(brief["dcf"]["upside_12m"], expected["upside_12m"])
        self.assertAlmostEqual(brief["assumptions"]["revenue_growth_mean"], 0.07)
        self.assertAlmostEqual(brief["assumptions"]["ebit_margin_mean"], 0.22)
        for name in ("Bear", "Base", "Bull"):
            got = next(s for s in brief["scenarios"] if s["name"] == name)
            want = next(s for s in expected["scenarios"] if s["name"] == name)
            self.assertEqual(got["target_price_12m"], want["target_price_12m"])
            # Brief-only inspectability: each scenario carries its deltas.
            self.assertIn("revenue_growth_delta", got["spec"])


class BriefApiTests(unittest.TestCase):
    def test_api_returns_brief_for_snapshot(self):
        from app import app

        client = app.test_client()
        doc = demo()
        response = client.post("/api/brief", json={"financials": doc})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True)[:300])
        body = response.get_json()
        self.assertEqual(body["ticker"], doc["company"]["ticker"])
        self.assertIn("Server-Timing", response.headers)
        self.assertIn("market_implied", body)

    def test_api_rejects_missing_snapshot(self):
        from app import app

        response = app.test_client().post("/api/brief", json={})
        self.assertEqual(response.status_code, 400)

    def test_api_marks_custom_basis(self):
        from app import app
        from compare import coerce_dcf_assumptions
        from dataclasses import asdict

        doc = demo()
        assumptions, _ = coerce_dcf_assumptions(doc, None, 0.065)
        raw = asdict(assumptions)
        raw["revenue_growth_rates"] = [0.06] * 5
        response = app.test_client().post(
            "/api/brief", json={"financials": doc, "assumptions": raw}
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True)[:300])
        body = response.get_json()
        self.assertEqual(body["basis"], "custom")
        self.assertIn("Custom", body["basis_note"])


class EmbeddedBriefTests(unittest.TestCase):
    def test_dcf_load_embeds_baseline_brief_matching_api(self):
        import auto_loading
        from test_yahoo_provider import MockHTTP

        doc = demo()
        bundle = auto_loading.load_method(
            "dcf", doc["company"]["ticker"], snapshot=demo(), http=MockHTTP()
        )
        brief = bundle.get("brief")
        self.assertIsNotNone(brief)
        self.assertEqual(brief["basis"], "baseline")
        self.assertIn("Baseline", brief["basis_note"])
        self.assertIn("brief_inline", bundle["load_summary"]["stage_seconds"])
        from brief import build_brief

        expected = build_brief(demo())
        self.assertEqual(brief["dcf"], expected["dcf"])
        self.assertEqual(brief["scenarios"], expected["scenarios"])
        self.assertEqual(
            brief["market_implied"]["revenue_growth"]["status"],
            expected["market_implied"]["revenue_growth"]["status"],
        )

    def test_invalid_baseline_still_loads_without_embedded_brief(self):
        import auto_loading
        from test_yahoo_provider import MockHTTP

        snapshot = demo()
        for row in snapshot["historical"]:
            row["net_income"] = row["revenue"] * 1.5  # baseline margin fails validation
        bundle = auto_loading.load_method(
            "dcf", snapshot["company"]["ticker"], snapshot=snapshot, http=MockHTTP()
        )
        self.assertNotIn("brief", bundle)
        self.assertIn("brief_skipped", bundle["load_summary"]["stage_seconds"])

    def test_ddm_load_carries_no_brief(self):
        import auto_loading
        from test_yahoo_provider import MockHTTP

        snapshot = demo()
        snapshot["source"]["common_dividends"] = {
            "value": 1.0, "period_end": snapshot["valuation_date"]
        }
        bundle = auto_loading.load_method(
            "ddm", snapshot["company"]["ticker"], snapshot=snapshot, http=MockHTTP()
        )
        self.assertNotIn("brief", bundle)


if __name__ == "__main__":
    unittest.main()
