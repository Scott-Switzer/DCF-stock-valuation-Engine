const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const workspace = fs.readFileSync('static/js/workspace.js', 'utf8');
const code = workspace.slice(workspace.indexOf('  function templateToForm('), workspace.indexOf('  async function loadTemplates('));
const current = {valuation_basis:'cuig_forward', peer_pe_0:'42', peer_basis_0:'forward_year_one', peer_period_0:'2027-12-31'};
const context = {results:new Map([['relative',{form:current,data:{form:{peer_pe_0:'20'}}}]]),baseline:null};
vm.createContext(context); vm.runInContext(code,context);
const restored = context.templateToForm('relative',{included_methods:['pe'],valuation_basis:'matched_forward'});
assert.equal(restored.valuation_basis,'matched_forward');
assert.equal(restored.peer_pe_0,'42');
assert.equal(restored.peer_period_0,'2027-12-31');
assert.equal(restored.include_pe,'yes');
assert.equal(context.templateToForm('relative',{included_methods:['pe']}).valuation_basis,'cuig_forward');
assert.equal(current.valuation_basis,'cuig_forward'); // Template application does not mutate previous state.

// Execute the shipped peer-field preservation expression used during replacement.
const editor = fs.readFileSync('static/js/editor.js','utf8');
const beforeStart = editor.indexOf('    const before = Array.from(');
const beforeEnd = editor.indexOf('    peerBox.replaceChildren();',beforeStart);
const fields = new Map();
for(let i=0;i<4;i++) for(const key of ['ticker','name','as_of','source','basis','period','ev_revenue','ev_ebitda','ev_ebit','pe','pb'])
  fields.set(`peer_${key}_${i}`,{value:`edited-${key}-${i}`});
const peerContext={field:name=>fields.get(name)};
vm.createContext(peerContext); vm.runInContext(editor.slice(beforeStart,beforeEnd)+'globalThis.saved = before;',peerContext);
assert.equal(peerContext.saved[1].basis,'edited-basis-1');
assert.equal(peerContext.saved[1].period,'edited-period-1');
