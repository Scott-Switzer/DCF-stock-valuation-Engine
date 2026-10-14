const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/workspace.js', 'utf8');
const start = source.indexOf('  function briefRow(label, value) {');
const end = source.indexOf('  function render(item) {', start);
const slice = source.slice(start, end);

function element() {
  return {
    textContent: '', hidden: true, disabled: false, value: '',
    replaceChildren() { this.children = []; },
    append(...kids) { this.children = (this.children || []).concat(kids); },
    querySelector() { return element(); },
  };
}

const BASE_FORM = { growth_0: 5, growth_1: 5, wacc: 6.5, terminal_growth: 2, base_document: '{"x":1}' };
const BASELINE_BRIEF = {
  basis: 'baseline', basis_note: 'Baseline note.', blocked: null,
  dcf: { target_price_12m: 90, upside_12m: -0.1, intrinsic_value: 88, upside: -0.12, wacc: 0.08, terminal_growth: 0.02 },
  price: { value: 100, as_of: '2026-10-13' },
  assumptions: { wacc: 0.08, terminal_growth_rate: 0.02, revenue_growth_mean: 0.05, ebit_margin_mean: 0.2 },
  market_implied: {}, scenarios: [], drivers: {}, freshness: {}, evidence: {},
};
const CUSTOM_BRIEF = {
  ...BASELINE_BRIEF, basis: 'custom', basis_note: 'Custom note.',
  dcf: { ...BASELINE_BRIEF.dcf, intrinsic_value: 95 },
};

function setup() {
  const nodes = new Map();
  const doc = {
    createElement: () => element(),
    createTextNode: (t) => ({ text: t }),
    getElementById: (id) => {
      if (!nodes.has(id)) nodes.set(id, element());
      return nodes.get(id);
    },
  };
  const briefPosts = [];
  const frameSource = {};
  const listeners = {};
  const context = {
    document: doc,
    location: { origin: 'https://x.test' },
    window: {
      researchWorkspace: { setContext() {} },
      addEventListener: (k, f) => { listeners[k] = f; },
    },
    performance: { mark() {} },
    fetch: async () => ({ ok: false }),
    setTimeout, clearTimeout,
    $: (id) => doc.getElementById(id),
    money: (v) => `M${v}`, pct: (v) => `P${v}`, date: (v) => `D${v}`,
    // Stubs for out-of-slice collaborators.
    send() {}, assemble() {}, status() {},
    loadGuidance() {},
    render(item) { context._rendered = item; },
    withBaseDocument: (d) => d,
    request: async (url, body) => {
      if (url === '/api/brief') {
        briefPosts.push(body);
        return body.assumptions ? CUSTOM_BRIEF : BASELINE_BRIEF;
      }
      throw Error(`unexpected request ${url}`);
    },
    // Live state, mirroring the workspace IIFE.
    editors: new Map([['dcf', { contentWindow: frameSource }]]),
    results: new Map(),
    ready: new Set(),
    analysts: null,
    method: 'dcf',
    baseline: {
      financials: { company: { ticker: 'TEST' }, market: {}, source: { kind: 'api' } },
      form: { ...BASE_FORM },
      brief: BASELINE_BRIEF,
    },
    baselineBrief: null, briefTimer: null, briefSeq: 0,
    generation: 7, loading: false, guidanceRequested: false,
  };
  // Mirror the load handler: the bundled brief becomes the restore point.
  context.__testBaselineBrief = BASELINE_BRIEF;
  vm.createContext(context);
  vm.runInContext(`${slice};baselineBrief = __testBaselineBrief;`, context);
  const dispatch = (data) => listeners.message({
    origin: 'https://x.test', source: frameSource, data,
  });
  const previewResult = (form, assumptions) => dispatch({
    type: 'preview-result', generation: 7,
    result: { assumptions, input_financials: context.baseline.financials },
    form,
  });
  return { context, nodes, briefPosts, dispatch, previewResult };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  // 1. Identical assumptions restore the bundled baseline with no request.
  {
    const { nodes, briefPosts, previewResult } = setup();
    previewResult({ ...BASE_FORM }, { revenue_growth_rates: [0.05] });
    await sleep(600);
    assert.equal(briefPosts.length, 0, 'no brief request for baseline assumptions');
    assert.ok(!nodes.get('research-brief').hidden, 'baseline brief rendered');
  }

  // 2. Edited assumptions fetch a custom brief exactly once.
  {
    const { nodes, briefPosts, previewResult } = setup();
    const edited = { ...BASE_FORM, growth_0: 9 };
    previewResult(edited, { revenue_growth_rates: [0.09] });
    await sleep(600);
    assert.equal(briefPosts.length, 1, 'one debounced brief request');
    assert.deepEqual(briefPosts[0].assumptions, { revenue_growth_rates: [0.09] });
    assert.ok(briefPosts[0].financials.company, 'accepted snapshot travels with assumptions');
    assert.ok(!nodes.get('research-brief').hidden, 'custom brief rendered');
  }

  // 3. Rapid successive edits collapse into a single latest request.
  {
    const { briefPosts, previewResult } = setup();
    previewResult({ ...BASE_FORM, growth_0: 8 }, { revenue_growth_rates: [0.08] });
    previewResult({ ...BASE_FORM, growth_0: 9 }, { revenue_growth_rates: [0.09] });
    previewResult({ ...BASE_FORM, growth_0: 10 }, { revenue_growth_rates: [0.1] });
    await sleep(600);
    assert.equal(briefPosts.length, 1, 'rapid edits collapse to one request');
    assert.deepEqual(briefPosts[0].assumptions, { revenue_growth_rates: [0.1] }, 'latest wins');
  }

  // 4. Reverting to defaults restores the bundle without another request.
  {
    const { briefPosts, previewResult } = setup();
    previewResult({ ...BASE_FORM, growth_0: 9 }, { revenue_growth_rates: [0.09] });
    await sleep(600);
    assert.equal(briefPosts.length, 1);
    previewResult({ ...BASE_FORM }, { revenue_growth_rates: [0.05] });
    await sleep(600);
    assert.equal(briefPosts.length, 1, 'revert restores bundle silently');
  }

  // 5. Invalid intermediate input never clears or refetches the brief.
  {
    const { nodes, briefPosts, dispatch, context } = setup();
    context.document.getElementById('research-brief').hidden = false;
    dispatch({ type: 'preview-error', generation: 7, error: 'Review growth 0.' });
    await sleep(600);
    assert.equal(briefPosts.length, 0, 'no brief request on invalid input');
    assert.ok(!nodes.get('research-brief').hidden, 'last good brief stays visible');
  }

  // 6. Numeric formatting differences (5 vs "5.00") still count as baseline.
  {
    const { briefPosts, previewResult } = setup();
    const reformatted = { ...BASE_FORM, growth_0: '5.00', wacc: '6.50' };
    previewResult(reformatted, { revenue_growth_rates: [0.05] });
    await sleep(600);
    assert.equal(briefPosts.length, 0, 'display formatting is not a real edit');
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
