# CUIG Valuation Suite

A valuation suite with five-year unlevered discounted cash flow, dividend discount and trading-comparable models based on the **CUIG Valuation Template Fall 2026**. It shows intrinsic value today and a separate 12-month target scenario, with editable operating drivers, auditable financial sources and a replaceable data provider.

**Public demo:** https://dcf-valuation-engine.scswitzer.workers.dev

![Synthetic DCF example](docs/screenshots/valuation-desktop.png)

## Features

- DDM based on common-dividend forecasts, equity-return discounting and separate present/12-month values.
- Relative valuation with EV/Revenue, EV/EBITDA, EV/EBIT, P/E and P/B, peer means, selectable methods and financial-firm restrictions.
- DCF-to-method handoff reuses identity/forward forecasts while requiring sourced dividends and peers.

- Three historical fiscal years and five years of individually editable revenue growth, EBIT, net-income, book-value, D&A, CapEx, working-capital and tax assumptions.
- Present and 12-month enterprise-to-common-equity bridges, including preferred claims, noncontrolling interests, other nonoperating assets and diluted shares.
- CUIG Gordon-growth terminal convention, plus optional ROIC-based terminal reinvestment normalization.
- WACC/terminal-growth sensitivity and explicitly defined bear/base/bull cases.
- Offline synthetic example, manual entry, JSON import, SEC companyfacts adapter, and an optional Zion/MiniBloomberg company-packet adapter.
- CSV export for Excel and complete JSON export containing inputs, assumptions, results and source provenance.
- Local ticker autocomplete, accessible input labels, mobile layouts and preserved inputs on errors.
- Pure Python calculation engine, Flask API, public Cloudflare Python Worker, private D1 valuation records, shared edge rate limits, regression tests and GitHub Actions.

## Run locally

Python 3.12 or 3.13 and Node.js (only for JavaScript syntax validation in development).

```bash
git clone https://github.com/Scott-Switzer/DCF-stock-valuation-Engine.git
cd DCF-stock-valuation-Engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py
```

Open <http://127.0.0.1:5000>. The initial example is deliberately synthetic and works without keys or internet. On the form, **5 means 5%**. Financial amounts and diluted shares use **absolute units**, not millions. JSON and CLI rates use decimals: `0.05` means 5%.

```bash
python run_dcf.py
python run_dcf.py --financials data/demo.json --wacc 0.065 --growth 0.05 0.05 0.05 0.05 0.05
pytest -q
ruff check .
node --check static/js/app.js
```

The old FMP/Yahoo/edgartools loader and console scraping have been replaced. No FMP key or Yahoo access is required for sample/manual mode. Local hosting uses Flask, requests and Gunicorn. Cloudflare hosting uses the Python Workers runtime and WSGI adapter; provider requests use bounded Workers fetch.

## Data providers

**Manual / sample:** Enter financials from your own annual reports. Missing input is rejected; zero is accepted only as an explicit numerical input. Import a `dcf-financials-v1` JSON document using the form. Downloads can be re-used as inputs by importing the `financials` object from a complete valuation export.

**SEC:** Set `EDGAR_IDENTITY` to your name and contact email in your shell or deployment environment. The app calls SEC's documented companyfacts API directly, selects annual USD facts available by the valuation date, and preserves tag/accession/filing provenance. No SEC key is required. Confirm company eligibility, enter a dated market price, and review diluted shares. Missing taxonomy fields remain blank for manual completion. SEC annual weighted-average diluted shares may need adjustments for current dilution. Debt classification, leases and D&A coverage require filing review.

**Zion / MiniBloomberg:** Optional server-side `ZION_API_BASE_URL` and `ZION_API_TOKEN`. The adapter reads `/v1/company/{ticker}` with an explicit point-in-time cutoff, maps annual metric observations, preserves release/observation provenance, and uses a dated price when present. Neither the endpoint nor credentials are embedded in frontend code. Configuration and a live integration acceptance check are required before claiming a connected deployment. Partial coverage remains incomplete rather than becoming zeros.

**Custom normalized API:** Optional server-side `DCF_API_BASE_URL` and `DCF_API_TOKEN`, exposing `/v1/valuation/financials/{ticker}`. See [the provider contract](docs/provider-contract.md) and [JSON schema](docs/financials.schema.json). This makes future provider changes independent of the model.

Environment variables are read directly. `.env.example` documents names, but the app does not automatically load a populated `.env` file. Do not commit keys or licensed datasets.

## Methodology and limits

Read [DCF alignment](docs/cuig-alignment.md) and [DDM/relative alignment](docs/ddm-relative-alignment.md) for exact worksheet references, formula reconciliation and intentional differences.

- End-of-year cash-flow discounting. Forecast periods start one year from the valuation date; fiscal-year stubs are not modeled.
- WACC is an explicit assumption in the browser, as in CUIG. The Python interface also retains CAPM/WACC calculation for complete inputs. No dated default is portrayed as a fetched market rate.
- Template terminal FCFF is year-five FCFF × (1 + g). Normalized mode uses terminal NOPAT × (1 − g / terminal ROIC). Terminal FCFF must be positive; terminal growth must be below WACC.
- 12-month target excludes year-one FCFF and discounts remaining flows one fewer year. Current debt/cash/claims/shares carry forward unless overridden. This is an assumption-dependent valuation scenario, not a stock-price forecast.
- Loss-period tax benefits follow the CUIG formula. Assess actual tax-loss utilization. Negative common equity is exposed; per-share value is floored at zero.
- USD operating companies only. Banks, insurers, REITs, funds and partnerships need other models. Sector metadata and user confirmation are required for eligibility; this is not an automated sector classifier.
- The sample, cases and tests establish formula behavior. They do not establish investment returns or accurate forecasts for all companies. No automatic financial recommendation is made.

## API and exports

`GET /api/sample`, `GET /api/search?q=AAPL`, `POST /api/financials`, `POST /api/calculate`, `POST /export/csv`, `POST /export/json`. Invalid input returns HTTP 400, provider failure HTTP 503, and rate limits HTTP 429. See [API examples](docs/provider-contract.md).

Exports retain full numeric precision; the UI rounds money for readability. They include the active assumptions and warnings. CSV opens in Excel; it is not a formula-driven `.xlsx` replica of the supplied workbook.

## Deploy

[Cloudflare deployment guide](docs/deployment.md). The public Worker supports sample/manual calculations, SEC statement loading and private D1 persistence. Optional Zion integration remains unconfigured. Docker and `render.yaml` are alternative hosting recipes.

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 35 app:app
```

Public calculations save inputs, assumptions, model version and results to private D1 storage with a visible privacy notice. Synthetic origins are flagged and repeat submissions are deduplicated. Raw IP addresses are not stored in valuation records. See [research limitations](docs/valuation-research.md). The historical suspended Render service has been replaced as the advertised demo.

## Future valuation suite

The normalized company document, pure calculation engine and structured API outputs are the foundation for additional methods. DCF, DDM and trading comparables are implemented. A combined football-field view and additional sector-specific methods remain future work. They will need their own assumptions, suitability checks and reconciliation tests rather than reusing FCFF for every sector.

MIT licensed. The CUIG workbook is a user-supplied reference and is not redistributed or modified. Public provider data remains subject to each provider's terms and access policies.
