'use strict';
const suiteForm = document.getElementById('suite-form');
const suiteSaved = document.getElementById('suite-saved-form');
if (suiteSaved) {
  document.getElementById('suite-edit').addEventListener('click',()=>sessionStorage.setItem('suite-form',suiteSaved.value));
}
if (suiteForm) {
  const method=suiteForm.dataset.method;
  const message=document.getElementById('suite-message');
  const notify=text=>{message.textContent=text;message.hidden=!text;};
  const preview=()=>{
    try {const doc=JSON.parse(suiteForm.elements.base_document.value);
      document.getElementById('suite-source').textContent=JSON.stringify(doc,null,2);
      document.getElementById('suite-status').textContent=doc.source.kind==='synthetic'||doc.source.origin_kind==='synthetic'?'Synthetic example origin':doc.source.name;
    } catch (_) { /* Server validates input. */ }
  };
  const fill=values=>{
    for (const field of suiteForm.elements) {
      if (!field.name) continue;
      const value=values[field.name];
      if (field.type==='checkbox') field.checked=value==='yes';
      else if (field.type!=='file' && field.type!=='submit') field.value=value==null?'':value;
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
