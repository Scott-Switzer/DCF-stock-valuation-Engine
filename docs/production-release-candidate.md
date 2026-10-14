# Production release candidate: `692d8ef` (PRs #17–#30; runtime code `63130e6`)

Production currently serves `c56df1d` (Worker version `3d504ea8-…`, deployed 2026-10-08).
This manifest covers the commits between `c56df1d` and current `main` `692d8ef`
so the release can be approved and executed as one controlled step. No production
resources have been changed; staging carries the candidate runtime now.

Build identity note: staging `/health` currently reports runtime commit `63130e6`
(PR #29) because #30 (`692d8ef`) is docs-only and staging was built before it.
The build script embeds the checked-out Git HEAD, so a fresh build from current
`main` must report `692d8ef` with `tracked_dirty:false`. Verify that value after
deploy; `63130e6` on staging is the expected pre-release runtime, not a mismatch.

## Scope (merged, CI green on 3.12 + 3.13)

- #17 structured transport receipts + non-saving pipeline audit
- #18 per-stage load timings + Server-Timing headers
- #19 isolated staging Worker environment for tracing
- #20 common-income numerator only when bridged to the filing
- #21 Instant Investment Research Brief in the ticker-first workspace
- #22 preferred equity derived from filed common-equity buildup
- #23 baseline brief in load bundle; lifecycle marks; SEC-first source label
- #24 staging-only PPE pointer override (candidate releases)
- #25 edge-cache packet GETs, traces, concurrency probe
- #26 edge-cache safety (user pages `private, no-store`), load payload dedup,
  live brief sync on assumption edits
- #27 browser benchmark, brief-sync hardening, skipped-brief explanations
- #28 D1 cache-hit instrumentation (current-request `hit_breakdown`)
- #29 bundled baseline preview (first value renders with the load response)
- #30 release manifest itself (docs-only; no runtime change — hence staging health still reports `63130e6` until rebuilt from `692d8ef`)

## Verification on staging (runtime commit `63130e6`; `main` is `692d8ef` docs-only)

- Full suite 636 passed + 10 subtests, `ruff` clean, 3 Node harnesses green.
- Real-Chromium benchmark, per ticker × actual cache state (evidence retained
  under `find/outputs/perf/`, reproducible via `scripts/bench_browser.mjs`):
  warm HIT value-painted — AAPL p50 510ms / p95 1691ms (n=11), MSFT p50 459 /
  p95 2331 (n=12), PEP p50 255 / p95 528 (n=11). Before this sprint the same
  harness measured warm p50s of 573–853ms and p95s near 3.1s.
- Load responses halved vs production (decoded AAPL 231KB → 116KB, MSFT
  192KB → 98KB, PEP 50KB → 26KB); zero `/api/brief` requests on unedited loads.
- Bundled preview ≡ iframe-preview evaluation (Python + Node parity tests).
- Cache safety: 8/8 live staging checks (revoked links 404 for both users,
  `cf-cache-status: BYPASS` on user content, per-user watchlist isolation).
- SEC-first PEP on staging: gate passes, no Yahoo annual-fundamental calls,
  browser value renders; packet shows preferred-equity 0.0 via filed buildup
  residual (accession 0000077476-26-000007), 3 annual periods, 1.373B diluted shares.
- O fails fast with an explicit missing-input reason; MRX explains its skipped
  baseline brief instead of rendering nothing.

## Production compatibility

- D1 `dcf-valuations`: `wrangler d1 migrations list --remote` reports nothing to
  apply (migrations 0001–0008 all predate the current production build).
- Bindings identical (Zion services, `PPE_DATA` R2, production D1). No new secrets.
  `PPE_POINTER_OVERRIDE` exists only in the staging env; production keeps reading
  authoritative `control/valuation/CURRENT.json` (untouched).
- Workers Caching (`cache.enabled`) and 100% trace sampling are staging-only;
  production keeps sampling 0.1 and no tiered cache. The `private, no-store`
  headers ship with this release and protect production heuristic caching too.
- `/api/diag/concurrency` returns 404 outside staging (environment-gated).
- Rate limits use separate staging/production namespaces.

## Deployment record (executed 2026-10-14, approved release)

- Commit `d1008a0` (PR #31 manifest fix on `692d8ef`), clean tree, CI green 3.12 + 3.13.
- `python3 scripts/embed_assets.py` exit 0; `wrangler deploy` to production bindings.
- Production Worker version `137718bd-49f6-4f88-ab68-f67fdf5dd34a`; `/health`
  reports commit `d1008a06b7c787b050d851335f9f4c67620ee83b`, `tracked_dirty:false`.
- Live smoke: AAPL 91.81 / MSFT 119.40 / PEP 196.95 baselines with bundled brief
  + preview; account 401 gates, no unauth writes; unknown share 404; packet
  export 200; BAC/O fail fast; MRX explained skip; `private, no-store` live.
- `control/valuation/CURRENT.json` sha256 `ecf1e1c4…` byte-identical before,
  during and after. No D1/R2 production data changes, no migrations.
- Authenticated two-account save/share/revoke verified on staging (14/14 account
  checks + full share→revoke→404 cycle); same flow in production remains a gap
  (no test identities created in prod without separate authorization).
- Rollback reference unchanged: `3d504ea8-2d06-4f88-ab68-f67fdf5dd34a`.
  (This section is docs-only and does not affect the deployed bundle.)

## Release (requires approval — do not run yet)

```sh
python3 scripts/embed_assets.py && wrangler deploy
```

then verify `/health` reports commit `692d8ef` (fresh build from `main`, `tracked_dirty:false`), smoke-test one ticker load,
one save/share/revoke cycle, and confirm `control/valuation/CURRENT.json`
is byte-identical before and after.

Rollback reference: production Worker version `3d504ea8-2d06-4f88-ab68-f67fdf5dd34a`
(`wrangler rollback` or redeploy the prior version).

## Known non-blockers

- Warm p95 (1.7–2.3s on AAPL/MSFT) misses the 2s aspiration; p50s are
  0.26–0.51s. Tail is D1 read spikes (measured 688/823ms on the two slowest
  HITs; Python JSON/hash/copy stages measure 0.0ms), not application CPU.
- Cold MISS carries 0.3–0.9s unattributed runtime overhead beyond provider stages.
- XOM/MRX/O gate blockers and the BAC/JPM pointer gap are unchanged and do not
  block release (strict fallbacks + visible explanations verified).
