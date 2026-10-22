# SEC evidence and screen-to-valuation implementation plan

> Execution: superpowers:executing-plans, inline in the existing isolated worktree.

**Goal:** Account for 50 selected public issuers through the existing readiness and valuation services, and extract inspectable dated share evidence from original SEC XBRL.

**Architecture:** Consume the published private readiness index with server-side credentials. Screening yields a pinned identity/cutoff and a request for the existing native-history API; the existing enterprise and claims routes remain the only valuation engines. Raw filing evidence is a separately labelled candidate and never silently replaces attested inputs.

**Spec:** User-approved screen-to-valuation recommendation in this chat, October 19, 2026.

**Tech stack:** Existing Flask/Cloudflare Python app, standard-library XML parser, pytest, existing Zion read-only API.

## Global constraints
- No paid providers, new cloud resources, credential changes or production publication.
- No missing-to-zero substitution, no weighted-average-to-outstanding substitution.
- Preserve source URL/hash, issuer, accession, period, availability and class dimensions.
- Do not alter the dirty Zion checkout or claim candidates are native attestations.

## Review focus
- Future filings and stale dates are excluded, with reasons.
- Conflicting values and multiple share classes never collapse into one count.
- Unsupported/malformed documents fail closed.
- Screen pins and issuer identities survive the handoff to existing financials.
- Every selected issuer receives a valuation result or an explicit blocker, including transport failure.

## Tasks
1. Add tests for dated raw XBRL/inline-XBRL share extraction, class contexts, conflicts, units, identity and historical availability; observe failure, implement parser, run tests, commit.
2. Add tests and implement a bounded readiness consumer and integrated screen view/API that supplies existing financials requests and preserves pins. Reuse current transport/configuration; observe failures and verify route behavior; commit.
3. Add a reproducible 50-company acceptance runner against the existing deployed services. It requires explicit valuation assumptions to run a valuation and otherwise records the exact missing-input blocker. Exercise public SEC extraction on actual source documents where reachable, save metadata-only receipts, run regression tests and commit evidence.

## Execution ledger
- Existing DCF worktree is clean; Zion checkout contains concurrent readiness work and is read-only for this task.
- User explicitly approved execution and no routine reapprovals; proceed inline.
