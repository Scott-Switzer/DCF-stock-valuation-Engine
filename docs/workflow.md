# Using the engine inside your workflow

The calculation engines are the source of truth. LLMs, scripts and
spreadsheets orchestrate; they never compute valuations themselves.

## LLM assistants (MCP)

`POST /mcp` is a dual-era JSON-RPC 2.0 endpoint on Streamable HTTP.

- **2026-07-28 (current, stateless):** every POST sends
  `MCP-Protocol-Version: 2026-07-28`, `Mcp-Method` (and `Mcp-Name` for
  `tools/call`) headers, and matching `_meta` protocolVersion. Discovery via
  `server/discover`; `tools/list` results carry `ttlMs` and `cacheScope`.
- **2025-06-18 (legacy):** `initialize` first, then the same methods with
  `MCP-Protocol-Version: 2025-06-18`.
- Header/body mismatches return 400 (-32020), unsupported versions 400
  (-32022, with the supported list), unknown methods 404 (modern) or 200
  error (legacy), notifications 202. A present `Origin` must be this host
  or listed in `MCP_ALLOWED_ORIGINS`, otherwise 403. Batches are rejected.

Discovery: `GET /.well-known/mcp.json`. `GET /mcp` and `DELETE /mcp`
return 405 by design.

Three read-only tools, all grounded in the audited server-side models:

| Tool | What it does |
|---|---|
| `value_company` | Baseline football field: DCF intrinsic + 12-month target, DDM lanes when dividends exist, peer-relative target, bear/base/bull band, reverse-DCF implied growth, top drivers |
| `reverse_dcf` | Solves for the uniform revenue growth or EBIT margin the market price implies; reports `below_range` / `above_range` / `unsolvable` explicitly |
| `search_tickers` | Ticker autocomplete by symbol or company-name fragment |

```bash
curl -X POST $BASE/mcp -H 'Content-Type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' -H 'Mcp-Method: tools/list' -d \
  '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
curl -X POST $BASE/mcp -H 'Content-Type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: value_company' -d \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"value_company","arguments":{"ticker":"AAPL"},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
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

Budgets: previews 120/min, references 20/min, MCP 60/min, writes 10/min (including DELETE) per
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

## Accounts

`/account` (HTML) and `POST /api/account/{signup,login,logout}` (JSON) use
email and password. Passwords are PBKDF2-SHA256 at 100,000 iterations, the
Workers WebCrypto maximum. Sessions are 256-bit tokens in an HttpOnly, Secure,
SameSite=Lax cookie; only their SHA-256 digest is stored and logout revokes
the row. `GET /api/account/me` returns 401 without a session. Signing up or
in claims the browser's existing library. Cookie-bearing writes must come
from this origin (403 otherwise). Known gaps: no email verification and no
password reset, because no mail sender is configured yet.

## Scale and limits

- Each D1 database is capped at 10 GB; valuations are not pruned yet, so
  heavy users grow storage. History is indexed by owner and time.
- A watchlist holds 25 tickers; a refresh re-prices within a 12-second budget
  and marks the rest for reload.
- Workers Free allows 10 ms CPU per request and 50 subrequests per invocation.
  Python Workers, PBKDF2 logins and 8-ticker batches need a paid plan for
  headroom (paid: 30 s default CPU, 10,000 subrequests).
- D1 allows 100 bound parameters per statement; the code uses small fixed
  parameter counts.
