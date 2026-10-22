// Live production browser acceptance. Requires NODE_PATH pointing at installed Playwright.
const fs = require('fs');
const {chromium} = require('playwright');
const base='https://dcf-valuation-engine.scswitzer.workers.dev';
const out=process.argv[2], auditPath=process.argv[3];
if(!out||!auditPath)throw Error('Usage: node verify_production_owner_browser.cjs OUTPUT AUDIT_RESULTS');
const env=Object.fromEntries(fs.readFileSync(process.env.HOME+'/.config/zion/private-api.env','utf8').split(/\r?\n/).filter(x=>x.includes('=')&&!x.startsWith('#')).map(x=>{const p=x.replace(/^export /,'').indexOf('=');x=x.replace(/^export /,'');return[x.slice(0,p),x.slice(p+1).trim().replace(/^["']|["']$/g,'')]}));
let stage='startup';
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const checks={}, errors=[];
 page.on('pageerror',()=>errors.push('pageerror'));
 stage='page'; const response=await page.goto(base+'/data'); checks.page=response.status()===200;
 checks.starts_disconnected=await page.locator('#data-controls').evaluate(n => n.disabled);
 stage='connect'; await page.locator('#data-owner-key').fill(env.ZION_PRIVATE_API_TOKEN); await page.locator('#data-connect-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelectorAll('#data-stock-catalog tbody tr').length>0,{timeout:60000});
 checks.symbol_catalog_rows=await page.locator('#data-stock-catalog tbody tr').count(); checks.password_cleared=(await page.locator('#data-owner-key').inputValue())==='';
 stage='stock'; await page.locator('#data-symbol').fill('AAPL'); await page.locator('#data-prices-form button').click();
 await page.waitForFunction(()=>document.querySelectorAll('#data-prices tbody tr').length>0,{timeout:60000});
 checks.stock_ohlcv_rows=await page.locator('#data-prices tbody tr').count();
 stage='collections'; await page.locator('#data-collections-form button').click(); await page.waitForFunction(()=>document.querySelectorAll('#data-collection-list tbody tr').length>0,{timeout:60000});
 checks.catalog_rows=await page.locator('#data-collection-list tbody tr').count();
 const audit=JSON.parse(fs.readFileSync(auditPath,'utf8'));
 const sample=audit.results.find(x=>x.http_status===200&&x.column_count<20&&x.column_count>1&&x.source_bytes<100000&&x.footer_declared_row_count>=10);
 if(!sample)throw Error('sample absent');
 stage='files'; await page.locator('#data-store').selectOption('research'); await page.locator('#data-prefix').fill(sample.path); await page.locator('#data-files-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelectorAll('#data-file-list tbody tr').length>0,{timeout:60000});
 await page.locator('#data-file-list button').filter({hasText:'Schema & 10 rows'}).first().click();
 stage='native_rows'; await page.waitForFunction(()=>document.querySelectorAll('#data-native-rows tbody tr').length>0,{timeout:60000});
 checks.native_schema_fields=await page.locator('#data-native-schema tbody tr').count(); checks.native_preview_rows=await page.locator('#data-native-rows tbody tr').count();
 checks.no_storage=await page.evaluate(()=>localStorage.length===0&&sessionStorage.length===0);
 stage='disconnect'; await page.locator('#data-disconnect').click();
 checks.disconnected=await page.locator('#data-controls').evaluate(n => n.disabled);
 checks.records_cleared=await page.evaluate(()=>['data-stock-catalog','data-prices','data-collection-list','data-file-list','data-native-rows'].every(id=>document.getElementById(id).textContent===''));
 checks.javascript_errors=errors.length;
 const pass=checks.page&&checks.starts_disconnected&&checks.symbol_catalog_rows>0&&checks.password_cleared&&checks.stock_ohlcv_rows>0&&checks.catalog_rows>0&&checks.native_preview_rows===10&&checks.no_storage&&checks.disconnected&&checks.records_cleared&&!errors.length;
 const receipt={status:pass?'PASS':'FAIL',origin:base,checks,private_values_printed:0,screenshots_created:0,provider_requests:0};
 fs.writeFileSync(out,JSON.stringify(receipt,null,2),{flag:'wx'});console.log(JSON.stringify(receipt)); if(!pass)process.exitCode=1;
 }finally{await browser.close();}
})().catch(()=>{console.log(JSON.stringify({status:'FAIL',stage,private_values_printed:0}));process.exitCode=1;});
