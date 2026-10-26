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
observation earlier than publication, an observation later than retrieval, a bare
string in place of structured evidence, and (for `SERVER_LAST_MODIFIED`) a date that
is not the server header's date for the exact bytes.

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
- The releases directory in this checkout is empty, so a local
  `coverage_catalog()` here would list nothing at all.
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

## 6. What would change this answer

| Action | Owner | Acceptance condition | Needs authorization |
| --- | --- | --- | --- |
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
