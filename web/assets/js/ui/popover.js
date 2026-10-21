window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("popover");
  const RELEASE = "release";
  const SUITE = "suite";
  const VIEW = "view";
  const METRIC = "metric";
  const COMPARE = "platform-compare";
  const MAC = "overview-mac";
  const WORKLOAD = "overview-workload";
  const ENGINE = "overview-engine";
  const HEAT_MAC = "overview-heat-mac";
  const MODEL = "overview-model";
  const STAND_MAC = "overview-stand-mac";
  const HIST_MAC = "overview-history-mac";
  const HIST_MODEL = "overview-history-model";
  const QUAL_ENGINE = "overview-quality-engine";
  const ALL = "";
  let owner = null;
  let anchor = null;  // the button the open menu belongs to: the menu stays attached to it while the page scrolls
  let onPick = () => {};

  const check = (selected) =>
    `<span class="popover-check">${selected ? '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6.4l2.4 2.4 4.6-5.3"/></svg>' : ""}</span>`;

  const option = (value, selected, label, role = "menuitemradio") => `
    <button class="popover-option" type="button" role="${role}" aria-checked="${selected}" data-value="${Pie.format.escape(value)}">
      ${check(selected)}${label}
    </button>`;

  const releaseMenu = (state) => {
    const options = Pie.query.releaseOptions();
    // releases first, manual runs under them
    const groups = [...new Set(options.map((release) => release.group))]
      .sort((a, b) => (/manual/i.test(a) ? 1 : 0) - (/manual/i.test(b) ? 1 : 0));
    return groups
      .map((group) =>
        `<div class="popover-heading">${group}</div>` +
        options
          .filter((release) => release.group === group)
          // the date sits right-aligned in grey, the way macOS menus show secondary text
          .map((release) => option(release.id, release.id === state.release,
            `<span class="popover-label">${Pie.format.escape(release.title)}</span>` +
            (release.date ? `<span class="popover-detail">${Pie.format.escape(release.date)}</span>` : "")))
          .join(""))
      .join(`<div class="popover-separator"></div>`) +
      // what the list leaves out, in a grey footnote under a separator, as a macOS menu explains itself
      `<div class="popover-separator"></div><p class="popover-note">Updated with each release.</p>`;
  };

  // a platform page's setup, when the window is too narrow for its sidebar: the sidebar's groups, a checkmark on the current one
  const metricMenu = (state) => {
    const setups = Pie.platform.metrics(state);
    return [...new Set(setups.map((m) => m.group))]
      // each phase under its heading, as the release menu groups its runs; the items then need only their own word
      .map((group) => `<div class="popover-heading">${Pie.format.escape(group)}</div>` + setups.filter((m) => m.group === group)
        .map((m) => option(m.id, m.id === state.platform.mode,
          // its symbol before its name, as a macOS menu sets an item's icon, and its key at the end where shortcuts sit
          `<svg class="popover-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="${m.icon}"/></svg><span class="popover-label">${Pie.format.escape(m.item || m.label)}</span><span class="popover-detail popover-key">${setups.indexOf(m) + 1}</span>`).replace('class="popover-option"', 'class="popover-option is-setup"'))
        .join(""))
      .join(`<div class="popover-separator"></div>`);
  };

  // a Limit setting: its options, a checkmark on the current one, like the other menus
  const isLimit = (key) => String(key).startsWith("limit:");
  const limitMenu = (key) => (Pie.methodology?.menu(String(key).slice(6)) || [])
    .map((o) => option(o.value, o.selected, `<span class="popover-label">${Pie.format.escape(o.label)}</span>`))
    .join("");

  // the view menu: Performance or Roofline, one pick with a checkmark; under a separator Hide Unavailable, checked while on,
  // as Finder's View menu keeps its show and hide items under the views
  const compareMenu = (state) => {
    const current = Pie.platform.compare();
    // holding R shows the other one: the key beside it, as a macOS menu shows a shortcut
    const key = '<span class="popover-detail popover-key">Hold R</span>';
    return option("engines", current === "engines", `<span class="popover-label">Performance</span>${current === "engines" ? "" : key}`) + option("ceiling", current === "ceiling", `<span class="popover-label">Roofline</span>${current === "ceiling" ? "" : key}`) +
      `<div class="popover-separator"></div>` + option("hide", state.hideEmpty, `<span class="popover-label">Hide Unavailable</span>`, "menuitemcheckbox");
  };

  // the suite: one pick, a checkmark on the current one, like the release menu
  const suiteMenu = (state) =>
    Pie.store.suites()
      .map((suite) => option(suite.id, suite.id === state.suite,
        `<span class="popover-label">${Pie.format.escape(suite.title)}</span>` +
        `<span class="popover-detail">${Pie.format.escape(suite.detail)}</span>`))
      .join("");

  // the compact toolbar's one picker: the release menu (the site shows the Full suite only)
  const viewMenu = (state) => {
    return `<div data-key="${RELEASE}">${releaseMenu(state)}</div>`;
  };

  // the overview's Mac: one pick, a checkmark on the current one, like the release menu
  const macMenu = (state, current = state.overview.hardware) =>
    Pie.overview.macs(state)
      .map((mac) => option(mac.id, mac.id === current,
        `<span class="popover-label">${Pie.format.escape(mac.label)}</span>`))
      .join("");

  // the overview's workload: the same menu as the Mac's
  const workloadMenu = (state) =>
    Pie.overview.workloads()
      .map((workload) => option(workload.id, workload.id === state.overview.workload,
        `<span class="popover-label">${Pie.format.escape(workload.label)}</span>`))
      .join("");

  // the overview's base engine: the one every other engine is measured against
  const engineMenu = (state) =>
    Pie.overview.engines(state)
      .map((engine) => option(engine.id, engine.id === state.overview.engine,
        `<span class="popover-label">${Pie.format.escape(engine.label)}</span>`))
      .join("");

  // the Across Macs section's model
  const modelMenu = (state) =>
    Pie.overview.models(state)
      .map((model) => option(model.id, model.id === state.overview.model,
        `<span class="popover-label">${Pie.format.escape(model.label)}</span>`))
      .join("");

  // the release history's model: one model, or all of them together
  const historyModelMenu = (state) =>
    option("", !state.overview.historyModel, `<span class="popover-label">All models</span>`) + `<div class="popover-separator"></div>` +
    Pie.overview.models(state)
      .map((model) => option(model.id, model.id === state.overview.historyModel,
        `<span class="popover-label">${Pie.format.escape(model.label)}</span>`))
      .join("");

  // the Quality section's engine, marked over the average
  const qualityEngineMenu = (state) =>
    Pie.overview.qualityEngines(state)
      .map((engine) => option(engine.id, engine.id === (state.overview.qualityEngine || state.overview.engine),
        `<span class="popover-label">${Pie.format.escape(engine.label)}</span>`))
      .join("");

  // A macOS pull-down with a checkmark per picked value: clicking toggles and the menu stays open.
  const filterMenu = (state, key) => {
    const column = Pie.schema[state.table].columns.find((entry) => entry.key === key);
    const current = state.selected(key);
    const entries = Pie.query.filterValues(state.table, key);
    const values = entries
      .map((entry) => option(entry.value, current.includes(entry.value), Pie.format.option(column, entry.value), "menuitemcheckbox"))
      .join("");
    return `${option(ALL, !current.length, `All ${Pie.filters.plural(column).toLowerCase()}`)}<div class="popover-separator"></div>${values}`;
  };

  const place = (target) => {
    const box = target.getBoundingClientRect();
    element.hidden = false;
    element.style.left = `${Math.max(8, Math.min(box.left, window.innerWidth - element.offsetWidth - 8))}px`;
    element.style.top = `${box.bottom + 6}px`;
    // on a phone the menu stops above the bottom of the screen and scrolls inside
    element.style.maxHeight = Pie.preferences.compact.matches ? `min(480px, ${Math.max(160, window.innerHeight - box.bottom - 18)}px)` : "";
  };

  // keep an open menu attached to its button when the window resizes
  const follow = () => {
    if (anchor && !element.hidden) place(anchor);
  };
  // scrolling the page closes an open menu, as macOS menus do; scrolling inside the menu itself does not
  window.addEventListener("scroll", (event) => {
    if (element.hidden || element.contains(event.target)) return;
    Pie.popover.close();
  }, { capture: true, passive: true });
  window.addEventListener("resize", follow);

  Pie.popover = {
    RELEASE,
    SUITE,
    VIEW,
    METRIC,
    COMPARE,
    MAC,
    WORKLOAD,
    ENGINE,
    HEAT_MAC,
    MODEL,
    STAND_MAC,
    HIST_MAC,
    HIST_MODEL,
    QUAL_ENGINE,
    ALL,

    isOpen() {
      return !element.hidden;
    },

    isOpenFor(key) {
      return owner === key && !element.hidden;
    },

    open(target, key, state) {
      if (this.isOpenFor(key)) {
        this.close();
        return;
      }
      owner = key;
      anchor = target;
      element.innerHTML = isLimit(key) ? limitMenu(key) : key === RELEASE ? releaseMenu(state) : key === VIEW ? viewMenu(state) : key === SUITE ? suiteMenu(state) : key === COMPARE ? compareMenu(state) : key === METRIC ? metricMenu(state) : key === MAC ? macMenu(state) : key === WORKLOAD ? workloadMenu(state) : key === ENGINE ? engineMenu(state) : key === HEAT_MAC ? macMenu(state, state.overview.heatMac) : key === STAND_MAC ? macMenu(state, state.overview.standMac) : key === HIST_MAC ? macMenu(state, state.overview.historyMac) : key === HIST_MODEL ? historyModelMenu(state) : key === QUAL_ENGINE ? qualityEngineMenu(state) : key === MODEL ? modelMenu(state) : filterMenu(state, key);
      element.scrollTop = 0;
      place(target);
    },

    // Redraw the open filter menu in place after a toggle, keeping its scroll position.
    refresh(state) {
      if (element.hidden || !owner || isLimit(owner) || owner === RELEASE || owner === SUITE || owner === VIEW || owner === METRIC || owner === MAC || owner === WORKLOAD || owner === ENGINE || owner === HEAT_MAC || owner === MODEL || owner === STAND_MAC || owner === HIST_MAC || owner === HIST_MODEL || owner === QUAL_ENGINE) return;
      const scroll = element.scrollTop;
      element.innerHTML = filterMenu(state, owner);
      element.scrollTop = scroll;
    },

    close() {
      element.hidden = true;
      owner = null;
      anchor = null;
    },

    onPick(handler) {
      onPick = handler;
    },

    bind() {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        const target = event.target.closest("[data-value]");
        if (!target || target.disabled) return;
        const key = target.closest("[data-key]")?.dataset.key || owner;
        if (isLimit(key) || key === RELEASE || key === SUITE || key === METRIC || key === COMPARE || key === MAC || key === WORKLOAD || key === ENGINE || key === HEAT_MAC || key === MODEL || key === STAND_MAC || key === HIST_MAC || key === HIST_MODEL || key === QUAL_ENGINE) this.close();
        onPick(key, target.dataset.value);
      });
    },
  };
})();
