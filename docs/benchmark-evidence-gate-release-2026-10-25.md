# Benchmark evidence gate — release receipt (2026-10-25)

Status: **deployed; configuration verified; authenticated acceptance blocked.**
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

## Verified

- Local: 98 passed, 2 skipped (`tests -k "benchmark or private_api"`), including the
  two P1 review findings (nested evidence digest, UTC day comparison) and a
  warm-cache test that no longer clears the cache it depends on.
- CI on #58: `existing-data-contract` and `full-offline-suite` pass. #59 merged with
  every runnable check green and Greptile still pending, not failed; #58's final
  rebase ran no Greptile job.
- Deployed module exercised offline against the **real** index, catalog and release
  bytes: 8/8 datasets resolve `EXACT_PINNED_HISTORICAL` with `SERVER_LAST_MODIFIED`,
  `day` precision; a pre-publication cutoff returns `HISTORICAL_COVERAGE_UNAVAILABLE`;
  current selection returns `EXACT_PINNED` with
  `NOT_APPLICABLE_CURRENT_SELECTION`.
- Live anonymous request to `/private/v1/query` returns **401 UNAUTHORIZED**.

## Not verified

- Authenticated endpoint calls: both development tokens in the local `.dev.vars` were
  rejected with 401, and the deployed secret is write-only. No authenticated
  historical response has been observed in production.
- DCF's downstream historical path was not exercised.

## Rollback (complete)

1. `wrangler rollback 5cc4eb62-fb6a-41ad-bf9e-c95557b7706c --name zion-ddfi-benchmark-staging`
2. Remove `DDFI_BENCHMARKS_EVIDENCE_KEY` and `DDFI_BENCHMARKS_EVIDENCE_SHA256` and redeploy the prior config, or let the rollback version run with the old vars (unused by old code).
3. Leave the immutable catalog object; it is unreferenced after rollback. The index
   (`4817c621…`) and release objects were never modified.

Decision: the worker was left deployed. Its failure mode is fail-closed 503 for
historical requests, current selection is unchanged, and the exact deployed code
passed real-byte exercise; rolling back would restore serving historical dates
without reviewed evidence. Complete authenticated acceptance before relying on the
gate operationally.
