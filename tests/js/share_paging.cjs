const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function element() {
  return { children: [], disabled: false, set textContent(value) {this.text=value; this.children=[];},
    get textContent() {return this.text;}, appendChild(e) {this.children.push(e);},
    addEventListener(event, handler) {this[event] = handler;},
    parentNode: {insertBefore(e) {paging = e;}} };
}
let paging;
const list = element(), message = element(), calls = [];
const pending = [];
const context = {document: {getElementById: id => id === 'share-list' ? list : message, createElement: element},
  window: {location: {origin: 'https://test.invalid'}},
  fetch(url) {calls.push(url); return new Promise((resolve, reject) => pending.push({resolve,reject}));}};
vm.runInNewContext(fs.readFileSync('static/js/shares.js', 'utf8'), context);
const flush = () => new Promise(resolve => setImmediate(resolve));
const shares = Array.from({length:50}, (_,i)=>({token:String(i), created_at:'2026-10-10'}));
(async () => {
  const [previous,next,refresh] = paging.children;
  pending.shift().reject(new Error('initial failure')); await flush();
  assert.equal(refresh.disabled,false);
  refresh.click(); assert.equal(calls.at(-1),'/api/shares?offset=0');
  pending.shift().resolve({ok:true,json:async()=>shares}); await flush();
  assert.equal(previous.disabled, true); assert.equal(next.disabled, false);
  next.click(); next.click();
  assert.deepEqual(calls.slice(-2), ['/api/shares?offset=0','/api/shares?offset=50']);
  assert.equal(next.disabled,true);
  pending.shift().reject(new Error('offline')); await flush();
  assert.equal(previous.disabled,true); assert.equal(next.disabled,false);
  next.click(); assert.equal(calls.at(-1),'/api/shares?offset=50');
  pending.shift().resolve({ok:true,json:async()=>shares.slice(0,1)}); await flush();
  assert.equal(previous.disabled,false); assert.equal(next.disabled,true);
  previous.click(); assert.equal(calls.at(-1),'/api/shares?offset=0');
  pending.shift().resolve({ok:true,json:async()=>shares}); await flush();
  next.click(); // Pending list response may predate a revoke on the visible page.
  list.children[0].children[2].click();
  pending.splice(1,1)[0].resolve({ok:true}); await flush();
  const before = calls.length;
  pending.shift().resolve({ok:true,json:async()=>shares}); await flush();
  assert.equal(calls.length,before+1);
  assert.equal(calls.at(-1),'/api/shares?offset=50');
  pending.shift().resolve({ok:true,json:async()=>[{...shares[0],revoked_at:'2026-10-10'}]}); await flush();
  assert.match(list.children[0].children[0].textContent,/Revoked/);
  assert.equal(list.children[0].children.length,2); // Label and copy, no revoke.
})().catch(error => {console.error(error); process.exitCode=1;});
