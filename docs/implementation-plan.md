# CUIG DCF foundation

The user's October 6 request authorizes fixing the audited priorities and using the CUIG workbook as the DCF reference. Purpose: a polished, reproducible resume project with a future Zion/MiniBloomberg connection. Implement directly in the isolated recovered GitHub checkout. Other valuation methods remain future work.

## Calculation design

Match DCF - GGM rows 11–47 (revenue × annual drivers; EBIT less taxes plus D&A less CapEx and change in NWC), C61/C62/C67/C82 (today), and I52/I62/I67/I82 (12 months). Keep five explicit periods, diluted shares and decimal rates internally. Show end-of-period timing explicitly. Template is blank: verify formulas with synthetic, hand-reconciled inputs rather than claiming a real-company Excel match. Keep workbook unchanged.

Default terminal mode matches year-five FCFF grown at g. Offer explicit stable-growth ROIC/reinvestment normalization and terminal-value share. Forecast drivers are editable per year. The future equity bridge has editable year-one debt/cash/shares; default unchanged values are labeled. Preferred claims and noncontrolling interests deducted, other nonoperating assets added. Negative common equity is shown separately, common-share value floors at zero.

## Implementation sequence

1. Write regressions for rejected numeric/data inputs and the current-value/target distinction. Run them against old implementation.
2. Replace duplicated model calculations with one deterministic calculation and structured results. Validate all financial histories, fiscal years, currencies, driver arrays, and output finiteness.
3. Normalize providers behind a versioned JSON document; offline demo and manual input always work. Replace incompatible Edgar SDK path with the documented SEC companyfacts HTTP API. Preserve each metric's fact provenance and period. No silent zero substitutions. Market price/shares can be entered independently of SEC. Inspect Zion sources for future integration; keep keys server-side.
4. Rebuild Flask input/result views with locally served CSS/JS; local autocomplete, accessible percent inputs, preserved errors, sample mode, history/forecast tables, sources, two valuation bridges, scenarios/sensitivity and exports. JSON endpoints support future clients.
5. Add SQLite cache and atomic shared-process limits, explicit trusted-proxy configuration, bounded network requests, health/readiness, slim pinned requirements, production start config and CI. No deployment credentials in source.
6. Test model against independent workbook formulas, adverse provider data and HTTP boundaries. Exercise the browser at desktop/mobile widths. Scan changes, commit and create a draft PR when authenticated. Public demo resumption depends on owner's Render account; report it separately from local success.

## Review focus

Missing differs from zero; period alignment and filing cutoff; no cross-currency valuation; no silent valuation during upstream failure; invalid sensitivity is N/A; present/12-month horizons consistent; all exports reflect entered assumptions and provenance; future API remains optional and validates payloads; demo is always explicitly synthetic.
