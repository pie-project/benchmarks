window.Pie = window.Pie || {};

Pie.state = {
  table: "board",
  platform: { metric: "decode", mode: null },
  overview: { hardware: null, workload: "raw", engine: "pie", heatMac: null, standMac: null, model: null, macsView: "rings", modelsView: "rings", bestView: "rings" },
  release: "main",
  // the models the measurement pages show: the release models (targeted) or every one (full)
  suite: "full",
  query: "",
  filters: {},
  sort: null,
  // unavailable rows are hidden; U shows them for a moment's look, and every visit starts hidden again
  hideEmpty: true,

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
