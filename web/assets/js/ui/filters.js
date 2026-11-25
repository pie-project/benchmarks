window.Pie = window.Pie || {};

(() => {
  const list = document.getElementById("filter-list");
  const chevron = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';

  const plural = (column) => {
    if (column.label === "Hardware") return column.label;
    if (/[^aeiou]y$/.test(column.label)) return `${column.label.slice(0, -1)}ies`;
    if (/(s|x)$/.test(column.label)) return `${column.label}es`;
    return `${column.label}s`;
  };

  const plainName = (column, value) =>
    column.type === "reference" ? Pie.store.names.of(column.table, value) : value;

  const summary = (column, values) => {
    if (values.length === 1) return Pie.format.option(column, values[0]);
    if (values.length === 2) return Pie.format.escape(values.map((value) => plainName(column, value)).join(", "));
    return `${values.length} ${Pie.format.escape(plural(column))}`;
  };

  const filter = (column, values) => {
    const set = values.length > 0;
    const label = set ? `${summary(column, values)}${chevron}` : `${column.label}${chevron}`;
    const title = set ? ` title="${Pie.format.escape(values.map((value) => plainName(column, value)).join(", "))}"` : "";
    return `
      <span class="filter${set ? " is-set" : ""}">
        <button class="filter-button" type="button" data-filter="${column.key}" aria-haspopup="menu"${title}>${label}</button>
      </span>`;
  };

  let shown = null;
  Pie.filters = {
    plural,

    render(state) {
      const schema = Pie.schema[state.table];
      list.innerHTML = schema.filters
        .map((key) => filter(schema.columns.find((column) => column.key === key), state.selected(key)))
        .join("")
        + (["results", "quality"].includes(state.table) && Pie.dates ? Pie.dates.button() : "")
        + (Object.keys(state.filters).length || (["results", "quality"].includes(state.table) && Pie.dates?.active()) ? `<button class="filter-clear" type="button" data-filter-clear><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg><span>Clear</span></button>` : "");
      shown = state;
    },

    onClear(handler) { this.cleared = handler; },

    onOpen(handler) {
      list.addEventListener("click", (event) => {
        event.stopPropagation();
        if (event.target.closest("[data-filter-clear]")) { Pie.popover?.close(); Pie.dates?.close(); Pie.dates?.clear(); this.cleared?.(); return; }
        const dates = event.target.closest("[data-dates]");
        if (dates) { Pie.popover?.close(); Pie.dates.open(dates, shown); return; }
        const button = event.target.closest("[data-filter]");
        if (button) handler(button, button.dataset.filter);
      });
    },
  };
})();
