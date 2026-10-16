# Deterministic browser acceptance

Run `npm ci --prefix tests/browser`, `cd tests/browser && npx playwright install chromium`, then `npm --prefix tests/browser test` from the repository root with development Python requirements installed. Set `PYTHON` to a virtual-environment executable if necessary; `CHROME_EXECUTABLE` optionally selects an installed Chrome.

The local fixture server blocks external Python provider requests and uses temporary SQLite databases. Chromium exercises the shipped workspace and iframe editor, changes a selected forecast-tax assumption, verifies recalculated WACC, saves/reloads research and downloads Excel. HyperFormula independently evaluates the downloaded workbook and compares FCFF and valuation outputs with the API. CI retains artifacts. This does not certify live provider availability or Microsoft Excel rendering.

`npm --prefix tests/browser run typecheck` checks the tracked experimental TypeScript engine in isolation. That module is not the production engine; a passing type check does not establish financial parity.

Live production monitoring remains in the separate scheduled/manual workflow. Do not use live services or production accounts in these tests.
