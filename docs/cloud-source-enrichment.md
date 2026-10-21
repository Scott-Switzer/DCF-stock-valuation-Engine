# Private source enrichment continuation

The existing staging Workers and queue now read the verified October 15 SEC
companyfacts archive already stored in private R2. The frozen 2,629-symbol cohort
is unchanged. The source plan covers 2,296 issuers and 2,317 symbols, including
388 symbols excluded by the previous completed-query restriction; 312 retain an
explicit missing CIK/archive-member reason. Source availability does not imply a
supported accounting taxonomy or a completed valuation.

The Python Worker verifies the archive/index/manifest context, performs bounded
ETag-conditional ZIP member reads, and verifies length, CRC and issuer identity.
Each raw member is content-addressed and reused through a source-context receipt.
No archive or financial payload is downloaded to the controller computer.
All annual packet construction and recent capital-claim projection run privately
in Cloudflare. Existing annual provider/adjustment policies remain in force.

Recent claims require one filing accession, period end and filed date. Missing
claims remain missing. Derivations require explicit same-filing components;
unspecified debt and notes components cannot prove total noncurrent debt. Weighted
average diluted shares remain qualified as neither spot nor class-specific shares.
Unsupported IFRS contexts have an adapter gap rather than a false absent-source
claim. Company-specific research and forecast assumptions remain required.

A single bounded SEC issuer-directory fetch also runs in Cloudflare and is cached.
Its reference confirms only current issuer/ticker evidence; conflicts with frozen
CIKs remain visible. It does not certify historical listings or share classes.
Unavailable/unassessed directory evidence is distinct from a checked negative match.

## Operations

Reuse the existing private API token profile; never put credentials in command
arguments. The controller writes metadata receipts only, outside Git:

```sh
python3 scripts/run_cloud_enrichment.py init
python3 scripts/run_cloud_enrichment.py submit
python3 scripts/run_cloud_enrichment.py status
python3 scripts/run_cloud_enrichment.py ledger
```

Do not resubmit a healthy active run or deploy a different Python runtime while its
queued messages are active. Jobs pin runtime, assessment date and source plan;
transient failures remain pending through bounded retries before becoming gaps.
The current run is `7f8e055fe0eae34a1582dff99cc970e9ceb9d74cdcc5959f32ee2a929ae37880`.

Ledger construction pins the parent accounting job, provider asset snapshot and
SEC directory evidence together. All 132 parts are content-addressed; finalization
checks their hashes, contexts and exactly 2,629 distinct symbols. Private
`GET /enrichment-ledger` returns the manifest; paged reads require
`part=N&expected_manifest_sha256=...`. Existing full history and older valuation
ledgers remain inspectable. The new section reports source freshness, recent-claim
period, annual accounting result, current SEC identity evidence and explicit gaps.
A source snapshot date is not an SEC acceptance timestamp or a live-price date.

Production data-pointer promotion remains a separate approval. This work does not
claim complete valuations, historical identity certification or trading readiness.
