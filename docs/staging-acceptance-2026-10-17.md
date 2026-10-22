# Dedicated Zion staging acceptance — October 17, 2026

## Result

The existing DCF application now has a freshly verified dedicated staging workflow:
native Zion financial history, explicitly selected Damodaran assumptions, operating
valuation, source-bound equity claims, a saved research record and a scoped export.
The workflow uses existing internal Cloudflare bindings, D1 and immutable source releases.

- Origin: https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev
- Deployed implementation: `a2dd659dc935e88104849b26aca863671438be43`.
- Active Worker version: `facc3400-2a02-4088-9d9f-df091ec389b3`.
- Previous baseline/rollback version: `73843326-0b6d-468e-9320-f85a3a1315bb`.
- Exact-revision live acceptance: **21 checks, zero failures**.
- Local DCF suite: **954 passed, 10 subtests passed**; one pre-existing test-return warning.
- Ruff, JavaScript syntax, Python compilation and deployment packaging passed.
- Independent raw-SEC bridge validation: Apple, Microsoft and Alphabet **VALIDATED**,
  with zero failures at the September 24 evidence cutoff.
- Zion cache-scope and equity-claims route regressions: **36 passed**. Credential
  rotation was simulated in tests; no deployed credentials were rotated.
- Portfolio Engine prescribed offline suite in its repaired isolated environment:
  **4,530 passed, 37 skipped, 5 deselected**. The seven previously failing/uncollectable
  modules separately pass 54 tests. Existing deprecation warnings remain; historical
  strategy performance is still not certified.

The aggregate [live receipt](receipts/staging-acceptance-2026-10-17.json) names the served
revision, both financial source releases, availability cutoff and every gate. Passing
local tests are not used as deployment evidence.

## Numerical reproduction

| Company | Reproduced per-share scenario |
| --- | ---: |
| Apple | 119.21703451950214 |
| Microsoft | 271.57328289297936 |
| Alphabet | 188.18558019134235 |

These are reproducible assumption-driven scenarios, not current prices or verified fair
value recommendations. The run deliberately repeats valuation date **October 15, 2026**
using financial evidence through **September 24, 2026** and exact published benchmark
releases. It does not relabel older source data as current. Alphabet's conversion terms
remain an explicit scenario selection. Saved exports preserve these qualifications.

## Changes made in this acceptance pass

- `d4a9fc2`: reconcile current remote main `09719a5` with the previously verified
  `integration/unified-valuation` branch, preserving recalculated-WACC behavior alongside
  benchmark and CAPM enrichment.
- `0cfea92`: reject a signed history bundle for a different issuer; default claims to the
  history's engine release; refuse a returned engine-release mismatch before saving.
- `81611bc`: reject recalculated WACC combined with an explicit benchmark or propagated
  CAPM WACC. This prevents a rate being overwritten while its provenance says it was used.
  Extend live acceptance to reject mixed issuers, edited evidence and forged attestations.
- `a2dd659`: advertise binding-backed native history as configured, and make that state
  part of the live acceptance gate.

Issuer and WACC regressions were observed failing before the fixes and passing afterward.
The new code received a focused independent review; its WACC finding was reproduced and
corrected. Existing code reconstructs operating inputs from HMAC-attested pages rather
than trusting editable derived fields. Both financial and benchmark dependencies use
their existing service bindings and existing credentials.

The live gate also verifies three saved exports, a second identity's 404 on each export,
foreign-Origin write rejection and wrong-release refusal. Test runs create isolated
research records in the existing staging database; they do not publish source releases.

## Reproduce and rollback

```sh
python scripts/verify_staging_e2e.py \
  --base https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev \
  --expected-commit a2dd659dc935e88104849b26aca863671438be43 \
  --output /tmp/staging-acceptance-reproduction.json
```

The script locates the existing reconciliation artifacts, or accepts their directory
through `ZION_INTEGRATION_ARTIFACTS`. It uses the named historical scenario and explicit
benchmark pins. It never prints credentials or exports other users' records.

Rollback, if needed, targets only the dedicated staging Worker:

```sh
wrangler versions deploy 73843326-0b6d-468e-9320-f85a3a1315bb \
  -c wrangler.verify.jsonc --env staging -y
```

## Boundaries and remaining work

Production and shared DCF staging were not deployed or reconfigured. Zion's dirty
readiness work was preserved. No source publication pointer, credential, permission,
subscription or resource allocation changed. New billing was not independently measured.
The integration is committed locally; no main-branch merge is claimed.

Refreshing source coverage beyond September 24 requires a separately validated immutable
release. Corporate-action correctness, continuous security identity and independent
historical strategy-performance validation remain separate gates; old backtest claims
are not promoted by this acceptance run.
