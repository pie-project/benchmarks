window.Pie = window.Pie || {};

// Engine Gaps: the cells where pie is 25% or more faster than the strongest other engine (the grid's yellow and green
// cells), each run with its own date and a maintainer's note: why the gap is real, or that the cell needs a rerun
(() => {
  const element = document.getElementById("gaps");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const tag = Pie.format;
  // how far apart the engines must sit to be listed, as a share of the theoretical maximum: picked in the bar, kept per browser
  const LEASTS = [0.25, 0.5, 0.75];
  let least = (() => { try { const v = Number(localStorage.getItem("pieGapsLeast")); return LEASTS.includes(v) ? v : 0.25; } catch { return 0.25; } })();
  // a yellow cell on the grid opens this view on its own row: machine, model and setup, whatever the Gap pick
  let focus = null;
  // the Conclusion pick: every row, or only those with one conclusion (Needs Rerun, Explained, ...), kept per browser
  const CONCLUSION = { explained: "Explained", real: "Real Gap", rerun: "Needs Rerun", study: "Needs Study" };
  let only = (() => { try { const v = localStorage.getItem("pieGapsConclusion"); return CONCLUSION[v] ? v : ""; } catch { return ""; } })();
  const every = () => Pie.platform?.gaps?.(Pie.state) || [];
  const atLeast = (list, share) => list.filter((g) => Math.round(Math.abs(g.gap) * 100) >= Math.round(share * 100));
  const gaps = () => {
    try {
      if (focus) return every().filter((g) => g.hardware === focus.hardware && g.model === focus.model && g.setup === focus.setup);
      const all = atLeast(every(), least);
      return only ? all.filter((g) => noteOf(g)[0] === only) : all;
    } catch { return []; }
  };
  const nameOf = (table, id) => {
    const row = (Pie.store.rows(table) || []).find((r) => r.id === id);
    return row?.name || row?.label || id;
  };
  const day = (t) => new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const dataDay = () => { const at = Pie.store.tables.updated_at; return at ? day(at) : ""; };
  const speed = (v) => `${Math.round(v).toLocaleString("en-US")} tok/s`;
  const share = (v) => `${Math.round(v * 100)}%`;

  const when = (t) => (t ? day(String(t).replace(" ", "T")) : dataDay());
  const pct = (g) => `${g.gap > 0 ? "+" : "−"}${Math.round(Math.abs(g.gap) * 100)}%`;
  const TRACED = ["explained", "real", "rerun"];
  const shape = (benchmark) => String(benchmark || "").replace(/^(raw|spec)-/, "");
  const ran = (r) => [r.miniature && `a ${r.miniature} slice`, r.benchmark].filter(Boolean).join(", ") || "another setup";
  const noteOf = (g) => {
    const note = (Pie.gapNotes || {})[`${g.hardware}|${g.model}|${g.setup}`];
    if (note && TRACED.includes(note[0])) return note;
    const rival = nameOf("engines", g.rival);
    if (g.overLimit) return ["rerun", "Above the hardware limit", "A number on this cell is above the machine's theoretical limit, which no run can reach."];
    if ((g.pieRun.benchmark && g.rivalRun.benchmark && shape(g.pieRun.benchmark) !== shape(g.rivalRun.benchmark)) || g.pieRun.miniature !== g.rivalRun.miniature) {
      return ["rerun", "Runs not comparable", `Pie ran ${ran(g.pieRun)} and ${rival} ran ${ran(g.rivalRun)}. Rerun both on the same setup.`];
    }
    if (g.pieNoisy || g.rivalNoisy) return ["rerun", "Noisy run", `${g.pieNoisy ? "Pie's" : `${rival}'s`} repeated runs disagree, so its number is not reliable yet.`];
    if (g.pieRun.workload === "raw" && g.rivalRun.workload === "raw" && g.setup === "decode" && (g.gap >= 1 || g.gap <= -0.5)) {
      return ["rerun", "Over 2x on Single Decode", "On one request both engines read the same weights for every token, so one engine more than twice as fast as the other points to a broken run."];
    }
    const spec = g.pieRun.workload === g.rivalRun.workload ? "" : g.pieRun.workload === "spec" ? ` Pie's number speculates and ${rival}'s does not.` : ` ${rival}'s number speculates and Pie's does not.`;
    return ["study", "Needs study", `No traced cause yet: profile Pie and ${rival} on this machine and model.${spec}`];
  };
  const conclusion = (k) => (k ? `<span class="gaps-tag is-${esc(k)}">${esc(CONCLUSION[k] || k)}</span>` : "");
  const row = (g, i) => `
    <tr data-pick>
      <td class="row-number">${i + 1}</td>
      <td>${esc(nameOf("models", g.model))}${g.miniature ? ` <span class="reports-none">(slice)</span>` : ""}</td>
      <td>${tag.hardwareTag(g.hardware)}</td>
      <td><span class="workload-tag">${Pie.platform.degree(g.setup)}${esc(g.label)}</span></td>
      <td class="is-numeric">${g.miniature ? "–" : esc(speed(g.pieValue))}${g.pieNoisy ? ` <span class="reports-none">noisy</span>` : ""}</td>
      <td>${esc(when(g.pieAt))}</td>
      <td>${tag.engineTag(g.rival, nameOf("engines", g.rival))}</td>
      <td class="is-numeric">${g.miniature ? "–" : esc(speed(g.rivalValue))}${g.rivalNoisy ? ` <span class="reports-none">noisy</span>` : ""}</td>
      <td>${esc(when(g.rivalAt))}</td>
      <td class="is-numeric ${g.gap > 0 ? "is-positive" : "is-negative"}">${pct(g)}</td>
      <td class="is-numeric">${g.engines}</td>
      <td class="gaps-note"${noteOf(g)[2] ? ` data-tip="${esc(noteOf(g)[2])}" data-tip-kind="${esc(noteOf(g)[0])}" data-tip-vs="${esc(`Pie vs ${nameOf("engines", g.rival)}`)}" data-tip-gap="${esc(pct(g))}" data-tip-at="${esc(`Note as of ${nameOf("engines", g.rival)}'s run, ${when(g.rivalAt)}`)}"` : ""}>${esc(noteOf(g)[1])}</td>
      <td class="gaps-end">${conclusion(noteOf(g)[0])}</td>
    </tr>`;

  const draw = () => {
    if (element.hidden) return;
    const list = gaps();
    element.innerHTML = `
      <div class="reports-table-wrap">
        <table class="data-table reports-table">
          <thead><tr><th class="row-number" aria-label="Row"></th><th>Model</th><th>Hardware</th><th>Workload</th><th class="is-numeric">Pie</th><th>Measured</th><th>Strongest Other</th><th class="is-numeric">Speed</th><th>Measured</th><th class="is-numeric">Pie vs Other</th><th class="is-numeric">Engines</th><th class="gaps-note">Note</th><th class="gaps-end">Conclusion</th></tr></thead>
          <tbody>${list.length ? list.map(row).join("") : `<tr><td class="table-empty" colspan="12">No reports yet</td></tr>`}</tbody>
        </table>
      </div>`;
  };

  Pie.pickRows(element);
  // a note's detail follows the pointer in the site's chart tooltip, as a narrow note (as on the Checks page)
  const tooltip = document.getElementById("chart-tooltip");
  element.addEventListener("mousemove", (event) => {
    // anywhere on the row, not only over its note
    const target = event.target.closest("tbody tr")?.querySelector("td.gaps-note[data-tip]");
    if (!target || !tooltip) { if (tooltip) { tooltip.hidden = true; tooltip.classList.remove("is-note", "is-gap-note"); } return; }
    // a popover's two levels: the two engines compared, their gap and the conclusion as its title, the reasoning under it
    tooltip.innerHTML = `<div class="gap-tip-title"><span>${esc(target.dataset.tipVs)}</span><span class="gap-tip-gap">${esc(target.dataset.tipGap)}</span><span class="gap-tip-end">${conclusion(target.dataset.tipKind)}</span></div><div class="gap-tip-body">${esc(target.dataset.tip)}</div><div class="gap-tip-at">${esc(target.dataset.tipAt)}</div>`;
    tooltip.classList.remove("is-card"); tooltip.classList.add("is-note", "is-gap-note");
    tooltip.hidden = false;
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  });
  element.addEventListener("mouseleave", () => { if (tooltip) { tooltip.hidden = true; tooltip.classList.remove("is-gap-note"); } });
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-gaps-all]")) { focus = null; event.stopPropagation(); document.querySelector('.sidebar-item[data-table="gaps"]')?.click(); return; }
    if (event.target.closest('.sidebar-item[data-table="gaps"]')) focus = null;
  }, true);
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-gaps-pick]");
    if (!button) return;
    event.stopPropagation();
    Pie.popover.open(button, `gaps:${button.dataset.gapsPick}`, null);
  }, true);

  Pie.gaps = {
    element,
    count: () => gaps().length,
    // how many rows the table holds, said under the window's title
    shown: () => { const n = gaps().length; return `${n.toLocaleString("en-US")} ${n === 1 ? "row" : "rows"}`; },
    // the bar's Gap pick, named as CI Reports names its Type, the share picked ticked in its menu
    bar: () => (focus
      ? `<span class="filter"><button class="filter-button" type="button" data-gaps-all>Show All Gaps</button></span>`
      : `<span class="filter"><button class="filter-button" type="button" data-gaps-pick="least" aria-haspopup="menu">Min Gap<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`
        + `<span class="filter"><button class="filter-button" type="button" data-gaps-pick="conclusion" aria-haspopup="menu">Conclusion<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`),
    // set by the grid before it opens this view on one cell; cleared by Show All Gaps or the sidebar
    focus(cell) { focus = cell || null; },
    menu: (k) => {
      if (k === "least") return LEASTS.map((v) => ({ value: String(v), label: `${Math.round(v * 100)}%`, selected: v === least }));
      if (k !== "conclusion") return [];
      // each conclusion with how many rows at the picked Min Gap carry it
      const all = atLeast(every(), least);
      const n = (c) => all.filter((g) => noteOf(g)[0] === c).length;
      return [{ value: "all", label: `All (${all.length})`, selected: !only },
        ...Object.entries(CONCLUSION).map(([c, label]) => ({ value: c, label: `${label} (${n(c)})`, selected: only === c }))];
    },
    pick(k, value) {
      if (k === "conclusion") {
        only = CONCLUSION[value] ? value : "";
        try { localStorage.setItem("pieGapsConclusion", only); } catch { /* private windows can refuse storage */ }
        draw();
        return;
      }
      if (k !== "least" || !LEASTS.includes(Number(value))) return;
      least = Number(value);
      try { localStorage.setItem("pieGapsLeast", value); } catch { /* private windows can refuse storage */ }
      draw();
      document.querySelector('.sidebar-item[data-table="gaps"] .sidebar-count')?.replaceChildren(String(gaps().length));
    },
    render(state) {
      element.hidden = state.table !== "gaps";
      draw();
    },
  };
})();
