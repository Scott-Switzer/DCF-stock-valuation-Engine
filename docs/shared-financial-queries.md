# Shared financial queries

Slack, the terminal command and the DCF website now use the existing private cloud
backend for historical price, price growth and SEC financial questions. Ordinary
financial questions bypass the older research planner. Research stays on its
existing route.

Examples:

- `/zion AAPL price on 2020-01-02`
- `/zion AAPL growth from 2010-01-04 to 2020-01-02`
- `/zion AAPL revenue`
- `/zion PEP operating margin`
- `python3 scripts/finance.py AAPL price on 2020-01-02`

The staged website exposes `/data`; private queries require the existing private
financial-system access key (held in page memory only) or a separately provisioned
owner user ID. Signing up with an owner-looking email does not grant access.
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

No production data pointer is promoted. The DCF website binding is staging-only.
Slack's existing staging-named Workers are the services already configured in its
app manifest; their financial-query path is deployed. Private tokens are configured
as existing Worker secrets, never in Git or response logs.
