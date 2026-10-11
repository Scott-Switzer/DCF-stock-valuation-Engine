# Real-company financial validation

Run the non-saving audit against the public Worker:

```bash
uv run python scripts/validate_universe.py \
  --snapshots find/outputs/research-expansion/snapshots \
  --output find/outputs/research-expansion/universe-live.json --api
```

This loads the 25-company universe sequentially and calls only `/api/load/dcf` and `/api/preview/dcf`. It does not save valuations, create accounts, modify D1, publish R2 data or advance any data pointer. Keep snapshots locally; they are not automatically committed or published. Live checks depend on current upstream coverage and rate limits. The JSON and Markdown reports retain all 25 results, including failures, rather than aborting after the first unavailable company.

Replay exact captured observations without provider traffic:

```bash
uv run python scripts/validate_universe.py --offline \
  --snapshots find/outputs/research-expansion/snapshots \
  --output find/outputs/research-expansion/universe-replay.json
```

The source audit records currencies, absolute units, fiscal periods, price date, diluted-share basis, classification, raw provider references, normalized values and missing provenance. EBIT plus reported D&A is explicitly identified as calculated EBITDA, not provider-adjusted EBITDA. It checks future availability observations against the valuation cutoff and preserves reported signs and values. Provider provenance is evidence to inspect, not proof that a human or independent source checked a filing.

The independent reference imports no production calculation engine. It computes five FCFFs, terminal value, present and year-one enterprise/common equity values and per-share values. Controlled test assumptions are 5% annual revenue growth, 10% WACC and 2% terminal growth. These are shared QA inputs, not proposed investment assumptions. Local and optional live API outputs must agree within 1e-9 relative or 1e-6 absolute tolerance, including every forecast FCFF. WACC component arithmetic is checked separately without certifying beta, Treasury yield, credit spread or market-cap inputs. Regression tests cover growth, operating margins, reinvestment, tax, discount rates, normalized terminal reinvestment and every future bridge override.

## Result meanings

- **PASS:** the particular check is supported and validated. Arithmetic PASS does not establish source accuracy or economic credibility.
- **PARTIAL:** a calculation may be supported, but named evidence limitations remain. Overall company/method status remains PARTIAL until both source and calculation have been independently validated.
- **BLOCKED:** required inputs, appropriate methodology or provider coverage are unavailable. A financial firm's blocked industrial DCF is expected; a blocked company load means no other method was evaluated and is not proof those methods are unsuitable.
- **FAIL:** invalid data contract, future observation, numerical mismatch or audit failure. The CLI exits nonzero for FAIL, while explicitly documented unsupported-method blocks remain reportable outcomes.

DDM, relative and residual readiness are reported but not advertised as numerical reconciliations by this DCF audit. Existing independent DDM/RV workbook tests remain separate evidence.

## October 10 production findings

[25-company matrix](../reconciliation/universe-2026-10-10.md): 20 loaded, 19 independently reconciled DCF cases and live API comparisons passed, all 20 available WACC component checks passed. MRX's industrial DCF was rejected by the live API. Overall source-level results remain PARTIAL.

Five initial loading blocks need targeted follow-up:

- ORCL: nonzero preferred equity with no preferred cost prevents automatic WACC. Inspect reported preferred classification before changing the provider or use explicit assumptions through an appropriate workflow.
- JPM, BAC, GS: the current universal loading contract requires industrial operating income, which their Yahoo snapshots lack. This limits equity-method access; do not substitute zero EBIT or relabel bank net income as industrial operating income.
- O: missing annual CapEx blocks the current loading contract. REIT-specific suitability and reported cash-flow treatment require review; this is not authorization to synthesize CapEx or add an unsupported REIT model.

Full field receipts and captured snapshots are local under `find/outputs/research-expansion/`. No new observation has been labeled independently filing-verified by this automated sweep. A later filing review should append explicit comparisons and accession evidence, not reinterpret readiness as source verification.
