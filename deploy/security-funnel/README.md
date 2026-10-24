# Private cloud readiness reconciliation

Staging-only Cloudflare Worker. Reads existing signed SEC queries and stored input
packets from private R2, checks all 2,629 frozen symbols, and persists readiness,
freshness, explicit gaps, cited briefs, and repair cohorts. The private research
binding reads pinned existing materializations and one pinned native factor
partition for a bounded repair audit. No bulk archive replay,
upstream provider requests, invented model assumptions, or production pointer writes.

`TOKEN` is a Worker secret. All routes require bearer authentication. POST routes:
`/initialize`, `/batch?n=0`, `/finalize`, `/reuse`. GET routes: `/status`,
`/security?symbol=`, `/brief?symbol=`, `/report`. Reads use fixed campaign paths.

The current campaign was initialized before the expanded campaign pin; finalize
binds that legacy pin to the frozen campaign hash and implementation version.
Do not reinitialize it with changed code or inputs: use a new output prefix.
Completed batch checkpoints can upgrade packet checks without rereading financial
queries. A source packet is not an executed valuation. No full workflow is certified.

Reuse existing Project-Portfolio-Engine security master/OpenFIGI, canonical_v1
identity.py, issuer_links.py, and prices.py. The reuse route checks the hash of an
existing recent Alpaca publication in cloud and records source-native availability,
not a verified issuer/security join. Raw, split-adjusted, distribution-adjusted,
and total-return series remain separate.

The metadata-only controllers are `scripts/run_cloud_reconciliation.py` and
`scripts/run_cloud_connections.py`; both use standard Python and the existing
private API credential profile (or ZION_PRIVATE_API_TOKEN). FUNNEL_RUN_DIR can
select the receipt directory. No other checkout or data library is required to
submit work. No secrets or financial datasets are in this branch; the tiny
Parquet test fixture is synthetic. Operational evidence is private in R2.

## Existing-dataset connections

`connections.mjs` consumes existing Project-Portfolio-Engine identity assertions,
issuer links and adjusted-price Parquets, plus an immutable recent Alpaca daily
publication. File hashes, sizes and row counts are checked in Cloudflare. Columns
are decoded one at a time. Raw quotes, retrospective split/distribution adjustments,
native issuer associations, dated CIK links and recent unjoined prices stay distinct.
Unknown public availability, provisional boundaries, missing factor rows, conflicting
identifiers and multiple matching securities remain visible.

After the pinned source metadata has been staged, run controller actions in order:
`init`, `identity`, `prices`, `price-index`, `batch`, `finish`. These are bounded
cloud tasks with reusable checkpoints, not a new acquisition pipeline. Final ledger
publication streams batches and checks their hashes again; the completion marker is
written last. Private `/security`, `/brief`, `/status`, and `/report` then serve the
connected data. Prior reconciliation output remains preserved.

Then run `select-init`, `select-batch`, `select-finish` to resolve reused tickers
at the actual latest native source date using those saved projections. Selection
requires both a native observation on that date and an active ticker interval.
Historical alternatives remain attached; unresolved ties stay explicit. The new
release becomes readable only after its completion summary exists. This does not
extend historical identities to the recent Alpaca session or establish a provider
bridge, public availability, or point-in-time eligibility.

Source ownership stays with Project-Portfolio-Engine; private financial serving
stays with zion-terminal; this directory is the DCF integration layer. No additional
repository copies or data backfills are needed.

## Full historical connections

Run `history-init`, `history-batch`, `history-expand-batch`, `history-finish` after source-date selection.
Initialization catalogs all saved price projections without rereading Parquet.
The immutable source-date selection chooses a PERMNO; it never sets the beginning
of that PERMNO's history. Former ticker periods remain included. Ambiguous symbols
require an explicit candidate PERMNO. Every release retains all alternatives.

Authenticated reads:
- `/history?symbol=AAPL&metadata_only=true`: full stored coverage and partition count.
- `/history?symbol=AAPL&limit=100`: raw, split/distribution-adjusted and native return
  fields from one verified existing Parquet partition. Follow `next.part` and
  `next.offset`, retaining symbol/date filters and `expected_input_sha256`, until
  `next` is null. Partitions are in source date-range order; rows retain source
  order. Omit date filters to traverse the entire source history.
- `/stored-history?source=crsp&permno=...`: existing Zion full-history API through
  a service binding. Its release IDs, native pagination, source semantics and
  permission gates remain authoritative. Other supported source views include
  `alpaca`, `alpaca_latest`, `yfinance`, `simfin`, `tiingo`, `eodhd`, `marketstack`,
  `polygon`, `twelve_data`, and `estate_alpaca`; coverage stays source-specific.
- `/valuation-inputs?symbol=AAPL`: every available observation from the full-range, nine-metric
  HMAC-verified annual SEC queries, with decimal strings, periods, availability and
  source records unchanged. This is an input source, not a model-ready document
  or an executed valuation. Existing published PPE packets are checked separately.

Factor auditing distinguishes absent joined source-factor rows from other unusable
adjusted values. Separate marginal invalid counts establish only a lower bound
for rows where either adjusted value is unusable. Never fill missing factors with
one or reuse weighted-average diluted shares as spot outstanding shares.
The recent-price bridge verifies the existing collector's published internal target
ID mapping; it does not relabel those IDs as Alpaca UUIDs or establish a dated
cross-provider issuer/class mapping. Its September target snapshot date stays visible.

`POST /connect/history-source-audit` inspects the pinned existing source catalog
metadata for alternate factor and identity sources. It reads no raw financial
payload and makes no provider request. All these routes remain private and staging-only.

The expansion phase calls the existing cloud financial engine for already
materialized issuers. Its 100-year query budget requires disjoint 1900–1999 and
2000–2026 windows. Both windows retain independent query fingerprints; combining
them changes no financial definitions or decimal values. It verifies zero interactive
archive bytes read. Failed expansions remain explicit and retryable without
repeating successful companies.

`/financial-history?cik=...&frequency=quarterly` (or `annual`/`ttm`) connects the
same existing engine. The default starts in 1900, not 2015. Follow native pagination
inside the returned `full_history_window`, then its `next` date range. The endpoint
uses the pinned financial release and never silently extends its freshness.

`POST /connect/history-factor-source-audit` reads the one pinned existing native
CRSP sample-factor partition in Cloudflare and compares its identity/date coverage
to histories with missing factors. It checks whether full-factor aliases are exact
payload duplicates. It reports repair candidates; it never splices sample adjustment
bases into the full history or labels candidates as repaired rows.

### Shared reader integration (October 22, 2026)

Exact recent-session questions such as `PEP price 2026-10-21` call the existing
thin `/v1/market/prices/PEP?session=2026-10-21` endpoint. The answer retains the
session's release hash and its parent `daily_session_index` hash. The source and
shared API must agree on the bundle; an absent session is never replaced with
the latest close. This adds daily-session lookup, not cross-provider returns or
point-in-time certification.

`WRDS coverage` and `WRDS datasets comp` use the existing private collection
catalog. The source snapshot must register `COLLECTION_CATALOG_KEY`; a different
catalog deployment fails closed. Only whitelisted metadata is returned (at most
50 entries); declared rows do not establish completeness. The authenticated
catalog endpoint remains available for pagination and detailed source schemas.
No licensed records, raw files, inferred units, or invented availability dates
are returned through this question route. Website owner access, terminal, Slack,
and MCP reuse these same shared routes.

### Explicit request objects

The same GET `/query` accepts either `query` text or one JSON-encoded `request`.
They are mutually exclusive; duplicate inputs, unsupported fields and invalid
calendar dates fail instead of silently changing the question.

```json
{"action":"price","symbol":"ON","date":"2020-01-02"}
{"action":"growth","symbol":"AAPL","date_from":"2020-01-02","date_to":"2021-01-04","basis":"split_adjusted_price"}
{"action":"financials","symbol":"AAPL","metric":"revenue","date_from":"2024-01-01","date_to":"2025-12-31"}
{"action":"dataset_catalog","search":"comp","offset":50,"limit":10}
{"action":"dataset_detail","dataset_id":"0123456789abcdef0123456789abcdef"}
```

A price without `date` means latest stored close. Financial requests default to annual
observations; both dates or neither must be supplied. Catalog limits are 1–50;
follow `next_offset` while retaining the same source bundle. Structured symbols
avoid ambiguity for short tickers such as `A` and `ON`. Dataset detail takes only
the 32-character catalog id (`WRDS dataset <id>` works as natural language) and
returns the same whitelisted metadata projection: id, dataset, family, release,
declared rows, object descriptors and native column descriptors. Raw records,
object payloads and unlisted keys are never returned.

The website `/api/data/query` forwards this same input and retains owner-only
price/catalog access. `scripts/finance.py --request '<JSON>' --json` uses the same
API. The separate [Financial Assistant Gateway MCP reader](https://github.com/Scott-Switzer/financial-assistant-gateway/pull/23) `query_financial_data` accepts `{request: ...}` or `{query: ...}` without
adding tools or credential scope. Invalid inputs never authorize acquisition.


Structured financial requests also accept `frequency: "quarterly"` or `"ttm"`;
`AAPL quarterly revenue 2025` and `AAPL TTM operating margin` use the same native
SEC engine. Quarter validation, TTM construction, source revisions and availability
remain owned by that engine. No annual packet or fallback replaces missing periods.
Explicit dates filter period ends. Without dates the engine defaults to 2015 or
its later minimum through the company cutoff, and the answer discloses that limit.
`Q1 2025` is rejected because fiscal and calendar quarters are not interchangeable.
Nonannual revenue growth is rejected until an explicit comparison policy exists.

The adapter bounds bytes, pages and elapsed time, preserves source records and
gaps, rejects changed source identity, and aligns margin periods/currencies.
Both annual source fallback and quarterly/TTM calls require
`materialized_only=true` (Zion #57): a missing company reports a gap without
queuing acquisition. The existing source may still cache calculations over stored
materializations. Deploy that source change before this reader.


To keep multi-request results consistent, retain `bundle_id` from the first reply
and send `x-zion-bundle-id` on the website/shared API, `--bundle-id` on the CLI,
or the optional top-level `bundle_id` on the Gateway MCP reader. A changed
snapshot returns `RELEASE_MISMATCH`; restart pagination rather than mixing pages.
This reader is separate from the DCF application's legacy `mcp.py` valuation tools.
