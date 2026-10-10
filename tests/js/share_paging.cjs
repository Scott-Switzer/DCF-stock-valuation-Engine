const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function element() {
  return { children: [], disabled: false, appendChild(e) {this.children.push(e);},
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
  pending.shift().resolve({ok:true,json:async()=>shares}); await flush();
  const [previous,next] = paging.children;
  assert.equal(previous.disabled, true); assert.equal(next.disabled, false);
  next.click(); next.click();
  assert.deepEqual(calls, ['/api/shares?offset=0','/api/shares?offset=50']);
  assert.equal(next.disabled,true);
  pending.shift().reject(new Error('offline')); await flush();
  assert.equal(previous.disabled,true); assert.equal(next.disabled,false);
  next.click(); assert.equal(calls.at(-1),'/api/shares?offset=50');
  pending.shift().resolve({ok:true,json:async()=>shares.slice(0,1)}); await flush();
  assert.equal(previous.disabled,false); assert.equal(next.disabled,true);
  previous.click(); assert.equal(calls.at(-1),'/api/shares?offset=0');
})().catch(error => {console.error(error); process.exitCode=1;});
