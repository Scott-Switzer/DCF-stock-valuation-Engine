# PEP valuation reconciliation: production Yahoo path vs staging SEC-first path

Same-day live loads (2026-10-14): production (Yahoo-backed, `CURRENT.json` has no
PEP entry) intrinsic **$196.95** vs staging SEC-first (candidate pointer,
accession `0000077476-26-000007`) intrinsic **$163.20** — a **$33.75/share** gap.
(Earlier reports cited $164.43 for staging; the candidate revalues with the live
quote. The bridge below uses the same-day pair.)

## Verdict up front

**The staging SEC-first value is the accurate one.** Both numbers come from the
identical model (`evaluate` reproduces each live value to the cent locally), so
there is no model error: the gap is input data. Filed SEC companyfacts show
Yahoo overstates PepsiCo FY2025 operating income by ~$2.0B and D&A by ~$0.7B.
The production $196.95 is inflated by about **$33.50/share** of provider-data
error. No mapping was changed to force agreement; the fix direction is SEC-first
expansion, which is already the workstream.

## Per-share bridge ($33.75 total)

| Component | $/share | How established |
| --- | --- | --- |
| Baseline EBIT-margin difference (14.18% Yahoo vs 13.13% SEC) | ~$18.41 | Local `evaluate` on the prod doc with only `ebit_margins` swapped |
| Baseline D&A-margin difference (4.15% Yahoo vs 3.45% SEC add-back) | ~$15.12 | Full SEC-derived assumption set on the prod doc: $33.53 total assumption-attributed |
| WACC/quote-time residual (5.7154% vs 5.7196%) | ~$0.22 | Remainder to the live staging value; both from same-day risk-free 5.236% |
| **Total** | **$33.75** | 196.95 − 163.20 |

WACC, revenue growth (5%), terminal growth (2%), tax, debt, shares (1.373B),
bridge items, revenue, net income, NWC and capex are identical or immaterial
between the two paths.

## Source evidence (FY2025, 10-K filed 2026-02-03, accession `0000077476-26-000007`)

| Field | Yahoo (`annualOperatingIncome` etc.) | SEC companyfacts (same accession) |
| --- | --- | --- |
| EBIT 2025 | 13,491M | `OperatingIncomeLoss` **11,498M** |
| EBIT 2024 | 12,920M | `OperatingIncomeLoss` **12,887M** |
| EBIT 2023 | 12,913M | `OperatingIncomeLoss` **11,986M** |
| D&A 2025 | 4,178M | `DepreciationDepletionAndAmortization` **3,451M** |
| Net income 2023/24/25 | 9,074 / 9,578 / 8,240M | identical (both sources agree) |
| Revenue 2025 | 93,925M | identical (both sources agree) |

Yahoo's higher EBIT with identical net income implies its non-operating
composition differs; the filed operating-income tag is authoritative, and the
staging packet carries it with REPORTED quality status plus archive receipts
(`sec/bulk/sec-nightly-20260924/companyfacts.zip`, member CRC `b9b1e1ab`).

## What was not changed

No Yahoo mapping was edited and no model constant was tuned: with Yahoo's
inputs the model correctly returns $196.95, and with filed inputs it correctly
returns $163.20. Forcing the two to agree would mean falsifying one source.
Production keeps reading authoritative `control/valuation/CURRENT.json`
(sha256 `ecf1e1c4…`, no PEP entry → Yahoo fallback); the staging PEP candidate
(`CANDIDATE-staging.json`, sha256 `a3be4251…`) stays staging-only.
