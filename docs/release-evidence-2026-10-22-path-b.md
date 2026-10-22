# Path B evidence — production limiter, release inventory, data roadmap

Date: 2026-10-22. Owner: Path B (DCF release safety). Scope: reconcile what is actually
shipped, make the production build enforce the edge limiter, and return costed proposals for
the remaining data gaps. No production publish, no source-release change, no rebuild.

## 1. Release inventory (re-verified from GitHub and the live workers)

| Component | Committed tree | Deployed version | Live identity | Status |
| --- | --- | --- | --- | --- |
| Shared query API (`zion-security-funnel-staging`) | `a035120` (PR #67 squash, checks green: 3.12, 3.13, browser, review) | `4a09d1be`, deployed 2026-10-22T18:23:43Z | not exposed | Deployed 4 min **before** the merge event from the branch tip `f8d6916`, whose tree is byte-identical to `a035120` (`git diff f8d6916 a035120` is empty). Content matches main; the deploy preceded the merge record. |
| Website, staging (`dcf-valuation-engine-staging`) | `13eabdc` (PR #70 branch, `main` + one commit) | `a2dc2f91`, deployed 2026-10-22T19:5xZ | `/health` → `commit 13eabdc`, `tracked_dirty: false` | Clean artifact from the committed tree. Replaced a dirty artifact (see finding 6). |
| Website, production (`dcf-valuation-engine`) | `3bf580bb` | `2c5ba38d`, deployed 2026-10-22T00:33:45Z | `/health` → `commit 3bf580bb`, `tracked_dirty: false` | Clean but **stale**: predates PR #67 and #68, so it carries neither the limiter nor the website-side packaging of the merged work. |
| Edge limiter rules | `edge_limits.py` in `7603585` | n/a (module) | n/a | Preserved unchanged; see §2. |

PR #67 (`a035120`) and #68 (`7603585`) are merged with green checks; PR #70 is open on the
branch `codex/production-limiter-entrypoint-20261022`.

Correction to the earlier handoff: the "20 successes then 429 on staging" claim was not
reproducible from outside the runtime. §2.3 records what the binding actually does, which is
approximate rather than strict.

## 2. The production limiter blocker, closed

### 2.1 Root cause
`wrangler.production.jsonc` ran `scripts/embed_assets.py` (which copies `worker.py`, the
entrypoint that awaits `edge_limits.enforce`) and then **overwrote** `worker_runtime/worker.py`
with `production_worker.py`, a near-duplicate that never called the limiter. Production
therefore bundled `edge_limits.py` and never reached it. The second copy existed only to
preserve the owner-authenticated routes, which `worker.py` already preserves.

### 2.2 Fix (PR #70, commit `13eabdc`)
- `production_worker.py` deleted.
- Production build command is `python3 scripts/embed_assets.py`, the same build staging uses.
- `tests/test_production_entrypoint.py` pins: the production `main`/build identity, the
  bundled `worker.py`/`edge_limits.py`/`owner_data_proxy.py`, the awaited `enforce()` call
  preceding any WSGI or owner-proxy dispatch at AST level, the four rate-limit bindings, and a
  **real build of the production artifact** in a scratch tree that is then inspected.
- `tests/test_owner_data_proxy.py` now loads the same entrypoint with the limiter stubbed, so
  the owner routes stay covered.
- Full suite: 1169 passed, 10 subtests passed, one pre-existing
  `tests/test_ppe_packets.py::test_disclosure` return-value warning (not introduced here).

### 2.3 What the binding actually does (measured, not assumed)
Instrumented staging temporarily, then reverted (`edge_limits.py` is unchanged in the commit):

- `request.method` arrives as `HTTPMethod` (`<HTTPMethod.GET>`); the enum-safe normalisation
  resolves `GET` and selects `REFERENCE_LIMIT` for `/api/data/query`. Confirmed in-tail.
- The binding is present and wrapped (`_BindingWrapper`); `limit({"key": ...})` is a plain
  dict and converts correctly through the SDK — no `to_js` needed.
- Thirty `limit()` calls inside **one request** returned `True` ×21 then `False` ×9. The
  counter works and the 20/min configuration is live.
- Independent requests do **not** accumulate dependably: 45 sequential requests over ~7s from
  one client were all served (45 × 403 from the owner-only route) with no 429; 30 requests
  over 20s behaved the same. Cloudflare documents this: counts are local to a Cloudflare
  location and synchronise in the background, so a burst can exceed the limit.

Consequence: the limiter is now *active* in production code for the first time, and it stops
sustained per-isolate abuse, but it is not a strict per-client quota. Strict limits require
Durable Objects (Cloudflare's own guidance). That is a design decision for Scott, not a code
defect to paper over — do not "fix" it by lowering thresholds.

### 2.4 Production candidate
`wrangler deploy --config wrangler.production.jsonc --dry-run` from the clean tree succeeds
with all five service bindings and all four rate-limit bindings; the emitted artifact
`worker.py` contains `limited = await enforce(self.env, request)` before dispatch and
`edge_limits.py` is in the bundle. Production publish still needs Scott's explicit approval;
rollback target is the current production version `2c5ba38d`.

## 3. Findings that change the release rules

1. **Staging was running uncommitted code.** Before today's redeploy, staging `/health`
   reported `commit f8d6916`, `tracked_dirty: true` — the artifact contained the bundle work
   that is still untracked locally (`model_bundle.py`, `snapshot.mjs`, `app.py` edits). Staging
   now runs `13eabdc`, clean. Agent A must redeploy from a committed integration tree before
   any bundle acceptance; a dirty-worktree deploy is not reviewable evidence.
2. **A second entrypoint is a drift trap.** Any future "production-only entrypoint" must fail
   the build test in `tests/test_production_entrypoint.py` before it can be deployed.
3. **The deploy event and the merge event are different facts.** Funnel deployment
   `4a09d1be` predates the merge record by four minutes while carrying an identical tree.
   Release notes should cite tree equality, not timestamps.

## 4. Proposals for the remaining data gaps (no rebuild performed)

Each item is a separate decision for Scott; none is authorized by this report.

### 4.1 Revenue missing for WMT, GE, ALL, C, GS, JPM
Observed (carried from the earlier bounded inspection): WMT's stored packet holds 132
observations across seven metrics spanning 2008-01-31..2026-01-31 with **zero** revenue
observations, and its coverage gaps report `AMBIGUOUS_CONCEPT_OR_DERIVATION` and
`NO_VALID_OBSERVATIONS_IN_REQUEST`. `dcf_loader.TAGS` already lists `Revenues` and
`RevenuesNetOfInterestExpense`, so the failure is in the SEC history engine's concept/context
resolution or in the release that froze the history — not in the query layer, and not a range
problem.

Next step, bounded: pull the companyfacts concept index for the six issuers only and record
which of `Revenues`, `RevenuesNetOfInterestExpense`, `SalesRevenueNet`,
`PremiumsEarnedNet` exist per fiscal year and with which durations. That separates three
cases (tag absent, tag present only in 10-Q durations, tag present but dropped as ambiguous)
and gives the exact engine change. Size the release from the issuer set the change touches,
not from the cohort: an affected-issuer incremental release is acceptable **only** if every
unaffected issuer's packet hash is byte-identical to the current release. Do not invent
revenue at the query layer and do not re-run the full cohort to find out.

### 4.2 Prior-session prices
`control/daily-prices/CURRENT.json` is a pointer with a `previous_version` chain and no
session index, so "yesterday's close" cannot be answered without walking the chain, which is
why the API answers only the latest stored session. Proposal: have the collector write a
small `control/daily-prices/sessions.json` (date → object key, bytes, sha256, provider,
session lineage) at publication time, capped and appended, and have serving read the index
once and fetch exactly one session object. That is collector-side (a data-contract change),
one object per session, no serving rewrite of stored prices.

### 4.3 Universe coverage
The stored universe holds 2,629 symbols and omits, among others, XOM, GOOGL, V, AMZN, TSLA,
META, ORCL, COST, IBM, ADBE, MO. A ticker list is not an identity map: the expansion needs
CIK resolution, security/share-class handling, ADR and regional eligibility, alias and
delisting rules, and duplicate-issuer collapse. Proposal: build the candidate list with those
columns and provenance first, rank by usefulness (mega-cap omissions first), then publish a
new cohort release. Do not append symbols to the live cohort ad hoc.

## 5. Remaining approvals and handoffs

- Scott: authorize production website publication from `13eabdc` (or after PR #70 merges).
- Scott: decide whether approximate edge limits are sufficient or a Durable Object limiter is
  wanted for strict per-client quotas.
- Scott: authorize, or decline, the three data increments above; each has its own release,
  validation and rollback path.
- Agent A: commit `model_bundle.py` with its import and module-list entry, and `snapshot.mjs`
  with its imports and route wrappers, then hand over a committed tree. Do not deploy staging
  from a dirty checkout.
