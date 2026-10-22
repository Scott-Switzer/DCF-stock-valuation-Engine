# Shared financial queries

Slack, the terminal command and the DCF website now use the existing private cloud
backend for historical price, price growth and SEC financial questions. Ordinary
financial questions bypass the older research planner. Research stays on its
existing route.

Examples:

- `/zion AAPL price on 2020-01-02`
- `/zion AAPL growth from 2010-01-04 to 2020-01-02`
- `/zion Apple revenue growth in 2025`
- `/zion AAPL revenue`
- `/zion PEP operating margin`
- `python3 scripts/finance.py AAPL price on 2020-01-02`

The existing `/data` workspace now includes the question form alongside its stock,
dataset and file browsers. Public SEC questions work without a key. Private price
questions reuse the connected tab's owner data key; disconnecting clears their
results. Signing up with an owner-looking email does not grant access.
Public `/api/company/<ticker>` serves only SEC-derived statements. Its existing
DCF load path reads those newer packets through a private service binding, then
uses the existing model, editable assumptions and market-data loading logic.

Observed-date prices do not mean information available at that historical time.
Price queries use exact trading sessions and raw observed prices. Growth uses
split-adjusted prices from one native CRSP security and excludes dividends; it is
not total shareholder return. Unknown dates, missing prices/factors and ambiguous
identities fail explicitly. Full native security history can include former
ticker names. Financial history displays reported annual revenue and operating
margins with source dates; derived margins include both input lineages.

The owner-authenticated Slack Worker `/api/ask?query=...` uses the actual Slack
parser, MCP transport and renderer without posting a message. This supports
read-only integration checks; it does not prove delivery to a Slack conversation.

Production rollout was approved by the user. Deploy with `wrangler deploy --config
wrangler.production.jsonc`; preserve the existing four service bindings and add
`FINANCIAL_DATA`. No source `CURRENT` pointer is promoted. The live production
feature branch was merged into main before release so its private data workspace,
benchmarks, screen and additional valuation methods remain present.
Slack's existing staging-named Workers are the services already configured in its
app manifest; their financial-query path is deployed. Private tokens are configured
as existing Worker secrets, never in Git or response logs.

Company names resolve through the stored SEC directory; explicit ticker ambiguity
is reported. Revenue growth means year-over-year change in consecutive full fiscal
years, with each pair of reported inputs retained. The prior year is loaded even
when the requested output range starts in a later year. This is reported growth,
not an organic-growth estimate or an acquisition-adjusted forecast.
