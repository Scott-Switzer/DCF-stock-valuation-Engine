# Foundation audit and reconciliation — 2026-10-24

Supersedes the first version of this file. The first version was produced against
**stale duplicate checkouts** and several of its claims were wrong. Corrections are
marked below; nothing is asserted without a command, a commit, or a CI run behind it.

## 1. Checkout reconciliation (main finding)

Two unrelated copies of the same repos exist on this machine. The earlier audit
tested the stale ones.

| Repo | Canonical path | Stale duplicate | Evidence |
|---|---|---|---|
| financial-assistant-gateway | `/Users/scottthomasswitzer/Documents/financial-assistant-gateway` — `origin/main` = `d7c7b3f` (2026-10-23, PR #24) | `/Users/scottthomasswitzer/Documents/Secret/financial-assistant-gateway` — `main` = `d5563a9` (2026-09-30, PR #13) | `git rev-parse origin/main`, `git log -1` |
| financial-system-core | `/Users/scottthomasswitzer/Documents/financial-system-core` — `origin/main` = `12d83ad` (PR #26) | `/Users/scottthomasswitzer/Documents/Secret/financial-system-core-workspace` — `87001c1`, reachable from core main but behind | `git rev-parse origin/main` in both |
| DCF engine | `/Users/scottthomasswitzer/Documents/Secret/dcf-staging-acceptance` — only checkout; HEAD = `origin/main` = `42b0625` | none | `git branch -r --contains HEAD` → `origin/main` only |

`Documents/Secret/financial-system-core` is a symlink to the stale
`financial-system-core-workspace`; the real repo is `Documents/financial-system-core`.

### Claims from the earlier audit that are now disproved

| Earlier claim | Actual |
|---|---|
| `bundle-acceptance.yml` missing | Present on canonical `main`: `.github/workflows/bundle-acceptance.yml`. Also `bundle-production.yml`, `bundle-staging.yml`. |
| `mcp/scripts/verify-read-data.mjs`, `verify-catalog-session.mjs` missing | Both present in the canonical checkout. |
| `financialData.ts` / `financialRequest.ts` / `query_financial_data` missing | Present. Live tool scope asserted by the acceptance script is exactly `load_dcf_model,query_financial_data`. |
| MCP suite has 23 tests | Canonical suite is **30 tests / 6 files**; 23 was the stale checkout. |
| Uncommitted gateway-referenced docs drift | No drift: canonical tree is clean on `main`. |
| Core handoff and annual-cutoff receipt uncommitted | Committed and pushed on `origin/codex/continuation-handoff-20261022` (`0b6fe92`), 6 commits ahead of main. Not merged, but not uncommitted. |
| Handoff contradicts itself about the gateway mismatch | False. `HANDOFF-2026-10-23.md` already records the resolved drift (`39925989076`) and the resolved final config; reconciled at `34cb5a1`. |
| Uncommitted `uv.lock` change in DCF | False. `uv.lock` is tracked and unmodified in DCF. The untracked `uv.lock` is in the stale gateway clone. |
| `GATEWAY_ACCEPTED_SHA` missing, stale `c4a3195` fallback active | False. It is an **environment** variable: `gh variable list --env staging` → `GATEWAY_ACCEPTED_SHA=d7c7b3f…`, set 2026-10-24T00:15:48Z. Repo-level listing was the wrong scope. |
| PanelDefinitionV1/ReturnDefinitionV1 changes are uncommitted core changes | They exist only in the stale duplicate `Secret/financial-system-core-workspace`, on top of `87001c1`. Canonical core does not contain them. |

### PR and deployment status (verified now)

- PR #78 `97cc158` — **MERGED** 2026-10-23T23:48:09Z, merge commit `e2271d4`; checks `test (3.12)`, `test (3.13)`, `browser`, `Greptile Review` all SUCCESS.
- PR #79 `42b0625` — **MERGED** 2026-10-24T00:12:56Z.
- DCF `origin/main` = `42b0625`; `97cc158` is an ancestor (`git merge-base --is-ancestor`).
- Gateway bundle acceptance run **40017723376** (head `40bb5ad`) — success.
- Gateway bundle acceptance run **40044543532** (head `d7c7b3f`) — success.
- New run **40048223159** (head `d7c7b3f`) dispatched from the canonical checkout during this session.

The reader version IDs quoted in earlier handoffs (`0e81c004…`, `4e93471b…`) are
deployment receipts, not code identities; they are not re-verified here.

## 2. Verified current behavior (commands run in this session, canonical checkouts)

| Surface | Command | Result |
|---|---|---|
| Shared reader | `node --test deploy/security-funnel/test/*.test.mjs` (DCF) | 27 tests, 0 fail — includes `cutoff-conflict.test.mjs` covering conflicting cutoffs **across annual windows** and **across pages within one window** |
| DCF suite (benchmark scope) | `uv run --group dev python -m pytest tests/test_zion_benchmark_chain.py tests/test_valuation_benchmarks.py -q` | 25 passed (after local fix below) |
| Gateway Python | `python3.12 -m pytest tests/ -q` (canonical, 2026-10-24) | 64 passed |
| Gateway MCP | `npm test` (canonical `mcp/`, `node_modules` present) | 30 passed / 6 files |
| Core contracts | `python3.12 -m pytest smoke/ -q` (canonical `/Users/.../Documents/financial-system-core`) | 16 passed |

Correct runtimes: `python3` (3.9.6) is too old for the DCF project (`>=3.12`);
use `uv run --group dev python` from the DCF repo. Gateway Python runs with
`python3.12` from its own repo root (`pythonpath = ["src"]`). MCP needs
`node_modules` present (`npm install`).

## 3. Defect fixed locally (DCF only, uncommitted)

`tests/test_zion_benchmark_chain.py` — two tests asserted the pre-hardening
permissive behavior and failed with
`Benchmark vintage unavailable at historical cutoff: NO_REVIEWED_PUBLICATION_EVIDENCE`.

Root cause: real manifests under `data/ddfi/registry/assumption_releases/*/manifest.json`
carry `publication_evidence: null`, and no `publication_evidence.json` catalog
exists beside them. `valuation_benchmarks.py` therefore correctly refuses
`as_of`-gated selection. The gate is intended (`9936590`, `52ddda8`, `ff3e57e`).

Change:
1. Success cases now use `mode="current"` (explicit, non-backdated, no evidence
   required) — the contract that actually exists.
2. Added an explicit assertion that historical release-root selection without
   evidence still returns 400 / `NO_REVIEWED_PUBLICATION_EVIDENCE`.
3. Added `test_release_historical_selection_needs_reviewed_evidence_via_api`
   driving `/api/calculate` with a **synthetic** byte-bound release pair:
   - reviewed evidence (`FIRST_OBSERVED`, synthetic `example.invalid` URL,
     synthetic dates) → 200, `selection_mode=HISTORICAL_PUBLISHED`,
     `publication_method=FIRST_OBSERVED`, WACC adopted;
   - cutoff before the synthetic publication date → 400 "published after cutoff";
   - identical release without evidence → 400 `NO_REVIEWED_PUBLICATION_EVIDENCE`.

No real publication date is fabricated, and no availability gate is weakened.

`uv.lock`, `HANDOFF-2026-10-23.md`, manifests and receipts were left untouched.

## 4. Deferred defect (not repaired, needs owner decision)

**Breaking change inside a V1 evaluator contract**, only in the stale duplicate
`/Users/scottthomasswitzer/Documents/Secret/financial-system-core-workspace`
(4 files, +222/−10, on top of `87001c1`, which is on core `main`):

- `return_definition` changes from `string` to a `ReturnDefinitionV1` object.
- Four fields become **required**: `panel_definition`, `daily_return_definition`,
  `daily_returns`, plus the reshaped `return_definition`.
- `returns` loses `minItems: 1`.
- The contract keeps the name `StatisticalReferencePanelV1` and the same
  `$id`/version surface.

Any existing producer or the `financial-world-qc` consumer emitting V1 panels
will fail validation. Correct resolution is one of: bump to `StatisticalReferencePanelV2`,
make the new fields optional with defaults, or coordinate a dual-write migration.
Not repaired here because it is not in the canonical repo and it changes an
evaluator contract consumed outside this checkout.

## 5a. Newly verified live behavior (2026-10-24T01:06Z, run 40048223159)

Dispatched from the canonical checkout at head `d7c7b3f`; **success**. Artifact
metadata only, no licensed rows printed:

- Bundle agreement across MCP reader, gateway `/readyz`, and source capabilities:
  `bundle_id=2c0419d1…994a`; `source_release_keys` include catalog, CRSP history,
  SEC engine/history/readiness, daily prices/session index and serving pointers.
- `gateway_sha=d7c7b3f…` matched the expected environment variable.
- Tool scope unchanged: exactly `load_dcf_model,query_financial_data`; the legacy
  `ask_financial_system` credential was denied (`legacy_research_denied=true`).
- Wrong bundle rejected: `RELEASE_MISMATCH`, HTTP 409.
- Catalog: `metadata_only=true`, `registered_releases=948`, `unique_datasets=946`,
  release `c1164473…6f53`; pagination verified and bundle mismatch rejected.
- Exact session `2026-10-21` verified (`session_release=d12b8230…cb4`,
  `session_index=0c10522b…236`); missing session rejected.
- Structured request path verified; model load retained an input snapshot and
  two outside-bundle inputs.

Quarterly and TTM assertions run inside the script and passed as part of the
successful job; their values are not emitted in the artifact.

## 5. Blocked checks (not verified, with reasons)

- **Local live acceptance**: `node mcp/scripts/verify-read-data.mjs` fails at the
  first HTTPS call with `ERR_SSL_WRONG_VERSION_NUMBER` (local TLS interception);
  `/readyz` via curl returned an empty body. Known environment limitation —
  cloud acceptance is the sanctioned path and was used instead (5a).
- **Direct reader/gateway live values**: requires the sanctioned workflow; the
  dispatch above is the recorded attempt. Anonymous MCP access still returns
  `AUTH_REQUIRED` (re-verified in the earlier session).
- **Financial coverage** (GE/JPM/C/GS annual revenue, banking accounting maps,
  `stocknames_v2` schema, 479 remaining acquisition jobs): not re-probed — needs
  private R2/engine access. Recorded earlier findings stand as *historical*, not
  current proof.

## 6. Missing data versus missing functionality

- Missing **functionality**: none identified in the paths that were exercised.
  Catalog pagination, `dataset_detail` projection, cutoff/provenance guards,
  bundle pinning, quarterly/TTM, and tool scope all have passing tests.
- Missing **data/evidence**: reviewed `publication_evidence` for the real
  Damodaran releases; certified industry mappings for banks/insurers; dataset-specific
  normalization/units; dated issuer/security links; revision history; point-in-time
  eligibility. These are data-model gaps, not code regressions.

## 7. Ranked backlog

| # | Item | Owner | Evidence | Acceptance condition | Depends on |
|---|---|---|---|---|---|
| 1 | Commit the DCF benchmark test fix (this session) | DCF | 25 passed locally; suite was red on `main` behavior change | Branch + PR, CI green on 3.12/3.13/browser | none |
| 2 | Decide merge for `codex/continuation-handoff-20261022` (6 commits, `0b6fe92`) | core | `git rev-list --left-right --count origin/main...HEAD` → `0 6` | PR merged or branch explicitly designated the release record | owner authorization |
| 3 | Resolve the V1 evaluator contract break (`PanelDefinitionV1`/`ReturnDefinitionV1`) | core + QC | 4-file diff in stale duplicate; new required fields | V2 bump or optional-with-defaults; QC consumer test green | #2 |
| 4 | Backfill reviewed publication evidence or formally restrict historical `source=release` to Zion | DCF/data | manifests have `publication_evidence: null`; historical path refuses | Either a validated `publication_evidence.json` with reviewed methods, or docs + code marking release-root historical as unsupported | rights review |
| 5 | Re-run cloud acceptance after any reader/gateway change | gateway | run 40048223159 dispatched at `d7c7b3f` | Green run; `GATEWAY_ACCEPTED_SHA` matches deployed SHA | #1 |
| 6 | Metadata-only catalog detail/schema exposure beyond `dataset_detail` | DCF reader | detail projection test exists; no bulk schema surface | Projected schema endpoint + MCP field, bundle-checked, no raw rows | #5 |
| 7 | Coverage/freshness/missingness presentation in Data workspace | DCF web | `renderAnswerEvidence` code-ready; production not redeployed | Deployed UI shows frequency, observed range, cutoff, gap counts | #5 |
| 8 | Issuer-by-issuer annual gap diagnosis (GE/JPM/C/GS) | data | `docs/annual-gap-diagnosis-2026-10-24.md` (historical) | Reproducible per-issuer report distinguishing mapping vs materialization | private R2 access |
| 9 | One bounded normalization increment | data | proposal only | Units, dated identity, availability, revisions, quality gates verified on one dataset | #8 |
| 10 | Remove stale duplicate checkouts or mark them clearly | ops | this audit | Single canonical path per repo; others archived/renamed | owner decision |

## 8. Changed files from this session

- `tests/test_zion_benchmark_chain.py` — modified (2 tests aligned to the current
  contract; 1 new synthetic-evidence API test; 1 helper).
- `docs/foundation-audit-2026-10-24.md` — rewritten (this file).

Nothing was committed, pushed, merged, deployed, or configured. No credentials,
private rows, or licensed data were printed.

## 9. Increment executed 2026-10-24 (authorized repair + record)

### Pull requests opened

| PR | Repo | Head | Checks at handoff |
|---|---|---|---|
| [#80](https://github.com/Scott-Switzer/DCF-stock-valuation-Engine/pull/80) | DCF | `3ddffb9` | `test (3.12)`, `test (3.13)`, `browser`, `Greptile Review` all SUCCESS; MERGEABLE |
| [#28](https://github.com/Scott-Switzer/financial-system-core/pull/28) | core | `2a9683b` | no CI checks configured for these paths; documentation-only |

State moved during this session: core `origin/main` advanced from `12d83ad` to
`071ef08` (PR #27), which merged the **first three** continuation commits. The other
three record commits (`675c835`, `34cb5a1`, `0b6fe92`) were still absent from main, so
PR #28 cherry-picks them unchanged onto `071ef08` and adds a reconciliation section.
Verified: `git merge-base --is-ancestor 0b6fe92 origin/main` → NO before the PR.

### StatisticalReferencePanelV1 compatibility finding

Recorded in `docs/statistical-reference-panel-v1-compatibility-2026-10-24.md`
(core, PR #28). Evidence:

- Canonical schema is 12,308 bytes, SHA-256 `cf165c5b…`, matching
  `docs/fwf/08-calibration.md`.
- Producer `project-portfolio-engine-workspace/ingestion/calibration/contracts/`
  vendors a **byte-identical** schema, and `reference.py:269` emits
  `return_definition` as compact JSON **text**, validated as a string
  (`contract.py:182-203`).
- `docs/fwf/08-calibration.md` already labels the structured/`panel_definition`/
  `daily_returns` edits as unmerged M10 preparatory work that must not be released.
- QC loader code was **not located** in `Documents/financial-world-qc`; its adapters
  are documented but not inspected here.

Outcome: the V1 reshape cannot be adopted under the V1 name. Recommendation is a V2
contract landed with producer and consumer, or optional-with-defaults fields. Owner
decision required; nothing was copied into canonical code.

### Data workspace coverage/freshness — exact status

- **Implemented and on main** (`e60e753`, `ed22931`): `renderAnswerEvidence` in
  `static/js/data-workspace.js` prints frequency, observed period range and count,
  source cutoff, coverage reason with stored range and metrics present, source gap
  reasons, and a native gap count. `templates/data_workspace.html` provides
  `financial-coverage`, `financial-warnings`, `financial-evidence`.
- **Deployed: no.** `GET /static/js/data-workspace.js` on
  `https://dcf-valuation-engine.scswitzer.workers.dev` returns 200 / 20,056 bytes,
  SHA-256 `230ab866…`, and contains **none** of the coverage strings. Local main asset
  (SHA-256 `4b27e14c…`) contains all three.
- `embedded_assets.py` (git-ignored build artifact) already contains the strings with
  `BUILD={'commit': '42b0625…', 'tracked_dirty': True}`, so the bundle is staged but
  never deployed.

Release plan (not executed):
1. Clean worktree at `origin/main`; run `uv run --group dev python scripts/embed_assets.py`
   so `BUILD.tracked_dirty` is false and `BUILD.commit` equals the release SHA.
2. `uv run --group dev python -m pytest tests/ -q` and `python3.12 -m node --check`
   equivalent for the touched JS (`node --check static/js/data-workspace.js`).
3. `npx wrangler deploy --config wrangler.production.jsonc` with existing credentials;
   no D1 migration, no data-pointer change.
4. Re-fetch `/static/js/data-workspace.js`, confirm the new hash matches
   `BUILD.asset_sha256`, and confirm the HTML carries the three elements.
5. Run the existing `live-smoke.yml` workflow; record the run. Rollback is a redeploy of
   the previous embedded bundle — D1 schema and data are untouched.

Missing before calling this done: a focused browser/DOM assertion that the coverage
line renders for a real answer; current tests cover the module, not the rendered panel.

### Revised ranked backlog

| # | Item | Owner | Evidence | Acceptance | Depends |
|---|---|---|---|---|---|
| 1 | Merge DCF #80 | DCF | 4/4 checks SUCCESS, MERGEABLE | Merged; `main` suite green | review |
| 2 | Merge core #28 | core | docs-only, 15 smoke tests pass locally | Record on main; no CI configured for docs | review |
| 3 | Decide `StatisticalReferencePanelV1` (V2 vs optional vs leave as M10 prep) | core + PPE + QC | compatibility doc; byte-identical vendored schema | V1 SHA unchanged and producer/consumer tests green, or V2 landed together | owner |
| 4 | Deploy the workspace coverage panel | DCF web | asset hash mismatch proven | Step 4-5 of the release plan recorded | #1 |
| 5 | Add a rendered-panel DOM test for coverage | DCF web | only module-level tests exist | Test fails when the coverage element is removed | #4 |
| 6 | Publication-evidence strategy for historical release-root benchmarks | data | manifests carry `publication_evidence: null` | Reviewed catalog or documented Zion-only historical | rights review |
| 7 | Catalog schema surface beyond `dataset_detail` | DCF reader | projection tests exist; no bulk schema endpoint | Bundle-checked schema view, no raw rows | #1 |
| 8 | Issuer gap diagnosis (GE/JPM/C/GS) | data | historical diagnosis doc | Reproducible per-issuer report | private R2 |
| 9 | One bounded normalization increment | data | proposal only | Units, identity, availability, revisions verified on one dataset | #8 |
| 10 | Retire or clearly mark stale duplicate checkouts | ops | this audit | One canonical path per repo | owner |
