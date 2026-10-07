# Using the engine inside your workflow

The calculation engines are the source of truth. LLMs, scripts and
spreadsheets orchestrate; they never compute valuations themselves.

## LLM assistants (MCP)

`POST /mcp` is a stateless JSON-RPC 2.0 endpoint using the Streamable HTTP
pattern (`initialize`, `tools/list`, `tools/call`, `ping`). Discovery:
`GET /.well-known/mcp.json`. `GET /mcp` returns 405 by design.

Three read-only tools, all grounded in the audited server-side models:

| Tool | What it does |
|---|---|
| `value_company` | Baseline football field: DCF intrinsic + 12-month target, DDM lanes when dividends exist, peer-relative target, bear/base/bull band, reverse-DCF implied growth, top drivers |
| `reverse_dcf` | Solves for the uniform revenue growth or EBIT margin the market price implies; reports `below_range` / `above_range` / `unsolvable` explicitly |
| `search_tickers` | Ticker autocomplete by symbol or company-name fragment |

```bash
curl -X POST $BASE/mcp -H 'Content-Type: application/json' -d \
  '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
curl -X POST $BASE/mcp -H 'Content-Type: application/json' -d \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"value_company","arguments":{"ticker":"AAPL"}}}'
```

Point any MCP-capable client (Claude, ChatGPT connectors, Muse,
custom agents) at `$BASE/mcp`. Guardrails: treat tool output as the
numbers; never ask the model to recompute DCF math.

## Code and API

- `POST /api/load/{dcf|ddm|relative}` — load a ticker, returns
  `{financials, form, warnings, load_summary}` without saving.
- `POST /api/calculate` (and `/ddm`, `/relative`) — `{financials,
  assumptions}` in, full result out. Money is unrounded in JSON.
- `POST /api/compare` — one-ticker football field.
- `POST /api/compare/batch` — up to 8 tickers per call, per-ticker
  `{ticker, company_name, market_price, lanes}` or `{ticker, error}`;
  one bad ticker never fails the batch.
- `POST /api/reverse` — implied growth/margin for a market price.
- `GET /api/providers` / `/providers` — adapter status, no secrets.
- `GET /ready`, `GET /health` — deployment checks.

Budgets: previews 120/min, references 20/min, writes 10/min per
client (HTTP 429 when exceeded). Invalid input is 400, provider
failure is 503.

## CLI, spreadsheets, exports

```bash
python run_dcf.py --help
```

`POST /export/json` is the lossless interchange format (inputs,
assumptions, results, provenance). `POST /export/csv` opens in Excel;
full formula workbooks come from the XLSX export. Re-import any
`financials` object from a JSON export as a new input.
