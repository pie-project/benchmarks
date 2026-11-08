window.Pie = window.Pie || {};

// Engine Gaps: the cells where the same run on different engines lands far apart, the fastest and slowest at least
// half the theoretical maximum apart, worked out from the live data (Pie.board.gaps) and listed as CI Reports lists its rows, widest gap first
(() => {
  const element = document.getElementById("gaps");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const tag = Pie.format;
  // how far apart the engines must sit to be listed, as a share of the theoretical maximum: picked in the bar, kept per browser
  const LEASTS = [0.25, 0.5, 0.75];
  let least = (() => { try { const v = Number(localStorage.getItem("pieGapsLeast")); return LEASTS.includes(v) ? v : 0.75; } catch { return 0.75; } })();
  const gaps = () => { try { return Pie.board?.gaps?.(least) || []; } catch { return []; } };
  const nameOf = (table, id) => {
    const row = (Pie.store.rows(table) || []).find((r) => r.id === id);
    return row?.name || row?.label || id;
  };
  const day = (t) => new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const dataDay = () => { const at = Pie.store.tables.updated_at; return at ? day(at) : ""; };
  const speed = (v) => `${Math.round(v).toLocaleString("en-US")} tok/s`;
  const share = (v) => `${Math.round(v * 100)}%`;

  const row = (g, i) => `
    <tr data-pick>
      <td class="row-number">${i + 1}</td>
      <td>${esc(nameOf("models", g.model))}${g.miniature ? ` <span class="reports-none">(slice)</span>` : ""}</td>
      <td>${tag.hardwareTag(g.hardware)}</td>
      <td><span class="workload-tag">${Pie.platform.degree(g.setup)}${esc(g.label)}</span></td>
      <td>${tag.engineTag(g.fast, nameOf("engines", g.fast))}</td>
      <td class="is-numeric">${esc(speed(g.fastValue))} <span class="reports-none">${share(g.fastValue / g.limit)}</span></td>
      <td>${tag.engineTag(g.slow, nameOf("engines", g.slow))}</td>
      <td class="is-numeric">${esc(speed(g.slowValue))} <span class="reports-none">${share(g.slowValue / g.limit)}</span></td>
      <td class="is-numeric">${share(g.spread)} of max</td>
      <td class="is-numeric">${g.engines}</td>
      <td>${esc(g.measured ? day(String(g.measured).replace(" ", "T")) : dataDay())}</td>
      <td class="reports-fix-cell"></td>
    </tr>`;

  const draw = () => {
    if (element.hidden) return;
    const list = gaps();
    element.innerHTML = `
      <div class="reports-table-wrap">
        <table class="data-table reports-table">
          <thead><tr><th class="row-number" aria-label="Row"></th><th>Model</th><th>Hardware</th><th>Workload</th><th>Fastest</th><th class="is-numeric">Speed</th><th>Slowest</th><th class="is-numeric">Speed</th><th class="is-numeric">Gap</th><th class="is-numeric">Engines</th><th>Date</th><th></th></tr></thead>
          <tbody>${list.length ? list.map(row).join("") : `<tr><td class="table-empty" colspan="12">No gaps of ${Math.round(least * 100)}% or more</td></tr>`}</tbody>
        </table>
      </div>`;
  };

  Pie.pickRows(element);
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
    bar: () => `<span class="filter"><button class="filter-button" type="button" data-gaps-pick="least" aria-haspopup="menu">Gap<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`,
    menu: (k) => (k === "least" ? LEASTS.map((v) => ({ value: String(v), label: `${Math.round(v * 100)}%`, selected: v === least })) : []),
    pick(k, value) {
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
