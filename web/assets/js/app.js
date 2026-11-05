(() => {
  const { state, store, query, sidebar, toolbar, popover, filters, table, preferences, overview } = Pie;
  const filterBar = document.querySelector(".filter-bar");

  // the overview's Mac and workload live in the address, so a reload or a shared link keeps them
  // a link to one chart, #board/<card>: Rankings opens on it, scrolled to that card once the page is drawn
  let linkedCard = null;
  const readHash = () => {
    const [view, hardware, workload, setup] = decodeURIComponent(location.hash.slice(1)).split("/");
    // #reports/<machine>/<model>/<setup>: Pie Reports narrowed to that one cell, as a GitHub report's Open link reads
    if (view === "reports" && hardware) Pie.reports?.focus(hardware, workload, setup);
    if (view === "board" && hardware) {
      state.table = "board";
      linkedCard = hardware;
    }
    if (view === "quality") state.table = "checks";  // #quality opens the Quality checks
    // any other page opens by its name too (#reports, #approach), so a link from outside the site lands on it
    else if (view && view !== "board" && view !== "overview" && view !== "mac" && Pie.schema[view]) state.table = view;
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
    // there is no release picker: every page shows the latest
    state.release = query.releaseOptions()[0]?.id;
  };

  // the site always shows the Full suite; CI still runs Targeted and Full, but only Full is published to read
  const ensureSuite = () => {
    const suites = store.suites();
    if (!suites.length) return;
    state.suite = suites.some((suite) => suite.id === "full") ? "full" : suites[suites.length - 1].id;
  };

  let shownTable = null;  // the page the last render drew, so a switch to another page restores where that one was left
  const render = () => {
    // a page only an account opens (Measurements, Catalog, Resources), kept from an earlier visit or linked to, opens Rankings
    if (!Pie.isOpen(state.table) || Pie.schema[state.table]?.href) state.table = "board";  // a link (Quality) is not a page
    Pie.palette?.refresh();
    if (state.table !== shownTable) {
      // from one grid page to another (Performance, Quality, a platform): the old numbers wave out as the new wave in,
      // as if one page changed
      const gridOf = (t) => (Pie.schema[t]?.view === "platform" ? "platform" : t === "checks" ? "checks" : null);
      const from = gridOf(shownTable), to = gridOf(state.table);
      if (from && to && Pie.platform.wave) (to === "checks" ? Pie.checks : Pie.platform).inherit(Pie.platform.ghostsOf(document.getElementById(from)));
      shownTable = state.table;
      restoreScroll();
    }
    ensureSuite();
    ensureRelease();
    toolbar.renderSuite(state);
    const isOverview = state.table === "overview";
    const isPlatform = Pie.schema[state.table]?.view === "platform";
    // the miniatures' banner over every page that can show their results
    document.getElementById("mini-banner").hidden = true;  // the miniatures note, off: !(Pie.store.miniatures && (isPlatform || ["results", "measurements", "welcome"].includes(state.table)));
    const isMethod = ["welcome", "inferlets", "services", "approach", "reports", "profiler", "methodology", "methods", "fit", "board", "accuracy", "checks"].includes(state.table);
    // Reports keeps the tables' bar above its table (empty for now, the info button at its end), as Performance does
    filterBar.hidden = (isOverview || isMethod || isPlatform) && state.table !== "reports";
    // the catalog lists what was measured on, not how: no Configuration there
    const rules = filterBar.querySelector("[data-rules]");
    if (rules) rules.hidden = Pie.schema[state.table]?.section === "catalog";
    table.container.hidden = isOverview || isMethod || isPlatform;
    overview.element.hidden = !isOverview;
    Pie.platform.element.hidden = !isPlatform;
    // a platform is a folder: back returns to All Platforms and forward reopens the platform just left, as in Finder
    // Efficiency is a page of its own, not a folder in the list: no back or forward there
    const inFolder = isPlatform && Pie.schema[state.table]?.platform;
    toolbar.elements.nav.hidden = true;  // no back or forward chevrons, for now
    toolbar.elements.back.disabled = !inFolder;
    toolbar.elements.forward.disabled = state.table !== "speedups" || !forwardTo;
    toolbar.elements.metricPicker.hidden = true;  // the metric lives in the platform table's own bar
    toolbar.elements.releasePicker.hidden = true;  // the latest release only, so nothing to pick
    toolbar.elements.viewPicker.hidden = true;
    // a tag kept apart (data/tags) is fetched first: the page's outline shows meanwhile, and a fetch done draws again
    if (store.pending(state.release)) {
      store.snapshot(state.release);
      Pie.skeleton.show(state.table);
      sidebar.render(state);
      toolbar.elements.title.textContent = Pie.schema[state.table]?.title || Pie.schema[state.table]?.label || "";
      toolbar.elements.subtitle.textContent = "";
      return;
    }
    // the outline gives way to the page, which fades in; a platform's numbers roll in instead
    if (Pie.skeleton.hide() && isPlatform) Pie.platform.roll();
    Pie.welcome.render(state);
    Pie.inferlets.render(state);
    Pie.services.render(state);
    Pie.approach.render(state);
    Pie.reports.render(state);
    Pie.profiler.render(state);
    Pie.methodology.render(state);
    Pie.methods.render(state);
    Pie.board.render(state);
    const checked = Pie.checks.render(state);
    sidebar.render(state);
    if (!isPlatform) Pie.platform.left();
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
      if (state.table === "reports") {
        filters.render(state);
        document.getElementById("filter-list").insertAdjacentHTML("afterbegin", Pie.reports.bar());  // its Type filter
        document.getElementById("report-selected").hidden = true;  // the Report button belongs to the measurement tables
        document.getElementById("download-rows").hidden = true;  // and so does Download
      }
      // Quality counts its machines and models under its title, as a grid page does
      toolbar.elements.subtitle.textContent = state.table === "board" ? "Engine Analysis"
        : checked?.macs ? `${checked.macs} ${checked.macs === 1 ? "machine" : "machines"}, ${checked.models} ${checked.models === 1 ? "model" : "models"}` : "";
      // All Platforms counts its folders and what they hold, as a platform page counts its machines
      if (state.table === "welcome") {
        const platforms = Object.values(Pie.schema).filter((s) => s.view === "platform" && s.platform).length;
        const machines = Pie.platform.machines();
        toolbar.elements.subtitle.textContent = `${platforms} ${platforms === 1 ? "platform" : "platforms"}, ${machines} ${machines === 1 ? "machine" : "machines"}`;
      }
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
      navigate("speedups");
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
    filters.onClear(() => { state.filters = {}; render(); });



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
      } else if (String(key).startsWith("board:")) {
        Pie.board.pick(key.slice(6), value);

      } else if (String(key).startsWith("grid:")) {
        Pie.platform.pick(key.slice(5), value);
      } else if (String(key).startsWith("reports:")) {
        Pie.reports.pick(key.slice(8), value);
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
      // ⌘S shows or hides the sidebar (Ctrl+S off a Mac, where the browser gets no Windows key), and ⌃⌘S as Finder has it;
      // the browser's Save Page waits, as a web app takes the keys it uses
      if (event.key.toLowerCase() === "s" && (event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey && !event.repeat) {
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
      // Spec Decode has no button (its runs are columns in Decode), so it takes no number
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
      // ] and [ open the next and the previous page in the sidebar's order (Rankings, the overviews, the platforms, and
      // the account's sections when they show), round from the last to the first, as macOS steps through tabs; a link
      // out of the site (Quality) is passed over; Tab keeps moving the focus
      const pages = [...document.querySelectorAll("#sidebar-nav .sidebar-item[data-table]")].map((b) => b.dataset.table);
      if ((event.key === "]" || event.key === "[") && plain && pages.length) {
        const here = Math.max(0, pages.indexOf(state.table));
        const next = pages[(here + (event.key === "[" ? pages.length - 1 : 1)) % pages.length];
        event.preventDefault();
        popover.close();
        document.querySelector(`.sidebar-item[data-table="${next}"]`)?.click();
      }
      // ← and → scroll a platform's grid three model columns at a time, not the browser's few points
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && onPlatform && !popover.isOpen()) {
        // on All Platforms each platform scrolls alone: the keys move the one under the pointer
        const scroller = document.querySelector("#platform .platform-section:hover .platform-section-scroll") || document.querySelector("#platform .platform-scroll");
        const col = [...(scroller?.querySelectorAll("col.col-model") || [])].pop();  // a model's column, not Overall's
        if (scroller && col) {
          event.preventDefault();
          scroller.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * col.offsetWidth, behavior: "smooth" });
        }
      }
      // on the Performance and Quality tables (and the catalog's) ← and → scroll across the columns as ↑ and ↓ scroll down them
      const tableScroll = document.getElementById("table-container");
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && plain && !event.shiftKey && !onPlatform && !popover.isOpen()
          && tableScroll && !tableScroll.hidden && tableScroll.scrollWidth > tableScroll.clientWidth) {
        event.preventDefault();
        tableScroll.scrollBy({ left: (event.key === "ArrowLeft" ? -3 : 3) * 132, behavior: "smooth" });
      }
      // ↑ and ↓ scroll the page's data the same distance ← and → move a grid across: three model columns' worth,
      // on every page with something to scroll (the grid, Rankings, the tables, the method pages)
      if ((event.key === "ArrowUp" || event.key === "ArrowDown") && plain && !event.shiftKey && !popover.isOpen()) {
        const scroller = pageScroller();
        const col = [...document.querySelectorAll("#platform col.col-model")].pop();
        if (scroller) {
          event.preventDefault();
          scroller.scrollBy({ top: (event.key === "ArrowUp" ? -3 : 3) * (col?.offsetWidth || 132), behavior: "smooth" });
        }
      }
      // V moves on to the next view for good, as a click on the view button does; holding R still only peeks
      if (event.key.toLowerCase() === "v" && plain && onPlatform && !event.repeat) {
        event.preventDefault();
        Pie.platform.setCompare(Pie.platform.next());
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
      if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
        event.preventDefault();
        Pie.palette.open();
      }
    });
  };

  const bindOverview = () => {
    Pie.platform.bind(state);
    Pie.platform.onChange(render);
    // an empty cell's runs are the unavailable rows Performance hides: they show, as U would show them
    Pie.platform.onOpenResults(({ _unavailable, ...filters }) => { if (_unavailable) state.hideEmpty = false; navigate("results", filters); });
    Pie.checks.onOpenRuns((filters) => navigate("quality", filters));
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
      // the filters picked on the page a reload reopens stay picked
      if (saved.filters && saved.table === state.table) state.filters = { ...saved.filters };
    } catch {
      // storage refused or damaged: start from the defaults
    }
  };
  const saveView = () => {
    try {
      localStorage.setItem(VIEW_KEY, JSON.stringify({
        table: state.table, suite: state.suite, suitePicked: Boolean(state.suitePicked), overview: { ...state.overview }, platform: { ...state.platform }, hideEmpty: state.hideEmpty, filters: { ...state.filters },
      }));
    } catch {
      // private windows can refuse storage
    }
  };

  // a page that changes in place, with no redraw (a platform folding on All Platforms), keeps its view the same way
  Pie.saveView = saveView;

  // the release history stays open or closed as the viewer left it
  document.addEventListener("toggle", (event) => {
    if (event.target.id !== "history-details") return;
    const opened = event.target.open && !state.overview.historyOpen;
    state.overview.historyOpen = event.target.open;
    saveView();
    if (opened) render();  // its tags are read, and fetched, only once it opens
  }, true);

  // the page's own scroller: the one the page's data scrolls in (the grid, Rankings, the tables, the method pages)
  const SCROLLERS = ["#platform .platform-scroll", "#board .board-scroll", "#table-container", "#methodology", ".method:not([hidden])", "#overview"];
  const pageScroller = () => SCROLLERS.map((selector) => document.querySelector(selector))
    .find((el) => el && el.offsetParent !== null && (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth));

  // how far down and across each page was scrolled is kept per browser, so a reload, or a return to the page, opens it
  // where the viewer left it: down its rows and across a grid's model columns
  const SCROLL_KEY = "pieScroll";
  const scrolls = (() => { try { return JSON.parse(localStorage.getItem(SCROLL_KEY) || "{}"); } catch { return {}; } })();
  let keepTimer = 0;
  let restoring = false;  // while a page is being put back, its scroller's own moves (a shared one clamping) are not kept
  document.addEventListener("scroll", (event) => {
    if (restoring || event.target !== pageScroller()) return;
    scrolls[state.table] = { top: Math.round(event.target.scrollTop), left: Math.round(event.target.scrollLeft) };
    clearTimeout(keepTimer);
    keepTimer = setTimeout(() => { try { localStorage.setItem(SCROLL_KEY, JSON.stringify(scrolls)); } catch { /* private windows can refuse storage */ } }, 150);
  }, { capture: true, passive: true });
  const restoreScroll = () => {
    restoring = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const at = scrolls[state.table] || 0;  // a page never scrolled opens at its top left
      const scroller = pageScroller();
      if (scroller) {
        // an older save kept the height alone, as a number
        scroller.scrollTop = typeof at === "number" ? at : at.top || 0;
        scroller.scrollLeft = typeof at === "number" ? 0 : at.left || 0;
      }
      // a chart linked to opens in view, over where the page was last left
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
  // logging in or out shows or hides the sections only an account opens, and leaves a page that closes with them
  document.addEventListener("pie:account", () => render());
  document.addEventListener("pie:refresh", () => render());
  // a toolbar row wider than the window (a phone, a narrow window) scrolls sideways by dragging it with a mouse, as a
  // finger swipes it; a drag never selects its words or clicks the button it started on
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
      // the click that ends the drag goes nowhere; one that never comes is not waited for
      const swallow = (e) => { e.stopPropagation(); e.preventDefault(); };
      bar.addEventListener("click", swallow, { capture: true, once: true });
      setTimeout(() => bar.removeEventListener("click", swallow, { capture: true }), 0);
    });
  }  // a pick kept outside the state (the Results page's dates)
  // the ⌘K palette opens pages and filters the ones that filter: a platform grid, the overview, a table
  Pie.palette.bind({
    state,
    render,
    filters: () => { const s = Pie.schema[state.table]; return s?.view === "platform" || state.table === "overview" || (!s?.view && Boolean(s?.columns?.length)); },
  });
  render();
})();
