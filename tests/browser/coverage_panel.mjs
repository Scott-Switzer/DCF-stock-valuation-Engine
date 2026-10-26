// Rendered coverage/freshness regression for the owner data workspace.
//
// The answer response is synthetic and intercepted in the browser, so this test
// asserts what the panel renders without touching providers, private data or the
// network. It fails if the coverage line, warnings list or evidence block stops
// being filled, and it fails if stale evidence survives a later failed request.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('../../', import.meta.url));
const base = 'http://127.0.0.1:5180';
const server = spawn(process.env.PYTHON || 'python3', ['tests/browser/fixture_server.py'], {
  cwd: root, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, PORT: '5180' },
});
let serverLog = '';
server.stdout.on('data', (x) => (serverLog += x));
server.stderr.on('data', (x) => (serverLog += x));
let browser, page;
const output = new URL('./artifacts/', import.meta.url);
await mkdir(output, { recursive: true });

const answer = {
  answer: 'Apple annual revenue for FY2024 and FY2025.',
  data_as_of: '2025-09-27',
  bundle_id: 'b'.repeat(32),
  warnings: ['Source gap retained: FY2019 revenue is not stored.'],
  source: { source_cutoff: '2026-02-01', source_releases: { serving: 'c'.repeat(32) } },
  source_releases: { serving: 'c'.repeat(32) },
  result: {
    frequency: 'annual',
    observations: [{ period_end: '2024-09-28' }, { period_end: '2025-09-27' }],
    coverage: {
      reason: 'INCOMPLETE_HISTORY',
      date_min: '2020-01-01',
      date_max: '2025-09-27',
      metrics_present: ['revenue'],
      coverage_gap_reasons: ['FY2019'],
    },
    calculation_gaps: [{ reason: 'MISSING_FY2019' }],
  },
};

try {
  for (let i = 0; i < 100; i++) {
    if (server.exitCode !== null) throw Error(serverLog);
    try { if ((await fetch(base + '/health')).ok) break; } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_EXECUTABLE ? { executablePath: process.env.CHROME_EXECUTABLE } : {}),
  });
  const context = await browser.newContext();
  page = await context.newPage();
  page.setDefaultTimeout(15000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));

  let mode = 'ok';
  await page.route('**/api/data/query**', (route) =>
    route.fulfill({
      status: mode === 'ok' ? 200 : 500,
      contentType: 'application/json',
      body: JSON.stringify(mode === 'ok' ? answer : { error: 'Synthetic failure for the clearing regression.' }),
    }));

  await page.goto(base + '/data');
  await page.locator('#question').fill('Apple annual revenue');
  await page.locator('#financial-query button').click();
  await page.locator('#financial-coverage').waitFor({ state: 'visible' });

  const coverage = await page.locator('#financial-coverage').innerText();
  assert.match(coverage, /Latest period in this answer: 2025-09-27/);
  assert.match(coverage, /Frequency: annual/);
  assert.match(coverage, /Observed periods: 2024-09-28 to 2025-09-27 \(2 observations\)/);
  assert.match(coverage, /Source cutoff: 2026-02-01/);
  assert.match(coverage, /Coverage: INCOMPLETE_HISTORY \(stored 2020-01-01 to 2025-09-27\)/);
  assert.match(coverage, /Metrics present: revenue/);
  assert.match(coverage, /Source gaps: FY2019/);
  assert.match(coverage, /Native gaps retained: 1/);

  const warnings = page.locator('#financial-warnings');
  await warnings.waitFor({ state: 'visible' });
  assert.equal(await warnings.locator('li').count(), 1);
  assert.match(await warnings.innerText(), /FY2019 revenue is not stored/);

  await page.locator('#financial-evidence').waitFor({ state: 'visible' });
  // The evidence block lives inside a closed <details>, so read its text
  // content rather than rendered innerText.
  const evidence = await page.locator('#financial-source').textContent();
  assert.match(evidence, /"source_cutoff": "2026-02-01"/);
  assert.match(evidence, /"bundle_id": "bbbbbbbb/);

  // A later failure must clear every evidence element rather than leaving the
  // previous answer's coverage on screen.
  mode = 'fail';
  await page.locator('#financial-query button').click();
  await page.waitForFunction(() =>
    document.querySelector('#financial-coverage')?.hidden === true);
  assert.equal(await page.locator('#financial-coverage').innerText(), '');
  assert.equal(await page.locator('#financial-warnings').innerText(), '');
  assert.equal(await page.locator('#financial-warnings').isVisible(), false);
  assert.equal(await page.locator('#financial-evidence').isVisible(), false);
  assert.match(await page.locator('#financial-answer').innerText(), /Synthetic failure/);

  assert.deepEqual(errors, []);
  await page.screenshot({ path: fileURLToPath(new URL('coverage-panel.png', output)), fullPage: true });
  const report = {
    status: 'PASS',
    scope: 'Synthetic intercepted answer; rendered coverage, warnings, evidence and clearing',
    coverage,
    cleared_on_failure: true,
  };
  await writeFile(new URL('coverage-panel.json', output), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} catch (error) {
  if (page) {
    await page.screenshot({ path: fileURLToPath(new URL('coverage-failure.png', output)), fullPage: true }).catch(() => {});
    await writeFile(new URL('coverage-failure.html', output), await page.content().catch(() => ''));
  }
  throw error;
} finally {
  await browser?.close();
  server.kill('SIGTERM');
  await writeFile(new URL('coverage-server.log', output), serverLog);
}
