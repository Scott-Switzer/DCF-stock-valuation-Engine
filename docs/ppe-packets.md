# PPE valuation packet contract

`GET /api/company/{ticker}?as_of=YYYY-MM-DD` returns `ppe-valuation-packet-v1`, or 404 when unpublished and 503 when an authoritative packet is unusable. It contains public SEC financial facts, exact fiscal periods, observation availability dates, release/hash/accession provenance, nullable fields, dated split debt and annual diluted weighted-average shares. Prices and licensed warehouse provider payloads are excluded. All monetary values are absolute USD; tax rates are decimal ratios.

## Publication

The bounded publisher reads `gold/serving/coverage25/CURRENT.json`, verifies the immutable release manifest and each SEC annual artifact, and follows the producer's identity resolver/storage keys. It never changes upstream producer pointers, starts acquisition or reads price artifacts. Explicit public SEC companyfacts files can supplement missing valuation fields. They are validated against the issuer CIK and archived by content hash.

AAPL uses three exact annual fiscal periods. Capex is a positive outflow. Operating working capital is `(current assets - cash) - (current liabilities - current interest-bearing debt)`; short-term debt is DebtCurrent or both current long-term maturities and short-term borrowing. Missing components remain missing. Tax is reported income-tax expense / pretax income. Only explicitly common dividends are accepted; generic dividends are not silently treated as common. No preferred/minority zero is invented.

The publisher processes at most four annual objects concurrently and uploads packets with read-back SHA verification. Each packet is capped at 128 KiB. All validated company objects must exist before the separate `control/valuation/CURRENT.json` pointer is conditionally promoted using its ETag. Concurrent pointer changes abort promotion. Incremental publications retain previous companies; unavailable/unsupported symbols are recorded in the report. Failure paths save accumulated diagnostics with published false until pointer promotion succeeds. Existing immutable objects remain recoverable.

Example (use an authenticated Wrangler remote R2 proxy config with binding DATA):

```sh
WRANGLER_MODULE=/path/to/wrangler/wrangler-dist/cli.js python scripts/publish_ppe_packets.py \
  --config /path/to/remote-r2.jsonc --symbols AAPL \
  --sec-facts AAPL=/path/to/public-companyfacts.json \
  --report /path/to/report.json
```

Default is dry-run. Add `--publish` to write; `--all` expands across the published resolver using existing SEC artifacts. No API keys belong in the command. The Wrangler config must use an existing account/bucket and `remote: true`. The publisher requires Node and Wrangler; they are not Worker runtime dependencies. Repeat this publication when a new upstream release or SEC supplement is available; no new scheduled job is installed by this change.

## Serving and fallback

The Worker reads a small index and one hash-verified packet through request-scoped R2 bindings. Its location cache retains the index for 60 seconds and immutable packets for a year; cache hits do not extend the pointer lifetime. Cache failure falls back to authoritative R2 reads. Storage/read/integrity/schema errors become a visible Yahoo fallback rather than an unhandled ticker failure. Public API responses remain no-store.

The application validates issuer, units, finite values, ISO dates, fiscal-period matching and cutoff availability. Yahoo sometimes normalizes a fiscal date to month-end; overlays require a unique annual match within seven days and retain actual SEC dates per field. Complete PPE rows use their actual fiscal end; partial rows retain individual field provenance and the dated baseline. Unmatched periods keep baseline data. Financial-firm eligibility rules still apply.

Latest packets cannot prove historical point-in-time selection for dates before their publication cutoff: such requests reject the packet. A historical archive/version selector is required before claiming backtest-ready coverage. Yahoo fallback observation dates describe current snapshots; their historical publication availability is unverified. SEC filing dates are day-level availability, not intraday timestamps.

Unqualified PPE net income is retained in packets for research but never substituted for common-stockholder income in the shared valuation history or P/E. Ordinary-share market equity is preserved for WACC weights; diluted annual shares remain a per-share valuation basis. Current prices, beta, Treasury benchmarks, common income, common book equity and common dividends remain labeled fallbacks where PPE has no unambiguous supported field. ROE's existing common-income/common-equity diagnostic retains its baseline basis; it is distinct from total shareholder equity. Annual weighted-average diluted shares are a dated dilution approximation, not a claim of live outstanding shares. Imported snapshots and manual overrides retain original provenance; overrides remain identified in calculation details.
