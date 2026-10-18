window.Pie = window.Pie || {};

(() => {
  const tables = DB;

  const resultKeys = {
    hardware: "hardware",
    engines: "engine",
    models: "model",
    workloads: "workload",
  };

  const snapshots = tables.snapshots || {};
  // each model's platforms come from its recorded results, not from the catalog: a platform counts only where a run has a result
  {
    const measured = (row) => ["pass", "noisy"].includes(row.status);
    // a hardware's class names its platform: mac, gpu or tpu
    const names = { mac: "Mac", gpu: "GPU", tpu: "TPU" };
    const platformOf = new Map((tables.hardware || []).map((h) => [h.id, names[h.class]]));
    const seen = {};
    for (const rows of Object.values(snapshots)) {
      for (const row of rows) {
        if (!measured(row)) continue;
        const tag = platformOf.get(row.hardware);
        if (tag) (seen[row.model] = seen[row.model] || new Set()).add(tag);
      }
    }
    // the export already lists where each model was measured across every stored result (GPU and TPU runs too,
    // which the grids' rows do not carry); the rows here only add to it
    for (const model of tables.models || []) {
      const all = new Set([...(seen[model.id] || []), ...String(model.platforms || "").split(", ").filter(Boolean)]);
      model.platforms = ["Mac", "GPU", "TPU"].filter((t) => all.has(t)).join(", ");
    }
  }
  // every combination has a row; only pass and noisy ones carry numbers (older exports have no status: all measured)
  const isMeasured = (row) => !row.status || row.status === "pass" || row.status === "noisy";
  const newestTag = (tables.tags || []).find((tag) => snapshots[tag.id]?.length)?.id;

  // the suites a run measures: Targeted (the release models) and Full (every model); the picked one
  // narrows the measurement pages, the Models catalog keeps every model. An export without suites shows all.
  const SUITES = [
    { id: "targeted", label: "Targeted", title: "Targeted", detail: "Release models" },
    { id: "full", label: "Full", title: "Full", detail: "Every model" },
  ];
  const suiteModels = () => {
    const ids = (tables.suites || {})[Pie.state.suite];
    return ids ? new Set(ids) : null;
  };
  const inSuite = (model) => {
    const ids = suiteModels();
    return !ids || ids.has(model);
  };
  const ofSuite = (rows) => (suiteModels() ? rows.filter((row) => inSuite(row.model)) : rows);

  // the rows shown for a tag: every combination, with a stale marker where that tag had no run
  const snapshot = (tag) => ofSuite(snapshots[tag] || []);
  // quality scores stack per tag the same way; an export without them falls back to the flat list
  const qualitySnapshot = (tag) => ofSuite(tables.quality_snapshots ? tables.quality_snapshots[tag] || [] : tables.quality || []);

  const countResults = () => {
    for (const [table, key] of Object.entries(resultKeys)) {
      const counts = {};
      // the catalog counts every suite's runs
      for (const row of snapshots[newestTag] || []) {
        if (!isMeasured(row)) continue;
        counts[row[key]] = (counts[row[key]] || 0) + 1;
      }
      for (const row of tables[table]) {
        row._results = counts[row.id] || 0;
      }
    }
  };

  const indexById = (table) => Object.fromEntries(tables[table].map((row) => [row.id, row]));

  countResults();

  const index = {
    hardware: indexById("hardware"),
    engines: indexById("engines"),
    models: indexById("models"),
    workloads: indexById("workloads"),
  };

  const names = {
    engine: (id) => index.engines[id]?.name || id,
    model: (id) => index.models[id]?.name || id,
    workload: (id) => index.workloads[id]?.label || id,
    of(table, id) {
      if (table === "engines") return this.engine(id);
      if (table === "models") return this.model(id);
      if (table === "workloads") return this.workload(id);
      return id;
    },
  };

  Pie.store = {
    tables,
    index,
    names,
    resultKeys,

    snapshot,
    isMeasured,
    qualitySnapshot,
    inSuite,

    suites() {
      return tables.suites ? SUITES.filter((suite) => tables.suites[suite.id]) : [];
    },

    rows(table) {
      if (Pie.schema[table]?.view) return [];
      if (table === "results") return snapshot(newestTag);
      return table === "quality" ? ofSuite(tables.quality || []) : tables[table];
    },

    coverage(table, column) {
      const rows = Pie.store.rows(table).filter((row) => !column.na?.(row));
      if (!rows.length) return 0;
      return rows.filter((row) => !Pie.format.isEmpty(row[column.key])).length / rows.length;
    },
  };
})();
