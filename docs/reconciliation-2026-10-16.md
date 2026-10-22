# Reconciliation of the v4 model line with the verified staging bindings

Branch `integration/unified-valuation` (merge commit `4dc2644`) joins the two lines that had
grown apart on the same files:

* `feat/v4-model-integration` (`c6e5faf`) adds `fcfe_valuation.py`, `apv_valuation.py` and
  `bank_excess_return.py` with their tests and financial-issuer routing;
* `codex/zion-benchmark-binding` (`f737b6e`) moves the equity-claims leg *and* the DDFI
  benchmark leg onto internal Cloudflare service bindings and records the live verification.

The merge is clean: the only overlapping edit was `app.py`, where the benchmark leg keeps the
binding transport (`ZION_BENCHMARK_QUERY`) while the new models keep their own bundled modules
and dispatch. `scripts/embed_assets.py` still lists every model module, so the merged bundle
carries `fcfe_valuation.py`, `apv_valuation.py` and `bank_excess_return.py`, and each bundled
module imports in a plain interpreter except `worker.py`, which imports the Workers-only `js`
module and can only load in the runtime.

## Verification on the merged revision

| Check | Result |
| --- | --- |
| `pytest tests/ -q` | **848 passed**, 0 skipped (includes the cross-repo claims contract test) |
| `ruff check .` | clean (7 pre-existing findings in inherited files fixed) |
| `node --check static/js/app.js` | clean |
| `scripts/embed_assets.py` + import every bundled module | 44 modules, only `worker.py` runtime-only |
| `pywrangler deploy --dry-run --env staging` | 393 modules, both Zion bindings, R2 and staging D1 |
| Live `scripts/verify_staging_e2e.py` | **18 checks, 0 failures** |

The live run was executed against
`https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev`, version
`73843326-0b6d-468e-9320-f85a3a1315bb`, revision `4dc2644`, `tracked_dirty: false`, with
`--expected-commit` gating `/health` so the receipt names the revision it actually exercised.
AAPL 119.21703451950214, MSFT 271.57328289297936 and GOOGL 188.18558019134235 all reproduce
the local run, each export stays library-scoped (a second identity gets 404), and the refusals
hold (foreign Origin 403, wrong engine pin 503 wrapping the internal 409).

## Two harness defects found while reproducing

1. **A cached probe can name a stale revision.** The staging environment enables the platform
   cache, so `/health` answered with the *previous* commit minutes after a successful deploy.
   Every read probe is now cache-busted, and `--expected-commit` fails the run when the served
   revision is not the expected one. A receipt that does not name its revision is not evidence.

2. **A fixed valuation date cannot use a `current` benchmark selection.** The engine refuses a
   selection that says "use the newest release" for a valuation dated in the past, by comparing
   the valuation date with the wall clock. The harness pinned `2026-10-15`, so it passed on the
   day it was written and failed on the next one. A valuation dated before the runtime's current
   UTC day is a reproduction of a past date against an explicitly pinned release, which the
   harness now expresses as `historical` mode with the same release pin. The product rule was
   left as it is: the correct long-term fix is to compare the pinned release's publication date
   with the valuation date instead of the wall clock, which is a behaviour change that deserves
   its own decision rather than a silent edit inside a verification harness.

## Deployment state

| Environment | Revision | State |
| --- | --- | --- |
| `dcf-valuation-engine-staging-zion` (dedicated) | `4dc2644` | deployed and live-verified (this receipt) |
| `dcf-valuation-engine-staging` (shared) | `a5bd33fe` (editor line) | **unchanged** — not touched by this work |
| `dcf-valuation-engine` (production) | unchanged | **unchanged** — no production Worker, route, binding or publication pointer touched |

Production still deliberately lacks `ZION_FINANCIAL_QUERY`/`ZION_BENCHMARK_QUERY`: every Zion
data plane in this account is a staging deployment, so binding the production Worker to them
would make a production release depend on staging. That stays a separate decision.

Reproduce:

```bash
uv sync
python scripts/embed_assets.py
pytest -q
uv run pywrangler deploy --env staging --config wrangler.verify.jsonc --keep-vars
uv run python scripts/verify_staging_e2e.py \
    --base https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev \
    --expected-commit "$(git rev-parse HEAD)" \
    --output docs/receipts/staging-verification.json
```
