# Private cloud readiness reconciliation

Staging-only Cloudflare Worker. Reads existing signed SEC queries and stored input
packets from private R2, checks all 2,629 frozen symbols, and persists readiness,
freshness, explicit gaps, cited briefs, and repair cohorts. The private research
binding reads only pinned existing materializations. No raw provider archives,
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

Source ownership stays with Project-Portfolio-Engine; private financial serving
stays with zion-terminal; this directory is the DCF integration layer. No additional
repository copies or data backfills are needed.
