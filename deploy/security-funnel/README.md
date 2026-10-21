# Private cloud readiness reconciliation

Staging-only Cloudflare Worker. Reads existing signed SEC queries and stored input
packets from private R2, checks all 2,629 frozen symbols, and persists readiness,
freshness, explicit gaps, cited briefs, and repair cohorts. No raw archive binding,
provider requests, model assumptions, or production pointer writes.

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

The metadata-only controller is scripts/run_cloud_reconciliation.py. It uses the
existing source-estate environment and private credential helper; no secrets or
financial datasets are in this branch. Operational evidence is private in R2.
