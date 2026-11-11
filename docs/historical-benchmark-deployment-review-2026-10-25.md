# Historical benchmark serving — deployment review (2026-10-25)

Status words: **verified now** (command run 2026-10-25), **recorded** (earlier
receipt/doc), **unverified**.

## 1. The deployed path is not the local loader

`app.py::resolve_benchmark_selections` has two sources. Only one is reachable in the
deployed Python Worker:

| Source | Mechanism | Deployable? |
|---|---|---|
| `zion` | `ZION_BENCHMARK_QUERY` service binding to `zion-ddfi-benchmark-staging` (HTTPS fallback with `ZION_BENCHMARK_TOKEN`) | Yes — bound in `wrangler.jsonc` (staging + production) and `wrangler.production.jsonc` |
| `release` | `DAMODARAN_RELEASE_ROOT` filesystem path → `load_benchmark` | **No.** A Python Worker has no repo filesystem, and no wrangler config sets the var. This path is for local tools/tests only |

So a catalog placed beside `Documents/Secret/data/ddfi/registry/assumption_releases`
changes nothing in production. Setting `DAMODARAN_RELEASE_ROOT` there would not help.

## 2. What the deployed benchmark service actually reads (verified)

Chain: DCF Worker → `ZION_BENCHMARK_QUERY` → `deploy/cloudflare-query/src/thin_worker.py`
→ `ddfi_benchmarks_api.query_benchmarks` → R2 `MARKET_DATA`
(`financial-system-datasets`) → `gold/ddfi-benchmarks/v1/index.json` → per-release
`manifest.json` + `normalized.json` (never `source.bin`).

- Index key and digest are pinned in the Worker vars:
  `DDFI_BENCHMARKS_INDEX_KEY=gold/ddfi-benchmarks/v1/index.json`,
  `DDFI_BENCHMARKS_INDEX_SHA256=4817c621…` (both wrangler configs in
  `zion-ddfi-benchmark-worktree`).
- **Live read (read-only, anonymous, 2026-10-25):** the object exists, is 7,592 bytes,
  and its sha256 is exactly `4817c621389ee06b65254d716573a43633b9a58a9572e57b11f7b2e4ac558ce2`.
  It is `ddfi-benchmark-index-v1` with **8 releases**, ids and `published_at` values
  identical to the current registry manifests (and to the candidate catalog).
- Deployed worker version: `5cc4eb62-fb6a-41ad-bf9e-c95557b7706c` (2026-10-15,
  secret change); previous upload `626acf5c-4371-411a-a958-0127d7dfa9b9`.
- Historical selection: `_select_release` picks the newest entry with
  `published_at <= as_of`; no cutoff match fails with `HISTORICAL_COVERAGE_UNAVAILABLE`;
  exact release ids are supported and mismatches return `RELEASE_MISMATCH`.

All eight registry releases have `published_at == server Last-Modified date` and a
recorded `evidence_sha256` in `manifest.lineage` (checked this hour). The index dates are
therefore server-derived, but that is a build-time fact, not a serve-time check.

## 3. The divergence that matters

The deployed service trusts `index[].published_at`. The DCF local loader (`source:
release`) requires a byte-bound, reviewed-evidence catalog. Both can be "correct" yet
they are different policies:

- Historical requests through Zion (`source: zion`, `mode: historical`) are served by
  the index, **without** consulting any publication-evidence catalog.
- Historical requests through the local loader are refused unless the catalog binds the
  exact bytes.

This is an owner decision, not a defect to fix silently: either the deployed serving path
adopts the evidence gate, or the index date is formally accepted as the record.

## 4. Release options

**Option A — evidence-gated serving (implemented in a PR, not merged or deployed).**
[zion-terminal #58](https://github.com/Scott-Switzer/zion-terminal/pull/58) adds the gate in
`ddfi_benchmarks_api.py`: historical selection loads a hash-pinned catalog object
(`DDFI_BENCHMARKS_EVIDENCE_KEY` / `_SHA256`) through the same `pinned()` reader and cache as
the index, then requires an entry for the exact release id whose `source_sha256` matches the
served manifest's `source.bin` digest, whose publication date agrees with index and manifest,
and whose method, statement, observation and download bounds pass. Missing, malformed,
conflicting or unreviewed evidence returns 503 before any observation is served. Current
selection never reads the catalog and is unchanged.

The PR deliberately does not set the catalog vars, so merging it makes historical requests
fail closed until the catalog and its digest are published and configured in the same
deploy. Tests: 94 passed, 1 skipped (`pytest tests -k "benchmark or private_api"`).

**Option B — accept index dates.** No code change. Document that historical availability
is the index's `published_at`, which is server-derived at build time but unverified at
serve time, and that per-request evidence binding remains a DCF-local property.

Neither option was executed.

## 5. Release and rollback (for Option A, when approved)

- Code revision: the benchmark repo commit that adds the gate (currently uncommitted; no
  PR opened).
- Data: new immutable R2 object(s) only. The publisher
  (`data/ddfi/scripts/publish_ddfi_benchmark_releases.py`) never overwrites an existing
  release key; add the catalog under a new key rather than replacing the index.
- Configuration: new/updated `DDFI_BENCHMARKS_EVIDENCE_*` vars plus the existing index
  sha; if the index itself is rewritten, pin the new digest.
- Prior state to restore on rollback: worker version `5cc4eb62-fb6a-41ad-bf9e-c95557b7706c`,
  the current index sha `4817c621…`, and the prior var values. R2 release objects are
  immutable and need no restore.
- Rollback is a worker version rollback plus var restore; it is **not** "delete the
  catalog" alone.

## 6. Acceptance (authenticated; not run here)

Use the existing sanctioned harness `data/ddfi/scripts/e2e_ddfi_zion_dcf_acceptance.py
--live`, plus targeted private-query calls:

1. An evidenced release at an eligible cutoff → `HISTORICAL_AS_OF`/`EXACT_PINNED_HISTORICAL`
   with the expected release id and `published_at`.
2. One day before `published_at` → `BENCHMARK_VINTAGE_UNAVAILABLE` / coverage error.
3. Removed or mismatched evidence entry → refusal (Option A only).
4. Altered release digest → `BENCHMARK_INTEGRITY_FAILURE`.
5. Current mode (`as_of` absent) still serves the newest release.
6. Anonymous request → the private route's `401` (its owning contract; verify rather than
   assume for any other endpoint).
7. Returned `release` block: `ddfi_release_id`, `source_sha256`, `index_sha256`,
   `rights`, and (Option A) an evidence identifier.

Not verified this hour: any authenticated call, so deployed *behavior* is still
**unverified**; only the deployed *configuration and stored index* are verified.

## 7. What the candidate does and does not establish

The candidate catalog establishes **eligibility**: for these exact preserved release
bytes, a reviewed server timestamp exists and the DCF loader resolves historical
selection. It does not establish that the deployed service uses it, nor eight complete
historical series.
