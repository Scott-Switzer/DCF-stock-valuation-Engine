// Real-browser latency benchmark: drives the workspace in Chromium and reads
// the app's own performance marks (including paint-aligned marks), resource
// timing for the load POST, and Server-Timing / Cf-Cache-Status headers.
// Usage: node scripts/bench_browser.mjs --base https://... --tickers AAPL,MSFT
//   --warm 20 --cold-tickers XOM,O --out /tmp/bench.json [--headed]
import { createRequire } from 'node:module';
const require = createRequire('/tmp/package.json');
const { chromium } = require('playwright-core');

const rawArgs = process.argv.slice(2);
const args = {};
for (let i = 0; i < rawArgs.length; i++) {
  const m = rawArgs[i].match(/^--([^=\s]+)(?:=(.*))?$/);
  if (!m) continue;
  if (m[2] !== undefined) args[m[1]] = m[2];
  else if (i + 1 < rawArgs.length && !rawArgs[i + 1].startsWith('--')) args[m[1]] = rawArgs[++i];
  else args[m[1]] = true;
}
const BASE = args.base;
const WARM_TICKERS = (args.tickers || 'AAPL,MSFT,PEP').split(',');
const WARM_N = parseInt(args.warm || '20', 10);
const COLD_TICKERS = (args['cold-tickers'] || '').split(',').filter(Boolean);
const OUT = args.out || '/tmp/bench_browser.json';
const HEADED = 'headed' in args;

if (!BASE) throw Error('--base is required');

const browser = await chromium.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: !HEADED,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

const health = await (await fetch(`${BASE}/health`)).json();
const revision = health.release;

const observations = [];

async function observe(ticker, cond) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const headers = {};
  let bodyInfo = null;
  page.on('response', (r) => {
    if (r.url().includes('/api/load/dcf')) {
      headers.serverTiming = r.headers()['server-timing'] || null;
      headers.cfCacheStatus = r.headers()['cf-cache-status'] || null;
      headers.contentEncoding = r.headers()['content-encoding'] || null;
      headers.contentLength = r.headers()['content-length'] || null;
      bodyInfo = r.json().then((b) => ({
        hasBrief: !!b.brief, briefBasis: b.brief?.basis || null,
        briefBlocked: b.brief?.blocked || null,
        hasForm: !!b.form, hasBaseDocument: !!b.form?.base_document,
        cacheState: b.load_summary?.assembly_cache?.state || null,
      })).catch((e) => ({ bodyError: String(e).slice(0, 120) }));
    }
  });
  const obs = { ticker, cond, revision: revision.commit };
  try {
    const consoleLines = [];
    page.on('console', (m) => { if (m.text().includes('[brief-sync]')) consoleLines.push(m.text()); });
    const url = args.debug ? `${BASE}/?brief-debug=1` : `${BASE}/`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('#company-loader', { timeout: 15000 });
    const t0 = await page.evaluate(() => performance.now());
    await page.evaluate((sym) => {
      document.getElementById('workspace-ticker').value = sym;
      document.getElementById('company-loader').requestSubmit();
    }, ticker);
    try {
      await page.waitForFunction(
        () => performance.getEntriesByName('workspace:value-painted').length > 0,
        null, { timeout: 45000 },
      );
    } catch {
      obs.timeout = true;
    }
    // Brief/editor marks are best-effort; value-painted is the primary signal.
    await page.waitForTimeout(1500);
    const data = await page.evaluate(() => ({
      now: performance.now(),
      // Keep every firing: duplicate mark names mean re-renders.
      marks: performance.getEntriesByType('mark')
        .map((m) => [m.name, Math.round(m.startTime)]),
      resources: performance.getEntriesByType('resource')
        .filter((r) => r.name.includes('/api/'))
        .map((r) => ({
          url: r.name.split('/').slice(-2).join('/'),
          transferSize: r.transferSize, encodedBodySize: r.encodedBodySize,
          decodedBodySize: r.decodedBodySize, duration: Math.round(r.duration),
          startTime: Math.round(r.startTime),
        })),
    }));
    Object.assign(obs, {
      t0: Math.round(t0),
      marks: data.marks,
      resources: data.resources,
      loadBody: bodyInfo ? await bodyInfo : null,
      briefSync: consoleLines,
      ...headers,
    });
  } catch (error) {
    obs.error = String(error).slice(0, 200);
  } finally {
    await context.close();
  }
  observations.push(obs);
  const rel = (name) => {
    const hit = (obs.marks || []).filter(([n]) => n === name).map(([, v]) => v - obs.t0);
    return hit.length ? hit.join('+') : '—';
  };
  const load = (obs.resources || []).find((r) => r.url.endsWith('load/dcf'));
  console.log(`${cond} ${ticker}: value=${rel('workspace:value-painted')} brief=${rel('workspace:brief-visible')} transfer=${load?.transferSize ?? '?'}`);
  return obs;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Cold first: each cold ticker once (server assembly-cache MISS expected).
for (const t of COLD_TICKERS) { await observe(t, 'cold'); await sleep(3000); }
// First touch per warm ticker counts as its cold sample, then warm repeats.
for (const t of WARM_TICKERS) { await observe(t, 'cold'); await sleep(3000); }
for (let i = 0; i < WARM_N; i++) {
  for (const t of WARM_TICKERS) { await observe(t, 'warm'); await sleep(2000); }
}

await browser.close();
await (await import('node:fs')).promises.writeFile(OUT, JSON.stringify({ base: BASE, revision, observations }, null, 1));
console.log(`wrote ${OUT} (${observations.length} observations)`);
