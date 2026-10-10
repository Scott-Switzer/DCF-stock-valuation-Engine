import copy
from datetime import datetime, timezone, timedelta
import unittest
from yahoo_provider import (
    load_yahoo,
    load_company_metrics,
    recalculate_costs,
    market_beta,
    ProviderError,
)

TODAY = datetime.now(timezone.utc).date().isoformat()


def fixture():
    year = datetime.now(timezone.utc).year
    ends = [f"{y}-12-31" for y in range(year - 3, year)]
    values = dict(
        TotalRevenue=1000,
        OperatingIncome=200,
        NetIncomeCommonStockholders=120,
        ReconciledDepreciation=30,
        CapitalExpenditure=-50,
        CurrentAssets=300,
        CurrentLiabilities=150,
        CashAndCashEquivalents=100,
        CurrentDebt=20,
        LongTermDebt=80,
        TotalDebt=100,
        StockholdersEquity=400,
        CommonStockEquity=400,
        TotalEquityGrossMinorityInterest=400,
        TotalAssets=700,
        TotalLiabilitiesNetMinorityInterest=300,
        TaxProvision=40,
        PretaxIncome=160,
        DilutedAverageShares=10,
        CommonStockDividendPaid=-30,
        OrdinarySharesNumber=9,
    )
    result = []
    for metric, value in values.items():
        result.append(
            {
                "meta": {"symbol": ["TEST"]},
                "annual" + metric: [
                    {
                        "asOfDate": end,
                        "periodType": "12M",
                        "currencyCode": "USD",
                        "reportedValue": {"raw": value},
                    }
                    for end in ends
                ],
            }
        )
    return {"timeseries": {"result": result}}, ends


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
        self.financials, self.ends = fixture()
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "/timeseries/" in url:
            return copy.deepcopy(self.financials)
        return chart_fixture(url.rsplit("/", 1)[-1].replace("%5E", "^"))


class YahooTests(unittest.TestCase):
    def test_complete_snapshot_and_provenance(self):
        http = MockHTTP()
        doc = load_yahoo("TEST", TODAY, http)
        self.assertEqual(len(http.calls), 4)
        self.assertEqual(doc["historical"][0]["capex"], 50)
        self.assertEqual(doc["historical"][0]["nwc"], 70)
        self.assertEqual(doc["bridge"]["preferred_equity"], 0)
        self.assertEqual(doc["source"]["common_dividends"]["per_share"], 3)
        self.assertEqual(doc["source"]["common_book_equity"]["value"], 400)
        self.assertEqual(doc["source"]["capital_costs"]["cost_of_debt"], 0.055)
        self.assertAlmostEqual(doc["source"]["capital_costs"]["beta"], 1)
        self.assertEqual(doc["historical"][0]["available_at"], TODAY)
        self.assertEqual(
            doc["historical"][0]["provenance"]["DilutedAverageShares"]["unit"], "shares"
        )
        self.assertTrue(any("not point-in-time" in w for w in doc["source"]["warnings"]))

    def test_historical_cutoff_rejected_without_http(self):
        http = MockHTTP()
        with self.assertRaisesRegex(ProviderError, "current UTC date"):
            load_yahoo("TEST", "2020-01-01", http)
        self.assertFalse(http.calls)

    def test_missing_claim_is_not_zero(self):
        http = MockHTTP()
        http.financials["timeseries"]["result"] = [
            b for b in http.financials["timeseries"]["result"] if "annualCommonStockEquity" not in b
        ]
        with self.assertRaisesRegex(ProviderError, "missing CommonStockEquity"):
            load_yahoo("TEST", TODAY, http)

    def test_negative_minority_interest_is_carried_as_reported(self):
        # Mirrors MRX 2025-12-31: reported minority interest of -200,000 USD.
        http = MockHTTP()
        http.financials["timeseries"]["result"].append(
            {
                "meta": {"symbol": ["TEST"]},
                "annualMinorityInterest": [
                    {
                        "asOfDate": http.ends[-1],
                        "periodType": "12M",
                        "currencyCode": "USD",
                        "reportedValue": {"raw": -200000},
                    }
                ],
            }
        )
        doc = load_yahoo("TEST", TODAY, http)
        self.assertEqual(doc["bridge"]["minority_interest"], -200000)
        self.assertTrue(any("negative" in w for w in doc["source"]["warnings"]))

    def test_missing_latest_annual_observation_is_not_carried_forward(self):
        http = MockHTTP()
        http.financials["timeseries"]["result"].append(
            {
                "annualInterestExpense": [
                    {
                        "asOfDate": http.ends[0],
                        "periodType": "12M",
                        "currencyCode": "USD",
                        "reportedValue": {"raw": 99},
                    }
                ]
            }
        )
        doc = load_yahoo("TEST", TODAY, http)
        self.assertIsNone(doc["source"]["capital_costs"]["reported_cost_of_debt"])
        self.assertEqual(doc["source"]["capital_costs"]["cost_of_debt"], 0.055)

    def test_nonfinite_wrong_currency_and_conflicts_rejected(self):
        for change in ("nan", "currency", "conflict"):
            with self.subTest(change=change):
                http = MockHTTP()
                block = http.financials["timeseries"]["result"][0]
                if change == "nan":
                    block["annualTotalRevenue"][0]["reportedValue"]["raw"] = float("nan")
                if change == "currency":
                    block["annualTotalRevenue"][0]["currencyCode"] = "EUR"
                if change == "conflict":
                    row = copy.deepcopy(block["annualTotalRevenue"][0])
                    row["reportedValue"]["raw"] = 20
                    block["annualTotalRevenue"].append(row)
                with self.assertRaises(ProviderError):
                    load_yahoo("TEST", TODAY, http)

    def test_beta_requires_two_years_and_adjusted_prices(self):
        packet = chart_fixture("TEST")["chart"]["result"][0]
        short = copy.deepcopy(packet)
        short["timestamp"] = short["timestamp"][:50]
        short["indicators"]["adjclose"][0]["adjclose"] = short["indicators"]["adjclose"][0][
            "adjclose"
        ][:50]
        with self.assertRaisesRegex(ProviderError, "104"):
            market_beta(short, short)
        del short["indicators"]["adjclose"]
        with self.assertRaisesRegex(ProviderError, "adjusted"):
            market_beta(short, packet)

    def test_peer_skips_capital_cost_requests(self):
        http = MockHTTP()
        doc = load_company_metrics("TEST", TODAY, http)
        self.assertEqual(len(http.calls), 2)
        self.assertEqual(doc["source"]["capital_costs"], {})

    def test_assumption_recompute(self):
        doc = load_yahoo("TEST", TODAY, MockHTTP())
        costs = recalculate_costs(doc, 0.06, 0.02)
        self.assertAlmostEqual(costs["cost_of_equity"], 0.10)
        self.assertAlmostEqual(costs["cost_of_debt"], 0.06)
        self.assertAlmostEqual(costs["wacc"], (450 * 0.1 + 100 * 0.06 * 0.75) / 550)

    def test_missing_dividends_does_not_block_dcf_or_mean_zero(self):
        http = MockHTTP()
        http.financials["timeseries"]["result"] = [
            b
            for b in http.financials["timeseries"]["result"]
            if "annualCommonStockDividendPaid" not in b
        ]
        doc = load_yahoo("TEST", TODAY, http)
        self.assertIsNone(doc["source"]["common_dividends"]["value"])
        self.assertIsNone(doc["source"]["common_dividends"]["per_share"])

    def test_debt_component_derived_only_from_reported_total_and_other_component(self):
        http = MockHTTP()
        http.financials["timeseries"]["result"] = [
            b for b in http.financials["timeseries"]["result"] if "annualCurrentDebt" not in b
        ]
        doc = load_yahoo("TEST", TODAY, http)
        self.assertEqual(doc["bridge"]["short_term_debt"], 20)
        self.assertIn("derived_from", doc["historical"][0]["provenance"]["CurrentDebt"])

    def test_common_equity_optional_with_explicit_preferred_fact(self):
        http = MockHTTP()
        http.financials["timeseries"]["result"] = [
            b for b in http.financials["timeseries"]["result"] if "annualCommonStockEquity" not in b
        ]
        http.financials["timeseries"]["result"].append(
            {
                "annualPreferredStockEquity": [
                    {
                        "asOfDate": end,
                        "periodType": "12M",
                        "currencyCode": "USD",
                        "reportedValue": {"raw": 0},
                    }
                    for end in http.ends
                ]
            }
        )
        doc = load_yahoo("TEST", TODAY, http)
        self.assertIsNone(doc["source"]["common_book_equity"]["value"])
        self.assertIsNone(doc["source"]["finance_diagnostics"]["roe"])

    def test_normalized_tax_fallback_is_observed_and_disclosed(self):
        for ratio in (None, -0.4, 1.5):
            with self.subTest(ratio=ratio):
                http = MockHTTP()
                provision = next(
                    b for b in http.financials["timeseries"]["result"] if "annualTaxProvision" in b
                )
                if ratio is None:
                    provision["annualTaxProvision"].pop()
                else:
                    provision["annualTaxProvision"][-1]["reportedValue"]["raw"] = 160 * ratio
                http.financials["timeseries"]["result"].append(
                    {
                        "annualTaxRateForCalcs": [
                            {
                                "asOfDate": http.ends[-1],
                                "periodType": "12M",
                                "currencyCode": "USD",
                                "reportedValue": {"raw": 0.18},
                            }
                        ]
                    }
                )
                doc = load_yahoo("TEST", TODAY, http)
                self.assertEqual(doc["historical"][-1]["tax_rate"], 0.18)
                self.assertEqual(doc["historical"][-1]["provenance"]["tax_rate"]["unit"], "pure")
                self.assertEqual(
                    doc["historical"][-1]["provenance"]["tax_rate"]["metric"],
                    "annualTaxRateForCalcs",
                )
                self.assertTrue(
                    any("normalized assumption" in w for w in doc["source"]["warnings"])
                )

    def test_missing_or_invalid_normalized_tax_cannot_be_invented(self):
        for normalized in (None, -0.1, 1.1, float("nan")):
            with self.subTest(normalized=normalized):
                http = MockHTTP()
                provision = next(
                    b for b in http.financials["timeseries"]["result"] if "annualTaxProvision" in b
                )
                provision["annualTaxProvision"].pop()
                if normalized is not None:
                    http.financials["timeseries"]["result"].append(
                        {
                            "annualTaxRateForCalcs": [
                                {
                                    "asOfDate": http.ends[-1],
                                    "periodType": "12M",
                                    "currencyCode": "USD",
                                    "reportedValue": {"raw": normalized},
                                }
                            ]
                        }
                    )
                with self.assertRaises(ProviderError):
                    load_yahoo("TEST", TODAY, http)

    def test_nonzero_preferred_cannot_invent_cost(self):
        http = MockHTTP()
        block = next(
            b for b in http.financials["timeseries"]["result"] if "annualCommonStockEquity" in b
        )
        block["annualCommonStockEquity"][-1]["reportedValue"]["raw"] = 390
        with self.assertRaisesRegex(ProviderError, "preferred cost"):
            load_yahoo("TEST", TODAY, http)


if __name__ == "__main__":
    unittest.main()
