// Regression test: the assumptions editor must receive workspace-data even
// when baseline results arrive bundled with the load response (PR #29's fast
// path made assemble() early-return, which skipped the send and left the
// editor showing "Enter a ticker" with a hidden form).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/workspace.js', 'utf8');

function sliceFn(startMarker, endMarker) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.ok(start !== -1 && end !== -1, `markers found: ${startMarker}`);
  return source.slice(start, end);
}

const helpers = sliceFn('  function withBaseDocument(data) {', '  async function request(');
const sender = sliceFn('  function send(key, data) {', '  async function assemble(');
const assemble = sliceFn('  async function assemble(key, token) {', '  function showMethod(key) {');

function makeContext(bundle) {
  const posted = [];
  const frame = {
    contentWindow: {
      postMessage: (msg) => posted.push(msg),
    },
  };
  const context = {
    location: { origin: 'https://x.test' },
    baseline: bundle,
    results: new Map(),
    ready: new Set(),
    editors: new Map([['dcf', frame]]),
    method: 'dcf',
    generation: 0,
    status() {},
    request: async () => { throw new Error('should not fetch on bundled path'); },
    withBaseDocument: null, // installed below via helpers
    send: null, // installed below via sender
    assemble: null, // installed below via assemble
  };
  vm.createContext(context);
  vm.runInContext(`${helpers}${sender}${assemble}`, context);
  return { context, posted };
}

(async () => {
  const bundle = {
    financials: { company: { ticker: 'PAYX', name: 'Paychex Inc.' } },
    form: { wacc: 8.65, wacc_mode: 'recalculated' },
  };

  // 1. Bundled-preview path with a ready editor: workspace-data is sent.
  let h = makeContext(bundle);
  h.context.results.set('dcf', { loaded: true, data: bundle });
  h.context.ready.add('dcf');
  await h.context.assemble('dcf', 0);
  assert.equal(h.posted.length, 1, 'editor receives exactly one workspace-data');
  assert.equal(h.posted[0].type, 'workspace-data');
  assert.equal(h.posted[0].data.financials.company.ticker, 'PAYX');
  assert.equal(h.posted[0].data.form.wacc_mode, 'recalculated');

  // 2. Editor not ready yet: nothing sent (editor-ready handler covers it later).
  h = makeContext(bundle);
  h.context.results.set('dcf', { loaded: true, data: bundle });
  await h.context.assemble('dcf', 0);
  assert.equal(h.posted.length, 0, 'no send before editor-ready');

  // 3. Stale generation: nothing sent.
  h = makeContext(bundle);
  h.context.results.set('dcf', { loaded: true, data: bundle });
  h.context.ready.add('dcf');
  h.context.generation = 1;
  await h.context.assemble('dcf', 0);
  assert.equal(h.posted.length, 0, 'no send on stale generation');

  // 4. Normal (non-bundled) path still fetches and sends.
  h = makeContext(bundle);
  h.context.baseline = bundle;
  h.context.ready.add('dcf');
  h.context.request = async () => bundle;
  await h.context.assemble('dcf', 0);
  assert.equal(h.posted.length, 1, 'normal path sends after fetch');
  assert.equal(h.posted[0].type, 'workspace-data');

  console.log('workspace editor fill: 4/4 scenarios pass');
})().catch((error) => { console.error(error); process.exitCode = 1; });
