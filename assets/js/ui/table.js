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
    // an (i) beside the label opens a note on how the column is measured, as macOS shows help for a setting
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
    // a long note stops at an ellipsis; hovering the cell shows all of it in the site's hover card
    const full = column.wide && !format.isEmpty(value) ? ` data-note="${format.escape(String(value))}"` : "";
    // a category reads as Apple's tables write one: plain text, a small coloured dot before it (no filled pills)
    const TINT = { mac: "#8e8e93", gpu: "#76b900", tpu: "#4285f4", wafer: "#ff9500" };
    const LABEL = { mac: "Mac", gpu: "GPU", tpu: "TPU", wafer: "Wafer" };
    const dotted = (key, text) => `<span class="cell-dot" style="--dot: ${TINT[key] || "#8e8e93"}">${format.escape(text)}</span>`;
    if (column.key === "class" && !format.isEmpty(value)) {
      const key = String(value).toLowerCase();
      return `<td class="${classes}">${dotted(key, LABEL[key] || String(value))}</td>`;
    }
    // a machine's platform as the Platforms table shows it: the platform's sidebar mark before its name
    const platform = column.key === "platform" && Object.entries(Pie.schema).find(([, s]) => s.view === "platform" && s.short === value);
    if (platform) {
      const [id, s] = platform;
      return `<td class="${classes}"><span class="welcome-cell"><span class="sidebar-glyph" style="--tint: ${s.tint}">${Pie.icon(id)}</span>${format.escape(value)}</span></td>`;
    }
    // an engine's name after its logo in the Engines catalog, as the charts mark it, on the white tile a model's maker sits
    // on in the Models catalog; one without a logo keeps its colour chip
    if (column.type === "reference" && column.table === "engines" && column.key === "id" && !format.isEmpty(value)) {
      const logo = Pie.engines.logo?.(value);
      if (logo) return `<td class="${classes}"><span class="engine-tag is-logo"><span class="model-badge" aria-hidden="true">${logo}</span>${format.escape(Pie.store.names.engine(value))}</span></td>`;
    }
    // a model's name after its maker's logo, as the grids head their columns
    if (column.key === "name" && "base_model" in row && Pie.platform?.makerBadge) {
      return `<td class="${classes}"><span class="model-name-cell">${Pie.platform.makerBadge(row.id)}<span>${format.escape(value)}</span></span></td>`;
    }
    if (column.key === "platforms" && (!format.isEmpty(value) || row.fits)) {
      // each platform as its sidebar tile alone, its name on hover, as Finder's Tags column shows colour, not words;
      // every platform keeps its own slot down the column, empty where a model was not measured there, so a platform's
      // tiles stand in one line and the eye runs down it
      const ID = { mac: "mac", gpu: "nvidia", tpu: "tpu", amd: "amd", wafer: "cerebras" };
      // a model not yet measured shows where it would fit, its tiles faded
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

  // the platform slots of the Platforms column: every platform any model was measured on, Mac, NVIDIA, TPU, AMD, Cerebras
  let slotsOf = null;
  const platformSlots = () => slotsOf ||= ["mac", "gpu", "tpu", "amd", "wafer"]
    .filter((t) => (Pie.store.tables.models || []).some((m) => String(m.platforms || "").toLowerCase().split(", ").includes(t)));

  // Performance and Quality rows are selected as a Mac list's are (click, ⌘-click, ⇧-click), and the bar's Report files
  // the selected ones as wrong
  const flaggable = (state) => state.table === "results" || state.table === "quality";  // Report opens a GitHub issue: no account
  const picked = new Set();  // the selected rows themselves, not a key: two rows alike in every column shown are still two
  // a measurement has no id of its own: a report names it by every field it has, so no other row reads the same
  const keyOf = (row) => Object.keys(row).sort().filter((k) => row[k] == null || typeof row[k] !== "object").map((k) => `${k}=${row[k] ?? ""}`).join("|");
  let pickedOn = null;       // the table they were picked on: another page starts with none
  const reportButton = document.getElementById("report-selected");
  const downloadButton = document.getElementById("download-rows");  // the rows the filters show, every column, as a CSV file
  // a CSV of the rows, every column the page has (hidden ones too), in the table's order: the raw values, not as drawn
  const csvOf = (rows, columns) => {
    const cell = (v) => { const t = v == null ? "" : String(v); return /[",\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
    return [columns.map((c) => cell(c.label)).join(","), ...rows.map((r) => columns.map((c) => cell(r[c.key])).join(","))].join("\n");
  };
  // the bar's Report keeps its one label, enabled while rows are selected; how many are selected is said in the
  // window's subtitle, as Finder says "3 of 40 selected" under its title
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
    // highlight the rows measured under the selected tag; filled-in rows from an older run stay plain
    if ((state.table === "results" || state.table === "quality") && !row.stale && store.isMeasured(row)) classes.push("is-highlighted");
    // a listed setup with no numbers stays in the table, in quiet grey
    if (state.table === "results" && !store.isMeasured(row)) classes.push("is-unmeasured");
    // a measurement above its theoretical limit, as CI Reports lists it: the row tinted red
    if (state.table === "results" && !row.miniature && overLimit().has(`${row.engine}|${row.hardware}|${row.model}|${OVER_SETUP[row.workload]}`)) classes.push("is-over-limit");
    // pie 25% or more ahead of its strongest competitor on the same machine, model and workload: the row tinted yellow
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

  // CI Reports' Exceeds Theoretical Limit cells, by engine, machine, model and setup, worked out once a data load
  const OVER_SETUP = { raw_decode: "decode", raw_prefill: "prefill", throughput: "batching", prefill_batch: "pbatch" };
  let overFor = null, overKeys = new Set();
  const overLimit = () => {
    if (overFor !== Pie.store.tables) {
      overFor = Pie.store.tables;
      try { overKeys = new Set((Pie.board?.outliers?.() || []).map((o) => `${o.engine}|${o.hardware}|${o.model}|${o.setup}`)); } catch { overKeys = new Set(); }
    }
    return overKeys;
  };

  // the best number each machine, model and workload has, by engine, worked out once a data load: a pie row 25% or more
  // ahead of the strongest other engine on its setup is tinted yellow
  const GAP_KEY = { raw_decode: "decode_tok_s", raw_prefill: "prefill_tok_s", throughput: "output_tok_s", prefill_batch: "prefill_tok_s" };
  let behindFor = null, bestBy = new Map();
  Pie.behind = (row) => {
    const key = GAP_KEY[row.workload];
    if (!key || !row[key]) return false;
    if (behindFor !== Pie.store.tables) {
      behindFor = Pie.store.tables;
      bestBy = new Map();
      for (const r of Pie.store.rows("results") || []) {
        const k = GAP_KEY[r.workload];
        if (!k || !r[k] || !Pie.store.isMeasured(r)) continue;
        const at = `${r.hardware}|${r.model}|${r.workload}`;
        const by = bestBy.get(at) || new Map();
        by.set(r.engine, Math.max(by.get(r.engine) || 0, r[k]));
        bestBy.set(at, by);
      }
    }
    const by = bestBy.get(`${row.hardware}|${row.model}|${row.workload}`);
    if (!by) return false;
    const rival = Math.max(0, ...[...by].filter(([e]) => e !== row.engine).map(([, v]) => v));
    return row.engine === "pie" && rival > 0 && row[key] / rival - 1 >= 0.25;
  };

  Pie.table = {
    container,

    // a catalog table keeps its columns at their width on the left; an empty column takes the rest, before Results
    // so that count stays at the right edge
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
      // a selected row the filters now hide is no longer selected, as Finder drops what a search hides
      if (picked.size) { const shown = new Set(rows); for (const r of picked) if (!shown.has(r)) picked.delete(r); }
      const head = `<thead><tr>${corner}${this.fill(columns.map((column) => headerCell(column, state)).join(""), columns, state, "th")}</tr></thead>`;
      this.rows = rows;
      this.source = state.table;
      if (reportButton) reportButton.hidden = !flaggable(state);
      if (downloadButton) downloadButton.hidden = !flaggable(state);
      // the row colours' keys, with the measurement tables only; CI Error tints Performance's rows alone
      const keys = document.getElementById("table-keys");
      if (keys) keys.hidden = !flaggable(state);
      const errorKey = document.getElementById("table-key-error");
      if (errorKey) errorKey.hidden = state.table !== "results";
      this.columns = Pie.schema[state.table].columns.filter((c) => c.key && !c.key.startsWith("_"));
      base = flaggable(state) ? subtitle?.textContent || "" : "";  // the page's own subtitle, just written, before the selection is added
      syncReport();
      // the first rows at once, the rest as the list scrolls toward them: thousands of rows drawn up front made every
      // sort and filter wait on the page's layout
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

    // a finger cannot hover a cell's note: a tap on a noted cell or row shows it instead
    bindTapNotes() {
      table.addEventListener("click", (event) => {
        if (!Pie.tapCard.isTouch() || event.target.closest("[data-result-key], thead")) return;
        const noted = event.target.closest("td[data-note], td[title], tr[title]");
        const note = noted?.dataset.note || noted?.title;
        if (note) Pie.tapCard.toggle(noted, format.escape(note));
      });
      // with a pointer, a note cut off at its ellipsis shows whole in the hover card as soon as the pointer is on it
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

    // a click selects a row alone (a second click on the only one selected clears it), ⌘-click adds or drops one, and
    // ⇧-click selects the run from the last one clicked; Escape clears. The bar's Report opens the sheet for them
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
      // ⇧-click would select the page's text instead of the rows
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
        const at = this.rows.flatMap((r, i) => (picked.has(r) ? [i] : []));  // in the table's order, with its row numbers
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
