(() => {
  const { state, store, query, sidebar, toolbar, popover, filters, table, preferences, overview } = Pie;
  const filterBar = document.querySelector(".filter-bar");

  // the overview's Mac and workload live in the address, so a reload or a shared link keeps them
  const readHash = () => {
    const [view, hardware, workload] = decodeURIComponent(location.hash.slice(1)).split("/");
    if (view === "overview" || view === "mac") {
      state.table = "mac";
      Object.assign(state.overview, { hardware: hardware || null, workload: workload || "single" });
    }
  };

  const writeHash = () => {
    const hash = state.table === "overview" ? `#overview/${state.overview.hardware || ""}/${state.overview.workload}` : "";
    if (location.hash !== hash) history.replaceState(null, "", hash || location.pathname + location.search);
  };

  // a phone shows the newest run in the Full suite, with no picker for either
  const phone = window.matchMedia("(max-width: 899px)");
  const ensurePhone = () => {
    if (!phone.matches) return;
    const newest = (store.tables.tags || [])[0]?.id;
    if (newest) state.release = newest;
    if (store.suites().some((suite) => suite.id === "full")) state.suite = "full";
  };

  const ensureRelease = () => {
    ensurePhone();
    const options = query.releaseOptions();
    if (!options.some((option) => option.id === state.release)) {
      state.release = options[0]?.id;
    }
  };

  const ensureSuite = () => {
    const suites = store.suites();
    if (suites.length && !suites.some((suite) => suite.id === state.suite)) state.suite = suites[suites.length - 1].id;
  };

  const render = () => {
    ensureSuite();
    ensureRelease();
    toolbar.renderSuite(state);
    const isOverview = state.table === "overview";
    const isPlatform = Pie.schema[state.table]?.view === "platform";
    const isMethod = ["welcome", "inferlets", "methodology"].includes(state.table);
    filterBar.hidden = isOverview || isMethod || isPlatform;
    table.container.hidden = isOverview || isMethod || isPlatform;
    overview.element.hidden = !isOverview;
    Pie.platform.element.hidden = !isPlatform;
    toolbar.elements.metricPicker.hidden = true;  // the metric lives in the platform table's own bar
    Pie.welcome.render(state);
    Pie.inferlets.render(state);
    Pie.methodology.render(state);
    sidebar.render(state);
    if (isPlatform) {
      const shown = Pie.platform.render(state);
      toolbar.elements.metricValue.textContent = shown.metric.label;
      toolbar.render(state, 0, 0);
      toolbar.elements.subtitle.textContent = shown.macs ? `${shown.macs} ${shown.macs === 1 ? "machine" : "machines"}, ${shown.models} ${shown.models === 1 ? "model" : "models"}` : "";
    } else if (isOverview) {
      const models = overview.render(state);
      toolbar.render(state, 0, 0);
      toolbar.elements.subtitle.textContent = `${models} ${models === 1 ? "model" : "models"}`;
    } else if (isMethod) {
      toolbar.elements.title.textContent = Pie.schema[state.table].label;
      toolbar.elements.subtitle.textContent = "";
      toolbar.renderRelease(state);
    } else {
      const rows = query.visibleRows(state);
      if (state.table === "results") {
        // every enumerated setup of the selected release counts, measured or not; the measured ones are said apart
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
    // on a phone the appearance switch sits at the foot of the slide-over, as in Settings
    document.getElementById("sidebar-theme").addEventListener("click", () => preferences.toggleTheme());

    elements.search.addEventListener("input", (event) => {
      state.query = event.target.value;
      render();
    });

    // the phone's search icon opens the field; an empty field closes again when it loses focus
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

    elements.viewPicker.addEventListener("click", (event) => {
      event.stopPropagation();
      popover.open(elements.viewPicker, popover.VIEW, state);
    });

    elements.releasePicker.addEventListener("click", (event) => {
      event.stopPropagation();
      popover.open(elements.releasePicker, popover.RELEASE, state);
    });

    elements.metricPicker.addEventListener("click", (event) => {
      event.stopPropagation();
      popover.open(elements.metricPicker, popover.METRIC, state);
    });

    elements.suitePicker.addEventListener("click", (event) => {
      event.stopPropagation();
      popover.open(elements.suitePicker, popover.SUITE, state);
    });
  };

  const bindFilters = () => {
    filters.onOpen((anchor, key) => popover.open(anchor, key, state));


    filters.hideEmpty.addEventListener("click", () => {
      state.hideEmpty = !state.hideEmpty;
      try {
        localStorage.setItem("hideUnavailable", state.hideEmpty ? "1" : "0");
      } catch {
        // private windows can refuse storage; the choice then lasts for this page only
      }
      render();
    });

    popover.bind();
    popover.onPick((key, value) => {
      if (key === popover.RELEASE) {
        state.release = value;
      } else if (key === popover.METRIC) {
        state.platform.metric = value;
      } else if (key === popover.SUITE) {
        state.suite = value;
        state.suitePicked = true;
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
      } else if (key === popover.HIST_MAC) {
        state.overview.historyMac = value;
      } else if (key === popover.HIST_MODEL) {
        state.overview.historyModel = value;
      } else if (key === popover.QUAL_ENGINE) {
        state.overview.qualityEngine = value;
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
    table.container.addEventListener("scroll", () => popover.close());
  };

  const bindGlobal = () => {
    sidebar.onSelect((tableName) => navigate(tableName));
    sidebar.bindLogo();
    sidebar.bindDrawer(() => preferences.showDrawer(false));
    // a slide-over left open closes when the window grows back to the desktop sidebar
    preferences.compact.addEventListener("change", () => preferences.showDrawer(false));

    document.addEventListener("click", () => popover.close());
    window.addEventListener("resize", () => popover.close());

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        popover.close();
        preferences.showDrawer(false);
      }
      if (event.ctrlKey && event.metaKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        preferences.toggleSidebar();
      }
      if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
        event.preventDefault();
        toolbar.focusSearch();
      }
    });
  };

  const bindOverview = () => {
    Pie.platform.bind(state);
    Pie.platform.onChange(render);
    overview.bind(state);
    overview.onChange(render);
    overview.onOpenMac((anchor) => popover.open(anchor, popover.MAC, state));
    overview.onOpenWorkload((anchor) => popover.open(anchor, popover.WORKLOAD, state));
    overview.onOpenEngine((anchor) => popover.open(anchor, popover.ENGINE, state));
    overview.onOpenHeatMac((anchor) => popover.open(anchor, popover.HEAT_MAC, state));
    overview.onOpenModel((anchor) => popover.open(anchor, popover.MODEL, state));
    overview.onOpenStandMac((anchor) => popover.open(anchor, popover.STAND_MAC, state));
    overview.onOpenHistoryMac((anchor) => popover.open(anchor, popover.HIST_MAC, state));
    overview.onOpenHistoryModel((anchor) => popover.open(anchor, popover.HIST_MODEL, state));
    overview.onOpenQualityEngine((anchor) => popover.open(anchor, popover.QUAL_ENGINE, state));
  };

  // the view a viewer left (page, suite, Mac, workload, hide choice) is kept per browser; the address still wins.
  // A reload always opens the newest run: a release picked in the menu lasts until the page reloads
  const VIEW_KEY = "pieView";
  const restoreView = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(VIEW_KEY) || "null");
      if (!saved) return;
      if (saved.table && Pie.schema[saved.table]) state.table = saved.table;
      if (saved.suite && saved.suitePicked) {
        state.suite = saved.suite;
        state.suitePicked = true;
      }
      if (saved.overview) Object.assign(state.overview, saved.overview);
      if (saved.platform) Object.assign(state.platform, saved.platform);
      state.hideEmpty = Boolean(saved.hideEmpty);
    } catch {
      // storage refused or damaged: start from the defaults
    }
  };
  const saveView = () => {
    try {
      localStorage.setItem(VIEW_KEY, JSON.stringify({
        table: state.table, suite: state.suite, suitePicked: Boolean(state.suitePicked), overview: { ...state.overview }, platform: { ...state.platform }, hideEmpty: state.hideEmpty,
      }));
    } catch {
      // private windows can refuse storage
    }
  };

  // the release history stays open or closed as the viewer left it
  document.addEventListener("toggle", (event) => {
    if (event.target.id !== "history-details") return;
    state.overview.historyOpen = event.target.open;
    saveView();
  }, true);

  restoreView();
  readHash();
  bindToolbar();
  bindOverview();
  bindFilters();
  bindTable();
  bindGlobal();
  render();
})();
