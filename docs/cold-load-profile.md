# Cold-load profile on the post-release baseline

Measured 2026-10-14, production (`d1008a0`) and staging (`e26eeee`), real
requests, `load_summary.stage_seconds`, assembly-cache MISS only.

## The old 0.3–0.9s unattributed overhead does not reproduce

| Ticker | Env | Elapsed | zion_packet | yahoo | sec_class | Unattributed |
| --- | --- | --- | --- | --- | --- | --- |
| KDP | prod | 2.17s | 0.923 | 0.783 | 0.468 | −0.004 |
| DELL | prod | 1.71s | 0.679 | 0.612 | 0.419 | 0.000 |
| KDP | staging | 1.73s | 0.382 | 0.770 | 0.575 | ~0 |
| DELL | staging | **0.65s** | 0.031 | 0.415 | 0.204 | ~0 |
| KO | staging | 2.03s | 1.447 | 0.587 | 0.000 | ~0 |

Every cold MISS is **fully attributed** to three sequential I/O stages. Python
JSON/hash/copy/response stages still measure 0.0ms. There is no application
overhead left to optimize.

## What the numbers actually show

- The floor is **0.65s** (DELL staging MISS): edge-cached pointer + fast Zion
  404 + Yahoo + registry classification. Edge caching (`_object_json` via
  `caches.default`, 60s pointer TTL) already works — it is the entire reason
  DELL costs 0.65s while KDP costs 1.7s on the same code.
- Variance is provider/edge latency: pointer R2 reads (up to ~500KB index),
  Zion 404 round trips, Yahoo statement latency, and live SEC classification
  lookups (0.2–0.6s when the ticker is not registry-confirmed).
- KO's 1.447s `zion_packet` is a pointer-hit packet fetch + validation before
  Yahoo still runs — worth revisiting only if packet-hit tickers show a
  systematic penalty, which this sample (n=1) does not establish.

## Deliberately not shipped

Overlapping `sec_classification` with the statement build would save ~0.2–0.6s
on cold MISS, and the staging concurrency probe proves overlap is possible in
principle — but threading `run_sync` provider pipelines inside the Workers
Python runtime is unvalidated here, and the instruction bars speculative
rewrites without end-to-end measurement. No memoization was added (prior
sprints already ruled it out: the memoized stages measure 0.0ms).

Next step if the tail still matters: a staging-only overlap experiment behind
the existing diagnostics, measured with real Chromium + Server-Timing before
any production consideration.
