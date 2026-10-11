# CUIG DDM and Relative Valuation alignment

Reference: the user-supplied CUIG Valuation Template Fall 2026 workbook. It is a blank template; it contains no completed real-company valuation. These sheets were read without alteration or redistribution. Only formula text used in reconciliation is included in the repository.

## Dividend discount model

| DDM worksheet | Engine |
|---|---|
| E17 and F18:J18 | Latest total annual **common** cash dividends × five individually editable annual growth rates |
| C25 | Explicit required return on equity; 7% sample assumption |
| F30:J31, C36 | Present value of years one through five, end-of-year equity discounting |
| G32:J32, I36 | In 12 months, exclude the first dividend and discount the remaining dividends one fewer period |
| C40:C44 | Year-five dividend × (1 + perpetual dividend growth) / (equity return − growth), discounted five periods |
| I43:I44 | Same terminal equity value, discounted four periods |
| C49/C52, I49/I52 | Equity value divided by diluted shares, without an enterprise-debt deduction |

The workbook's dividends are total distributions because it divides aggregate equity value by shares at the end. The application labels this explicitly to avoid interpreting dividends per share as company-wide dividends. Shares carry forward unless an explicit 12-month override is provided. Buybacks and preferred dividends are excluded. Non-dividend companies cannot use this growth-from-current-dividends model; future initiating-dividend or payout-ratio models need separate implementation. Required return must exceed terminal growth and all numerical results must be finite.

Linked revenue, earnings and book-value rows in DDM provide context in the spreadsheet but do not drive its dividend discount calculation. They are not required solely to calculate DDM. Company details can carry from DCF; dividends remain blank until entered from a verified source.

## Relative valuation

| Relative Valuation worksheet | Engine |
|---|---|
| C6:G9 | Four editable comparable-company rows; the JSON API accepts up to twenty unique peers |
| C10:G10 | Arithmetic mean of valid peer multiples |
| C12:E12 | Mean EV multiple × target year-one revenue/EBITDA/EBIT, converted from enterprise to common equity |
| F12:G12 | Mean P/E or P/B × target year-one common-attributable earnings/book equity, divided by diluted shares |
| C13:G13 | Select appropriate methods; template default EV/Revenue, EV/EBITDA and P/E |
| C15 | Equal-weight mean of selected implied forward prices |
| J20 | Banks, insurers and investment firms may select only P/E and P/B |

Target year-one forecasts can be carried directly from a completed DCF, mirroring the workbook links. Historical and forward denominators are editable. The P/B forecast is explicit: the user can enter the workbook's DDM-linked or DCF-linked book value rather than silently selecting an unrelated balance.

Intentional differences: current target trading EV multiples use **market** common equity plus explicit claims, rather than the workbook's DCF-derived enterprise value in C5:E5. This avoids circularity when comparing observable trading multiples. The enterprise-to-common-equity bridge includes preferred and noncontrolling claims and other nonoperating assets in addition to net debt. Negative implied common equity is displayed before a zero share-price floor. Missing/nonpositive peer multiples are excluded with per-metric counts and warnings; a selected method requires a positive target forward denominator and at least one positive valid peer multiple. Unknown, nonfinite or mismatched-unit input is rejected rather than becoming zero. Peer dates and references are explicit.

Relative valuation supplies a year-one forward target, not a present discounted intrinsic value. Accordingly `intrinsic_value` and `upside` are null for this method. `target_price_12m` and `upside_12m` hold the forward result. P/E and P/B already imply common equity, so debt is not deducted twice. Current shares/claims carry into the target as in the template; projected capital structure remains a review item. Use consistent peer trailing/forward definitions and common-attributable denominators.

## Verification and storage

`tests/test_suite_reconciliation.py` independently interprets the supplied formula text in `tests/fixtures/cuig-suite-formulas.json`. It compares DDM C54/I54 across two dividend-growth paths and RV C15/per-method prices across two method selections. The restricted evaluator supports arithmetic, PV, SUM, AVERAGE, IF, ISBLANK and COUNTIF; it does not execute arbitrary formulas and is not native Excel recalculation.

Synthetic defaults: DDM today $23.2899272023 and 12-month $23.8702221065; relative target $26.8783333333. These demonstrate formula behavior, not real-company fair values. JSON and CSV preserve assumptions/results/provenance. Public calculations store `method` and model version in private D1. The migration retains prior DCF rows and allows null present value for relative valuation; sentiment research must group by method/horizon and exclude synthetic submissions.

DCF handoff leaves historical and forward P/B book equity blank: the DCF total book value does not establish common-attributable equity. Enter verified common book equity separately before selecting P/B. Imported peer availability dates and provenance survive editor submissions, including valuation-date changes.

## Explainable comparable-company analysis

Relative results retain the CUIG arithmetic mean and equal weighting across selected methods. They also report median multiples and their alternative implied share values, individual peer weights, raw implied prices and contributions, exclusions, and outlier flags. At least four valid peers are needed for the 1.5×IQR flag (inclusive quartiles); flagged observations remain included. Raw contributions sum before the common-equity value is floored at zero. No automatic winsorization occurs.

Automatically loaded ratios use the latest reported annual denominator, **not TTM and not forward analyst estimates**. Peer records preserve `denominator_basis`, `financial_period_end`, price date, financial/bridge/market provenance and source. The default `valuation_basis=cuig_forward` explicitly applies those ratios to the target's year-one forecast as a constant-multiple scenario. It is not represented as a matched forward comparison. Legacy manual peer records without basis remain `unspecified` and are disclosed.

`valuation_basis=matched_forward` requires every contributing peer ratio to be declared `forward_year_one`, with a future estimate-period date and the existing required source reference. Historical, unspecified or mixed inputs are rejected. These are user-supplied estimates; declaring the basis does not independently certify the provider forecast. Review fiscal-period alignment and accounting comparability.

Unreviewed `candidate` and `excluded` peers cannot contribute through the JSON calculation API or workbook. A browser inclusion marks the peer user-confirmed. Source basis controls are locked with sourced inputs; users must unlock them to override. P/E and P/B do not subtract enterprise claims; financial firms cannot contribute EV multiples. Readiness recognizes P/B and EV/EBIT as well as the three original starter metrics.

The workspace and standalone result provide expandable contribution tables. JSON exports retain the complete distribution. XLSX preserves the existing formula-driven target and includes basis/period/source columns; unreviewed peers are explicitly excluded from its formulas.
