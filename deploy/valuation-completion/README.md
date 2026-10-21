# Private cloud accounting packets

This staging Worker reuses `ppe_packets.build_packet`, `eligibility_gate`, and
`valuation_readiness`. It reads one bounded ZIP member from the existing pinned
SEC archive in R2, verifies source ETag, header/name, length, CRC, member SHA and
CIK, and caches the full member privately. It does not reacquire the SEC archive
or fetch providers. No financial computation or financial payload download runs
in the laptop controller.

Build with `python3 scripts/build_cloud_packet_runtime.py`, then deploy using
`wrangler deploy --config deploy/valuation-completion/wrangler.jsonc` from the repo
root. Reuse the root locked Python Worker dependencies in `python_modules`; the
build creates only a symlink from this config directory. No new environment is
needed. Provision secret `TOKEN` through stdin from the existing private profile.
There is no workers.dev route; the private funnel uses a service binding.

The funnel's queue runs with 24 consumers, one symbol per message and bounded
retries. Submission pins a run generation, runtime digest and UTC gate date.
Tasks and status pages are isolated by generation; cached packets are verified
against runtime, assessment date and packet hash. Detailed accounting diagnostics
stay private in R2; controllers receive machine codes, counts and source refs.

`python3 scripts/run_cloud_valuation.py submit` submits eligible already-queried
symbols. `status` refreshes bounded status pages and aggregates metadata. A packet
receipt is never a DCF result. Assumptions remain
`COMPANY_SPECIFIC_RESEARCH_REQUIRED`; no generic forecast, discount-rate or
terminal-growth defaults are introduced.

Existing source identity evidence remains scoped to its provider/date. The
canonical reference has provisional ticker keys; the legacy OpenFIGI adapter is
present in Financial System but its configured local mapping file is absent.
It also aliases FIGI to composite FIGI, so that field cannot establish a distinct
share-class identity without authoritative mapping evidence.

`python3 scripts/run_cloud_valuation.py reconcile` publishes a partitioned snapshot
of all 2,629 symbols, including pending and blocked rows. Read `/valuation-ledger`
to obtain its `manifest_sha256`, then supply it as `expected_manifest_sha256` on
all `?part=n` requests. Parts and manifests are immutable by content hash, so a
later reconciliation cannot mix a client's pages across snapshots.

Current provider references reuse the October 20 `continuous-v1` Alpaca asset
snapshot already in R2. Projection checks its fixed size/ETag, records SHA-256,
validates actual UUID syntax, and filters the frozen cohort. Those UUIDs are
provider references; they do not certify the CIK/share-class join or extend CRSP
identity intervals. The dated object key and storage timestamp are recorded;
a provider observation timestamp is not present in the payload.
