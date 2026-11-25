window.Pie = window.Pie || {};

(() => {
  const { store, format, engines } = Pie;
  const GROUPS = { release: "Releases", manual: "Manual runs" };

  const newestRun = () => store.tables.tags.find((tag) => tag.kind !== "release" && store.count(tag.id).rows)?.id;
  const BETA = /^\d+\.\d+\.\d+-b\d+$/;
  const newestBeta = () => store.tables.tags.find((tag) => BETA.test(tag.id) && store.count(tag.id).rows)?.id;
  const releaseOptions = () =>
    store.tables.tags
      .filter((tag) => store.count(tag.id).rows)
      .filter((tag) => tag.kind === "release" || tag.id === newestRun() || tag.id === newestBeta())
      .map((tag) => ({
        id: tag.id,
        label: tag.id,
        title: tag.id,
        date: tag.date ? format.date(tag.date) : "",
        group: GROUPS[tag.kind] || "Earlier runs",
        runs: store.count(tag.id).runs,
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

  const runOf = (key, value) => (key === "workload" ? store.index.workloads[value]?.of || value : value);
  const matchesFilters = (row, filters) =>
    Object.entries(filters).every(([key, values]) => !values.length || values.some((value) => value === String(row[key]) || runOf(key, value) === String(row[key])));

  const DECODE_ONLY = ["decode_tok_s", "output_tok_s", "itl_ms_p50", "itl_ms_p99"];
  const PREFILL_ONLY = ["prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99"];
  const byPhase = (rows) => rows.flatMap((row) => {
    if (!["raw", "spec"].includes(row.workload)) return [row];
    const decode = { ...row, workload: `${row.workload}_decode` };
    const prefill = { ...row, workload: `${row.workload}_prefill` };
    for (const key of PREFILL_ONLY) delete decode[key];
    for (const key of DECODE_ONLY) delete prefill[key];
    return [decode, prefill];
  });

  const compare = (key, direction) => (a, b) => {
    const emptyOrder = format.isEmpty(a[key]) - format.isEmpty(b[key]);
    if (emptyOrder) return emptyOrder;
    if (a[key] < b[key]) return -direction;
    if (a[key] > b[key]) return direction;
    return 0;
  };

  const QUALITY_MAC = "m5-max-128g";
  const qualityRows = (release) => [
    ...store.qualitySnapshot(release).map((r) => ({ ...r, hardware: r.platform || QUALITY_MAC })),
    ...(store.tables.quality_parity || []).flatMap((r) => {
      const check = { ...r, task: "parity", hardware: r.platform || QUALITY_MAC };
      return r.ref_engine ? [check, { ...check, engine: r.ref_engine, version: r.ref_version, artifact: r.ref_artifact || r.artifact }] : [check];
    }),
  ];

  const visibleRows = (state) => {
    const schema = Pie.schema[state.table];
    const source = state.table === "results" ? byPhase(store.snapshot(state.release))
      : state.table === "quality" ? qualityRows(state.release)
      : store.rows(state.table);
    const query = state.query.trim().toLowerCase();

    const unavailable = state.table === "hardware" ? (row) => !row.runs
      : Pie.schema[state.table]?.section === "catalog" ? (row) => "_results" in row && !row._results && !row.catalog
      : (row) => row.status === "no_fit" || row.status === "unsupported" || row.status === "no_data";
    const rows = source.filter((row) => matchesFilters(row, state.filters) && matchesSearch(row, schema.columns, query)
      && !(state.hideEmpty && unavailable(row))
      && !(["results", "quality"].includes(state.table) && Pie.dates && !Pie.dates.keeps(row)));
    return state.sort ? [...rows].sort(compare(state.sort.key, state.sort.direction)) : rows;
  };

  const filterValues = (table, key) => {
    const counts = {};
    for (const row of (table === "quality" ? qualityRows(Pie.state.release) : store.rows(table))) {
      if (!format.isEmpty(row[key])) {
        counts[row[key]] = (counts[row[key]] || 0) + 1;
      }
    }

    const order = (a, b) => {
      if (key === "engine") return (a !== engines.primary) - (b !== engines.primary) || a.localeCompare(b);
      if (key === "workload") return (store.index.workloads[a]?.concurrency ?? 0) - (store.index.workloads[b]?.concurrency ?? 0);
      return a.localeCompare(b);
    };

    if (key === "workload") {
      return store.tables.workloads.filter((w) => counts[w.of || w.id]).map((w) => ({ value: w.id, count: counts[w.of || w.id] }));
    }
    return Object.keys(counts).sort(order).map((value) => ({ value, count: counts[value] }));
  };

  Pie.query = {
    releaseOptions,
    visibleRows,
    filterValues,
  };
})();
