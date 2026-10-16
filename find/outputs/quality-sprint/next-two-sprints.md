# Financial accuracy roadmap after the parity sprint

These are proposed acceptance gates, not shipped capabilities or newly verified coverage. Scope one provider contract and frozen reconciliation cohort before expanding public coverage. Keep all source periods, currencies, availability dates, units and missing reasons. Never fill an absent financial value with zero.

## Sprint 1: dated financial inputs that improve every valuation

| Order | Deliverable | Economic materiality / reuse | Cost / complexity | Acceptance gate |
|---|---|---|---|---|
| 1 | Quarterly and TTM statement packet contract | Very high / DCF, RV, research | Medium infrastructure cost; high accounting complexity | Reconcile a named 12-issuer cohort to filings; every issuer passes or has a specific gap. Derive discrete quarters from compatible YTD observations, handle 52/53-week years and restatements, and enforce filing availability. TTM = last annual + current YTD − comparable prior YTD only when scope/units/periods match. |
| 2 | Current ordinary shares and share-class reconciliation | Very high / market equity weights, bridge, RV | Low incremental acquisition where DEI facts exist; high semantic complexity | Separate dated ordinary outstanding shares, weighted-average basic EPS shares and diluted forecast shares. Reconcile split factors, classes/ADRs and issuance/repurchases for the same cohort. Never silently substitute an annual EPS denominator for current market capitalization. |
| 3 | Filing reconciliations and usable-coverage ledger | High / all methods | Low runtime cost; medium mapping/review cost | Publish counts by issuer AND method: discovered → parsed → inputs complete → accounting reconciled → independently valued → public-use permitted. Keep the historical 86/52/5/4 staging funnel separate from the 237-entry production index. Require a pre/post ledger showing newly usable issuers, not merely extra packets. |
| 4 | Public macro and filing evidence adapters | Medium / risk-free curve, scenario evidence, management guidance | Low serving cost; medium lineage/licensing work | Compact dated observations with source URL, retrieval time, publication time and revision/vintage. Management guidance is attributed guidance with period and units, not analyst consensus or a verified forecast. No private WRDS rows or derived restricted fields in public packets. |

The SEC APIs expose submissions and standardized entity-wide XBRL facts. Custom tags and company-specific dimensions need filing-level reconciliation; the existence of a companyfacts response does not establish a usable statement. Calendar frames can contain different fiscal start/end dates, so do not sum them blindly. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## Sprint 2: financing economics and forecast quality

| Order | Deliverable | Economic materiality / reuse | Cost / complexity | Acceptance gate |
|---|---|---|---|---|
| 1 | Cost of Capital 2.0 | Very high / every FCFF valuation | Medium data cost (rights-dependent); high model complexity | Use price × current ordinary shares for equity weights; identify book vs estimated market debt; expose a dated risk-free curve, issuer yield or documented spread estimate, ERP and tax-shield scenario separately. Compare 6 issuers to independently reproduced calculations. Fall back with labels when a yield is unavailable; historical interest/debt is never labeled a current market yield. |
| 2 | Forecast fade and stable-growth reinvestment | Very high / most operating companies | Low serving cost; medium implementation complexity | Explicit base/upside/downside growth, margin, reinvestment and dilution paths. For normalized terminal mode, reconcile reinvestment = growth / sustainable ROIC and terminal FCFF independently. Show terminal-value share and sensitivity; reject infeasible regimes. Explain that the 12-month target is conditional on the modeled bridge/share path. |
| 3 | One sector pilot, selected by verifiable data coverage | High / new usable company types | High accounting complexity; bounded pilot | Prefer a 2-issuer financial-institution equity/residual-income pilot if book equity, capital requirements and distributions reconcile; otherwise choose a 2-issuer REIT pilot with issuer-reconciled FFO/AFFO/NAV. Do not add all sectors at once. Keep industrial FCFF applicability checks. |

Market-value weights and stable-growth reinvestment should be explicit assumptions, not a silent plug. Damodaran's project guidance discusses market equity, debt estimates and reinvestment tied to growth/return on capital; use it as a documented framework, not issuer-specific evidence. [NYU valuation guidance](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/project/prques.htm)

## Ordered sector backlog after those gates

1. Financial institutions: equity discounting, dividend capacity and residual income; reconcile common equity, regulatory capital and noncommon claims. High materiality, medium sector reuse, high complexity. Validate the cost-of-equity basis independently; do not discount equity cash flows at WACC. [Damodaran valuation framework](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm)
2. REITs: issuer-reconciled FFO, recurring capex, AFFO and asset-level NAV. High materiality within REITs, moderate acquisition cost and high reconciliation complexity. AFFO has no uniform definition; retain issuer-specific adjustments and avoid a universal EBITDA-to-AFFO shortcut. [Nareit AFFO](https://www.reit.com/glossary/adjusted-funds-operations-affo)
3. Regulated utilities: rate-base growth, allowed returns by jurisdiction, financing and maintenance/growth capex. High materiality, low reuse outside utilities, high filing/manual-review cost. Require dated regulator orders for allowed returns; a general national ROE assumption is insufficient. [FERC glossary](https://ferc.gov/industries-data/resources/public-reference-room/ferc-glossary)
4. Cyclical and high-growth variants: normalized midcycle margins/capex, loss-to-profit transition, dilution and longer explicit fade. High cross-company reuse but only after TTM/share and stable-growth gates.

## Infrastructure and product guardrails

- Profile provider stages before overlap. Python Workers currently use synchronous `run_sync` bridges; a thread-pool or native rewrite is not a demonstrated optimization. Prototype independent awaits in the actual Worker runtime before any concurrency PR, preserving one shared deadline and deterministic fallback order.
- Existing reviewed issuer classification already removes classification calls for covered names. Additional issuer-name reuse must match packet CIK and cited availability date. A miss must preserve current validation/fallback; no permissive ticker-only identity cache.
- Negative service caching must include immutable release identity and expiration/invalidation behavior. Do not cache a 404 across a new financial-source release merely to improve benchmarks.
- Keep market observations keyed by date/currency/security/source and distinguish retrospective current observations from genuine point-in-time data.
- Extend CI's frozen browser cohort as new methods arrive. Keep production monitoring read-only and separately scheduled; broaden a bounded cohort across source paths without saving synthetic research.
- Email verification/recovery is a separate adoption gate requiring enumeration-safe responses, single-use expiry-bound tokens, delivery tests and revocation tests. Do not bundle it into financial-model changes.
- Licensed research remains in an authorized private service with an explicit redistribution contract. Public source adapters and private datasets must not share a permissive export path.
