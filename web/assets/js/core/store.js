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
  Pie.platformOf = (hw) => (hw.class === "android" ? "android"  // a phone first: an iPhone's vendor is Apple too
    : hw.class === "mac" || hw.vendor === "Apple" ? "mac"
    : hw.backend === "xla" ? "tpu"
    : hw.vendor === "NVIDIA" ? "nvidia"
    : hw.vendor === "AMD" ? "amd"
    : hw.vendor === "Cerebras" ? "cerebras"
    : hw.class === "web" ? "web" : null);
  // each machine names its platform as the sidebar does, for the hardware table's Platform column and filter
  for (const hw of tables.hardware || []) {
    const id = Pie.platformOf(hw);
    if (id) hw.platform = Pie.schema[id]?.short || id;
  }
  // the Mobile and Browser platforms get their pages once a phone (the benchmark app, mobile/) or a browser (WebGPU in
  // Chrome) is on the site
  for (const id of ["android", "web"]) if ((tables.hardware || []).some((hw) => Pie.platformOf(hw) === id)) Pie.schema[id].section = "platforms";

  // what each workload is for: the limit it pushes against
  const GOALS = {
    raw: "How fast one request runs alone: its prompt read and its output written.",
    spec: "How fast one request writes when a small drafter guesses ahead and the model checks several tokens at once.",
    throughput: "How many output tokens per second the machine writes when many requests share it.",
    prefill_batch: "How many prompt tokens per second the machine reads when many prompts arrive at once.",
  };
  for (const w of tables.workloads || []) w.goal = GOALS[w.id] || null;
  // the requests a workload runs at once: one for a single request, else the range its benchmark sweeps (c4 ... c1024)
  for (const w of tables.workloads || []) {
    const counts = String(w.benchmark || "").split(",").map((b) => Number(b.trim().match(/^(?:c|pf)(\d+)/)?.[1])).filter(Boolean);
    w.parallel = counts.length > 1 ? `${Math.min(...counts).toLocaleString()}–${Math.max(...counts).toLocaleString()}` : String(w.concurrency ?? "");
  }
  // Raw and Speculative measure both phases of one request: its Prefill and its Decode
  const PD = { raw: "Single P/D", spec: "Speculative P/D", throughput: "Batched Decode" };
  for (const w of tables.workloads || []) if (PD[w.id]) w.label = PD[w.id];
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
  // runs whose first-token timing is known to be wrong, by engine, workload and run: there the client sent every request
  // of a round at once to an engine serving one at a time, so each time to first token counted the queue ahead of it
  // (pie PR #1011). Prefill, TTFT and whole-request latency are withheld; decode, timed between tokens, is kept
  // only the Oct 18 rows, from runs started before the fix (benchmarks #538, 2026-10-18 02:24 Pacific), were timed that way; later reruns
  // stream one request at a time and keep their prefill
  const QUEUED_TTFT = [{ engine: "vllm", workload: "raw", runs: ["0.5.3-b5"], before: "2026-10-19 00:00" }];
  // a tag's rows made ready once, as the core loads or as its own file arrives (data/tags, loaded on demand)
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
    // which the grids' rows do not carry, and the tags kept apart); the rows here only add to it
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
  // a split export (tools/split_db.py) keeps most tags apart, in data/tags/<tag>.json, each tag with its row counts;
  // a page asking for one fetches it, shows its placeholder meanwhile, and draws again once every fetch is done
  const tagOf = new Map((tables.tags || []).map((tag) => [tag.id, tag]));
  const apart = (tag) => !(tag in snapshots) && Boolean(tagOf.get(tag)?.counts);
  const loading = new Map();
  const load = (tag) => {
    if (!apart(tag) || loading.has(tag)) return;
    loading.set(tag, fetch(`data/tags/${encodeURIComponent(tag)}.json?v=${encodeURIComponent(tables.updated_at || "")}`)
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error(`data/tags/${tag}.json: ${response.status}`))))
      .catch((error) => { console.warn(error); return {}; })  // a missing file leaves the tag empty, not loading for good
      .then((part) => {
        prepare(snapshots[tag] = part.snapshots || []);
        if (tables.quality_snapshots) tables.quality_snapshots[tag] = part.quality_snapshots || [];
        loading.delete(tag);
        if (!loading.size) document.dispatchEvent(new CustomEvent("pie:refresh"));
      }));
  };
  const newestTag = (tables.tags || []).find((tag) => snapshots[tag.id]?.length || tag.counts?.all[0])?.id;

  // the suites a run measures: Targeted (the release models) and Full (every model); the picked one
  // narrows the measurement pages, the Models catalog keeps every model. An export without suites shows all.
  const SUITES = [
    { id: "targeted", label: "Targeted", title: "Targeted", detail: "Release models" },
    { id: "full", label: "Full", title: "Full", detail: "Every model" },
  ];
  // the picked suite's models as one set, built once a suite: built per row, it made every page change slow
  let suiteSet = { suite: undefined, ids: null };
  const suiteModels = () => {
    if (suiteSet.suite !== Pie.state.suite) {
      const ids = (tables.suites || {})[Pie.state.suite];
      suiteSet = { suite: Pie.state.suite, ids: ids ? new Set(ids) : null };
    }
    return suiteSet.ids;
  };
  // a model of the catalog list counts in every suite once CI has measured it, so new models reach the grids
  const catalogIds = new Set((tables.models || []).filter((m) => m.catalog).map((m) => m.id));
  const inSuite = (model) => {
    const ids = suiteModels();
    return !ids || ids.has(model) || catalogIds.has(model);
  };
  const ofSuite = (rows) => (suiteModels() ? rows.filter((row) => inSuite(row.model)) : rows);

  // the rows shown for a tag: every combination, with a stale marker where that tag had no run
  // kept per tag and suite: the release menu and the pages ask for every tag's rows on each draw
  const snapshotOf = new Map();
  const snapshot = (tag) => {
    const key = `${Pie.state.suite}\u0000${tag}`;
    if (apart(tag)) return load(tag), [];
    if (!snapshotOf.has(key)) snapshotOf.set(key, ofSuite(snapshots[tag] || []));
    return snapshotOf.get(key);
  };
  // quality scores stack per tag the same way; an export without them falls back to the flat list
  const qualitySnapshot = (tag) => (apart(tag) ? (load(tag), [])
    : ofSuite(tables.quality_snapshots ? tables.quality_snapshots[tag] || [] : tables.quality || []));
  // a tag's rows, measured rows and fresh measured rows in the picked suite, from its rows or, kept apart, its counts
  const count = (tag) => {
    if (apart(tag)) {
      const [rows, measured, runs] = tagOf.get(tag).counts[suiteModels() ? Pie.state.suite : "all"] || tagOf.get(tag).counts.all;
      return { rows, measured, runs };
    }
    const rows = snapshot(tag);
    return { rows: rows.length, measured: rows.filter(isMeasured).length, runs: rows.filter((row) => !row.stale && isMeasured(row)).length };
  };

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

  // Raw and Speculative each measure a request's two phases in one run: the Workloads table lists each phase as its
  // own row of the same benchmark; the results keep naming the run (raw, spec)
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
    // whether any result is a miniature (a datacenter model cut to fit one device): the pages showing them carry a banner
    miniatures: tables.miniatures ?? Object.values(snapshots).some((rows) => rows.some((row) => row.miniature)),
    tables,
    index,
    names,
    resultKeys,

    snapshot,
    isMeasured,
    qualitySnapshot,
    count,
    // whether a tag's own file is still on its way (or not asked for yet): its page shows the placeholder
    pending: (tag) => apart(tag),
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
