const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = new Map();
function node(id) { if (!nodes.has(id)) nodes.set(id,{disabled:false,textContent:'',value:'',events:{},addEventListener(k,f){this.events[k]=f;},replaceChildren(){},append(){}}); return nodes.get(id); }
const fields = ['title','scenario_name','thesis'].map(name=>Object.assign(node(name),{name,value:name==='title'?'Research':'Base'}));
const form=node('research-form');
form.elements={namedItem:name=>node(name)};
form.querySelectorAll=selector=>selector==='textarea[name]'?[fields[2]]:[...fields,node('research-save'),node('research-new'),node('research-active')];
form.reset=()=>fields.forEach(el=>el.value='');
let resolveSave;
let sent;
const context={document:{getElementById:node,createElement:()=>({append(){}})},window:{},location:{search:''},URLSearchParams,
 fetch:async(url,opts)=>{if(opts){sent=JSON.parse(opts.body);return new Promise(resolve=>{resolveSave=()=>resolve({ok:true,json:async()=>({id:'saved',ticker:'AAPL',scenario_name:'Base'})});});}return {ok:true,json:async()=>[]};}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/js/research.js','utf8'),context);
const active={valid:true,result:{method:'dcf',input_financials:{company:{ticker:'AAPL'},valuation_date:'2026-10-10'},target_price_12m:100,assumptions:{}}};
(async()=>{
 context.window.researchWorkspace.setContext(active);
 assert.equal(node('research-save').disabled,false);
 context.window.researchWorkspace.setContext(null);
 assert.equal(node('research-save').disabled,true); // Loading cannot save the previous company.
 context.window.researchWorkspace.setContext(active);
 const saving=form.events.submit({preventDefault(){}});
 assert.equal(node('research-new').disabled,true);
 assert.equal(node('research-active').disabled,true);
 assert.equal(node('thesis').disabled,true);
 node('research-new').events.click(); // Defensive handler also ignores a pending save.
 assert.equal(node('title').value,'Research');
 resolveSave(); await saving;
 assert.equal(sent.financials.company.ticker,'AAPL');
 context.window.researchWorkspace.setContext(null);
 assert.equal(node('research-save').disabled,false); // Explicit saved snapshot remains frozen.
 assert.match(node('research-snapshot').textContent,/Frozen research snapshot: AAPL/);
 node('research-new').events.click();
 assert.equal(node('research-save').disabled,true);
 // Execute the actual workspace load callback through its synchronous invalidation.
 const source=fs.readFileSync('static/js/workspace.js','utf8');
 const start=source.indexOf('  $("company-loader").addEventListener("submit"');
 const end=source.indexOf('  async function loadReferences(',start);
 let cleared=false,callback;
 const loadContext={loading:false,generation:0,window:{researchWorkspace:{setContext(x){assert.equal(x,null);cleared=true;}}},
  $:id=>({addEventListener:(k,f)=>callback=f,disabled:false,value:'MSFT'}),status(){},request:()=>new Promise(()=>{})};
 vm.createContext(loadContext);vm.runInContext(source.slice(start,end),loadContext);
 callback({preventDefault(){}});
 assert.equal(cleared,true);
 assert.ok(source.includes('setContext(loading ? null : item)'));
})().catch(error=>{console.error(error);process.exitCode=1;});
