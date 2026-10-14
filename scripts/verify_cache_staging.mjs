// Staging edge-cache security check: shared-link revocation and per-user
// isolation through a real browser (cookies + page flows, not curl).
// Usage: node scripts/verify_cache_staging.mjs --base https://...
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
if (!BASE) throw Error('--base is required');

const browser = await chromium.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const results = [];
const check = (name, ok, detail) => {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`);
};

const ctxA = await browser.newContext();
const pageA = await ctxA.newPage();
await pageA.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
await pageA.waitForSelector('#company-loader', { timeout: 15000 });
// Load AAPL through the real UI, wait for the interactive preview, save it.
await pageA.evaluate(() => {
  document.getElementById('workspace-ticker').value = 'AAPL';
  document.getElementById('company-loader').requestSubmit();
});
try {
  await pageA.waitForFunction(
    () => performance.getEntriesByName('workspace:value-visible').length > 0,
    null, { timeout: 45000 },
  );
} catch { check('AAPL preview becomes interactive', false, 'timeout'); await browser.close(); process.exit(1); }
await pageA.waitForTimeout(1000);
await pageA.click('#save-valuation');
await pageA.waitForTimeout(2000);
const api = (page, method, path, body) => page.evaluate(async ([m, p, b, base]) => {
  const r = await fetch(new URL(p, base), {
    method: m, headers: { 'Content-Type': 'application/json' },
    body: b ? JSON.stringify(b) : undefined,
  });
  return { status: r.status, headers: { cache: r.headers.get('cache-control'), cfCache: r.headers.get('cf-cache-status') }, json: await r.json().catch(() => null), text: null };
}, [method, path, body, BASE]);

const history = await api(pageA, 'GET', '/api/history');
const id = history.json?.[0]?.id;
check('valuation saved to caller-scoped history', !!id, `records=${history.json?.length ?? 0}`);
const share = await api(pageA, 'POST', '/api/share', { valuation_id: id });
const token = share.json?.token;
check('share link minted', !!token, `cache=${share.headers.cache}`);

// Separate user B reads the live link (bearer access works pre-revocation).
const ctxB = await browser.newContext();
const pageB = await ctxB.newPage();
await pageB.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
await pageB.waitForSelector('#company-loader', { timeout: 15000 });
const liveB = await api(pageB, 'GET', `/v/${token}`);
check('second user reads live shared link', liveB.status === 200, `status=${liveB.status} cache=${liveB.headers.cache} cf=${liveB.headers.cfCache}`);

// Owner revokes; both users must immediately see unknown/expired.
const revoke = await api(pageA, 'DELETE', `/api/share/${token}`);
check('revoke accepted', revoke.status === 200, `status=${revoke.status}`);
const afterA = await api(pageA, 'GET', `/v/${token}`);
check('owner sees revoked link as gone', afterA.status === 404, `status=${afterA.status} cache=${afterA.headers.cache} cf=${afterA.headers.cfCache}`);
const afterB = await api(pageB, 'GET', `/v/${token}`);
check('second user sees revoked link as gone (no stale edge copy)', afterB.status === 404, `status=${afterB.status} cache=${afterB.headers.cache} cf=${afterB.headers.cfCache}`);

// Watchlist isolation across users, live.
await api(pageA, 'POST', '/api/watchlist', { ticker: 'MSFT', target: 500, direction: 'above' });
const watchA = await api(pageA, 'GET', '/api/watchlist');
const watchB = await api(pageB, 'GET', '/api/watchlist');
check('watchlist isolated per user', watchA.json?.length > 0 && watchB.json?.length === 0,
  `A=${watchA.json?.length ?? '?'} B=${watchB.json?.length ?? '?'}`);

// User pages carry private directives end to end.
const home = await api(pageB, 'GET', '/');
check('workspace page is private,no-store', home.headers.cache === 'private, no-store', `cache=${home.headers.cache}`);

await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(failed.length ? `RESULT: ${failed.length} FAILURES` : 'RESULT: ALL PASS');
process.exit(failed.length ? 1 : 0);
