# Data-gap repair candidates — 2026-10-22

Scope: diagnose the six issuers with no stored revenue, prepare a recent-price session
index, propose an identity-checked universe expansion, and inventory the benchmark
assumptions. Read-only against stored releases and SEC's public API. No source pointer,
release ID, dataset, ingestion job, collector or CURRENT file was changed. Nothing was
deployed or promoted.

Reproduction inputs (all already stored, all read with bounded single-object GETs):

| Input | Release / key | Bytes read |
| --- | --- | --- |
| SEC engine manifest + directory | `b39a670b…` → `releases/0f0fa0be…/directory.json` | 35 KB + 2.2 MB |
| Engine catalog shards (6 of 100) | `releases/0f0fa0be…/catalog/{01,17,45,51,69,82}.json` | 2.5 MB |
| Stored stock universe | `gold/stock-history/releases/12bf4774…/manifest.json` (inline 2,629-symbol catalog) | 416 KB |
| SEC expanded ticker map | `gold/sec-expanded/releases/66c116df…/tickers.json` | 169 KB |
| SEC company tickers + exchange | `https://www.sec.gov/files/company_tickers_exchange.json` | 523 KB |
| Damodaran release set | `artifacts/zero-subscription-integration/damodaran-releases/` (7 releases) | local |

Serving observations below use the live staging bundle `f44fa392…` (29 source references).
The stored SEC input is the frozen 2026-09-24 nightly; the tag
inventory was cross-checked against SEC's current `companyconcept` API because the archive
member itself is a 3 MB range-read per issuer. Treat the tag/duration evidence as
structural, not snapshot-exact; the serving symptom and the release coverage counts are
exact.

## 1. Revenue is missing for two different reasons, and only one is a bug

### 1.1 What the API returns today

`GET /api/data/query?query=<issuer> annual revenue` on the staging website:

| Issuer | CIK | Revenue observations | Coverage reason | Metrics the release does carry |
| --- | --- | --- | --- | --- |
| WMT | 0000104169 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | capex, cash, diluted shares, net income, operating cash flow, operating income |
| GE | 0000040545 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | cash, diluted shares, net income, operating cash flow |
| ALL | 0000899051 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | diluted shares, net income, operating cash flow |
| C | 0000831001 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | cash, diluted shares, net income, operating cash flow |
| GS | 0000886982 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | cash, diluted shares, net income, operating cash flow |
| JPM | 0000019617 | 0 | `METRIC_NOT_REPORTED_BY_ISSUER` | cash, diluted shares, net income, operating cash flow |

The frozen release itself agrees: annual revenue `{observations: 0, gaps: N}` for every
issuer — WMT 112, GE 78, ALL 34, C 29, GS 24, JPM 21 attempted fiscal periods.

Caveat that matters for reading the UI: the `coverage_gap_reasons` list is the issuer's
aggregate across *all* metrics. `AMBIGUOUS_CONCEPT_OR_DERIVATION` on GE/ALL/C can come from
debt or free-cash-flow components, not revenue. Only
`FINANCIAL_STATEMENT_INDUSTRY_MAPPING_NOT_CERTIFIED` is provably revenue-specific, because
the policy writes it per metric.

### 1.2 The two mechanisms in the engine

`sec_engine.py` / `sec_history.py` (identical blocks at line 71):

```python
"revenue": {"concepts": ["RevenueFromContractWithCustomerExcludingAssessedTax",
                         "SalesRevenueNet", "Revenues"], ...}
REVENUE_CONCEPTS = {"0000909832": ["Revenues"]}   # only UnitedHealth is pinned
```

**Mechanism A — definitional collision.** `insert()` keeps a period only if all selected
concepts agree. Two concepts for the same fiscal year with different values set the period
to `False` and append `AMBIGUOUS_CONCEPT_OR_DERIVATION`; nothing is chosen.

**Mechanism B — statement-family quarantine.** `statement_policy()` looks for any of six
insurance/lending evidence tags. If one exists it quarantines revenue, operating income,
capex, free cash flow and total debt with
`FINANCIAL_STATEMENT_INDUSTRY_MAPPING_NOT_CERTIFIED`, and `history()` removes those
observations and records the reason. This is a deliberate certification gate, not a
concept-resolution failure.

### 1.3 Per-issuer evidence (SEC companyconcept, 2026-10-22)

Annual 10-K rows, 350–380 day durations:

| Issuer | Registry concept rows | Evidence tags present | Dominant cause |
| --- | --- | --- | --- |
| WMT | `Revenues` 51 rows, latest 713.163B (FY2026); `RevenueFromContractWithCustomerExcludingAssessedTax` 24 rows, latest 706.413B; `SalesRevenueNet` 27 rows to FY2018, 495.76B | none | **A**: every annual period from FY2008 on has two definitions that differ (FY2026: 713.163 vs 706.413; FY2025: 680.985 vs 674.538) |
| GE | `Revenues` 61 rows, latest 45.85B; old ASC-606 and `SalesRevenueNet` rows overlap 2014–2018 | `LoansAndLeasesReceivableNetReportedAmount` | **B** |
| ALL | `Revenues` 51 rows, latest 67.69B | `PremiumsEarnedNet`, `InterestAndDividendIncomeOperating` | **B** |
| C | `Revenues` 51 rows, latest 85.22B | `InterestAndDividendIncomeOperating`, `PremiumsEarnedNet`, `PolicyholderBenefitsAndClaimsIncurredNet`, `LoansAndLeasesReceivableNetReportedAmount` | **B** |
| GS | **no `Revenues` concept at all** (HTTP 404); only `RevenuesNetOfInterestExpense` | `InterestAndDividendIncomeOperating`, `LoansAndLeasesReceivableNetReportedAmount` | **B**, plus a registry omission: the only concept Goldman files is not in the registry |
| JPM | `Revenues` 51 rows, latest 182.45B; also `RevenuesNetOfInterestExpense` | `InterestAndDividendIncomeOperating`, `LoansAndLeasesReceivableNetReportedAmount` | **B** |

Two secondary facts:

- **`Revenues` alone can be internally ambiguous.** GE shows several different values for
  the same `end` date in `companyconcept` (restatements/reclassifications across filings),
  which the history layer rejects as `CONFLICTING_SOURCE_VALUES` unless the latest filing
  timestamp is unique. That is upstream data behaviour, not a registry bug.
- **WMT's collision is not a range problem**: it exists for every year, including the
  oldest, so widening or narrowing the request cannot recover it.

### 1.4 Representative fixtures and tests

`worktrees/path-b-diagnosis/tests/unit/test_revenue_coverage_diagnosis.py` (9 tests, all
pass on Python 3.12 against the deployed engine commit `538605e`):

- WMT-shaped facts (total revenues vs ASC-606, real FY2024–FY2026 values) produce zero
  observations and `AMBIGUOUS_CONCEPT_OR_DERIVATION`;
- adding a WMT issuer pin (`REVENUE_CONCEPTS[CIK] = ["Revenues"]`) yields exactly the three
  total-revenue values, all `us-gaap:Revenues`, annual;
- GS-shaped facts produce zero observations *and* the policy quarantine;
- adding `RevenuesNetOfInterestExpense` to the registry normalises Goldman's two values but
  they are still removed by the quarantine — proving the concept fix alone is useless;
- ALL/GE/C/JPM-shaped fixtures quarantine revenue with the exact reason and leave
  `net_income`/`cash` untouched.

Command: `python3.12 -m pytest tests/unit/test_revenue_coverage_diagnosis.py -q`.

Consequence for planning: **WMT is one issuer-pin change. GE/ALL/C/GS/JPM are a
certification decision covering bank and insurer statement families.** A concept-only patch
for GS would be dead code behind the gate.

## 2. Recent-price session index

Design and contract: `ppe-m9-final/docs/daily-price-session-index.md`.
Producer module: `ppe-m9-final/cloudflare/data-plane/src/session-index.ts`.
Tests: `ppe-m9-final/cloudflare/data-plane/test/session-index.test.ts` — 11 passing:

```
npx vitest@4.1.11 run cloudflare/data-plane/test/session-index.test.ts
✓ 11 tests
```

The index maps `session → {release sha256, derived data key, bytes, rows, provider, feed,
published_at, previous_version}`, capped at 300 sessions, pinned into CURRENT by
`{key, sha256, bytes}`, verified before any historical row is served, and degrades to
today's CURRENT-only behaviour when missing or stale. Republishing a session replaces only
that entry; an older backfill never moves `latest_session` backwards; an unverifiable prior
entry is dropped rather than republished. It is deliberately **not wired into
`finalizeDailyRefresh` or serving yet** — that is the follow-up change with its own staging
validation.

## 3. Identity-checked expansion proposal

Artifacts (generated, reproducible):

- `docs/universe-expansion-2026-10-22.csv` — 4,078 in-scope candidates, 11 columns.
- `docs/universe-expansion-2026-10-22.json` — counts, exclusions, identity limits.
- `scripts/propose_universe_expansion.py` + `tests/test_universe_expansion.py` (9 tests).

Inputs: the stored Alpaca stock-history catalog (2,629 symbols, release `12bf4774…`) and
SEC's `company_tickers_exchange.json` (10,428 listed tickers; 5,975 issuers have at least
one ticker absent from the cohort).

| Segment | Count |
| --- | --- |
| Named high-impact omissions (XOM, GOOGL, GOOG, AMZN, TSLA, META, ORCL, COST, IBM, ADBE, MO, BRK-A, BRK-B, V) | 14 |
| New exchange-listed common equity, issuer not represented anywhere in the proposal | 3,828 listings / 3,665 issuers |
| Additional listing of a represented issuer (234 of covered issuers, 2 more Alphabet listings) | 236 |
| Excluded: OTC (outside Alpaca coverage) | 2,575 |
| Excluded: exchange not verified | 166 |
| Excluded: preferred / derivative / suspect 5-letter instruments | 1,224 |

Identity rules enforced by the generator and the tests: `cik` is zero-padded to ten digits;
`data_key`-style ticker syntax is the only classification signal; a candidate whose CIK is
already represented is never labelled a new issuer, and neither is an extra listing of an issuer
that a named omission already introduces; duplicate ticker rows with conflicting CIKs are rejected;
tiers sort deterministically. Of the 2,629 stored symbols, 2,364 resolve to a CIK in SEC's
current file; the other 265 (delisted, renamed, or notation differences) are not asserted
either way.

What the proposal deliberately does **not** claim:

- **ADR status is unknown.** Neither input carries it; every row says
  `UNKNOWN_NOT_IN_CONTRACTS`. Adding 3,665 issuers without that column would sweep in
  foreign private issuers and ADRs that Alpaca may not trade.
- **Tier 2 is unranked.** Ordering by liquidity or index membership needs a market-cap
  input the current contracts do not carry. The named set is the evidence-driven first wave.
- **XOM identity needs a check.** SEC's current file maps `XOM` to CIK `0002115436`
  ("ExxonMobil Holdings Corp"), not the historical `0000034088`. Confirm the filing entity
  against the archive before ingestion rather than trusting the ticker.
- `BRK-A`/`BRK-B` use SEC's hyphen notation; the stored catalog has no share-class
  separators at all, so a notation normalisation step is required in any ingestion job.

## 4. Benchmark assumption inventory

The app has two benchmark paths and no catalog surface.

| Path | Configuration | Live status | Verdict |
| --- | --- | --- | --- |
| `source: zion` | binding `ZION_BENCHMARK_QUERY` → `zion-ddfi-benchmark-staging`; URL var; `ZION_BENCHMARK_TOKEN` secret on staging and production | worker deployed `5cc4eb62` (2026-10-15, secret-only change); unauthenticated probe returns `401 UNAUTHORIZED` | **Configured and reachable**; data availability cannot be asserted without the credential |
| `source: release` | `DAMODARAN_RELEASE_ROOT` is unset in every wrangler config; the Worker bundle contains no release directory | local loader works; deployed path raises "Damodaran releases are not configured" | **Unavailable by configuration**, not broken integration |
| pytest-benchmark | test dependency | Path A closed it: real fixture, 11 benchmarks pass | unrelated to these data benchmarks |

Local release set, 7 releases, all verified by `load_benchmark` manifest/file hashes:

| Dataset | Region | Subjects | Measures relevant to DCF targets |
| --- | --- | --- | --- |
| margins | US | 96 | `operating_margin`, `net_margin` |
| cost_of_capital | US | 96 | `wacc`, `tax_rate` |
| industry_betas | US | 96 | — (bottom-up beta inputs) |
| implied_erp | US | 66 | — (ERP context) |
| multiples | US | 96 | — |
| reinvestment | US | 96 | — |
| country_risk | Global | 157 | — (country ERP) |

Findings:

- All four DCF targets are covered for current selection — but only by two of the seven
  releases (`wacc`/`tax_rate` in cost_of_capital, margins in **margins**). Selecting the
  wrong release returns "Benchmark missing or ambiguous", which is correct fail-closed
  behaviour, not a missing dataset.
- **Historical selection is unavailable for every release**: all seven manifests carry
  `published_at: null`, so `as_of` fails with "Benchmark vintage unavailable at historical
  cutoff". Current-mode works; backdated benchmark selection cannot work until publication
  evidence exists.
- The deployed app can only use `source: zion`; the release path is a local/offline path.
  Both staging and production have the token and binding, so the zion path is configured in
  both — but there is no endpoint to enumerate what the worker holds, so a missing
  subject/measure is discovered only when a user selects it.

## 5. Costed repair candidates

Effort is engineering time for one experienced engineer including validation; storage and
compute are Cloudflare-side and stay inside the existing $5 cap unless stated. None of these
is authorized by this report.

### R1 — WMT revenue issuer pin (recommended first)

- **Change**: add `"0000104169": ["Revenues"]` to `REVENUE_CONCEPTS` in **both**
  `sec_engine.py` and `sec_history.py` (they are duplicated at line 71; a single-file patch
  would drift), plus a fixture test for the pin. Rebuild an affected-issuer incremental
  engine release from the frozen archive: WMT changes, every other issuer's catalog entry
  and company member must hash byte-identically.
- **Touches**: new `sec-engine` release + both thin configs' `SEC_ENGINE_MANIFEST_KEY`
  (+ SHA), new bundle id, one staging rollout. No dataset, provider call, or collector
  change.
- **Cost**: ~0.5 engineering day; 1 company object + 1 catalog shard + manifest written
  (tens of KB); verification reads the 100 catalog shards (~40 MB). Negligible spend.
- **Validation**: WMT annual revenue equals the 10-K "Total revenues" line (713.163B FY2026,
  680.985B FY2025, 648.125B FY2024) exactly; observation concept is `us-gaap:Revenues`;
  AAPL/PEP/JPM packet hashes unchanged; new bundle id differs exactly once; live query
  returns non-zero observations with the FY2026 `data_as_of`; the ambiguity gap for WMT is
  gone and no new gap reason appears for other issuers.
- **Rollback**: repoint `SEC_ENGINE_MANIFEST_KEY` and the bundle to the prior release (the
  old release and bundle stay in R2), redeploy the prior worker version. No data deletion.
- **Rejected alternative**: editing packets or the query layer to inject revenue — it would
  hide the ambiguity rather than resolve it.

### R2 — Certified revenue definitions for banks and insurers (separate decision)

- **Change**: define, with an accounting owner, one certified revenue definition per
  statement family — bank: total revenues net of interest expense
  (`RevenuesNetOfInterestExpense` where filed, else `Revenues`); insurer: total `Revenues`
  with `PremiumsEarnedNet` shown as a component — then replace the blanket
  `FINANCIAL_STATEMENT_INDUSTRY_MAPPING_NOT_CERTIFIED` quarantine with that mapping, add
  the concepts to the registry (GS needs `RevenuesNetOfInterestExpense` simply to have a
  candidate), and pin per-issuer overrides where a single tag is wrong.
- **Touches**: engine policy + registry in both modules; new engine release; bundle; staged
  source rollout. **Five issuers change together**, because the gate is family-wide.
- **Cost**: 2–3 engineering days plus an accounting review; one full-family validation
  sample (the five issuers plus 10 unaffected financials); release size same as R1.
  This is the only candidate that needs a non-engineering sign-off.
- **Validation**: for each issuer, revenue equals the audited income-statement total
  revenue line for the last three fiscal years; operating income/capex/FCF stay quarantined
  or are separately certified (do not lift them implicitly); no non-financial issuer's
  packet hash changes; gaps disappear only for revenue.
- **Rollback**: same pointer/version rollback as R1; the prior release remains intact.
- **Do not do**: add GS's concept without certifying the family. It changes nothing
  observable and creates the false impression the gap is fixed.

### R3 — Session index producer + serving

- **Status**: implemented behind staging flags on the review branches, not deployed.
  Publication writes the index only with `DAILY_SESSION_INDEX=enabled` (ppe
  `ea8efebe1`); serving answers `session=YYYY-MM-DD` only with `SESSION_INDEX_ENABLED`
  true (zion-terminal `94f2e2b`, contract fixture `6d42f58`).
- **Change**: `maybeFinalizeDailyRun` extends a verified prior index, writes and re-reads the
  immutable object, then advances CURRENT once with release and index pins; the thin market
  route verifies pin, freshness, entry and release bytes before returning rows.
- **Touches**: data-plane worker and thin source serving code; one new R2 object per
  session; CURRENT gains one optional block. No stored price object changes.
- **Cost**: implementation complete; the remaining ~0.5 day is enabling the staging flag,
  publishing one session and running the live acceptance below; index ≈ 100 KB at 300 sessions.
- **Validation**: published staging session is served by date; a flipped byte in the index
  or a session object returns `SOURCE_LIMITED` with `SESSION_INDEX_*`, never a wrong row;
  the producer-generated fixture is served by the thin worker and a one-field tamper is
  rejected; `previous_version` chain remains readable for older sessions.
- **Rollback**: remove `sessions_index` from CURRENT (serving falls back), stop writing the
  index; session objects and CURRENT remain valid.

### R4 — Universe expansion in waves

- **Wave 1 (recommended)**: the 14 named omissions. Ingest identity + packets + price
  history for 14 listings across 12 issuers (GOOG/GOOGL and BRK-A/BRK-B share issuers), publish one new cohort release.
- **Wave 2**: 3,665 issuers. Requires the ADR/FPI column and a liquidity or index ranking
  first; without them this is an unbounded scope.
- **Cost**: wave 1 ~0.5 day and a small release (12 issuer packets plus 14 listing mappings and price
  pages). Wave 2: about 1.25 M additional price rows on top of the current 856,633 (≈2.5×
  the cohort) and ≈3,665 new packet builds — measure with a 25-issuer dry run before
  committing; expect a multi-day ingest and a materially larger R2 footprint, still inside
  the current spend cap only if the dry run confirms bytes per issuer.
- **Validation**: every new symbol resolves to exactly one CIK; no duplicate issuer packet per CIK, while preserving distinct share-class listings in the
  cohort; ADR/foreign-issuer rows excluded unless explicitly approved; unaffected packet
  hashes unchanged; the readiness count changes by the approved number only.
- **Rollback**: publish the new cohort as a new release and keep the old pointer; repoint
  CURRENT back if validation fails. Never mutate the frozen 2,629-symbol release in place.

### R5 — Benchmark publication metadata and preflight

- **Change**: (a) record `published_at` + publication evidence for the 7 local releases so
  historical mode works; (b) add a read-only catalog/preflight endpoint so the app can list
  available subject/measure pairs instead of failing at selection; (c) decide whether the
  deployed app should also get a release root (it cannot read a local filesystem, so that
  would mean uploading a release to R2 and reading it).
- **Cost**: (a) ~0.5 day data curation (source dates exist on the Damodaran history page);
  (b) ~1 day; (c) a new release contract, out of scope here.
- **Validation**: historical selection before/after `published_at` behaves and is refused
  when the cutoff precedes publication; the catalog matches the release contents; the
  current-mode values are unchanged.
- **Rollback**: metadata is additive; a bad release is withdrawn by removing it from the
  catalog and leaving the old release untouched.

### R6 — Not proposed

- Rewriting stored prices to make recent sessions answerable (violates source preservation;
  R3 solves it without touching data).
- Lowering the ambiguity rule to "pick the larger value" (would silently redefine revenue
  for every retailer).
- Adding the 3,828 wave-2 symbols as a single cohort without identity ranking.

## 6. What remains open

- No revenue fix was applied: WMT needs R1 authorization; five issuers need R2's accounting
  decision.
- The session index is code and tests only; publication and serving are unchanged.
- The expansion CSV is a proposal, not an ingestion plan; ADR and ranking inputs are missing
  by design.
- Benchmark inventory is complete for the local set; the zion path's contents cannot be
  enumerated without the credential, and the client has no catalog endpoint.
- All source releases, pointers, bundle IDs and the production website version remain
  unchanged.

## Review corrections

The session-index contract now uses immutable content-addressed index keys and a
single CURRENT advance after index verification. Duplicate ticker rows with conflicting
CIKs are rejected rather than silently selecting the first identity. The CSV remains a
proposal based on ticker syntax and unknown ADR status, not certified security identity.
GE's quarantine is an implemented policy outcome; historical lending tags do not by
themselves certify its present statement family. Reassess that evidence by period in R2.
R1 changes derived dataset contents by publishing a new release even though raw SEC
source data remains unchanged; the earlier phrase "No dataset change" means no raw-source
mutation, not an exemption from release validation.

Latest regenerated proposal excludes 166 rows lacking exchange evidence. Authoritative
counts are in the accompanying JSON: 4078 candidates; {'TIER_1_NAMED': 14, 'TIER_2_WAVE': 3828,
'TIER_3_REVIEW': 236}; 3,677 distinct new issuers. The two extra Alphabet listings (GOOGM, GOOGN)
are review rows of an issuer the named set already introduces, not wave-2 issuers.
The earlier 4,244 headline included those unverified listings and is superseded.

## Repair status — 2026-10-22 (execution record)

The diagnostics above were executed as follows. No staging flag was enabled, no release or
pointer was republished, and nothing was pushed or deployed.

| Candidate | Status | Evidence |
| --- | --- | --- |
| R1 Walmart revenue pin | Applied in both registries; engine release rebuild still required | `116c8d4`; 24 engine tests pass, including a test that the ambiguity rule still fires without the pin and a digest test that both registries agree |
| R2 Bank/insurer certification | Worksheet delivered; accounting decision still open | `docs/revenue-certification-2026-10-22.md`; five issuers, per-period accessions, mappings marked `PROPOSED_NOT_CERTIFIED` |
| R3 Session index | Code and drills complete; staging enablement not run | 36 producer tests and 22 serving tests pass, covering retention eviction, republish, lost race, rollback and pin bounds |
| R4 Wave 1 identities | Resolved to dated receipts | `docs/identity-receipts-2026-10-22.md`; 14 listings, 12 issuers, all share classes resolved from cover pages |
| R4 Wave 2 foreign status | Classified; ADR status still unknown by design | `docs/wave2-foreign-status-2026-10-22.md`; 3,665 issuers / 3,828 listings, 0 read errors |
| R5 Benchmark publication | Forward-only metadata enforced; no backfill claimed | `docs/benchmark-publication-ledger-2026-10-22.md`; 7/7 releases refuse historical selection |

What the execution changed in the diagnosis:

- **Walmart** now resolves revenue from total `Revenues` (FY2026 713.163B). The pin is the
  smallest defensible change; the ambiguity rule itself is untouched.
- **GE** files no insurance or lending tag in its last ten annual reports, and its 2023 revenue
  is restated from 67.954B to 35.348B by a later filing. The blanket quarantine is therefore a
  stale-evidence question for GE, not a present statement-family question.
- **Citigroup** files total `Revenues`, not `RevenuesNetOfInterestExpense`; **JPMorgan** files
  both with equal values; **Allstate** has current premiums evidence; **Goldman** files only the
  net-of-interest concept.
- **XOM** now maps to CIK 0002115436 (ExxonMobil Holdings Corp), whose 8-K12B names CIK
  0000034088 as predecessor. The successor has no annual report; historical packets belong to
  the predecessor. A packet built from the successor alone would be empty.
- **Wave 2** is not one cohort: 844 listings (22%) are IFRS filers outside the us-gaap engine,
  184 are N-CSR investment companies, 91 are mixed-form, 280 have no annual report yet, and
  2,429 are taxonomy-compatible domestic 10-K filers. ADR status remains
  `UNKNOWN_NOT_IN_CONTRACTS` for every row and is not inferred from exchange or ticker.

Not done, and deliberately so: engine/cohort release publication, staging flag enablement,
any deployment, and any push or pull request.
