# CRSP total return with delisting treatment — release receipt

Date: 2026-10-26
Status: **deployed to staging; live acceptance passed on the question, CLI and MCP paths.**
Related: shared query change in this branch, gateway MCP change in
`financial-assistant-gateway` (`codex/total-return-mcp`).

## Why

The only historical return the system served was `growth`: `split_adjusted_price`
at two sessions, `includes_dividends:false`. CRSP's daily `RET` and its delisting
file were stored but unused, so any portfolio or backtest arithmetic built on
`growth` understated long-horizon outcomes and silently ignored total losses.

## What shipped

- `total_return` action on the shared `/query` route (`{action,symbol,date_from,date_to,include_series?,max_points?}`),
  plus natural language: `AAPL total return from 2010-01-04 to 2020-01-02`,
  `dividend-adjusted return`.
- Chains the stored `source_total_return` column and reports, in one answer, the
  cumulative total return, its annualization, the split-adjusted price growth over
  the same window, and the distribution contribution between them.
- Delisting treatment is explicit and never double counted:
  - reported CRSP delisting return → the source row already contains it,
    `APPLIED_ONCE_BY_SOURCE_ROW`, `cross_check` against `DSEDELIST.DLRET`;
  - unreported delisting return → the observed chain is returned as an upper bound
    with `bounds {lower:-1, upper}`, status `DELISTING_RETURN_NOT_OBSERVED`, no
    imputation;
  - interior missing returns → segments, no single cumulative claim.
- `delistings-index.json` derived from `crsp_a_stock__dsedelist` (catalog
  `4833fe6633fc104b61475e35b253898a`): 38,872 rows scanned, 1,898 true delistings
  (`dlstcd>=200`) for frozen permnos, 82 KB, entries sha256
  `616fa3a40ec31d1923659044a22323bab324dcf89769e30ea3cc9460c007bc93`, source object
  sha256 `c56ce83b872128339434bf5aa1d296083d059c82c3f92bc28a9bd6f7502fa28e`.
  Built by `scripts/build-delistings-index.mjs` (shared `delistingEntries` rules) or
  the owner-only `POST /connect/delistings-init`.

## Deployed identities

| Component | Worker | Version | Previous |
| --- | --- | --- | --- |
| Shared query | `zion-security-funnel-staging` | `932c4a23-4cb5-4655-b10f-19f5716dfa98` | `e2dd73ce-a47c-4410-8df3-9e9ebaea90b6` |
| MCP reader | `zion-financial-mcp-staging` | `a722421e-8754-4fa3-a823-2f32ac8a273e` | `8824a564-ba43-40fc-9878-c1b5ce1328f8` |

Both deployed with `--keep-vars`. No secret, bucket, queue, service binding,
pointer or licensed object changed; one new data object (`delistings-index.json`)
was added to the existing full-history prefix.

## Verified live (2026-10-26)

| Check | Result |
| --- | --- |
| `AAPL total return from 2010-01-04 to 2020-01-02` | 200; **1029.18%** total return (27.45% annualized) over 2,517 sessions vs **882.41%** split-adjusted price growth; dividends **+14.94%**; 0 missing returns; `data_as_of 2020-01-02` |
| `VIVO total return from 2020-01-02 to 2023-01-31` | 200; 253.80% total return; delisting `2023-01-31` code `233` (merged) with row return `0.000883` matching `DLRET`; `APPLIED_ONCE_BY_SOURCE_ROW`, `cross_check MATCH_OR_NOT_RECORDED`; price comparison ends `2023-01-30` and says so; provenance carries index + source shas |
| Structured `total_return` through CLI → MCP | 200; identical numbers; `include_series:false` returns no series array |
| `max_points: 1` | 422 `INVALID_REQUEST: max_points must be 2–5,000.` |
| Anonymous funnel `/query` | 401 |
| Website `/api/data/query` without a key | 403 |
| MCP tool scope | still exactly `load_dcf_model`, `query_financial_data` |

Tests: `deploy/security-funnel/test/total-return.test.mjs` (7, pure math and
delisting classification), `structured-query.test.mjs` (7, now includes the
total-return route and the reported-delisting path), MCP `vitest` 33 passed,
`tsc --noEmit` clean. The existing funnel adapters (reader, history, valuation,
enrichment, queries) still pass.

## Not verified / limits

- The unobserved-delisting branch is unit-tested and reachable, but the frozen
  universe currently exposes no symbol whose resolved permno has both a null
  `DLRET` and reachable sessions, so it was not exercised against live CRSP rows.
- A price series has no adjusted price on the delisting row, so the dividend
  contribution is only reported when both series share the end date.
- Total return is not point-in-time: the adjustment base remains retrospective
  (`crsp-ciz-research-v1`) and `historical_availability` is still
  `NOT_ESTABLISHED`.
- Licensed CRSP values stay private; no redistribution right is implied.

## Rollback

```bash
npx wrangler rollback e2dd73ce-a47c-4410-8df3-9e9ebaea90b6 --config deploy/security-funnel/wrangler.jsonc
cd mcp && npx wrangler rollback 8824a564-ba43-40fc-9878-c1b5ce1328f8
```

Rollback leaves `delistings-index.json` in place; it is inert to the previous
version.
