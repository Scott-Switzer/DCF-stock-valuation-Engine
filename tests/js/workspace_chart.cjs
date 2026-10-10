const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
// Exercise the shipped chart adapter with the method-specific API documents.
const source = fs.readFileSync('static/js/workspace.js','utf8');
const adapter = source.slice(source.indexOf('  function chart(r) {'),source.indexOf('  function bridge(r) {'));
const calls = [];
const context = {$:()=>({replaceChildren(){}}), baseline:{financials:{historical:[{revenue:999}]}},
 window:{financialCharts:{renderProjectionChart(...args){calls.push(args);}}}};
vm.createContext(context); vm.runInContext(adapter,context);
const dividends = [{period_end:'2025-12-31',value:100}];
const forecast = [{year:1,dividends:105}];
context.chart({method:'ddm',input_financials:{source:{common_dividends:{historical:dividends}}},projections:forecast});
assert.equal(calls[0][1],dividends); assert.equal(calls[0][2],forecast);
context.chart({method:'ddm',input_financials:{source:{}},projections:forecast});
assert.equal(calls[1][1].length,0);
context.chart({method:'relative',input_financials:{source:{}}});
assert.equal(calls.length,2);
context.chart({method:'dcf',input_financials:{historical:dividends},projections:forecast});
assert.equal(calls[2][1],dividends);
