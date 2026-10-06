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
