# Common-income reconciliation evidence

`common_income` is the earnings numerator attributable to common shareholders. The
packet publisher maps it from `NetIncomeLossAvailableToCommonStockholdersBasic`
only when the value can be bridged to the filing's own net income attributable to
the parent, using disclosed preferred stock/dividends, participating securities and
other adjustments from the same 10-K. A standardized tag is never accepted on its
own.

Basic and diluted numerators are kept separate. `common_diluted` is only used as
evidence and is never substituted for the basic numerator.

## Method

`scripts/reconcile_common_income.py` reads SEC companyfacts (using the configured
`EDGAR_IDENTITY` User-Agent and rejecting placeholder addresses) and reports, per
company-year, the observed tags, their accession numbers, forms and values, and a
verdict:

- `explained_by_*` — the residual between net income attributable to the parent and
  common basic income is fully explained by disclosed items in the same filing across
  mutually exclusive economic categories (preferred dividends, participating securities,
  and preferred redemption premium). Synonymous tags within the same category are never
  summed together.
- `unexplained_residual` — a residual remains that the disclosed items do not cover.
  The observation is rejected and never published.
- `no_direct_tag` — the issuer does not report the common-basic tag for that period.
  The packet abstains and the existing baseline stays in force.

## Independent filing check

| Issuer | Fiscal year | Accession | Net income to parent | Preferred stock | Participating securities | Redemption premium | Common basic (bridged) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JPM | FY2025 | 0001628280-26-008131 | 57,048 | 1,099 | 268 | 0 | 55,681 | explained |
| JPM | FY2010 (in FY2011 10-K) | 0000019617-12-000163 | 17,370 | 642 | 964 | 0 | 15,764 | explained |
| JPM | FY2009 (in FY2011 10-K) | 0000019617-12-000163 | 11,728 | 1,327 | 515 | 1,112 | 8,774 | explained |

57,048 − 1,099 − 268 = 55,681 (USD millions), matching the FY2025 filing's EPS numerator
reconciliation.

## Reconciliation summary (committed SEC fixtures, 136 original-10-K company-years)

| Issuer | Verdicts |
| --- | --- |
| AAPL, MSFT, KO, XOM | `no_direct_tag` (abstain; companyfacts has no `NetIncomeLossAvailableToCommonStockholdersBasic` rows for these issuers in any period) |
| JPM | 15 explained in original 10-K (preferred + participating securities); 2 `unexplained_residual` in original 10-K (FY2009, FY2010) that reconcile in later comparative 10-K accessions (`0000019617-12-000163`, `0000019617-13-000221`) |
| BAC | 17 explained (preferred dividends / cash / adjustments) |
| GS | 16 explained in original 10-K (preferred dividends); 1 `unexplained_residual` in original 10-K (FY2009) that reconciles in comparative accession `0001193125-12-085822` |
| C | 1 `no_direct_tag`; 16 `unexplained_residual` — all rejected |

## Known limitations

- Citigroup residuals are not explained by the disclosed preferred, NCI and
  participating items in the fixtures (its participating-security allocation is
  disclosed in the EPS footnote table without a standardized US-GAAP companyfacts tag).
  Citigroup is therefore not published for common income; the field abstains.
- Pre-2011 JPM original-10-K rows (FY2009 accession `0000950123-10-016029` and FY2010
  accession `0000950123-11-019773`) are rejected by the tag-only gate when evaluated
  strictly at their original filing date. Their 10-K text does bridge: FY2010 is
  17,370 − 642 (preferred) − 964 (participating securities) = 15,764, and FY2009 is
  11,728 − 1,327 (preferred) − 1,112 (redemption premium) − 515 (participating
  securities) = 8,774. The original XBRL submissions omitted the `ParticipatingSecurities*`
  fact tags, so at an early cutoff date the gate fails closed. In subsequent 10-K
  comparatives (accession `0000019617-12-000163`), all three components (`DividendsPreferredStock`,
  `PreferredStockRedemptionPremium`, and `ParticipatingSecuritiesDistributedAndUndistributedEarnings`)
  are tagged in the same filing and bridge exactly.
- Coverage is limited to issuers and years present in the committed fixtures. Other
  issuers have not been verified against filings.
