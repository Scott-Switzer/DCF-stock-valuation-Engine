# Candidate routing fix + PEP republication — verification (2026-10-14)

Supersedes the PEP-packet section of `cat-pep-staging-verification.md`
(live PEP packet is now `b769215f…`, not `488286a4…`).

## 1. Routing defect fix (`ppe_provider.py`, PR #39)

After a staging candidate miss and a Zion miss, the final `_packet_from_pointer()`
call reused `pointer_key` (the candidate index) instead of the authoritative
`POINTER`, bypassing valid production R2 entries. The fallback now always reads
`control/valuation/CURRENT.json`; candidate-listed issuers still override
everything else in staging. Packet validation and integrity checks unchanged.

Tests added (`tests/test_ppe_provider.py`): candidate absent → Zion 404 →
production R2 hit (asserts read order candidate → production → packet);
Zion error → production fallback; candidate+Zion+production miss → `None`;
corrupt candidate raises without suppression (Zion not consulted);
production routing without override queries `CURRENT.json`.
Corrected the stale test that expected the candidate pointer twice.

## 2. PEP dry-run vs live comparison — exact financial parity

Rebuilt PEP from SEC archive `sec/bulk/sec-nightly-20260924/companyfacts.zip`
(producer release `0a318ed6`, cutoff 2026-10-14) and diffed against live
candidate packet `488286a4…`: three historical periods, common income, revenue,
EBIT, D&A, CapEx, NWC, taxes, diluted shares (1,373,000,000), interest expense,
bridge and dividends — **all values identical**. Delta is source-metadata-only
(archive etag/member digests, PPE canonical evidence) plus the newly attached
`adjustment_facts`.

New `adjustment_facts` validated: `as_of` 2026-10-14 = cutoff, CIK 0000077476,
accession 0000077476-26-000007, 10-K filed 2026-02-03, three periods;
`ebit_facts` ×3 (OperatingIncomeLoss 11,986M / 12,887M / 11,498M),
`intangible_impairment` ×3 (927M / 33M / 1,993M), `goodwill_impairment` ×2
(amount 0, as reported), no conflicts.

## 3. Publication record

- New packet `gold/valuation/releases/b769215f22e6093a4a684dc0d6d696a681d836b6400953435d347add5d25dd18/companies/PEP.json`
  (40,173 bytes; downloaded bytes re-hashed to the pointer sha256; `validate_packet` OK).
- Candidate pointer `40075ded…` → `beee5c14…`, companies still `[CAT, PEP]`;
  CAT reference preserved exactly (`6ac3aec3…`); update was ETag-conditional.
- Previous pointer saved in `pep-pointer-rollback.json`.
- Production `CURRENT.json` sha256 `ecf1e1c4…` byte-identical before/after.
- Machine-readable: `pep-candidate-dryrun.json`, `pep-candidate-publish.json`.

## 4. Live staging verification (worker `eadacfc0`)

`staging-verification.json`:
- PEP cold build: `CANDIDATE_R2` (`Direct PPE R2 binding (staging candidate index)`),
  SEC-first, 4.08 s client (sec_first 0.671 s, zion_packet 0.136 s);
  `accounting_adjustments_source: "published with packet"`,
  `accounting_adjustments_timing: 0.0` — **zero live SEC concept requests** for adjustments.
- CAT: candidate SEC-first, periods 2023/2024/2025-12-31 intact.
- Workbook parity both: snapshot reused, DCF-target band Base exact (Δ0),
  staging brief == local brief; custom growth edit moves the principal
  (PEP 156.78 → 200.32, CAT 217.46 → 246.60) with band Base exact and custom flagged.
- Fallback matrix: AAPL/HD → `ZION_SERVICE_BINDING`; KHC (unlisted) → Yahoo;
  ZYME/WCT/PALI 503s are pre-existing Yahoo data gaps, byte-identical on production.
  A live production-`DIRECT_R2` hit was not observable (probed production-listed
  tickers are Zion-served or Yahoo-broken); the path is covered by unit test.

## 5. CAT WACC reconciliation

The 6.5% fallback was invalid for CAT: with the server-recalculated WACC
≈ 9.65817% (from `recalculate_costs`, same inputs both sides), local math
reproduces the staging DCF lane 209.87086438600514 bit-for-bit; the
time-separated local rebuild drifts 5.9e-07 (market micro-drift), and the
independent Yahoo baseline agrees to 6.1e-05.

## 6. Limitations

- No production deployment; `CURRENT.json` never written by this workflow.
- PEP is staging-only (absent from production `CURRENT.json`).
- Per-build packet sha churn (`built_at`) is expected; content parity is the check.
