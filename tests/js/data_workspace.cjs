const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor(tag = 'div') { this.tagName = tag; this.children = []; this.events = {}; this.value = ''; this.disabled = false; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent ?? '').join(''); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  addEventListener(name, fn) { this.events[name] = fn; }
  setAttribute(name, value) { this[name] = value; }
}
const nodes = new Map();
const byId = id => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
const document = { getElementById: byId, createElement: tag => new Element(tag) };
const window = { events: {}, addEventListener(name, fn) { this.events[name] = fn; } };
const calls = [];
const dataCalls = () => calls.filter(call => call.url.startsWith("/api/data/"));
let nextResponse = null;
const responses = [];
const reply = body => ({ ok: true, status: 200, json: async () => body });
window.fetch = async (url, options) => {
  calls.push({url, options});
  if (responses.length) return responses.shift();
  if (nextResponse) { const response = nextResponse; nextResponse = null; return response; }
  if (url.includes('/stock-history')) return reply({symbols: [{symbol:'TEST', date_min:'2000-01-03', date_max:'2000-01-04', normalized_rows:2}], symbol_count:2629, total_matches:1, release_id:'r', next_cursor:null});
  return reply({entries:[], matching_releases:0, next_offset:null});
};
const context = {window, document, URLSearchParams, AbortController, JSON, Map, Set};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/js/data-workspace.js','utf8'), context);
const submit = id => byId(id).events.submit({preventDefault(){}});
(async () => {
  assert.equal(calls.length, 0);
  byId('data-owner-key').value = 'owner-fixture-key';
  await submit('data-connect-form');
  assert.equal(byId('data-owner-key').value, '');
  assert.equal(dataCalls()[0].options.headers.Authorization, 'Bearer owner-fixture-key');
  assert.equal(dataCalls()[0].options.credentials, 'omit');
  assert.equal(dataCalls()[0].options.cache, 'no-store');
  assert.equal(dataCalls()[0].options.redirect, 'error');
  assert.match(dataCalls()[0].url, /^\/api\/data\/stock-history\?/);
  assert.match(dataCalls()[0].url, /source=crsp/);
  byId('data-permno').value='10001';
  await submit('data-prices-form');
  assert.match(dataCalls().at(-1).url, /permno=10001/);
  assert.ok(!dataCalls().at(-1).url.includes('symbol='));
  assert.ok(!dataCalls()[0].url.includes('owner-fixture-key'));
  assert.match(byId('data-stock-catalog').textContent, /TEST/);
  assert.equal(byId('data-controls').disabled, false);
  let finish;
  nextResponse = new Promise(resolve => { finish = resolve; });
  const pending = submit('data-stocks-form');
  await byId('data-disconnect').events.click();
  assert.equal(byId('data-controls').disabled, true);
  assert.equal(byId('data-stock-catalog').textContent, '');
  assert.ok(dataCalls().at(-1).options.signal.aborted);
  finish(reply({symbols:[{symbol:'LATE_PRIVATE_VALUE'}], total_matches:1, next_cursor:null}));
  await pending;
  assert.equal(byId('data-stock-catalog').textContent, '');
  const before = calls.length;
  await submit('data-stocks-form');
  assert.equal(calls.length, before);
  byId('data-owner-key').value='another-key';
  await submit('data-connect-form');
  byId('data-symbol').value='TEST';
  byId('data-date-from').value='2000-01-03';
  responses.push(reply({symbol:'TEST', prices:[{session_date:'2000-01-03', currency:'SYNTHETIC', open:'1.0', high:'2.0', low:'0.5', close:'1.5', volume:'3'}], gaps:[], total_matches:2, next_cursor:'cursor-one', release_id:'release-fixture'}));
  await submit('data-prices-form');
  assert.equal(new URLSearchParams(calls.at(-1).url.split('?')[1]).get('limit'), '500');
  assert.match(byId('data-prices').textContent, /SYNTHETIC/);
  responses.push(reply({symbol:'TEST', prices:[], total_matches:2, next_cursor:null, release_id:'release-fixture'}));
  await byId('data-prices-next').events.click();
  const paged = new URLSearchParams(calls.at(-1).url.split('?')[1]);
  assert.equal(paged.get('cursor'), 'cursor-one');
  assert.equal(paged.get('expected_release_id'), 'release-fixture');
  byId('data-store').value='research';
  responses.push(reply({prefixes:['folder/'], objects:[{path:'folder/native.parquet',etag:'fixture-etag',bytes:20}], cursor:null}));
  await submit('data-files-form');
  function find(element, label) { if (element.tagName==='button' && element.textContent===label) return element; for(const child of element.children || []) { const match=find(child,label); if(match) return match; } }
  responses.push(reply({data:{row_count:1,columns:[{name:'native_field',type:'BYTE_ARRAY'}]}}));
  responses.push(reply({data:{columns:[{name:'native_field'}],rows:[{native_field:'<img src=x onerror=bad()>'}]}}));
  await find(byId('data-file-list'),'Schema & 10 rows').events.click();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls.at(-1).options.headers['If-Match'], '\"fixture-etag\"');
  assert.equal(new URLSearchParams(calls.at(-1).url.split('?')[1]).get('limit'),'10');
  assert.match(byId('data-native-rows').textContent, /<img src=x onerror=bad\(\)>/);
  assert.ok(dataCalls().every(call=>call.options.credentials==='omit'));
  assert.ok(calls.every(call=>!call.url.includes('/object?')));
  let finishNative;
  nextResponse = new Promise(resolve=>{finishNative=resolve;});
  const staleNative = find(byId('data-file-list'),'Schema & 10 rows').events.click();
  responses.push(reply({prefixes:[],objects:[],cursor:null}));
  await submit('data-files-form');
  const afterNewFolder=calls.length;
  finishNative(reply({data:{row_count:999,columns:[{name:'OLD_PRIVATE_SCHEMA'}]}}));
  await staleNative;
  assert.equal(calls.length,afterNewFolder);
  assert.equal(byId('data-native-schema').textContent,'');
  responses.push(reply({prefixes:[],objects:[],cursor:null}));
  await byId('data-browse-wrds').events.click();
  assert.equal(byId('data-store').value,'research');
  assert.equal(byId('data-prefix').value,'raw/wrds/');
  assert.match(calls.at(-1).url,/^\/api\/data\/datasets\/research\/objects/);
  assert.equal(new URLSearchParams(calls.at(-1).url.split('?')[1]).get('prefix'),'raw/wrds/');
  window.events.pagehide();
  assert.equal(byId('data-controls').disabled, true);
  assert.equal(byId('data-stock-catalog').textContent, '');
})().catch(error => { console.error(error); process.exitCode = 1; });
