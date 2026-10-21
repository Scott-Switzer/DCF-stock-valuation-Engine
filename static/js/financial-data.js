document.getElementById('financial-query')?.addEventListener('submit', async event => {
  event.preventDefault();
  const output = document.getElementById('financial-answer');
  const button = event.currentTarget.querySelector('button');
  button.disabled = true; output.textContent = 'Loading…';
  try {
    const query = document.getElementById('question').value;
    const key = document.getElementById('data-key').value;
    const response = await fetch('/api/data/query?' + new URLSearchParams({query}), {headers: key ? {Authorization: 'Bearer ' + key} : {}});
    if (response.status === 403) document.getElementById('data-key-label').hidden = false;
    const result = await response.json();
    output.textContent = response.ok ? result.answer : result.error || 'Could not retrieve this data.';
  } catch { output.textContent = 'Could not reach financial data. Please try again.'; }
  finally { button.disabled = false; }
});
