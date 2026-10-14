const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/workspace.js', 'utf8');

function element() {
  return {
    textContent: '', hidden: true, disabled: false, value: 'TEST', open: false,
    replaceChildren() { this.children = []; },
    append(...kids) { this.children = (this.children || []).concat(kids); },
    querySelector() { return element(); },
  };
}
function makeDocument() {
  const nodes = new Map();
  return {
    createElement: () => element(),
    createTextNode: (t) => ({ text: t }),
    getElementById: (id) => {
      if (!nodes.has(id)) nodes.set(id, element());
      return nodes.get(id);
    },
    _nodes: nodes,
  };
}

async function runLoad(data) {
  const marks = [];
  const fetched = [];
  const doc = makeDocument();
  let submit;
  const context = {
    document: doc,
    location: { origin: 'https://x.test' },
    window: { researchWorkspace: { setContext() {} } },
    performance: { mark: (n) => marks.push(n) },
    fetch: async (url) => { fetched.push(url); return { ok: false }; },
    requestAnimationFrame: () => {},
    $: (id) => {
      if (id === 'company-loader') return { addEventListener: (k, f) => { submit = f; } };
      if (id === 'workspace-ticker') return { value: 'TEST' };
      return doc.getElementById(id);
    },
    status() {}, assemble: async () => {}, render() {},
    loadReferences() {}, editors: new Map(), results: new Map(),
    method: 'dcf', baseline: null, analysts: null, guidanceRequested: false,
    baselineBrief: null, briefTimer: null, briefSeq: 0,
    generation: 0, loading: false,
    money: (v) => String(v), pct: (v) => String(v), date: (v) => String(v),
    withBaseDocument: (d) => d,
    request: async (url) => { fetched.push(url); return data; },
  };
  const start = source.indexOf('  $("company-loader").addEventListener("submit"');
  const end = source.indexOf('  async function loadReferences(', start);
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  await submit({ preventDefault() {} });
  return { marks, fetched, doc };
}

const financials = (overrides) => ({
  company: { ticker: 'TEST', name: 'Test Inc.' },
  market: { price: 100, price_as_of: '2026-10-13' },
  source: { warnings: [], ...(overrides || {}) },
});

(async () => {
  // Embedded baseline brief renders with no extra round trip and real marks.
  const brief = { blocked: null, dcf: { target_price_12m: 90, upside_12m: -0.1, intrinsic_value: 88, upside: -0.12, wacc: 0.08, terminal_growth: 0.02 }, price: { value: 100, as_of: '2026-10-13' }, assumptions: { wacc: 0.08, terminal_growth_rate: 0.02, revenue_growth_mean: 0.05, ebit_margin_mean: 0.2 }, market_implied: {}, scenarios: [], drivers: {}, freshness: {}, evidence: {}, basis: 'baseline', basis_note: 'Baseline note.' };
  let r = await runLoad({ financials: financials({ statement_source: 'SEC-first', ppe_release: { release_id: 'x' } }), brief });
  assert.ok(!r.doc.getElementById('research-brief').hidden, 'brief panel visible');
  assert.ok(!r.fetched.includes('/api/brief'), 'no extra brief request when embedded');
  assert.match(r.doc.getElementById('workspace-source').textContent, /^SEC-first/, 'SEC-first label wins over generic PPE label');
  for (const m of ['workspace:load-start', 'workspace:load-response', 'workspace:company-visible', 'workspace:brief-visible', 'workspace:handler-settled', 'workspace:method-assembled']) {
    assert.ok(r.marks.includes(m), `mark recorded: ${m}`);
  }
  assert.ok(!r.marks.includes('workspace:visible'), 'finally-block visible mark removed');
  assert.match(r.doc.getElementById('brief-content').children.map(String).join(''), /./);

  // Without an embedded brief the client falls back to one POST.
  r = await runLoad({ financials: financials({}) });
  assert.ok(r.fetched.includes('/api/brief'), 'fallback brief request fires');

  // A skipped baseline brief explains why instead of staying silent.
  r = await runLoad({ financials: financials({}), load_summary: { stage_seconds: { brief_skipped: 'No baseline could be solved' } } });
  assert.ok(!r.doc.getElementById('research-brief').hidden, 'skipped-brief note visible');
  assert.ok(!r.fetched.includes('/api/brief'), 'no fallback fetch when the skip reason is known');

  // Blocked brief still renders instead of failing the load.
  r = await runLoad({ financials: financials({}), brief: { blocked: 'Financial firm', ticker: 'TEST' } });
  assert.ok(!r.doc.getElementById('research-brief').hidden, 'blocked brief visible');
})().catch((error) => { console.error(error); process.exitCode = 1; });
