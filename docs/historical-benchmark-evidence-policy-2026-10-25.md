# Historical benchmark evidence policy — 2026-10-25

This fixes one question: **which historical benchmark requests does Zion support, and
why does release-root historical selection fail closed?** It records the policy that
`valuation_benchmarks.py`, `app.py` and the 2026-10-22 evidence work already implement.
It changes no code and no data.

Status vocabulary: **verified now** (command or probe run 2026-10-25), **recorded**
(earlier receipt/doc; not re-run), **unverified**.

## 1. Two benchmark sources, two different gates

`app.py::resolve_benchmark_selections` accepts exactly two `source` values.

| Source | What it reads | Gate before data | Configuration state |
| --- | --- | --- | --- |
| `zion` | `zion-ddfi-benchmark-staging` through the `ZION_BENCHMARK_QUERY` binding (or a URL + token) | binding/URL **and** token present, else `Zion benchmark provider is not configured in this runtime.` | recorded as configured on staging and production (`docs/data-gap-repairs-2026-10-22.md` §4; published 2026-10-15). Unauthenticated probe returns 401. **Not re-probed here with credentials.** |
| `release` | local Damodaran assumption releases under `DAMODARAN_RELEASE_ROOT` | root set, else `Damodaran releases are not configured in this runtime.` | **verified now:** none of the six wrangler configs in this repo (`wrangler.jsonc`, `wrangler.production.jsonc`, `wrangler.dev.jsonc`, `wrangler.verify.jsonc`, `deploy/security-funnel/wrangler.jsonc`, `deploy/valuation-completion/wrangler.jsonc`) sets `DAMODARAN_RELEASE_ROOT`. |

The Worker bundle contains no release directory, so the variable is the only way the
deployed path can find releases. Repo absence is not proof of runtime absence (a var
could be set out-of-band); see §4 for what the live probe could and could not settle.

## 2. Why `release` + `historical` fails closed — three independent gates

1. **Runtime configuration.** Without `DAMODARAN_RELEASE_ROOT` the request is refused
   before any release is opened.
2. **Reviewed evidence.** A `published_at` on its own is not evidence — a hand-edited
   manifest could carry any date. `publication_status()` requires a structured
   `publication_evidence` whose `method` is one of `SERVER_LAST_MODIFIED`,
   `PUBLISHER_STATED`, `FIRST_OBSERVED` (`PUBLICATION_METHODS`). Anything else returns
   `NO_REVIEWED_PUBLICATION_EVIDENCE` and `load_benchmark` raises
   `Benchmark vintage unavailable at historical cutoff: NO_REVIEWED_PUBLICATION_EVIDENCE`.
   The remaining refusal reasons are `NO_PUBLICATION_DATE`,
   `INCOMPLETE_PUBLICATION_EVIDENCE`, `UNPARSEABLE_PUBLICATION_EVIDENCE`,
   `EVIDENCE_PRECEDES_PUBLICATION`.
3. **Cutoff.** Even with valid evidence, `published_at` after the requested `as_of`
   raises `... published after cutoff`. A vintage is never served before its
   publication.

`validate_publication()` additionally refuses a non-https source URL, an
observation earlier than publication, a publication date after the recorded download, a
bare string in place of structured evidence, and (for `SERVER_LAST_MODIFIED`) a date
that is not the server header's date for the exact bytes.

**Corrected 2026-10-25.** The loader used to require `observed_at <= retrieved_at`.
That conflated two independent collection events (the ingest download and the header
re-check that produces `observed_at`), and it rejected all five evidenced entries in the
real catalog. It is removed; the remaining ordering gates are the meaningful ones.
`download_retrieved_at` and `retrieved_at` are now both accepted as the disclosed
download time. See §8.

## 3. What evidence actually exists

Recorded in `docs/benchmark-publication-evidence-2026-10-22.md` (curation receipt
`PREPARED_NOT_PROMOTED`). Seven local releases; five have a server `Last-Modified`
bound to the exact source bytes:

| Dataset | `published_at` | Basis | Historical availability |
| --- | --- | --- | --- |
| industry_betas | 2026-04-12 | server Last-Modified | AVAILABLE_FROM_PUBLISHED_AT |
| cost_of_capital | 2026-01-12 | server Last-Modified | AVAILABLE_FROM_PUBLISHED_AT |
| implied_erp | 2026-01-08 | server Last-Modified | AVAILABLE_FROM_PUBLISHED_AT |
| multiples | 2026-01-08 | server Last-Modified | AVAILABLE_FROM_PUBLISHED_AT |
| reinvestment | 2026-01-08 | server Last-Modified | AVAILABLE_FROM_PUBLISHED_AT |
| margins | — | no preserved record for these bytes | UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED |
| country_risk | — | no preserved record for these bytes | UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED |

**This is the correction to the 2026-10-24 audit's phrasing.** The audit said the
manifests carry `publication_evidence: null` "and no `publication_evidence.json`
catalog exists beside them". Both are true of the *runtime release root* — but the
evidence work was done: the curated catalog exists as the review copy
`evidence/benchmark_publication_evidence.json` (8,141 bytes, `schema_version`
`damodaran-publication-evidence-v1`, 7 entries, 5 with evidence). The gap is
**promotion**, not collection:

- `load_publication_evidence(root)` reads `<root>/publication_evidence.json` only.
- The DCF registry release root is `/Users/.../Documents/Secret/data/ddfi/registry/assumption_releases`
  (sibling repo; `tests/test_zion_benchmark_chain.py` resolves it as `parents[2]`). **Verified
  2026-10-25:** 8 releases, every `index.json` entry carrying a `published_at`, every
  `manifest.json` carrying `publication_evidence: null`, and **no**
  `publication_evidence.json` beside them. So local historical release-root selection is
  fail-closed for every one of the 8, while current selection serves
  (`cost_of_capital` → `0.09344048072400105`, `CURRENT_EXPLICIT_SELECTION`).
- The curated catalog exists at `evidence/benchmark_publication_evidence.json` and, as a
  full release root with its catalog, at
  `artifacts/zero-subscription-integration/damodaran-releases/`. Its release ids
  (`6a7510cf…` for `cost_of_capital`) are **not** the ids of the rebuilt registry
  releases (`11c1e6bb…`), so copying it beside the registry would resolve nothing.
- The curator (`scripts/build_benchmark_publication_evidence.py`) writes the catalog
  beside the releases; the receipt records the work as `PREPARED_NOT_PROMOTED`.

Evidence dates are never invented. `margins` and `country_risk` therefore refuse every
historical cutoff, and that is the correct behaviour: no server-timestamped record
exists for those exact bytes anywhere in the preserved stores.

## 4. Live probe, 2026-10-25 (read-only, no credentials)

`GET https://dcf-valuation-engine.scswitzer.workers.dev/api/assumptions/damodaran/<synthetic-64-hex>?subject=Software&measure=wacc&mode=current`

→ `401 {"code":"OWNER_BENCHMARK_AUTH_REQUIRED"}`

Two things this establishes and one it does not:

- Establishes: anonymous access to private benchmark inputs is denied (re-verified),
  and owner authorization precedes every configuration or release check.
- Does **not** establish: whether `DAMODARAN_RELEASE_ROOT` is set at runtime. Auth
  short-circuits before that branch is reached, so the runtime state stays
  **unverified** — only the repo-level absence in §1 is verified. Confirming it needs
  the owner credential and is not attempted here.

## 5. Support matrix — the policy answer

| Request | Supported? | Conditions |
| --- | --- | --- |
| `source: zion`, `mode: current` | Yes | binding + token configured; owner authorized |
| `source: zion`, `mode: historical` | Yes, subject to the provider's own availability | same configuration; Zion decides whether the vintage was available at that date |
| `source: release`, `mode: current` | Yes where a release root is configured (local/dev, tests) | `DAMODARAN_RELEASE_ROOT` set and release present; `mode: current` cannot be backdated (`Current benchmark selection cannot be backdated.`) |
| `source: release`, `mode: historical` | **Only for the five evidenced vintages, and only where the catalog sits beside the release root** | gate 2 and gate 3 of §2 must both pass; `margins` and `country_risk` refuse at every cutoff |
| `source: release` in the deployed Worker | **Effectively unavailable** until R5(c) | no repo config sets the root; anonymous probes cannot distinguish "unset" from "unauthorized" |

So "historical release-root selection fails closed" is not a bug and not an evidence
shortage. It is the intended three-gate design, currently compounded by the release
root not being part of the deployed bundle.

## 8. Resolution defect found and fixed (2026-10-25)

Even where the catalog *is* present, historical selection refused every evidenced
release. Two deterministic defects, both verified against the real artifacts by running
`load_benchmark` directly:

| Defect | Evidence | Fix |
| --- | --- | --- |
| Producer/consumer field mismatch: the curator writes `download_retrieved_at`, the loader read `retrieved_at`, so `_instant(None)` raised and the entry failed closed | every entry in `evidence/` and `artifacts/…/damodaran-releases/publication_evidence.json` has `download_retrieved_at` and no `retrieved_at` | loader accepts either name; a catalog with neither still fails closed |
| Impossible ordering: `observed_at <= retrieved_at` required, but the catalog records the 19:28Z ingest download and a 20:50Z header re-check of the same bytes | 5/5 evidenced entries rejected even after the key fix | ordering check removed; publication-before-retrieval and publication-before-observation both remain |

Measured on `artifacts/zero-subscription-integration/damodaran-releases`, cutoff
2026-09-01: **before 0/7 resolved; after 5/7 resolve** (`HISTORICAL_PUBLISHED`),
`margins` and `country_risk` still refuse. No gate was weakened: the date must still be
the server `Last-Modified` of the exact bytes, and a publication date after the recorded
download is still refused.

PR: [#82](https://github.com/Scott-Switzer/DCF-stock-valuation-Engine/pull/82), stacked on
#80, 51 focused tests and 144 benchmark/valuation/coverage tests passing locally.

## 9. What would change this answer

| Action | Owner | Acceptance condition | Needs authorization |
| --- | --- | --- | --- |
| Re-run the curator against the **current registry release bytes** so the catalog's release ids match | data | `coverage_catalog(registry_root)` lists 8 releases and 5 available; `load_benchmark` resolves the registry `cost_of_capital` historically | data write (catalog generation) — not performed |
| R5(c): ship a release root with the catalog beside it, or serve releases from a bound store, and read the catalog from that same root | DCF + data | deployed historical request for `cost_of_capital` at a cutoff after 2026-01-12 returns `HISTORICAL_PUBLISHED`; a cutoff before it returns "published after cutoff" | deploy + release contract change |
| Acquire server-timestamped evidence for `margins` and `country_risk` exact bytes | data | `publication_status` returns `available: true` for those two releases; `coverage_catalog()` shows 7/7 | new acquisition (fetching from the provider) |
| Mirror this policy in the owner-facing docs/UI | DCF web | the Data workspace states that historical release selection is limited to evidenced vintages | none (docs) |
| Re-verify runtime configuration | ops | `/api/assumptions/damodaran/...` with owner credential returns a release, not "not configured" | owner credential use |

Until the first row lands, the honest statement to any consumer is: **benchmark
assumptions can be selected for the current vintage where a release root or the Zion
provider is configured; historical selection is available through Zion, and through
release data only for the five evidenced vintages.** No historical benchmark answer is
point-in-time certified, and none of this makes a valuation decision-grade.

## 7. Verification behind this document

- Read: `valuation_benchmarks.py` (`publication_status`, `validate_publication`,
  `load_publication_evidence`, `resolve_publication`, `load_benchmark`),
  `app.py::resolve_benchmark_selections` (lines ~1000-1040),
  `tests/test_valuation_benchmarks.py`, `tests/test_benchmark_publication_evidence.py`.
- Ran: `ls` of the release root and of `evidence/`; a JSON summary of the review copy
  — `damodaran-publication-evidence-v1`, 7 releases, **5** with
  `method: SERVER_LAST_MODIFIED` and dates 2026-04-12 / 2026-01-12 / three on
  2026-01-08, **2** (`margins`, `country_risk`) with `published_at: null` and no
  evidence; `grep` for `DAMODARAN_RELEASE_ROOT` across the six wrangler configs
  (none); one anonymous HTTPS probe (401).
- Not run: authenticated benchmark selection, any release fetch, the coverage
  preflight script (it needs the populated release root).

## 10. Candidate catalog against the current registry (2026-10-25)

The 5/7 figure in §3 and §8 was measured on the older
`artifacts/zero-subscription-integration/damodaran-releases` set. Running the existing
curator against a **byte copy of the current registry** (8 releases) gives **8/8 evidenced,
all byte-identical**, candidate catalog
`artifacts/benchmark-evidence-candidate-2026-10-25/releases/publication_evidence.json`
(receipt and `candidate-report.json` beside it, status `PREPARED_NOT_PROMOTED`).

Each dataset resolves `HISTORICAL_PUBLISHED` at a cutoff after its `published_at` and is
refused the day before. Negative controls all hold: altered source byte → integrity
mismatch, removed catalog entry → `NO_REVIEWED_PUBLICATION_EVIDENCE`, renamed release
directory → identity mismatch. The rebuilt `country_risk_premiums` (July 2026 bytes) and
`industry_aggregates` do have preserved server timestamps, unlike the January vintages
described earlier.

Disclosed deviation: registry releases carry no `retrieval.json`, so the curator could not
read the download time it requires. In the copy only, `retrieval.json` was written from
each manifest's recorded `lineage.retrieved_at`. The curator should fall back to that
field when the file is absent; that small change was not made here.

**Catalog regeneration alone is not sufficient for deployed historical coverage.** Still
required: (a) the catalog (or a regenerated one) placed in the canonical root, (b) a
decision on `retrieval.json` vs the curator fallback, (c) a runtime release root
(`DAMODARAN_RELEASE_ROOT` is unset in all six wrangler configs), (d) deployment, and
(e) deployed acceptance. None of (a)–(e) was performed.
