# Historical information cutoff (`as_of`) — release receipt

Date: 2026-10-26
Status: **merged and deployed; live acceptance passed for the shared query Worker and the MCP reader.**
Related: PR #89 (shared query), gateway PR #26 (MCP forwarding).

## Shipped identities

| Component | Commit | Worker | Version | Previous |
| --- | --- | --- | --- | --- |
| Shared query | `c4bfcab` (#89) | `zion-security-funnel-staging` | `8e468054-9e6b-4efb-accd-8aad0e9e31c8` | `4e93471b-cecf-4e6e-bd30-ecccb1648857` |
| MCP reader | `caf9f38` (#26) | `zion-financial-mcp-staging` | `8544bc4e-984c-4cd1-9b70-f1babce58662` | `4dfd3f1d-f010-44ac-bd3e-e55a58f1c1e3` |

Both deployments used `--keep-vars`. No secret, binding, R2 object, index, pointer or
schedule was changed. The only unreleased shared-query commit at deploy time was
`c4bfcab` itself; `e60e753` had already been live since the 2026-10-24T00:13Z deployment.

## What changed

Financials-only optional `as_of`, strict `YYYY-MM-DDTHH:mm:ssZ`. Annual historical reads
bypass the current materialized packets and forward the cutoff to the native SEC source,
which already selects the revision available at that instant. The validation layer
compares returned evidence against the requested cutoff at nanosecond precision and
fails closed. Requests without `as_of` are unchanged.

## Verified live

Read-only probes of the deployed service. Metadata only; no financial values were
recorded.

| Check | Result |
| --- | --- |
| `as_of=2025-05-02T00:00:00Z`, PEP quarterly revenue, 2025-01-01…2025-03-31 | 200; 1 observation; `result.as_of` and `source.as_of` echo the request exactly; accounting check `available_at=2025-04-25T04:00:00Z` ≤ cutoff; `data_as_of=2025-03-22` |
| `as_of=2025-04-01T00:00:00Z` (pre-publication) | 200; 0 observations; `coverage_gaps=[NO_VALID_OBSERVATIONS_IN_REQUEST]`; `data_as_of=null`; cutoff echoed; no fallback to later data |
| No `as_of` | 200; 1 observation; `source.as_of` absent, so current-mode provenance is unchanged |
| `as_of=2025-05-02`, `…+00:00`, `2025-02-30T00:00:00Z` | rejected (HTTP 422 / MCP input validation); no partial answer |
| Anonymous request without a bearer | 401 |
| Same three cases through the deployed MCP reader (`query_financial_data`) | identical cutoff echo, observation counts and gap codes; tool scope still exactly `load_dcf_model`, `query_financial_data` |
| Same two cutoff cases through the installed CLI (`~/.local/bin/finance --request … --json`, pinned at `6c9d53d`) | identical echo, 1 observation, and 0 observations with `NO_VALID_OBSERVATIONS_IN_REQUEST` |
| Same three cases through the deployed website `/api/data/query` (production still `6c9d53d`; not redeployed) | 200; exact echo; post-filing 1 observation; pre-publication 0 observations with the explicit gap; no `as_of` still omits `source.as_of` |
| Public Worker smoke on `main` `c4bfcab` | run 40285078319, success |

The website and CLI needed no redeploy: both forward the structured request verbatim and
the existing answer validator accepts the added `result.as_of` / `source.as_of` fields.

Identity observed on every response: bundle `2c0419d1…994a`, SEC engine release
`202719b5…db148`, CIK `0000077476`, provider `SEC`, `source_releases` 34 entries.

## Sample sweep (2026-10-26)

72 read-only requests: 12 symbols x 2 frequencies (annual, quarterly) x 3 cases (two
cutoffs, current), revenue, window 2024-01-01…2025-12-31. Metadata only.

| Group | Result |
| --- | --- |
| WMT, PEP, JNJ, CAT, MSFT, AAPL | 36 cutoff requests returned 200, every one echoed the exact cutoff, and **0** observations carried `available_at` after the requested cutoff |
| Same six, period sets | `mid (2025-04-01) ⊆ late (2026-01-01) ⊆ current` for both frequencies; quarterly goes 4–5 → 7–8 → 8 observations, annual 1 → 1–2 → 2 |
| JPM, NEE, AMT | 200 with zero observations in all three cases — the known source-layer gap, unchanged by the cutoff |
| XOM, TSLA, COST | 422 `Symbol is not in the stored universe` in all three cases — absent from the frozen query universe, which is not evidence that SEC data is absent |

Only-current quarters are the 2025Q4 periods (2025-12-27…2025-12-31), first available in
2026, so their absence at a 2026-01-01 cutoff is the intended behaviour.

Pre-existing behaviour, not introduced here: `coverage_gaps` include entries far outside
the requested window (a `1900-01-01…1999-12-31` placeholder plus 2008–2017
`AMBIGUOUS_CONCEPT_OR_DERIVATION` / `OVERLAPPING_FISCAL_CONTEXTS` items) and some entries
repeat verbatim. The identical lists appear with and without `as_of`, so the cutoff does
not add or suppress them; a future source-layer change should scope those gaps.

## Not verified

- `mcp/scripts/verify-read-data.mjs` cannot complete in this environment: it stops at
  `https://assistant-staging.scotttunnel.xyz/readyz` with `ERR_SSL_WRONG_VERSION_NUMBER`,
  the known unresolved local gateway tunnel TLS problem. The reader and model checks that
  precede that step use the same deployed MCP Worker and are unaffected.
- No point-in-time backtest was run. A cutoff narrows what the stored source may return;
  it does not certify complete historical coverage, corporate actions, or total return.

## Rollback

```bash
# shared query
npx wrangler rollback 4e93471b-cecf-4e6e-bd30-ecccb1648857 --config deploy/security-funnel/wrangler.jsonc
# MCP reader (from mcp/)
npx wrangler rollback 4dfd3f1d-f010-44ac-bd3e-e55a58f1c1e3
```

Reverting the MCP Worker alone is sufficient to stop callers sending `as_of`; the shared
Worker keeps accepting the optional field, so rollback order is not hazardous.
