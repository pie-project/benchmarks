window.Pie = window.Pie || {};

Pie.state = {
  table: "welcome",
  overview: { hardware: null, workload: "single", engine: "pie", heatMac: null, standMac: null, model: null, macsView: "rings", modelsView: "rings" },
  release: "main",
  query: "",
  filters: {},
  sort: null,
  // the Hide unavailable choice is kept per viewer, so it survives a reload
  hideEmpty: (() => {
    try {
      return localStorage.getItem("hideUnavailable") === "1";
    } catch {
      return false;
    }
  })(),

  reset(table, filters = {}) {
    this.table = table;
    this.filters = { ...filters };
    this.sort = null;
    this.query = "";
  },

  selected(key) {
    return this.filters[key] || [];
  },

  setFilter(key, values) {
    if (values.length) {
      this.filters[key] = values;
    } else {
      delete this.filters[key];
    }
  },

  toggleFilter(key, value) {
    const current = this.selected(key);
    this.setFilter(key, current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value]);
  },

  cycleSort(key) {
    if (this.sort?.key !== key) {
      this.sort = { key, direction: 1 };
    } else if (this.sort.direction > 0) {
      this.sort = { key, direction: -1 };
    } else {
      this.sort = null;
    }
  },
};
