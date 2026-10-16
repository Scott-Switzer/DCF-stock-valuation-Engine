// Real-browser latency benchmark: drives the workspace in Chromium and reads
// the app's own performance marks (including paint-aligned marks), resource
// timing for the load POST, and Server-Timing / Cf-Cache-Status headers.
// Install: npm ci --prefix tests/browser; cd tests/browser && npx playwright install chromium
// Usage: node scripts/bench_browser.mjs --base https://... --tickers AAPL,MSFT
//   --warm 20 --cold-tickers XOM,O --out /tmp/bench.json [--headed]
import { createRequire } from 'node:module';
const require = createRequire(new URL('../tests/browser/package.json', import.meta.url));
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
const INTERVAL_MS = Number(args['interval-ms'] || 6500);
const REUSE = 'reuse' in args;
if (args.summarize) {
  const fs = await import('node:fs');
  const d = JSON.parse(fs.readFileSync(args.summarize, 'utf8'));
  const groups = new Map();
  for (const o of d.observations) {
    const rel = (name, idx = 0) => {
      const hits = (o.marks || []).filter(([n]) => n === name).map(([, v]) => v - o.t0);
      return hits.length > idx ? hits[idx] : null;
    };
    const load = (o.resources || []).find((r) => r.url.endsWith('load/dcf'));
    const key = `${o.ticker} | cache=${o.loadBody?.cacheState ?? '?'} | ctx=${o.ctx ?? 'fresh'}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ value: rel('workspace:value-painted'), brief: rel('workspace:brief-visible'), wire: load?.transferSize ?? null, flask: o.serverTiming });
  }
  const q = (s, p) => s.length ? s.sort((a, b) => a - b)[Math.min(s.length - 1, Math.max(0, Math.ceil(p * s.length) - 1))] : null;
  for (const [key, rows] of [...groups.entries()].sort()) {
    const ok = rows.filter((r) => r.value !== null);
    const v = ok.map((r) => r.value), b = ok.map((r) => r.brief).filter((x) => x !== null);
    console.log(`${key} n=${rows.length} ok=${ok.length} value p50=${q(v, .5)} p95=${q(v, .95)} min=${q(v, 0)} max=${q(v, 1)}`);
    console.log(`    brief-first p50=${q(b, .5)} p95=${q(b, .95)} wire=${ok[0]?.wire ?? '?'}`);
  }
  process.exit(0);
}

if (!BASE) throw Error('--base is required');

const browser = await chromium.launch({
  ...(process.env.CHROME_EXECUTABLE ? {executablePath:process.env.CHROME_EXECUTABLE}
    : process.platform === 'darwin' ? {executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'} : {}),
  headless: !HEADED,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

const health = await (await fetch(`${BASE}/health`)).json();
const revision = health.release;

const observations = [];

let sharedContext = null;
async function observe(ticker, cond) {
  const context = REUSE ? (sharedContext ??= await browser.newContext()) : await browser.newContext();
  const page = await context.newPage();
  const ctx = REUSE ? 'reused' : 'fresh';
  const headers = {};
  let bodyInfo = null;
  page.on('response', (r) => {
    if (r.url().includes('/api/load/dcf')) {
      headers.loadStatus = r.status();
      headers.serverTiming = r.headers()['server-timing'] || null;
      headers.cfCacheStatus = r.headers()['cf-cache-status'] || null;
      headers.contentEncoding = r.headers()['content-encoding'] || null;
      headers.contentLength = r.headers()['content-length'] || null;
      bodyInfo = r.json().then((b) => ({
        hasBrief: !!b.brief, briefBasis: b.brief?.basis || null,
        briefBlocked: b.brief?.blocked || null,
        hasForm: !!b.form, hasBaseDocument: !!b.form?.base_document,
        cacheState: b.load_summary?.assembly_cache?.state || null,
        stageSeconds: b.load_summary?.stage_seconds, hitBreakdown: b.load_summary?.hit_breakdown, statementSource: b.financials?.source?.statement_source,
      })).catch((e) => ({ bodyError: String(e).slice(0, 120) }));
    }
  });
  const obs = { ticker, cond, ctx, revision: revision.commit };
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
    await page.close();
    if (!REUSE) await context.close();
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

// First touch is a sampling label, not proof of a cache miss. Read cacheState.
for (const t of COLD_TICKERS) { await observe(t, 'cold'); await sleep(INTERVAL_MS); }
// First touch per warm ticker counts as its cold sample, then warm repeats.
for (const t of WARM_TICKERS) { await observe(t, 'cold'); await sleep(INTERVAL_MS); }
for (let i = 0; i < WARM_N; i++) {
  for (const t of WARM_TICKERS) { await observe(t, 'warm'); await sleep(INTERVAL_MS); }
}

await browser.close();
await (await import('node:fs')).promises.writeFile(OUT, JSON.stringify({ base: BASE, revision, observations }, null, 1));
console.log(`wrote ${OUT} (${observations.length} observations)`);
