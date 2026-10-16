import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { HyperFormula } from 'hyperformula';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('../../', import.meta.url));
const base = 'http://127.0.0.1:5179';
const server = spawn(process.env.PYTHON || 'python3', ['tests/browser/fixture_server.py'], {cwd:root, stdio:['ignore','pipe','pipe']});
let serverLog = ''; server.stdout.on('data', x => serverLog += x); server.stderr.on('data', x => serverLog += x);
let browser, page;
const output = new URL('./artifacts/', import.meta.url);
await mkdir(output, {recursive:true});
try {
  for (let i=0; i<100; i++) {
    if (server.exitCode !== null) throw Error(serverLog);
    try { if ((await fetch(base+'/health')).ok) break; } catch {}
    await new Promise(r=>setTimeout(r,100));
  }
  browser = await chromium.launch({headless:true, ...(process.env.CHROME_EXECUTABLE ? {executablePath:process.env.CHROME_EXECUTABLE}: {})});
  const context = await browser.newContext({acceptDownloads:true});
  page = await context.newPage(); page.setDefaultTimeout(15000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);
  await page.locator('#workspace-ticker').fill('DEMO');
  const load = page.waitForResponse(r=>r.url().endsWith('/api/load/dcf') && r.request().method()==='POST');
  await page.locator('#company-loader').evaluate(form=>form.requestSubmit());
  const bundle=await (await load).json();
  assert.ok(bundle.preview,JSON.stringify(bundle));
  await page.locator('#live-price').waitFor({state:'visible'});
  const editor=page.frameLocator('iframe[data-method="dcf"]');
  // Regression for the bundled-preview fast path: the editor must actually fill.
  await editor.locator('[name="tax_rate_0"]').waitFor({state:'attached'});
  await page.waitForFunction(()=>{
    const f=document.querySelector('iframe[data-method="dcf"]');
    return Number(f?.contentDocument?.querySelector('[name="tax_rate_0"]')?.value)===23.1;
  });
  assert.equal(bundle.preview.wacc,bundle.brief.dcf.wacc);
  assert.equal(bundle.preview.intrinsic_value,bundle.brief.dcf.intrinsic_value);
  // Expand enclosing detail panels before making a real user input change.
  await editor.locator('[name="tax_rate_0"]').evaluate(el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;});
  const preview=page.waitForResponse(r=>r.url().endsWith('/api/preview/dcf') && r.request().method()==='POST' && new URLSearchParams(r.request().postData()).get('tax_rate_0')==='30');
  await editor.locator('[name="tax_rate_0"]').fill('30');
  const edited=await (await preview).json();
  assert.equal(edited.assumptions.tax_rates[0],.30);
  const costs=bundle.financials.source.capital_costs;
  const wacc=(costs.market_equity_value*costs.cost_of_equity+costs.debt*costs.cost_of_debt*(1-.30))/(costs.market_equity_value+costs.debt);
  assert.equal(edited.wacc,wacc);
  await page.waitForFunction(()=>JSON.parse(document.querySelector('#live-details').textContent || '{}').assumptions?.tax_rates?.[0]===.30);
  assert.deepEqual(edited.input_financials.historical,bundle.financials.historical);
  await page.locator('#research-panel > summary').click();
  await page.locator('#research-title').fill('Browser scenario regression');
  const save=page.waitForResponse(r=>r.url().endsWith('/api/research') && r.request().method()==='POST');
  await page.locator('#research-save').click();
  const saved=await (await save).json();
  assert.ok(saved.id,JSON.stringify(saved));
  assert.equal(saved.snapshot.result.intrinsic_value,edited.intrinsic_value);
  assert.equal(saved.snapshot.assumptions.wacc_override,wacc);
  const download=page.waitForEvent('download');
  await page.locator('#export-xlsx').click();
  const workbook=await download;await workbook.saveAs(fileURLToPath(new URL('scenario.xlsx',output)));
  const parsed = spawnSync(process.env.PYTHON || 'python3', ['tests/browser/workbook_cells.py',fileURLToPath(new URL('scenario.xlsx',output))], {cwd:root,encoding:'utf8'});
  assert.equal(parsed.status,0,parsed.stderr);
  const hf = HyperFormula.buildFromSheets(JSON.parse(parsed.stdout),{licenseKey:'gpl-v3',precisionRounding:15});
  const model = hf.getSheetId('Model');
  const reconciliation=[];
  for (const [field,row] of [['terminal_value',15],['enterprise_value',17],['equity_value',23],['intrinsic_value',25]]) {
    const value=hf.getCellValue({sheet:model,row:row-1,col:1});
    assert.equal(typeof value,'number',JSON.stringify(value));
    assert.ok(Math.abs(value-edited[field])<=Math.max(1e-9,Math.abs(edited[field])*1e-10),`${field}: workbook ${value}, API ${edited[field]}`);
    reconciliation.push({field,workbook:value,api:edited[field]});
  }
  for (let i=0;i<5;i++) {
    const value=hf.getCellValue({sheet:model,row:9,col:i+1});
    assert.ok(Math.abs(value-edited.projections[i].UFCF)<=1e-8,JSON.stringify(edited.projections[i]));
  }
  hf.destroy();
  await writeFile(new URL('workbook-reconciliation.json',output),JSON.stringify(reconciliation,null,2));
  await page.reload();
  const restored=await (await context.request.get(base+'/api/research/'+saved.id)).json();
  assert.deepEqual(restored.snapshot,saved.snapshot);
  await page.goto(base+'/research/'+saved.id);
  assert.ok((await page.locator('body').innerText()).includes('Browser scenario regression'));
  assert.deepEqual(errors,[]);
  await page.screenshot({path:fileURLToPath(new URL('saved-research.png',output)),fullPage:true});
  const report={status:'PASS',scope:'Real headless browser, deterministic local providers, isolated local SQLite; no production writes',initial:{tax:bundle.preview.assumptions.tax_rates,wacc:bundle.preview.wacc,price:bundle.preview.intrinsic_value},edited:{tax:edited.assumptions.tax_rates,wacc:edited.wacc,price:edited.intrinsic_value},saved_reload_equal:true,xlsx_downloaded:true,page_errors:errors};
  await writeFile(new URL('acceptance.json',output),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
} catch (error) {
  if (page) {
    await page.screenshot({path:fileURLToPath(new URL('failure.png',output)),fullPage:true}).catch(()=>{});
    await writeFile(new URL('failure.html',output),await page.content().catch(()=>''));
  }
  throw error;
} finally { await browser?.close();server.kill('SIGTERM');await writeFile(new URL('server.log',output),serverLog); }
