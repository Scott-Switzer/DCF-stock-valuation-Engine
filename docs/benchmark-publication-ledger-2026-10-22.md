# Benchmark publication ledger — 2026-10-22

Read-only status of every local Damodaran benchmark release. A release is usable for historical selection only when its hashed manifest carries both `published_at` and reviewed publication evidence.

| Release | Dataset | published_at | Evidence | Current mode | Historical mode |
| --- | --- | --- | --- | --- | --- |
| 5ce3d0a0f23f | margins | null | NO_PUBLICATION_DATE | 0.36242944995377313 (gross_margin) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| 69e27f1c09fb | industry_betas | null | NO_PUBLICATION_DATE | 1.210506967409714 (levered_beta) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| 6a7510cfc34c | cost_of_capital | null | NO_PUBLICATION_DATE | 0.09348861074647324 (cost_of_equity) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| 87b92aedda84 | implied_erp | null | NO_PUBLICATION_DATE | 0.0276 (treasury_rate) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| 899542d35d98 | multiples | null | NO_PUBLICATION_DATE | 11.998645075035455 (ev_ebitda_positive) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| a7a323992ca4 | reinvestment | null | NO_PUBLICATION_DATE | 705566999.9999999000000 (capital_expenditures) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |
| fba2da429a41 | country_risk | null | NO_PUBLICATION_DATE | 0.004195048511608233 (default_spread) | Benchmark vintage unavailable at historical cutoff: NO_PUBLICATION_DATE |

## What the ledger establishes

- All 7 releases refuse historical selection at 2000-01-01; the refusal names the missing publication evidence rather than a missing dataset.
- Current-mode selection succeeds for every release through the same verified loader.
- None of the existing manifests is edited: a publication date is never inferred from retrieval time, a workbook update label, or the release hash.

## Forward-only rule

New releases pass `--published-at` and `--publication-evidence` to the importer, which rejects a bare string, an observation before publication, and an observation after retrieval. Historical selection for those releases becomes available only from the recorded date onward.
