"use strict";
(function (window, document) {
  if (!document.getElementById("data-workspace")) return;
  const el = (id) => document.getElementById(id);
  const pending = new Set(), channels = new Map();
  let ownerKey = "", generation = 0;
  let grantPending = null, revocation = Promise.resolve();
  let stocks = {}, prices = {}, collections = {}, files = {};
  const privateRegions = ["data-stock-summary", "data-stock-catalog", "data-prices-summary", "data-prices", "data-price-evidence", "data-collections-summary", "data-collection-list", "data-collection-detail", "data-families", "data-files-summary", "data-file-list", "data-native-summary", "data-native-schema", "data-native-rows", "data-file-detail"];
  const paging = ["data-stock-next", "data-prices-next", "data-collections-next", "data-files-next"];
  const text = (value) => value === null || value === undefined ? "—" : typeof value === "object" ? JSON.stringify(value) : String(value);
  function node(tag, value) { const n = document.createElement(tag); if (value !== undefined) n.textContent = text(value); return n; }
  function action(label, callback) { const b = node("button", label); b.type = "button"; b.className = "secondary"; b.addEventListener("click", callback); return b; }
  function table(target, headings, rows) {
    const t = node("table"); t.className = "value-table";
    const head = node("thead"), tr = node("tr");
    headings.forEach((h) => { const th = node("th", h); th.scope = "col"; tr.append(th); }); head.append(tr); t.append(head);
    const body = node("tbody");
    rows.forEach((row) => { const r = node("tr"); row.forEach((v) => { const c = node("td"); c.append(v && typeof v === "object" && typeof v.addEventListener === "function" ? v : node("span", v)); r.append(c); }); body.append(r); });
    t.append(body); el(target).replaceChildren(t);
    if (!rows.length) el(target).append(node("p", "No stored results for this query."));
  }
  async function deleteGrant() {
    try {
      const response = await window.fetch("/api/account/data-access", {
        method: "DELETE", credentials: "same-origin", cache: "no-store", redirect: "error",
        referrerPolicy: "no-referrer", keepalive: true,
      });
      return response.ok;
    } catch (_) { return false; }
  }
  function revokeGrant(unloading) {
    // On unload send immediately; after an in-flight mint settles send again so
    // a late POST response cannot silently restore the cookie during disconnect.
    if (unloading) void deleteGrant();
    const activeGrant = grantPending;
    revocation = revocation.catch(() => false).then(async () => {
      if (activeGrant) await activeGrant.catch(() => {});
      return deleteGrant();
    });
    return revocation;
  }
  function clear(unloading = false) {
    ownerKey = ""; generation += 1;
    if (el("financial-answer")) el("financial-answer").textContent = "";
    for (const controller of pending) controller.abort(); pending.clear(); channels.clear();
    stocks = {}; prices = {}; collections = {}; files = {};
    el("data-owner-key").value = ""; el("data-controls").disabled = true;
    privateRegions.forEach((id) => el(id).replaceChildren());
    ["data-stock-search", "data-symbol", "data-permno", "data-date-from", "data-date-to", "data-collection-search", "data-family", "data-prefix"].forEach((id) => { el(id).value = ""; });
    paging.forEach((id) => { el(id).disabled = true; });
    el("data-status").textContent = "Disconnected. Private key and loaded data cleared.";
    el("data-benchmark-grant").disabled = true;
    el("data-grant-status").textContent = "Clearing this browser's private benchmark grant…";
    const epoch = generation;
    return revokeGrant(unloading).then((confirmed) => {
      if (generation === epoch) el("data-grant-status").textContent = confirmed
        ? "Private benchmark grant cleared."
        : "Could not confirm grant removal. An existing grant expires within 15 minutes; reconnect and disconnect to retry.";
    });
  }
  function grantBenchmarks() {
    if (!ownerKey || grantPending) return;
    const epoch = generation;
    el("data-benchmark-grant").disabled = true;
    el("data-grant-status").textContent = "Requesting private benchmark access…";
    grantPending = (async () => {
      try {
        const response = await window.fetch("/api/account/data-access", {
          method: "POST", headers: {Authorization: "Bearer " + ownerKey},
          credentials: "same-origin", cache: "no-store", redirect: "error",
          referrerPolicy: "no-referrer", keepalive: true,
        });
        if (epoch !== generation || !ownerKey) return;
        if (response.status === 401) {
          el("data-grant-status").textContent = "Log in to your app account in another tab, then retry with an authorized owner key.";
        } else if (response.ok) {
          el("data-grant-status").textContent = "Private benchmarks enabled for this account for 15 minutes. Keep this tab open; disconnecting or leaving clears the browser grant.";
        } else {
          el("data-grant-status").textContent = "Private benchmark grant unavailable (HTTP " + response.status + "). No grant was confirmed.";
        }
      } catch (_) {
        if (epoch === generation) el("data-grant-status").textContent = "Private benchmark grant unavailable. Retry when connected.";
      } finally {
        if (epoch === generation && ownerKey) el("data-benchmark-grant").disabled = false;
      }
    })().finally(() => { grantPending = null; });
    return grantPending;
  }
  function invalidate(...names) { names.forEach((name) => channels.set(name, (channels.get(name) || 0) + 1)); }
  async function read(channel, route, params, render, headers = {}) {
    if (!ownerKey) return;
    const ticket = (channels.get(channel) || 0) + 1; channels.set(channel, ticket);
    const epoch = generation, controller = new AbortController(); pending.add(controller);
    const current = () => epoch === generation && ownerKey && channels.get(channel) === ticket;
    try {
      const response = await window.fetch("/api/data/" + route + "?" + new URLSearchParams(params), {
        method: "GET", headers: {Authorization: "Bearer " + ownerKey, ...headers}, credentials: "omit",
        cache: "no-store", redirect: "error", referrerPolicy: "no-referrer", signal: controller.signal,
      });
      if (!current()) return;
      if (!response.ok) {
        if (response.status === 401) { clear(); el("data-status").textContent = "Owner data key rejected. Reconnect with an authorized key."; return; }
        el("data-status").textContent = "Source request could not be completed (HTTP " + response.status + "). Review the query or retry."; return;
      }
      const data = await response.json();
      if (current()) { render(data); el("data-status").textContent = "Connected in this tab. Disconnect to clear private data."; }
    } catch (_) {
      if (current()) el("data-status").textContent = "Request unavailable. No data was inferred; retry the source query.";
    } finally { pending.delete(controller); }
  }
  const archiveSources = new Set(["yfinance", "simfin", "tiingo", "eodhd", "marketstack", "polygon", "twelve_data", "estate_alpaca"]);
  function stockCatalog(next = false) {
    if (!next) stocks = {query: {source: el("data-stock-source").value || "crsp", search: el("data-stock-search").value.trim(), limit: 100}};
    const q = {...stocks.query};
    if (next && stocks.cursor) { q.cursor = stocks.cursor; q.expected_release_id = stocks.release; }
    el("data-stock-next").disabled = true; el("data-stock-catalog").replaceChildren();
    return read("stocks", "stock-history", q, (data) => {
      stocks.cursor = data.next_cursor; stocks.release = data.release_id;
      el("data-stock-summary").textContent = text(data.security_count ?? data.symbol_count) + " indexed securities · " + text(data.total_matches) + " match · source coverage shown per symbol.";
      table("data-stock-catalog", ["Security ID", "Latest ticker", "Company", "First stored session", "Last stored session", "Stored rows", "Open"], (data.symbols || []).map((s) => [s.permno ? "PERMNO " + s.permno : archiveSources.has(stocks.query.source) ? s.security_id : s.symbol, s.symbol, s.name, s.date_min, s.date_max, s.normalized_rows, action("Read history", () => { const nativeId = s.permno || (archiveSources.has(stocks.query.source) ? s.security_id : ""); el("data-symbol").value = nativeId ? "" : s.symbol; el("data-permno").value = nativeId ? String(nativeId) : ""; el("data-date-from").value = s.date_min || ""; el("data-date-to").value = s.date_max || ""; return stockPrices(); })]));
      el("data-stock-next").disabled = !stocks.cursor;
    });
  }
  function stockPrices(next = false) {
    if (!next) {
      const source = el("data-stock-source").value || "crsp";
      const q = {source: source, limit: 500};
      const permno = el("data-permno").value.trim(), symbol = el("data-symbol").value.trim().toUpperCase();
      if ((source === "crsp" || archiveSources.has(source)) && permno) {
        if (!(source === "crsp" ? /^[1-9][0-9]{0,9}$/ : /^[0-9]{1,20}$/).test(permno)) { el("data-status").textContent = "Enter a valid source security ID."; return; }
        if (source === "crsp") q.permno = permno; else q.security_id = permno;
      } else {
        if (!/^[A-Z0-9][A-Z0-9.\-]{0,24}$/.test(symbol)) { el("data-status").textContent = "Select a security or enter a ticker."; return; }
        q.symbol = symbol;
      }
      if (el("data-date-from").value) q.date_from = el("data-date-from").value;
      if (el("data-date-to").value) q.date_to = el("data-date-to").value;
      prices = {query:q};
    }
    const q = {...prices.query};
    if (next && prices.cursor) { q.cursor = prices.cursor; q.expected_release_id = prices.release; }
    el("data-prices-next").disabled = true; el("data-prices").replaceChildren(); el("data-price-evidence").replaceChildren();
    return read("prices", "stock-history", q, (data) => {
      prices.cursor = data.next_cursor; prices.release = data.release_id;
      const rows = data.prices || [];
      el("data-prices-summary").textContent = text(data.security_id || data.symbol) + " · " + rows.length + " rows on this page · " + text(data.source) + " · " + text(data.coverage?.price_basis) + ". Missing source fields remain blank.";
      table("data-prices", ["Session", "Source ticker", "Currency", "Open", "High", "Low", "Native close", "Adjusted close (stored)", "Price magnitude", "Total return", "Volume", "Native flags"], rows.map((r) => [r.session_date, r.symbol, r.currency, r.open, r.high, r.low, r.close, r.adjusted_close, r.price_magnitude, r.total_return, r.volume, r.native_flags]));
      el("data-price-evidence").textContent = JSON.stringify({coverage:data.coverage, identity_intervals:data.identity_intervals, gaps:data.gaps || [], source_pages:data.source_pages, source_lineage:data.source_lineage}, null, 2);
      el("data-prices-next").disabled = !prices.cursor;
    });
  }
  function collectionCatalog(next = false) {
    invalidate("collection-detail");
    if (!next) collections = {query: {search: el("data-collection-search").value.trim(), limit: 50, offset: 0}};
    if (!next && el("data-family").value.trim()) collections.query.family = el("data-family").value.trim();
    const q = {...collections.query}; if (next) q.offset = collections.next;
    el("data-collections-next").disabled = true; el("data-collection-list").replaceChildren(); el("data-collection-detail").replaceChildren();
    return read("collections", "datasets/catalog", q, (data) => {
      collections.next = data.next_offset;
      el("data-collections-summary").textContent = text(data.matching_releases) + " matching releases · catalog " + text(data.release_id) + ".";
      const entries = data.entries || [];
      el("data-families").replaceChildren(...[...new Set(entries.map((e) => e.family).filter(Boolean))].map((f) => { const option = node("option"); option.value = f; return option; }));
      table("data-collection-list", ["Dataset", "Family", "Details"], entries.map((e) => [e.dataset, e.family, action("Inspect release", () => {
        if (!/^[a-f0-9]{32}$/.test(e.id)) return;
        return read("collection-detail", "datasets/catalog/" + e.id, {}, (detail) => { el("data-collection-detail").textContent = JSON.stringify(detail, null, 2); });
      })]));
      el("data-collections-next").disabled = data.next_offset === null || data.next_offset === undefined;
    });
  }
  function fileCatalog(next = false) {
    invalidate("native", "native-rows");
    if (!next) files = {store: el("data-store").value, query: {prefix: el("data-prefix").value.trim(), limit: 50}};
    if (!["financial", "research", "filings", "lakehouse"].includes(files.store)) return;
    const q = {...files.query}; if (next && files.cursor) q.cursor = files.cursor;
    el("data-files-next").disabled = true; el("data-file-list").replaceChildren();
    ["data-native-summary", "data-native-schema", "data-native-rows", "data-file-detail"].forEach((id) => el(id).replaceChildren());
    const store = files.store;
    return read("files", "datasets/" + store + "/objects", q, (data) => {
      files.cursor = data.cursor;
      el("data-files-summary").textContent = store + " / " + (q.prefix || "(root)") + " · " + (data.objects || []).length + " files on this page.";
      const folders = (data.prefixes || []).map((prefix) => [action("Folder: " + prefix, () => { el("data-prefix").value = prefix; return fileCatalog(); }), "Folder", "", ""]);
      const objects = (data.objects || []).map((o) => [o.path, o.bytes, o.stored_at, action(/\.parquet$/i.test(o.path) ? "Schema & 10 rows" : "Metadata", () => inspectFile(store, o))]);
      table("data-file-list", ["Path", "Bytes / kind", "Stored at", "Inspect"], folders.concat(objects));
      el("data-files-next").disabled = !files.cursor;
    });
  }
  function inspectFile(store, object) {
    invalidate("native", "native-rows");
    el("data-file-detail").textContent = JSON.stringify(object, null, 2);
    ["data-native-summary", "data-native-schema", "data-native-rows"].forEach((id) => el(id).replaceChildren());
    if (!/\.parquet$/i.test(object.path)) { el("data-native-summary").textContent = "Metadata only. Raw downloads are not offered here."; return; }
    if (typeof object.etag !== "string" || !/^[A-Za-z0-9._-]+$/.test(object.etag)) { el("data-native-summary").textContent = "An exact source ETag is required. Refresh the folder listing."; return; }
    const headers = {"If-Match": '"' + object.etag + '"'};
    return read("native", "datasets/" + store + "/schema", {path:object.path}, (data) => {
      const schema = data.data || {};
      el("data-native-summary").textContent = text(schema.row_count) + " footer-declared rows · native source fields · source quality unvalidated.";
      table("data-native-schema", ["Field", "Native schema"], (schema.columns || []).map((c) => [c.name, c]));
      return read("native-rows", "datasets/" + store + "/rows", {path:object.path, limit:10}, (preview) => {
        const fields = (preview.data?.columns || []).map((c) => c.name);
        table("data-native-rows", fields, (preview.data?.rows || []).map((r) => fields.map((name) => r[name])));
      }, headers);
    }, headers);
  }
  const onSubmit = (id, callback) => el(id).addEventListener("submit", (event) => { event.preventDefault(); return callback(); });
  if (el("financial-query")) onSubmit("financial-query", async () => {
    const epoch = generation, controller = new AbortController(); pending.add(controller);
    const button = el("financial-query").querySelector("button"); button.disabled = true;
    el("financial-answer").textContent = "Loading…";
    try {
      const response = await window.fetch("/api/data/query?" + new URLSearchParams({query:el("question").value}), {
        headers:ownerKey ? {Authorization:"Bearer " + ownerKey} : {}, cache:"no-store",
        redirect:"error", referrerPolicy:"no-referrer", signal:controller.signal,
      });
      const result = await response.json(); if (epoch !== generation) return;
      el("financial-answer").textContent = response.ok ? result.answer : response.status === 403
        ? "Connect this tab below with your owner data key to request private prices."
        : result.error || "This question could not be answered.";
    } catch (_) { if (epoch === generation) el("financial-answer").textContent = "Request unavailable. Please try again."; }
    finally { pending.delete(controller); button.disabled = false; }
  });
  onSubmit("data-connect-form", async () => {
    const supplied = el("data-owner-key").value.trim();
    const clearing = clear(), epoch = generation;
    await clearing;
    if (generation !== epoch) return;
    if (!/^[A-Za-z0-9._~+/-]+=*$/.test(supplied) || supplied.length > 4096) { el("data-status").textContent = "Enter an owner data key without spaces."; return; }
    ownerKey = supplied; el("data-benchmark-grant").disabled = false; el("data-controls").disabled = false; el("data-status").textContent = "Connecting this tab…";
    return stockCatalog();
  });
  onSubmit("data-stocks-form", () => stockCatalog()); onSubmit("data-prices-form", () => stockPrices());
  onSubmit("data-collections-form", () => collectionCatalog()); onSubmit("data-files-form", () => fileCatalog());
  el("data-disconnect").addEventListener("click", () => clear());
  el("data-benchmark-grant").addEventListener("click", grantBenchmarks);
  el("data-stock-source").addEventListener("change", () => {
    invalidate("prices"); prices = {}; el("data-permno").value = ""; el("data-symbol").value = ""; el("data-date-from").value = ""; el("data-date-to").value = "";
    el("data-prices").replaceChildren(); el("data-price-evidence").replaceChildren(); el("data-prices-next").disabled = true;
    return stockCatalog();
  });
  el("data-stock-next").addEventListener("click", () => stockCatalog(true));
  el("data-prices-next").addEventListener("click", () => stockPrices(true));
  el("data-collections-next").addEventListener("click", () => collectionCatalog(true));
  el("data-browse-wrds").addEventListener("click", () => { el("data-store").value = "research"; el("data-prefix").value = "raw/wrds/"; return fileCatalog(); });
  el("data-files-next").addEventListener("click", () => fileCatalog(true));
  el("data-files-up").addEventListener("click", () => { const parts = el("data-prefix").value.replace(/\/$/, "").split("/"); parts.pop(); el("data-prefix").value = parts.length ? parts.join("/") + "/" : ""; return fileCatalog(); });
  window.addEventListener("pagehide", () => clear(true));
  window.addEventListener("pageshow", (event) => { if (event.persisted) clear(); });
})(window, document);
