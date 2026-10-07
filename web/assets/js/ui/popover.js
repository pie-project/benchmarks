window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("popover");
  const RELEASE = "release";
  const ALL = "";
  const EVERY = "__every__";
  let owner = null;
  let onPick = () => {};

  const check = (selected) =>
    `<span class="popover-check">${selected ? '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6.4l2.4 2.4 4.6-5.3"/></svg>' : ""}</span>`;

  const option = (value, selected, label, role = "menuitemradio") => `
    <button class="popover-option" type="button" role="${role}" aria-checked="${selected}" data-value="${Pie.format.escape(value)}">
      ${check(selected)}${label}
    </button>`;

  const action = (value, label, disabled) => `
    <button class="popover-action" type="button" data-value="${value}"${disabled ? " disabled" : ""}>${label}</button>`;

  const releaseMenu = (state) =>
    `<div class="popover-heading">pie release</div>` +
    Pie.query.releaseOptions()
      .map((release) => option(release.id, release.id === state.release, Pie.format.escape(release.title)))
      .join("");

  // A macOS pull-down with a checkmark per picked value: clicking toggles and the menu stays open.
  const filterMenu = (state, key) => {
    const column = Pie.schema[state.table].columns.find((entry) => entry.key === key);
    const current = state.selected(key);
    const entries = Pie.query.filterValues(state.table, key);
    const values = entries
      .map((entry) => option(entry.value, current.includes(entry.value), Pie.format.option(column, entry.value), "menuitemcheckbox"))
      .join("");
    const actions = `<div class="popover-actions">${action(EVERY, "Select All", current.length === entries.length)}${action(ALL, "Clear", !current.length)}</div>`;
    return `${option(ALL, !current.length, `All ${Pie.filters.plural(column).toLowerCase()}`)}<div class="popover-separator"></div>${values}<div class="popover-separator"></div>${actions}`;
  };

  const place = (anchor) => {
    const box = anchor.getBoundingClientRect();
    element.hidden = false;
    element.style.left = `${Math.max(8, Math.min(box.left, window.innerWidth - element.offsetWidth - 8))}px`;
    element.style.top = `${box.bottom + 6}px`;
  };

  Pie.popover = {
    RELEASE,
    ALL,
    EVERY,

    isOpenFor(key) {
      return owner === key && !element.hidden;
    },

    open(anchor, key, state) {
      if (this.isOpenFor(key)) {
        this.close();
        return;
      }
      owner = key;
      element.innerHTML = key === RELEASE ? releaseMenu(state) : filterMenu(state, key);
      element.scrollTop = 0;
      place(anchor);
    },

    // Redraw the open filter menu in place after a toggle, keeping its scroll position.
    refresh(state) {
      if (element.hidden || !owner || owner === RELEASE) return;
      const scroll = element.scrollTop;
      element.innerHTML = filterMenu(state, owner);
      element.scrollTop = scroll;
    },

    close() {
      element.hidden = true;
      owner = null;
    },

    onPick(handler) {
      onPick = handler;
    },

    bind() {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        const target = event.target.closest("[data-value]");
        if (!target || target.disabled) return;
        const key = owner;
        if (key === RELEASE) this.close();
        onPick(key, target.dataset.value);
      });
    },
  };
})();
