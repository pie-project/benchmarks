window.Pie = window.Pie || {};

(() => {
  const { store, format, engines } = Pie;
  const GROUPS = { release: "Releases", manual: "Manual runs" };

  // one option per tag that has rows, newest first, grouped for the picker
  // the menu offers the published releases and the newest run only; older manual runs, probes and main builds stay
  // in the data but are not offered (tags are listed newest first)
  // a tag kept apart (data/tags) is judged by its counts, so the menu never fetches every tag
  const newestRun = () => store.tables.tags.find((tag) => tag.kind !== "release" && store.count(tag.id).rows)?.id;
  // the newest pre-release (0.5.3-b5) stays on offer even when a later manual run or main build is newer
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

  // a phase of a run (Raw Decode) picks the run's rows (raw): the Workloads table's rows, one run each
  const runOf = (key, value) => (key === "workload" ? store.index.workloads[value]?.of || value : value);
  const matchesFilters = (row, filters) =>
    Object.entries(filters).every(([key, values]) => !values.length || values.some((value) => value === String(row[key]) || runOf(key, value) === String(row[key])));

  // a Raw or Speculative run as two Results rows, its Decode and its Prefill, each with its own phase's numbers
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

  const visibleRows = (state) => {
    const schema = Pie.schema[state.table];
    const source = state.table === "results" ? byPhase(store.snapshot(state.release))
      // the model slices' first-token checks list with the scores, so a slice cell's See Runs lands on them
      // each check is one run of both engines on the same prompts: a row for Pie and a matching one for the reference
      : state.table === "quality" ? [...store.qualitySnapshot(state.release), ...(store.tables.quality_parity || []).flatMap((r) => (r.ref_engine
        ? [r, { ...r, engine: r.ref_engine, version: r.ref_version, artifact: r.ref_artifact || r.artifact }] : [r]))]
      : store.rows(state.table);
    const query = state.query.trim().toLowerCase();

    // "Hide unavailable" drops the setups that cannot run (too big for the Mac, or unsupported by the engine);
    // in the Hardware catalog, the accelerators no CI run uses; in the other catalogs, the entries with no result
    const unavailable = state.table === "hardware" ? (row) => !row.runs
      : Pie.schema[state.table]?.section === "catalog" ? (row) => "_results" in row && !row._results && !row.catalog  // a model on the catalog list stays, measured or not
      : (row) => row.status === "no_fit" || row.status === "unsupported" || row.status === "no_data";
    const rows = source.filter((row) => matchesFilters(row, state.filters) && matchesSearch(row, schema.columns, query)
      && !(state.hideEmpty && unavailable(row))
      && !(["results", "quality"].includes(state.table) && Pie.dates && !Pie.dates.keeps(row)));  // the dates picked in the bar
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

    // the workloads as the Workloads table lists them, Raw and Speculative each as Decode and Prefill
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
