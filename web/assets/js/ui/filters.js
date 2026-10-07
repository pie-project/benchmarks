window.Pie = window.Pie || {};

(() => {
  const list = document.getElementById("filter-list");
  const hideEmpty = document.getElementById("hide-empty");
  const chevron = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
  const cross = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2.5 2.5l5 5M7.5 2.5l-5 5"/></svg>';

  const plural = (column) => {
    if (column.label === "Hardware") return column.label;
    if (/[^aeiou]y$/.test(column.label)) return `${column.label.slice(0, -1)}ies`;
    if (/(s|x)$/.test(column.label)) return `${column.label}es`;
    return `${column.label}s`;
  };

  const plainName = (column, value) =>
    column.type === "reference" ? Pie.store.names.of(column.table, value) : value;

  // One pick shows its tag, two show both names, more show a count, like a macOS pop-up button.
  const summary = (column, values) => {
    if (values.length === 1) return Pie.format.option(column, values[0]);
    if (values.length === 2) return Pie.format.escape(values.map((value) => plainName(column, value)).join(", "));
    return `${values.length} ${Pie.format.escape(plural(column))}`;
  };

  const filter = (column, values) => {
    const set = values.length > 0;
    const label = set ? `${summary(column, values)}${chevron}` : `${column.label}${chevron}`;
    const title = set ? ` title="${Pie.format.escape(values.map((value) => plainName(column, value)).join(", "))}"` : "";
    const clear = set
      ? `<button class="filter-clear" type="button" data-clear="${column.key}" aria-label="Clear ${Pie.format.escape(column.label.toLowerCase())}">${cross}</button>`
      : "";
    return `
      <span class="filter${set ? " is-set" : ""}">
        <button class="filter-button" type="button" data-filter="${column.key}" aria-haspopup="menu"${title}>${label}</button>${clear}
      </span>`;
  };

  let onClear = () => {};

  Pie.filters = {
    hideEmpty,
    plural,

    render(state) {
      const schema = Pie.schema[state.table];
      list.innerHTML = schema.filters
        .map((key) => filter(schema.columns.find((column) => column.key === key), state.selected(key)))
        .join("");
      hideEmpty.classList.toggle("is-active", state.hideEmpty);
    },

    onOpen(handler) {
      list.addEventListener("click", (event) => {
        event.stopPropagation();
        const clear = event.target.closest("[data-clear]");
        if (clear) {
          onClear(clear.dataset.clear);
          return;
        }
        const button = event.target.closest("[data-filter]");
        if (button) handler(button, button.dataset.filter);
      });
    },

    onClear(handler) {
      onClear = handler;
    },
  };
})();
