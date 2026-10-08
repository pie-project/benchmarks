(() => {
  const { state, store, query, sidebar, toolbar, popover, filters, table, preferences, overview } = Pie;
  const filterBar = document.querySelector(".filter-bar");

  // the overview's Mac and workload live in the address, so a reload or a shared link keeps them
  const readHash = () => {
    const [view, hardware, workload] = decodeURIComponent(location.hash.slice(1)).split("/");
    if (view === "overview") Object.assign(state.overview, { hardware: hardware || null, workload: workload || "single" });
  };

  const writeHash = () => {
    const hash = state.table === "overview" ? `#overview/${state.overview.hardware || ""}/${state.overview.workload}` : "";
    if (location.hash !== hash) history.replaceState(null, "", hash || location.pathname + location.search);
  };

  const ensureRelease = () => {
    const options = query.releaseOptions();
    if (!options.some((option) => option.id === state.release)) {
      state.release = (options.find((option) => option.group === "Releases") || options[0])?.id;
    }
  };

  const render = () => {
    ensureRelease();
    const isOverview = state.table === "overview";
    filterBar.hidden = isOverview;
    table.container.hidden = isOverview;
    overview.element.hidden = !isOverview;
    sidebar.render(state);
    if (isOverview) {
      const models = overview.render(state);
      toolbar.render(state, 0, 0);
      toolbar.elements.subtitle.textContent = `${models} ${models === 1 ? "model" : "models"}`;
    } else {
      const rows = query.visibleRows(state);
      if (state.table === "results") {
        // every enumerated setup of the selected release counts, measured or not; the measured ones are said apart
        toolbar.render(state, rows.length, query.resultRows(state).length);
        toolbar.elements.subtitle.textContent += ` · ${rows.filter((row) => !row.empty && row.workload !== store.NO_FIT).length} measured`;
      } else {
        toolbar.render(state, rows.length, store.rows(state.table).length);
      }
      filters.render(state);
      table.render(state, rows);
    }
    writeHash();
  };

  const navigate = (tableName, initialFilters = {}) => {
    state.reset(tableName, initialFilters);
    toolbar.clearSearch();
    popover.close();
    render();
  };

  const bindToolbar = () => {
    const { elements } = toolbar;

    elements.sidebarToggle.addEventListener("click", () => preferences.toggleSidebar());
    elements.themeToggle.addEventListener("click", () => preferences.toggleTheme());

    elements.search.addEventListener("input", (event) => {
      state.query = event.target.value;
      render();
    });

    elements.releasePicker.addEventListener("click", (event) => {
      event.stopPropagation();
      popover.open(elements.releasePicker, popover.RELEASE, state);
    });
  };

  const bindFilters = () => {
    filters.onOpen((anchor, key) => popover.open(anchor, key, state));


    filters.hideEmpty.addEventListener("click", () => {
      state.hideEmpty = !state.hideEmpty;
      render();
    });

    popover.bind();
    popover.onPick((key, value) => {
      if (key === popover.RELEASE) {
        state.release = value;
      } else if (key === popover.MAC) {
        state.overview.hardware = value;
      } else if (key === popover.WORKLOAD) {
        state.overview.workload = value;
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
    table.container.addEventListener("scroll", () => popover.close());
  };

  const bindGlobal = () => {
    sidebar.onSelect((tableName) => navigate(tableName));
    sidebar.bindLogo();

    document.addEventListener("click", () => popover.close());
    window.addEventListener("resize", () => popover.close());

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") popover.close();
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
    overview.bind(state);
    overview.onChange(render);
    overview.onOpenMac((anchor) => popover.open(anchor, popover.MAC, state));
    overview.onOpenWorkload((anchor) => popover.open(anchor, popover.WORKLOAD, state));
  };

  readHash();
  bindToolbar();
  bindOverview();
  bindFilters();
  bindTable();
  bindGlobal();
  render();
})();
