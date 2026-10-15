# Zion equity-claims integration: live runtime milestone, 2026-10-15

Scope: make the Zion equity-claims service and the DCF consumer run across the Cloudflare
Worker boundary, validate the financial bridge, and decide whether a private staging
release is safe. Nothing here is a redesign of the claims model, the extraction, or the
enterprise valuation engine.

## 1. Headline

The integration now runs in a real Workerd runtime over a genuine Cloudflare service
binding, and the authorization boundary behaves exactly as designed. Running it there
exposed **one decisive defect that no in-process test could have found**: the Zion
`/private/v1/equity-claims` route reads a member shape that the deployed SEC archive does
not have, so **the endpoint answers `SOURCE_CONTEXT_INVALID` (503) for every filer,
including all three plan companies**. Until that is repaired the required end-to-end
per-share demonstration through the Worker cannot succeed, and a staging release of this
route would ship a broken endpoint. The repair is described in §9: implemented and verified
in process, and still undeployed.

Comparing the two independent bridge paths also exposed a quieter defect on the DCF side:
the public-SEC bridge missed Alphabet's 7,100,000,000 noncontrolling interest and overstated
common equity by that amount. It is repaired, and the paths now agree to the last digit (§5).

## 2. What changed

| File | Change |
| --- | --- |
| `wrangler.jsonc` | Production environment no longer binds a staging Zion Worker; the scoped `ZION_FINANCIAL_QUERY` binding exists only in the `staging` environment (Priority 1). |
| `wrangler.dev.jsonc` | New local multi-Worker dev harness mirroring the staging environment. |
| `zion_equity_claims_service.py` | New. The service-binding transport, the integrated bridge route and the saved research record. |
| `equity_claims_provider.py` | Fixed the request cutoff; dual-layout import so the module also loads from a flat Worker bundle. |
| `scripts/embed_assets.py` | Bundles `equity_claims_provider`, `zion_equity_claims_service` and the public-SEC bridge helper the provider imports. |
| `migrations/0009_equity_claims.sql`, `library.py` | Store for saved bridge records, plus the route paths added to the library identity and same-origin write guards. |
| `app.py` | Registers the new routes; adds them to the cross-site write guard and the rate-limit prefixes. |
| `scripts/public_sec_equity_bridge.py` | Carries the caller's offering terms into as-converted and liquidation scenarios, and resolves the noncontrolling interest from the filed total or the VIE disclosure, never both (Priority 3). |
| `scripts/validate_equity_bridge.py` | New independent balance-level validation (Priority 3). |
| `tests/test_public_sec_equity_bridge.py` | Adds the preferred-terms scenarios and the minority-claim cases, including the fail-closed guards. |
| `tests/test_zion_equity_claims_service.py` | New. Transport, fail-closed and record tests. |
| `tests/test_equity_claims_contract_e2e.py` | Adds the service-binding flow over the real SEC-backed contract and the refusal cases. |
| `tests/test_equity_claims_provider.py` | Corrects the request-cutoff assertion. |
| Zion `thin/wrangler.dev.jsonc` | New local dev harness with the three R2 buckets bound remotely. |

## 3. Priority 1 — production and staging are now separate

The deployed facts, read from the Cloudflare API:

* `dcf-valuation-engine` (production) service bindings: `ZION_DATASET_CATALOG → zion-datasets`,
  `ZION_VALUATIONS → zion-valuation`. **No `ZION_FINANCIAL_QUERY`.** Production has never
  carried the binding.
* Account worker inventory: 31 Workers, of which every Zion financial-data Worker is
  `-staging` or `-candidate` named. **There is no production Zion thin Worker.**

So the reported collision was not an accidental cross-wiring so much as a real
asymmetry: the local default (production) environment was prepared to publish a
production DCF Worker whose data plane is a *staging* Zion. That is now closed — the
default environment declares no such binding, and a production DCF deploy cannot acquire
a staging dependency.

Verified with `wrangler deploy --dry-run` on both environments on wrangler 4.151.0:
default exits 0 with no `ZION_FINANCIAL_QUERY` in its binding list; `--env staging` exits
0 with `ZION_FINANCIAL_QUERY (zion-financial-serving-v2-thin-staging)` present.

## 4. Priority 2 — both Workers, one real runtime

    wrangler dev \
      -c {zion}/deploy/cloudflare-query/thin/wrangler.dev.jsonc \
      -c wrangler.dev.jsonc --port 8791 --ip 127.0.0.1 --persist-to /tmp/dcf-dev-state

The DCF Worker bundled 389 modules (5.3 MiB) including `zion_equity_claims_service.py`,
with `python_modules` vendored by `pywrangler sync`. The Zion thin Worker bundled its 30
modules with `MARKET_DATA`, `SEC_CORPUS` and `SEC_ARCHIVE` bound **remote**, so every
claim came from the real immutable archive, not a simulator.

### Authorization matrix over the real route

| Request | Response |
| --- | --- |
| no credential | `401 UNAUTHORIZED` |
| wrong service token | `401 UNAUTHORIZED` |
| unapproved caller (`x-zion-service-caller: someone-else`) | `403 SERVICE_CALLER_NOT_PERMITTED` |
| `recipient=bulk` | `403 RECIPIENT_NOT_PERMITTED` |
| malformed CIK | `400 INVALID_CIK` |
| missing cutoff | `422 CUTOFF_REQUIRED` |
| date-only cutoff | `400 INVALID_AVAILABILITY_CUTOFF` |
| future cutoff | `422 CUTOFF_EXCEEDS_SOURCE_RELEASE` |
| unknown query parameter | `400 INVALID_PARAMETER` |
| pinned release that is not the served one | `409 SOURCE_VERSION_CHANGED` |
| correctly authorized | `503 SOURCE_CONTEXT_INVALID` ← the defect |

Two rows above are superseded by §9: a date-only `as_of` is now the route's documented
whole-day request rather than a rejected one, and the `503` row is the defect the companion
Company Facts release repairs.

The scoped service credential is **not** widened to bearer-only routes: the same
credential on `POST /private/v1/query` is refused `401 UNAUTHORIZED`, while the corporate
bearer is accepted (and reaches the operation dispatcher). Cloudflare Access identity is
not relied on anywhere; every downstream check is explicit.

### The defect, and its evidence

`equity_claims_api.execute` ends with

    company = await artifact(env, reference)          # the SEC engine archive member
    if str(company.get("cik")).zfill(10) != cik or not isinstance(company.get("facts"), dict):
        fail("SOURCE_CONTEXT_INVALID", 503)

The archive member at
`gold/sec-engine/releases/c1fae45f…/companies/0001652044.json` of release
`b39a670bad06…` has these top-level keys:

    cik, concept_definitions, label, member_sha256, observations, policy,
    registry_sha256, registry_version, rejected_contexts, rejections, release_id,
    rights, schema_version, source_inventory, source_lineage

There is **no `facts` key** and **no `entityName`** key. The member carries 1075
normalised `observations` (`concept`, `source_record {accn, end, filed, form, fp, fy,
val}`, `period_*`), not the SEC Company Facts `{taxonomy: {tag: {units: {unit: [rows]}}}}`
shape that `equity_claims.build_claims` consumes. So the identity check cannot pass, and
the route fails identically for Apple, Microsoft, Alphabet and JPMorgan.

Repair options, in order of preference:

1. **Publish the facts the extractor requires inside the engine release.** Add
   `gold/sec-engine/releases/<id>/companyfacts/cik=<cik>.json`, derived from the same
   immutable source and covered by the release manifest digest, and read that key. The
   release pin then still names the archive the facts came from.
2. **Repoint the route at the SEC corpus**, which *does* hold the right shape at
   `{SEC_CORPUS_PREFIX}/raw/sec/companyfacts/cik=<cik>/companyfacts.json`. But the corpus
   currently contains only three companyfacts objects — JPMorgan `0000019617`, Apple
   `0000320193`, Microsoft `0000789019` — so this cannot serve Alphabet, and the release
   pin would have to become the corpus prefix so provenance stays honest.
3. Extend the corpus with Alphabet and any other planned filer, then choose 1 or 2.

This is a data-contract decision with provenance consequences, so it is reported rather
than made: the pin must name whatever archive the facts actually came from.

## 5. Priority 3 — independent bridge validation

`scripts/validate_equity_bridge.py` re-derives every claim straight from the downloaded
SEC Company Facts, without using the claims contract as its source of truth, and checks
the things a bridge gets wrong quietly. Result: `status: VALIDATED`, `failures: []`, all
three filers `VALIDATED`. Receipt:
`artifacts/validation/equity-bridge.json`.

Answers to the three flagged questions, all from the filing itself:

* **Alphabet's $7.1B noncontrolling interest.** It is not inside additional paid-in
  capital. The value comes from `us-gaap:NoncontrollingInterestInVariableInterestEntity`
  = 7,100,000,000 at 2026-06-30, filed in 10-Q accession `0001652044-26-000071`. Parent
  equity is `us-gaap:StockholdersEquity` = 640,480,000,000, and the balance identity
  Assets 921,983,000,000 − Liabilities 281,503,000,000 = 640,480,000,000 holds with a
  residual of exactly 0 — so the VIE interest sits *outside* the parent's equity line and
  is a distinct claim on the consolidated cash flows the enterprise value measures.
  Deducting its reported carrying amount once is therefore correct in principle. Two
  caveats stand: it is a carrying amount, not a fair value, and the DCF keeps an explicit
  `EXCLUDE_WITH_SENSITIVITY` policy for exactly this judgment.
* **Alphabet's $242.474B nonoperating total.** Constituents are
  `us-gaap:CashAndCashEquivalentsAtCarryingValue` 55,911,000,000 and
  `us-gaap:MarketableSecuritiesCurrent` 186,563,000,000, summing to 242,474,000,000.
  Cash is one of the constituents and appears in exactly one bridge role; the contract
  adds `nonoperating_assets − cash` = 186,563,000,000 as `other_nonoperating_assets`, so
  reported cash is counted exactly once. `us-gaap:EquityMethodInvestments` 2,300,000,000
  is correctly excluded from the nonoperating total.
* **Preferred conversion and leases.** Alphabet reports
  `us-gaap:ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue`
  18,023,000,000 with 19,000,000 preferred shares; the contract carries no dilution
  terms, so the caller's offering terms replace the carrying claim rather than joining it,
  and the as-converted scenarios deduct no preferred claim and add converted shares while
  the liquidation scenario deducts the preference and adds no shares. Finance leases
  (`us-gaap:FinanceLeaseLiability` 2,590,000,000) are deducted; operating leases
  (`us-gaap:OperatingLeaseLiability` 18,037,000,000) are excluded because EBIT is after
  operating lease cost.

Reconciliation, re-run and reproduced: `failures: []`, Apple $119.217, Microsoft $271.573,
Alphabet $188.186 per share. These remain assumption-dependent scenarios, not certified
fair values.

### The reconciliation found a real defect, and it is fixed

The two paths did **not** agree when first compared, and the gap was not an assumption:

| Path | Artifact | Apple | Microsoft | Alphabet (as-converted, max rate) |
| --- | --- | --- | --- | --- |
| Independent validator (`scripts/validate_equity_bridge.py`) | `artifacts/validation/equity-bridge.json` | `VALIDATED` | `VALIDATED` | `VALIDATED` |
| Claims contract → enterprise → bridge (in-process) | `GOOGL-equity-claims.json` | 119.217 | 271.573 | 188.186 |
| Bridge receipt, before the fix | `public-sec-bridge-GOOGL-preferred.json` | 119.217 | 271.573 | 188.764 |
| Bridge receipt, after the fix | `public-sec-bridge-GOOGL-preferred.json` | 119.217 | 271.573 | **188.186** |

The difference was exactly Alphabet's 7,100,000,000 noncontrolling interest. The claims
contract reads `us-gaap:NoncontrollingInterestInVariableInterestEntity` when the filer does
not file a `us-gaap:MinorityInterest` total, and Alphabet files only the VIE disclosure. The
public-SEC bridge script looked only for the total, so it recorded the claim as
`NOT_REPORTED_ASSUMED_ABSENT`, deducted nothing, and overstated Alphabet's common equity by
7,100,000,000 (\$0.578 per share) — the same class of silent error the validator exists to
catch, found by comparing the two paths rather than by trusting either.

`scripts/public_sec_equity_bridge.py` now resolves the minority claim the same way, the
filed total when present and otherwise the VIE disclosure, never both, and records which
row was used plus the rule in `result.minority_interest`. Apple and Microsoft receipts are
unchanged (they file no such row); the Alphabet receipts were regenerated and are
byte-stable under re-run.

| Alphabet scenario, corrected | Per share | Artifact |
| --- | --- | --- |
| Preferred absent, NCI deducted | 189.024 | `public-sec-bridge-GOOGL.json` |
| As-converted at the maximum rate (primary) | 188.186 | `public-sec-bridge-GOOGL-preferred.json`, `GOOGL-equity-claims.json` |
| As-converted at the minimum rate | 188.353 | same |
| At the liquidation preference, no shares added | 187.470 | same |

The contract's liquidation scenario deducts 19,000,000,000 (the reported 19,000,000
preferred shares) where the bridge deducts 19,250,000,000 (the offering terms' 19,250,000);
the 250,000-share difference is the documented rounding tolerance, and both are labelled.

## 6. Priority 4 — test environments

The Zion failure was an interpreter problem, not a dependency problem: the repository's
own `.venv` already contains `diskcache` 5.6.3, while the interpreter that was failing
lacked it. A declared-environment venv was built instead, without editing
`pyproject.toml` or any lockfile:

    uv venv --python 3.12 .venv-test312
    uv pip install --python .venv-test312/bin/python -e . pytest pytest-mock \
        pytest-benchmark fastapi 'httpx<1' 'uvicorn<1'
    .venv-test312/bin/python -m pytest tests -q -p no:randomly

**1045 passed, 1 failed, 3 skipped in 53.42s.** The single failure is
`tests/unit/test_sec_universe_basin.py::test_prepare_compact_parquet_full_parity`,
which raises `STOP_DISK_RESERVE` from its own `disk_guard` because this machine had
148 MiB free at the time (99% full). It is an environmental resource failure in a module
unrelated to this change.

DCF, after every change: `.venv-ddfi-test/bin/python -m pytest -q -p no:randomly` →
**788 passed, 10 subtests passed in 18.31s** (773 before this work).

Re-verified at the end of the milestone (this is the run the receipts in §5 came from):

* `.venv-ddfi-test/bin/python -m pytest -q -p no:randomly` → **788 passed** before the
  minority-claim repair below, **790 passed** after it (two new tests cover the VIE
  fallback and the never-sum rule).
* `.venv-ddfi-test/bin/python scripts/validate_equity_bridge.py --output /tmp/equity-bridge.json`
  → `status: VALIDATED`, `failures: []`, byte-identical to the committed receipt.
* `scripts/public_sec_equity_bridge.py` re-run for AAPL, MSFT and GOOGL (the last with
  `--preferred-terms`) → each receipt byte-identical to the stored one, so the bridge
  numbers in §5 are reproducible from the pinned filings and the caller's terms. The
  Alphabet receipts were regenerated once, for the minority-claim repair, and then
  reproduced byte-identically.
* Zion claims and private-route modules: `.venv-ddfi-test/bin/python -m pytest
  tests/unit/test_equity_claims.py tests/unit/test_equity_claims_api.py
  tests/unit/test_private_api.py tests/unit/test_private_api_routes.py
  tests/unit/test_private_financials.py tests/unit/test_sec_history_api.py -q` →
  **94 passed**. A borrowed interpreter (the DCF venv, Python 3.12) is used deliberately
  here: it documents that these modules need nothing beyond `pytest`, and it avoids both
  editing the locked dependencies and spending the ~200 MiB free at the time.
* The full Zion suite result above (1045 passed, 1 disk-guard failure) was not re-run:
  `.venv-test312` was removed when the milestone closed and the volume is again at 95%
  (735 MiB free). The only Zion commit after that run, `6365d8f`, touches `.gitignore`
  and the new `thin/wrangler.dev.jsonc` and no Python, so the recorded coverage still
  describes the committed Python. Two limitations to carry: the recorded full-suite figure
  is not freshly reproducible on this machine, and `tests/unit/test_sec_universe_basin.py`
  cannot pass under disk pressure.

## 7. Priority 5 — staging deployment: not performed

Deliberately stopped at the deployment boundary. Deploying this route now would publish
the `SOURCE_CONTEXT_INVALID` defect to staging, and the repair choice in §4 changes what
the release pin attests to — both are decisions for the operator. No secret was set, no
version was uploaded, no route was changed, and no production credential was retrieved.

Minimum operator action, with the §9 repair now implemented but not deployed:

1. Deploy the repaired Zion Workers and re-run the authorization matrix above; the last row
   must become `200` with real claims for each planned filer.
2. `wrangler d1 migrations apply DB --env staging` (adds
   `0009_equity_claims.sql`; without it the bridge route returns 503 on save).
3. Set `ZION_SERVICE_TOKEN` on `zion-financial-serving-v2-thin-staging` with
   `wrangler versions secret put` — not `wrangler secret put`, which creates and
   immediately deploys a version. The DCF `staging` environment needs the same value in
   its own secret.
4. Deploy both staging Workers and repeat the matrix against the deployed origin.

## 8. Limitation that remains after the repair

The bridge route recomputes the enterprise value from the attested bundle, and the
benchmark assumptions it needs come from Zion's private query API
(`operation: benchmark_context`), which needs the private bearer credential. That is a
pre-existing property of `/api/calculate/enterprise`, not of this change, but it means
the enterprise leg of the in-Worker demonstration cannot be exercised without that
credential. In this run the claims leg, the binding, the authorization boundary and the
saved-record plumbing were exercised in the runtime; the claims → enterprise → bridge →
per-share → saved record chain was exercised in process over the real SEC-backed contract
(28 focused tests, 788 suite tests).

## 9. Follow-up: the §4 defect repaired, and the cutoff convention made explicit

The repair follows the first §4 option in its own shape: rather than mutate the published
engine release or widen its metric registry, the raw Company Facts members are published as a
**separate immutable companion release** derived from the same pinned public SEC bulk archive.

| File (repo) | Change |
| --- | --- |
| Zion `src/sec_companyfacts.py` | New. Reads the companion release manifest, its approved previous releases and one member by CIK; only the companion prefix is read and no caller-supplied key is accepted. |
| Zion `scripts/publish_sec_companyfacts.py` | New. Extracts exactly the archive member bytes the engine release pinned, re-verifies zip CRC32, size and `materialized.member_sha256` against the engine release's own pin, and publishes with `--immutable`. |
| Zion `src/equity_claims_api.py` | The route reads the companion member, requires the engine pin and the companion member to name the same bytes (`SOURCE_BUNDLE_MEMBER_MISMATCH` otherwise), applies the availability filter at the serving boundary, and returns a `source_bundle` plus the resolved `cutoff` report. |
| Zion `src/equity_claims.py` | `AVAILABILITY_POLICY`, `end_of_day_utc`, `restrict_to_available`; the claims block records the policy and the rule. |
| Zion `thin/wrangler.jsonc`, `thin/wrangler.dev.jsonc` | Both thin environments name the companion manifest key and digest. |
| DCF `equity_claims_provider.py` | Verifies the dual-release bundle, asks for a day-level cutoff, and reads back the cutoff the source resolved. |
| DCF `zion_equity_claims_service.py` | Carries `source_asof` and `expected_source_release_id`, and records the companion release, the evidence ceiling and the served cutoff in the attestation. |
| DCF `scripts/verify_equity_claims.py` | Wraps the fixture the way the route now does (availability filter, dual release blocks, resolved cutoff) and pins both releases. |

### The cutoff convention, and why an instant is the wrong request

SEC Company Facts carries a filing date but no acceptance time, so the route publishes one
rule: a filing dated D is available once day D has ended in UTC. A date-only `as_of` is the
whole of that day (`DATE_ONLY_END_OF_DAY_UTC_V1`, `day_complete: true`); an explicit instant
is honoured as given and therefore **excludes** filings dated that day. End of day is the last
nanosecond, not `23:59:59.000`, so a request spelled `2026-10-14T23:59:59Z` is an intraday
request that silently drops the day's own filings.

That was the defect this follow-up found, in the consumer rather than the producer: the DCF
consumer asked for `<date>T23:59:59Z`, so a valuation dated D would have been served with D's
filings missing while still being labelled D. The consumer now asks for the evidence date
itself and reads the resolution back — the requested cutoff, the resolved instant, the
valuation date, the named policy and `day_complete` must all agree, or the claims are refused
(`an intraday cutoff leaves the evidence day incomplete`).

### Verification after the repair

* Zion: `python3 -m pytest tests/unit/test_equity_claims.py tests/unit/test_equity_claims_api.py tests/unit/test_dataset_registry.py tests/unit/test_sec_history_api.py -q` → **80 passed**. The route tests pin the whole cutoff report, that a filing dated the valuation day is `REPORTED` for a day-level request and not for an intraday one, and that releases pinning different bytes for one filer are a conflict.
* DCF: `.venv/bin/python -m pytest tests -q` → **800 passed, 10 subtests passed**.
* DCF reconciliation re-run: `scripts/verify_equity_claims.py --output-dir artifacts/zero-subscription-integration` → `failures: []`, Apple 119.217, Microsoft 271.573, Alphabet 188.186 (the §5 numbers, unchanged), with every receipt now carrying the served cutoff and both release identities.

Limitations: nothing was deployed — no secret set, no version uploaded — so the repaired route
has still never answered over a real runtime, and the operator list in §7 stands. The Zion
suite could not be run in full on this machine: the only interpreter holding the project's
`diskcache` is the repository `.venv`, which has no `pytest`, so the covering modules were run
under the global pytest 8.4.2 (18 unrelated test modules fail collection for missing
third-party deps in that interpreter). The `tests/unit/test_sec_universe_basin.py` disk-guard
failure recorded in §6 is unaffected.

## 10. The repaired code answers through a real Workerd runtime

Everything in §9 is now observed, not asserted: the repaired DCF consumer and the Zion claims
route ran together in three local Workerd processes, and the whole chain executed over HTTP.

| Process | Config | Port |
| --- | --- | --- |
| Zion thin financial-data Worker | `{zion}/deploy/cloudflare-query/thin/wrangler.dev.jsonc` | 8790 |
| DDFI benchmark Worker (assumptions leg) | `{ddfi}/deploy/cloudflare-query/thin-benchmark/wrangler.dev.jsonc` | 8792 |
| DCF valuation engine | `dcf-zero-subscription/wrangler.dev.jsonc` | 8791 |

The DCF Worker reaches Zion through the `ZION_FINANCIAL_QUERY` service binding, so the claims
and the native history both resolve inside the account; the private bearer and the scoped
service credential are the only credentials used. `migrations/0009_equity_claims.sql` was
applied to the local D1 first, without which the bridge route cannot save.

### 10.1 The blocker, and why the dev harness now owns a local copy of the releases

The first live attempt failed on the **native-history** leg, not the claims route:

```
financials fetch failed: 503 {"error":"Zion equity claims service: the internal service
refused the request with HTTP 409 (CACHE_INTEGRITY_FAILURE)"}
```

`sec_engine_api.stored()` authenticates every derived query-cache envelope with the
deployment's private credential (`env.ZION_PRIVATE_API_TOKEN`). The shared bucket already held
the exact object for this query — key
`gold/sec-engine/releases/b39a670b…/queries/fa3ac589…json` — and its `mac` does **not** verify
under the local credential:

```
envelope keys ['mac', 'value']
local-private raw mac match False
```

so a local run is refused before it can read the cache, and `persist()` is create-only with
`etagDoesNotMatch: "*"`, so it cannot repair one either. The same object fetched with the
pinning manifest confirmed what it is: the engine's own cache for the identical query
fingerprint, written under a different credential (the fingerprint `fa3ac589…` the local
runtime then reported as `cache.state = MISS` is the same value).

Two consequences were separated:

* **For local development**, `thin/wrangler.dev.jsonc` now binds `MARKET_DATA` to a local
  simulator, while `SEC_CORPUS` and `SEC_ARCHIVE` stay on their real read-only buckets. The
  local store is seeded from the pinned releases by the new
  `{zion}/scripts/seed_dev_market_data.py`, which verifies every object against the digest its
  manifest names — the same check the Worker performs — and re-reads it from the local store
  before reporting it:

  ```
  python3 scripts/seed_dev_market_data.py --ciks 0000320193,0000789019,0001652044 \
      --persist-to /tmp/zion-dev-r2
  -> 11 objects, 17,038,461 bytes (engine manifest + 3 catalogs + 3 engine members +
     companion manifest + 3 companion members), every digest re-verified
  ```

  `tests/unit/test_dev_harness_config.py` (4 tests) now fails if the dev harness drifts from
  `thin/wrangler.jsonc` pins, if `MARKET_DATA` becomes remote again, or if the source archives
  stop being remote.

* **For the deployment**, this is an operational landmine worth its own fix: every derived
  cache envelope is bound to one secret value, so rotating `ZION_PRIVATE_API_TOKEN` (or reading
  the shared bucket with any other credential) turns every cached query into a permanent
  `CACHE_INTEGRITY_FAILURE` 409 that the create-only writer cannot repair. Namespacing the
  derived-cache key with a keyed digest of the credential — so each credential sees its own
  cache namespace — would remove the failure mode; a documented purge is the interim
  mitigation. §7 is unchanged by this: nothing was deployed to any environment.

### 10.2 Priority 1 — three filers, HTTP 200, whole contract

`POST /api/financials` (`provider=zion_history`) and `POST /api/equity-claims/bridge` through
the real Worker, with the DCF asking at valuation date `2026-10-15` and evidence cutoff
`2026-09-24`:

| Filer | CIK | HTTP | Enterprise value | Equity value | Per share |
| --- | --- | --- | --- | --- | --- |
| Apple | 0000320193 | 201 | 1,678,931,860,843.83 | 1,739,874,860,843.83 | **119.21703451950214** |
| Microsoft | 0000789019 | 201 | 2,046,624,766,262.03 | 2,016,579,766,262.03 | **271.57328289297936** |
| Alphabet | 0001652044 | 201 | 2,179,137,903,112.57 | 2,311,757,903,112.57 | **188.18558019134235** |

The §5 numbers are reproduced through the Worker boundary. Every receipt carries:

* engine release `b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb` and its
  manifest digest `4e0d6b9e…`, plus the companion Company Facts release
  `f4f81944fbf79e2cac8b119b457fd8e45b92f2171e783ecd36f85b18df80b25b` and manifest digest
  `032d432d…`;
* `reconciliation_status = MEMBER_SHA256_AGREES_WITH_ENGINE_PINNED_MEMBER`, with engine and
  companion member digests equal (`73a86c6a…` Apple, `f8aae296…` Microsoft, `a017f26e…`
  Alphabet);
* `cutoff_policy = DATE_ONLY_END_OF_DAY_UTC_V1`, `evidence_cutoff = 2026-09-24`,
  `served_cutoff_utc = 2026-09-24T23:59:59.999999999Z`, `bridge_valuation_date = 2026-10-15`,
  `snapshot_date = 2026-09-24`, bulk archive etag `8e09f7f4e3577b361c2bcf09f9edab6f-27`;
* `attestation.transport = CLOUDFLARE_SERVICE_BINDING`,
  `attestation.binding = ZION_FINANCIAL_QUERY`, caller `dcf-valuation-engine`,
  `authenticated_via = SERVICE_CREDENTIAL`.

The valuation date and the evidence cutoff are therefore separately named on the receipt: a
September 24 snapshot is never presented as though it contained all information available on
October 15.

Evidence states across the three filers (live): Apple and Microsoft each 6 `REPORTED` +
2 `REVIEWED_ABSENT` (`noncontrolling_interests`, `preferred_equity` — absent with the candidate
concepts reviewed and named); Alphabet 8 `REPORTED`. No claim was zeroed to fill a gap, and
every `REPORTED` claim carries its own `available_at` filing date.

### 10.3 Priority 2 — the cutoff convention, measured against real filings

The live archive has a filing dated **2026-07-31**, so the rule was measured on that day rather
than on a synthetic one. Same route, same release, six cutoffs:

| Requested `as_of` | `day_complete` | Apple `cash` claim | `available_at` |
| --- | --- | --- | --- |
| `2026-07-30` (day before) | true | 45,572,000,000 (period 2026-03-28) | 2026-05-01 |
| `2026-07-31` (date-only) | true | **39,544,000,000 (period 2026-06-27)** | **2026-07-31** |
| `2026-07-31T12:00:00Z` (intraday) | false | 45,572,000,000 (period 2026-03-28) | 2026-05-01 |
| `2026-07-31T20:00:00Z` (16:00 New York) | false | 45,572,000,000 (period 2026-03-28) | 2026-05-01 |
| `2026-08-01T02:00:00Z` (next UTC day) | true | 39,544,000,000 (period 2026-06-27) | 2026-07-31 |
| `2026-08-01` (date-only) | true | 39,544,000,000 (period 2026-06-27) | 2026-07-31 |

A filing dated the cutoff day is included exactly when that UTC day has ended, and a request
inside the filing day falls back to the earlier filing instead of assuming an intraday
acceptance time. The `20:00Z` row is the UTC-versus-New-York boundary: 16:00 in New York is
after the filing was accepted in practice, and it is still excluded, because the contract is
deliberately conservative rather than claiming exact intraday availability. Repeated identical
requests returned byte-identical claims (`sha256 03c1044f…` three times).

Boundaries observed on the same route: a cutoff after the pinned release ceiling is refused
(`2026-10-14` and `2026-09-25T00:30:00Z` → **422 `CUTOFF_EXCEEDS_SOURCE_RELEASE`**), so a
source archive older than the requested date cannot be silently served as if it were current.

### 10.4 Priority 4 — refusals, substitution and isolation, all live

| Probe | Result |
| --- | --- |
| No credential | **401 `UNAUTHORIZED`** |
| Wrong bearer | **401 `UNAUTHORIZED`** |
| Service credential naming an unapproved caller | **403 `SERVICE_CALLER_NOT_PERMITTED`** |
| Approved service credential (`dcf-valuation-engine`) | **200** |
| `recipient=automated_agent` | **403 `RECIPIENT_NOT_PERMITTED`** |
| Unknown query parameter | **400 `INVALID_PARAMETER`** |
| Malformed date (`2026-9-24`) | **400 `INVALID_AVAILABILITY_CUTOFF`** |
| Wrong engine release pin | **409 `SOURCE_VERSION_CHANGED`** |
| Wrong companion release pin | **409 `SOURCE_RELEASE_CHANGED`** |
| Foreign `Origin` on the DCF write | **403 `Cross-site writes are not allowed.`** |
| Malformed CIK at the DCF route | **400** |
| DCF request with a bad engine pin | **503** wrapping the internal **409 `SOURCE_VERSION_CHANGED`** |
| Bundle with one attested page edited | **400** `evidence attestation mismatch; caller-supplied bundle rejected` |
| Bundle with a forged attestation | **400** `evidence attestation mismatch; caller-supplied bundle rejected` |
| Bundle with an edited *derived* float, genuine attestation | **201**, and the valuation is recomputed from the attested pages: enterprise value and per-share identical to the untampered run (1,678,931,860,843.83 / 119.21703451950214), so the edit is ignored rather than trusted |

The research export ran through the library identity that saved it:
`GET /api/equity-claims/bridges/<id>/export/json` → **200**,
`Content-Disposition: attachment; filename="AAPL-equity-claims-<id>.json"`, carrying CIK,
both release identities, member digests, `snapshot_date`, `evidence_cutoff`,
`served_cutoff_utc`, `cutoff_policy`, `bridge_valuation_date`, enterprise and equity values,
per-share, the unresolved advisory list and the scenario set. A second library identity and an
anonymous caller both receive **404** for the same record.

Environment separation was re-checked from the deployment configuration itself:
`wrangler deploy --dry-run` on the default (production) environment lists `ZION_VALUATIONS` and
`ZION_DATASET_CATALOG` and **no** `ZION_FINANCIAL_QUERY`; the same command with `--env staging`
lists `ZION_FINANCIAL_QUERY (zion-financial-serving-v2-thin-staging)`. No production binding,
route or publication pointer was changed by this work.

### 10.5 Test environments

* DCF: `.venv/bin/python -m pytest -q` → **808 passed, 10 subtests passed**.
* Zion: `python3 -m pytest tests/unit/test_equity_claims.py tests/unit/test_equity_claims_api.py
  tests/unit/test_sec_history_api.py tests/unit/test_dataset_registry.py -q` → **80 passed**,
  plus `tests/unit/test_dev_harness_config.py` → **4 passed**.
* One real defect was found by the DCF suite and fixed rather than worked around:
  `tests/test_worker_bundle.py` failed because `app.py` imports `bottom_up_capm` and
  `scripts/embed_assets.py` did not bundle it, so the CAPM route would have raised
  `ImportError` inside Workerd. `bottom_up_capm.py` is now in `module_names`, the bundle was
  rebuilt, and the suite is green.

### 10.6 What this still does not establish

* Nothing is deployed. §7 stands unchanged: no staging Worker version was uploaded and no
  environment secret was set, so "works in local Workerd" is not "works in staging".
* The Zion route is still pointed at a pinned weekly snapshot whose ceiling is
  `2026-09-24T23:59:59.999999999Z`. A valuation dated later than that is refused today; making
  October valuations possible means publishing a newer immutable release, not relaxing the
  cutoff.
* `available_at` comes from the Company Facts `filed` date, which carries no acceptance time.
  The route's conservative rule is the contract's answer to that; an acceptance-time-backed
  point-in-time signal would need filing headers or the SEC index and is not implemented.

## 11. Private staging: the Zion Worker is deployed and verified; the DCF side is blocked

### 11.1 What was deployed

| Item | Value |
| --- | --- |
| Worker | `zion-financial-serving-v2-thin-staging` |
| Candidate version | `b193fa48-773b-44e9-aeca-d529d68b5a1f` (uploaded from `codex/private-existing-financials` @ `a46a6db`) |
| Activated | 2026-10-15T22:40:46Z at 100%, message `Promote companion-source claims route to staging` |
| Previous active version (rollback target) | `3361eacb-877f-4a6b-aa8e-479062d4f555` |
| Rollback command | `cd {zion}/deploy/cloudflare-query && npx wrangler versions deploy 3361eacb-877f-4a6b-aa8e-479062d4f555 -c thin/wrangler.jsonc -y` |
| Preview URL used for pre-activation verification | `https://b193fa48-zion-financial-serving-v2-thin-staging.scswitzer.workers.dev` |

Nothing was deployed to production, no production binding or publication pointer was touched,
and the Zion Worker carries the same single secret it already had
(`ZION_PRIVATE_API_TOKEN`); no staging credential was created or rotated.

The candidate was verified on its own preview URL *before* activation, so the promotion was
gated on the checks passing: `/healthz` 200, `/v1/capabilities` 200, the claims route 200 for
Apple, Microsoft and Alphabet, `/private/v1/financial-history` 200 with the pinned engine
release, and the refusals (no credential 401, wrong engine pin `SOURCE_VERSION_CHANGED`,
cutoff beyond the release ceiling `CUTOFF_EXCEEDS_SOURCE_RELEASE`).

### 11.2 Live verification of the deployed staging route

Against the main staging origin `https://zion-financial-serving-v2-thin-staging.scswitzer.workers.dev`:

| Check | Result |
| --- | --- |
| `/healthz` | 200 |
| `/private/v1/equity-claims` Apple `0000320193` | 200, 6 `REPORTED` + 2 `REVIEWED_ABSENT`, `DATE_ONLY_END_OF_DAY_UTC_V1` |
| … Microsoft `0000789019` | 200, 6 `REPORTED` + 2 `REVIEWED_ABSENT`, `DATE_ONLY_END_OF_DAY_UTC_V1` |
| … Alphabet `0001652044` | 200, 8 `REPORTED`, `DATE_ONLY_END_OF_DAY_UTC_V1` |
| Engine / companion release identity | `b39a670b…` / `f4f81944…`, members `73a86c6a…` Apple (equal engine and companion digests) |
| `/private/v1/financial-history` (Microsoft, annual revenue) | 200, 7 observations, release `b39a670b…` — unchanged, so the promotion did not regress the existing route |
| No credential | 401 |
| Wrong engine pin | 409 `SOURCE_VERSION_CHANGED` |
| Cutoff past the source ceiling | 422 `CUTOFF_EXCEEDS_SOURCE_RELEASE` |
| Service caller not on the allowlist | 401 |

Edge propagation was visible: the preview URL answered the claims route immediately after
upload, while the main origin returned 404 for roughly 45 seconds after activation and then
answered 200 — the same lag the repository's `EDGE_VERSION_NOT_PROPAGATED` guard exists for.

### 11.3 The DCF staging Worker: exact prerequisites, not deployed

The DCF staging Worker (`dcf-valuation-engine-staging`, workers.dev, D1 `dcf-valuations-staging`)
was **not** deployed, because the chain cannot complete there and a half-configured promotion
would advertise a working integration that cannot finish. Evidence, from the deployment
configuration and the Workers themselves:

| Requirement | State |
| --- | --- |
| `ZION_FINANCIAL_QUERY` → `zion-financial-serving-v2-thin-staging` binding | present in `env.staging` |
| Zion staging accepts a private bearer | yes (verified above) |
| Zion staging accepts the scoped service credential | **no** — the Worker has no `ZION_SERVICE_TOKEN` secret, and the DCF consumer presents only the service credential for claims (`authorize()` therefore answers `SERVICE_AUTH_UNCONFIGURED`/401) |
| DCF staging secrets | only `RECORD_SALT` is set: **`ZION_HISTORY_TOKEN` and `ZION_SERVICE_TOKEN` are missing**, so the attested native-history leg cannot be verified and the claims leg cannot authenticate |
| Benchmark assumptions leg (`source: 'zion'`) | **not configured**: `env.staging` sets neither `ZION_BENCHMARK_BASE_URL` nor `ZION_BENCHMARK_TOKEN`, and `resolve_benchmark_selections` refuses with "Zion benchmark provider is not configured in this runtime." Neither the deployed benchmark origin nor its credential is available to me |
| `equity_claims_bridges` table | migration `0009_equity_claims.sql` has not been applied to the remote staging D1 |

The remaining steps are therefore mechanical but need one operator decision and one value only
Cloudflare holds:

1. `ZION_SERVICE_TOKEN` must be set to the **same** staging-only value on both Workers, and
   `ZION_HISTORY_TOKEN` on the DCF staging must be the staging private token that the Zion
   Worker already holds as `ZION_PRIVATE_API_TOKEN` (the private token is write-only in
   Cloudflare, so it has to come from the operator).
   ```
   cd {zion}/deploy/cloudflare-query
   npx wrangler secret put ZION_SERVICE_TOKEN -c thin/wrangler.jsonc      # new staging-only value
   npx wrangler secret put ZION_SERVICE_TOKEN -c {dcf}/wrangler.jsonc --env staging  # same value
   npx wrangler secret put ZION_HISTORY_TOKEN -c {dcf}/wrangler.jsonc --env staging  # = staging private token
   ```
2. Decide the benchmark leg for staging: set `ZION_BENCHMARK_BASE_URL` (the deployed DDFI
   benchmark Worker origin) and `ZION_BENCHMARK_TOKEN` in `env.staging`, or use the `release`
   source for staging selections.
3. `npx wrangler d1 migrations apply dcf-valuations-staging --env staging --remote`
4. `npx wrangler deploy -c wrangler.jsonc --env staging`, then verify with the public routes
   (`GET /api/equity-claims/status`, `POST /api/financials` with `provider=zion_history`) and
   one full bridge scenario, exactly as §10 did locally.

Re-run this document's §10 checks against the deployed staging pair after those four steps;
until then the milestone's staging criterion is met for Zion and open for the DCF.
