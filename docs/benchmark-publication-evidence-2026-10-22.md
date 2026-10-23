# Benchmark publication/vintage evidence — October 22, 2026 (prepared)

## Result

The 7 local Damodaran assumption releases now have a source-backed
publication-evidence catalog and a read-only coverage preflight. Historical
benchmark selection works for the vintages that have evidence and stays
fail-closed for the two that do. Nothing was promoted and no release object was
modified: the catalog is one additive file beside the releases.

R5 (a) and (b) of `data-gap-repairs-2026-10-22.md` are prepared here; R5 (c)
(giving the deployed app a release root) remains a separate, unscoped action.

## Evidence rule

`published_at` is the provider's HTTP `Last-Modified` **date of the exact source
bytes**, bound to the preserved `evidence_sha256` — mirroring the reviewed PPE
importer contract (`ingestion/damodaran/importer.py::validate_publication`) and
the `data/ddfi` ingest rule (`published_at = http_date_to_iso(last_modified_server)`).

- Download time (`retrieval.json.retrieved_at`) is disclosed and never used for
  availability; each release's retrieval record already says so
  (`UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED`).
- Stated vintage labels (e.g. the "january_2026" evidence labels, or
  `stated_publication_date`) are recorded but never used for eligibility.
- A guessed year, a bare string, an unreviewed method, an observation before
  publication, or a `published_at` that is not the server header's date are
  rejected before anything is stored — and fail closed at resolution time.

## Evidence bound (byte-exact)

| Release | Source bytes | published_at | Basis | Availability |
| --- | --- | --- | --- | --- |
| industry_betas | `betas.xls` `fa5d91af…` | 2026-04-12 | server Last-Modified `Sun, 12 Apr 2026 16:39:33 GMT` | AVAILABLE_FROM_PUBLISHED_AT |
| cost_of_capital | `wacc.xls` `d38b149c…` | 2026-01-12 | `Mon, 12 Jan 2026 13:41:41 GMT` | AVAILABLE_FROM_PUBLISHED_AT |
| implied_erp | `histimpl.xls` `bb4d8da0…` | 2026-01-08 | `Thu, 08 Jan 2026 19:22:50 GMT` | AVAILABLE_FROM_PUBLISHED_AT |
| multiples | `vebitda.xls` `c75ec898…` | 2026-01-08 | `Thu, 08 Jan 2026 19:22:49 GMT` | AVAILABLE_FROM_PUBLISHED_AT |
| reinvestment | `capex.xls` `97216e36…` | 2026-01-08 | `Thu, 08 Jan 2026 19:22:52 GMT` | AVAILABLE_FROM_PUBLISHED_AT |
| margins | `margin.xls` `25b04fce…` | — | no preserved evidence for these bytes | UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED |
| country_risk | `ctryprem.xlsx` `b5200e8a…` | — | no preserved evidence for these bytes | UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED |

The five evidenced source files are byte-identical to the preserved
`data/ddfi/evidence/` copies whose ingest records carry `last_modified_server`.
For `margins` and `country_risk` no server-timestamped record exists for the
exact bytes anywhere in the preserved stores (the `data/ddfi` store only holds a
later July-2026 `ctryprem` vintage), so those two refuse every historical
cutoff instead of being backdated.

## Artifacts

- `publication_evidence.json` — additive catalog beside the releases (source of
  truth), plus review copy `evidence/benchmark_publication_evidence.json`.
- `evidence/benchmark-publication-evidence-receipt.json` — curation receipt
  (`PREPARED_NOT_PROMOTED`, 5 recorded / 2 fail-closed, 0 release objects
  modified).
- `artifacts/path1-benchmark-vintage/coverage-preflight.json` / `.md` — the
  read-only preflight report.

## Code

- `valuation_benchmarks.py`: publication-evidence catalog loading and
  validation, byte-bound fail-closed resolution in `load_benchmark`, and a
  read-only `coverage_catalog()` listing only subject/measure pairs a selection
  would actually serve (null/ambiguous pairs are counted, not advertised).
  Releases whose manifests carry their own `published_at` behave exactly as
  before.
- `scripts/build_benchmark_publication_evidence.py` — curator; binds each
  release's exact bytes to the preserved ingest records and refuses to write
  anything the loader's contract would reject.
- `scripts/benchmark_coverage_preflight.py` — read-only preflight: catalog byte
  binding, root/review copy identity, coverage listing, and historical probes
  (refused the day before `published_at`, served on it; unevidenced releases
  refused at every cutoff while current-mode selection is unchanged).
- `tests/test_benchmark_publication_evidence.py` — 21 contract tests: evidence
  rejection cases (download time, guessed vintage, bare string, unreviewed
  method, non-https, observation before publication, missing statement),
  fail-closed resolution on byte mismatch, historical cutoff behavior, and
  catalog coverage reporting.

## Verification gates run (this worktree)

- Focused benchmark/valuation set: 66 passed (21 new).
- Full suite: **1106 passed, 16 skipped, 10 subtests passed** (uv-locked
  environment). Three modules (`test_aapl_reconciliation.py`,
  `test_comps_analysis.py`, `test_workbook_recalc.py`) could not run: they
  import the undeclared `formulas` package, a pre-existing environment gap
  unrelated to this change. The real-DDFI-release tests skip in the worktree
  layout as before.

## What remains explicitly out of scope

- Publishing/promoting any release or dataset job.
- R5 (c): uploading a release for the deployed app (a new release contract).
- Fetching new source evidence for `margins`/`country_risk` (a new acquisition,
  which would then be a distinct authorized action).
