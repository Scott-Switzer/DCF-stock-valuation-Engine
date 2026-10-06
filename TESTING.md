# Verification

Install `requirements-dev.txt`, then run:

```bash
pytest -q
ruff check .
node --check static/js/app.js
python run_dcf.py
```

Tests cover independent CUIG formula reconciliation, present vs. 12-month horizons, preferred claims, driver overrides, terminal normalization, invalid sensitivity cells, missing/nonfinite data, fiscal/currency/availability checks, SEC and Zion fixture mapping, provider failures, export parity, input preservation, local autocomplete, script escaping, shared SQLite state, forwarded-header abuse and request limits.

CI runs on Python 3.12 and 3.13. Provider tests use synthetic representative records and never require keys or licensed datasets. The supplied workbook is not required to run the suite; extracted relevant formula text is stored with its provenance.

## Browser acceptance

- Load the offline example and calculate. Confirm the synthetic label and $31.45 present/$32.24 12-month result.
- Edit a forecast driver, calculate again and inspect the changed forecast/value. Edit assumptions restores the submitted form.
- Type AAP and select AAPL from autocomplete. Load its configured provider or switch to manual before reusing the form.
- Enter terminal growth at/above WACC. The frontend prevents submission and the server independently rejects it.
- Check missing fields, unavailable providers, JSON import, CSV/JSON exports and mobile table scrolling.

October 6 local evidence: current result, restored inputs and working autocomplete inspected in the in-app browser; no console errors. Result layout checked at 390 px with no document-level horizontal overflow. Screenshots in `docs/screenshots` show synthetic results. Public Render service remains suspended; configured SEC/Zion live success and real-company reconciliations remain separate acceptance checks.

## Cloudflare acceptance

Python Workers local smoke checks cover pages, static files, calculations and D1 insertion. Public production checks cover readiness, sample calculation, saved-reference lookup through authenticated D1, duplicate suppression, invalid input, exports, autocomplete and browser console errors. SEC AAPL annual statement loading succeeded in the Workers runtime; this is coverage evidence, not a completed real-company valuation. Zion remains unconfigured. D1 record tests bound serialization and avoid duplicate source documents.
