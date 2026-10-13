# Company packets and coverage ledger

`GET /api/company/{ticker}/packet?as_of=YYYY-MM-DD` assembles one dated
`company-packet-v1` response from the existing automatic DCF loader. It contains
normalized financial inputs, field receipts, units, fiscal periods, availability
dates when known, method readiness, dataset mapping/use counts, and SEC accession
references already present in fact provenance. Four peer candidates are included
as unreviewed suggestions. Analyst references are included only when an existing
issuer-bound USD cache entry is recent and no later than the valuation date.
Assembly does not start an additional analyst or peer acquisition request.

`GET /coverage/{ticker}` displays the ledger and links all 25 validation companies.
Both packet and coverage routes share the reference request rate limit. A company
whose required automatic inputs are unavailable returns a BLOCKED packet with the
reason, not a fabricated valuation or an omitted ledger row. Invalid dates and
query parameters are rejected. The public packet never reads WRDS/private records.

## Source quality

The assembler preserves the established published SEC overlay and labeled baseline
selection. It does not introduce an unreviewed source-selection algorithm or resolve
new dataset conflicts. Values remain absolute USD or shares; prices are USD/share
and tax rates are decimal ratios. Earlier annual observations are HISTORICAL, not
stale merely because they are old. Price freshness uses 7 calendar days; the latest
annual period uses 550 days. These are explicit screening policies, not market
session calendars or assertions of currentness. Missing dates remain UNKNOWN. Baseline retrieval/cutoff dates are retained as
`reported_available_at`, but are not promoted to verified financial availability.
Fiscal-year grouping uses the normalized row identity while displaying the exact
source period date.

PARTIAL means contract/readiness checks ran but independent filing reconciliation
is not established. Contract validation, source accuracy and arithmetic agreement
are distinct. The ledger explicitly identifies unmapped private WRDS, macro, news,
filing-corpus and lakehouse data. Dataset-family discovery is based on the existing
connection inventory; readability is not reprobed by each packet request.

## Automatic-load cache

`POST /api/load/{method}` shares successful default automatic loads for up to 300
seconds in the existing provider cache. Cache keys include build commit, method,
ticker and valuation date. Integrity digest, identity, date and TTL are checked on
hits; corruption or cache failure falls back to normal loading. Original financial
observation dates are never replaced by cache timestamps. Hits return current
request elapsed time separately from the original assembly time.

Only default 5% equity-risk premium and 1.5% credit spread loads are shared.
Custom assumptions bypass this cache. Imported documents, saved valuations and
account research are not cached by this mechanism. Failures are not cached. A new
source publication can take at most this additional five-minute TTL to appear in
an already assembled bundle. This is on-demand caching, not a new scheduled
acquisition job, distributed single-flight guarantee or high-concurrency benchmark.

## Reproducible 25-company ledger

```sh
# Replay previously captured dated public snapshots without upstream traffic.
uv run python scripts/build_company_ledger.py \
  --snapshots find/outputs/research-expansion/snapshots \
  --output find/outputs/company-packets/offline-ledger.json

# Exercise the deployed assembler. Retains blocked/failing companies and writes
# individual packets, JSON summary and Markdown matrix locally. No valuations saved.
uv run python scripts/build_company_ledger.py \
  --base https://dcf-valuation-engine.scswitzer.workers.dev \
  --output find/outputs/company-packets/live-ledger.json
```

Live requests default to a 3.2-second delay to respect the reference budget; do not
run other reference sweeps concurrently. Use the separate financial validation
script for independent DCF reconciliation. A coverage ledger does not replace it.
