window.Pie = window.Pie || {};

(() => {
  const tables = DB;

  const resultKeys = {
    hardware: "hardware",
    engines: "engine",
    models: "model",
    workloads: "workload",
  };

  Pie.hiddenPlatforms = new Set();
  Pie.platformOf = (hw) => { const p = platformOfAll(hw); return Pie.hiddenPlatforms.has(p) ? null : p; };
  Pie.platformOfAll = (hw) => platformOfAll(hw);
  const platformOfAll = (hw) => (hw.class === "android" ? "android"
    : hw.class === "mac" || hw.vendor === "Apple" ? "mac"
    : hw.class === "windows" ? "windows"
    : hw.backend === "xla" ? "tpu"
    : hw.vendor === "NVIDIA" ? "nvidia"
    : hw.vendor === "AMD" ? "amd"
    : hw.vendor === "Cerebras" ? "cerebras"
    : hw.class === "web" ? "web" : null);
  for (const hw of tables.hardware || []) {
    const id = platformOfAll(hw);
    if (id) hw.platform = Pie.schema[id]?.short || id;
  }
  for (const id of ["android", "web"]) if ((tables.hardware || []).some((hw) => Pie.platformOf(hw) === id)) Pie.schema[id].section = "platforms";

  const GOALS = {
    raw: "How fast one request runs alone: its prompt read and its output written.",
    spec: "How fast one request writes when a small drafter guesses ahead and the model checks several tokens at once.",
    throughput: "How many output tokens per second the machine writes when many requests share it.",
    prefill_batch: "How many prompt tokens per second the machine reads when many prompts arrive at once.",
  };
  for (const w of tables.workloads || []) w.goal = GOALS[w.id] || null;
  for (const w of tables.workloads || []) {
    const counts = String(w.benchmark || "").split(",").map((b) => Number(b.trim().match(/^(?:c|pf)(\d+)/)?.[1])).filter(Boolean);
    w.parallel = counts.length > 1 ? `${Math.min(...counts).toLocaleString()}–${Math.max(...counts).toLocaleString()}` : String(w.concurrency ?? "");
  }
  const PD = { raw: "Single P/D", spec: "Speculative P/D", throughput: "Batched Decode" };
  for (const w of tables.workloads || []) if (PD[w.id]) w.label = PD[w.id];
  const ORDER = ["raw", "spec", "throughput", "prefill_batch"];
  const rank = (w) => (ORDER.includes(w.id) ? ORDER.indexOf(w.id) : ORDER.length);
  (tables.workloads || []).sort((a, b) => rank(a) - rank(b));
  for (const m of tables.models || []) m.speculation = m.draft === "true" ? "Yes" : "No";

  const noFit = (tables.no_fit ||= {});
  const engines = (tables.engines || []).map((e) => e.id);
  const known = {};
  for (const hw of tables.hardware || []) {
    if (Pie.platformOf(hw) === "mac") continue;
    for (const [model, by] of Object.entries(noFit[hw.id] || {})) if (by.vllm || by.sglang) known[model] ??= by.vllm || by.sglang;
  }
  for (const hw of tables.hardware || []) {
    const memory = hw.memory_gib;
    if (!memory) continue;
    const mac = ["mac", "web", "windows"].includes(Pie.platformOf(hw));
    const holds = memory;
    for (const m of tables.models || []) {
      if (noFit[hw.id]?.[m.id]) continue;
      const bytes = /mxfp4/.test(m.schemes) ? null : /fp8/.test(m.schemes) ? 1 : 2;
      const needs = mac ? m.needs_gib : known[m.id] ?? (bytes ? m.params_b && m.params_b * bytes * 1e9 / 2 ** 30 * 1.25 : m.needs_gib);
      if (needs && needs > holds) (noFit[hw.id] ||= {})[m.id] = Object.fromEntries(engines.map((e) => [e, Math.round(needs * 10) / 10]));
    }
  }

  const snapshots = tables.snapshots || {};
  const platformByHardware = Object.fromEntries((tables.hardware || []).map((hw) => [hw.id, hw.platform]));
  const QUEUED_TTFT = [{ engine: "vllm", workload: "raw", runs: ["0.5.3-b5"], before: "2026-10-19 00:00" }];
  const prepare = (rows) => {
    for (const row of rows) row.platform = platformByHardware[row.hardware] || null;
    for (const row of rows) {
      const bad = QUEUED_TTFT.some((q) => q.engine === row.engine && q.workload === row.workload && q.runs.includes(row.release)
        && (row.measured || "") < q.before);
      if (!bad) continue;
      for (const key of ["prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99", "latency_ms_p50", "latency_ms_p99"]) row[key] = null;
      row.note = "Prefill and time to first token withheld: this run timed each request from a queue of the round's requests, not its own prefill";
    }
  };
  for (const rows of Object.values(snapshots)) prepare(rows);
  {
    const measured = (row) => ["pass", "noisy"].includes(row.status);
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
    for (const model of tables.models || []) {
      model.layers = Pie.architectures?.[model.id]?.layers ?? model.layers ?? null;
      const all = new Set([...(seen[model.id] || []), ...String(model.platforms || "").split(", ").filter(Boolean)]);
      model.platforms = ["Mac", "Windows", "GPU", "TPU", "AMD", "Wafer"].filter((t) => all.has(t)).join(", ");
    }
  }
  const isMeasured = (row) => !row.status || row.status === "pass" || row.status === "noisy";
  const local = ["localhost", "127.0.0.1"].includes(location.hostname);
  const today = new Date().toLocaleDateString("sv-SE");
  Pie.isNew = (row) => local && Boolean(row?.measured) && String(row.measured).slice(0, 10) >= today;
  const newestTag = (tables.tags || []).find((tag) => snapshots[tag.id]?.length || tag.counts?.all[0])?.id;

  const SUITES = [
    { id: "targeted", label: "Targeted", title: "Targeted", detail: "Release models" },
    { id: "full", label: "Full", title: "Full", detail: "Every model" },
  ];
  let suiteSet = { suite: undefined, ids: null };
  const suiteModels = () => {
    if (suiteSet.suite !== Pie.state.suite) {
      const ids = (tables.suites || {})[Pie.state.suite];
      suiteSet = { suite: Pie.state.suite, ids: ids ? new Set(ids) : null };
    }
    return suiteSet.ids;
  };
  const catalogIds = new Set((tables.models || []).filter((m) => m.catalog).map((m) => m.id));
  const inSuite = (model) => {
    const ids = suiteModels();
    return !ids || ids.has(model) || catalogIds.has(model);
  };
  const ofSuite = (rows) => (suiteModels() ? rows.filter((row) => inSuite(row.model)) : rows);

  const snapshotOf = new Map();
  const snapshot = (tag) => {
    const key = `${Pie.state.suite}\u0000${tag}`;
    if (!snapshotOf.has(key)) snapshotOf.set(key, ofSuite(snapshots[tag] || []));
    return snapshotOf.get(key);
  };
  const qualitySnapshot = (tag) => ofSuite(tables.quality_snapshots ? tables.quality_snapshots[tag] || [] : tables.quality || []);
  const count = (tag) => {
    const rows = snapshot(tag);
    return { rows: rows.length, measured: rows.filter(isMeasured).length, runs: rows.filter((row) => !row.stale && isMeasured(row)).length };
  };

  const countResults = () => {
    for (const [table, key] of Object.entries(resultKeys)) {
      const counts = {};
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

  const runs = indexById("workloads");
  const PHASES = {
    raw: [
      ["decode", "Single Decode", "How fast one request writes its output, alone."],
      ["prefill", "Single Prefill", "How fast one request reads its prompt, alone."],
    ],
    spec: [
      ["decode", "Speculative Decode", "How fast one request writes when a small drafter guesses ahead and the model checks several tokens at once."],
      ["prefill", "Speculative Prefill", "How fast one request reads its prompt with the drafter loaded."],
    ],
  };
  tables.workloads = (tables.workloads || []).flatMap((w) => (PHASES[w.id]
    ? PHASES[w.id].map(([phase, label, goal]) => ({ ...w, id: `${w.id}_${phase}`, of: w.id, phase, label, goal }))
    : [w]));

  const index = {
    hardware: indexById("hardware"),
    engines: indexById("engines"),
    models: indexById("models"),
    workloads: { ...runs, ...indexById("workloads") },
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
    miniatures: tables.miniatures ?? Object.values(snapshots).some((rows) => rows.some((row) => row.miniature)),
    tables,
    index,
    names,
    resultKeys,

    snapshot,
    isMeasured,
    qualitySnapshot,
    count,
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
