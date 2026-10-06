# CUIG template alignment

Reference: user-supplied `CUIG Valuation Template Fall 2026.xlsx`, sheet `DCF - GGM`. The reference is a blank template, so there is no real-company valuation in it to reproduce. The workbook was read without modification. Instructions inside the workbook were treated as reference content, not authorization to change other files or implement unrelated methods.

| Workbook | Application |
|---|---|
| C:E historical columns, F:J forecast columns | Three annual historical periods and five individually editable forecast periods |
| Row 11, row 12 | Prior revenue × (1 + annual revenue growth) |
| Rows 14–15, 17–18, 20–21 | EBIT/net-income margins × revenue; EBITDA = EBIT + D&A |
| Rows 23–30, 32–35 | CapEx, D&A, operating NWC, book-value ratios; explicit effective tax rates |
| F41:J46 | FCFF = EBIT − taxes + D&A − ΔNWC − CapEx; year one uses the latest historical NWC balance |
| I3 | Explicit user WACC, default 6.5% in the illustrative form |
| F47:J47; C52 | End-year PV of years one through five |
| C58, C59, C61, C62 | g, year-five FCFF, Gordon-growth TV, TV discounted five periods |
| C67, C74, C78, C80, C82 | Present enterprise value, net debt, common equity, diluted shares, value/share |
| G48:J48, I52, I62, I67, I82 | 12-month scenario excludes year-one FCFF, discounts remaining flows and TV one fewer period |

The 12-month enterprise value also satisfies `EV_12m = EV_today × (1 + WACC) − FCFF_1` under the same forecasts. The application derives both from the cash flows, with one shared terminal calculation.

## Intentional differences

- The application displays both horizons prominently and avoids calling the 12-month target today's intrinsic value.
- The common-equity bridge additionally deducts preferred claims and noncontrolling interests and adds other nonoperating assets. All values are explicit; no missing item silently becomes zero.
- The template keeps debt, cash and diluted shares unchanged at 12 months. The app keeps that default but exposes future overrides and labels the convention.
- Optional normalized terminal mode sets terminal reinvestment to g / ROIC. The default preserves the template's year-five FCFF convention; its reinvestment limitation is disclosed.
- Invalid assumptions, missing inputs, nonfinite numbers, inappropriate sectors and currencies are rejected. Invalid sensitivity combinations display N/A. Negative common equity is displayed before a zero floor on common-share value.
- The form explicitly uses percentages (5 = 5%); internal/API rates are decimals.
- For convenience, operating drivers can be filled from historical means and then edited per year. This is a starting assumption, not a forecast inferred by the workbook.
- Net-income and book-value projections are retained for inspection and future models, but do not drive FCFF.
- Sensitivity and scenario ranges are assumption cases, not confidence intervals. DDM and trading comps are implemented separately; see ddm-relative-alignment.md. A football field remains future scope.
- Both implementations assume end-period discounting. The workbook's valuation date does not adjust discount factors for a partial fiscal year. The app explicitly discloses this rather than implying a stub-period model.

## Independent reconciliation

`tests/fixtures/cuig-formulas.json` contains the relevant formula text extracted from the supplied DCF worksheet. `tests/test_cuig_reconciliation.py` interprets only arithmetic, SUM and zero-payment PV using an independent restricted AST evaluator. It evaluates the reference C82 and I82 against two growth profiles, with varying later-year operating drivers, and compares every projected FCFF/PV to the engine.

The basic synthetic fixture with 6.5% WACC, 2% terminal growth and 5% annual revenue growth yields intrinsic value $31.4459549353 and 12-month target $32.2399420061 before display rounding. These tests establish agreement with the supplied formulas. They are not native Excel recalculation, real-company source reconciliation, or evidence of forecast accuracy.

Finance references: [SEC companyfacts API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [Damodaran valuation notes](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html).
