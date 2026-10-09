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
    const classes = column.type === "number" ? "is-numeric" : "";
    return `<th class="${classes}" data-sort="${column.key}" title="${hint}">${column.label}${unit}${headerMeta(column, coverage)}${sort}</th>`;
  };

  const bodyCell = (column, row) => {
    const value = row[column.key];
    const classes = [
      column.type === "number" ? "is-numeric" : "",
      column.code && !format.isEmpty(value) ? "is-code" : "",
      format.isEmpty(value) ? "is-empty" : "",
    ].filter(Boolean).join(" ");
    return `<td class="${classes}">${format.value(column, value)}</td>`;
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
    const number = Pie.schema[state.table].numbered ? `<td class="row-number">${index + 1}</td>` : "";
    return `<tr class="${classes.join(" ")}"${link || stale}>${number}${cells}</tr>`;
  };

  Pie.table = {
    container,

    visibleColumns(state) {
      return Pie.schema[state.table].columns;
    },

    render(state, rows) {
      const columns = this.visibleColumns(state);
      const numbered = Pie.schema[state.table].numbered;
      const corner = numbered ? `<th class="row-number" aria-label="Row"></th>` : "";
      const head = `<thead><tr>${corner}${columns.map((column) => headerCell(column, state)).join("")}</tr></thead>`;
      const body = rows.length
        ? `<tbody>${rows.map((row, index) => bodyRow(row, columns, state, index)).join("")}</tbody>`
        : `<tbody><tr><td class="table-empty" colspan="${columns.length + (numbered ? 1 : 0)}">Nothing matches these filters</td></tr></tbody>`;
      table.innerHTML = head + body;
    },

    onShowResults(handler) {
      table.addEventListener("click", (event) => {
        const row = event.target.closest("[data-result-key]");
        if (row) handler(row.dataset.resultKey, row.dataset.resultValue);
      });
    },

    onSort(handler) {
      table.addEventListener("click", (event) => {
        const header = event.target.closest("[data-sort]");
        if (header) handler(header.dataset.sort);
      });
    },
  };
})();
