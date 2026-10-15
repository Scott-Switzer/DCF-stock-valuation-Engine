# Production release candidate: `db35686` + sprint fix (code-only; packets separate)

> Release-identity correction: the prior revision of this record targeted
> runtime commit `b9993a3` while `main` had already advanced to `2bbb92a`
> (and now `db35686`). A build from `main` embeds the current Git SHA, so
> the deployment and the health check must agree on the commit actually
> released. This revision re-targets the candidate to clean `main`
> `db35686` (PRs #49–#51 over #48) plus the sprint fix in this branch
> (brief carries the explicit `wacc_mode`; regression test
> `test_brief_carries_explicit_wacc_mode`). The exact release SHA is the
> merge commit of that fix PR; staging MUST be redeployed from that clean
> commit and `/health` MUST report it with `tracked_dirty:false` before
> any GO decision. Production serves `d1008a0` and is untouched.
> **No production deployment is authorized by this document.**
>
> Superseded candidate `b9993a3` (Worker version
> `1e1af6ca-813a-4063-8d0d-09cff03e297d`) is retained in git history.

Candidate: clean `main` at the fix-PR merge (base `db35686`). Production
serves `d1008a0` and is untouched. **No production deployment is authorized
by this document.**

Prior release record (PRs #17–#31, production `d1008a0`, Worker version
`137718bd-49f6-4f88-ab68-f67fdf5dd34a`) is superseded as the running
candidate but retained in git history (`git show d1008a0:docs/production-release-candidate.md`).

## Scope: code in staging but not in production

Merged, CI green on 3.12 + 3.13. Grouped by area (full list:
`git log --oneline d1008a0..db35686`, plus the sprint fix here):

- Preproduction tax API (#49–#50): `/api/load/dcf` accepts and validates
  `tax_override`/`tax_scenario`; `load_cached_method` and `load_method`
  forward them; explicit-policy loads bypass the shared assembly cache
  (`BYPASSED`, never stored under the ticker/date key); Yahoo path records
  an explicit selection over the default policy without mutating history.
- Explicit WACC mode (#49 + this fix): `recalculated` vs `fixed` travels
  in the form, raw assumptions, saves, exports and compare posts; the
  Research Brief now labels the selected mode (`wacc_mode` + basis note)
  instead of hardcoding `recalculated`.
- Scenario provenance (#49): arbitrary filing strings are accepted but
  labeled `unverified_citation`; only an accession matching loaded packet
  provenance earns `packet_accession_matched`; overrides are
  `user_assumption`; defaults are `not_applicable_default`.
- Editor fill (#51): bundled-preview fast path fills the assumptions
  editor (negative control verified against unfixed code).

- Accounting policy + packets (#33–#35): source-independent normalization,
  audited add-backs, filing-date/context evidence, CAT advance.
- Candidate packet flow (#36–#40): CAT then PEP republication, staging-only
  pointer override, candidate-miss fallback to the production R2 index.
- PAYX (#43–#45): dual-identity zero claims, corrected income taxonomy with
  affirmative NCI evidence, balance-sheet economics + client-funds proof.
- Forecast-tax framework (#46): `tax_policy.py` separates signed history
  from forecast/shield assumptions; ABBV/AEP reconciliations + frozen runs.
- Live tax integration (#47, this release): latest-only gate resolvability;
  packet→doc→policy→assumptions→brief route with explicit policies
  (`source.tax_policy`, Yahoo filed-ratio retention); recalculated vs
  fixed-WACC modes with labels (`wacc_basis_note`); workspace stale-shield
  recomputation; FY2025 reconciliations (AEP 13.4% correction); TS parity.
  Full suite 764 passed, `ruff check` clean, `tsc` clean.

## Scope: data packets (NOT part of a code release)

- Production `control/valuation/CURRENT.json` sha256
  `ecf1e1c4b56936bc6af7fd93fe1bccadc41b7c6885f5e07c661dec5a93c7b5c1`
  — byte-identical before, during and after this assessment. No
  production D1/R2 writes, no migrations.
- Staging-only `control/valuation/CANDIDATE-staging.json` lists CAT, ORCL,
  PAYX, PEP, T. Promoting any packet set is a SEPARATE release with its own
  pointer update and rollback file (e.g.
  `find/outputs/company-packets/payx-pointer-rollback.json`).
- A production code deploy does not promote candidate packets and vice versa.

## Verification on staging (commit `b9993a3`)

Evidence: `find/outputs/tax-integration/staging-verification.json`.

- Full Python suite 764 passed (758 + 6 edge, 10 subtests), `ruff check`
  clean, `node --check` on shipped scripts via CI, `tsc --noEmit` clean,
  TS engine runtime parity vs Python (signed history, latest-OOB refusal
  naming the explicit fix, explicit-case WACC 0.088648 on both).
- SEC-first loads: CAT, PEP, T, PAYX all `latest_reported`, intrinsics
  exactly 213.05 / 170.11 / 76.14 / 88.01 — numerically identical to the
  pre-change staging build (recalculated-WACC default ≡ loaded rate).
- PAYX bundled brief: reported 23.79/23.83/23.83%, forecast
  `latest_reported`, "Recalculated WACC 8.65% … (recalculated mode)".
- ORCL still honestly blocked (nonzero preferred, no invented cost); BAC
  fails fast (SIC 6021 financial firm); AAPL Yahoo-only with tax policy.
- Real-Chromium browser test: PAYX workspace renders ($88.01, WACC 8.6%,
  brief + live result), zero console errors, zero non-200 network.
- Live account/security cycle on staging: 24/24 (signup/login/isolation,
  password change + prior-session revoke, foreign-origin 403, signed-out
  401s, MCP discovery).

## Production compatibility

- D1: no migration changes since production (`migrations/0001–0008`
  untouched); nothing to apply.
- Bindings/secrets: identical (`ZION_VALUATIONS`, `ZION_DATASET_CATALOG`,
  `PPE_DATA` R2, production D1). `PPE_POINTER_OVERRIDE` exists only in the
  staging env. No new secrets, env vars, or scheduled tasks.
- Cache/auth: unchanged code paths; staging-only Workers caching/trace
  sampling as before; user pages stay `private, no-store`.
- User/account + D1 compatibility: account flow verified against staging D1
  (24/24); production same-flow check remains a gap (no test identities
  created in prod without separate authorization) — unchanged from the
  prior release.

## Readiness matrix and GO/NO-GO

| Gate | Status | Evidence |
| ---- | ------ | -------- |
| Full Python suite + Ruff + embed + Node checks | PENDING | rerun on the fix-PR merge SHA; prior base 764 passed, CI 3.12/3.13 green through #51 |
| TS/browser-engine parity (tax bounds) | PASS* | tsc clean + runtime checks vs Python; *TS engine is experimental/unused — not browser-parity proof |
| Staging serves candidate commit, clean tree | PENDING | `/health` must report the fix-PR merge SHA, `tracked_dirty:false` |
| Yahoo-only loads (AAPL) | PASS | statement Yahoo, policy recorded |
| CAT/PEP/T/PAYX SEC-first loads + parity | PASS | intrinsics exact vs pre-change build |
| ORCL intentional block | PASS | preferred-cost refusal, no fallback invention |
| Negative-history docs + explicit scenarios | PASS | unit + integration tests; gate honors policy |
| Bank/REIT exclusions | PASS | BAC SIC-6021 fail-fast live |
| Save/share/revoke isolation (staging) | PASS | 24/24 live checks |
| Brief/preview/scenario tax+WACC labels | PASS | PAYX brief fields live |
| Workbook parity + security unit tests | PASS | in-suite, green |
| Real-browser staging test | PASS | Chromium PAYX load, 0 console errors |
| Production pointer untouched | PASS | `ecf1e1c4…` before/during/after |
| ABBV/AEP unlocked | BLOCKED by design | preferred-equity evidence still missing; no zero-derivation |

**Recommendation: A — promote corrected code only.** Rationale: every
mandatory gate passes, default valuations are numerically identical, no
migrations/bindings/secrets, and data packets ride a separate pointer
with independent rollback. Packet promotion (B) waits for its own
evidence cycle. No further fixes gate the code release (C rejected).

## Release (requires approval — do not run yet)

```sh
git checkout main && git pull --ff-only   # expect the fix-PR merge SHA recorded above
python3 scripts/embed_assets.py && wrangler deploy --env staging
```

then verify `/health` reports that exact merge SHA (`tracked_dirty:false`),
smoke-test one SEC-first load (PAYX 88.01) + one save/share/revoke cycle,
and confirm `control/valuation/CURRENT.json` is byte-identical before
and after.

Rollback (code): `wrangler rollback` or redeploy prior version
`137718bd-49f6-4f88-ab68-f67fdf5dd34a` (production `d1008a0`).
Rollback (data): not applicable — production pointers are not written by
this release; candidate pointer has its own per-publication rollback files.

## Known non-blockers

- `frontend/src/lib/dcf-engine.ts` was introduced in PR #47 (not
  pre-existing) and is EXPERIMENTAL and unused by the shipped workspace,
  the Worker bundle (`scripts/embed_assets.py` `module_names`), and every
  test harness — the file header says so explicitly. The production
  calculation path is `dcf_code.py` served from the Worker. Tests of the
  TS engine MUST NOT be cited as proof of production browser parity; the
  margin-averaging drift (year-1 ratios vs historical means) needs a
  dedicated parity pass or removal — not this release.
- Ruff format is not CI-enforced (87 files repo-wide pre-existing);
  `ruff check` is clean.
- Warm p95/cost notes from the prior release are unchanged.
