# Handoff — benchmark consumer integration, V1 contract, UI readiness (2026-10-26)

## 1. Deployed benchmark service (already recorded)

Worker `zion-ddfi-benchmark-staging` `8af6d9d9-7c43-46cd-b58b-6e35d2ec9645`
(commit `ac83f11`), live acceptance run 40256588261, **PASS 16/16**. Not repeated here.

## 2. DCF consumer integration

**Verified through the real consumer code.** `resolve_benchmark_selections` (not a
reimplementation) was run against the benchmark service serving the deployed revision
from real R2 bytes:

| Case | Result |
| --- | --- |
| historical `cost_of_capital` @ 2026-06-01 | `HISTORICAL_PUBLISHED`, release `11c1e6bb…`, evidence `d8c75248…`, `day` precision, `coverage.as_of` 2026-06-01 |
| pre-publication cutoff 2026-01-11 | rejected `BENCHMARK_VINTAGE_UNAVAILABLE` — no fallback to current or release-root data |
| current selection | `CURRENT_EXPLICIT_SELECTION`, pinned release |

**Defect found and fixed (DCF PR #85).** The provider sent both `release_id` and
`dataset_id`; the private contract accepts exactly one. Every dataset-qualified
historical request failed with `INVALID_REQUEST`. The provider now sends only the
pinned release and asserts `release.dataset_id` on the response. The deployed Worker
`90d0531d` (2026-10-23) carries the defective provider.

**Not verified: the deployed DCF Worker itself.** `POST /api/calculate` with a
benchmark selection returns `401 OWNER_BENCHMARK_AUTH_REQUIRED` on
`dcf-valuation-engine-staging`; its `ZION_OWNER_DATA_TOKEN` is a write-only Worker
secret and the repository has no CI secret for it. Smallest owner action: add that
secret for an acceptance workflow, or issue one owner-authenticated request.
Deployed bindings are present and correct: `ZION_BENCHMARK_QUERY` →
`zion-ddfi-benchmark-staging`, `ZION_BENCHMARK_BASE_URL`, secret
`ZION_BENCHMARK_TOKEN`, `DEPLOY_ENVIRONMENT=staging`.

## 3. `StatisticalReferencePanelV1`

Intent resolved: **not active work for V1.** The 4-file edit lives only in the stale
duplicate `financial-system-core-workspace` (uncommitted, +222/−10 on `87001c1`).
`docs/fwf/08-calibration.md` labels it M10 preparatory work, the PPE producer still
emits `return_definition` as compact JSON text, and the vendored schema is
byte-identical to released V1 (`cf165c5b…`). Making the new fields required would
invalidate published panels, including the M9 acceptance artifact.

Core PR #29 adds a guard: the released schema digest is pinned, and the test fails if
`return_definition` becomes an object or `panel_definition` / `daily_returns` become
V1-required. No consumer was migrated. If M10 ships, it needs a V2 contract (or
optional-with-defaults under V1) landed with producer and QC together.

## 4. Coverage/freshness UI

Ready to release, not deployed. Per the foundation audit: assets `e60e753`, `ed22931`
are on `main`; deployed `/static/js/data-workspace.js` is the older 20,056-byte asset
(`230ab866…`) without the coverage strings, while the local asset (`4b27e14c…`) has
`financial-coverage`, `financial-warnings`, `financial-evidence`. `embedded_assets.py`
is staged but never deployed.

Release: clean `origin/main` → `python scripts/embed_assets.py` (so
`BUILD.tracked_dirty` is false) → `pytest tests/ -q` and `node --check` on the touched
JS → `npx wrangler deploy --config wrangler.production.jsonc` → re-fetch the asset and
confirm the hash and the three elements → run `live-smoke.yml`. Rollback is a redeploy
of the previous bundle; no data or D1 change.

Missing before calling it done: a rendered-panel DOM test. Existing tests cover the
module, not the panel output; the test should fail when the coverage element is
removed.

## 5. Remaining ranked work

1. Owner: authenticate the deployed DCF Worker (secret or owner session) and merge
   DCF #85, redeploy, then record one authenticated historical request.
2. Deploy the coverage panel and add its DOM test.
3. Decide M10 contract shape (V2 vs optional fields) before any producer change.
4. Publication evidence for release-root benchmarks (unchanged policy gap).
