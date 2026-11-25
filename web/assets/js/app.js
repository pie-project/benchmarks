(() => {
  const { state, store, query, sidebar, toolbar, popover, filters, table, preferences, overview } = Pie;
  const filterBar = document.querySelector(".filter-bar");

  let linkedCard = null;
  const readHash = () => {
    let address = "";
    try { address = decodeURIComponent(location.hash.slice(1)); } catch { address = ""; }
    const [view, hardware, workload, setup] = address.split("/");
    if (view === "reports" && hardware) Pie.reports?.focus(hardware, workload, setup);
    if (view === "board" && hardware) {
      state.table = "board";
      linkedCard = hardware;
    }
    if (view === "quality") state.table = "checks";
    else if (view && view !== "board" && view !== "overview" && view !== "mac" && Object.hasOwn(Pie.schema, view)) state.table = view;
    if (view === "overview" || view === "mac") {
      state.table = "mac";
      Object.assign(state.overview, { hardware: hardware || null, workload: workload || "raw" });
    }
  };

  const writeHash = () => {
    const hash = state.table === "overview" ? `#overview/${state.overview.hardware || ""}/${state.overview.workload}` : "";
    if (location.hash !== hash) history.replaceState(null, "", hash || location.pathname + location.search);
  };

  const phone = window.matchMedia("(max-width: 899px)");
  const ensurePhone = () => {
    if (!phone.matches) return;
    const newest = (store.tables.tags || [])[0]?.id;
    if (newest) state.release = newest;
    if (store.suites().some((suite) => suite.id === "full")) state.suite = "full";
  };

  const ensureRelease = () => {
    ensurePhone();
    state.release = query.releaseOptions()[0]?.id;
  };

  const ensureSuite = () => {
    const suites = store.suites();
    if (!suites.length) return;
    state.suite = suites.some((suite) => suite.id === "full") ? "full" : suites[suites.length - 1].id;
  };

  let shownTable = null;
  const render = () => {
    if (Pie.schema[state.table]?.href) state.table = "board";
    Pie.palette?.refresh();
    if (state.table !== shownTable) {
      const gridOf = (t) => (Pie.schema[t]?.view === "platform" ? "platform" : t === "checks" ? "checks" : null);
      const from = gridOf(shownTable), to = gridOf(state.table);
      if (from && to && Pie.platform.wave) (to === "checks" ? Pie.checks : Pie.platform).inherit(Pie.platform.ghostsOf(document.getElementById(from)));
      shownTable = state.table;
      restoreScroll();
    }
    ensureSuite();
    ensureRelease();
    const isOverview = state.table === "overview";
    const isPlatform = Pie.schema[state.table]?.view === "platform";
    const isMethod = ["welcome", "approach", "reports", "gaps", "reasons", "methods", "fit", "board", "accuracy", "checks"].includes(state.table);
    filterBar.hidden = (isOverview || isMethod || isPlatform) && state.table !== "reports" && state.table !== "gaps" && state.table !== "approach";
    const rules = filterBar.querySelector("[data-rules]");
    if (rules) rules.hidden = Pie.schema[state.table]?.section === "catalog" || Pie.schema[state.table]?.section === "reports" || state.table === "approach";
    table.container.hidden = isOverview || isMethod || isPlatform;
    overview.element.hidden = !isOverview;
    Pie.platform.element.hidden = !isPlatform;
    if (Pie.loading.done() && isPlatform) Pie.platform.roll();
    Pie.welcome.render(state);
    Pie.approach.render(state);
    Pie.reports.render(state);
    Pie.gaps.render(state);
    Pie.reasons.render(state);
    Pie.methods.render(state);
    Pie.board.render(state);
    const checked = Pie.checks.render(state);
    sidebar.render(state);
    if (!isPlatform) Pie.platform.left();
    if (isPlatform) {
      const shown = Pie.platform.render(state);
      toolbar.render(state, 0, 0);
      toolbar.elements.subtitle.textContent = shown.macs ? `${shown.macs} ${shown.macs === 1 ? "machine" : "machines"}, ${shown.models} ${shown.models === 1 ? "model" : "models"}` : "";
    } else if (isOverview) {
      const models = overview.render(state);
      toolbar.render(state, 0, 0);
      toolbar.elements.subtitle.textContent = `${models} ${models === 1 ? "model" : "models"}`;
    } else if (isMethod) {
      toolbar.elements.title.textContent = Pie.schema[state.table].title || Pie.schema[state.table].label;
      if (state.table === "approach") {
        document.getElementById("filter-list").innerHTML = "";
        for (const id of ["report-selected", "download-rows", "table-keys"]) document.getElementById(id).hidden = true;
      }
      if (state.table === "reports" || state.table === "gaps") {
        filters.render(state);
        document.getElementById("filter-list").insertAdjacentHTML("afterbegin", state.table === "reports" ? Pie.reports.bar() : Pie.gaps.bar());
        document.getElementById("report-selected").hidden = true;
        document.getElementById("download-rows").hidden = true;
        document.getElementById("table-keys").hidden = true;
        if (state.table === "reports") filterBar.hidden = !document.getElementById("filter-list").children.length;
      }
      toolbar.elements.subtitle.textContent = state.table === "board" ? "Engine Analysis" : state.table === "approach" ? Pie.approach.place()
        : state.table === "reports" ? Pie.reports.shown() : state.table === "gaps" ? Pie.gaps.shown() : state.table === "reasons" ? Pie.reasons.shown()
        : checked?.macs ? `${checked.macs} ${checked.macs === 1 ? "machine" : "machines"}, ${checked.models} ${checked.models === 1 ? "model" : "models"}` : "";
      if (state.table === "welcome") {
        const platforms = Object.values(Pie.schema).filter((s) => s.view === "platform" && s.platform).length;
        const machines = Pie.platform.machines();
        toolbar.elements.subtitle.textContent = `${platforms} ${platforms === 1 ? "platform" : "platforms"}, ${machines} ${machines === 1 ? "machine" : "machines"}`;
      }
    } else {
      const rows = query.visibleRows(state);
      if (state.table === "results") {
        toolbar.render(state, rows.length, store.snapshot(state.release).length);
        toolbar.elements.subtitle.textContent += ` · ${rows.filter(store.isMeasured).length} measured`;
      } else {
        toolbar.render(state, rows.length, store.rows(state.table).length);
      }
      filters.render(state);
      table.render(state, rows);
    }
    writeHash();
    saveView();
  };

  const navigate = (tableName, initialFilters = {}) => {
    state.reset(tableName, initialFilters);
    toolbar.clearSearch();
    popover.close();
    preferences.showDrawer(false);
    render();
  };

  const bindToolbar = () => {
    const { elements } = toolbar;

    elements.sidebarToggle.addEventListener("click", () => preferences.toggleSidebar());
    elements.themeToggle.addEventListener("click", () => preferences.toggleTheme());
    document.getElementById("sidebar-theme").addEventListener("click", () => preferences.toggleTheme());

    elements.search.addEventListener("input", (event) => {
      state.query = event.target.value;
      render();
    });

    elements.search.addEventListener("focus", () => {
      if (preferences.compact.matches) toolbar.showSearch(true);
    });
    elements.search.addEventListener("blur", () => {
      if (!elements.search.value) toolbar.showSearch(false);
    });
    elements.searchCancel.addEventListener("click", () => {
      toolbar.clearSearch();
      if (state.query) {
        state.query = "";
        render();
      }
    });
  };

  const bindFilters = () => {
    filters.onOpen((anchor, key) => popover.open(anchor, key, state));
    filters.onClear(() => { state.filters = {}; render(); });



    popover.bind();
    popover.onPick((key, value) => {
      if (key === popover.METRIC) {
        state.platform.mode = value;
      } else if (key === popover.COMPARE && value === "hide") {
        state.hideEmpty = !state.hideEmpty;
        try {
          localStorage.setItem("hideUnavailable", state.hideEmpty ? "1" : "0");
        } catch {
        }
      } else if (key === popover.COMPARE) {
        Pie.platform.setCompare(value);
      } else if (key === popover.MAC) {
        state.overview.hardware = value;
      } else if (key === popover.WORKLOAD) {
        state.overview.workload = value;
      } else if (key === popover.ENGINE) {
        state.overview.engine = value;
      } else if (key === popover.HEAT_MAC) {
        state.overview.heatMac = value;
      } else if (key === popover.MODEL) {
        state.overview.model = value;
      } else if (key === popover.STAND_MAC) {
        state.overview.standMac = value;
      } else if (key === popover.QUAL_ENGINE) {
        state.overview.qualityEngine = value;
      } else if (String(key).startsWith("board:")) {
        Pie.board.pick(key.slice(6), value);

      } else if (String(key).startsWith("grid:")) {
        Pie.platform.pick(key.slice(5), value);
      } else if (String(key).startsWith("reports:")) {
        Pie.reports.pick(key.slice(8), value);
      } else if (String(key).startsWith("gaps:")) {
        Pie.gaps.pick(key.slice(5), value);
      } else if (String(key).startsWith("reasons:")) {
        Pie.reasons.pick(key.slice(8), value);
      } else if (String(key).startsWith("methods:")) {
        Pie.methods.pick(key.slice(8), value);
      } else if (value === popover.ALL) {
        state.setFilter(key, []);
      } else {
        state.toggleFilter(key, value);
      }
      render();
      popover.refresh(state);
    });
  };

  const bindTable = () => {
    table.onSort((key) => {
      state.cycleSort(key);
      render();
    });
    table.onShowResults((key, value) => navigate("results", { [key]: [value] }));
    table.bindTapNotes();
    table.bindFlags();
    table.container.addEventListener("scroll", () => popover.close());
  };

  const bindGlobal = () => {
    sidebar.onSelect((tableName) => navigate(tableName));
    Pie.welcome.onOpen((platform) => navigate("results", { platform: [platform] }));
    sidebar.bindLogo();
    sidebar.bindDrawer(() => preferences.showDrawer(false));
    preferences.compact.addEventListener("change", () => preferences.showDrawer(false));

    document.addEventListener("click", () => popover.close());
    window.addEventListener("resize", () => popover.close());

    const peek = (on) => {
      if (!Pie.platform.peek(on)) return;
      popover.close();
      render();
      Pie.platform.refreshCard();
    };
    const showUnavailable = (on) => {
      if (state.hideEmpty === !on) return;
      state.hideEmpty = !on;
      popover.close();
      render();
    };
    document.addEventListener("keyup", (event) => {
      if (event.key.toLowerCase() === "r") peek(false);
      if (event.key.toLowerCase() === "u") showUnavailable(false);
    });
    window.addEventListener("blur", () => {
      peek(false);
      showUnavailable(false);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        popover.close();
        preferences.showDrawer(false);
        if (document.activeElement === toolbar.elements.search) {
          event.preventDefault();
          toolbar.clearSearch();
          toolbar.elements.search.blur();
          if (state.query) {
            state.query = "";
            render();
          }
        }
      }
      if (event.key.toLowerCase() === "s" && (event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey && !event.repeat) {
        event.preventDefault();
        preferences.toggleSidebar();
      }
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
      if (event.key.toLowerCase() === "r" && !event.metaKey && !event.ctrlKey && !event.altKey && !typing && Pie.schema[state.table]?.view === "platform") {
        event.preventDefault();
        if (!event.repeat) peek(true);
      }
      if (event.key.toLowerCase() === "u" && !event.metaKey && !event.ctrlKey && !event.altKey && !typing) {
        event.preventDefault();
        if (!event.repeat) showUnavailable(true);
      }
      const setup = Pie.platform.metrics().filter((m) => m.id !== "spec")[Number(event.key) - 1];
      if (setup && Pie.platform.metrics(state).includes(setup) && /^[1-9]$/.test(event.key) && !event.metaKey && !event.ctrlKey && !event.altKey && !typing
          && (Pie.schema[state.table]?.view === "platform" || state.table === "methods")) {
        event.preventDefault();
        state.platform.mode = setup.id;
        popover.close();
        render();
      }
      const plain = !event.metaKey && !event.ctrlKey && !event.altKey && !typing;
      const onPlatform = Pie.schema[state.table]?.view === "platform";
      const pages = [...document.querySelectorAll("#sidebar-nav .sidebar-item[data-table]")].map((b) => b.dataset.table);
      if ((event.key === "]" || event.key === "[") && plain && pages.length) {
        const here = Math.max(0, pages.indexOf(state.table));
        const next = pages[(here + (event.key === "[" ? pages.length - 1 : 1)) % pages.length];
        event.preventDefault();
        popover.close();
        document.querySelector(`.sidebar-item[data-table="${next}"]`)?.click();
      }
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && onPlatform && !popover.isOpen()) {
        const scroller = document.querySelector("#platform .platform-section:hover .platform-section-scroll") || document.querySelector("#platform .platform-scroll");
        const col = [...(scroller?.querySelectorAll("col.col-model") || [])].pop();
        if (scroller && col) {
          event.preventDefault();
          scroller.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * col.offsetWidth, behavior: "smooth" });
        }
      }
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && state.table === "checks" && !popover.isOpen()) {
        const scroller = document.querySelector("#checks .platform-section:hover .platform-section-scroll") || document.querySelector("#checks .platform-section-scroll");
        const col = scroller?.querySelector("tbody td:nth-child(3), thead th:nth-child(3)");
        if (scroller) {
          event.preventDefault();
          scroller.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * (col?.offsetWidth || 132), behavior: "smooth" });
        }
      }
      const tableScroll = document.getElementById("table-container");
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && !onPlatform && !popover.isOpen()
          && tableScroll && !tableScroll.hidden && tableScroll.scrollWidth > tableScroll.clientWidth) {
        event.preventDefault();
        tableScroll.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * 132, behavior: "smooth" });
      }
      if ((event.key === "ArrowUp" || event.key === "ArrowDown") && plain && !event.shiftKey && !popover.isOpen()) {
        const scroller = pageScroller();
        const col = [...document.querySelectorAll("#platform col.col-model")].pop();
        if (scroller) {
          event.preventDefault();
          scroller.scrollBy({ top: (event.key === "ArrowUp" ? -3 : 3) * (col?.offsetWidth || 132), behavior: "smooth" });
        }
      }
      if (event.key.toLowerCase() === "v" && plain && onPlatform && !event.repeat) {
        event.preventDefault();
        Pie.platform.setCompare(Pie.platform.next());
        popover.close();
        render();
      }
      if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
        event.preventDefault();
        Pie.palette.open();
      }
    });
  };

  const bindOverview = () => {
    Pie.platform.bind(state);
    Pie.platform.onChange(render);
    Pie.platform.onOpenResults(({ _unavailable, ...filters }) => { if (_unavailable) state.hideEmpty = false; navigate("results", filters); });
    Pie.platform.onOpenGap((cell) => { Pie.reasons.focus(cell); navigate("reasons"); });
    Pie.checks.onOpenRuns((filters) => navigate("quality", filters));
    overview.bind(state);
    overview.onChange(render);
    overview.onOpenMac((anchor) => popover.open(anchor, popover.MAC, state));
    overview.onOpenWorkload((anchor) => popover.open(anchor, popover.WORKLOAD, state));
    overview.onOpenEngine((anchor) => popover.open(anchor, popover.ENGINE, state));
    overview.onOpenHeatMac((anchor) => popover.open(anchor, popover.HEAT_MAC, state));
    overview.onOpenModel((anchor) => popover.open(anchor, popover.MODEL, state));
    overview.onOpenStandMac((anchor) => popover.open(anchor, popover.STAND_MAC, state));
    overview.onOpenQualityEngine((anchor) => popover.open(anchor, popover.QUAL_ENGINE, state));
  };

  const VIEW_KEY = "pieView";
  const restoreView = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(VIEW_KEY) || "null");
      if (!saved) return;
      if (saved.table && Pie.schema[saved.table]) state.table = saved.table;
      if (saved.overview) Object.assign(state.overview, saved.overview);
      if (saved.platform) Object.assign(state.platform, saved.platform);
      if (saved.filters && saved.table === state.table) state.filters = { ...saved.filters };
    } catch {
    }
  };
  const saveView = () => {
    try {
      localStorage.setItem(VIEW_KEY, JSON.stringify({
        table: state.table, suite: state.suite, overview: { ...state.overview }, platform: { ...state.platform }, hideEmpty: state.hideEmpty, filters: { ...state.filters },
      }));
    } catch {
    }
  };

  Pie.saveView = saveView;

  const SCROLLERS = ["#platform .platform-scroll", "#board .board-scroll", "#table-container", ".method:not([hidden])", "#overview"];
  const pageScroller = () => SCROLLERS.map((selector) => document.querySelector(selector))
    .find((el) => el && el.offsetParent !== null && (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth));

  const SCROLL_KEY = "pieScroll";
  const scrolls = (() => { try { return JSON.parse(localStorage.getItem(SCROLL_KEY) || "{}"); } catch { return {}; } })();
  let keepTimer = 0;
  let restoring = false;
  document.addEventListener("scroll", (event) => {
    if (restoring || event.target !== pageScroller()) return;
    scrolls[state.table] = { top: Math.round(event.target.scrollTop), left: Math.round(event.target.scrollLeft) };
    clearTimeout(keepTimer);
    keepTimer = setTimeout(() => { try { localStorage.setItem(SCROLL_KEY, JSON.stringify(scrolls)); } catch { } }, 150);
  }, { capture: true, passive: true });
  const restoreScroll = () => {
    restoring = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const at = scrolls[state.table] || 0;
      const scroller = pageScroller();
      if (scroller) {
        scroller.scrollTop = typeof at === "number" ? at : at.top || 0;
        scroller.scrollLeft = typeof at === "number" ? 0 : at.left || 0;
      }
      if (linkedCard) {
        document.getElementById(`board-${linkedCard}`)?.scrollIntoView({ block: "start" });
        linkedCard = null;
      }
      requestAnimationFrame(() => { restoring = false; });
    }));
  };

  restoreView();
  readHash();
  bindToolbar();
  bindOverview();
  bindFilters();
  bindTable();
  bindGlobal();
  document.addEventListener("pie:refresh", () => render());
  {
    const BARS = ".platform-bar, .board-bar, .filter-bar";
    let drag = null;
    document.addEventListener("pointerdown", (event) => {
      const bar = event.target.closest?.(BARS);
      if (!bar || event.pointerType !== "mouse" || event.button !== 0 || bar.scrollWidth <= bar.clientWidth) return;
      drag = { bar, x: event.clientX, left: bar.scrollLeft, moved: false };
    });
    document.addEventListener("pointermove", (event) => {
      if (!drag) return;
      const dx = event.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) < 4) return;
      drag.moved = true;
      drag.bar.scrollLeft = drag.left - dx;
      drag.bar.classList.add("is-dragging");
    });
    document.addEventListener("pointerup", () => {
      if (!drag) return;
      const { bar, moved } = drag;
      drag = null;
      bar.classList.remove("is-dragging");
      if (!moved) return;
      const swallow = (e) => { e.stopPropagation(); e.preventDefault(); };
      bar.addEventListener("click", swallow, { capture: true, once: true });
      setTimeout(() => bar.removeEventListener("click", swallow, { capture: true }), 0);
    });
  }
  Pie.palette.bind({
    state,
    render,
    filters: () => { const s = Pie.schema[state.table]; return s?.view === "platform" || state.table === "overview" || (!s?.view && Boolean(s?.columns?.length)); },
  });
  render();
})();
