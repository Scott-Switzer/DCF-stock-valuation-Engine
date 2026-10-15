# DCF staging: live end-to-end verification (2026-10-15)

The DCF Worker now retrieves Zion data, values a scenario, saves it and exports it **in
staging**, against the live Zion staging pair. This file is the receipt; the machine
receipt is [staging-verification.json](receipts/staging-verification.json), produced by
[scripts/verify_staging_e2e.py](../scripts/verify_staging_e2e.py).

```
python3 scripts/verify_staging_e2e.py \
    --base https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev \
    --output docs/receipts/staging-verification.json
# checks: 18  failures: 0
```

## 1. What is deployed

| Item | Value |
| --- | --- |
| DCF Worker (verified) | `dcf-valuation-engine-staging-zion`, version `38191751-f893-4f5a-b339-2cc0bd51987c`, commit `628ec5e`, `tracked_dirty: false` |
| Origin | `https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev` |
| Branch | `codex/zion-benchmark-binding` (worktree `/Users/scottthomasswitzer/Documents/Secret/.dcf-staging-deploy`) |
| D1 | `dcf-valuations-staging` (`cb4e6d0f-…`); migration `0009_equity_claims.sql` applied |
| Zion thin staging | `zion-financial-serving-v2-thin-staging`, version `bab55224-3fe9-4f96-8535-15caa6f61dca` |
| Zion benchmark staging | `zion-ddfi-benchmark-staging` (unchanged) |
| Secrets set (names only) | `RECORD_SALT`, `ZION_SERVICE_TOKEN`, `ZION_HISTORY_TOKEN`, `ZION_BENCHMARK_TOKEN` — staging values only, never printed |

Staging-only credentials were created with `wrangler secret put` from the operator's own
local files. `ZION_SERVICE_TOKEN` is a new staging-only value held by both Workers, and it
is accepted **only** on `/private/v1/equity-claims`; `ZION_HISTORY_TOKEN` and
`ZION_BENCHMARK_TOKEN` are the staging private bearer the Zion Worker already held.

## 2. The verified chain (18 checks, 0 failures)

| Check | Result |
| --- | --- |
| `/health`, `/ready` | 200, commit `628ec5e`, `tracked_dirty: false` |
| `/api/equity-claims/status` | 200, binding `ZION_FINANCIAL_QUERY`, scoped credential configured, caller `dcf-valuation-engine` approved |
| `/api/providers` | `zion_benchmarks` and `zion_valuation` configured |
| `provider=zion_history` (AAPL, MSFT, GOOGL) | 200, `zion-native-history-v1`, `historical_cutoff 2026-09-24T00:00:00Z`, evidence attestation `zion-native-evidence-mac-v1` |
| `POST /api/equity-claims/bridge` (AAPL) | **201**, EV 1,678,931,860,843.83, equity 1,739,874,860,843.83, per share **119.21703451950214** |
| … (MSFT) | **201**, EV 2,046,624,766,262.03, equity 2,016,579,766,262.03, per share **271.57328289297936** |
| … (GOOGL) | **201**, EV 2,179,137,903,112.57, equity 2,311,757,903,112.57, per share **188.18558019134235** |
| Arithmetic vs the verified local run | equal to the last digit for all three filers |
| Claims transport | `attestation.transport = CLOUDFLARE_SERVICE_BINDING`, `binding = ZION_FINANCIAL_QUERY`, `audit.authenticated_via = SERVICE_CREDENTIAL`, `caller = dcf-valuation-engine`, `authorized_paths = ["/private/v1/equity-claims"]` |
| Evidence lineage | engine release `b39a670b…`, `reconciliation_status = MEMBER_SHA256_AGREES_WITH_ENGINE_PINNED_MEMBER`, `snapshot_date 2026-09-24` |
| Valuation date vs evidence cutoff | `bridge_valuation_date = 2026-10-15`, `evidence_cutoff = 2026-09-24`, `served_cutoff_utc = 2026-09-24T23:59:59.999999999Z`, `cutoff_policy = DATE_ONLY_END_OF_DAY_UTC_V1` — separately named, never conflated |
| Benchmark assumptions | `wacc`, `tax_rate`, `sales_capital` resolved through the benchmark Worker |
| Saved + exported | export 200, `Content-Disposition: attachment; filename="AAPL-equity-claims-42fb2f5a….json"`, 199,811 bytes, carrying the same per-share value |
| Library isolation | a second library identity gets 404 for the same record |
| Foreign `Origin` write | 403 `Cross-site writes are not allowed.` |
| Wrong engine pin | 503 wrapping the internal 409 `SOURCE_VERSION_CHANGED` |

## 3. Two defects the live run found (both fixed)

1. **The benchmark leg could not reach a sibling Worker.** With the public origin
   configured, the bridge failed with `Expecting value: line 1 column 1 (char 0)`: a
   Worker's subrequest to another Worker's public hostname **on the same zone** is refused
   by the edge with a plain-text `error code: 1042`, so `requests` parsed a non-JSON body.
   Measured directly with a throwaway probe Worker: same-zone worker → 404 `error code:
   1042`, `https://example.com` → 200. Fixed by binding the leg to its own Worker
   (`ZION_BENCHMARK_QUERY`) and adding a `requests`-shaped `post` to the binding transport.
2. **The first attempt of that fix bound to the wrong Worker.** `service_binding()` was
   hardcoded to the financial query binding, so the benchmark request went to the financial
   Worker and answered `INVALID_REQUEST: unsupported operation`. `service_binding()` now
   takes the binding name, and a regression test pins `ZION_BENCHMARK_QUERY`.

## 4. Concurrency: the shared staging name is not mine right now

`dcf-valuation-engine-staging` (the plain staging name) was overwritten twice by another
thread while this work ran: version `90f16e31` at 23:12 and `a5bd33fe` at 23:27, both from
the `editor-fill-fix` line (`db356869`), which contains no Zion routes — `/api/equity-claims/status`
answers 404 there. My verified revision is therefore live on the dedicated staging worker
`dcf-valuation-engine-staging-zion` (same bindings, same staging D1, same secrets), and the
configuration that would move it back to the shared name is committed on the branch.

Two related notes for whoever owns the shared name:

* The committed revision references `fcfe_valuation.py` and `apv_valuation.py`, which are
  still untracked in the main checkout and are **not** in `scripts/embed_assets.py`'s module
  list, so `tests/test_worker_bundle.py` fails on the main checkout and a deploy of that
  revision cannot import them at runtime. That is in-flight work of the other thread.
* Secrets and D1 state are per-Worker-name, so activating the verified revision on the
  shared name needs the same three secrets there (they are already set) and nothing else.

## 5. Not done here

* No production Worker, route, binding or publication pointer was touched.
* The issuer-universe coverage workstream (readiness index, screening endpoint, SEC release
  refresh) has not started; the verified universe screen remains the September release.
