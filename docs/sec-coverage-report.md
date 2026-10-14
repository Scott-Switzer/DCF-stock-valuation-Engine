# SEC financial coverage: before / after (staging)

Measured 2026-10-14 on staging (`e26eeee`, worker version
`c9bf1291-ba3b-4f51-adb4-281c3df81966`) and production (`d1008a0`, version
`137718bd-…`). "Coverage" here means: the load either produces a baseline brief
with a preview, or fails **for a reason the user can act on**.

## Before → after

| Ticker | Before | After | Change |
| --- | --- | --- | --- |
| AAPL | loads | loads, 91.81 | parity held (byte-identical across repeat loads) |
| MSFT | loads | loads, 119.40 | unchanged |
| PEP | loads (Yahoo $196.95 prod / SEC-first $163.20 staging) | loads, SEC-first 163.20 | source conflict now explained, not hidden |
| XOM | loads (Yahoo fallback) | loads, 153.26 | unchanged; `CURRENT.json` has no XOM entry |
| BAC | `Yahoo missing OperatingIncome for 2023-12-31; cannot complete financials.` | `SEC SIC 6021 (National Commercial Banks) is a financial firm; an industrial FCFF DCF cannot be completed from its available statements (Yahoo missing OperatingIncome …). Use P/E and P/B relative valuation or file-based review.` | 503 → 503, now actionable |
| JPM | same opaque error | same reframed SIC 6021 message | actionable |
| O | `Yahoo missing CapitalExpenditure …` | `SEC SIC 6798 (Real Estate Investment Trusts) is a financial firm; …` | actionable |
| MRX | loads, brief skipped | unchanged (`minority_interest must be at least 0.`) | already explained |
| ORCL | `Nonzero preferred equity requires an explicit preferred cost assumption` | unchanged | pre-existing, honest |
| unknown ticker | validation error | unchanged | unchanged |

Net: two tickers (BAC, JPM) plus O move from an unexplained provider error to an
explicit suitability statement; no ticker lost coverage; every intrinsic value
other than PEP's source-corrected path is unchanged.

## What the BAC/JPM investigation found

1. **The publication pointer already serves both.** `control/valuation/CURRENT.json`
   contains valid entries for BAC (release `5895c908…`, served via the DIRECT_R2
   path) and JPM (release `166978062e…`). The packets are reachable and
   integrity-checked; this is not a serving gap.
2. **The packet deliberately carries nulls.** `BAC.json` has
   `"capex": null` and an all-null `bridge`, because those fields are absent
   from the filed companyfacts archive member — the packet records absence
   rather than inventing a value.
3. **The 503 was a preference problem, not a data problem.** The SEC-first gate
   did not select the packet for these tickers, so the load fell through to
   Yahoo, whose annual API no longer returns industrial operating income for
   banks. The error that surfaced described Yahoo, which pointed the user at
   the wrong remedy (retry the provider) for a structural fact (banks are not
   FCFF-DCF candidates).
4. **Fix shipped (#32, reusable):** on statement failure the load resolves
   issuer classification and, for **confirmed financial firms only**, replaces
   the provider error with an SEC-SIC-labelled suitability message that
   preserves the original cause. Non-financial and unconfirmed tickers keep the
   exact original error; a classification lookup failure also keeps it. No
   bank or brokerage is pushed through an industrial FCFF DCF, and no Yahoo
   mapping was faked to make a bank value.

## Packet gaps (not fixed, recorded honestly)

- `BAC.json`: `capex` and the whole `bridge` are null in the published packet.
  Bridge values are derivable from companyfacts (`CashAndCashEquivalents`,
  `LongTermDebtNoncurrent`, `LongTermDebtCurrent`, `StockholdersEquity` are all
  present in the same accession), so filing-backed extraction is feasible — but
  it is a packet-builder change, and packets are staging-only publications.
  Not attempted here rather than shipping a half-built extractor.
- `XOM` and `PEP` have no `CURRENT.json` entry: production intentionally falls
  back to Yahoo for them. The PEP case is quantified in
  [pep-reconciliation.md](pep-reconciliation.md) and is the strongest argument
  for promoting SEC-first coverage — that promotion needs separate approval.

## Additional staging SEC-first example

PEP is already the working SEC-first example (gate passes, 3 annual periods,
1.373B diluted shares, preferred equity 0.0 via filed buildup residual,
accession `0000077476-26-000007`). BAC/JPM are **not** suitable examples: their
filed packets lack CAPEX and bridge fields by construction, so manufacturing an
SEC-first industrial DCF for them would be fabricated coverage. Recorded as work
for the packet builder, not claimed as delivered.
