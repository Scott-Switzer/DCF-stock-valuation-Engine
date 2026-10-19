# Unified financial expansion — October 19, 2026

Working code now connects the existing Zion source API, terminal, MCP/Slack readiness path and DCF application. All deployments below target existing staging Workers. No production publication pointers, licensed data exports, purchases or new cloud resources were changed.

## What works in each interface

| Interface | Verified behavior | Limit |
| --- | --- | --- |
| Private source API | Readiness, pinned histories, 50-company filing-backed equity claims; source/member integrity and availability checked | Owner credential required; research eligibility is not trading readiness |
| DCF staging API | Signed-in screen, exact-release preparation, enterprise calculation and saved equity bridge for ABT and AP; existing 21 integration checks also pass | Standardized explicit research assumptions; no certified historical security-price join |
| DCF web screen | Existing `/screen` selects issuers, loads evidence and runs explicit enterprise scenarios | Per-share bridge remains a separate API operation |
| Installed Zion terminal | `zion research readiness` and new `zion claims` both return live pinned results | Claims are data retrieval, not an integrated terminal forecast command |
| MCP | New `query_valuation_readiness` backed by the same source API | Readiness only; no invented forecasts |
| Slack staging Worker | Explicit `/zion readiness ...` parser and owner REST → Slack Worker → MCP → source chain verified, five matching rows, auth/argument refusals | No actual Slack message sent; Slack delivery and valuation execution are not certified |

DCF staging: https://dcf-valuation-engine-staging-zion.scswitzer.workers.dev/screen

Slack command: `/zion readiness method=operating_dcf limit=5`.
MCP tool: `query_valuation_readiness` with `{"method":"operating_dcf","limit":5}`.

Terminal:

```sh
zion research readiness --method operating_dcf --limit 5 --format table
zion claims --cik 0000320193 --as-of 2026-09-24 \
  --release-id ac8f14de487eee6b78fd6c108e8611af8f326d864a162b00d5308f6c90abfd18 \
  --source-release-id 162c3745857617b185579b874a9adcf16e25a0a553ed4277080acdfbc474aebf
```

Credentials remain in the owner's existing local credential file or scoped Worker secrets. No token belongs in the command line, receipts or Git.

## Blockers resolved in code

- The enterprise model can consume one or two genuinely observed annual periods. It uses the latest reported annual revenue and EBIT. It never fills missing years; the conventional three-period DCF parser remains strict. Every bundle reports observed periods and conventional DCF eligibility. The form fallback now averages over observed periods, fixing the one-year 20% margin incorrectly displayed as 6.67%.
- Issuer aliases are independently verified against authoritative SEC submissions. Current aliases remain explicitly ineligible for historical security/price joins; they are sufficient for a CIK-bound issuer research scenario. Wrong-issuer aliases still fail closed.
- Engine and companion pins are selections as well as assertions. Approved old releases remain selectable after expansion, with a live old-companion regression check.
- A new 50-member Company Facts manifest references the exact existing immutable SEC archive members. All 174,999,400 raw bytes were verified locally; only a 35,687-byte immutable manifest was uploaded. No duplicate raw objects or CURRENT pointer promotion. Bounded archive reads verify lengths, CRC and SHA against both manifests.
- Terminal claims retrieval and explicit MCP/Slack readiness reuse existing services. They do not introduce another research application, paid provider or LLM dependency.

## Measured expansion

| Result | Count |
| --- | ---: |
| Distinct issuers accounted for in enterprise cohort | 100 |
| Native histories loaded | 81 |
| Independently reconciled enterprise scenarios | 59 |
| Explicit blocked enterprise outcomes | 41 |
| Expanded companion members verified through the live claims API | 50 |
| Issuer common-share scenarios independently reconciled | 35 |
| Companion members blocked by their enterprise model/input stage | 15 |

The 100-company run uses the existing provider/model functions for 97 cases and local authenticated DCF API routes for three. Every source request is live; this is **not 100 hosted API valuations**. Separate hosted authenticated tests for ABT and AP returned HTTP200 for screen/preparation/calculation and HTTP201 for the saved bridge; they match the independently reconciled cohort. AP retains its single 2020 annual period explicitly, so this is not a claim of fresh annual financials.

All 59 use a deliberately common research scenario: valuation date October15, evidence cutoff September24, five annual growth rates of 5%, terminal growth2%, terminal ROIC15%, and pinned NYU Total Market (without financials) references. These are explicit benchmark/forecast assumptions, not company observations or issuer-specific forecasts. They are not investment recommendations, current market prices or validated historical backtests. No missing financial inputs were replaced with assumptions or zero.

The claims receipt pins the exact full enterprise input receipt by SHA256. A final independent code review found no blocking issues.

The 35 bridges use the existing claims mapper and equity bridge, with an independent 40-digit Decimal bridge reconciliation. No caller preferred-conversion assumptions were added. Unresolved claims cannot become a verified receipt. Issuer-level common share counts are not certified class-specific tradable price denominators.

Enterprise refusals remain visible: 19 negative terminal-FCFF cases, 12 missing verified annual revenue histories, six missing current ticker aliases, two missing EBIT observations, one nonpositive revenue case and one missing source-term case. Negative-FCFF cases require a justified turnaround scenario or a different suitable model; overriding the guard would not resolve them correctly.

## Reproduction and evidence

```sh
.venv/bin/python scripts/verify_usable_cohort.py --size 100 \
  --scenario-industry 'Total Market (without financials)' --scenario-date 2026-10-15 \
  --growth .05 --terminal-growth .02 --terminal-roic .15 \
  --output /tmp/enterprise-cohort-new.json

.venv/bin/python scripts/verify_claims_cohort.py \
  --enterprise-receipt /tmp/enterprise-cohort-new.json \
  --source-manifest /path/to/verified/archive-reference-release/manifest.json \
  --output /tmp/claims-cohort-new.json
```

Outputs must be new files. The reference manifest and publication receipt remain in `/Users/scottthomasswitzer/Documents/Secret/artifacts/sec-companyfacts-cohort-2026-10-19/`. Full enterprise receipt is local at `/tmp/expanded-sec-cohort-20261019-final.json`. The committed compact receipt retains immutable benchmark references while excluding private benchmark numeric observations/payloads.

Receipts under `docs/receipts/`: `expanded-enterprise-cohort-2026-10-19.json`, `expanded-claims-cohort-2026-10-19.json`, `expanded-staging-e2e-2026-10-19.json`, `hosted-screen-expansion-2026-10-19.json`, `slack-readiness-chain-2026-10-19.json`, `terminal-claims-2026-10-19.json`, `approved-original-companion-2026-10-19.json`.

## Tests, commits and deployments

- DCF full suite: **996 passed, 10 subtests passed**, one pre-existing warning; focused regression suite55passed; Ruff and diff checks passed.
- Zion claims/terminal focused suite83passed; source publisher/claims/archive suite99passed. Latest full source run: **1,195 passed, 3 skipped, 11 setup errors** from the pre-existing absent `benchmark` pytest fixture. This is not a fully green source suite.
- Gateway: MCP36tests, Slack55tests, TypeScript checks and deployment dry runs passed. Live owner-chain acceptance passed without posting a Slack message.
- DCF staging21checks passed after deployment. Additional signed-in hosted ABT/AP flows passed. Deployed DCF code9472f155ba774cfac6ee50ad605bc78f036f64f7, Worker version0af82ea7-7c50-492c-8064-83c123bded94.
- Source thin staging versionff3ad9c9-9a0c-408d-bb4b-b1dd17692477; MCP versione85907f2-3a2f-48b3-a558-ec165adf6c23; Slack version017a43b7-4b93-4ea8-8414-60e345ec6d49.
- DCF commits: d8eb298, fd6ecb4, 9472f15. Source/terminal: c5416ba, f873899, 92b9e83. Gateway isolated worktree: a65dc93, 1fa04b4. All commits local; no public Git publication.

Remaining boundaries: actual Slack transport acceptance; direct valuation orchestration in terminal/Slack; the 41 explicit model/input/identity refusals; class-specific security/corporate-action reconciliation; historical backtest revalidation; and benchmark redistribution review. Current API success does not remove these requirements. Concurrent source readiness/sector edits were preserved.
