const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = new Map();
class Element {
  constructor() { this.children=[]; this.events={}; this.value=''; this.textContent=''; this.disabled=false; }
  replaceChildren(...children) { this.children=children; this.textContent=''; }
  append(...children) { this.children.push(...children); }
  addEventListener(name, callback) { this.events[name]=callback; }
}
const el=id=>{if(!nodes.has(id)) nodes.set(id,new Element());return nodes.get(id);};
const calls=[];
const reply=(status,body)=>({ok:status===200,status,json:async()=>body});
let postReply=reply(401,{});
const window={events:{}, addEventListener(name,fn){this.events[name]=fn;}, fetch:async(url,options)=>{
  calls.push({url,options});
  if(options.method==='POST') return postReply;
  if(options.method==='DELETE') return reply(200,{owner_benchmark_access:false});
  return reply(200,{symbols:[],total_matches:0,symbol_count:0,next_cursor:null});
}};
const document={getElementById:el,createElement:()=>new Element()};
vm.runInNewContext(fs.readFileSync('static/js/data-workspace.js','utf8'),{window,document,AbortController,URLSearchParams,Map,Set,JSON});
const connect=async()=>{el('data-owner-key').value='synthetic-owner-key'; await el('data-connect-form').events.submit({preventDefault(){}});};
(async()=>{
  await connect();
  assert.equal(calls.filter(c=>c.options.method==='POST').length,0);
  await el('data-benchmark-grant').events.click();
  assert.match(el('data-grant-status').textContent,/log in/i);
  const grant=calls.find(c=>c.options.method==='POST');
  assert.equal(grant.url,'/api/account/data-access');
  assert.equal(grant.options.headers.Authorization,'Bearer synthetic-owner-key');
  assert.equal(grant.options.credentials,'same-origin');
  postReply=reply(200,{owner_benchmark_access:true,expires_at:123456});
  await el('data-benchmark-grant').events.click();
  assert.match(el('data-grant-status').textContent,/15 minutes/i);
  await el('data-disconnect').events.click();
  const revoke=calls.at(-1);
  assert.equal(revoke.options.method,'DELETE');
  assert.equal(revoke.options.credentials,'same-origin');
  assert.equal(revoke.options.keepalive,true);
  assert.ok(!revoke.options.headers?.Authorization);
  assert.equal(el('data-benchmark-grant').disabled,true);
  await connect();
  let complete;
  postReply=new Promise(resolve=>{complete=resolve;});
  const granting=el('data-benchmark-grant').events.click();
  const revoking=el('data-disconnect').events.click();
  assert.equal(el('data-owner-key').value,'');
  assert.equal(el('data-controls').disabled,true);
  complete(reply(200,{owner_benchmark_access:true}));
  await granting; await revoking;
  assert.equal(calls.at(-1).options.method,'DELETE');
  assert.doesNotMatch(el('data-grant-status').textContent,/enabled/i);
  window.events.pagehide();
  assert.equal(calls.at(-1).options.method,'DELETE');
  assert.equal(calls.at(-1).options.keepalive,true);
  assert.ok(calls.filter(c=>c.url.startsWith('/api/data/')).every(c=>c.options.credentials==='omit'));
})().catch(error=>{console.error(error);process.exitCode=1;});
