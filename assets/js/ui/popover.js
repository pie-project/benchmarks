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
          `<svg class="popover-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="${m.icon}"/></svg><span class="popover-label">${Pie.format.escape(m.item || m.label)}</span>${m.id === "spec" ? "" : `<span class="popover-detail popover-key">${Pie.platform.metrics().filter((x) => x.id !== "spec").indexOf(m) + 1}</span>`}`).replace('class="popover-option"', 'class="popover-option is-setup"'))
        .join(""))
      .join(`<div class="popover-separator"></div>`);
  };

  // a Limit setting: its options, a checkmark on the current one, like the other menus
  // a page's own menus by prefix: limit: for the Limit page, board: for the Leaderboard
  const COMPACT = new Set(["board:size", "board:moe", "board:metric", "board:use-engine", "board:scale-engine"]);
  // a long list opens with a field over it that narrows it as one types, as Artificial Analysis sets its model menus
  const SEARCHABLE = new Set(["board:model", "board:scale"]);
  // any list longer than a few rows takes the search field too: a model, machine or engine list, wherever it opens
  const SEARCH_FROM = 9;
  // the open menu's list, under a search field when it is long: the field stays put over it and only the list scrolls.
  // A redraw (a toggle in a filter or the Models pick) keeps what was typed and where the list was scrolled
  const searchWrap = (key, query = "", scroll = 0) => {
    const searchable = SEARCHABLE.has(key) || element.querySelectorAll(".popover-option").length >= SEARCH_FROM;
    element.classList.toggle("is-searchable", searchable);
    if (!searchable) return;
    element.innerHTML = `<label class="popover-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input type="text" placeholder="Search…" autocomplete="off" spellcheck="false" aria-label="Search the list"></label><div class="popover-scroll">${element.innerHTML}</div>`;
    const input = element.querySelector(".popover-search input");
    if (query) { input.value = query; input.dispatchEvent(new Event("input", { bubbles: true })); }
    element.querySelector(".popover-scroll").scrollTop = scroll;
  };
  const typed = () => element.querySelector(".popover-search input")?.value || "";
  const scrolled = () => (element.querySelector(".popover-scroll") || element).scrollTop;
  const isLimit = (key) => /^(limit|board|grid|reports|gaps|methods):/.test(String(key));
  // a submenu's row, as a Mac menu shows one: its name, what is picked in it in grey, and a chevron; its list opens to the side on hover
  const sub = Object.assign(document.createElement("div"), { className: "popover popover-sub", hidden: true });
  sub.setAttribute("role", "menu");
  document.body.append(sub);
  let subs = [];
  const CHEVRON = '<svg class="popover-chevron" viewBox="0 0 8 12" aria-hidden="true"><path d="M2 2l4 4-4 4"/></svg>';
  // a submenu row: its list beside it on hover; a row with a value of its own (a view) is picked by a click too, its list
  // then a finer choice within it (the view's engine)
  const parentRow = (o) => `<button class="popover-option popover-parent" type="button" aria-haspopup="menu" data-sub="${subs.push(o.submenu) - 1}"${o.value !== undefined ? ` data-value="${Pie.format.escape(o.value)}"${o.key ? ` data-key="${o.key}"` : ""}` : ""}>${check(Boolean(o.selected))}${o.icon || ""}<span class="popover-label">${Pie.format.escape(o.label)}</span><span class="popover-detail">${Pie.format.escape(o.detail || "")}</span>${CHEVRON}</button>`;
  const limitMenu = (key) => (subs = [], (String(key).startsWith("board:") ? Pie.board : String(key).startsWith("grid:") ? Pie.platform : String(key).startsWith("reports:") ? Pie.reports : String(key).startsWith("gaps:") ? Pie.gaps : String(key).startsWith("methods:") ? Pie.methods : Pie.methodology)?.menu(String(key).slice(String(key).indexOf(":") + 1)) || [])
    .map((o) => (o.submenu ? parentRow(o) : o.separator ? `<div class="popover-separator"></div>` : o.heading ? `<div class="popover-heading">${Pie.format.escape(o.heading)}</div>` : (o.key ? (html) => `<div data-key="${o.key}">${html}</div>` : (html) => html)(option(o.value, o.selected, `${o.indent ? '<span class="popover-indent"></span>' : ""}${o.icon || ""}<span class="popover-label">${o.dot ? `<span class="cell-dot" style="--dot: ${o.dot}">${Pie.format.escape(o.label)}</span>` : Pie.format.escape(o.label)}</span>${o.detail ? `<span class="popover-detail">${Pie.format.escape(o.detail)}</span>` : ""}`, o.check ? "menuitemcheckbox" : undefined))))
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
      // a model after its maker's logo, as the Models page lists them
      .map((entry) => option(entry.value, current.includes(entry.value), `${column.table === "models" && Pie.platform?.makerBadge ? Pie.platform.makerBadge(entry.value) : ""}${Pie.format.option(column, entry.value)}`, "menuitemcheckbox"))
      .join("");
    return `${option(ALL, !current.length, `All ${Pie.filters.plural(column).toLowerCase()}`)}<div class="popover-separator"></div>${values}`;
  };

  const showSub = (row) => {
    if (row.classList.contains("is-open")) return;
    for (const r of element.querySelectorAll(".popover-parent.is-open")) r.classList.remove("is-open");
    row.classList.add("is-open");
    const items = subs[row.dataset.sub] || [];
    sub.innerHTML = items.map((o) => (o.separator ? `<div class="popover-separator"></div>` : `<div data-key="${o.key}">${option(o.value, o.selected, `<span class="popover-label">${o.dot ? `<span class="cell-dot" style="--dot: ${o.dot}">${Pie.format.escape(o.label)}</span>` : Pie.format.escape(o.label)}</span>`)}</div>`)).join("");
    sub.hidden = false;
    const box = row.getBoundingClientRect();
    const right = box.right + 4 + sub.offsetWidth <= window.innerWidth - 8;
    sub.style.left = `${right ? box.right + 4 : box.left - 4 - sub.offsetWidth}px`;
    sub.style.top = `${Math.max(8, Math.min(box.top - 5, window.innerHeight - sub.offsetHeight - 8))}px`;
  };
  const hideSub = () => {
    sub.hidden = true;
    for (const r of element.querySelectorAll(".popover-parent.is-open")) r.classList.remove("is-open");
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
      hideSub();
      Pie.dates?.close();  // one menu open at a time: the Results page's calendar shuts
      owner = key;
      anchor = target;
      element.classList.toggle("is-fit", String(key).startsWith("board:"));  // the Rankings' picks: as wide as their longest item
      element.innerHTML = isLimit(key) ? limitMenu(key) : key === RELEASE ? releaseMenu(state) : key === VIEW ? viewMenu(state) : key === SUITE ? suiteMenu(state) : key === COMPARE ? compareMenu(state) : key === METRIC ? metricMenu(state) : key === MAC ? macMenu(state) : key === WORKLOAD ? workloadMenu(state) : key === ENGINE ? engineMenu(state) : key === HEAT_MAC ? macMenu(state, state.overview.heatMac) : key === STAND_MAC ? macMenu(state, state.overview.standMac) : key === QUAL_ENGINE ? qualityEngineMenu(state) : key === MODEL ? modelMenu(state) : filterMenu(state, key);
      // a short menu of a few words (a card's Decode or Prefill) fits its words, not the menus' usual width
      element.classList.toggle("is-compact", COMPACT.has(key));
      // the field stays put over the list, and only the list scrolls under it
      searchWrap(key);
      element.scrollTop = 0;
      place(target);
      element.querySelector(".popover-search input")?.focus();
    },

    // Redraw the open filter menu in place after a toggle, keeping its scroll position.
    refresh(state) {
      if (!element.hidden && (owner === "grid:maker" || owner === "grid:platform" || owner === "grid:size" || owner === "grid:model")) {
        const query = typed(), scroll = scrolled();
        // a side list left open (Group by) is drawn again on its new row, so its checkmark moves with the pick
        const openSub = sub.hidden ? -1 : [...element.querySelectorAll(".popover-parent")].findIndex((r) => r.classList.contains("is-open"));
        element.innerHTML = limitMenu(owner);
        searchWrap(owner, query, scroll);
        if (openSub >= 0) { const row = element.querySelectorAll(".popover-parent")[openSub]; if (row) showSub(row); else hideSub(); }
        return;
      }
      if (element.hidden || !owner || isLimit(owner) || owner === RELEASE || owner === SUITE || owner === VIEW || owner === METRIC || owner === MAC || owner === WORKLOAD || owner === ENGINE || owner === HEAT_MAC || owner === MODEL || owner === STAND_MAC || owner === QUAL_ENGINE) return;
      const query = typed(), scroll = scrolled();
      element.innerHTML = filterMenu(state, owner);
      searchWrap(owner, query, scroll);
      if (!element.classList.contains("is-searchable")) element.scrollTop = scroll;
    },

    close() {
      element.hidden = true;
      hideSub();
      owner = null;
      anchor = null;
    },

    onPick(handler) {
      onPick = handler;
    },

    bind() {
      // the field narrows the list to the options whose name holds every word typed; Return picks the first one left
      element.addEventListener("input", (event) => {
        if (!event.target.matches(".popover-search input")) return;
        const words = event.target.value.toLowerCase().split(/\s+/).filter(Boolean);
        for (const o of element.querySelectorAll(".popover-option")) o.hidden = !words.every((w) => o.textContent.toLowerCase().includes(w));
      });
      element.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" || !event.target.matches(".popover-search input")) return;
        event.preventDefault();
        element.querySelector(".popover-option:not([hidden])")?.click();
      });
      // a submenu row opens its list on hover, or on click as a Mac menu also allows; any other row shuts it
      element.addEventListener("pointerover", (event) => {
        const row = event.target.closest(".popover-option");
        if (!row) return;
        if (row.classList.contains("popover-parent")) showSub(row);
        else hideSub();
      });
      const choose = (event) => {
        event.stopPropagation();
        const parent = event.target.closest(".popover-parent");
        if (parent && parent.dataset.value === undefined) { showSub(parent); return; }
        const target = event.target.closest("[data-value]");
        if (!target || target.disabled) return;
        const key = target.closest("[data-key]")?.dataset.key || owner;
        // a menu that checks several (the makers) stays open between picks, as a filter menu does
        const several = key === "grid:maker" || key === "grid:platform" || key === "grid:size" || key === "grid:model";
        if (!several && (isLimit(key) || key === RELEASE || key === SUITE || key === METRIC || key === COMPARE || key === MAC || key === WORKLOAD || key === ENGINE || key === HEAT_MAC || key === MODEL || key === STAND_MAC || key === QUAL_ENGINE)) this.close();
        onPick(key, target.dataset.value);
      };
      element.addEventListener("click", choose);
      sub.addEventListener("click", choose);
    },
  };
})();
