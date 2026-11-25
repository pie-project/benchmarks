window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("reports");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const STATUS = { open: "Open" };

  const outliers = () => {
    try { return Pie.board?.outliers?.() || []; } catch { return []; }
  };
  const openCount = () => outliers().length;

  const nameOf = (table, id) => {
    const row = (Pie.store.rows(table) || []).find((r) => r.id === id);
    return row?.name || row?.label || id;
  };
  const tag = Pie.format;
  const day = (t) => new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const statusTag = (s) => `<span class="status-tag is-noisy">${esc(STATUS[s] || s)}</span>`;

  const OUTLIER_WORKLOAD = { decode: "decode", prefill: "prefill", batching: "batching", pbatch: "pbatch" };
  const TYPES = {
    limit: { label: "Exceeds Theoretical Limit", color: "#FF9500", title: "Pie measures above the hardware's theoretical maximum: the run or the limit's inputs are off" },
  };
  const typeTag = (t) => `<span class="cell-dot" style="--dot: ${TYPES[t].color}" title="${esc(TYPES[t].title)}">${esc(TYPES[t].label)}</span>`;
  let typeFilter = (() => { try { const v = localStorage.getItem("pieReportsType"); return TYPES[v] ? v : ""; } catch { return ""; } })();
  const keeps = (t) => !typeFilter || t === typeFilter;
  let focused = null;
  const inFocus = (r) => !focused || (r.hardware === focused.hardware && r.model === focused.model && (!focused.setup || !r.setup || r.setup === focused.setup));
  const outlierRow = (o, i) => `
    <tr class="is-outlier-row" data-pick>
      <td class="row-number">${i + 1}</td>
      <td>${typeTag("limit")}</td>
      <td>${statusTag("open")}</td>
      <td>${tag.engineTag(o.engine, nameOf("engines", o.engine))}</td>
      <td>${esc(nameOf("models", o.model))}${o.miniature ? ` <span class="reports-none">(slice)</span>` : ""}</td>
      <td>${tag.hardwareTag(o.hardware)}</td>
      <td><span class="workload-tag">${Pie.platform.degree(OUTLIER_WORKLOAD[o.setup])}${esc(o.label)}</span></td>
      <td class="is-numeric">${esc(`${Math.round(o.pie).toLocaleString("en-US")} ${o.unit}`)}</td>
      <td class="is-wide reports-auto">${o.above ? "Above theoretical limit" : `Slower than strongest competitor (${esc(nameOf("engines", o.best))} ${Math.round(o.bestValue).toLocaleString("en-US")} ${esc(o.unit)})`}</td>
      <td class="reports-auto">Auto</td>
      <td>${esc(o.measured ? day(String(o.measured).replace(" ", "T")) : dataDay())}</td>
      <td class="reports-fix-cell">${issueLinks(o)}</td>
    </tr>`;
  const ISSUES = "https://github.com/pie-project/pie/issues";
  const PLATFORM_NAME = { mac: "Apple", windows: "Windows", nvidia: "NVIDIA", amd: "AMD", tpu: "TPU", android: "Mobile", web: "WebGPU", cerebras: "Cerebras" };
  const issueLinks = (o) => {
    const code = Pie.platformOf(Pie.store.index.hardware[o.hardware] || {});
    const platform = PLATFORM_NAME[code] || "";
    const link = `${ISSUES}?q=${encodeURIComponent(`is:issue is:open label:benchmarks in:title "[${platform}] Benchmarks"`)}`;
    return `<a class="reports-issue" href="${esc(link)}" target="_blank" rel="noopener" title="Open [${esc(platform)}] Benchmarks on GitHub">${esc(platform)} Reports<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 11 11 5M6 5h5v5"/></svg></a>`;
  };
  const dataDay = () => { const at = Pie.store.tables.updated_at; return at ? day(at) : ""; };

  const COLUMNS = 12;
  let sort = null;
  const SORTS = [["type", "Type"], ["status", "Status"], ["engine", "Engine"], ["model", "Model"], ["hardware", "Hardware"],
    ["workload", "Workload"], ["value", "Value", true], ["details", "Details"], ["reporter", "Reported by"], ["date", "Date"]];
  const sortKey = ({ x }, key) => {
    switch (key) {
      case "type": return TYPES.limit.label;
      case "status": return STATUS.open;
      case "engine": return nameOf("engines", x.engine);
      case "model": return nameOf("models", x.model);
      case "hardware": return x.hardware === "unknown" ? "" : nameOf("hardware", x.hardware);
      case "workload": return x.label;
      case "value": return Number.isFinite(x.pie) ? x.pie : null;
      case "details": return x.above ? "Above theoretical limit" : "Slower than strongest competitor";
      case "reporter": return "Auto";
      case "date": { const t = Date.parse(String(x.measured || "").replace(" ", "T")); return Number.isFinite(t) ? t : null; }
      default: return null;
    }
  };
  const ordered = (items) => {
    if (!sort) return items;
    const numeric = SORTS.find(([key]) => key === sort.key)?.[2];
    const keyed = items.map((item, at) => ({ item, at, key: sortKey(item, sort.key) }));
    const empty = (k) => k === null || k === undefined || k === "";
    keyed.sort((a, b) => {
      if (empty(a.key) || empty(b.key)) return empty(a.key) - empty(b.key) || a.at - b.at;
      const order = numeric || typeof a.key === "number" ? a.key - b.key : String(a.key).localeCompare(String(b.key), "en", { numeric: true, sensitivity: "base" });
      return order * sort.direction || a.at - b.at;
    });
    return keyed.map(({ item }) => item);
  };
  const sortHead = ([key, label, numeric]) => `<th${numeric ? ' class="is-numeric"' : ""} data-reports-sort="${key}" title="Sort by ${label}">${label}${sort?.key === key ? `<span class="column-sort">${sort.direction > 0 ? "↑" : "↓"}</span>` : ""}</th>`;
  const list = () => {
    const note = (text) => `<tr><td class="table-empty" colspan="${COLUMNS}">${esc(text)}</td></tr>`;
    const found = outliers().filter((o) => keeps("limit") && inFocus(o));
    shown = `${found.length.toLocaleString("en-US")} ${found.length === 1 ? "row" : "rows"}`;
    const body = found.length ? ordered(found.map((x) => ({ x }))).map((it, i) => outlierRow(it.x, i)).join("") : note("No reports yet");
    return `
      <div class="reports-table-wrap">
        <table class="data-table reports-table">
          <thead><tr><th class="row-number" aria-label="Row"></th>${SORTS.map(sortHead).join("")}<th>Issue</th></tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>`;
  };

  element.addEventListener("click", (event) => {
    const head = event.target.closest("[data-reports-sort]");
    if (!head) return;
    const key = head.dataset.reportsSort;
    sort = sort?.key !== key ? { key, direction: 1 } : sort.direction > 0 ? { key, direction: -1 } : null;
    draw();
  });
  Pie.pickRows = (root) => {
    let anchor = null;
    root.addEventListener("mousedown", (event) => { if (event.shiftKey && event.target.closest("tr[data-pick]")) event.preventDefault(); });
    root.addEventListener("click", (event) => {
      const tr = event.target.closest("tr[data-pick]");
      if (!tr || event.target.closest("a, button, input, select")) return;
      const rows = [...root.querySelectorAll("tr[data-pick]")], at = rows.indexOf(tr);
      const set = (row, on) => { row.classList.toggle("is-picked", on); row.setAttribute("aria-selected", on); };
      if (event.shiftKey && anchor !== null) {
        if (!event.metaKey && !event.ctrlKey) rows.forEach((row) => set(row, false));
        rows.slice(Math.min(anchor, at), Math.max(anchor, at) + 1).forEach((row) => set(row, true));
        return;
      }
      if (event.metaKey || event.ctrlKey) set(tr, !tr.classList.contains("is-picked"));
      else {
        const only = tr.classList.contains("is-picked") && rows.filter((row) => row.classList.contains("is-picked")).length === 1;
        rows.forEach((row) => set(row, false));
        if (!only) set(tr, true);
      }
      anchor = at;
    });
  };
  Pie.pickRows(element);

  let shown = "";
  const draw = () => {
    if (element.hidden) return;
    element.innerHTML = list();
    if (Pie.toolbar?.elements?.subtitle) Pie.toolbar.elements.subtitle.textContent = shown;
  };

  const fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US", { maximumFractionDigits: n < 10 ? 2 : 0 }) : n);
  const valueOf = (row, source) => source === "quality"
    ? (row.score != null ? `Score ${fmt(row.score)}` : "")
    : [["decode_tok_s", "decode"], ["prefill_tok_s", "prefill"], ["output_tok_s", "output"]]
      .filter(([k]) => row[k] != null).map(([k, label]) => `${fmt(row[k])} tok/s ${label}`).join(", ");

  document.addEventListener("click", (event) => {
    const clear = event.target.closest("[data-reports-unfocus]");
    if (clear) { focused = null; clear.closest(".filter")?.remove(); draw(); return; }
    const button = event.target.closest("[data-reports-pick]");
    if (!button) return;
    event.stopPropagation();
    Pie.popover.open(button, `reports:${button.dataset.reportsPick}`, null);
  }, true);

  Pie.reports = {
    element,
    focus(hardware, model, setup) { focused = { hardware, model, setup: setup || null }; if (!element.hidden) draw(); },
    bar() {
      const chip = focused ? `<span class="filter is-set"><button class="filter-button" type="button" data-reports-unfocus title="Show every report">${esc([nameOf("hardware", focused.hardware), nameOf("models", focused.model), focused.setup && { decode: "Single Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" }[focused.setup]].filter(Boolean).join(" · "))}<svg class="popup-chevron" viewBox="0 0 10 10" aria-hidden="true"><path d="M2.5 2.5l5 5M7.5 2.5l-5 5"/></svg></button></span>` : "";
      return chip;
    },
    menu(k) {
      if (k !== "type") return [];
      return [{ value: "", label: "All Types", selected: !typeFilter },
        ...Object.entries(TYPES).map(([id, t]) => ({ value: id, label: t.label, selected: id === typeFilter, icon: `<span class="cell-dot" style="--dot: ${t.color}"></span>` }))];
    },
    pick(k, value) {
      if (k !== "type") return;
      typeFilter = TYPES[value] ? value : "";
      try { localStorage.setItem("pieReportsType", typeFilter); } catch { }
      draw();
    },
    open: () => openCount(),
    shown: () => shown,
    flag(rows, source, sent) {
      if (!rows.length) return;
      const lines = rows.map((row) => `| ${nameOf("engines", row.engine)} | ${nameOf("models", row.model)} | ${nameOf("hardware", row.hardware || row.platform)} | ${source === "quality" ? row.task : nameOf("workloads", row.workload)} | ${valueOf(row, source) || "—"} |`);
      const body = `<!-- What looks off in these measurements? -->\n\n\n| Engine | Model | Machine | ${source === "quality" ? "Task" : "Workload"} | Value |\n|---|---|---|---|---|\n${lines.join("\n")}\n`;
      window.open(`https://github.com/pie-project/benchmarks/issues/new?body=${encodeURIComponent(body)}&labels=report`, "_blank", "noopener");
      sent?.();
    },
    render(state) {
      const was = element.hidden;
      element.hidden = state.table !== "reports";
      if (element.hidden) return;
      if (was) draw();
    },
  };
})();
