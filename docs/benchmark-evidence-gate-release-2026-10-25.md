# Benchmark evidence gate — release receipt (2026-10-25/26)

Status: **released and verified end to end on the deployed service.**
Machine-readable: `docs/benchmark-evidence-gate-release-2026-10-25.json`.

## What shipped

- `zion-terminal` main `ac83f11` (PRs #59, #58, #60): historical DDFI benchmark
  selection requires a hash-pinned, reviewed evidence catalog bound to the served
  `source.bin` digest, index/manifest publication date, a reviewed method, and
  observation/download bounds.
- Worker `zion-ddfi-benchmark-staging`, active version `8af6d9d9-7c43-46cd-b58b-6e35d2ec9645`
  (previous `00930556…`, before that `5cc4eb62…`). Evidence key/digest, index pin,
  existing vars, secrets and bindings preserved; no other service deployed.
- Catalog object `gold/ddfi-benchmarks/v1/evidence/d8c75248…0414f.json`
  (10,989 bytes, 8 releases), read back and digest-verified. Index (`4817c621…`) and
  release objects untouched.

## Pre-existing defect fixed by this release

`snapshot_bundle.stamp` compared the answer's `release.serving_release_id`
(`ddfi-benchmarks:<sha256>`) with the financial serving pointer and raised
`ValueError('RELEASE_MISMATCH')`, so every successful benchmark answer was discarded.
The defect predates the evidence gate (`snapshot_bundle.py` last changed 2026-10-22,
before both prior versions) and is independent of it. PR #60 treats the namespaced
benchmark family as foreign while keeping the financial mismatch guard intact.

## Verified on the deployed revision

Workflow run **40256588261** (`Benchmark evidence live acceptance`, dispatch from main,
repository `ZION_PRIVATE_API_TOKEN`) against the deployed origin — **PASS 16/16**:

| Check | Result |
| --- | --- |
| anonymous / invalid bearer | 401 `UNAUTHORIZED` |
| historical `cost_of_capital` @ 2026-06-01 | 200, catalog `d8c75248…`, `SERVER_LAST_MODIFIED`, `download_precision: day`, stamped |
| pre-publication cutoff (dataset / explicit pin) | 404 `HISTORICAL_COVERAGE_UNAVAILABLE` / `BENCHMARK_VINTAGE_UNAVAILABLE` |
| current selection | 200 `CURRENT_EXPLICIT`, `NOT_APPLICABLE_CURRENT_SELECTION`, stamped |
| future cutoff | 400 `INVALID_REQUEST` |
| caller-declared stale bundle pin | 409 `RELEASE_MISMATCH` |
| all eight evidenced datasets @ 2026-10-01 | 200, expected release identity and catalog digest, stamped |

The bundle stamp matched the served `bundle_id` on every successful answer, and a
wrong pin still fails closed. Local `wrangler dev` (real R2) and the offline suite
(18 focused tests) agreed before merge; CI `existing-data-contract` and
`full-offline-suite` passed on the merged commit.

## Not verified

- DCF's deployed Worker making the call through `ZION_BENCHMARK_QUERY`; its provider
  contract is covered by tests here, but no authenticated DCF request was issued.
- Intraday ordering remains impossible: retrieval evidence is day-precision.

## Rollback (available; not executed)

1. `wrangler rollback 00930556-deba-4edb-8948-d501c730c4a3 --name zion-ddfi-benchmark-staging`
2. No configuration change is needed to roll back; `00930556` reads the same evidence
   vars. Leave the immutable catalog object in place.
3. Re-dispatch the acceptance workflow; it is expected to fail with
   `409 RELEASE_MISMATCH` on successful selections because the stamp defect returns.

## Next

Benchmark release work is complete. Next: the V1 contract compatibility decision, then
the coverage/freshness UI.
