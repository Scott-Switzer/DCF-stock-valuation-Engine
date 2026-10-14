# Production release candidate: `63130e6` (PRs #17–#29)

Production currently serves `c56df1d` (Worker version `3d504ea8-…`, deployed 2026-10-08).
This manifest covers the 15 commits between `c56df1d` and release candidate `63130e6`
so the release can be approved and executed as one controlled step. No production
resources have been changed; staging carries the candidate now.

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

## Verification on staging (version `19213256-…`, commit `63130e6`)

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

## Release (requires approval — do not run yet)

```sh
python3 scripts/embed_assets.py && wrangler deploy
```

then verify `/health` reports commit `63130e6`, smoke-test one ticker load,
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
