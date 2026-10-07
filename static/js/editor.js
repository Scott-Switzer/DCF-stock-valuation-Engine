"use strict";
(() => {
  if (
    !document.body.classList.contains("embedded-editor") ||
    window.parent === window
  )
    return;
  const form =
    document.getElementById("valuation-form") ||
    document.getElementById("suite-form");
  if (!form) return;
  const method = form.dataset.method || "dcf",
    parent = window.parent;
  let generation = 0,
    version = 0,
    timer,
    request,
    doc = null,
    analysts = null,
    filling = false;
  const scaledInputs = new Map();
  const preciseRates = new Map(),
    peerRequests = [0, 0, 0, 0];
  const emit = (data) =>
    parent.postMessage({ ...data, generation }, location.origin);
  const field = (name) => form.elements.namedItem(name);
  const set = (name, value) => {
    const el = field(name);
    if (!el) return;
    if (el.type === "checkbox") el.checked = value === "yes";
    else el.value = value ?? "";
  };
  const add = (box, tag, text, cls = "") => {
    const el = document.createElement(tag);
    el.textContent = text;
    el.className = cls;
    box.append(el);
    return el;
  };
  const pct = (value) =>
    Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "—";
  function collect() {
    const values = {};
    for (const [key, value] of new FormData(form))
      if (typeof value === "string") values[key] = value;
    for (const [name, rate] of preciseRates)
      if (values[name] === rate.display) values[name] = rate.raw;
    for (const [name, scale] of scaledInputs) {
      if (values[name] !== "" && values[name] != null)
        values[name] =
          !scale.edited && values[name] === scale.display
            ? scale.raw
            : String(Number(values[name]) * 1e9);
    }
    return values;
  }
  function height() {
    emit({
      type: "editor-height",
      height:
        Math.ceil(
          document.querySelector("main").getBoundingClientRect().height,
        ) + 24,
    });
  }
  new ResizeObserver(height).observe(document.body);
  // Collapse provider/import/identity controls into a single inspectable disclosure.
  if (method !== "dcf") {
    for (const el of form.querySelectorAll(".ticker-loader,.suite-actions"))
      el.hidden = true;
    const importDetails = form
      .querySelector(".suite-actions")
      ?.closest("details");
    if (importDetails) importDetails.hidden = true;
  }
  const sourcePanel = form.querySelector("section.panel");
  if (sourcePanel) {
    const details = document.createElement("details");
    details.className = "panel sourced-settings";
    const summary = document.createElement("summary");
    summary.textContent = "Company data, sources and advanced providers";
    details.append(summary);
    sourcePanel.replaceWith(details);
    details.append(sourcePanel);
  }
  const sourceSettings = form.querySelector(".sourced-settings");
  if (sourceSettings) {
    const unlock = form.querySelector(".source-control");
    if (unlock) sourceSettings.append(unlock);
    for (const child of Array.from(form.children))
      if (child.matches("details.audit-details")) sourceSettings.append(child);
    const notes =
      document.getElementById("provider-notes") ||
      document.getElementById("suite-notes");
    if (notes) sourceSettings.append(notes);
    if (method === "ddm") {
      const baselineInputs = field("base_common_dividends")?.closest(".fields");
      if (baselineInputs) sourceSettings.append(baselineInputs);
    }
    if (method === "relative") {
      const forward = document.createElement("section");
      forward.className = "panel";
      add(forward, "h2", "Year-one target assumptions");
      const fields = add(forward, "div", "", "fields three");
      for (const [name, label] of [
        ["forward_revenue", "Revenue (USD billions)"],
        ["forward_ebitda", "EBITDA (USD billions)"],
        ["forward_net_income", "Common net income (USD billions)"],
      ]) {
        const input = field(name);
        if (input) {
          const wrapper = add(fields, "div", "", "field");
          const lab = add(wrapper, "label", label);
          input.id = name;
          input.setAttribute("aria-label", label);
          lab.htmlFor = name;
          wrapper.append(input);
        }
      }
      Array.from(form.children)
        .find((x) => x.matches("section.panel") && x.id !== "decision-context")
        ?.before(forward);
    }
    form.append(sourceSettings);
  }
  for (const p of form.querySelectorAll("p.help"))
    if (!p.closest("details") && !p.id) p.classList.add("routine-copy");
  const reference = document.createElement("section");
  reference.className = "compact-reference";
  reference.hidden = true;
  const anchor =
    method === "dcf"
      ? form.querySelector(".forecasts")?.closest(".table-wrap")
      : form.querySelector("#decision-context");
  if (anchor) anchor.before(reference);
  else form.prepend(reference);
  form.addEventListener(
    "submit",
    (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      schedule();
    },
    true,
  );
  function schedule() {
    clearTimeout(timer);
    version++;
    if (request) request.abort();
    emit({ type: "preview-pending" });
    timer = setTimeout(preview, 350);
  }
  async function preview() {
    if (!doc) return;
    const token = version,
      gen = generation;
    const invalid = [...form.elements].find(
      (el) => el.willValidate && !el.validity.valid,
    );
    if (invalid) {
      emit({
        type: "preview-error",
        error: `Review ${invalid.getAttribute("aria-label") || invalid.name.replaceAll("_", " ")}.`,
      });
      return;
    }
    request = new AbortController();
    try {
      const values = collect();
      const response = await fetch(`/api/preview/${method}`, {
        method: "POST",
        body: new URLSearchParams(values),
        signal: request.signal,
      });
      const result = await response.json();
      if (token !== version || gen !== generation) return;
      if (!response.ok) throw Error(result.error || "Unable to calculate.");
      emit({ type: "preview-result", result, form: values });
    } catch (error) {
      if (
        error.name !== "AbortError" &&
        token === version &&
        gen === generation
      )
        emit({ type: "preview-error", error: error.message });
    }
  }
  document.addEventListener("forecast-drivers-changed", () => {
    for (const el of form.elements) {
      if (
        !/^(ebit_margin|da_margin|capex_margin|nwc_margin|net_income_margin|book_value_margin|tax_rate)_\d$/.test(
          el.name,
        )
      )
        continue;
      preciseRates.delete(el.name);
      if (el.value !== "" && Number.isFinite(Number(el.value))) {
        const raw = el.value;
        el.value = Number(raw).toFixed(2);
        preciseRates.set(el.name, { raw, display: el.value });
      }
    }
    if (doc) schedule();
  });
  form.addEventListener("input", (event) => {
    if (!doc || !event.target.name) return;
    preciseRates.delete(event.target.name);
    if (scaledInputs.has(event.target.name))
      scaledInputs.get(event.target.name).edited = true;
    const peerIndex = event.target.name.match(
      /^peer_(?:ev_revenue|ev_ebitda|ev_ebit|pe|pb)_(\d)$/,
    );
    if (peerIndex) peerStats(Number(peerIndex[1]));
    schedule();
  });
  form.addEventListener("change", (event) => {
    if (!doc || !event.target.name) return;
    schedule();
  });
  function references() {
    reference.replaceChildren();
    if (!doc || method === "relative") {
      reference.hidden = true;
      return;
    }
    reference.hidden = false;
    const dividend = method === "ddm";
    const hist =
      doc.source[
        dividend ? "dividend_growth_reference" : "revenue_growth_reference"
      ];
    add(
      reference,
      "strong",
      dividend ? "Dividend growth reference" : "Revenue growth reference",
    );
    const table = add(reference, "table", "");
    const head = add(table, "tr", "");
    for (const text of dividend
      ? ["Fiscal period", "Dividend growth"]
      : ["Fiscal period", "Historical growth", "Analyst expected growth"])
      add(head, "th", text);
    const dates = [
      ...new Set([
        ...(hist?.annual || []).map((x) => x.period_end),
        ...(dividend ? [] : analysts?.revenue || []).map((x) => x.period_end),
      ]),
    ].sort();
    for (const date of dates) {
      const row = add(table, "tr", "");
      add(row, "td", date.slice(0, 4));
      add(
        row,
        "td",
        pct(hist?.annual?.find((x) => x.period_end === date)?.growth),
      );
      if (!dividend)
        add(
          row,
          "td",
          pct(analysts?.revenue?.find((x) => x.period_end === date)?.growth),
        );
    }
    const actions = add(reference, "div", "", "compact-actions");
    const cagr = hist?.cagr;
    if (Number.isFinite(cagr)) {
      const button = add(actions, "button", `Use historical CAGR ${pct(cagr)}`);
      button.type = "button";
      button.addEventListener("click", () => {
        for (let i = 0; i < 5; i++)
          set(
            dividend ? `dividend_growth_${i}` : `growth_${i}`,
            (cagr * 100).toFixed(2),
          );
        schedule();
      });
    }
    if (!dividend && analysts) {
      const latest = doc.historical?.at(-1)?.period_end;
      const year = Number(latest?.slice(0, 4));
      const applicable = (analysts.revenue || []).filter(
        (x) =>
          Number.isFinite(x.growth) &&
          Number(x.period_end.slice(0, 4)) > year &&
          Number(x.period_end.slice(0, 4)) <= year + 5 &&
          x.period_end.slice(5, 7) === latest.slice(5, 7),
      );
      if (applicable.length) {
        const button = add(
          actions,
          "button",
          "Use consensus for matching years",
        );
        button.type = "button";
        button.addEventListener("click", () => {
          for (const x of applicable)
            set(
              `growth_${Number(x.period_end.slice(0, 4)) - year - 1}`,
              (x.growth * 100).toFixed(2),
            );
          schedule();
        });
      }
      const source = add(
        reference,
        "a",
        "Yahoo analyst estimates · source",
        "reference-source",
      );
      source.href = analysts.source_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
    }
    add(
      reference,
      "p",
      dividend
        ? "Total common cash dividends; excludes repurchases. CAGR is a reference, not a forecast."
        : "Only matching future fiscal years are applied. Other years stay as your assumptions.",
      "reference-source",
    );
    if (!dividend && !analysts)
      add(
        reference,
        "p",
        "Analyst estimates loading or unavailable; historical references remain available.",
        "reference-source",
      );
  }
  let peerBox;
  if (method === "relative") {
    peerBox = document.createElement("div");
    form.querySelector(".peer-table")?.closest(".table-wrap").before(peerBox);
    const original = form.querySelector(".peer-table")?.closest(".table-wrap");
    if (original) {
      const details = document.createElement("details");
      details.className = "audit-details";
      add(details, "summary", "Inspect or override sourced peer multiples");
      original.before(details);
      details.append(original);
    }
    const marker = document.createElement("input");
    marker.type = "hidden";
    marker.name = "peer_selection";
    marker.value = "explicit";
    form.append(marker);
    for (let i = 0; i < 4; i++) {
      const include = document.createElement("input");
      include.type = "hidden";
      include.name = `peer_include_${i}`;
      form.append(include);
    }
  }
  function writePeer(index, peer) {
    for (const key of ["ticker", "name", "as_of", "source"])
      set(`peer_${key}_${index}`, peer?.[key] || "");
    for (const key of ["ev_revenue", "ev_ebitda", "ev_ebit", "pe", "pb"])
      set(`peer_${key}_${index}`, peer?.multiples?.[key] ?? "");
    set(`peer_include_${index}`, peer ? "yes" : "");
  }
  function peerStats(index) {
    const element = peerBox?.querySelector(`[data-peer-stats="${index}"]`);
    if (!element) return;
    const values = ["ev_revenue", "ev_ebitda", "pe"].map((key) => {
      const value = field(`peer_${key}_${index}`).value;
      return value !== "" && Number.isFinite(Number(value))
        ? Number(value).toFixed(1)
        : "—";
    });
    element.textContent = `EV/Revenue ${values[0]}× · EV/EBITDA ${values[1]}× · P/E ${values[2]}×`;
  }
  function peers(initial = false, changedIndex = null) {
    if (!peerBox || !doc) return;
    const selections = Array.from(
      { length: 4 },
      (_, i) => field(`peer_include_${i}`).value,
    );
    const before = Array.from({ length: 4 }, (_, i) =>
      Object.fromEntries(
        [
          "ticker",
          "name",
          "as_of",
          "source",
          "ev_revenue",
          "ev_ebitda",
          "ev_ebit",
          "pe",
          "pb",
        ].map((key) => [key, field(`peer_${key}_${i}`)?.value]),
      ),
    );
    peerBox.replaceChildren();
    const suggestions =
      doc.source.peer_suggestions ||
      doc.comparables.map((x) => ({
        ticker: x.ticker,
        name: x.name,
        available: true,
      }));
    for (let i = 0; i < 4; i++) {
      const candidate = suggestions[i] || {
        ticker: "",
        name: "Replace candidate",
        available: false,
      };
      const peer = doc.comparables.find((x) => x.ticker === candidate.ticker);
      writePeer(i, peer);
      if (!initial) {
        set(`peer_include_${i}`, selections[i]);
        if (i !== changedIndex)
          for (const [key, value] of Object.entries(before[i]))
            set(`peer_${key}_${i}`, value);
      }
      const card = add(peerBox, "article", "", "peer-card");
      const label = add(card, "label", "", "check"),
        checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !!peer && field(`peer_include_${i}`).value === "yes";
      checkbox.disabled = !peer;
      checkbox.setAttribute(
        "aria-label",
        `Include ${candidate.ticker || "peer " + (i + 1)}`,
      );
      label.append(
        checkbox,
        document.createTextNode(
          `${candidate.ticker || "Candidate " + (i + 1)} · ${peer?.name || candidate.name}`,
        ),
      );
      checkbox.addEventListener("change", () => {
        set(`peer_include_${i}`, checkbox.checked ? "yes" : "");
        schedule();
      });
      add(card, "p", candidate.fit_label || "Fit unverified");
      if (peer) {
        const stats = add(card, "p", "");
        stats.dataset.peerStats = String(i);
        peerStats(i);
      }
      add(
        card,
        "p",
        `${candidate.industry || "Industry unverified"} · ${(candidate.shared_products_segments || []).join(", ") || "Shared products unverified"}${candidate.market_cap_ratio != null ? " · " + candidate.market_cap_ratio.toFixed(2) + "× target market-equity size" : ""}`,
      );
      if (candidate.caveats?.length)
        add(card, "p", candidate.caveats.join(" "));
      add(
        card,
        "p",
        peer
          ? `${peer.source} · ${peer.as_of}`
          : "Snapshot unavailable · excluded until replaced.",
        "reference-source",
      );
      const controls = add(card, "div", "", "peer-change"),
        input = document.createElement("input");
      input.value = candidate.ticker;
      input.maxLength = 9;
      input.setAttribute("aria-label", `Replacement peer ${i + 1} ticker`);
      controls.append(input);
      const button = add(controls, "button", "Replace & load");
      button.type = "button";
      const notice = add(card, "p", "", "reference-source");
      button.addEventListener("click", async () => {
        const token = generation,
          revision = ++peerRequests[i];
        button.disabled = true;
        notice.textContent = "Loading sourced peer data…";
        try {
          const response = await fetch("/api/peer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: input.value.trim().toUpperCase() }),
          });
          const data = await response.json();
          if (token !== generation || revision !== peerRequests[i]) return;
          if (!response.ok) throw Error(data.error || "Peer unavailable.");
          if (
            data.ticker === doc.company.ticker ||
            suggestions.some(
              (x, j) =>
                j !== i &&
                (x.ticker === data.ticker ||
                  (["GOOG", "GOOGL"].includes(x.ticker) &&
                    ["GOOG", "GOOGL"].includes(data.ticker))),
            )
          )
            throw Error(
              "Choose a different company; duplicate issuers cannot be included.",
            );
          doc.comparables = doc.comparables.filter(
            (x) => x.ticker !== candidate.ticker,
          );
          doc.comparables.push(data);
          suggestions[i] = {
            ticker: data.ticker,
            name: data.name,
            available: true,
            fit_label: "User-selected peer; review fit",
            industry: "Fit unverified",
          };
          doc.source.peer_suggestions = suggestions;
          doc.comparables = suggestions
            .map((x) => doc.comparables.find((p) => p.ticker === x.ticker))
            .filter(Boolean);
          field("base_document").value = JSON.stringify(doc);
          set(`peer_include_${i}`, "yes");
          peers(false, i);
          filling = true;
          document.dispatchEvent(new Event("financials-loaded"));
          filling = false;
          schedule();
        } catch (e) {
          notice.textContent = e.message;
        } finally {
          button.disabled = false;
        }
      });
    }
  }
  function fill(data) {
    filling = true;
    preciseRates.clear();
    scaledInputs.clear();
    if (
      doc?.company?.ticker !== data.financials.company.ticker ||
      doc?.source?.kind !== data.financials.source.kind
    )
      analysts = null;
    doc = data.financials;
    document.dispatchEvent(
      new CustomEvent("workspace-fill", { detail: data.form }),
    );
    for (const name of Array.from(form.elements)
      .map((x) => x.name)
      .filter((name) =>
        /^(wacc|required_return|terminal_growth|(?:growth|dividend_growth|ebit_margin|da_margin|capex_margin|nwc_margin|tax_rate|net_income_margin|book_value_margin)_\d)$/.test(
          name,
        ),
      )) {
      const el = field(name);
      if (el && el.value !== "" && Number.isFinite(Number(el.value))) {
        const raw = el.value;
        el.value = Number(raw).toFixed(2);
        preciseRates.set(name, { raw, display: el.value });
      }
    }
    if (method === "relative")
      for (const name of [
        "forward_revenue",
        "forward_ebitda",
        "forward_net_income",
      ]) {
        const input = field(name);
        if (
          input &&
          input.value !== "" &&
          Number.isFinite(Number(input.value))
        ) {
          const raw = input.value;
          input.value = (Number(raw) / 1e9).toFixed(2);
          scaledInputs.set(name, { raw, display: input.value, edited: false });
        }
      }
    const costSummary = document.getElementById("capital-cost-summary"),
      costDetails = document.getElementById("capital-cost-details");
    if (costSummary)
      costSummary.textContent =
        "Starting capital costs from loaded market inputs; editable assumption.";
    if (costDetails)
      costDetails.textContent = JSON.stringify(
        doc.source.capital_costs || {},
        null,
        2,
      );
    for (const id of ["provider-message", "suite-message"]) {
      const el = document.getElementById(id);
      if (el) el.hidden = true;
    }
    const notes =
      document.getElementById("provider-notes") ||
      document.getElementById("suite-notes");
    if (notes) {
      const ul = notes.querySelector("ul");
      ul.replaceChildren();
      for (const text of data.warnings || []) add(ul, "li", text);
      notes.hidden = !(data.warnings || []).length;
      notes.querySelector("summary").textContent =
        `Source and methodology notes (${(data.warnings || []).length})`;
    }
    references();
    peers(true);
    filling = false;
    schedule();
    height();
  }
  document.addEventListener("financials-loaded", () => {
    if (filling) return;
    try {
      const loaded = JSON.parse(field("base_document").value);
      doc = loaded;
      analysts = null;
      preciseRates.clear();
      scaledInputs.clear();
      version++;
      if (request) request.abort();
      references();
      peers(true);
      schedule();
      emit({ type: "editor-company", financials: loaded, form: collect() });
    } catch (_) {
      emit({ type: "preview-error", error: "Source document is invalid." });
    }
  });
  window.addEventListener("message", (event) => {
    if (event.origin !== location.origin || event.source !== parent) return;
    const message = event.data || {};
    if (message.type === "workspace-reset") {
      generation = message.generation;
      version++;
      if (request) request.abort();
      clearTimeout(timer);
      doc = null;
      analysts = null;
      reference.hidden = true;
      form.hidden = true;
      return;
    }
    if (message.type === "workspace-data") {
      if (generation !== message.generation) analysts = null;
      generation = message.generation;
      form.hidden = false;
      fill(message.data);
    }
    if (
      message.type === "workspace-references" &&
      message.generation === generation
    ) {
      analysts = message.data;
      references();
      height();
    }
  });
  emit({ type: "editor-ready" });
  height();
})();
