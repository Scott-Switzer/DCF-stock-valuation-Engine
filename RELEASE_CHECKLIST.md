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
- [ ] Apply pending migrations before deployment. Remote inspection on October 10 found only `0007_residual_method.sql` pending; migrations through `0006_share_controls.sql` were already applied. Recheck with `wrangler d1 migrations list dcf-valuations --remote`. Migration 0007 preserves valuation rows while expanding the method constraint; migration tests check row and index preservation.
- [x] Existing deployed `MCP_LIMIT` binding uses namespace `1946100604`, 60 requests/minute; the release dry-run preserves it. Namespace IDs are self-chosen integers, and bindings sharing an ID share counters.
- [ ] Set `MCP_ALLOWED_ORIGINS` only if a browser-based MCP client needs an origin other than this host.
- [ ] Reconcile completed real-company valuations to source filings, price/share assumptions and an independent spreadsheet.
- [x] Suite methods (DDM, relative valuation, football field) are implemented in `suite_models.py` and `compare.py`. Source reconciliation and workbook recalculation tests cover them (`tests/test_suite_reconciliation.py`, `tests/test_workbook_recalc.py`). Browser checks for these pages are still not recorded.

The old suspended Render service is not the advertised deployment and was not changed. User-submitted valuation assumptions are self-selected research data; they are not independently validated market sentiment.
