# PEP reconciliation, corrected: accounting definitions, not provider error

Supersedes the earlier version of this note, which overconfidently labeled the
SEC-first value accurate and the Yahoo value inflated. The filing supports a
more precise statement: **the two paths use different, individually defensible
accounting conventions, and neither DCF output is an objectively verifiable
price.** See [pep-three-bases.md](pep-three-bases.md) for the three valuations
on frozen inputs.

## What the FY2025 10-K actually says (accession `0000077476-26-000007`)

Income statement (USD M): net revenue 93,925; impairment of intangible assets
**1,993**; operating profit **11,498**; core non-GAAP operating profit 14,912.
Cash-flow statement: D&A **3,451**; operating-lease ROU amortization **727**.
Note 12: operating lease cost 880 (incl. the 727 ROU amortization).

## Source-to-source reconciliation (USD M)

| Field | FY2025 Yahoo | FY2025 filed GAAP | Relation |
| --- | --- | --- | --- |
| EBIT | 13,491 | operating profit 11,498 | 13,491 − 1,993 = 11,498 exactly: Yahoo excludes the separately-disclosed impairment line |
| D&A | 4,178 | cash-flow D&A 3,451 | 3,451 + 727 = 4,178 exactly: Yahoo folds operating-lease ROU amortization in |
| Net income | 8,240 | 8,240 | agree |
| Revenue | 93,925 | 93,925 | agree |

FY2023–FY2024 follow the same pattern (impairment line 927 / 33; ROU
amortization 570 / 655). Yahoo's EBIT is a pre-impairment operating measure;
Yahoo's D&A is a cash-flow D&A plus operating-lease amortization measure.

## Reported-GAAP vs normalized definitions

- **Reported-GAAP basis** (forecast default): EBIT = GAAP operating profit
  (impairment stays in), D&A = ordinary cash-flow D&A (no ROU add-back).
  Compatible with `UFCF = EBIT×(1−t) + D&A − CapEx − ΔNWC` and with a bridge
  that carries no lease liabilities.
- **Normalized basis** (explicit alternative): EBIT before qualifying,
  source-backed impairment add-backs. It assumes non-recurrence — but PEP
  reports impairments in all three loaded years (927 / 33 / 1,993), so the
  ledger flags normalization as aggressive. Tax applies at the period rate;
  the add-back's own shield is not separately modeled (disclosed).
- **Provider basis** (Yahoo as served): pre-impairment EBIT **and** ROU-loaded
  D&A. The EBIT leg resembles normalization; the D&A leg has no matching
  balance-sheet treatment (no lease liability in any bridge), so it is
  methodologically inconsistent as FCFF input even though each number traces
  to a real disclosure.

## Add-back audit (verified against OperatingIncomeLoss)

The provider EBIT is not just *assumed* to exclude the charges: it is tied out.
`accounting_policy` compares each period's EBIT with SEC `OperatingIncomeLoss`
(accession `0000077476-26-000007`), matching fiscal dates within seven days
because Yahoo normalizes to month ends.

| Period | Yahoo EBIT | SEC OperatingIncomeLoss | Disclosed charge | Verdict |
| --- | --- | --- | --- | --- |
| FY2023 | 12,913M | 11,986M | 927M | 11,986 + 927 = 12,913 → charges already excluded |
| FY2024 | 12,920M | 12,887M | 33M | equal sum → charges already excluded |
| FY2025 | 13,491M | 11,498M | 1,993M | equal sum → charges already excluded |

So the provider basis earns **no** impairment add-back (refused: $2,953M), while
the SEC-first basis earns the verified $2,953M add-back because its EBIT equals
filed operating income with the charges inside. Refusing the provider add-back
is what closes the 1.7× overstatement risk in the previous draft, which had
applied normalization logic to provider data by hand.

## Corrected conclusion

Yahoo's inputs are not fabrications — each reconciles exactly to a filed
number under a different convention, and the tie-out above proves which
convention rather than inferring it. The production $196.95 and the staging
$163.20 are both correct evaluations of their stated bases and neither is
the true price. What remains actionable is narrower: the provider basis pairs
a pre-impairment EBIT with an ROU-loaded D&A that has no matching balance-sheet
treatment, so it lands ~$15/share above the explicit normalized basis
(B $181.56 vs C $196.67 on frozen inputs). The Research Brief now labels that
snapshot `provider_defined` (never reported GAAP), refuses impairment
add-backs on it with the tie-out as evidence, and states that comparability
with filed GAAP is **unverified** unless a source-specific reconciliation is
attached. Production keeps the Yahoo fallback; no packet was rewritten.
