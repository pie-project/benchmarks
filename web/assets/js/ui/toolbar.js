window.Pie = window.Pie || {};

(() => {
  const elements = {
    title: document.getElementById("toolbar-title"),
    subtitle: document.getElementById("toolbar-subtitle"),
    search: document.getElementById("search"),
    searchCancel: document.getElementById("search-cancel"),
    releasePicker: document.getElementById("release-picker"),
    releaseValue: document.getElementById("release-value"),
    suitePicker: document.getElementById("suite-picker"),
    metricPicker: document.getElementById("metric-picker"),
    metricValue: document.getElementById("metric-value"),
    suiteValue: document.getElementById("suite-value"),
    viewPicker: document.getElementById("view-picker"),
    viewValue: document.getElementById("view-value"),
    themeToggle: document.getElementById("theme-toggle"),
    sidebarToggle: document.getElementById("sidebar-toggle"),
    nav: document.getElementById("nav-buttons"),
    back: document.getElementById("back-button"),
    forward: document.getElementById("forward-button"),
  };

  const root = document.documentElement;

  // the compact toolbar's one picker names the release and the suite together
  const releaseLabel = (state) => Pie.query.releaseOptions().find((option) => option.id === state.release)?.label || state.release || "No runs yet";
  const renderView = (state) => {
    const parts = [releaseLabel(state), elements.suitePicker.hidden ? "" : elements.suiteValue.textContent];
    elements.viewValue.textContent = parts.filter(Boolean).join(" · ");
  };

  Pie.toolbar = {
    elements,

    render(state, shown, total) {
      elements.title.textContent = Pie.schema[state.table].label;
      elements.subtitle.textContent = Pie.format.count(shown, total);
      this.renderRelease(state);
    },

    // the button names the run, Latest or its day, on every page, the table-less ones too; the tag is in its tooltip and menu
    renderRelease(state) {
      const options = Pie.query.releaseOptions();
      const run = options.find((option) => option.id === state.release);
      const day = run?.date ? String(run.date).replace(/,?\s*\d{1,2}:\d{2}.*$/, "") : "";
      // the newest run (the list is newest first) is simply Latest; an older one is named by its day
      elements.releaseValue.textContent = run && run === options[0] ? "Latest" : day || releaseLabel(state);
      elements.releasePicker.title = releaseLabel(state);
    },

    // the suite picker stays hidden: the site shows the Full suite only
    renderSuite(state) {
      const suites = Pie.store.suites();
      elements.suitePicker.hidden = true;  // no suite to pick: the site shows Full
      elements.suiteValue.textContent = suites.find((suite) => suite.id === state.suite)?.label || "";
      renderView(state);
    },

    clearSearch() {
      elements.search.value = "";
      this.showSearch(false);
    },

    // on a phone the search is an icon; it opens into a field across the bar with Cancel beside it, as in iOS
    showSearch(open) {
      if (open) {
        root.dataset.search = "open";
      } else {
        delete root.dataset.search;
      }
    },

    focusSearch() {
      elements.search.focus();
    },
  };
})();
