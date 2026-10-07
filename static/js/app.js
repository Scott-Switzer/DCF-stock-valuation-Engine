'use strict';
const valuationForm = document.getElementById('valuation-form');
const storedForm = document.getElementById('saved-form');
if (storedForm) {
  document.getElementById('edit-assumptions').addEventListener('click', () => {
    sessionStorage.setItem('dcf-form', storedForm.value);
  });
}
if (valuationForm) {
  const input = document.getElementById('ticker');
  const suggestions = document.getElementById('ticker-options');
  const message = document.getElementById('provider-message');
  let debounceTimer;
  let searchRequest;
  let selected = -1;
  const setField = (name, value) => {
    const field = valuationForm.elements.namedItem(name);
    if (!field) return;
    if (field.type === 'checkbox') field.checked = value === 'yes';
    else field.value = value == null ? '' : value;
  };
  const notify = (text, error = false) => {
    message.textContent = text;
    message.className = error ? 'notice error' : 'notice';
    message.hidden = !text;
  };
  const showNotes = notes => {
    const details=document.getElementById('provider-notes');
    const list=document.getElementById('provider-notes-list');list.replaceChildren();
    for(const note of notes){const item=document.createElement('li');item.textContent=note;list.append(item);}
    details.hidden=!notes.length;details.open=false;
    details.querySelector('summary').textContent=`${notes.length} data notes · review sources and estimates`;
  };
  const preview = () => {
    try {
      const doc = JSON.parse(document.getElementById('base-document').value);
      document.getElementById('source-preview').textContent = JSON.stringify(doc, null, 2);
      document.getElementById('data-status').textContent = doc.source.kind === 'synthetic' ? 'Synthetic offline example' : `Source: ${doc.source.name}`;
      document.dispatchEvent(new Event('financials-loaded'));
    } catch (_) { /* Server validates the document before valuation. */ }
  };
  const closeSuggestions = () => {
    suggestions.replaceChildren(); suggestions.hidden = true;
    input.setAttribute('aria-expanded', 'false'); selected = -1;
  };
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer); if (searchRequest) searchRequest.abort(); closeSuggestions();
    const query = input.value.trim(); if (query.length < 1) return;
    debounceTimer = setTimeout(async () => {
      searchRequest = new AbortController();
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`, {signal:searchRequest.signal});
        if (!response.ok) return;
        const items = await response.json(); if (query !== input.value.trim()) return;
        for (const item of items) {
          const button = document.createElement('button'); button.type = 'button';
          const symbol = document.createElement('b'); symbol.textContent = item.symbol;
          button.append(symbol, document.createTextNode(item.shortname));
          button.addEventListener('click', () => {input.value = item.symbol; closeSuggestions();});
          suggestions.append(button);
        }
        suggestions.hidden = !items.length; input.setAttribute('aria-expanded', String(!!items.length));
      } catch (error) { if (error.name !== 'AbortError') closeSuggestions(); }
    }, 200);
  });
  input.addEventListener('keydown', event => {
    const buttons = Array.from(suggestions.querySelectorAll('button'));
    if (event.key === 'Escape') closeSuggestions();
    if (['ArrowDown','ArrowUp'].includes(event.key) && buttons.length) {
      event.preventDefault(); selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
      buttons[selected].focus();
    }
    if(event.key==='Enter'){event.preventDefault();closeSuggestions();document.getElementById('load-data').click();}
  });
  suggestions.addEventListener('keydown', event => {
    const buttons = Array.from(suggestions.querySelectorAll('button'));
    if (['ArrowDown','ArrowUp'].includes(event.key) && buttons.length) {
      event.preventDefault(); selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
      buttons[selected].focus();
    }
    if (event.key === 'Escape') {closeSuggestions(); input.focus();}
  });
  document.addEventListener('click', event => {if (!input.contains(event.target) && !suggestions.contains(event.target)) closeSuggestions();});
  const fillForm = values => {for (const [name,value] of Object.entries(values)) setField(name,value); preview(); updateGrowth();};
  const remembered = sessionStorage.getItem('dcf-form');
  if (remembered && !document.querySelector('.notice.error')) {
    try {fillForm(JSON.parse(remembered));} catch (_) {sessionStorage.removeItem('dcf-form');}
    sessionStorage.removeItem('dcf-form');
  }
  function updateGrowth() {
    document.getElementById('growth-warning').hidden = Number(valuationForm.elements.terminal_growth.value) <= 4;
    document.getElementById('terminal-roic').disabled = valuationForm.elements.terminal_mode.value !== 'normalized';
    document.getElementById('terminal-roic').required = valuationForm.elements.terminal_mode.value === 'normalized';
  }
  valuationForm.elements.terminal_growth.addEventListener('input', updateGrowth);
  valuationForm.elements.terminal_mode.addEventListener('change', updateGrowth);
  document.getElementById('load-data').addEventListener('click', async event => {
    const button = event.currentTarget;
    const provider = valuationForm.elements.mode.value;
    const start = Date.now();
    button.disabled = true; button.textContent = 'Loading…';
    notify('Loading company statements, market inputs and starting assumptions…');
    const timer = setInterval(() => notify(`Loading company data… ${Math.floor((Date.now()-start)/1000)}s elapsed.`), 1000);
    try {
      const automatic = provider === 'auto';
      const payload = {provider,ticker:input.value,valuation_date:valuationForm.elements.valuation_date.value,
        equity_risk_premium:Number(document.getElementById('equity-risk-premium').value)/100,
        credit_spread:Number(document.getElementById('credit-spread').value)/100};
      const response = await fetch(automatic ? '/api/load/dcf' : '/api/financials', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Data source unavailable.');
      fillForm(data.form); setField('mode',provider);
      const source = data.financials?.source || {};
      const costs = source.capital_costs;
      document.getElementById('capital-cost-summary').textContent = costs ? 'Starting WACC estimated from loaded capital-cost inputs; review and edit it below.' : 'Review the WACC assumption; this source did not provide a capital-cost calculation.';
      document.getElementById('capital-cost-details').textContent = 'Cost of equity = risk-free rate + beta × equity risk premium. WACC weights equity and after-tax debt costs.';
      if (costs) {
        document.getElementById('capital-cost-summary').textContent = 'Starting WACC estimated from loaded capital-cost inputs. Review the calculation and edit WACC as needed.';
        document.getElementById('capital-cost-details').textContent = 'Cost of equity = risk-free rate + beta × equity risk premium. WACC weights equity and after-tax debt costs.\n\n' + JSON.stringify(costs,null,2);
      }
      clearInterval(timer);
      const warnings = (data.warnings || []).map(item => typeof item === 'string' ? item : JSON.stringify(item));
      showNotes(warnings.concat(source.retrieved_at ? ['Data retrieved: '+source.retrieved_at] : []));
      notify(provider === 'sample' ? 'Loaded synthetic example data. It is not a real security.' : `Loaded ${data.financials?.company?.name || input.value} in ${((Date.now()-start)/1000).toFixed(1)}s. Review and edit the assumptions.${warnings.length ? ' '+warnings.length+' data notes.' : ''}`);
    } catch(error) {clearInterval(timer);notify(error.message, true);}
    finally {clearInterval(timer);button.disabled = false;button.textContent = 'Load company';}
  });
  document.getElementById('derive-drivers').addEventListener('click', () => {
    const fields = {ebit_margin:'ebit',da_margin:'d_and_a',capex_margin:'capex',nwc_margin:'nwc',net_income_margin:'net_income',book_value_margin:'book_value'};
    for (const [driver,metric] of Object.entries(fields)) {
      let sum = 0;
      for (let i=0;i<3;i++) {
        const rev = valuationForm.elements[`h_revenue_${i}`].value;
        const val = valuationForm.elements[`h_${metric}_${i}`].value;
        if (rev === '' || val === '' || Number(rev) <= 0) {notify('Complete all three historical years before deriving ratios.',true);return;}
        sum += Number(val)/Number(rev);
      }
      for (let i=0;i<5;i++) setField(`${driver}_${i}`, (sum/3*100).toFixed(6));
    }
    const tax=valuationForm.elements.h_tax_rate_2.value;
    if (tax==='') {notify('Enter the latest historical tax rate.',true);return;}
    for (let i=0;i<5;i++) setField(`tax_rate_${i}`,tax);
    notify('Filled annual operating drivers from historical averages. Review and edit the forecast assumptions.');
  });
  document.getElementById('import-file').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    if (file.size > 1000000) {notify('JSON file exceeds 1 MB.',true);return;}
    try {
      const doc = JSON.parse(await file.text());
      if (doc.schema_version !== 'dcf-financials-v1' || !Array.isArray(doc.historical) || doc.historical.length !== 3) throw new Error('Use a dcf-financials-v1 document with three historical periods.');
      const values = {base_document:JSON.stringify(doc),mode:'manual',ticker:doc.company.ticker,company_name:doc.company.name,
        sector:doc.company.sector,eligible:doc.company.eligible ? 'yes' : '',valuation_date:doc.valuation_date,
        price:doc.market.price,price_as_of:doc.market.price_as_of,diluted_shares:doc.market.diluted_shares,
        shares_basis:doc.market.shares_basis,bridge_as_of:doc.bridge.as_of,source_name:doc.source.name,...doc.bridge};
      delete values.as_of;
      doc.historical.forEach((row,i) => {values[`period_${i}`]=row.period_end;for (const key of ['revenue','ebit','net_income','capex','d_and_a','nwc','book_value','tax_rate']) values[`h_${key}_${i}`]=row[key] == null ? '' : row[key]*(key==='tax_rate'?100:1);});
      fillForm(values); document.getElementById('derive-drivers').click();notify('Imported financial document. Review all forecast assumptions before calculating.');
    } catch(error) {notify(error.message || 'Invalid financial JSON.',true);}
  });
  valuationForm.addEventListener('invalid', event => {
    for (let parent=event.target.parentElement; parent; parent=parent.parentElement) if(parent.tagName==='DETAILS') parent.open=true;
  }, true);
  valuationForm.addEventListener('submit', event => {
    if (Number(valuationForm.elements.terminal_growth.value) >= Number(valuationForm.elements.wacc.value)) {
      event.preventDefault();notify('Terminal growth must be lower than WACC.',true);valuationForm.elements.terminal_growth.focus();return;
    }
    document.getElementById('calculate-button').disabled = true;
    document.getElementById('calculate-button').textContent = 'Calculating…';
  });
  preview();updateGrowth();
}
