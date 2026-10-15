# SEC-first batch expansion: coverage report

Machine-readable matrix: [matrix.json](matrix.json) (86 companies, every failure recorded).

## Before / after

- Screened with the real builder + gate: **86** public operating companies
  (38 batch 1 across tech/industrials/staples/healthcare/communications/energy/
  utilities + 48 batch 2 with deeper industrials/staples/healthcare/energy coverage).
- Packet builds (READY): **52 of 86** (was 26 of 38 at baseline).
- Gate-eligible: **CAT, PEP (pilot) + T, ORCL (new)**.
- Staging candidate index: `CAT, PEP` → `CAT, ORCL, PEP, T`; production pointer
  byte-identical before/after (`ecf1e1c4…`, raw-SHA-256 proof in
  `find/outputs/company-packets/t-orcl-candidate-publish.json`).

## New reusable mappings (all generic, filing-identity disciplined)

1. Common-equity buildup variants: generic `AdditionalPaidInCapital` APIC leg and
   `TreasuryStockCommonValue` treasury leg (AEP/Paychex/EOG patterns).
2. Long-term-debt total/current pairs: `(LongTermDebt, LongTermDebtCurrent)`,
   capital-lease-obligations pair, and the mixed Honeywell/AbbVie pair — this
   unlocked **T**; same-accession difference, never zero.
3. D&A as `Depreciation + AmortizationOfIntangibleAssets` from one accession
   (Microsoft/Broadcom/Intuit/Abbott pattern; partial sums refused).
4. Pretax as domestic + foreign continuing income from one accession (Oracle) —
   this unlocked **ORCL**, with `LongTermNotesPayable` as an LTD variant.
5. Explicit `EarningsBeforeInterestAndTaxes`, base
   `IncomeLossFromContinuingOperationsBeforeIncomeTaxes`, `InterestCostsIncurred`,
   oil-and-gas capex, and lowest-priority utility revenue
   (`RegulatedAndUnregulatedOperatingRevenue`).
6. Benchmark harness: HIT/MISS is now classified from the server's own
   `assembly_cache.state` per request (`classify_cache`), with summaries grouped
   by evidence class — attempt order is never a substitute
   (`tests/test_bench_warm.py`).

Near-miss movement: MSFT 10→7, AVGO 11→8, INTU 11→8, IBM 11→8, ABBV 6→2,
ABT 11→8 gate reasons.

## Newly onboarded in staging (candidate-only, production untouched)

- **T** (`8ca66fae…`, 41,519 bytes, 2023/2024/2025-12-31, 3 common-income periods
  `explained_by_preferred_and_adjustments`, preferred 0.0 via buildup residual):
  staging `/api/load/dcf` returns **SEC-first**, verified live.
- **ORCL** (`91a9787e…`, 41,891 bytes, 2024/2025/2026-05-31, 3 common-income
  periods, preferred 4954M filed tag, tax 0.108/0.121/0.126): packet validates and
  passes the gate. Staging load returns the honest pre-existing limitation
  `Nonzero preferred equity requires an explicit preferred cost assumption`
  (same as `docs/sec-coverage-report.md`): the packet is truthful, the DCF lane
  cannot price nonzero preferred with default assumptions.

## Most commonly missing (READY but ineligible, 48 companies)

1. `missing_common_income` (100): giants without the direct basic-available tag
   (KO/AAPL/ADBE/CSCO/WMT/NVDA/HON/LECO/LIN/UPS/TSN…). Policy requires the direct
   tag; parent income never substitutes.
2. `missing_nwc` (66) via `missing_bridge_short_term_debt` (16): filers with no
   current-debt tags at all (CL, LOW, EOG…); absence is never zero.
3. `incomplete_provenance_ebit` + `missing_ebit` (62): energy majors (COP/CVX)
   disclose no operating-income tag; bank rows lack filing provenance.
4. `missing_bridge_minority_interest` (24) / `preferred_equity` (21): no NCI or
   equity-buildup legs filed (MSFT has no treasury/NCI tags; PAYX has no treasury
   or NCI tags; ABBV lacks the par-value leg).
5. `tax_rate_out_of_bounds` (7): real economics the gate refuses — ABBV 2024
   benefit-driven −0.15, AEP 2024 credit-driven −0.01, BA/AVGO/IBM/ABT loss years.
   Relaxing the bound is out of scope.
6. `missing_capex` (18): e.g. CI; `missing_bridge_cash` (8): PG stopped filing
   the plain cash tag in 2019 (restricted-inclusive total only).

## Explicitly excluded financial firms

JPM, BAC (16 gate reasons each; banks are not industrial-FCFF candidates —
see `docs/sec-coverage-report.md`). No bank mappings were faked.

## Remaining accounting issues / next-batch evidence

- Upstream lake gap: DUK's canonical revenue ends at 2016 (the lake producer
  lacks the utility revenue tag), so packet periods stay stale despite the new
  packet-level fallback. Evidence: lake must map
  `RegulatedAndUnregulatedOperatingRevenue`.
- Model gap (not packet): explicit `preferred_cost` assumption support to make
  ORCL-class issuers loadable end-to-end.
- Gate walls (by design): negative/credit-driven tax rates, missing par-value
  legs (ABBV), untagged short-term debt, absent direct common tags.
- 31 tickers not in the resolver index and 3 build-unavailable are recorded in
  the matrix with reasons — none silently discarded.

## Batch 2: PAYX unlocked, ORCL modeled and held blocked

Functional SEC-first issuers: **3 → 4** (CAT, PEP, T + **PAYX**).

### PAYX (Paychex): dual-identity zero-claim derivation (corrected)

New reusable `_sec_zero_claims_from_dual_identity` (`ppe_packets.py`): preferred
and NCI are established at zero **atomically** only when, in one 10-K
accession for one annual period, (1) SE minus built-up parent-common equity
is $0 with treasury proven zero — filed tag, or issued-equals-outstanding
filed share counts (PAYX FY2026: 355.6M = 355.6M) — which proves preferred
zero only (`StockholdersEquity` excludes NCI by definition); (2) filed
**consolidated `ProfitLoss` equals filed parent `NetIncomeLoss`** (affirmative
NCI evidence: equal values mean zero NCI income), with the filed direct
common basic tag equal to parent (no preferred distribution); and (3) a
member-wide scan finds no preferred/NCI tag at all. Taxonomy is strict
throughout: `NetIncomeLoss` is parent-attributable income, never labeled
consolidated; parent-minus-direct equality alone cannot prove zero NCI. A
lone zero residual never suffices (offsetting components could mimic it),
tag absence alone never proves zero (a missing consolidated leg leaves NCI
unavailable and blocks eligibility), and every leg — including the parent
income leg — must share the accession and the annual start date.
Negative counterexamples in `tests/test_ppe_packets.py`: ORCL (filed preferred),
T (filed NCI), ABBV (missing par leg), nonzero residuals, treasury shares
outstanding, split accessions (equity, parent, consolidated, or direct leg),
parent-equals-direct despite nonzero NCI (`ProfitLoss` above parent), missing
`ProfitLoss`, and mismatched annual periods.

Correction history (2026-10-15): the first version compared parent
`NetIncomeLoss` to the direct tag and called that a consolidated identity —
a conceptual error, since parent-minus-direct equality is consistent with
nonzero NCI. The corrected rule adds the `ProfitLoss`-vs-`NetIncomeLoss`
reconciliation, same-accession/start enforcement on all three income legs,
and separated preferred/NCI evidence. Re-verified against live SEC facts:
PAYX FY2026 (accession `0001193125-26-307785`) still establishes 0.0/0.0 —
SE 3735.1M = 3.6 + 1975.6 + 1805.8 − 49.9 exactly, consolidated 1760.1M =
parent 1760.1M = common basic 1760.1M, all starts 2025-06-01, 19-claim-tag
scan clean — while a prior-period end with equity legs from a different
accession than the income legs is correctly refused. ORCL stays blocked.
Because the supported accounting inputs are unchanged (0.0/0.0), the
$86.69 intrinsic value is **not** recomputed.
Client-funds review: bridge cash 1088.2M is the plain corporate-cash tag and
excludes the separately-tagged 4832.2M funds held for clients (no
separately-tagged client obligation exists in companyfacts; the filed
`LiabilitiesCurrent` 6840.6M carries it per the 10-K balance sheet); NWC uses
filed legs on both sides — (8613.3 − 1088.2) − (6840.6 − 0) = 684.5M — so the
client balances offset symmetrically and never become distributable cash
(regression test `test_client_funds_never_become_distributable_cash`).
Published `cff0e309…` (45,906 bytes) via the candidate-only workflow;
production pointer byte-identical. Staging `/api/load/dcf`: **SEC-first, DCF
intrinsic 86.69, target 89.32, WACC 8.74%**; parity holds (staging net_income
equals the direct common tags; bridge identical to the dollar).

Note: the republished PAYX packet (`3b1577c8…`, 46,406 bytes, candidate-only;
production pointer still byte-identical `ecf1e1c4…`) carries corrected
provenance wording under the same accounting values — bridge, common income
(1690.4/1657.3/1760.1M), historical NWC (492.2/750.0/684.5M) and shares all
verified byte-identical old-vs-new. Live staging re-verification 2026-10-15:
**SEC-first, intrinsic 88.11, target 90.77, WACC 8.64%** at live price 111.88
(vs 86.69/89.32/8.74% earlier — the move is live market inputs repricing
market-cap weights, not accounting: no accounting input changed, so no
accounting recompute was warranted). Staging net_income equals the direct
common tags; bridge identical to the dollar.

### ORCL: mandatory convertible preferred stays blocked (correctly)

Verified against the FY2026 10-K (accession `0001193125-26-277521`): the packet
carries the genuine $4.954B Series D 6.50% mandatory convertible preferred
(filed `PreferredStockValue`), FY2026 common income $16.984B
(`explained_by_preferred_dividends` over consolidated $17.087B less $103M
preferred dividends), and pre-conversion diluted shares 2914M. The apply path
was verified locally: the model sees the direct common observations, never the
consolidated total. The block is purely capital-cost pricing: mandatory
conversion (~25–31M shares, Jan 2029, price-dependent) plus interim dividends
cannot be represented by a flat preferred cost, and no `preferred_cost` input
plumbing exists anywhere (always `None` in both loaders) — inventing either
would fabricate the valuation, so the 503 stands with its truthful message.

### Coverage states now distinguished

New `valuation_readiness` (`sec_first.py`, tested in `tests/test_sec_first.py`)
separates data-readiness states — PACKET_BUILT, INPUTS_COMPLETE (gate),
POLICY_VALID (conflict-free published adjustment evidence; presence only),
CAPITAL_COSTS_AVAILABLE (zero preferred or explicit cost), DCF_EVALUABLE
(data-complete prediction: no DCF is run here, market price/beta/Treasury
still required) — from operational checks (brief, staging runs) recorded
here. Adjustment-evidence conflicts block POLICY_VALID, so conflicting or
market-input-less packets can never read as fully verified:

| Issuer | Packet | Inputs | Policy | Capital costs | DCF | Staging |
| --- | --- | --- | --- | --- | --- | --- |
| CAT | ✓ | ✓ | ✓ | ✓ (0 pref) | ✓ | working |
| PEP | ✓ | ✓ | ✓ | ✓ (0 pref) | ✓ | working |
| T | ✓ | ✓ | ✓ | ✓ (0 pref) | ✓ | working (74.91) |
| PAYX | ✓ | ✓ | ✓ | ✓ (dual-identity 0/0 + ownership) | ✓ | working (88.01 @ price 110.78) |
| ORCL | ✓ | ✓ | ✓ | **blocked** (4954M mand. conv.) | blocked | honest 503 |

The matrix `readiness` section records this per issuer; READY packet ≠ working
valuation anywhere in the report.

### Nearby companies assessed, not forced

ABBV/AEP keep genuine negative historical effective tax rates (preserved, not
clamped); a normalized forecast-tax assumption is model work for later, not a
packet rewrite. LECO/LIN lack direct common tags; BA needs debt-branch
semantics plus a loss-year tax bound; PAYX-style dual identity changes nothing
for issuers with filed claims (ORCL/T correctly rejected). Full re-screen: 86
screened, 52 READY, 5 eligible, 4 valuation-ready — no regressions.

## Batch 3: PAYX balance-sheet economics (ownership + client funds)

Two remaining PAYX accounting issues resolved against the original FY2026
10-K (accession `0001193125-26-307785`, filed 2026-07-17), with no change to
the packet's accounting inputs and no republication.

### 1. Zero NCI equity now needs equity-level evidence

The Batch-2 rule proved zero NCI *income* (consolidated `ProfitLoss` ==
parent `NetIncomeLoss`) but a subsidiary can hold minority-owned equity
without generating minority-attributable earnings in the year, so income
equality alone cannot establish zero NCI *equity*. The derivation
(`ppe_packets.py`) now additionally requires exactly one of two reusable,
non-hardcoded paths: an exact same-accession filed total-equity
reconciliation (`StockholdersEquityIncludingPortionAttributableTo-
NoncontrollingInterest` == `StockholdersEquity`, which is promoted from a
blanket block to affirmative evidence — a nonzero gap refuses outright and
no text can override filed numbers), or a verified wholly owned-subsidiaries
ownership disclosure from `evidence/ownership_disclosures.json` bound to the
same CIK and accession, with location, exact quote, source URL, filing date,
filing hash and verification date all required. The member-wide claim scan
now also covers company-extension namespaces (e.g. a `payx:` NCI tag refuses
even with a valid disclosure). PAYX qualifies via Note A: "The consolidated
financial statements include the accounts of the Company and its wholly owned
subsidiaries." Negative tests: income equality with no equity evidence,
nonzero total-equity gap despite a disclosure, wrong-accession or
incomplete disclosures, split-accession total-equity legs, and
custom-taxonomy NCI claims.

### 2. Client-funds reconciliation: Method A retained, quantified

Filed FY2026 balance sheet (USD M): cash 1088.2 (incl. 217.7 PEO float per
Note A), funds held for clients 4832.2, total CA 8613.3, client fund
obligations 4884.6, total CL 6840.6. Full 2024–2026 history plus the frozen-
input valuation bridge lives in `find/outputs/company-packets/payx-client-
funds.json` (regenerated by `scripts/reconcile_payx_client_funds.py`; pinned
by `tests/test_payx_client_funds.py`). Findings:

- **No double count.** Client balances enter once, net (−52.4M), inside NWC;
  the bridge carries plain reported cash only. `cash + NWC = CA − CL + debt`
  holds exactly (1088.2 + 684.5 = 8613.3 − 6840.6 + 0).
- **B1 (remove $217.7M from cash only) is rejected**: it fabricates a claim
  (−$0.605/share = exactly −217.7/360.0M) with no liability relief, while the
  float's offset sits undisclosed inside operating CL (accrued worksite comp
  844.8M). MD&A supports operating treatment — PEO collections/payments
  "are settled through our corporate cash and the fluctuations impact our
  operating activities" — while client-obligation fluctuations impact
  financing activities.
- **B2 (symmetric fiduciary carve-out, both legs filed) is level-neutral** by
  construction and moves only NWC-margin forecasts: intrinsic 87.6380 vs
  88.0140 (**−$0.376/share, −0.43%**). It cannot be a reusable companyfacts
  mapping — `ClientFundObligations` is a `payx:` extension concept absent
  from companyfacts, as is the PEO float — so Method A is retained and B2
documented.
- **B3 (symmetric PEO carve-out) stays a sensitivity** (−$1.46/share): it
  assumes the float's liability offset equals the float each year, a split
  the filing never discloses. Its swing dwarfing B2's is itself evidence
  against assuming it.
- The frozen harness replicates the live staging DCF to 1e-9 (intrinsic
  88.0140 at the recorded assumption set), so every delta above is
  accounting-driven by construction; the 86.69 → 88.01 live move remains
  market-input repricing (price 110.78, WACC 8.647%), not accounting.

No packet change, no republication: every financial input of `3b1577c8…`
remains the filing-supported, symmetric, companyfacts-buildable treatment.

## Batch 4: forecast-tax policy (ABBV/AEP cases, reusable model)

Reported historical ETRs and forecast tax assumptions are now separate
concepts (`tax_policy.py`): signed history is preserved with provenance;
the 5-year forecast reuses the latest reported rate only inside 0-1 and
refuses loudly otherwise until an explicit user override or a
filing-supported normalized scenario arrives; the debt shield defaults
coherently to the resolved forecast rate with an explicit override path.
The SEC-first gate no longer invalidates statements over unusual history —
it blocks the *baseline run* with `tax_forecast_assumption_required_*`
and names the fix. No ticker constants, no automatic 21% substitution.

ABBV FY2024 (accession `0001551152-25-000020`): ETR −15.3% bridges as 21.0
+ 7.6 (foreign) − 5.4 (credits) − 1.2 (stock comp) + 1.1 (non-deductible)
− 0.3 (law/structuring) − 51.4 (audits/settlements closed — discrete)
+ 13.4 (ImmunoGen/Cerevel deal costs — discrete) − 0.1; recurring-only
23.1%. FY2025 (accession `0001551152-26-000007`) corroborates discrete noise
both ways (ETR 35.8% = 21.0 + 21.6 PR differential − 45.3 one-time PR
industrial income + 16.9 GILTI + 9.9 reserve builds + 9.8 deal costs +
routine mix; full bridge in `reconciliation_2025`): recurring-only under the
adopted flags is 42.3%, but moving the whole PR pair to discrete gives
21.0% — that single judgment call spans the adopted 23.1%, so no FY2025
point is stable and none is adopted. Frozen DCF (all else identical): BASE
(latest 35.8%) 271.54, NORM (23.1%) 288.27 (+16.74), USER (25%) 285.86.

AEP FY2024 (accession `0000004904-25-000027`): ETR −1.3% bridges as 21.0
+ 0.7 (flow-through) − 2.0 (ITC amort.) − 7.3 (PTCs, earned with output)
+ 0.6 (state) − 0.5 (removal) − 1.6 (AFUDC equity, non-cash) − 3.1
(TCJA excess ADIT reversal, declining) − 8.9 (excess ADIT remeasurement —
discrete) − 0.2; recurring-only 7.8%. FY2025 (accession
`0000004904-26-000103`): reported 3.37% = 21.0 + 0.81 (state) − 6.38 (PTCs)
− 0.18 (ITC/other credits) + 0.08 (UTB) + 0.47 (flow-through) − 1.62
(ADIT reversal) − 10.01 (Oklahoma + NOLC remeasurement — the ONLY discrete
item) − 1.07 (AFUDC) + 0.29; recurring-equivalent 13.4% (3.37 + 10.01),
showing credit variability — never a statutory 21%. (An earlier draft wrote
13.0%; the filed bridge supports 13.4%.) Frozen 5-yr cumulative FCFF:
BASE (3.37%) −3527M, NORM (7.8%) −4742M, USER (12%) −5895M; WACC
5.71% → 5.62% → 5.54%, coherent with each forecast. No terminal value is
supportable under the industrial template — regulated capex (~39% of
revenue) structurally exceeds operating cash flow — so AEP gets quantified
tax channels, not a per-share intrinsic. That refusal is the utility-fit
finding: rate-base economics need their own model, not a patched template.

Eligibility before/after: both carried `tax_rate_out_of_bounds_2024-12-31`;
the gate then named `tax_forecast_assumption_required_*` per unusual year.
Since the Batch-5 refinement only the latest year governs default-forecast
resolvability — a negative middle year stays signed but never blocks — so
ABBV (latest 2025: 35.8%) now carries NO tax reason while AEP (latest 2025:
3.37%, in-bounds) likewise has none; both still carry
`missing_bridge_preferred_equity` (no XBRL preferred tag; filed NCI — ABBV
39-42M, AEP up to 1080M — correctly refuses any zero derivation), so
neither unlocks and nothing was manufactured. ORCL's
convertible-preferred restriction is untouched. Evidence:
`find/outputs/forecast-tax/abbv-aep-evidence.json` (regenerated by
`scripts/reconcile_forecast_tax.py`; pinned by `tests/test_tax_policy.py`).
CAT/PEP/T/PAYX histories are in-bounds, so their defaults — and staging
valuations — are numerically unchanged (full-suite parity).

## Packet sizes, serving, cost/latency

- New packets ~41–42 KB (under the 128 KB serving limit), immutable
  content-addressed keys, conditional uploads with read-back verification.
- Staging T load: SEC-first, assembly-cache HIT ~2.6 s wall on the paced check;
  one transient 503 preceded it (also seen pre-change; retried successfully).
  No worker code changed, so no redeploy was needed — staging reads the
  candidate pointer live.
- R2/SEC-archive access stays bounded (range reads, 16 MB fact cap); screening
  cost is ~1 min per 40 companies on the operator machine. No production
  traffic impact: no production writes, no Worker changes.
