# Product-quality sprint receipt — October 15, 2026 (Pacific)

## Delivered correctness improvement

PR [#56](https://github.com/Scott-Switzer/DCF-stock-valuation-Engine/pull/56) reproduces and repairs the selected-tax/editor and WACC/bundled-preview discrepancies. Frozen input: historical rates `[0.22, -0.153, 0.358]`; selected forecast `[0.231, 0.24, 0.25, 0.26, 0.27]`.

Before repair the editor showed five 35.8% rates; bundled WACC was `0.08975333333333334` and intrinsic value `19.386528673283944`, while Research Brief used `0.09102333333333333` and `19.019516765588715`. After repair all paths use the selected vector and the latter WACC/value. This is a concrete correctness improvement on identical frozen financials, not evidence that the fixture forecasts are economically correct.

The tests compare form, automatic load, bundled preview, iframe edit, JSON preview, brief, save/reload and exports; reported history and provenance remain unchanged. They include Yahoo fallback. Explicit recalculated JSON mode now recomputes after a shield edit (19% shield yields WACC `0.09143333333333334`); fixed mode and legacy overrides remain supported. Percent display/parse restores only numerically identical baseline inputs to avoid rounding drift.

Real Chromium acceptance changes the first forecast tax to 30%, producing WACC `0.09033333333333333` and intrinsic `19.084102601020753`, then saves/reloads and downloads XLSX. HyperFormula independently evaluates workbook FCFF, terminal, enterprise, equity and per-share values (relative tolerance 1e-10 with 1e-9 absolute floor; FCFF absolute 1e-8). This is numerical reconciliation, not Microsoft Excel visual acceptance. The browser negative control failed with the original tax-fill defect restored. Linux CI initially exposed a test submission while the save control was disabled; waiting for the actual usable button fixed the harness without relaxing valuation assertions.

## Bounded performance change

PR [#57](https://github.com/Scott-Switzer/DCF-stock-valuation-Engine/pull/57) reuses reviewed issuer identity only when the packet CIK matches and the cited date is valid and no later than the valuation date. Unknown/mismatched/future/uncited entries retain the original directory lookup. No financial mapping, cache key/TTL or asynchronous scheduling changed.

The controlled fixture makes **4 provider operations before, 3 after**: one SEC ticker-directory lookup is eliminated. All other financial/source fields agree except retrieval timestamps. In a real request that lookup may have been satisfied by the existing HTTP cache: **live origin requests eliminated are not established**. PEP is the eligible reuse case in this staging benchmark; other cohort members are controls for the broader parity release.

## Validation and release boundary

- 782 Python tests + 10 subtests pass; one existing test-return warning remains. Ruff and all shipped JS syntax checks pass through CI.
- Python 3.12/3.13, deterministic browser acceptance and isolated experimental TypeScript checking all pass in PR CI and on merged runtime commit. Type checking is not TS financial parity or evidence the TS module ships.
- Staging runtime: `6eb7821332b8d8ecb59e3ed55c59245b41630e23`, `tracked_dirty:false`.
- Staging Worker version: `2bd50245-0844-480b-9358-07d93ed15614` at 100%.
- Merge CI: [38846095730](https://github.com/Scott-Switzer/DCF-stock-valuation-Engine/actions/runs/38846095730).
- Deployment command: `uv tool run --from 'uv>=0.12.3' uv run pywrangler deploy --env staging --keep-vars`.
- Production stays on `bdca36455c6159cc698f664d10af8d79dbd8e394`. Its 237-company `CURRENT.json` is byte-identical before/after, SHA-256 `ecf1e1c4b56936bc6af7fd93fe1bccadc41b7c6885f5e07c661dec5a93c7b5c1`.
- No production deployment, candidate promotion, migration, production account or research creation. Read-only company loads can populate the application's existing provider cache.
- Coverage gain: **0 newly supported issuers/methods claimed**. This sprint fixes valuation consistency and removes a redundant lookup.

## Reproduce

From repository root:

```sh
uv run pytest -q
uv run ruff check .
npm ci --prefix tests/browser
npm --prefix tests/browser run typecheck
# Install Chromium as documented in tests/browser/README.md, then:
PYTHON="$PWD/.venv/bin/python" npm --prefix tests/browser test
node scripts/bench_browser.mjs --base https://dcf-valuation-engine-staging.scswitzer.workers.dev --tickers AAPL,PEP --warm 10 --cold-tickers CAT,T,PAYX,MSFT --reuse --out /tmp/staging-benchmark.json
python3 find/outputs/quality-sprint/summarize.py
```

The benchmark consumes normal reference budgets; the default 6.5-second spacing plus render wait avoids aggressive requests. It changes no financial data. A first-touch label does not prove a cache miss: classify only by the response's `assembly_cache.state`. The files retain browser marks, response size/timing, source path, server stages and current-request HIT breakdown.

## Limits and next decisions

No load/concurrency stress test was performed; these measurements do not establish global capacity, billion-user scalability or provider accuracy. Six MISS samples are descriptive, not a reliable cold-tail distribution. The historical October 13–14 values (4.71s first / 3.34s repeated AAPL) used smaller and different samples; the fresh pre-change run was already faster. Do not attribute that historical improvement to these PRs.

Existing telemetry combines candidate/production pointer, service/404 fallback and R2 retrieval in `zion_packet`; individual substage timings are **not measured**. It similarly combines Yahoo statements and market observations. `sec_classification`, `sec_first`, model-input preparation, preview and brief are separately recorded, but 0.000 seconds is rounding, not zero work. On HIT responses the original provider stage timings describe the cached build; only `hit_breakdown` describes current cache-delivery work. Further cold-path optimization needs bounded per-transport spans before claims about which underlying call dominates.

Concurrency was investigated in source: provider calls use synchronous `run_sync` bridges under a shared deadline. No measured benefit or runtime-tested safe overlap was established, so no thread pool, native rewrite, broad negative cache or new cross-request memo was introduced. Future registry entries still require source review and date/identity validation.

The [next two sprints](next-two-sprints.md) rank quarterly/TTM inputs, ordinary-share reconciliation, usable coverage, cost of capital, terminal reinvestment and bounded sector pilots by materiality, reuse, cost and complexity. Licensed datasets remain private. New production code deployment and financial-data promotion are separate approval decisions.

## Before/after browser measurements

Same workstation, headless Chrome, reused browser context with a fresh page per observation, 6.5-second pacing, same six-company cohort; first paint relative to submitting ticker. Quantiles use nearest rank `ceil(p*n)`. Assembly MISS does **not** establish that every upstream provider cache was cold.

| Run / actual cache state | n | Value p50 | Value p95 | Load POST duration p50 / p95 |
|---|---:|---:|---:|---:|
| Staging before, HIT | 20 | 149 ms | 245 ms | 92 / 148 ms |
| Staging after, HIT | 20 | 136 ms | 239 ms | 109 / 214 ms |
| Staging before, MISS | 6 | 924 ms | 2,275 ms | 889 / 2,138 ms |
| Staging after, MISS | 6 | 1,086 ms | 2,394 ms | 1,064 / 2,292 ms |
| Production read-only, HIT | 4 | 239 ms | 619 ms | 176 / 593 ms |
| Production read-only, MISS | 3 | 1,952 ms | 4,252 ms | 1,924 / 4,150 ms |

The warm rendering target of under 2 seconds was already achieved before this sprint. The after-run warm median improved 13 ms, but the small nonrandomized comparison does not establish causality. **Cold latency did not improve**; no cold-speed gain is claimed. Keep the operation reduction as a bounded resource-efficiency improvement. No cache flush was performed, and later observation times/provider-cache warmth are confounders.

Source controls: staging AAPL/MSFT use Yahoo; CAT/PEP/T/PAYX use SEC-first. Warm samples split 10 AAPL / 10 PEP per run. Production PEP uses Yahoo, so its 4,252 ms first observation is not directly comparable to candidate PEP's 732 ms. All 52 staging benchmark observations and all 7 production observations painted a value successfully.

| First-touch issuer | Before → after value paint | Before → after main provider stage | Before → after packet stage | Before → after SEC classification |
|---|---:|---:|---:|---:|
| CAT (SEC-first) | 2,275 → 2,394 ms | 680 → 905 ms | 142 → 183 ms | 224 → 311 ms |
| T (SEC-first) | 1,202 → 836 ms | 426 → 248 ms | 38 → 20 ms | 300 → 64 ms |
| PAYX (SEC-first) | 924 → 1,086 ms | 217 → 285 ms | 30 → 25 ms | 58 → 50 ms |
| MSFT (Yahoo) | 1,543 → 1,757 ms | 307 → 196 ms | 688 → 794 ms | 0 → 0 ms |
| AAPL (Yahoo) | 906 → 1,114 ms | 352 → 311 ms | 46 → 59 ms | 0 → 0 ms |
| PEP (SEC-first, identity reuse) | 616 → 732 ms | 225 → 253 ms | 28 → 19 ms | 0 → 0 ms |

These are single observations per issuer, not per-issuer p95 estimates. Inline preview, brief and WACC preparation round to 0 ms in these samples; no evidence justifies a language/runtime rewrite. Raw response resource timing includes server wait plus transfer; it does not isolate network-only transfer. Warm editor-ready offsets were p50/p95 51/127 ms before and 55/85 ms after; negative offsets in some rows mean the iframe was already ready before submission, not negative elapsed work.

The two explicit live AAPL/PEP tax cases are separately recorded as **BYPASSED**, never treated as warm hits. See [staging-parity.json](staging-parity.json). The complete source-aware observations and percentiles are in [performance-summary.json](performance-summary.json), with raw before/after browser JSON alongside it.

## Post-deployment parity result

Live AAPL (Yahoo) and PEP (SEC-first) explicit-tax loads both returned BYPASSED and matched form, bundled preview, brief and JSON preview exactly, with reported history preserved. CAT, T and PAYX still load through SEC-first. ORCL remains blocked for nonzero preferred equity without an explicit preferred-cost assumption. The candidate pointer was also re-read and still hashes to `ff7b1b08e6fc459468c07336543bb3b2f4dec9ac469a60a2b8d41ed91d7ad5da`.

**Disposition:** verified staging correctness release; no demonstrated cold-latency improvement and no coverage expansion. Production remains unchanged. The documentation/benchmark-script receipt commit is not a new application runtime; continue pinning staging evidence to `6eb7821`.
