window.Pie = window.Pie || {};

(() => {
  const { store, format, engines } = Pie;
  const GROUPS = { release: "Releases", manual: "Manual runs" };

  // one option per tag that has rows, newest first, grouped for the picker
  // the menu offers the published releases and the newest run only; older manual runs, probes and main builds stay
  // in the data but are not offered (tags are listed newest first)
  const newestRun = () => store.tables.tags.find((tag) => tag.kind !== "release" && store.snapshot(tag.id).length)?.id;
  const releaseOptions = () =>
    store.tables.tags
      .filter((tag) => store.snapshot(tag.id).length)
      .filter((tag) => tag.kind === "release" || tag.id === newestRun())
      .map((tag) => ({
        id: tag.id,
        label: tag.id,
        title: tag.id,
        date: tag.date ? format.date(tag.date) : "",
        group: GROUPS[tag.kind] || "Earlier runs",
        runs: store.snapshot(tag.id).filter((row) => !row.stale && store.isMeasured(row)).length,
      }));

  const matchesSearch = (row, columns, query) => {
    if (!query) return true;
    return columns.some((column) => {
      const value = row[column.key];
      if (format.isEmpty(value)) return false;
      const text = column.type === "reference" ? store.names.of(column.table, value) : value;
      return String(text).toLowerCase().includes(query);
    });
  };

  const matchesFilters = (row, filters) =>
    Object.entries(filters).every(([key, values]) => !values.length || values.includes(String(row[key])));

  const compare = (key, direction) => (a, b) => {
    const emptyOrder = format.isEmpty(a[key]) - format.isEmpty(b[key]);
    if (emptyOrder) return emptyOrder;
    if (a[key] < b[key]) return -direction;
    if (a[key] > b[key]) return direction;
    return 0;
  };

  const visibleRows = (state) => {
    const schema = Pie.schema[state.table];
    const source = state.table === "results" ? store.snapshot(state.release)
      : state.table === "quality" ? store.qualitySnapshot(state.release)
      : store.rows(state.table);
    const query = state.query.trim().toLowerCase();

    // "Hide unavailable" drops the setups that cannot run (too big for the Mac, or unsupported by the engine);
    // in the Hardware catalog, the accelerators no CI run uses; in the other catalogs, the entries with no result
    const unavailable = state.table === "hardware" ? (row) => !row.runs
      : Pie.schema[state.table]?.section === "catalog" ? (row) => "_results" in row && !row._results
      : (row) => row.status === "no_fit" || row.status === "unsupported" || row.status === "no_data";
    const rows = source.filter((row) => matchesFilters(row, state.filters) && matchesSearch(row, schema.columns, query)
      && !(state.hideEmpty && unavailable(row)));
    return state.sort ? [...rows].sort(compare(state.sort.key, state.sort.direction)) : rows;
  };

  const filterValues = (table, key) => {
    const counts = {};
    for (const row of store.rows(table)) {
      if (!format.isEmpty(row[key])) {
        counts[row[key]] = (counts[row[key]] || 0) + 1;
      }
    }

    const order = (a, b) => {
      if (key === "engine") return (a !== engines.primary) - (b !== engines.primary) || a.localeCompare(b);
      if (key === "workload") return (store.index.workloads[a]?.concurrency ?? 0) - (store.index.workloads[b]?.concurrency ?? 0);
      return a.localeCompare(b);
    };

    return Object.keys(counts).sort(order).map((value) => ({ value, count: counts[value] }));
  };

  Pie.query = {
    releaseOptions,
    visibleRows,
    filterValues,
  };
})();
