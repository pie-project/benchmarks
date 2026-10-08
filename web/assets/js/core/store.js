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
  // the third workload: a setup too big for the Mac, listed with no numbers
  const NO_FIT = "no-fit";
  const newestTag = (tables.tags || []).find((tag) => snapshots[tag.id]?.length)?.id;

  // the rows shown for a tag: every combination, with a stale marker where that tag had no run
  const snapshot = (tag) => snapshots[tag] || [];
  // the runs among them: the export also lists every setup nothing measured, as an empty row
  const measured = (tag) => snapshot(tag).filter((row) => !row.empty);
  // the enumerated grid: every hardware, engine, model and workload, measured or not (no-fit marks are extra)
  const grid = (tag) => snapshot(tag).filter((row) => row.workload !== NO_FIT);
  // quality scores stack per tag the same way; an export without them falls back to the flat list
  const qualitySnapshot = (tag) => (tables.quality_snapshots ? tables.quality_snapshots[tag] || [] : tables.quality || []);

  const countResults = () => {
    for (const [table, key] of Object.entries(resultKeys)) {
      const counts = {};
      for (const row of measured(newestTag)) {
        if (row.workload === NO_FIT) continue;
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
    measured,
    grid,
    NO_FIT,
    qualitySnapshot,

    rows(table) {
      if (Pie.schema[table]?.view) return [];
      return table === "results" ? snapshot(newestTag) : tables[table];
    },

    coverage(table, column) {
      const rows = Pie.store.rows(table);
      if (!rows.length) return 0;
      return rows.filter((row) => !Pie.format.isEmpty(row[column.key])).length / rows.length;
    },
  };
})();
