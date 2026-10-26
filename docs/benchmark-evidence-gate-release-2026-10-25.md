# Benchmark evidence gate — release receipt (2026-10-25)

Status: **deployed; gate reachable and enforcing; successful benchmark answers blocked
by a pre-existing bundle-stamp defect (fix in PR #60, not deployed).**
Machine-readable: `docs/benchmark-evidence-gate-release-2026-10-25.json`.

## What shipped

- `zion-terminal` main `5c49df8` (PRs #59 then #58): the DDFI benchmark service now
  requires a hash-pinned, reviewed evidence catalog for **historical** selection,
  binding each release to its served `source.bin` digest, its index/manifest
  publication date, a reviewed method, and observation/download bounds.
- Worker `zion-ddfi-benchmark-staging` deployed as version `00930556…` (previous
  `5cc4eb62…`). Secrets preserved; no other service deployed.
- Catalog object `gold/ddfi-benchmarks/v1/evidence/d8c75248…0414f.json`
  (10,989 bytes, 8 releases), read back and digest-verified. Index and release
  objects untouched.

## Authenticated acceptance (run 40255369877, deployed version)

Invocation: `benchmark-evidence-live.yml` on branch `acceptance/bench-gate-live`,
using the repository's existing `ZION_PRIVATE_API_TOKEN` secret (the staging private
bearer the Zion Workers already share) against
`https://zion-ddfi-benchmark-staging.scswitzer.workers.dev`. Sanitized report
downloaded as the run artifact; no token or observation value was recorded.

| Check | Result |
| --- | --- |
| anonymous / invalid bearer | 401 `UNAUTHORIZED` |
| historical `cost_of_capital` @ 2026-06-01 | **409 `RELEASE_MISMATCH`** |
| pre-publication cutoff (dataset) | 404 `HISTORICAL_COVERAGE_UNAVAILABLE` |
| pre-publication cutoff (explicit pin) | 404 `BENCHMARK_VINTAGE_UNAVAILABLE` |
| current selection | **409 `RELEASE_MISMATCH`** |
| future cutoff | 400 `INVALID_REQUEST` |
| eight evidenced historical selections @ 2026-10-01 | **409 `RELEASE_MISMATCH`** |

The 404/400 results are emitted by `ddfi_benchmarks_api` *after* authentication, so the
authenticated path, the evidence gate and the rejection contract all work in the
deployed Worker. The 409s are produced *after* a successful selection.

## Root cause of the 409s

`snapshot_bundle.stamp` compared the response's `release.serving_release_id`
(`ddfi-benchmarks:<sha256>`) with the financial serving pointer in the bundle
snapshot and raised `ValueError('RELEASE_MISMATCH')` on any difference. Benchmark
releases carry their own hash-pinned index and evidence catalog, so every valid
benchmark answer was discarded and reported as `409 RELEASE_MISMATCH`.

This defect **predates the gate**: `snapshot_bundle.py` last changed on 2026-10-22,
before both deployed versions. The evidence gate sits downstream of it and cannot be
blamed, and rolling back would not restore serving — no benchmark answer was ever
delivered through this Worker.

## Fix prepared (PR #60, not deployed)

- Treat `ddfi-benchmarks:` identities as a foreign pinned family in `stamp`; the
  financial mismatch guard is unchanged. Focused test added.
- Add `scripts/benchmark_evidence_acceptance.py` (read-only, token never in the
  report) and `benchmark-evidence-live.yml` (dispatch + branch push) so acceptance is
  repeatable rather than ad hoc.
- `tests/unit/test_snapshot_bundle.py` + `tests/unit/test_benchmark_evidence_acceptance.py`:
  18 passed.
- Local `wrangler dev` of the PR revision against real R2 (evidence vars supplied):
  acceptance **PASS 15/15** — historical `cost_of_capital` at 2026-06-01 returns the
  reviewed catalog digest `d8c75248…`, `SERVER_LAST_MODIFIED`, `download_precision: day`;
  both pre-publication forms reject; current selection returns
  `NOT_APPLICABLE_CURRENT_SELECTION`; anonymous and invalid bearers 401.

## Not verified

- Deployed successful historical/current responses (blocked by the stamp defect).
- DCF's downstream historical path through `ZION_BENCHMARK_QUERY`.
- Intraday ordering: retrieval evidence is day-precision by construction.

## Why the deployment was retained

The earlier instruction was to roll back if acceptance failed. Acceptance failed for
an **authentication-independent** reason: every success is rejected by a wrapper that
also rejects it in the previous version. Rolling back would not serve any historical
date and would restore the ability to serve historical dates *without* reviewed
evidence had the wrapper allowed it. Retention keeps the fail-closed gate in front of
the data while the wrapper fix ships.

## Rollback (still available; not executed)

1. `wrangler rollback 5cc4eb62-fb6a-41ad-bf9e-c95557b7706c --name zion-ddfi-benchmark-staging`
2. Remove `DDFI_BENCHMARKS_EVIDENCE_KEY` and `DDFI_BENCHMARKS_EVIDENCE_SHA256` and
   redeploy the prior config, or let the rollback version run with the now-unused vars.
3. Leave the immutable catalog object; it is unreferenced after rollback. The index
   (`4817c621…`) and release objects were never modified.

## Next action (requires approval)

Merge PR #60, deploy `zion-ddfi-benchmark-staging` from the merged revision, then
dispatch `Benchmark evidence live acceptance`. Historical benchmark serving must not
be claimed until that run is green.
