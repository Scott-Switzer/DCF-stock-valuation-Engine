(() => {
  let selected, index;
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
  byId('screen-form').addEventListener('submit', async event => {
    event.preventDefault();
    byId('screen-results').replaceChildren();
    byId('prepare-section').hidden = true;
    selected = index = null;
    status('Loading published screen…');
    try {
      const params = new URLSearchParams(new FormData(event.target));
      if (!params.get('sector')) params.delete('sector');
      const page = await api('/api/research-screen?' + params);
      index = page.index_id;
      status(`${page.matches.length} of ${page.total_matches} matches. Evidence cutoff ${page.archive_cutoff}. Index ${index}`);
      for (const row of page.matches) {
        const button = document.createElement('button');
        button.textContent = `${row.label} · CIK ${row.cik} · ${row.share_basis || row.share_absence || 'Shares unavailable'}`;
        button.addEventListener('click', () => {
          selected = row;
          byId('prepare-section').hidden = false;
          byId('selected-company').textContent = `${row.label} · CIK ${row.cik}`;
          byId('screen-ticker').value = '';
          byId('valuation-request').value = '';
          byId('screen-evidence').textContent = JSON.stringify(row, null, 2);
          byId('valuation-result').textContent = '';
        });
        const line = document.createElement('p'); line.append(button);
        byId('screen-results').append(line);
      }
    } catch (error) { status(error.message); }
  });
  byId('prepare-button').addEventListener('click', async () => {
    if (!selected) return;
    try {
      const result = await api('/api/research-screen/prepare', {
        ticker: byId('screen-ticker').value, cik: selected.cik, expected_index_id: index
      });
      byId('screen-evidence').textContent = JSON.stringify({blockers:result.valuation_blockers, source:result.financials.source}, null, 2);
      byId('valuation-request').value = JSON.stringify(result.request_template, null, 2);
      status('Financial history loaded. Fill the explicit assumptions before calculating.');
    } catch (error) { status(error.message); }
  });
  byId('value-button').addEventListener('click', async () => {
    try {
      const body = JSON.parse(byId('valuation-request').value);
      if (body.cik !== selected.cik) throw new Error('Selected issuer and valuation request differ');
      const result = await api('/api/calculate/enterprise', body);
      byId('valuation-result').textContent = JSON.stringify(result, null, 2);
      status('Enterprise scenario calculated. Equity and per-share values remain unavailable.');
    } catch (error) { status(error.message); }
  });
})();
