(() => {
  let selected, index, nextCursor, currentParams, prepared;
  const byId = id => document.getElementById(id);
  const status = text => { byId('screen-status').textContent = text; };
  async function api(path, body) {
    const response = await fetch(path, body === undefined ? {} : {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
    return result;
  }
  async function showPage(params) {
    byId('screen-results').replaceChildren();
    byId('prepare-section').hidden = true;
    selected = index = prepared = null;
    status('Loading published screen…');
    try {
      currentParams = new URLSearchParams(params);
      byId('next-page').hidden = true;
      const page = await api('/api/research-screen?' + params);
      index = page.index_id;
      nextCursor = page.next_cursor;
      byId('next-page').hidden = !nextCursor;
      status(`${page.matches.length} of ${page.total_matches} matches. Evidence cutoff ${page.archive_cutoff}. Index ${index}`);
      for (const row of page.matches) {
        const button = document.createElement('button');
        button.textContent = `${row.label} · CIK ${row.cik} · ${row.share_basis || row.share_absence || 'Shares unavailable'}`;
        button.addEventListener('click', () => {
          selected = row; prepared = null;
          byId('scenario-form').reset();
          byId('prepare-section').hidden = false;
          byId('selected-company').textContent = `${row.label} · CIK ${row.cik}`;
          byId('screen-ticker').value = '';
          byId('valuation-request').value = '';
          byId('screen-evidence').textContent = `Issuer ${row.label} · CIK ${row.cik}\nSector: ${row.sector || 'Unavailable'}\nShare basis: ${row.share_basis || row.share_absence || 'Unavailable'}\nEligible methods: ${row.methods.join(', ')}\nMissing company inputs: ${row.missing.join(', ') || 'None reported by the screen'}`;
          byId('valuation-result').textContent = ''; byId('valuation-response').value = '';
        });
        const line = document.createElement('p'); line.append(button);
        byId('screen-results').append(line);
      }
    } catch (error) { status(error.message); }
  }
  byId('screen-form').addEventListener('submit', event => {
    event.preventDefault();
    const params = new URLSearchParams(new FormData(event.target));
    for (const [key, value] of [...params]) if (!value) params.delete(key);
    showPage(params);
  });
  byId('next-page').addEventListener('click', () => {
    if (!nextCursor || !index) return;
    const params = new URLSearchParams(currentParams);
    params.set('cursor', nextCursor); params.set('expected_index_id', index);
    showPage(params);
  });
  byId('prepare-button').addEventListener('click', async () => {
    if (!selected) return;
    try {
      const result = await api('/api/research-screen/prepare', {
        ticker: byId('screen-ticker').value, cik: selected.cik, expected_index_id: index
      });
      prepared = result;
      byId('valuation-date').value = new Date().toISOString().slice(0, 10);
      byId('screen-evidence').textContent = `Source: ${result.financials.source.name}\nFinancial cutoff: ${result.financials.source.historical_cutoff}\nEngine release: ${result.financials.source.release_id}\nTo calculate: ${result.valuation_blockers.join(', ')}\nOther source gaps: ${Object.keys(result.source_missing_fields).length} (retained in the reproducible request).\nEquity and per-share values require a separately verified claims bridge.`;
      byId('valuation-request').value = JSON.stringify(result.request_template, null, 2);
      status('Financial history loaded. Fill the explicit assumptions before calculating.');
    } catch (error) { status(error.message); }
  });
  byId('scenario-form').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      if (!prepared) throw new Error('Load the selected financial history first');
      const body = structuredClone(prepared.request_template);
      const tokens = byId('growth-rates').value.split(',').map(value => value.trim());
      if (tokens.length !== 5 || tokens.some(value => !value || !Number.isFinite(Number(value)))) throw new Error('Enter five numeric growth percentages');
      body.revenue_growth_rates = tokens.map(value => Number(value) / 100);
      body.valuation_date = byId('valuation-date').value;
      body.terminal_growth = Number(byId('terminal-growth').value) / 100;
      body.terminal_roic = Number(byId('terminal-roic').value) / 100;
      body.suitable = byId('suitable').checked;
      body.benchmark_selections = Object.fromEntries(Object.entries(prepared.benchmark_references).map(([target, ref]) => [target, {...ref, subject: byId('benchmark-industry').value.trim(), mode:'historical', source:'zion'}]));
      byId('valuation-request').value = JSON.stringify(body, null, 2);
      if (body.cik !== selected.cik) throw new Error('Selected issuer and valuation request differ');
      const result = await api('/api/calculate/enterprise', body);
      const money = value => new Intl.NumberFormat('en-US', {style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
      byId('valuation-result').textContent = `Enterprise scenario: ${money(result.enterprise_value)}\nValuation date: ${result.valuation_date}\nFinancial cutoff: ${result.financial_cutoff}\nWACC benchmark: ${(result.wacc * 100).toFixed(2)}%\nEquity value: unavailable\nPer-share value: unavailable\nAssumption-driven scenario; inspect the reproducible request for source versions.`;
      byId('valuation-response').value = JSON.stringify(result, null, 2);
      status('Enterprise scenario calculated. Equity and per-share values remain unavailable.');
    } catch (error) { status(error.message); }
  });
})();
