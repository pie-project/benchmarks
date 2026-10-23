(() => {
  const { state, store, query, sidebar, toolbar, popover, filters, table, preferences, overview } = Pie;
  const filterBar = document.querySelector(".filter-bar");

  // the overview's Mac and workload live in the address, so a reload or a shared link keeps them
  const readHash = () => {
    const [view, hardware, workload] = decodeURIComponent(location.hash.slice(1)).split("/");
    if (view === "overview" || view === "mac") {
      state.table = "mac";
      Object.assign(state.overview, { hardware: hardware || null, workload: workload || "raw" });
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

  // the site always shows the Full suite; CI still runs Targeted and Full, but only Full is published to read
  const ensureSuite = () => {
    const suites = store.suites();
    if (!suites.length) return;
    state.suite = suites.some((suite) => suite.id === "full") ? "full" : suites[suites.length - 1].id;
  };

  const render = () => {
    ensureSuite();
    ensureRelease();
    toolbar.renderSuite(state);
    const isOverview = state.table === "overview";
    const isPlatform = Pie.schema[state.table]?.view === "platform";
    const isMethod = ["welcome", "inferlets", "services", "profiler", "methodology", "methods"].includes(state.table);
    filterBar.hidden = isOverview || isMethod || isPlatform;
    // the catalog lists what was measured on, not how: no Configuration there
    const rules = filterBar.querySelector("[data-rules]");
    if (rules) rules.hidden = Pie.schema[state.table]?.section === "catalog";
    table.container.hidden = isOverview || isMethod || isPlatform;
    overview.element.hidden = !isOverview;
    Pie.platform.element.hidden = !isPlatform;
    // a platform is a folder: back returns to All Platforms and forward reopens the platform just left, as in Finder
    toolbar.elements.nav.hidden = !isPlatform && state.table !== "welcome";
    toolbar.elements.back.disabled = !isPlatform;
    toolbar.elements.forward.disabled = state.table !== "welcome" || !forwardTo;
    toolbar.elements.metricPicker.hidden = true;  // the metric lives in the platform table's own bar
    Pie.welcome.render(state);
    Pie.inferlets.render(state);
    Pie.services.render(state);
    Pie.profiler.render(state);
    Pie.methodology.render(state);
    Pie.methods.render(state);
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
      toolbar.elements.title.textContent = Pie.schema[state.table].title || Pie.schema[state.table].label;
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

  let forwardTo = null;  // the platform the back chevron left, for the forward one
  const navigate = (tableName, initialFilters = {}) => {
    forwardTo = null;
    state.reset(tableName, initialFilters);
    toolbar.clearSearch();
    popover.close();
    preferences.showDrawer(false);
    render();
  };

  const bindToolbar = () => {
    const { elements } = toolbar;

    elements.sidebarToggle.addEventListener("click", () => preferences.toggleSidebar());
    const back = () => {
      const from = state.table;
      navigate("welcome");
      forwardTo = from;
      render();
    };
    const forward = () => navigate(forwardTo);
    elements.back.addEventListener("click", back);
    elements.forward.addEventListener("click", forward);
    // ⌘[ and ⌘] go back and forward, as in Finder and Safari
    document.addEventListener("keydown", (event) => {
      if (!event.metaKey || elements.nav.hidden) return;
      const button = event.key === "[" ? elements.back : event.key === "]" ? elements.forward : null;
      if (!button || button.disabled) return;
      event.preventDefault();
      button === elements.back ? back() : forward();
    });
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



    popover.bind();
    popover.onPick((key, value) => {
      if (key === popover.RELEASE) {
        state.release = value;
      } else if (key === popover.METRIC) {
        state.platform.mode = value;
      } else if (key === popover.SUITE) {
        state.suite = value;
        state.suitePicked = true;
      } else if (key === popover.COMPARE && value === "hide") {
        // the same Hide unavailable as the results and quality tables: one choice for every page
        state.hideEmpty = !state.hideEmpty;
        try {
          localStorage.setItem("hideUnavailable", state.hideEmpty ? "1" : "0");
        } catch {
          // private windows can refuse storage
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
      } else if (key === popover.HIST_MAC) {
        state.overview.historyMac = value;
      } else if (key === popover.HIST_MODEL) {
        state.overview.historyModel = value;
      } else if (key === popover.QUAL_ENGINE) {
        state.overview.qualityEngine = value;
      } else if (String(key).startsWith("limit:")) {
        Pie.methodology.pick(key.slice(6), value);
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

    // the peek: the grid and the card under a still pointer redraw in the other view, and come back on release
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
    // leaving the window while R or U is held lets go too
    window.addEventListener("blur", () => {
      peek(false);
      showUnavailable(false);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        popover.close();
        preferences.showDrawer(false);
        // Escape in the search field clears it and leaves it, as a Mac search field does; the filter clears with it
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
      if (event.ctrlKey && event.metaKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        preferences.toggleSidebar();
      }
      // holding R on a platform page shows the other view, Speedup or Efficiency, until it is let go: a plain key,
      // never while typing or with a modifier held; the key's repeats while held change nothing
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
      if (event.key.toLowerCase() === "r" && !event.metaKey && !event.ctrlKey && !event.altKey && !typing && Pie.schema[state.table]?.view === "platform") {
        event.preventDefault();
        if (!event.repeat) peek(true);
      }
      // holding U shows the unavailable rows and cells until it is let go, as R peeks at the other view
      if (event.key.toLowerCase() === "u" && !event.metaKey && !event.ctrlKey && !event.altKey && !typing) {
        event.preventDefault();
        if (!event.repeat) showUnavailable(true);
      }
      // 1 to 4 pick a setup by its fixed number, whatever a platform measured: a number keeps its setup on every
      // platform, and one the page does not list does nothing; plain keys, as R and U are
      const setup = Pie.platform.metrics()[Number(event.key) - 1];
      if (setup && Pie.platform.metrics(state).includes(setup) && /^[1-9]$/.test(event.key) && !event.metaKey && !event.ctrlKey && !event.altKey && !typing
          && (Pie.schema[state.table]?.view === "platform" || state.table === "methods")) {
        event.preventDefault();
        state.platform.mode = setup.id;
        popover.close();
        render();
      }
      const plain = !event.metaKey && !event.ctrlKey && !event.altKey && !typing;
      const onPlatform = Pie.schema[state.table]?.view === "platform";
      // ] and [ open the next and the previous platform in the sidebar's order, round from the last to the first,
      // as macOS steps through tabs; Tab keeps moving the focus
      if ((event.key === "]" || event.key === "[") && plain && onPlatform) {
        const ids = Object.keys(Pie.schema).filter((id) => Pie.schema[id].view === "platform");
        const next = ids[(ids.indexOf(state.table) + (event.key === "[" ? ids.length - 1 : 1)) % ids.length];
        event.preventDefault();
        popover.close();
        document.querySelector(`.sidebar-item[data-table="${next}"]`)?.click();
      }
      // ← and → scroll a platform's grid three model columns at a time, not the browser's few points
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && onPlatform && !popover.isOpen()) {
        const scroller = document.querySelector("#platform .platform-scroll");
        const col = [...(scroller?.querySelectorAll("col.col-model") || [])].pop();  // a model's column, not Overall's
        if (scroller && col) {
          event.preventDefault();
          scroller.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * col.offsetWidth, behavior: "smooth" });
        }
      }
      // V switches Speedup and Efficiency for good; holding R still only peeks
      if (event.key.toLowerCase() === "v" && plain && onPlatform && !event.repeat) {
        event.preventDefault();
        Pie.platform.setCompare(Pie.platform.compare() === "engines" ? "ceiling" : "engines");
        popover.close();
        render();
      }
      // , and . open the older and the newer run of the release menu
      if ((event.key === "," || event.key === ".") && plain) {
        const runs = query.releaseOptions();  // newest first
        const next = runs[runs.findIndex((run) => run.id === state.release) + (event.key === "," ? 1 : -1)];
        if (next) {
          event.preventDefault();
          state.release = next.id;
          popover.close();
          render();
        }
      }
      // S shows or hides the sidebar, one key for what ⌃⌘S also does
      if (event.key.toLowerCase() === "s" && plain && !event.shiftKey && !event.repeat) {
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
      if (saved.overview) Object.assign(state.overview, saved.overview);
      if (saved.platform) Object.assign(state.platform, saved.platform);
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
