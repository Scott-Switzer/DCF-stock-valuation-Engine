# Identity receipts for the named listings — 2026-10-22

Read-only SEC resolution of the 14 named listings in `docs/universe-expansion-2026-10-22.csv`. No ingestion, no release change.

Sources: SEC `company_tickers_exchange.json` and per-issuer submissions JSON, read on 2026-10-22. Every source object's sha256 is in the JSON receipt.

| Ticker | CIK | Issuer | Exchange | Sibling listings | Statement family | Latest annual report | Share class (cover page) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADBE | 0000796343 | ADOBE INC. | Nasdaq | — | DOMESTIC_10K | 10-K 2026-01-15 (2025-11-28) | Common Stock, $0.0001 par value per share |
| AMZN | 0001018724 | AMAZON COM INC | Nasdaq | — | DOMESTIC_10K | 10-K 2026-02-06 (2025-12-31) | Common Stock, par value $.01 per share |
| BRK-A | 0001067983 | BERKSHIRE HATHAWAY INC | NYSE | BRK-B | DOMESTIC_10K | 10-K 2026-03-02 (2025-12-31) | Class A Common Stock |
| BRK-B | 0001067983 | BERKSHIRE HATHAWAY INC | NYSE | BRK-A | DOMESTIC_10K | 10-K 2026-03-02 (2025-12-31) | Class B Common Stock |
| COST | 0000909832 | COSTCO WHOLESALE CORP /NEW | Nasdaq | — | DOMESTIC_10K | 10-K 2026-10-07 (2026-08-30) | Common Stock, $.005 Par Value |
| GOOG | 0001652044 | Alphabet Inc. | Nasdaq | GOOGL, GOOGM, GOOGN | DOMESTIC_10K | 10-K 2026-02-05 (2025-12-31) | Class C Capital Stock, $0.001 par value |
| GOOGL | 0001652044 | Alphabet Inc. | Nasdaq | GOOG, GOOGM, GOOGN | DOMESTIC_10K | 10-K 2026-02-05 (2025-12-31) | Class A Common Stock, $0.001 par value |
| IBM | 0000051143 | INTERNATIONAL BUSINESS MACHINES CORP | NYSE | — | DOMESTIC_10K | 10-K 2026-02-24 (2025-12-31) | Capital stock, par value $.20 per share |
| META | 0001326801 | Meta Platforms, Inc. | Nasdaq | — | DOMESTIC_10K | 10-K 2026-01-29 (2025-12-31) | Class A Common Stock, $0.000006 par value |
| MO | 0000764180 | ALTRIA GROUP, INC. | NYSE | — | DOMESTIC_10K | 10-K 2026-02-25 (2025-12-31) | Common Stock, $0.33 1/3 par value |
| ORCL | 0001341439 | ORACLE CORP | NYSE | ORCL-PD | DOMESTIC_10K | 10-K 2026-06-22 (2026-05-31) | Common Stock, par value $0.01 per share |
| TSLA | 0001318605 | Tesla, Inc. | Nasdaq | — | DOMESTIC_10K | 10-K 2026-01-29 (2025-12-31) | Common stock |
| V | 0001403161 | VISA INC. | NYSE | — | DOMESTIC_10K | 10-K 2025-11-06 (2025-09-30) | Class A Common Stock, par value $0.0001 per share |
| XOM | 0002115436 | ExxonMobil Holdings Corp | NYSE | — | NO_ANNUAL_REPORT_FOUND | 10-K 2026-02-18 (2025-12-31) via predecessor | Common Stock, without par value |

## Issuer grouping

- **0000051143 INTERNATIONAL BUSINESS MACHINES CORP** — listings IBM; former names: none; family DOMESTIC_10K; succession none.
- **0000764180 ALTRIA GROUP, INC.** — listings MO; former names: ALTRIA GROUP INC, PHILIP MORRIS COMPANIES INC; family DOMESTIC_10K; succession none.
- **0000796343 ADOBE INC.** — listings ADBE; former names: ADOBE SYSTEMS INC; family DOMESTIC_10K; succession none.
- **0000909832 COSTCO WHOLESALE CORP /NEW** — listings COST; former names: COSTCO COMPANIES INC, PRICE/COSTCO INC; family DOMESTIC_10K; succession none.
- **0001018724 AMAZON COM INC** — listings AMZN; former names: none; family DOMESTIC_10K; succession none.
- **0001067983 BERKSHIRE HATHAWAY INC** — listings BRK-A, BRK-B; former names: NBH INC; family DOMESTIC_10K; succession none.
- **0001318605 Tesla, Inc.** — listings TSLA; former names: TESLA MOTORS INC; family DOMESTIC_10K; succession none.
- **0001326801 Meta Platforms, Inc.** — listings META; former names: Facebook Inc; family DOMESTIC_10K; succession none.
- **0001341439 ORACLE CORP** — listings ORCL; former names: Ozark Holding Inc.; family DOMESTIC_10K; succession none.
- **0001403161 VISA INC.** — listings V; former names: none; family DOMESTIC_10K; succession none.
- **0001652044 Alphabet Inc.** — listings GOOG, GOOGL; former names: none; family DOMESTIC_10K; succession none.
- **0002115436 ExxonMobil Holdings Corp** — listings XOM; former names: none; family NO_ANNUAL_REPORT_FOUND; succession VERIFIED.

## Entity transitions

- **XOM** files under CIK 0002115436 (ExxonMobil Holdings Corp). Form 8-K12B 0001193125-26-291990 (filed 2026-07-01) establishes CIK 0000034088 as the predecessor registrant. The successor has no annual report of its own; the latest annual report belonging to this ticker is 10-K 2026-02-18 for period 2025-12-31, filed by the predecessor. Excerpt: "eck mark if the registrant has elected not to use the extended transition period for complying with any new or revised financial accounting standards provided pursuant to Section 13(a) of the Exchange Act. ☐ Explanatory Note On July 1, 2026, Exxon Mobil Corporation, a New Jersey corporation and the predecessor registrant (“ ExxonMobil ”), completed its previously announced redomiciliation reorganization (the “ Redomiciliation Merger ”) pursuant to the Agreement and Plan of Merger, dated as of April 8, 2026 (the “ Merger Agreement ”), by and among ExxonMobil, ExxonMobil Holdings Corporation, a Texas corporation, and Ensign LLC, a Texas limited liability company. This Current Report on Form 8-K is being filed for the purpose of establishing ExxonMobil Holdings Corporation as the successor registrant of ExxonMobil’s common stock pursuant to Rule 12g-3(a) under the Securities Exchange Act of 1934, as amended (the “ Exchange Act ”) and to disclose certain related matters. The Redomiciliation Merger became effective on July 1, 2026 in accordance with the terms of the Merger Agreement (the “ Effective Time ”). The foregoing description of the Merger Agreement is not complete and is qualified in its entirety by reference to the Merger Agreement, a copy of which was filed as Annex A to the proxy statement included in ExxonMobil’s definitive proxy statement on Schedule 14A filed with the Commission on April 8, 2026. Item 1.01 Entry Into a Material Definitive Agreement. Upon the consummation of the Redomiciliation Merger and pursuant to the terms of the indenture, dated as of March 20"

## Limits carried by these receipts

- Receipts read SEC's public ticker file and submissions API only; no packet was built and no release changed.
- Statement family is classified from annual-report form type (10-K domestic, 20-F/40-F foreign private issuer), not from company name or exchange.
- Share class is taken from the latest annual report cover page; a class the cover page does not state stays unresolved rather than being guessed from ticker syntax.
- ADR trading venue, free float and liquidity are not established by these receipts.
- Submissions history is read newest-first with a bounded window of 2,500 filings plus at most three archive pages; an annual report older than that window would read as absent.
- A CIK appearing here is an identity claim by SEC's own index, not an endorsement of data quality or filing completeness.
