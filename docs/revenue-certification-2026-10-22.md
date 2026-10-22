# Bank and insurer revenue certification worksheet — 2026-10-22

Read-only evidence for the R2 decision. No policy, release or dataset changed; revenue stays quarantined for these issuers until an accounting owner signs the mapping.

Source: SEC XBRL `companyfacts` per issuer, 10-K annual facts only. Each issuer's source sha256 is in the JSON worksheet.

## GE — GENERAL ELECTRIC COMPANY (CIK 0000040545)

Proposed family: **GENERAL_TOTAL_REVENUE** — primary `Revenues`. Status: **PROPOSED_NOT_CERTIFIED**.

| Period end | Revenues | RevenuesNetOfInterestExpense | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet |
| --- | --- | --- | --- | --- |
| 2023-12-31 | 35348000000 | — | — | — |
| 2024-12-31 | 38702000000 | — | — | — |
| 2025-12-31 | 45855000000 | — | — | — |

Latest 2025-12-31 Revenues value: 45855000000 (as filed).

Conflicts in the source facts:
- same period end 2023-12-31 has 2 distinct values: 67954000000 filed 2024-02-02 (10-K 0000040545-24-000027); 35348000000 filed 2025-02-03 (10-K 0000040545-25-000015); 35348000000 filed 2026-01-29 (10-K 0000040545-26-000008)

Evidence tags by period:
- `PremiumsEarnedNet` — not present in the 10-K window.
- `InterestAndDividendIncomeOperating` — not present in the 10-K window.
- `PolicyholderBenefitsAndClaimsIncurredNet` — not present in the 10-K window.
- `LoansAndLeasesReceivableNetReportedAmount` — not present in the 10-K window.

Open questions:
- Two filings report different values for the same fiscal period (restatement or reclassification); confirm which value is the income-statement total as presented, and whether the engine should use the latest filing.
- No insurance or lending tag appears in the latest 10-K fact set; the blanket quarantine may be stale for this issuer.


Sign-off needed: Accounting owner must confirm that Revenues is the total revenue line the issuer's income statement presents for 2025-12-31, and whether any component tag remains a component only.

## ALL — ALLSTATE CORP (CIK 0000899051)

Proposed family: **INSURER_TOTAL_REVENUE** — primary `Revenues`, component `PremiumsEarnedNet`. Status: **PROPOSED_NOT_CERTIFIED**.

| Period end | Revenues | RevenuesNetOfInterestExpense | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet |
| --- | --- | --- | --- | --- |
| 2023-12-31 | 57094000000 | — | — | — |
| 2024-12-31 | 64106000000 | — | — | — |
| 2025-12-31 | 67685000000 | — | — | — |

Latest 2025-12-31 Revenues value: 67685000000 (as filed).

Evidence tags by period:
- `PremiumsEarnedNet` — periods 2023-12-31, 2024-12-31, 2025-12-31; latest 2025-12-31 (accession 0000899051-26-000031, filed 2026-02-20).
- `InterestAndDividendIncomeOperating` — periods 2023-12-31, 2024-12-31, 2025-12-31; latest 2025-12-31 (accession 0000899051-26-000031, filed 2026-02-20).
- `PolicyholderBenefitsAndClaimsIncurredNet` — not present in the 10-K window.
- `LoansAndLeasesReceivableNetReportedAmount` — not present in the 10-K window.


Sign-off needed: Accounting owner must confirm that Revenues is the total revenue line the issuer's income statement presents for 2025-12-31, and whether PremiumsEarnedNet remains a component only.

## C — Citigroup Inc (CIK 0000831001)

Proposed family: **BANK_TOTAL_REVENUE** — primary `Revenues`, component `InterestAndDividendIncomeOperating`. Status: **PROPOSED_NOT_CERTIFIED**.

| Period end | Revenues | RevenuesNetOfInterestExpense | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet |
| --- | --- | --- | --- | --- |
| 2023-12-31 | 78066000000 | — | — | — |
| 2024-12-31 | 80722000000 | — | — | — |
| 2025-12-31 | 85225000000 | — | — | — |

Latest 2025-12-31 Revenues value: 85225000000 (as filed).

Conflicts in the source facts:
- same period end 2023-12-31 has 2 distinct values: 78462000000 filed 2024-02-23 (10-K 0000831001-24-000033); 78462000000 filed 2025-02-21 (10-K 0000831001-25-000067); 78066000000 filed 2026-02-20 (10-K 0000831001-26-000011)
- same period end 2024-12-31 has 2 distinct values: 81139000000 filed 2025-02-21 (10-K 0000831001-25-000067); 80722000000 filed 2026-02-20 (10-K 0000831001-26-000011)

Evidence tags by period:
- `PremiumsEarnedNet` — periods 2016-12-31; latest 2016-12-31 (accession 0000831001-17-000038, filed 2017-02-24).
- `InterestAndDividendIncomeOperating` — periods 2023-12-31, 2024-12-31, 2025-12-31; latest 2025-12-31 (accession 0000831001-26-000011, filed 2026-02-20).
- `PolicyholderBenefitsAndClaimsIncurredNet` — periods 2023-12-31, 2024-12-31, 2025-12-31; latest 2025-12-31 (accession 0000831001-26-000011, filed 2026-02-20).
- `LoansAndLeasesReceivableNetReportedAmount` — not present in the 10-K window.

Open questions:
- Two filings report different values for the same fiscal period (restatement or reclassification); confirm which value is the income-statement total as presented, and whether the engine should use the latest filing.


Sign-off needed: Accounting owner must confirm that Revenues is the total revenue line the issuer's income statement presents for 2025-12-31, and whether InterestAndDividendIncomeOperating remains a component only.

## GS — The Goldman Sachs Group, Inc. (CIK 0000886982)

Proposed family: **BANK_NET_REVENUE** — primary `RevenuesNetOfInterestExpense`, component `InterestAndDividendIncomeOperating`. Status: **PROPOSED_NOT_CERTIFIED**.

| Period end | Revenues | RevenuesNetOfInterestExpense | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet |
| --- | --- | --- | --- | --- |
| 2023-12-31 | — | 46254000000 | — | — |
| 2024-12-31 | — | 53512000000 | — | — |
| 2025-12-31 | — | 58283000000 | — | — |

Latest 2025-12-31 RevenuesNetOfInterestExpense value: 58283000000 (as filed).

Evidence tags by period:
- `PremiumsEarnedNet` — not present in the 10-K window.
- `InterestAndDividendIncomeOperating` — periods 2023-12-31, 2024-12-31, 2025-12-31; latest 2025-12-31 (accession 0000886982-26-000091, filed 2026-02-25).
- `PolicyholderBenefitsAndClaimsIncurredNet` — not present in the 10-K window.
- `LoansAndLeasesReceivableNetReportedAmount` — not present in the 10-K window.


Sign-off needed: Accounting owner must confirm that RevenuesNetOfInterestExpense is the total revenue line the issuer's income statement presents for 2025-12-31, and whether InterestAndDividendIncomeOperating remains a component only.

## JPM — JPMORGAN CHASE & CO (CIK 0000019617)

Proposed family: **BANK_NET_REVENUE** — primary `RevenuesNetOfInterestExpense`, component `InterestAndDividendIncomeOperating`. Status: **PROPOSED_NOT_CERTIFIED**.

| Period end | Revenues | RevenuesNetOfInterestExpense | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet |
| --- | --- | --- | --- | --- |
| 2023-12-31 | 158104000000 | 158104000000 | — | — |
| 2024-12-31 | 177556000000 | 177556000000 | — | — |
| 2025-12-31 | 182447000000 | 182447000000 | — | — |

Latest 2025-12-31 RevenuesNetOfInterestExpense value: 182447000000 (as filed).

Evidence tags by period:
- `PremiumsEarnedNet` — not present in the 10-K window.
- `InterestAndDividendIncomeOperating` — not present in the 10-K window.
- `PolicyholderBenefitsAndClaimsIncurredNet` — not present in the 10-K window.
- `LoansAndLeasesReceivableNetReportedAmount` — not present in the 10-K window.

Open questions:
- Several revenue concepts carry a value for 2025-12-31; confirm which is the income-statement total.
- No insurance or lending tag appears in the latest 10-K fact set; the blanket quarantine may be stale for this issuer.


Sign-off needed: Accounting owner must confirm that RevenuesNetOfInterestExpense is the total revenue line the issuer's income statement presents for 2025-12-31, and whether InterestAndDividendIncomeOperating remains a component only.

## Limits

- Only 10-K annual facts with a 330-400 day duration are read; quarterly and TTM figures are out of scope.
- A tag whose only facts are quarterly or older than the ten-year window reads as absent here, even when the engine's taxonomy scan still sees it.
- A concept value here is what the filing reported, not a restated or normalised figure.
- The proposed mapping is mechanical and uncertified; it does not change the engine's quarantine.
- Historical insurance or lending tags are evidence pointers, not proof that the issuer's present statement family is financial.
- No packet, release, source pointer, or deployed bundle was modified.
