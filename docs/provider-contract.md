# Financial provider and valuation API contracts

## Provider boundary

The engine receives a **complete `dcf-financials-v1` document**, independent of network/client code. `data/demo.json` is a complete synthetic example; `docs/financials.schema.json` documents the structure. Providers may return an incomplete document to the editor, but calculation requires all explicit numeric fields.

| Section | Required meaning |
|---|---|
| `schema_version` | `dcf-financials-v1` |
| `units` | `absolute`: monetary amounts and share counts are not scaled in millions |
| `valuation_date` | ISO date; calculation uses end-of-day availability |
| `company` | ticker, name, USD currency, sector/industry and `eligible: true` after suitability review |
| `historical` | exactly three consecutive annual periods, oldest first |
| Each historical row | `period_end`, revenue, EBIT, net income, positive CapEx outflow, D&A, operating NWC, book value, effective tax rate as a decimal |
| `market` | positive USD `price`, `price_as_of`, positive `diluted_shares`, `shares_basis` |
| `bridge` | short-term debt, long-term debt, cash, preferred claims, minority interest, other nonoperating assets, `as_of` |
| `source` | name, kind, warnings and optional URLs/observation/accession/release provenance |

Historical records from SEC/Zion/custom API require `available_at` no later than the valuation date. A provider must align the same fiscal periods, units, entity and currency. No silent FX conversion or missing-to-zero mapping is performed. A complete provider document uses typed JSON numbers; numeric strings are not accepted at the model boundary. Decimal strings in Zion observations are normalized by its adapter. JSON rate values are decimals.

CapEx is positive because it is subtracted in FCFF. NWC is operating current assets less operating current liabilities, excluding cash and financing debt. The model does not silently reconstruct NWC from unrelated/nonaligned line items. Explicit zero is permitted for a verified zero claim; absent/null is incomplete.

## Browser/API routes

`GET /api/sample` returns the offline document. `GET /api/search?q=AAPL&limit=12` returns public local autocomplete metadata (`symbol`, `shortname`). This search does not certify eligibility.

`POST /api/financials` loads a provider document and editor defaults:

```json
{"provider":"zion","ticker":"AAPL","valuation_date":"2026-10-06"}
```

Returns `{ "financials": document, "form": editorDefaults }`. Providers: `sample`, `sec`, `zion`, `api`. Missing server configuration/provider failure returns HTTP 503. Invalid input returns HTTP 400. Completing missing fields in the editor is required before valuation.

`POST /api/calculate` accepts:

```json
{
  "financials": "replace this placeholder with the complete document object from data/demo.json",
  "assumptions": {
    "revenue_growth_rates": [0.05, 0.05, 0.05, 0.05, 0.05],
    "terminal_growth_rate": 0.02,
    "wacc_override": 0.065
  }
}
```

The quoted placeholder above is explanatory, not a valid request. A runnable example is:

```python
import json
import requests
from pathlib import Path

financials = json.loads(Path("data/demo.json").read_text())
response = requests.post(
    "http://127.0.0.1:5000/api/calculate",
    json={
        "financials": financials,
        "assumptions": {
            "revenue_growth_rates": [0.05] * 5,
            "terminal_growth_rate": 0.02,
            "wacc_override": 0.065,
        },
    },
    timeout=30,
)
response.raise_for_status()
print(response.json()["intrinsic_value"])
```

Optional annual arrays: `ebit_margins`, `da_margins`, `capex_margins`, `nwc_margins`, `tax_rates`, `net_income_margins`, `book_value_margins`. Each has exactly five decimal rates. When omitted, operating ratios default to historical means and taxes to the latest historical rate. These defaults are returned in result `drivers` and are assumptions, not predictions.

`terminal_mode` is `template` or `normalized`; normalized mode also requires `terminal_roic`. Optional nonnegative future bridge values: `future_debt`, `future_cash`, `future_preferred`, `future_minority`, `future_other_assets`, and positive `future_shares`. Omitted future values carry current values forward.

Results contain present/12-month enterprise and equity values, per-share values, full forecast cash flows, terminal-value share, active assumptions, source document, warnings, sensitivity and scenarios. Invalid sensitivity/scenario results use null, never a fabricated zero. Money is unrounded in JSON.

`POST /export/json` and `POST /export/csv` accept the same JSON body as calculation. CSV is readable in Excel; JSON contains complete financials/assumptions/results and is the lossless interchange format. Browser downloads use an escaped posted payload. Text fields in CSV are protected against spreadsheet-formula interpretation.

## Zion / MiniBloomberg adapter

The adapter was based on the local owning source `zion-final/deploy/cloudflare-query/src/company_api.py` and its representative unit tests as inspected October 6, 2026. It has not yet been verified against a configured live endpoint.

Configure `ZION_API_BASE_URL` (HTTPS base URL) and optional server-side `ZION_API_TOKEN`. It calls:

```text
GET /v1/company/{ticker}?as_of=YYYY-MM-DDT23:59:59Z&limit=1000
Authorization: Bearer <server-side token, when configured>
```

The company packet contains `symbol`, `identity`, `releases`, `fundamentals.annual`, and `prices.latest.observation`. Annual observations expose `metric_id`, `period_end`, `unit`, `value_decimal` or `value`, `available_at`, and observation/provenance identifiers. The adapter groups the last three annual revenue periods and requires matching units (USD, shares, pure rate). It preserves identity, release IDs, request ID and original observations. Conflicting revisions require review.

Supported metric mappings are listed in `ZION_METRICS` in `dcf_loader.py`. Actual release catalogs can differ; fields not mapped remain blank, not guessed. Before enabling, compare the intended release's metric catalog with the mapping, check coverage and reconcile against filings. The cutoff may exclude current-market prices lacking historical availability; the editor accepts a separately sourced dated price. Price currency must be verified.

No modification to Zion's service is required for the company-packet adapter. The DCF application does not copy licensed datasets into the repository or log bearer tokens.

## Optional normalized API

`DCF_API_BASE_URL`/`DCF_API_TOKEN` support a server-side HTTPS endpoint:

```text
GET /v1/valuation/financials/{ticker}?as_of=YYYY-MM-DD
```

Return the complete canonical financial document. That endpoint is an optional future contract, **not a claim that Zion already exposes it**. The current Zion adapter uses its existing company route. URLs are fixed by server configuration; browser users cannot request arbitrary hosts. Redirects are disabled to avoid forwarding credentials to another origin.

## Future methods

Keep financial providers separate from method-specific assumptions. DDM requires dividends/equity cost, comps require a reviewed peer set and comparable multiples, and bank residual-income methods need sector-specific capital assumptions. Add those as distinct calculation modules and tests; do not substitute the FCFF engine for every valuation method.

## DDM and relative valuation interfaces

Each method has its own typed boundary. `GET /api/sample/ddm` or `/api/sample/relative` returns `{financials,form}`; these are complete synthetic examples and useful contract fixtures. Add `?blank=1` for incomplete manual editor defaults. `POST /api/calculate/ddm` and `/api/calculate/relative` accept `{financials,assumptions}`. Matching exports use `/export/{method}/json` or `/export/{method}/csv`. Browser/import routes accept complete documents or exports through `/api/import/{method}`. Import and export do not create valuation records.

Common sections: `company` (ticker, name, USD currency, suitability confirmation, sector/industry), `market` (positive dated USD price, diluted shares and share-count basis), `source` (kind/name/provenance/warnings), `units: "absolute"`, and `valuation_date`. All dated input must be on or before the valuation date. SEC, Zion and custom API documents require `source.available_at`; any supplied availability date is checked against the valuation date. RV peers may also supply `available_at`, which is checked when present. Typed numeric JSON is required for financial values; API assumption rates are decimals. Preserve `source.origin_kind: "synthetic"` when editing a synthetic-origin document.

**DDM** uses `schema_version: "ddm-financials-v1"`, positive `base_common_dividends` (one fiscal year's total common cash dividends), and `dividend_as_of`. Assumptions:

```json
{"dividend_growth_rates":[0.05,0.05,0.05,0.05,0.05],"required_return":0.07,"terminal_growth_rate":0.02}
```

Optional `future_shares` sets 12-month diluted shares. Results contain present/12-month equity values, projected dividends, PVs, terminal equity value, sensitivity and warnings. Automatic Yahoo loading supplies reported annual common dividends and starter peer multiples. Manual/import inputs remain available; the standalone SEC loader remains a DCF statement loader. A future Zion dividend adapter must provide verified common distributions, not fabricated inferred dividends.

**Relative** uses `schema_version: "relative-financials-v1"`, `target.historical_as_of`, `target.historical` and `target.forward`, each with revenue, EBITDA, EBIT, common net income and common book equity. Unused metrics may be null. It uses the same explicit `bridge` claims as DCF and `comparables` containing unique ticker/name, USD currency, `as_of`, source reference and a `multiples` object. Multiple keys: `ev_revenue`, `ev_ebitda`, `ev_ebit`, `pe`, `pb`. Missing/nonpositive multiples are unsuitable observations and excluded; selected methods must remain computable. Browser supports four peers; API supports twenty. Set `company.is_financial: true` for financial firms; sector/industry metadata also enforces equity-only methods.

```json
{"included_methods":["ev_revenue","ev_ebitda","pe"]}
```

Relative results have `intrinsic_value: null` and `upside: null`, plus the forward `target_price_12m`/`upside_12m`, per-metric mean/range/count, observable target market multiples, explicit claims and active selection. A forward peer-implied price is not mislabeled as a present intrinsic value.

`POST /api/from-dcf/{method}` accepts a complete DCF financials/assumptions payload and returns editor defaults. It carries company identity, sources, market inputs and RV year-one forecasts. It leaves DDM dividends and RV peers blank, and clears suitability confirmation for the new method. These routes provide a clean future API integration boundary independent of UI code.


## Ticker-first automatic loading

`POST /api/load/{dcf|ddm|relative}` accepts `{ "ticker":"AAPL", "valuation_date":"YYYY-MM-DD", "equity_risk_premium":0.05, "credit_spread":0.015 }`. The date must be today in UTC. It returns normalized `financials`, editable browser `form`, `warnings` and `load_summary`; loading does not persist a valuation. Calculation uses the existing method-specific API.

Yahoo public chart/time-series endpoints are unofficial. Current snapshots use retrieval availability dates, not historical filing dates. Fiscal dates are standardized to month ends. Annual diluted-average shares and current-price market equity weights have different stated bases. Missing reported tax provision can use observed annual TaxRateForCalcs with a warning; it is not replaced by a generic tax rate. Explicit preferred/minority claims or provable equity identities are required. Other nonoperating assets default to an explicitly disclosed adjustment assumption of zero.

Beta uses at least 104 matched weekly total-return observations against SPY. Cost of equity = Treasury yield + beta × equity risk premium. Debt cost uses latest annual interest/debt if available, otherwise Treasury yield + credit spread. WACC uses market equity and book debt, after-tax debt cost and any supported preferred cost. ROE uses annual common net income / ending common equity and is diagnostic only.

RV starter peers are editable suggestions, not a claim of complete industry comparability. Negative/missing denominators are excluded; source dates and coverage warnings remain in the result. Automatic sector support is presently USD operating companies. Zion/MiniBloomberg remains an optional, unconfigured replacement behind the normalized provider boundary.

Method loading requires only the applicable capital costs: DCF estimates full WACC; DDM estimates the common-equity return without requiring preferred-stock cost; RV does not require beta, Treasury or WACC observations. Restoring the peer editor preserves excluded-method checkbox states. The offline example can load with an empty ticker.
