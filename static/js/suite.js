'use strict';
const suiteForm = document.getElementById('suite-form');
const suiteSaved = document.getElementById('suite-saved-form');
if (suiteSaved) {
  document.getElementById('suite-edit').addEventListener('click',()=>sessionStorage.setItem('suite-form',suiteSaved.value));
}
if (suiteForm) {
  const method=suiteForm.dataset.method;
  const message=document.getElementById('suite-message');
  const notify=(text,error=false)=>{message.textContent=text;message.hidden=!text;message.className=error?'notice error':'notice';};
  const showNotes = notes => {
    const details=document.getElementById('suite-notes');
    const list=document.getElementById('suite-notes-list');list.replaceChildren();
    for(const note of notes){const item=document.createElement('li');item.textContent=note;list.append(item);}
    details.hidden=!notes.length;details.open=false;
    details.querySelector('summary').textContent=`${notes.length} data notes · review sources and estimates`;
  };
  const preview=()=>{
    try {const doc=JSON.parse(suiteForm.elements.base_document.value);
      document.getElementById('suite-source').textContent=JSON.stringify(doc,null,2);
      document.getElementById('suite-status').textContent=doc.source.kind==='synthetic'||doc.source.origin_kind==='synthetic'?'Synthetic example origin':doc.source.name;
      document.dispatchEvent(new Event('financials-loaded'));
    } catch (_) { /* Server validates input. */ }
  };
  const fill=values=>{
    for (const field of suiteForm.elements) {
      if (!field.name) continue;
      if (field.type==='checkbox') {field.checked=values[field.name]==='yes';continue;}
      if (!Object.prototype.hasOwnProperty.call(values,field.name)) continue;
      const value=values[field.name];
      if (field.type!=='file' && field.type!=='submit') field.value=value==null?'':value;
    }
    preview();
  };
  const remembered=sessionStorage.getItem('suite-form');
  if (remembered&&!document.querySelector('.notice.error')) {
    try {const values=JSON.parse(remembered);const doc=JSON.parse(values.base_document);
      if (doc.schema_version===`${method}-financials-v1`) fill(values);
    } catch (_) { /* Keep the current inputs if restoration is invalid. */ }
    sessionStorage.removeItem('suite-form');
  }
  suiteForm.elements.ticker.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();document.getElementById('suite-load').click();}});
  document.getElementById('suite-load').addEventListener('click',async event=>{
    const button=event.currentTarget; const start=Date.now();
    button.disabled=true;button.textContent='Loading…';notify('Loading company financials and starting assumptions…');
    const timer=setInterval(()=>notify(`Loading company data… ${Math.floor((Date.now()-start)/1000)}s elapsed.`),1000);
    try {
      const premium=document.getElementById('equity-risk-premium');
      const payload={ticker:suiteForm.elements.ticker.value,valuation_date:suiteForm.elements.valuation_date.value};
      if(premium) payload.equity_risk_premium=Number(premium.value)/100;
      const response=await fetch(`/api/load/${method}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data=await response.json();if(!response.ok)throw new Error(data.error||'Unable to load this company.');
      fill(data.form);const source=data.financials?.source||{};
      const costs=source.capital_costs;
      if(document.getElementById('capital-cost-details')) {
        document.getElementById('capital-cost-details').textContent='';
        document.getElementById('capital-cost-summary').textContent='Review the required return assumption; this source did not provide a capital-cost calculation.';
      }
      if(costs&&document.getElementById('capital-cost-details')) {
        document.getElementById('capital-cost-details').textContent=JSON.stringify(costs,null,2);
        document.getElementById('capital-cost-summary').textContent='Required return estimated from loaded capital-cost inputs; review and edit it above.';
      }
      clearInterval(timer);
      const warnings=(data.warnings||[]).map(item=>typeof item==='string'?item:JSON.stringify(item));
      showNotes(warnings.concat(source.retrieved_at ? ['Data retrieved: '+source.retrieved_at] : []));
      notify(`Loaded ${data.financials?.company?.name||suiteForm.elements.ticker.value} in ${((Date.now()-start)/1000).toFixed(1)}s. Review and edit your assumptions.${warnings.length?' '+warnings.length+' data notes.':''}`);
    }catch(error){clearInterval(timer);notify(error.message||'Unable to load company data.',true);}
    finally{clearInterval(timer);button.disabled=false;button.textContent='Load company';}
  });
  const load=async blank=>{
    try {const response=await fetch(`/api/sample/${method}${blank?'?blank=1':''}`);
      const data=await response.json();if(!response.ok)throw new Error(data.error);
      fill(data.form);notify(blank?'Blank model loaded. Enter sourced financials and confirm suitability.':'Synthetic example loaded; these are not real-company inputs.');
    }catch(error){notify(error.message||'Unable to load inputs.');}
  };
  document.getElementById('suite-demo').addEventListener('click',()=>load(false));
  document.getElementById('suite-blank').addEventListener('click',()=>load(true));
  document.getElementById('suite-import').addEventListener('change',async event=>{
    const file=event.target.files[0];if(!file)return;
    if(file.size>1000000){notify('JSON exceeds 1 MB.');return;}
    try {const raw=JSON.parse(await file.text());
      const response=await fetch(`/api/import/${method}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(raw)});
      const data=await response.json();if(!response.ok)throw new Error(data.error);
      fill(data.form);notify('Imported inputs. Review all assumptions before calculating.');
    }catch(error){notify(error.message||'Invalid JSON document.');}
  });
  suiteForm.addEventListener('invalid',event=>{
    for(let parent=event.target.parentElement;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
  },true);
  suiteForm.addEventListener('submit',event=>{
    if(method==='ddm'&&Number(suiteForm.elements.terminal_growth.value)>=Number(suiteForm.elements.required_return.value)){
      event.preventDefault();notify('Terminal dividend growth must be below the required return on equity.');return;
    }
    document.getElementById('suite-calculate').disabled=true;
    document.getElementById('suite-calculate').textContent='Calculating…';
  });
  const handoff=sessionStorage.getItem('suite-dcf-transfer');
  if(handoff) {
    sessionStorage.removeItem('suite-dcf-transfer');
    (async()=>{
      try {const transfer=JSON.parse(handoff);if(transfer.method!==method)return;
        const response=await fetch(`/api/from-dcf/${method}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(transfer.payload)});
        const data=await response.json();if(!response.ok)throw new Error(data.error);
        fill(data.form);notify(method==='ddm'?'Company inputs carried from DCF. Enter verified common dividends and confirm dividend-model suitability.':'Year-one forecast carried from DCF. Enter comparable multiples and confirm their suitability.');
      }catch(error){notify(error.message||'Unable to carry the DCF inputs.');}
    })();
  }
  preview();
}

const dcfTransfer = document.getElementById('dcf-transfer-payload');
if (dcfTransfer) {
  for (const link of document.querySelectorAll('.suite-transfer')) {
    link.addEventListener('click',()=>sessionStorage.setItem('suite-dcf-transfer',JSON.stringify({method:link.dataset.method,payload:JSON.parse(dcfTransfer.value)})));
  }
}
