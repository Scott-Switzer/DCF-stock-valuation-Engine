# Release checklist — October 10, 2026

- [x] CUIG formula reconciliation, adverse-input/provider tests and regression suite pass locally.
- [x] Lint, JavaScript syntax and diff checks pass.
- [x] Public Cloudflare Worker deployed; D1 migration applied and secret configured.
- [x] Public readiness, sample calculation, saved reference, duplicate suppression and exports verified.
- [x] Public autocomplete, mobile width and browser console verified.
- [x] Collection disclosure and private database access verified; synthetic records are flagged.
- [x] SEC annual AAPL statement loading verified in Workers; missing values still require review.
- [ ] Verify GitHub Actions and Greptile for the exact release PR head before merging; older green runs do not validate this release.
- [ ] Connect the intended custom company API (Zion-compatible) and run `scripts/check_company_api.py TICKER DATE` for real-company coverage before advertising connected data.
- [ ] Recheck pending migrations with `wrangler d1 migrations list dcf-valuations --remote` before every release, and apply only reviewed migrations before deploying dependent code. Preserve existing records. Research persistence requires additive migration `0008_research.sql`; prior method migrations must already be applied.
- [x] Existing deployed `MCP_LIMIT` binding uses namespace `1946100604`, 60 requests/minute; the release dry-run preserves it. Namespace IDs are self-chosen integers, and bindings sharing an ID share counters.
- [ ] Set `MCP_ALLOWED_ORIGINS` only if a browser-based MCP client needs an origin other than this host.
- [ ] Reconcile completed real-company valuations to source filings, price/share assumptions and an independent spreadsheet.
- [x] Suite methods (DDM, relative valuation, football field) are implemented in `suite_models.py` and `compare.py`. Source reconciliation and workbook recalculation tests cover them (`tests/test_suite_reconciliation.py`, `tests/test_workbook_recalc.py`). Browser checks for these pages are still not recorded.

The old suspended Render service is not the advertised deployment and was not changed. User-submitted valuation assumptions are self-selected research data; they are not independently validated market sentiment.

## Every research-platform release

- [ ] Exact PR head: deterministic CI and Greptile findings resolved before merge.
- [ ] Record main SHA, prior recovery Worker version, deployment version and migration state.
- [ ] Deploy with preserved variables and verify `/health` embeds the expected clean Git SHA when build identity is available.
- [ ] Run non-saving AAPL smoke with independent DCF arithmetic, source freshness and formula workbook delivery.
- [ ] Browser-check real ticker loading, editable assumptions, suitable comps and mobile width; test private research save/revision/export/ownership when included.
- [ ] Distinguish arithmetic parity from independent filing verification. Keep known company/provider gaps visible.
- [ ] Preserve D1/R2 data and shared financial publication pointers.
