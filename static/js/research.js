"use strict";
(() => {
  document.getElementById("research-print")?.addEventListener("click", () => window.print());
  const form = document.getElementById("research-form");
  if (!form) return;
  const message = document.getElementById("research-status");
  const save = document.getElementById("research-save");
  const list = document.getElementById("research-list");
  let context = null, activeContext = null, parentId = null, draftTicker = null, pending = false, frozen = false;
  const field = name => form.elements.namedItem(name);
  const note = text => { message.textContent = text; };
  const request = async (url, options) => {
    const response = await fetch(url, options);
    const value = await response.json();
    if (!response.ok) throw Error(value.error || "Research request failed.");
    return value;
  };
  function updateSave() {
    for (const el of form.querySelectorAll("input,textarea,button")) el.disabled = pending;
    const ticker = context?.result?.input_financials?.company?.ticker;
    save.disabled = pending || !context?.valid || (!!draftTicker && ticker !== draftTicker);
    const result = context?.result;
    document.getElementById("research-snapshot").textContent = result
      ? `${frozen ? "Frozen research snapshot" : "Active valuation"}: ${ticker} · ${result.method.toUpperCase()} · ${result.input_financials.valuation_date} · 12-month scenario $${result.target_price_12m.toFixed(2)}`
      : "Load a company and complete a valuation before saving research.";
    if (draftTicker && ticker && ticker !== draftTicker)
      note(`This draft belongs to ${draftTicker}. Return to that company or start a new draft.`);
  }
  window.researchWorkspace = {
    setContext(item) {
      activeContext = item;
      if (!frozen) context = item;
      updateSave();
    },
  };
  form.addEventListener("input", () => {
    draftTicker = draftTicker || context?.result?.input_financials?.company?.ticker || null;
    updateSave();
  });
  document.getElementById("research-new").addEventListener("click", () => {
    if (pending) return;
    form.reset(); parentId = null; draftTicker = null; frozen = false; context = activeContext;
    note("New draft. Earlier saved revisions remain in your library."); updateSave();
  });
  document.getElementById("research-active").addEventListener("click", () => {
    if (pending) return;
    frozen = false; context = activeContext; parentId = null;
    note("Using the active valuation. Existing saved snapshots remain unchanged."); updateSave();
  });
  async function refresh(ticker) {
    const rows = await request("/api/research" + (ticker ? `?ticker=${encodeURIComponent(ticker)}` : ""));
    list.replaceChildren();
    for (const row of rows) {
      const li = document.createElement("li"), link = document.createElement("a");
      link.href = `/research/${encodeURIComponent(row.id)}`;
      link.textContent = `${row.ticker} · ${row.scenario_name} · ${row.title} · ${row.created_at.slice(0, 10)}`;
      li.append(link); list.append(li);
    }
  }
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (save.disabled || !context?.valid) return;
    const result = context.result;
    const thesis = {};
    for (const el of form.querySelectorAll("textarea[name]")) thesis[el.name] = el.value;
    pending = true; updateSave(); note("Saving a dated research snapshot…");
    try {
      const record = await request("/api/research", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({title:field("title").value, scenario_name:field("scenario_name").value,
          method:result.method, financials:result.input_financials, assumptions:result.assumptions,
          thesis, parent_id:parentId})});
      parentId = record.id; draftTicker = record.ticker;
      frozen = true; context = {valid:true, result};
      note(`Saved ${record.ticker} ${record.scenario_name}. Earlier revisions are preserved. Further note edits use this frozen valuation; choose Use active valuation for changed assumptions.`);
      await refresh(record.ticker);
    } catch (error) { note(error.message); }
    finally { pending = false; updateSave(); }
  });
  const previous = new URLSearchParams(location.search).get("research");
  if (previous) request(`/api/research/${encodeURIComponent(previous)}`).then(record => {
    parentId = record.id; draftTicker = record.ticker;
    field("title").value = record.title; field("scenario_name").value = record.scenario_name;
    for (const [key, value] of Object.entries(record.snapshot.thesis)) if (field(key)) field(key).value = value;
    // Editing notes starts from the frozen result, not a silently refreshed company.
    const result = {...record.snapshot.result, input_financials:record.snapshot.financials,
      assumptions:record.snapshot.assumptions};
    frozen = true; context = {valid:true, result}; updateSave();
    note(`Editing ${record.ticker} notes against the saved ${record.snapshot.financials.valuation_date} snapshot. Load a company only if you intend to use new valuation inputs.`);
    document.getElementById("research-panel").open = true;
  }).catch(error => note(error.message));
  refresh().catch(() => note("Research library is unavailable right now."));
})();
