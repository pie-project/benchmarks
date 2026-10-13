window.Pie = window.Pie || {};

(() => {
  const elements = {
    title: document.getElementById("toolbar-title"),
    subtitle: document.getElementById("toolbar-subtitle"),
    search: document.getElementById("search"),
    releasePicker: document.getElementById("release-picker"),
    releaseValue: document.getElementById("release-value"),
    suitePicker: document.getElementById("suite-picker"),
    metricPicker: document.getElementById("metric-picker"),
    metricValue: document.getElementById("metric-value"),
    suiteValue: document.getElementById("suite-value"),
    themeToggle: document.getElementById("theme-toggle"),
    sidebarToggle: document.getElementById("sidebar-toggle"),
  };

  Pie.toolbar = {
    elements,

    render(state, shown, total) {
      const options = Pie.query.releaseOptions();
      elements.title.textContent = Pie.schema[state.table].label;
      elements.subtitle.textContent = Pie.format.count(shown, total);
      elements.releaseValue.textContent = options.find((option) => option.id === state.release)?.label || state.release || "No runs yet";
    },

    // on every page: an export without suites has nothing to pick between
    renderSuite(state) {
      const suites = Pie.store.suites();
      elements.suitePicker.hidden = !suites.length;
      elements.suiteValue.textContent = suites.find((suite) => suite.id === state.suite)?.label || "";
    },

    clearSearch() {
      elements.search.value = "";
    },

    focusSearch() {
      elements.search.focus();
    },
  };
})();
