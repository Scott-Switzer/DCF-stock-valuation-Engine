# Investment research expansion

Master specification: user-supplied October 10, 2026 platform expansion. Existing production recovery point: main `f2a8918adf13839a4c8e735a8c6e8153d15e40c7`, Worker `93e9f682-73ea-430c-9332-6d5f2882ea89`.

## Baseline audit

Python/Flask on Cloudflare Python Workers; D1 persistence and PPE R2; replaceable Yahoo/SEC/PPE/custom-provider adapters. DCF, DDM, relative and residual-income engines exist. Company workspace already provides historical growth, analyst references, reverse DCF, driver impacts, sensitivities, football field, basic bear/base/bull cases, saved templates, watchlists, sharing, accounts and formula-driven XLSX/CSV/JSON exports. Preserve these; no framework rewrite.

Final baseline CI and public smoke succeeded for `f2a8918`. Release evidence: `find/outputs/release-verification-2026-10-10.md`. Existing reconciliation narrative includes historical defects fixed by PRs #7/#8, so treat it as dated evidence, not current product status. Unrelated untracked scratch work is preserved.

## Sequential milestones and acceptance

- [x] Financial QA infrastructure: reproducible 25-company matrix; source/period/field receipts; distinct integrity/readiness/reconciliation results; independently computed FCFF, bridge and per-share values; numerical discrepancies fail explicitly. Current scope: CLI audit and deterministic tests, with a dated live report. No unsupported claim of full filing verification.
- [ ] Resolve observed financial data defects: inspect source records for flagged companies; preserve missing values and unsupported-method blocks. Extend independent cases and workbook parity where inputs support them.
- [x] Comparable-company methodology: inspect existing peer metrics; add explicit basis, transparent statistics/exclusions and peer contributions; regression tests for financial firms and unmatched bases.
- [ ] Research workspace: integrate existing overview/valuation/reverse/driver/scenario tools, add owned thesis/scenario persistence and snapshot-consistent exports; browser desktop/mobile acceptance.
- [ ] Reliability: separate deterministic and live validation, scheduled non-saving real-company/export/freshness checks, measured latency evidence, release identity and rollback record.
- [ ] Account recovery: inspect available email infrastructure, implement secure single-use hashed tokens and session revocation only with a configured delivery path; otherwise record exact setup dependency and continue independent work.
- [ ] Documentation and release acceptance: exact-main CI, reviewed milestone PRs, deployment verification, provider/migration status and remaining limitations.

Each milestone uses a dedicated branch and PR. Merge/deploy only after applicable acceptance passes; preserve the last good release if a critical defect remains. No destructive migration, user-data cleanup shortcut, or shared PPE pointer changes.

## Current milestone

Branch: `codex/financial-validation-universe`. Implement a local/non-saving audit of exact company snapshots and API calculations. An independent reference calculator shares explicit assumptions but imports no production calculation engine. PASS for arithmetic does not assert economic credibility or filing accuracy. Source assertions must retain their evidence boundaries.

### Financial QA infrastructure results

Implemented `financial_qa.py`, `reconciliation/reference_dcf.py`, `scripts/validate_universe.py`, regression tests and a dated 25-company matrix. Existing engines and production behavior remain unchanged. Live sweep: 20 company snapshots loaded, 19 independent local/API DCF comparisons passed, 20 WACC component checks passed, MRX blocked industrial DCF as intended; five provider/contract loads remain blocked. Overall filing verification is PARTIAL, not complete. The matrix names all limitations and exact loading errors. Next independent task: professional comps methodology, while targeted bank/REIT/provider contract work retains explicit missing observations.

### Comparable-company analysis milestone

Branch: `codex/explainable-comps`. Adds source-dated peer basis, explicit constant-multiple versus matched-forward modes, peer distributions/contributions, median alternatives, visible IQR flags without deletion, API candidate exclusion, formula-workbook parity, and workspace/standalone inspection tables. Existing CUIG mean-based target arithmetic is preserved. Targeted regression tests cover mixed/unknown bases, required forward periods, financial-firm EV exclusions, P/B readiness, source-locked form round-trips, candidate API exclusion, raw equity contributions before flooring and independently recalculated workbook output. No database migration is required. Peer ranking still uses the existing source-backed starter/fit workflow; this milestone does not claim verified segment/geography information that is absent.

### Saved investment research milestone

Private structured thesis notes and named scenario snapshots for DCF, DDM and relative valuation. Every save recalculates on the server without fetching new provider data, creates an immutable revision and keeps financial provenance. Research library, frozen-note editing, same-input scenario comparison, complete JSON, printable summary and formula-driven model Excel reuse existing engines. Existing residual-income calculations remain available separately; research persistence for that method is not included yet. Additive migration `0008_research.sql` is required before deployment. Ownership, account claim, foreign-Origin rejection, escaped notes, migration preservation and exact snapshot exports have deterministic regression coverage. Browser and deployed acceptance are recorded separately in release evidence.
