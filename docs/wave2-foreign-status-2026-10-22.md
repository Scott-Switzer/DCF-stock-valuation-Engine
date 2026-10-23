# Wave-2 foreign-status classification — 2026-10-22

Read-only classification of the wave-2 candidates by annual-report form family, from SEC submissions. ADR status remains unknown: a foreign private issuer can be an ADR or a direct listing, and submissions alone cannot tell them apart.

| Foreign status | Listings | Engine taxonomy |
| --- | --- | --- |
| DOMESTIC_10K | 2429 | US_GAAP_COMPATIBLE |
| FOREIGN_PRIVATE_ISSUER_20F | 740 | IFRS_NOT_COVERED |
| NO_ANNUAL_FORM_IN_WINDOW | 280 | UNKNOWN_NO_ANNUAL_REPORT |
| INVESTMENT_COMPANY_NCSR | 184 | INVESTMENT_COMPANY_NOT_MODELLED |
| MIXED_ANNUAL_FORMS | 91 | REVIEW_MIXED_TAXONOMY |
| FOREIGN_PRIVATE_ISSUER_40F | 74 | IFRS_NOT_COVERED |
| FOREIGN_PRIVATE_ISSUER_MIXED | 30 | IFRS_NOT_COVERED |

3665 issuers / 3828 listings classified; 0 could not be read.

## What this changes for the wave

- 2429 listings file 10-K statements and are taxonomy-compatible with the current engine.
- 844 listings file 20-F/40-F statements under IFRS; ingesting them would produce no us-gaap facts, so they need a separate pipeline or exclusion.
- 184 listings are registered investment companies filing N-CSR reports; the engine models no fund schedule, so they are out of scope.
- 91 listings show both families and need review before either branch is trusted.
- 280 listings have no annual report in the window. The sample starts with AAC, AACP, AADX, ACAA, ACCV; these are mostly recently listed SPACs and new registrants that should re-enter the wave after their first annual report.
- ADR status is still `UNKNOWN_NOT_IN_CONTRACTS` for every row; this classification does not fill that column and must not be used as if it did.

## Method and limits

- Annual forms are counted in the newest 4,000 filings plus at most two older archive pages.
- A listing is classified by its issuer CIK; two listings of one issuer share the result.
- No exchange or ticker syntax is used to infer foreign status.
- Each issuer row in the JSON carries the URL and sha256 of the submissions objects read.
- No proposal row, release, packet, or pointer was modified.
