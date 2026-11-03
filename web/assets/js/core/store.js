window.Pie = window.Pie || {};

(() => {
  const tables = DB;

  const resultKeys = {
    hardware: "hardware",
    engines: "engine",
    models: "model",
    workloads: "workload",
  };

  // the platform a machine belongs to, as the sidebar groups them; the platform pages and the hardware table share it
  Pie.platformOf = (hw) => (hw.class === "mac" || hw.vendor === "Apple" ? "mac"
    : hw.backend === "xla" ? "tpu"
    : hw.vendor === "NVIDIA" ? "nvidia"
    : hw.vendor === "AMD" ? "amd"
    : hw.vendor === "Cerebras" ? "cerebras"
    : hw.class === "android" ? "android"
    : hw.class === "web" ? "web" : null);
  // each machine names its platform as the sidebar does, for the hardware table's Platform column and filter
  for (const hw of tables.hardware || []) {
    const id = Pie.platformOf(hw);
    if (id) hw.platform = Pie.schema[id]?.short || id;
  }

  // what each workload is for: the limit it pushes against
  const GOALS = {
    raw: "How fast one request runs alone: its prompt read and its output written.",
    spec: "How fast one request writes when a small drafter guesses ahead and the model checks several tokens at once.",
    throughput: "How many output tokens per second the machine writes when many requests share it.",
    prefill_batch: "How many prompt tokens per second the machine reads when many prompts arrive at once.",
  };
  for (const w of tables.workloads || []) w.goal = GOALS[w.id] || null;
  // Raw measures both phases of one request: its Prefill and its Decode
  for (const w of tables.workloads || []) if (w.id === "raw") w.label = "Raw P/D";
  // single-request workloads first, then the batched ones
  const ORDER = ["raw", "spec", "throughput", "prefill_batch"];
  const rank = (w) => (ORDER.includes(w.id) ? ORDER.indexOf(w.id) : ORDER.length);
  (tables.workloads || []).sort((a, b) => rank(a) - rank(b));
  // whether a model can speculate: it has a drafter
  for (const m of tables.models || []) m.speculation = m.draft === "true" ? "Yes" : "No";

  // what does not fit, worked out for every machine and model, run or not: the weights times 1.25 against the
  // machine's memory. A Mac runs the MLX build (the model's own needs figure); a GPU runs the weights a recorded misfit
  // names, else the model's own release
  const noFit = (tables.no_fit ||= {});
  const engines = (tables.engines || []).map((e) => e.id);
  const known = {};
  for (const hw of tables.hardware || []) {
    if (Pie.platformOf(hw) === "mac") continue;
    // only a misfit the GPU engines recorded names the weights a GPU runs; the catalog's other cards carry the Mac builds'
    for (const [model, by] of Object.entries(noFit[hw.id] || {})) if (by.vllm || by.sglang) known[model] ??= by.vllm || by.sglang;
  }
  for (const hw of tables.hardware || []) {
    const memory = hw.memory_gib;
    if (!memory) continue;
    const mac = Pie.platformOf(hw) === "mac";
    const holds = memory;
    for (const m of tables.models || []) {
      if (noFit[hw.id]?.[m.id]) continue;
      // the GPU runs the model's own release: MXFP4 at the 4-bit size, FP8 at a byte a weight, else 16 bits
      const bytes = /mxfp4/.test(m.schemes) ? null : /fp8/.test(m.schemes) ? 1 : 2;
      const needs = mac ? m.needs_gib : known[m.id] ?? (bytes ? m.params_b && m.params_b * bytes * 1e9 / 2 ** 30 * 1.25 : m.needs_gib);
      if (needs && needs > holds) (noFit[hw.id] ||= {})[m.id] = Object.fromEntries(engines.map((e) => [e, Math.round(needs * 10) / 10]));
    }
  }

  const snapshots = tables.snapshots || {};
  // each result names its machine's platform, for the Results table's Platform filter
  const platformByHardware = Object.fromEntries((tables.hardware || []).map((hw) => [hw.id, hw.platform]));
  for (const rows of Object.values(snapshots)) for (const row of rows) row.platform = platformByHardware[row.hardware] || null;
  // runs whose first-token timing is known to be wrong, by engine, workload and run: there the client sent every request
  // of a round at once to an engine serving one at a time, so each time to first token counted the queue ahead of it
  // (pie PR #1011). Prefill, TTFT and whole-request latency are withheld; decode, timed between tokens, is kept
  // only the Oct 18 rows, from runs started before the fix (benchmarks #538, 2026-10-18 02:24 Pacific), were timed that way; later reruns
  // stream one request at a time and keep their prefill
  const QUEUED_TTFT = [{ engine: "vllm", workload: "raw", runs: ["0.5.3-b5"], before: "2026-10-19 00:00" }];
  for (const rows of Object.values(snapshots)) {
    for (const row of rows) {
      const bad = QUEUED_TTFT.some((q) => q.engine === row.engine && q.workload === row.workload && q.runs.includes(row.release)
        && (row.measured || "") < q.before);
      if (!bad) continue;
      for (const key of ["prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99", "latency_ms_p50", "latency_ms_p99"]) row[key] = null;
      row.note = "Prefill and time to first token withheld: this run timed each request from a queue of the round's requests, not its own prefill";
    }
  }
  // each model's platforms come from its recorded results, not from the catalog: a platform counts only where a run has a result
  {
    const measured = (row) => ["pass", "noisy"].includes(row.status);
    // a hardware's class names its platform: mac, gpu or tpu, and a GPU on ROCm is AMD's, apart from NVIDIA's ("GPU")
    const names = { mac: "Mac", gpu: "GPU", tpu: "TPU", wafer: "Wafer" };
    const platformOf = new Map((tables.hardware || []).map((h) => [h.id, h.class === "gpu" && h.backend === "rocm" ? "AMD" : names[h.class]]));
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
      // its layer count, from its config.json as the bounds read it
      model.layers = Pie.architectures?.[model.id]?.layers ?? model.layers ?? null;  // or the catalog's stated count
      const all = new Set([...(seen[model.id] || []), ...String(model.platforms || "").split(", ").filter(Boolean)]);
      model.platforms = ["Mac", "GPU", "TPU", "AMD", "Wafer"].filter((t) => all.has(t)).join(", ");
    }
  }
  // every combination has a row; only pass and noisy ones carry numbers (older exports have no status: all measured)
  const isMeasured = (row) => !row.status || row.status === "pass" || row.status === "noisy";
  // on a local preview only: a result measured today or later, so new CI data stands out while it lands
  const local = ["localhost", "127.0.0.1"].includes(location.hostname);
  const today = new Date().toLocaleDateString("sv-SE");  // YYYY-MM-DD, as "measured" begins
  Pie.isNew = (row) => local && Boolean(row?.measured) && String(row.measured).slice(0, 10) >= today;
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
  // a model of the catalog list counts in every suite once CI has measured it, so new models reach the grids
  const catalogIds = new Set((tables.models || []).filter((m) => m.catalog).map((m) => m.id));
  const inSuite = (model) => {
    const ids = suiteModels();
    return !ids || ids.has(model) || catalogIds.has(model);
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
    // whether any result is a miniature (a datacenter model cut to fit one device): the pages showing them carry a banner
    miniatures: Object.values(snapshots).some((rows) => rows.some((row) => row.miniature)),
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
