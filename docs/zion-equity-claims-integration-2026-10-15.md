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
route would ship a broken endpoint.

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
| `scripts/validate_equity_bridge.py` | New independent balance-level validation (Priority 3). |
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
**788 passed, 10 subtests passed in 16.44s** (773 before this work).

## 7. Priority 5 — staging deployment: not performed

Deliberately stopped at the deployment boundary. Deploying this route now would publish
the `SOURCE_CONTEXT_INVALID` defect to staging, and the repair choice in §4 changes what
the release pin attests to — both are decisions for the operator. No secret was set, no
version was uploaded, no route was changed, and no production credential was retrieved.

Minimum operator action once the repair is chosen:

1. Apply the repair and re-run the authorization matrix above; the last row must become
   `200` with real claims for each planned filer.
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
