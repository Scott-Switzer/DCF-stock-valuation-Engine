# PEP three-basis valuation (frozen inputs, 2026-10-14)

Frozen: price $128.55 (Midpoint of same-day Yahoo quotes 128.495 / 128.60; held fixed to isolate statement-definition effects.)
shares 1,373,000,000; WACC 0.0572 (Held fixed (rounding of both live WACCs) to isolate accounting effects; live WACCs differ by 0.4bp from quote timing.)
growth 5%, terminal 2%, 5-year horizon. None of these is a true price:
each is the model output of a stated accounting convention.

| Basis | EBIT convention | D&A convention | Intrinsic | 12m target |
| --- | --- | --- | --- | --- |
| A reported-GAAP | GAAP operating profit | ordinary cash-flow D&A | $163.18 | $167.47 |
| B normalized | pre-impairment (add-back, flagged) | ordinary cash-flow D&A | $181.56 | $186.29 |
| C provider | Yahoo ex-impairment OperatingIncome | Yahoo incl. operating-lease ROU amortization | $196.67 | $201.76 |

A→B normalization effect: $+18.38/share.
A→C provider-convention effect: $+33.49/share.

## Historical inputs (USD)

### A_reported_gaap
- 2023-12-30: revenue $91,471,000,000, EBIT $11,986,000,000, net $9,074,000,000, D&A $2,948,000,000, capex $5,518,000,000
- 2024-12-28: revenue $91,854,000,000, EBIT $12,887,000,000, net $9,578,000,000, D&A $3,160,000,000, capex $5,318,000,000
- 2025-12-27: revenue $93,925,000,000, EBIT $11,498,000,000, net $8,240,000,000, D&A $3,451,000,000, capex $4,415,000,000
### B_normalized_operating
- 2023-12-30: revenue $91,471,000,000, EBIT $12,913,000,000, net $9,074,000,000, D&A $2,948,000,000, capex $5,518,000,000
- 2024-12-28: revenue $91,854,000,000, EBIT $12,920,000,000, net $9,578,000,000, D&A $3,160,000,000, capex $5,318,000,000
- 2025-12-27: revenue $93,925,000,000, EBIT $13,491,000,000, net $8,240,000,000, D&A $3,451,000,000, capex $4,415,000,000
### C_provider_yahoo
- 2023-12-31: revenue $91,471,000,000, EBIT $12,913,000,000, net $9,074,000,000, D&A $3,518,000,000, capex $5,518,000,000
- 2024-12-31: revenue $91,854,000,000, EBIT $12,920,000,000, net $9,578,000,000, D&A $3,815,000,000, capex $5,318,000,000
- 2025-12-31: revenue $93,925,000,000, EBIT $13,491,000,000, net $8,240,000,000, D&A $4,178,000,000, capex $4,415,000,000

## Adjustment ledger (B only)

- 2023-12-30: +$927,000,000 impairment add-back (ImpairmentOfIntangibleAssetsExcludingGoodwill 0000077476-26-000007)
- 2024-12-28: +$33,000,000 impairment add-back (ImpairmentOfIntangibleAssetsExcludingGoodwill 0000077476-26-000007, GoodwillImpairmentLoss 0000077476-26-000007)
- 2025-12-27: +$1,993,000,000 impairment add-back (ImpairmentOfIntangibleAssetsExcludingGoodwill 0000077476-26-000007, GoodwillImpairmentLoss 0000077476-26-000007)

Separately-disclosed impairments appear in 3 of 3 loaded periods; normalizing assumes they do not recur, which consecutive-year impairments contradict. Review the filing Notes before relying on a normalized basis.

The forecast applies the period tax rate to adjusted EBIT; the tax shield on the add-back itself is not separately modeled.
