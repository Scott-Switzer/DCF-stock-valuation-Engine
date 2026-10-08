# Release checklist — October 6, 2026

- [x] CUIG formula reconciliation, adverse-input/provider tests and regression suite pass locally.
- [x] Lint, JavaScript syntax and diff checks pass.
- [x] Public Cloudflare Worker deployed; D1 migration applied and secret configured.
- [x] Public readiness, sample calculation, saved reference, duplicate suppression and exports verified.
- [x] Public autocomplete, mobile width and browser console verified.
- [x] Collection disclosure and private database access verified; synthetic records are flagged.
- [x] SEC annual AAPL statement loading verified in Workers; missing values still require review.
- [x] GitHub Actions `Validate valuation engine` passed on `main` for `b79bddf` (checked with `gh run list`). Re-run on the PR or branch that carries this batch.
- [ ] Connect the intended custom company API (Zion-compatible) and run `scripts/check_company_api.py TICKER DATE` for real-company coverage before advertising connected data.
- [ ] Apply D1 migrations through `0005_accounts.sql` on the remote database (`wrangler d1 migrations apply dcf-valuations --remote`) before deploying accounts. Checked: `0005_accounts.sql` is still pending remotely (`wrangler d1 migrations list dcf-valuations --remote`).
- [ ] Confirm rate-limit namespace `1946100604` (`MCP_LIMIT`) is not used by another binding in this account before deploying. Cloudflare namespace IDs are self-chosen integers with no creation step, and bindings sharing an ID share counters. `/mcp` depends on this binding.
- [ ] Set `MCP_ALLOWED_ORIGINS` only if a browser-based MCP client needs an origin other than this host.
- [ ] Reconcile completed real-company valuations to source filings, price/share assumptions and an independent spreadsheet.
- [ ] Future suite: implement comparables, DDM and football field with their own model-suitability tests.

The old suspended Render service is not the advertised deployment and was not changed. User-submitted valuation assumptions are self-selected research data; they are not independently validated market sentiment.
