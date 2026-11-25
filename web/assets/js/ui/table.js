window.Pie = window.Pie || {};

(() => {
  const { format, store, engines } = Pie;
  const container = document.getElementById("table-container");
  const table = document.getElementById("data-table");

  const headerMeta = (column, coverage) => {
    if (column.planned) return `<span class="column-planned">soon</span>`;
    if (coverage < 1) return `<span class="column-coverage${coverage < .5 ? " is-low" : ""}">${Math.round(coverage * 100)}%</span>`;
    return "";
  };

  const headerCell = (column, state) => {
    const coverage = store.coverage(state.table, column);
    const unit = column.unit ? `<span class="column-unit">${column.unit}</span>` : "";
    const sort = state.sort?.key === column.key ? `<span class="column-sort">${state.sort.direction > 0 ? "↑" : "↓"}</span>` : "";
    const hint = column.planned ? "Not collected yet" : `${Math.round(coverage * 100)}% of rows have a value`;
    const classes = column.type === "number" || column.numeric ? "is-numeric" : "";
    const info = column.info
      ? `<span class="column-info" tabindex="0" role="button" aria-label="${format.escape(column.info)}"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="column-info-pop" role="tooltip">${format.escape(column.info)}</span></span>`
      : "";
    return `<th class="${classes}" data-sort="${column.key}" title="${column.info ? "" : hint}">${column.label}${unit}${info}${headerMeta(column, coverage)}${sort}</th>`;
  };

  const bodyCell = (column, row) => {
    const value = row[column.key];
    if (column.na?.(row) && format.isEmpty(value)) {
      return `<td class="is-numeric is-empty" title="${format.escape(column.naHint || "")}">n/a</td>`;
    }
    const classes = [
      column.type === "number" || column.numeric ? "is-numeric" : "",
      column.code && !format.isEmpty(value) ? "is-code" : "",
      format.isEmpty(value) ? "is-empty" : "",
      column.wide ? "is-wide" : "",
    ].filter(Boolean).join(" ");
    const full = column.wide && !format.isEmpty(value) ? ` data-note="${format.escape(String(value))}"` : "";
    const TINT = { mac: "#8e8e93", gpu: "#76b900", tpu: "#4285f4", wafer: "#ff9500" };
    const LABEL = { mac: "Mac", gpu: "GPU", tpu: "TPU", wafer: "Wafer" };
    const dotted = (key, text) => `<span class="cell-dot" style="--dot: ${TINT[key] || "#8e8e93"}">${format.escape(text)}</span>`;
    if (column.key === "class" && !format.isEmpty(value)) {
      const key = String(value).toLowerCase();
      return `<td class="${classes}">${dotted(key, LABEL[key] || String(value))}</td>`;
    }
    const platform = column.key === "platform" && Object.entries(Pie.schema).find(([, s]) => s.view === "platform" && s.short === value);
    if (platform) {
      const [id, s] = platform;
      return `<td class="${classes}"><span class="welcome-cell"><span class="sidebar-glyph" style="--tint: ${s.tint}">${Pie.icon(id)}</span>${format.escape(value)}</span></td>`;
    }
    if (column.type === "reference" && column.table === "engines" && column.key === "id" && !format.isEmpty(value)) {
      const logo = Pie.engines.logo?.(value);
      if (logo) return `<td class="${classes}"><span class="engine-tag is-logo"><span class="model-badge" aria-hidden="true">${logo}</span>${format.escape(Pie.store.names.engine(value))}</span></td>`;
    }
    if (column.key === "name" && "base_model" in row && Pie.platform?.makerBadge) {
      return `<td class="${classes}"><span class="model-name-cell">${Pie.platform.makerBadge(row.id)}<span>${format.escape(value)}</span></span></td>`;
    }
    if (column.key === "platforms" && (!format.isEmpty(value) || row.fits)) {
      const ID = { mac: "mac", windows: "windows", gpu: "nvidia", tpu: "tpu", amd: "amd", wafer: "cerebras" };
      const has = String(value || "").toLowerCase().split(", ");
      const fits = String(row.fits || "").toLowerCase().split(", ");
      const slots = platformSlots().map((t) => {
        const s = Pie.schema[ID[t]];
        if (has.includes(t) && s) return `<span class="sidebar-glyph" style="--tint: ${s.tint}" title="${format.escape(s.label)}" aria-label="${format.escape(s.label)}">${Pie.icon(ID[t])}</span>`;
        if (fits.includes(t) && s) return `<span class="sidebar-glyph is-fit" style="--tint: ${s.tint}" title="${format.escape(`${s.label}: fits, not measured yet`)}" aria-label="${format.escape(`${s.label}, fits`)}">${Pie.icon(ID[t])}</span>`;
        return `<span class="cell-slot" aria-hidden="true"></span>`;
      });
      return `<td class="${classes}"><span class="cell-glyphs is-slotted">${slots.join("")}</span></td>`;
    }
    return `<td class="${classes}"${full}>${format.value(column, value)}</td>`;
  };

  let slotsOf = null;
  const platformSlots = () => slotsOf ||= ["mac", "windows", "gpu", "tpu", "amd", "wafer"]
    .filter((t) => (Pie.store.tables.models || []).some((m) => String(m.platforms || "").toLowerCase().split(", ").includes(t)));

  const flaggable = (state) => state.table === "results" || state.table === "quality";
  const picked = new Set();
  const keyOf = (row) => Object.keys(row).sort().filter((k) => row[k] == null || typeof row[k] !== "object").map((k) => `${k}=${row[k] ?? ""}`).join("|");
  let pickedOn = null;
  const reportButton = document.getElementById("report-selected");
  const downloadButton = document.getElementById("download-rows");
  const csvOf = (rows, columns) => {
    const cell = (v) => { const t = v == null ? "" : String(v); return /[",\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
    return [columns.map((c) => cell(c.label)).join(","), ...rows.map((r) => columns.map((c) => cell(r[c.key])).join(","))].join("\n");
  };
  const subtitle = document.getElementById("toolbar-subtitle");
  let base = "";
  const syncReport = () => {
    if (!reportButton) return;
    reportButton.disabled = !picked.size;
    if (subtitle && base) subtitle.textContent = picked.size ? `${base} · ${picked.size.toLocaleString("en-US")} selected` : base;
  };

  const bodyRow = (row, columns, state, index) => {
    const resultKey = store.resultKeys[state.table];
    const classes = [];
    let link = "";

    let stale = "";
    if ((state.table === "results" || state.table === "quality") && !row.stale && store.isMeasured(row)) classes.push("is-highlighted");
    if (state.table === "results" && !store.isMeasured(row)) classes.push("is-unmeasured");
    if (state.table === "results" && !row.miniature && overLimit().has(`${row.engine}|${row.hardware}|${row.model}|${OVER_SETUP[row.workload]}`)) classes.push("is-over-limit");
    else if (state.table === "results" && Pie.behind?.(row)) classes.push("is-gap");
    if (row.stale) {
      classes.push("is-stale");
      const when = row.stale.measured ? `, ${format.date(row.stale.measured)}` : "";
      stale = ` title="From ${format.escape(row.stale.tag)}${when}: this tag has no run for this setup"`;
    }
    if (resultKey) {
      classes.push("is-link");
      link = ` data-result-key="${resultKey}" data-result-value="${format.escape(row.id)}" title="Show results"`;
    }

    const cells = columns.map((column) => bodyCell(column, row)).join("");
    const filled = Pie.table.fill(cells, columns, state, "td");
    const number = Pie.schema[state.table].numbered ? `<td class="row-number">${index + 1}</td>` : "";
    if (picked.has(row)) classes.push("is-picked");
    const pick = flaggable(state) ? ` data-pick="${index}" aria-selected="${picked.has(row)}"` : "";
    return `<tr class="${classes.join(" ")}"${link || stale}${pick}>${number}${filled}</tr>`;
  };

  const OVER_SETUP = { raw_decode: "decode", raw_prefill: "prefill", throughput: "batching", prefill_batch: "pbatch" };
  let overFor = null, overKeys = new Set();
  const overLimit = () => {
    if (overFor !== Pie.store.tables) {
      overFor = Pie.store.tables;
      try { overKeys = new Set((Pie.board?.outliers?.() || []).map((o) => `${o.engine}|${o.hardware}|${o.model}|${o.setup}`)); } catch { overKeys = new Set(); }
    }
    return overKeys;
  };

  const SETUP = { raw_decode: "decode", raw_prefill: "prefill", spec_decode: "spec", throughput: "batching", prefill_batch: "pbatch" };
  let reviewFor = null, review = new Set();
  Pie.behind = (row) => {
    if (row.engine !== Pie.engines.primary || !SETUP[row.workload]) return false;
    if (reviewFor !== Pie.store.tables) {
      reviewFor = Pie.store.tables;
      review = new Set((Pie.platform?.gaps?.(Pie.state) || []).map((g) => `${g.hardware}|${g.model}|${g.setup}`)
        .filter((key) => !Pie.verifiedProfile?.(key)));
    }
    return review.has(`${row.hardware}|${row.model}|${SETUP[row.workload]}`);
  };

  Pie.table = {
    container,

    fill(cells, columns, state, tag) {
      if (Pie.schema[state.table].section !== "catalog") return cells;
      const blank = `<${tag} class="col-fill"></${tag}>`;
      if (columns[columns.length - 1]?.key !== "_results") return cells + blank;
      const at = cells.lastIndexOf(`<${tag}`);
      return cells.slice(0, at) + blank + cells.slice(at);
    },

    visibleColumns(state) {
      return Pie.schema[state.table].columns.filter((column) => !column.hidden);
    },

    render(state, rows) {
      const columns = this.visibleColumns(state);
      const numbered = Pie.schema[state.table].numbered;
      const corner = numbered ? `<th class="row-number" aria-label="Row"></th>` : "";
      if (pickedOn !== state.table) { picked.clear(); pickedOn = state.table; }
      if (picked.size) { const shown = new Set(rows); for (const r of picked) if (!shown.has(r)) picked.delete(r); }
      const head = `<thead><tr>${corner}${this.fill(columns.map((column) => headerCell(column, state)).join(""), columns, state, "th")}</tr></thead>`;
      this.rows = rows;
      this.source = state.table;
      if (reportButton) reportButton.hidden = !flaggable(state);
      if (downloadButton) downloadButton.hidden = !flaggable(state);
      const keys = document.getElementById("table-keys");
      if (keys) keys.hidden = !flaggable(state);
      const errorKey = document.getElementById("table-key-error");
      if (errorKey) errorKey.hidden = state.table !== "results";
      const reviewKey = document.getElementById("table-key-review");
      if (reviewKey) reviewKey.hidden = state.table !== "results";
      this.columns = Pie.schema[state.table].columns.filter((c) => c.key && !c.key.startsWith("_"));
      base = flaggable(state) ? subtitle?.textContent || "" : "";
      syncReport();
      const FIRST = 150, MORE = 400;
      const draw = (from, to) => rows.slice(from, to).map((row, i) => bodyRow(row, columns, state, from + i)).join("");
      const body = rows.length
        ? `<tbody>${draw(0, FIRST)}</tbody>`
        : `<tbody><tr><td class="table-empty" colspan="${columns.length + 1 + (numbered ? 1 : 0)}">Nothing matches these filters</td></tr></tbody>`;
      table.innerHTML = head + body;
      this.more?.disconnect();
      if (rows.length <= FIRST) return;
      let shown = FIRST;
      const tbody = table.querySelector("tbody");
      const watch = new IntersectionObserver((entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        tbody.insertAdjacentHTML("beforeend", draw(shown, shown + MORE));
        shown += MORE;
        watch.disconnect();
        if (shown < rows.length) watch.observe(tbody.lastElementChild);
      }, { rootMargin: "1200px 0px" });
      watch.observe(tbody.lastElementChild);
      this.more = watch;
    },

    bindTapNotes() {
      table.addEventListener("click", (event) => {
        if (!Pie.tapCard.isTouch() || event.target.closest("[data-result-key], thead")) return;
        const noted = event.target.closest("td[data-note], td[title], tr[title]");
        const note = noted?.dataset.note || noted?.title;
        if (note) Pie.tapCard.toggle(noted, format.escape(note));
      });
      const tooltip = document.getElementById("chart-tooltip");
      table.addEventListener("pointermove", (event) => {
        if (event.pointerType !== "mouse") return;
        const cell = event.target.closest("td[data-note]");
        if (!cell || cell.scrollWidth <= cell.clientWidth) {
          tooltip.hidden = true;
          return;
        }
        tooltip.textContent = cell.dataset.note;
        tooltip.classList.remove("is-card");
        tooltip.hidden = false;
        const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      });
      table.addEventListener("pointerleave", () => (tooltip.hidden = true));
      table.closest(".table-scroll, .table-wrap")?.addEventListener("scroll", () => (tooltip.hidden = true));
    },

    bindFlags() {
      let anchor = null;
      const mark = () => {
        for (const tr of table.querySelectorAll("tr[data-pick]")) {
          const on = picked.has(this.rows[Number(tr.dataset.pick)]);
          tr.classList.toggle("is-picked", on);
          tr.setAttribute("aria-selected", on);
        }
        syncReport();
      };
      table.addEventListener("mousedown", (event) => { if (event.shiftKey && event.target.closest("tr[data-pick]")) event.preventDefault(); });
      table.addEventListener("click", (event) => {
        const tr = event.target.closest("tr[data-pick]");
        if (!tr || event.target.closest("a, button, input")) return;
        const at = Number(tr.dataset.pick), key = this.rows[at];
        if (event.shiftKey && anchor !== null) {
          const [from, to] = anchor < at ? [anchor, at] : [at, anchor];
          if (!event.metaKey && !event.ctrlKey) picked.clear();
          for (let i = from; i <= to; i++) picked.add(this.rows[i]);
        } else if (event.metaKey || event.ctrlKey) {
          picked.has(key) ? picked.delete(key) : picked.add(key);
          anchor = at;
        } else {
          const only = picked.size === 1 && picked.has(key);
          picked.clear();
          if (!only) picked.add(key);
          anchor = at;
        }
        mark();
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && picked.size && !document.querySelector("dialog[open]")) { picked.clear(); anchor = null; mark(); }
      });
      downloadButton?.addEventListener("click", () => {
        const blob = new Blob([csvOf(this.rows, this.columns)], { type: "text/csv" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${this.source === "results" ? "performance" : this.source}.csv`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      });
      reportButton?.addEventListener("click", () => {
        const at = this.rows.flatMap((r, i) => (picked.has(r) ? [i] : []));
        if (at.length) Pie.reports?.flag(at.map((i) => this.rows[i]), this.source, () => { picked.clear(); anchor = null; mark(); }, at.map((i) => i + 1));
      });
    },

    keyOf,


    onShowResults(handler) {
      table.addEventListener("click", (event) => {
        const row = event.target.closest("[data-result-key]");
        if (row) handler(row.dataset.resultKey, row.dataset.resultValue);
      });
    },

    onSort(handler) {
      table.addEventListener("click", (event) => {
        if (event.target.closest(".column-info")) return;
        const header = event.target.closest("[data-sort]");
        if (header) handler(header.dataset.sort);
      });
    },
  };
})();
