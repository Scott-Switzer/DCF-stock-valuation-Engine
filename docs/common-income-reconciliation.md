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

`scripts/reconcile_common_income.py` reads SEC companyfacts and reports, per
company-year, the observed tags, their accession numbers, forms and values, and a
verdict:

- `explained_by_*` — the residual between net income attributable to the parent and
  common basic income is fully explained by disclosed items in the same filing.
- `unexplained_residual` — a residual remains that the disclosed items do not cover.
  The observation is rejected and never published.
- `no_direct_tag` — the issuer does not report the common-basic tag for that period.
  The packet abstains and the existing baseline stays in force.

## Independent filing check

| Issuer | Fiscal year | Accession | Net income to parent | Preferred stock | Participating securities | Common basic (bridged) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JPM | FY2025 | 0001628280-26-008131 | 57,048 | 1,099 | 268 | 55,681 | explained |

57,048 − 1,099 − 268 = 55,681 (USD millions), matching the filing's EPS numerator
reconciliation.

## Reconciliation summary (committed SEC fixtures, 136 company-years)

| Issuer | Verdicts |
| --- | --- |
| AAPL, MSFT, KO, XOM | `no_direct_tag` (abstain; the common-basic tag is absent for these periods) |
| JPM | 15 explained (preferred + participating securities); 2 `unexplained_residual` (FY2009, FY2010) — rejected |
| BAC | 17 explained (preferred dividends / cash / adjustments) |
| GS | 16 explained (preferred dividends); 1 `unexplained_residual` (FY2009) — rejected |
| C | 1 `no_direct_tag`; 16 `unexplained_residual` — all rejected |

## Known limitations

- Citigroup residuals are not explained by the disclosed preferred, NCI and
  participating items in the fixtures. Citigroup is therefore not published for
  common income; the field abstains.
- Pre-2011 JPM periods are rejected: their disclosures do not bridge.
- Coverage is limited to issuers and years present in the committed fixtures. Other
  issuers have not been verified against filings.
