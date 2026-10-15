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

Note: the republished PAYX packet carries corrected provenance wording under
the same accounting values; its content hash changes while every financial
input stays identical.

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
| PAYX | ✓ | ✓ | ✓ | ✓ (dual-identity 0/0) | ✓ | working (86.69) |
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
