"use strict";
(() => {
  if (!document.getElementById("company-loader")) return;
  const $ = (id) => document.getElementById(id),
    editors = new Map(),
    results = new Map(),
    ready = new Set();
  let method = "dcf",
    baseline = null,
    generation = 0,
    loading = false,
    analysts = null,
    guidanceRequested = false;
  const money = (value) =>
    Number.isFinite(value)
      ? value.toLocaleString(undefined, {
          style: "currency",
          currency: "USD",
          maximumFractionDigits: 2,
        })
      : "—";
  const pct = (value) =>
    Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "—";
  const date = (value) =>
    value
      ? new Date(value + "T12:00:00").toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      : "—";
  function status(text, error = false) {
    $("workspace-status").textContent = text;
    $("workspace-status").className = error ? "notice error" : "notice";
  }
  async function request(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) throw Error(data.error || "Unable to complete request.");
    return data;
  }
  function createEditor(key) {
    if (editors.has(key)) return editors.get(key);
    const frame = document.createElement("iframe");
    frame.title = `${key.toUpperCase()} assumptions`;
    frame.src = (key === "dcf" ? "/" : `/${key}`) + "?embedded=1";
    frame.dataset.method = key;
    frame.hidden = key !== method;
    editors.set(key, frame);
    $("workspace-editors").append(frame);
    return frame;
  }
  function send(key, data) {
    editors
      .get(key)
      ?.contentWindow.postMessage(
        { type: "workspace-data", data, generation },
        location.origin,
      );
  }
  async function assemble(key, token) {
    if (!baseline || (results.has(key) && results.get(key).loaded)) return;
    if (key === "relative" && results.get("dcf")?.pending) return;
    const item = results.get(key) || {};
    if (item.assembling) return;
    item.assembling = true;
    results.set(key, item);
    try {
      const data =
        key === "dcf"
          ? baseline
          : await request(`/api/assemble/${key}`, {
              financials: results.get("dcf")?.valid
                ? results.get("dcf").result.input_financials
                : baseline.financials,
              ...(results.get("dcf")?.valid
                ? { assumptions: results.get("dcf").result.assumptions }
                : {}),
            });
      if (token !== generation) return;
      item.loaded = true;
      item.data = data;
      item.assembling = false;
      results.set(key, item);
      if (ready.has(key)) send(key, data);
      if (key === method)
        status(
          `Loaded ${data.financials.company.name}. Edit assumptions; results update automatically.`,
        );
    } catch (e) {
      if (token !== generation) return;
      item.assembling = false;
      item.error = e.message;
      if (key === method) {
        status(e.message, true);
        $("preview-status").textContent = e.message;
      }
    }
  }
  function showMethod(key) {
    method = key;
    for (const button of document.querySelectorAll(".workspace-tabs button"))
      button.setAttribute(
        "aria-selected",
        String(button.dataset.method === key),
      );
    for (const [k, frame] of editors) frame.hidden = k !== key;
    createEditor(key);
    const item = results.get(key);
    render(item);
    if ($("template-box")?.open) loadTemplates();
    if (baseline) assemble(key, generation);
  }
  for (const button of document.querySelectorAll(".workspace-tabs button"))
    button.addEventListener("click", () => showMethod(button.dataset.method));
  $("company-loader").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (loading) return;
    loading = true;
    const token = generation;
    $("workspace-load").disabled = true;
    status("Loading statements and market data…");
    try {
      const data = await request("/api/load/dcf", {
        ticker: $("workspace-ticker").value.trim().toUpperCase(),
      });
      if (token !== generation) return;
      generation++;
      baseline = data;
      analysts = null;
      results.clear();
      $("live-result").hidden = true;
      $("save-valuation").disabled = true;
      $("management-guidance").hidden = true;
      for (const frame of editors.values())
        frame.contentWindow.postMessage(
          { type: "workspace-reset", generation },
          location.origin,
        );
      $("workspace-company").textContent =
        `${data.financials.company.ticker} · ${data.financials.company.name}`;
      $("workspace-market").textContent =
        `${money(data.financials.market.price)} · ${date(data.financials.market.price_as_of)}`;
      $("workspace-source").textContent =
        data.financials.source.ppe_release ? "PPE / SEC + labeled fallbacks · sourced inputs locked" : `Yahoo${data.financials.source.classification ? " + SEC" : ""} · sourced inputs locked`;
      $("company-strip").hidden = false;
      await assemble(method, generation);
      loadReferences(data.financials.company.ticker, generation);
      guidanceRequested = false;
      $("guidance-content").textContent =
        "Open to retrieve dated SEC filings and available revenue outlook excerpts.";
      $("management-guidance").hidden = false;
      $("management-guidance").querySelector("details").open = false;
    } catch (e) {
      if (token === generation) status(e.message, true);
    } finally {
      loading = false;
      $("workspace-load").disabled = false;
    }
  });
  async function loadReferences(ticker, token) {
    try {
      const r = await fetch(`/api/references/${encodeURIComponent(ticker)}`);
      if (!r.ok) return;
      const data = await r.json();
      if (token !== generation) return;
      analysts = data;
      for (const frame of editors.values())
        frame.contentWindow.postMessage(
          { type: "workspace-references", data, generation },
          location.origin,
        );
      render(results.get(method));
    } catch (_) {
      /* Optional references never block valuation. */
    }
  }
  async function loadGuidance(ticker, token) {
    try {
      const r = await fetch(`/api/guidance/${encodeURIComponent(ticker)}`);
      if (!r.ok) throw Error("Guidance unavailable");
      const data = await r.json();
      if (token !== generation) return;
      const box = $("guidance-content");
      box.replaceChildren();
      const note = document.createElement("p");
      note.textContent = data.note;
      box.append(note);
      for (const item of data.filings || []) {
        const row = document.createElement("div");
        row.className = "guidance-item";
        const link = document.createElement("a");
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = `${item.form} · filed ${date(item.filed)}${item.report_date ? " · period " + date(item.report_date) : ""}`;
        row.append(link);
        if (item.excerpt) {
          const p = document.createElement("p");
          p.textContent = item.excerpt;
          row.append(p);
        }
        box.append(row);
      }
      $("management-guidance").hidden = false;
    } catch (_) {
      if (token === generation) {
        $("guidance-content").textContent =
          "SEC guidance research is unavailable right now. Valuation inputs remain available.";
        $("management-guidance").hidden = false;
      }
    }
  }
  window.addEventListener("message", (event) => {
    if (event.origin !== location.origin) return;
    const pair = [...editors].find(
      ([, frame]) => frame.contentWindow === event.source,
    );
    if (!pair) return;
    const [key, frame] = pair;
    const message = event.data || {};
    if (message.type === "editor-ready") {
      ready.add(key);
      const item = results.get(key);
      if (item?.data) send(key, item.data);
      if (analysts)
        frame.contentWindow.postMessage(
          { type: "workspace-references", data: analysts, generation },
          location.origin,
        );
      return;
    }
    if (message.type === "editor-height") {
      frame.style.height = `${Math.min(20000, Math.max(300, message.height))}px`;
      return;
    }
    if (message.generation !== generation) return;
    if (message.type === "editor-company") {
      if (key !== "dcf") {
        status(
          "This method’s imported company inputs are active. Load a ticker above for a shared company workspace.",
        );
      } else {
        generation++;
        baseline = { financials: message.financials, form: message.form };
        analysts = null;
        guidanceRequested = false;
        $("guidance-content").replaceChildren();
        $("management-guidance").querySelector("details").open = false;
        $("management-guidance").hidden =
          message.financials.source.kind === "synthetic";
        if (!$("management-guidance").hidden)
          $("guidance-content").textContent =
            "Open to retrieve this issuer’s SEC filings.";
        results.clear();
        $("live-result").hidden = true;
        $("save-valuation").disabled = true;
        $("export-xlsx").disabled = true;
        $("compare-scenario").disabled = true;
        $("export-json").disabled = true;
        $("export-csv").disabled = true;
        $("preview-status").textContent = "Updating company inputs…";
        results.set("dcf", { loaded: true, data: baseline });
        for (const [k, other] of editors) {
          if (k !== "dcf")
            other.contentWindow.postMessage(
              { type: "workspace-reset", generation },
              location.origin,
            );
        }
        $("workspace-company").textContent =
          `${message.financials.company.ticker} · ${message.financials.company.name}`;
        $("workspace-market").textContent =
          `${money(message.financials.market.price)} · ${date(message.financials.market.price_as_of)}`;
        $("workspace-source").textContent = message.financials.source.name;
        $("company-strip").hidden = false;
        send("dcf", baseline);
        if (message.financials.source.kind !== "synthetic")
          loadReferences(message.financials.company.ticker, generation);
      }
      return;
    }
    const item = results.get(key) || {};
    if (message.type === "preview-pending") {
      item.valid = false;
      item.pending = true;
      item.error = null;
    }
    if (message.type === "preview-error") {
      item.valid = false;
      item.pending = false;
      item.error = message.error;
    }
    if (message.type === "preview-result") {
      item.result = message.result;
      item.form = message.form;
      item.valid = true;
      item.pending = false;
      item.error = null;
      item.saved = false;
    }
    results.set(key, item);
    if (key === method) render(item);
    if (
      key === "dcf" &&
      method === "relative" &&
      ["preview-result", "preview-error"].includes(message.type)
    )
      assemble("relative", generation);
  });
  function render(item) {
    $("save-valuation").disabled = !item?.valid || !!item?.saving;
    $("export-xlsx").disabled = !item?.valid;
    $("export-json").disabled = !item?.valid;
    $("export-csv").disabled = !item?.valid;
    $("compare-scenario").disabled = !item?.valid;
    $("save-status").textContent = item?.saved ? "Valuation saved." : "";
    if (!item?.result) {
      $("live-result").hidden = true;
      $("preview-status").textContent =
        item?.error ||
        (baseline
          ? "Preparing this method…"
          : "Load a company to see your valuation.");
      return;
    }
    $("live-result").hidden = false;
    $("preview-status").textContent = item.error
      ? `Fix inputs: ${item.error}. Showing the last valid result.`
      : item.pending
        ? "Updating… showing the last valid result."
        : "Updated · unsaved";
    const r = item.result;
    $("live-price").textContent = money(r.target_price_12m);
    $("live-upside").textContent =
      `12-month model target · ${pct(r.upside_12m)} vs market`;
    insights(r);
    priceBars(r);
    chart(r);
    bridge(r);
    sensitivity(r);
    compsAnalysis(r);
    $("live-notes").replaceChildren();
    for (const text of r.warnings || []) {
      const li = document.createElement("li");
      li.textContent = text;
      $("live-notes").append(li);
    }
    $("live-details").textContent = JSON.stringify(r, null, 2);
  }
  function insights(r) {
    const box = $("valuation-insights");
    box.replaceChildren();
    const cards = [];
    if (Number.isFinite(analysts?.target?.mean) && analysts.target.mean > 0)
      cards.push(["Versus analyst target", pct(r.target_price_12m / analysts.target.mean - 1), "Your 12-month target relative to consensus."]);
    const terminalShare = r.method === "dcf" ? r.terminal_value_share : r.method === "ddm" && r.equity_value > 0 ? r.pv_terminal / r.equity_value : null;
    if (Number.isFinite(terminalShare))
      cards.push(["Terminal dependence", pct(terminalShare), terminalShare > 0.8 ? "Most value lies beyond year five. Review long-run growth." : "Share of present value beyond year five."]);
    if (r.method === "relative") {
      const selected = (r.multiples || []).filter(x => x.included && Number.isFinite(x.implied_price));
      if (selected.length) {
        cards.push(["Selected-method range", `${money(Math.min(...selected.map(x => x.implied_price)))}–${money(Math.max(...selected.map(x => x.implied_price)))}`, `${selected.length} equally weighted methods; not a confidence interval.`]);
        cards.push(["Peer coverage", `${Math.min(...selected.map(x => x.count))}–${Math.max(...selected.map(x => x.count))}`, "Valid peers per selected multiple. Review missing or weak fits."]);
      }
    } else {
      const a = r.assumptions || {};
      const rate = r.method === "dcf" ? r.wacc : a.required_return;
      if (Number.isFinite(rate) && Number.isFinite(a.terminal_growth_rate))
        cards.push(["Discount / growth spread", `${((rate - a.terminal_growth_rate) * 100).toFixed(2)} pp`, "A narrow spread makes terminal value more sensitive."]);
    }
    for (const [label, value, note] of cards) {
      const card = document.createElement("div"); card.className = "insight-card";
      const title = document.createElement("span"); title.textContent = label;
      const metric = document.createElement("strong"); metric.textContent = value;
      const caption = document.createElement("small"); caption.textContent = note;
      card.append(title, metric, caption); box.append(card);
    }
  }
  function compsAnalysis(r) {
    const box = $("comps-analysis");
    if (!box) return;
    box.replaceChildren();
    box.hidden = r.method !== "relative";
    if (box.hidden) return;
    const add = (parent, tag, text) => {
      const el = document.createElement(tag); el.textContent = text;
      parent.append(el); return el;
    };
    add(box, "h3", "Explain your comps");
    add(box, "p", r.basis_convention || "Peer denominator basis not recorded in this snapshot.");
    for (const row of (r.multiples || []).filter(x => x.included)) {
      const details = add(box, "details", "");
      const multiple = x => Number.isFinite(x) ? `${x.toFixed(2)}×` : "—";
      add(details, "summary", `${row.label}: mean ${multiple(row.mean)} · median ${multiple(row.median)}`);
      add(details, "p", `Mean-implied ${money(row.implied_price)} · median-implied ${money(row.median_implied_price)}. ${row.outlier_count || 0} flagged outliers; kept in the calculation. Peer contributions below use raw common equity; the aggregate share value is floored at zero.`);
      const wrap = add(details, "div", ""); wrap.className = "table-wrap";
      const table = add(wrap, "table", ""); table.className = "value-table";
      const head = add(add(table, "thead", ""), "tr", "");
      for (const title of ["Peer", "Multiple", "Weight", "Raw implied / contribution", "Basis / period", "Coverage"])
        add(head, "th", title);
      const body = add(table, "tbody", "");
      for (const peer of row.distribution || []) {
        const tr = add(body, "tr", "");
        add(tr, "th", peer.ticker);
        for (const value of [multiple(peer.multiple), pct(peer.weight), `${money(peer.raw_implied_price)} / ${money(peer.raw_price_contribution)}`,
          `${peer.basis} · ${peer.period_end || "period not recorded"}`,
          peer.exclusion_reason || (peer.outlier ? "Outlier · included" : "Included")])
          add(tr, "td", value);
        add(details, "p", `${peer.ticker}: ${peer.source || "source not recorded"} · price ${peer.price_as_of || "date not recorded"}`);
      }
      add(details, "p", row.outlier_rule || "No outlier rule recorded.");
    }
  }
  function priceBars(r) {
    const values = [
      ["Market", r.current_price, "market"],
      ["Your 12m target", r.target_price_12m, "model"],
      ["Analyst 12m", analysts?.target?.mean, "analyst"],
    ];
    if (Number.isFinite(r.intrinsic_value))
      values.splice(1, 0, ["Value today", r.intrinsic_value, "model"]);
    const max = Math.max(
      ...values.map(([, v]) => (Number.isFinite(v) ? v : 0)),
      1,
    );
    const box = $("price-bars");
    box.replaceChildren();
    for (const [label, value, kind] of values) {
      const row = document.createElement("div");
      row.className = `price-bar-row ${kind}`;
      const text = document.createElement("span");
      text.textContent = label;
      const track = document.createElement("div");
      track.className = "price-track";
      const fill = document.createElement("div");
      fill.className = "price-fill";
      fill.style.width = `${Number.isFinite(value) ? (Math.max(0, value) / max) * 100 : 0}%`;
      track.append(fill);
      const val = document.createElement("strong");
      val.textContent = money(value);
      row.append(text, track, val);
      box.append(row);
    }
    const note = document.createElement("p");
    note.className = "chart-caption";
    note.textContent = analysts?.target?.mean
      ? `Analyst range ${money(analysts.target.low)}–${money(analysts.target.high)} · ${analysts.target.analysts ?? "unknown"} analysts · Yahoo consensus`
      : "Analyst consensus unavailable for this snapshot.";
    box.append(note);
  }
  const svgElement = (tag, attrs) => {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attrs))
      el.setAttribute(key, String(value));
    return el;
  };
  function chart(r) {
    const box = $("projection-chart");
    box.replaceChildren();
    if (!baseline) return;
    if (!["dcf", "ddm"].includes(r.method)) return;

    // Use new interactive charts module
    if (window.financialCharts) {
      const doc = r.input_financials || baseline.financials;
      const historical = r.method === "ddm"
        ? doc.source.common_dividends?.historical || []
        : doc.historical || [];
      const forecast = r.projections || [];
      window.financialCharts.renderProjectionChart(
        "projection-chart",
        historical,
        forecast,
        r.method
      );
      return;
    }

    // Fallback to original SVG if charts module not loaded
    let rows, caption;
    if (r.method === "dcf") {
      rows = (r.input_financials || baseline.financials).historical
        .map((x) => ({
          value: x.revenue,
          label: x.period_end.slice(0, 4),
          historical: true,
        }))
        .concat(
          (r.projections || []).map((x) => ({
            value: x.Revenue,
            label: `Y${x.Year}`,
          })),
        );
      caption = "Revenue · historical (gray), your forecast (green)";
    } else if (r.method === "ddm") {
      rows = (
        (r.input_financials || baseline.financials).source.common_dividends
          ?.historical || []
      )
        .filter((x) => Number.isFinite(x.value))
        .map((x) => ({
          value: x.value,
          label: x.period_end.slice(0, 4),
          historical: true,
        }))
        .concat(
          (r.projections || []).map((x) => ({
            value: x.dividends,
            label: `Y${x.year}`,
          })),
        );
      caption =
        "Total common dividends · historical (gray), your forecast (green)";
    } else return;
    if (!rows.length) return;
    const width = 400,
      height = 160,
      max = Math.max(...rows.map((x) => x.value), 1),
      step = width / rows.length;
    const svg = svgElement("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": caption,
    });
    rows.forEach((x, i) => {
      const h = (Math.max(0, x.value) / max) * 110,
        rect = svgElement("rect", {
          x: i * step + 5,
          y: 120 - h,
          width: step - 10,
          height: h,
          fill: x.historical ? "#aebeb4" : "#176754",
          rx: 3,
        });
      const title = svgElement("title", {});
      title.textContent = `${x.label}: ${money(x.value)}`;
      rect.append(title);
      const text = svgElement("text", {
        x: i * step + step / 2,
        y: 141,
        "text-anchor": "middle",
        "font-size": 12,
        fill: "#5a6b63",
      });
      text.textContent = x.label;
      svg.append(rect, text);
    });
    box.append(svg);
    const p = document.createElement("p");
    p.className = "chart-caption";
    p.textContent = caption;
    box.append(p);
  }
  function bridge(r) {
    const box = $("bridge-chart");
    box.replaceChildren();
    if (!Number.isFinite(r.enterprise_value)) return;
    const values = [
        ["Enterprise", r.enterprise_value],
        ["Net claims", r.enterprise_value - r.equity_value],
        ["Common equity", r.equity_value],
      ],
      max = Math.max(...values.map(([, v]) => Math.abs(v)), 1);
    for (const [label, value] of values) {
      const row = document.createElement("div");
      row.className = "price-bar-row";
      const text = document.createElement("span");
      text.textContent = label;
      const track = document.createElement("div");
      track.className = "price-track";
      const fill = document.createElement("div");
      fill.className = "price-fill";
      fill.style.width = `${(Math.abs(value) / max) * 100}%`;
      track.append(fill);
      const val = document.createElement("strong");
      val.textContent = value.toLocaleString(undefined, {
        style: "currency",
        currency: "USD",
        notation: "compact",
        maximumFractionDigits: 1,
      });
      row.append(text, track, val);
      box.append(row);
    }
    const caption = document.createElement("p");
    caption.className = "chart-caption";
    caption.textContent =
      "Value today: enterprise less net claims = common equity.";
    box.append(caption);
  }
  function sensitivity(r) {
    const box = $("live-sensitivity");
    box.replaceChildren();
    if (!r.sensitivity) {
      box.textContent = "Sensitivity is available for DCF and DDM.";
      return;
    }

    // Use new interactive charts module
    if (window.financialCharts) {
      window.financialCharts.renderSensitivityChart(
        "live-sensitivity",
        r.sensitivity,
        r.target_price_12m
      );
      return;
    }

    // Fallback to original implementation
    const table = document.createElement("table");
    table.className = "heatmap";
    const header = document.createElement("tr");
    for (const v of ["Rate / growth", ...r.sensitivity.growth_rates.map(pct)]) {
      const th = document.createElement("th");
      th.textContent = v;
      header.append(th);
    }
    table.append(header);
    for (const row of r.sensitivity.rows) {
      const tr = document.createElement("tr"),
        th = document.createElement("th");
      th.textContent = pct(row.wacc ?? row.rate);
      tr.append(th);
      for (const value of row.values) {
        const td = document.createElement("td");
        td.textContent = money(value);
        if (Number.isFinite(value) && Number.isFinite(r.current_price) && r.current_price > 0) {
          const spread = (value - r.current_price) / r.current_price;
          const strength = Math.min(0.35, Math.max(0.04, Math.abs(spread) * 1.2));
          td.style.background = spread >= 0 ? `rgba(23,103,84,${strength})` : `rgba(154,52,52,${strength})`;
          td.style.color = spread >= 0 ? "#0e654e" : "#943d35";
        }
        tr.append(td);
      }
      table.append(tr);
    }
    box.append(table);
  }
  $("save-valuation").addEventListener("click", async () => {
    const key = method,
      item = results.get(key);
    if (!item?.valid || item.saving) return;
    item.saving = true;
    const snapshot = JSON.stringify(item.form),
      token = generation;
    $("save-valuation").disabled = true;
    try {
      const body = new URLSearchParams();
      for (const [k, v] of Object.entries(item.form)) body.set(k, v);
      const r = await fetch(
        key === "dcf" ? "/api/calculate" : `/api/calculate/${key}`,
        { method: "POST", body },
      );
      const data = await r.json();
      if (!r.ok) throw Error(data.error || "Saving failed.");
      if (token === generation && snapshot === JSON.stringify(item.form)) {
        item.saved = !!data.saved_record_id;
        if (key === method)
          $("save-status").textContent = data.saved_record_id
            ? `Saved · record ${data.saved_record_id}`
            : "Storage is not enabled in this environment.";
      }
    } catch (e) {
      if (key === method) $("save-status").textContent = e.message;
    } finally {
      item.saving = false;
      if (key === method && token === generation)
        $("save-valuation").disabled = !results.get(method)?.valid;
    }
  });
  function download(format) {
    const item = results.get(method);
    if (!item?.valid) return;
    const payload = {
      financials: item.result.input_financials,
      assumptions: item.result.assumptions,
    };
    const exportForm = document.createElement("form");
    exportForm.method = "POST";
    exportForm.action =
      method === "dcf" ? `/export/${format}` : `/export/${method}/${format}`;
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = method === "dcf" ? "payload" : "suite_payload";
    input.value = JSON.stringify(payload);
    exportForm.append(input);
    document.body.append(exportForm);
    exportForm.requestSubmit();
    exportForm.remove();
  }
  $("compare-scenario").addEventListener("click", async () => {
    const item = results.get(method);
    if (!item?.valid) return;
    const form = new FormData();
    form.set("ticker", baseline.financials.company.ticker);
    form.set("assumptions", JSON.stringify(item.result.assumptions));
    form.set("base_document", JSON.stringify(
      method === "dcf" ? item.result.input_financials : baseline.financials
    ));
    const target = document.createElement("form");
    target.method = "POST";
    target.action = "/compare";
    for (const [k, v] of form.entries()) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = k;
      input.value = v;
      target.append(input);
    }
    document.body.append(target);
    target.requestSubmit();
  });
  $("export-xlsx").addEventListener("click", () => download("xlsx"));
  $("export-json").addEventListener("click", () => download("json"));
  $("export-csv").addEventListener("click", () => download("csv"));
  const DCF_TEMPLATE_FIELDS = [
    ["growth", "revenue_growth_rates"],
    ["ebit_margin", "ebit_margins"],
    ["da_margin", "da_margins"],
    ["capex_margin", "capex_margins"],
    ["nwc_margin", "nwc_margins"],
    ["tax_rate", "tax_rates"],
    ["net_income_margin", "net_income_margins"],
    ["book_value_margin", "book_value_margins"],
  ];
  function templateToForm(key, assumptions) {
    const source = results.get(key)?.form || results.get(key)?.data?.form || baseline?.form || {};
    const form = { ...source };
    if (key === "dcf") {
      for (const [field, name] of DCF_TEMPLATE_FIELDS)
        (assumptions[name] || []).forEach((v, i) => {
          if (Number.isFinite(v)) form[`${field}_${i}`] = String(v * 100);
        });
      if (Number.isFinite(assumptions.wacc_override))
        form.wacc = String(assumptions.wacc_override * 100);
      if (Number.isFinite(assumptions.terminal_growth_rate))
        form.terminal_growth = String(assumptions.terminal_growth_rate * 100);
      if (Number.isFinite(assumptions.terminal_roic))
        form.terminal_roic = String(assumptions.terminal_roic * 100);
      if (assumptions.terminal_mode) form.terminal_mode = assumptions.terminal_mode;
      for (const name of ["future_debt", "future_cash", "future_shares", "future_preferred", "future_minority", "future_other_assets"])
        if (assumptions[name] !== undefined && assumptions[name] !== null && assumptions[name] !== "")
          form[name] = String(assumptions[name]);
    } else if (key === "ddm") {
      (assumptions.dividend_growth_rates || []).forEach((v, i) => {
        if (Number.isFinite(v)) form[`dividend_growth_${i}`] = String(v * 100);
      });
      if (Number.isFinite(assumptions.required_return))
        form.required_return = String(assumptions.required_return * 100);
      if (Number.isFinite(assumptions.terminal_growth_rate))
        form.terminal_growth = String(assumptions.terminal_growth_rate * 100);
      if (assumptions.future_shares) form.future_shares = String(assumptions.future_shares);
    } else {
      form.valuation_basis = assumptions.valuation_basis || "cuig_forward";
      for (const name of ["ev_revenue", "ev_ebitda", "ev_ebit", "pe", "pb"])
        form[`include_${name}`] = (assumptions.included_methods || []).includes(name) ? "yes" : "";
    }
    return form;
  }
  async function loadTemplates() {
    const list = $("template-list");
    list.replaceChildren();
    try {
      const r = await fetch(`/api/templates?method=${method}`);
      const data = await r.json();
      for (const t of data || []) {
        const li = document.createElement("li");
        const apply = document.createElement("button");
        apply.type = "button";
        apply.className = "secondary";
        apply.textContent = `Apply ${t.name}`;
        apply.addEventListener("click", () => {
          const data = results.get(method)?.data || baseline;
          if (!data) return;
          send(method, { financials: data.financials, form: templateToForm(method, t.assumptions) });
          $("template-status").textContent = `Applied ${t.name}.`;
        });
        const del = document.createElement("button");
        del.type = "button";
        del.className = "text-button";
        del.textContent = "Delete";
        del.addEventListener("click", async () => {
          await fetch(`/api/templates/${t.id}`, { method: "DELETE" });
          loadTemplates();
        });
        li.append(apply, " ", del);
        list.append(li);
      }
      if (!list.children.length) list.textContent = "No saved templates yet.";
    } catch {
      list.textContent = "Templates unavailable.";
    }
  }
  $("template-save").addEventListener("click", async () => {
    const name = $("template-name").value.trim();
    const assumptions = results.get(method)?.result?.assumptions;
    if (!name || !assumptions) {
      $("template-status").textContent = "Name the template and load a company first.";
      return;
    }
    const r = await fetch("/api/templates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, method, assumptions }),
    });
    const data = await r.json();
    $("template-status").textContent = r.ok ? `Saved ${name}.` : data.error || "Save failed.";
    if (r.ok) { $("template-name").value = ""; loadTemplates(); }
  });
  document.getElementById("template-box")?.addEventListener("toggle", (e) => {
    if (e.target.open) loadTemplates();
  });
  $("management-guidance")
    .querySelector("details")
    .addEventListener("toggle", (event) => {
      if (event.currentTarget.open && baseline && !guidanceRequested) {
        guidanceRequested = true;
        loadGuidance(baseline.financials.company.ticker, generation);
      }
    });
  const mobile = window.matchMedia("(max-width:900px)");
  $("visual-details").open = !mobile.matches;
  mobile.addEventListener("change", (event) => {
    $("visual-details").open = !event.matches;
  });
  document.querySelector(".method-nav").hidden = true;
  createEditor("dcf");
})();
