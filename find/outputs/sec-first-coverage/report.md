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
