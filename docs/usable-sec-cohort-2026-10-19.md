# Usable SEC research milestone — October 19, 2026

The existing DCF application now consumes Zion's private readiness index at `/screen`, selects a pinned issuer, loads that exact approved financial-history release, and runs the existing enterprise valuation engine with explicit industry benchmarks and analyst forecasts. This is an integrated application change, not a separate research application.

## Implemented

- Account-authenticated `/api/research-screen` and `/api/research-screen/prepare`. Credentials stay server-side; anonymous API requests receive 401. Existing no-store and origin checks cover the research routes.
- Company screen with method/sector/CIK filters and pagination preserving the source index pin. Selected CIK, evidence cutoff, engine release and source gaps survive the handoff. Dated ticker identities must be reviewed before preparing a valuation.
- A scenario form for industry, five annual growth rates, terminal growth, terminal ROIC and operating-company suitability. Forecasts remain blank until entered. Benchmarks use named existing immutable releases and historical selection. The full request is inspectable for reproduction.
- Fixed the native-history adapter: `expected_release_id` previously checked only the currently served engine. It now also supplies `release_id`, allowing the service to select an explicitly approved historical release before verifying its identity. Live AAPL loading reproduced the screen's `ac8f14de...` engine without changing any source pointer.
- Original SEC XBRL/inline-XBRL share extractor and bounded public acquisition CLI. It preserves issuer, accession, filing date, observation date, source SHA-256, units and class dimensions. Future/stale facts, wrong issuers, malformed documents, unsupported units and conflicting counts are refused. Candidates never override native attestations or become automatically permitted for valuation.

## Measured results

`docs/receipts/usable-sec-cohort-2026-10-19.json` accounts for exactly 50 distinct issuers: the first 47 operating-DCF screen matches, excluding the three review cases, plus AAPL/MSFT/GOOGL.

| Result | Count |
| --- | ---: |
| Issuers accounted for | 50 |
| Native histories loaded through the existing provider | 39 |
| Enterprise scenarios reconciled independently | 3 |
| Blocked outcomes | 47 |

The three enterprise scenarios use the previously reviewed October 15 forecasts and dated Damodaran references, with financial evidence cut off at September 24. Independent 40-digit Decimal calculations agree within $0.01. These are illustrative scenarios, not current market valuations or recommendations. Equity and per-share outputs stay null.

- 34 blocked issuers lack a dated reviewed ticker identity.
- 2 lack a current SEC ticker alias in the separately observed directory.
- 9 have available SEC observations, but the existing native adapter refuses them because three consecutive annual revenue periods are unavailable. Direct pinned API probes returned HTTP 200 for all nine; this is an adapter/history qualification blocker, not missing storage or a network outage.
- Forecast assumptions were not selected for any of the 47 blocked issuers. Blocker counts overlap.

The 50-company receipt exercises **local authenticated DCF routes and live Zion sources**. It is not evidence that 50 valuations completed, nor a deployed authenticated 50-company browser test.

## Actual additional SEC evidence

The public acquisition run found 17 dated share observations across three original filings (AAPL 3, MSFT 3, GOOGL 11), including eight class-scoped Alphabet observations. The summary receipt records source URLs, accessions, filing dates and hashes. All remain `CANDIDATE_REQUIRES_REVIEW` with `permitted_for_valuation=false` and no class aggregation. The final parser was re-run against the live documents and matched all recorded hashes and observations.

Reproduce public recovery:

```sh
.venv/bin/python scripts/recover_sec_shares.py 0000320193 0000789019 0001652044 \
  --as-of 2026-09-24 --identity 'Research application contact@example.com' \
  --output /tmp/sec-share-candidates.json
```

Reproduce the 50-company check with the owner's existing private credential file and the previously reconciled scenario artifacts:

```sh
.venv/bin/python scripts/verify_usable_cohort.py --reviewed-scenarios \
  --output /tmp/usable-sec-cohort.json
```

The output path must not exist. The scripts make no remote writes. The cohort runner creates and removes an isolated local test account/store; source credentials are read locally and never saved to a receipt.

## Remaining limits

The broader screen's engine and the current claims-serving engine must align before per-share results can be published for that cohort. No fallback engine is silently substituted. Raw class evidence still needs reconciliation against corporate actions and class-specific claim semantics. Dated identity review, incomplete annual histories and issuer-specific assumptions remain explicit expansion work.

Production and source CURRENT pointers, private licensed datasets and provider subscriptions are unchanged. Only the pre-existing dedicated DCF staging deployment is used for hosted verification. No new cloud resources or purchases were created.
