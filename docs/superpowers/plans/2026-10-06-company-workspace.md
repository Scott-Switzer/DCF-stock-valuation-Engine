# Company Workspace Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this approved scope task by task.

**Goal:** One ticker workspace with persistent methods, live previews and explicit saves.
**Architecture:** Preserve each existing audited form in an isolated same-origin editor, coordinated by one workspace. Reuse the loaded company snapshot for method assembly; server preview uses existing pure evaluators without persistence. Optional research is independently loaded and cached.
**Tech Stack:** Flask/Python Workers, vanilla JavaScript, SVG, existing D1.
**Spec:** ../specs/2026-10-06-company-workspace.md

## Global Constraints
No workbook export. No fabricated peer fundamentals or inferred management growth. Preserve mathematical definitions, source inspection and override tracking. Four unique peer candidates, user can exclude or replace. Save only deliberately.

## Review Focus
Stale responses after ticker/method changes; non-dividend issuers; failed peer snapshots; forecast consensus fiscal-year alignment; invalid live inputs must not leave a savable stale result.

### Task 1: Server assembly and preview
Files: auto_loading.py, app.py, suite_views.py, tests/test_workspace.py.
- [x] Test preview has no saved ID and never calls storage; snapshot assembly never reloads company; peer candidates remain four and unique.
- [x] Refactor load_method to accept validated company snapshot; add preview and replacement-peer endpoints, separate rate budget for preview.
- [x] Run targeted tests and existing suite.

### Task 2: Workspace and compact editor
Files: templates/workspace.html, templates/base.html, static/js/workspace.js, static/js/editor.js, static/css/workspace.css.
- [x] Persistent same-origin editors, one ticker loader, method tabs and sticky result, explicit save/export.
- [x] Debounced preview with generation guards, invalid-input states and compact source details; growth reference actions aligned to fiscal periods.
- [x] Four selectable peer cards with source-based replacement; SVG financial/price/sensitivity views.
- [x] Browser verify switching preserves inputs, saving is separate, invalid values and responsive layout.

### Task 3: Optional guidance
Files: guidance.py, app.py, scripts/embed_assets.py, tests/test_guidance.py.
- [x] Bound official SEC source lookup, attach dated recent filings with explicit guidance availability; extract only identified issuer management prose with period/date/source.
- [x] Test stale/mismatched/ambiguous sources and optional failures.

### Task 4: Release
- [x] Full tests, Ruff, JS syntax, browser evidence and fresh code review.
- [x] Push and create PR, inspect Greptile exact-head findings and CI, fix valid findings.
- [ ] Deploy, verify public app, merge only passing reviewed head, record evidence.
