# Production release candidate: `655aa2f` + tax-route fix (code-only; packets separate)

> Release-identity correction: the prior revision of this record targeted
> runtime commit `b9993a3`/`db35686` while `main` has since advanced through
> PRs #51–#52 to `655aa2f`. A build from `main` embeds the current Git SHA,
> so the deployment and the health check must agree on the commit actually
> released. This revision re-targets the candidate to clean `main`
> `655aa2f` (PRs #49–#52) plus the narrow tax-route fix in this branch
> (unreachable explicit-tax-policy route in `auto_loading.load_method`;
> regression test
> `test_auto_loading_tax_only_gate_uses_sec_first_with_explicit_policy`).
> The exact release SHA is the merge commit of that fix PR and is recorded
> post-merge in the machine-readable receipt
> `find/outputs/release-readiness/release-receipt.json` — this document is
> NOT re-edited with the merge SHA, breaking the merge-SHA/document-update
> loop. Staging currently serves `655aa2f` clean (see below); post-merge,
> staging MUST be redeployed from the receipt SHA and `/health` MUST report
> it with `tracked_dirty:false` before any GO decision. Production serves
> `d1008a0` and is untouched.
> **No production deployment is authorized by this document.**
>
> Superseded candidates `b9993a3` and `db35686` are retained in git history.

Candidate: fix-PR merge over base `655aa2f`. Production serves `d1008a0`
and is untouched. **No production deployment is authorized by this
document.**

Prior release record (PRs #17–#31, production `d1008a0`) is superseded as
the running candidate but retained in git history
(`git show d1008a0:docs/production-release-candidate.md`).

## Scope: code in staging but not in production

Merged, CI green on 3.12 + 3.13. Grouped by area (full list:
`git log --oneline d1008a0..655aa2f`, plus the tax-route fix here):

- Preproduction tax API (#49–#50): `/api/load/dcf` accepts and validates
  `tax_override`/`tax_scenario`; `load_cached_method` and `load_method`
  forward them; explicit-policy loads bypass the shared assembly cache
  (`BYPASSED`, never stored under the ticker/date key); Yahoo path records
  an explicit selection over the default policy without mutating history.
- Explicit WACC mode (#49 + #52): `recalculated` vs `fixed` travels in the
  form, raw assumptions, saves, exports and compare posts; the Research
  Brief now labels the selected mode (`wacc_mode` + basis note) instead of
  hardcoding `recalculated`.
- Scenario provenance (#49): arbitrary filing strings are accepted but
  labeled `unverified_citation`; only an accession matching loaded packet
  provenance earns `packet_accession_matched`; overrides are
  `user_assumption`; defaults are `not_applicable_default`.
- Editor fill (#51): bundled-preview fast path fills the assumptions
  editor (negative control verified against unfixed code).
- **Tax-only SEC-first route (this fix, unmerged):** `load_sec_first()`
  already permitted a gate held up solely by
  `tax_forecast_assumption_required_*` with a valid explicit policy, but the
  outer `if gate["eligible"]` in `auto_loading.load_method()` made that
  exception unreachable in real automatic loading. The outer condition now
  mirrors the inner exception (`eligible OR (tax-only AND explicit)`), so a
  fully eligible packet takes the normal path, a tax-only-blocked packet
  with explicit policy enters SEC-first, all unrelated gate failures stay
  blocking, invalid policy evidence raises `ProviderError`, no Yahoo annual
  statements are fetched for a successful SEC-first load, history is never
  mutated, and explicit loads still bypass the shared cache. Covered by the
  new end-to-end `load_method()` integration test (negative latest ETR).

- Accounting policy + packets (#33–#35): source-independent normalization,
  audited add-backs, filing-date/context evidence, CAT advance.
- Candidate packet flow (#36–#40): CAT then PEP republication, staging-only
  pointer override, candidate-miss fallback to the production R2 index.
- PAYX (#43–#45): dual-identity zero claims, corrected income taxonomy with
  affirmative NCI evidence, balance-sheet economics + client-funds proof.
- Forecast-tax framework (#46): `tax_policy.py` separates signed history
  from forecast/shield assumptions; ABBV/AEP reconciliations + frozen runs.
- Live tax integration (#47): latest-only gate resolvability;
  packet→doc→policy→assumptions→brief route with explicit policies
  (`source.tax_policy`, Yahoo filed-ratio retention); recalculated vs
  fixed-WACC modes with labels (`wacc_basis_note`); workspace stale-shield
  recomputation; FY2025 reconciliations (AEP 13.4% correction); TS parity.
  Full suite now 771 passed (was 764 + growth + this fix), `ruff check`
  clean, worker bundle 2 passed.

## Scope: data packets (NOT part of a code release)

- Production `control/valuation/CURRENT.json` sha256
  `ecf1e1c4b56936bc6af7fd93fe1bccadc41b7c6885f5e07c661dec5a93c7b5c1`
  (237 companies) — re-read from live R2 2026-10-16, byte-identical
  before, during and after this assessment. No production D1/R2 writes, no
  migrations, no packet promotion.
- Staging-only `control/valuation/CANDIDATE-staging.json` sha256
  `ff7b1b08e6fc459468c07336543bb3b2f4dec9ac469a60a2b8d41ed91d7ad5da`
  lists CAT, ORCL, PAYX, PEP, T. Promoting any packet set is a SEPARATE
  data release with its own pointer update and rollback file (e.g.
  `find/outputs/company-packets/payx-pointer-rollback.json`). Staging
  candidate issuers remain a separate data-release decision; a production
  code deploy never promotes them.
- A production code deploy does not promote candidate packets and vice versa.

## Verification on staging (commit `655aa2f`, fresh 2026-10-16)

Staging serves the pre-fix merge commit clean; the new fix is covered by
local regression until the post-merge staging redeploy.

- `/health` (staging): commit `655aa2f669496d47235325a1b129b0c698019bd7`,
  `tracked_dirty:false`. Latest staging deployment `5a868b60-…`
  (2026-10-15T23:27Z), Worker version
  `a5bd33fe-363c-4524-afc2-de61dc593a9f`.
- Full Python suite **771 passed**, 10 subtests, on the fix branch
  (`.venv` Python 3.12.3); `ruff check` clean; `scripts/embed_assets.py`
  clean; `tests/test_worker_bundle.py` 2 passed. CI 3.12/3.13 green through
  #52; CI on the fix-PR merge SHA is pending by definition (unmerged).
- New regression
  `test_auto_loading_tax_only_gate_uses_sec_first_with_explicit_policy`
  passes: negative-latest-ETR packet, tax-only gate, explicit scenario ⇒
  `statement_source == "SEC-first"`, no `/timeseries/` fetch, signed
  history preserved, no-explicit ⇒ Yahoo fallback (not SEC-first), invalid
  override ⇒ `ProviderError`, unrelated bridge failure stays blocking even
  with explicit policy, explicit ⇒ assembly-cache `BYPASSED`.
- Staging cache isolation rechecked live on `655aa2f` (AAPL, Yahoo-only):
  first default load `MISS`, immediate second default load `HIT`, explicit
  `tax_scenario` load `BYPASSED` with `normalized_scenario` basis. Default
  intrinsic renders (AAPL ≈ 93.56 in this check).
- Prior staging evidence (inherited, unchanged code paths): CAT/PEP/T/PAYX
  SEC-first intrinsics exact vs pre-change build; PAYX bundled brief
  tax+WACC labels; ORCL intentional block; BAC SIC-6021 fail-fast; 24/24
  account/security cycle; real-Chromium PAYX render with 0 console errors.
  Not re-run on the new build (server-side brief/tax change covered by
  regression + live API above).

## Production smoke expectations (corrected for a code-only release)

A code-only release keeps reading the authoritative production
`CURRENT.json` — never the staging candidate index. Production smoke MUST
use securities available through the production source path and MUST NOT
require CAT, PEP, T or PAYX to load SEC-first merely because their staging
candidate packets work.

- Fresh 2026-10-16 read-only production smoke
  (`scripts/smoke_public.py --expected-commit d1008a0`): **PASS 7/7**
  (health, readiness, providers, ticker_search, sample, non_saving_preview,
  json_export). Production `/health`: commit
  `d1008a06b7c787b050d851335f9f4c67620ee83b`, `tracked_dirty:false`.
- Verified: Yahoo fallback path, brief + preview rendering, market inputs,
  identity, and JSON export — with no packet promotion and no production
  test accounts created. Signed-out/authenticated isolation remains covered
  by the inherited staging 24/24 cycle; production account flows are
  intentionally not exercised (no test identities in prod without separate
  authorization).

## Production compatibility

- D1: no migration changes since production (`migrations/0001–0008`
  untouched); nothing to apply.
- Bindings/secrets: identical (`ZION_VALUATIONS`, `ZION_DATASET_CATALOG`,
  `PPE_DATA` R2, production D1). `PPE_POINTER_OVERRIDE` exists only in the
  staging env. No new secrets, env vars, or scheduled tasks.
- Cache/auth: unchanged code paths except the tax-only routing exception,
  which cannot alter default (non-explicit) loads; staging-only Workers
  caching/trace sampling as before; user pages stay `private, no-store`.
- User/account + D1 compatibility: account flow verified against staging D1
  (24/24, inherited); production same-flow check remains a gap (no test
  identities created in prod without separate authorization) — unchanged
  from the prior release.

## Readiness matrix and GO/NO-GO

| Gate | Status | Evidence |
| ---- | ------ | -------- |
| Full Python suite + Ruff + embed + bundle | PASS (local) / PENDING (CI on merge SHA) | 771 passed + ruff clean + embed + bundle 2 passed on fix branch; CI green through #52, rerun required on fix-PR merge |
| TS/browser-engine parity (tax bounds) | PASS* | inherited; *TS engine is experimental/unused — not browser-parity proof |
| Staging serves pre-fix candidate `655aa2f`, clean tree | PASS | `/health` `655aa2f` + `tracked_dirty:false`, version `a5bd33fe` (fresh) |
| Staging serves fix-PR merge SHA, clean tree | PENDING by design | post-merge redeploy + `/health` check required; receipt records the SHA |
| Tax-only SEC-first route + cache bypass | PASS | new end-to-end regression + live staging MISS/HIT/BYPASSED recheck |
| Yahoo-only loads (AAPL, production path) | PASS | staging Yahoo + prod smoke 7/7 on `d1008a0` |
| CAT/PEP/T/PAYX staging parity | PASS (inherited) | intrinsics exact vs pre-change build; NOT a production requirement |
| ORCL intentional block | PASS (inherited) | preferred-cost refusal, no fallback invention |
| Negative-history docs + explicit scenarios | PASS | unit + integration tests; gate honors policy |
| Bank/REIT exclusions | PASS (inherited) | BAC SIC-6021 fail-fast live |
| Save/share/revoke isolation (staging) | PASS (inherited) | 24/24 live checks |
| Brief/preview/scenario tax+WACC labels | PASS | regression + live API fields |
| Workbook parity + security unit tests | PASS | in-suite, green |
| Real-browser staging test | PASS (inherited) | Chromium PAYX load, 0 console errors |
| Production pointer untouched | PASS | `ecf1e1c4…` re-read 2026-10-16, 237 companies |
| Candidate pointer separate | PASS | `ff7b1b08…` CAT/ORCL/PAYX/PEP/T; promotion is a separate decision |
| ABBV/AEP unlocked | BLOCKED by design | preferred-equity evidence still missing; no zero-derivation |

**Recommendation: code-only GO subject to post-merge staging redeploy.**
Rationale: every mandatory gate passes except the post-merge staging
redeploy, which is structurally pending until the fix PR merges; default
valuations are numerically identical, no migrations/bindings/secrets, and
data packets ride a separate pointer with independent rollback. Packet
promotion waits for its own evidence cycle.

## Release (requires separate approval — DO NOT RUN)

`wrangler.jsonc` defines NO `production` env: the top-level Worker
(`name: dcf-valuation-engine`) IS production; `env.staging` is the only
named environment. Therefore the production-targeted command is a bare
`wrangler deploy` with NO `--env` flag. The prior revision's
`wrangler deploy --env staging` deploys **staging**, never production.

The receipt pins an immutable **release SHA**, independently of a later
receipt-only documentation commit. Do not deploy whatever `main` happens to
point to after recording the receipt. Use a clean checkout of that exact SHA.
The original tax fix reached main by direct push as `e89956e`; the subsequent
release-control PR provides the reviewed merged staging target. No fix PR is
retroactively claimed.

```sh
# AFTER separate production approval only. These commands were NOT executed.
# Read the completed receipt from the operator checkout before checking out the
# release SHA, whose in-tree receipt necessarily predates final staging evidence.
RELEASE_SHA=$(python3 -c 'import json; print(json.load(open("find/outputs/release-readiness/release-receipt.json"))["release_sha"])')
test "$RELEASE_SHA" != None || exit 1
test -z "$(git status --porcelain --untracked-files=no)" || exit 1
git checkout --detach "$RELEASE_SHA"
test "$(git rev-parse HEAD)" = "$RELEASE_SHA" || exit 1
# Top-level config is production; no --env production exists.
uv tool run --from 'uv>=0.12.3' uv run pywrangler deploy --keep-vars
```

Staging-only command (authorized for this review):

```sh
uv tool run --from 'uv>=0.12.3' uv run pywrangler deploy --env staging --keep-vars
```

Before any separately approved production deployment, recheck production
`/health`, the exact active Worker version, the raw `CURRENT.json` digest and
production binding configuration against the completed receipt. Abort on drift.
After deployment verify `/health` reports the receipt SHA with
`tracked_dirty:false` and run non-saving smoke checks against production-source
securities. Candidate-company SEC-first loads are not a production requirement.

Rollback (code, requires production authorization): explicitly target the prior
production version recorded and freshly verified in the receipt:

```sh
wrangler rollback 137718bd-49f6-4c12-ae03-9776e01e7cfc --name dcf-valuation-engine
```

The completed receipt is committed separately after staging acceptance. Its
commit is evidence-only, not a new runtime release target. This avoids a
self-referential merge-SHA/receipt-update loop.

Rollback (data): not applicable — production pointers are not written by
this release; candidate pointer has its own per-publication rollback files.

## Known non-blockers

- `frontend/src/lib/dcf-engine.ts` is EXPERIMENTAL and unused by the
  shipped workspace, the Worker bundle (`scripts/embed_assets.py`
  `module_names`), and every test harness — the file header says so
  explicitly. The production calculation path is `dcf_code.py` served from
  the Worker. Tests of the TS engine MUST NOT be cited as proof of
  production browser parity; the margin-averaging drift (year-1 ratios vs
  historical means) needs a dedicated parity pass or removal — not this
  release.
- Ruff format is not CI-enforced (87 files repo-wide pre-existing);
  `ruff check` is clean.
- The current validation workflow syntax-checks shipped JavaScript with
  `node --check`; it does not run `tsc`. No TypeScript CI claim is made.
- Warm p95/cost notes from the prior release are unchanged.
