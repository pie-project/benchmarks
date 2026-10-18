window.Pie = window.Pie || {};

// A platform page: its machines down, the suite's models across, each cell the picked engine against the
// fastest other engine on that machine (single request). Hovering a cell lists every engine's number.
(() => {
  const element = document.getElementById("platform");
  const tooltip = document.getElementById("chart-tooltip");
  const esc = (s) => Pie.format.escape(String(s ?? ""));
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Decode", detail: "Tokens per second while answering", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Prefill", detail: "Tokens per second reading the prompt", key: "prefill_tok_s", unit: "tok/s", higher: true },
  ];
  // the setups, picked from a pop-up in the bar and grouped by the kernel they measure: decode and prefill
  // run different kernels with different bottlenecks. Each group opens on its raw row (speculation off), held against
  // the hardware limit; the features under it are only those that change that phase, each shown as its gain over raw
  const MODES = [
    { id: "decode", group: "Decode", label: "Raw Decode", icon: "M2 8h8M7 5l3 3-3 3M13 3v10", detail: "single request, speculation off", workload: "raw", metric: METRICS[0], limit: true },
    { id: "batching", group: "Decode", label: "Batched Decode", icon: "M8 2.5l6 3-6 3-6-3zM2 8.5l6 3 6-3M2 11.5l6 3 6-3", detail: "32 requests at once", workload: "throughput", metric: { id: "throughput", label: "Throughput", key: "output_tok_s", unit: "tok/s", higher: true } },
    { id: "prefill", group: "Prefill", label: "Raw Prefill", icon: "M3 4.5h10M3 8h10M3 11.5h6", detail: "single request, speculation off", workload: "raw", metric: METRICS[1], limit: true },
  ];
  let onChange = () => {};

  // the platforms machines belong to, in the order the page lists them; Apple's logo is the simple-icons glyph (CC0)
  const PLATFORMS = [
    { id: "mac", label: "Apple Silicon", sub: "Metal", has: (hw) => Pie.platformOf(hw) === "mac" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", has: (hw) => Pie.platformOf(hw) === "tpu" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", has: (hw) => Pie.platformOf(hw) === "nvidia" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", has: (hw) => Pie.platformOf(hw) === "amd" },
    { id: "cerebras", label: "Cerebras", sub: "Wafer-scale", has: (hw) => Pie.platformOf(hw) === "cerebras" },
    { id: "android", label: "Android", sub: "Mobile GPU", has: (hw) => Pie.platformOf(hw) === "android" },
    { id: "web", label: "WebGPU", sub: "In-browser", has: (hw) => Pie.platformOf(hw) === "web" },
  ];
  const platformOf = (hw) => PLATFORMS.find((p) => p.has(hw));
  // a platform's mark is the sidebar's: the same tinted squircle and glyph wherever it appears
  const badgeOf = (id) => `<span class="sidebar-glyph" style="--tint: ${Pie.schema[id]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(id)}</span>`;

  // a model's maker as a small app icon: its logo on a white tile (logos from LobeHub's icon set, MIT)
  const MAKERS = [
    { test: /^qwen/, name: "Alibaba", logo: "qwen" },
    { test: /^gemma/, name: "Google", logo: "gemma" },
    { test: /^gpt_oss/, name: "OpenAI", logo: "openai" },
    { test: /^muse/, name: "Meta", logo: "meta" },
  ];
  const makerOf = (model) => MAKERS.find((m) => m.test.test(Pie.store.index.models[model]?.family || "")) || { name: "", logo: "" };
  const badge = (maker) => `<span class="model-badge" aria-hidden="true">${maker.logo ? `<img src="assets/img/models/${maker.logo}.svg" alt="">` : ""}</span>`;

  const chipName = (id) => String(Pie.store.index.hardware[id]?.name || id).replace(/^Apple\s+/, "");
  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    return hw ? `${chipName(id)}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}` : id;
  };
  // "48 GB · 20-core GPU · 273 GB/s" on a quiet second line under the chip, the specs that set LLM speed; the CPU waits for the hover
  // a machine's row says only what tells it from its namesakes, its memory, as Apple lists a Mac; the full spec sheet
  // shows when the pointer rests on it, and grows as the catalog does (interconnect, power, more) without crowding the row
  const specOf = (hw) => (hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : "");
  const LINKS = { uma: "Unified memory", nvlink: "NVLink", pcie: "PCIe", tb5: "Thunderbolt 5" };
  const specSheet = (hw) => {
    const rows = [
      ["Memory", hw.memory_gib && `${hw.memory_gib} GB`],
      ["Bandwidth", hw.bandwidth_gbs && `${hw.bandwidth_gbs} GB/s`],
      ["GPU", hw.gpu_cores && `${hw.gpu_cores} cores`],
      ["CPU", hw.cpu_cores && `${hw.cpu_cores} cores`],
      ["Compute", hw.tflops_fp16 && `${hw.tflops_fp16} TFLOPS fp16`],
      ["Devices", hw.count > 1 && `${hw.count}`],
      ["Interconnect", hw.interconnect && (LINKS[hw.interconnect] || hw.interconnect)],
      ["Power", hw.power_w && `${hw.power_w} W at full load`],
    ].filter(([, v]) => v);
    return `<div class="tip-title">${esc(hw.name || hw.id)}</div><div class="spec-rows">${rows.map(([k, v]) => `<div class="spec-row"><span>${esc(k)}</span><span>${esc(v)}</span></div>`).join("")}</div>`;
  };
  const value = (n, unit) => {
    const v = n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
    return `${v} ${unit}`;
  };
  const EVEN = 0.045;  // under 5%, as the cell rounds it, the engines are even: run-to-run spread, not a result
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/><path d="M3.8 12.2 12.2 3.8"/></svg>';
  const signed = (p) => {
    const pct = Math.round(p * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  // pie's advantage over the best other engine: a speed ratio, or the inverse for a time
  // Compare: "engines" shows each engine against the best other engine; "ceiling", named Roofline, shows each engine's share
  // of its theoretical bound, the card drawing the roofline. The last choice is kept per browser
  const COMPARES = { engines: "Engines", ceiling: "Roofline" };
  let compare = (() => {
    try {
      const saved = localStorage.getItem("platformCompare");
      return saved === "roofline" ? "ceiling" : COMPARES[saved] ? saved : "engines";
    } catch {
      return "engines";
    }
  })();
  // the theoretical bound for a cell: Raw's hardware limit, or for batched decode the lower of compute and bandwidth
  const boundOf = (mac, model, mode, metric, pie) => {
    if (mode.limit) return Pie.ceiling?.(pie, metric.id) || null;
    if (mode.workload !== "throughput") return null;
    return batchedBound(mac, model, pie?.scheme);
  };
  // batched decode: the lower of two bounds, in output tokens per second. Compute: peak FLOPS over the active parameters,
  // shared with the prompt tokens each request prefills at the same cost, so only output / (prompt + output) of it is output.
  // Bandwidth: each step reads the weights once, so the batch's tokens per second are batch x bandwidth / weight bytes.
  function batchedBound(mac, model, scheme) {
    // the architecture-based bound (methodology.js), the same one the Methods page explains
    return Pie.batchedCeiling?.(mac, model, scheme) || null;
  }
  const cell = (rows, metric, base) => {
    const pie = rows.find((r) => r.engine === base && r[metric.key]);
    const others = rows.filter((r) => r.engine !== base && r[metric.key]);
    if (!pie || !others.length) return null;
    const best = others.reduce((a, b) => ((metric.higher ? b[metric.key] > a[metric.key] : b[metric.key] < a[metric.key]) ? b : a));
    const gain = metric.higher ? pie[metric.key] / best[metric.key] - 1 : best[metric.key] / pie[metric.key] - 1;
    return { pie, best, gain, all: [pie, ...others] };
  };

  // each engine's share of the hardware limit, against its own weights (Raw only: a drafter skips the passes the limit counts)
  const share = (r, metric) => {
    const own = Pie.ceiling?.(r, metric.id);
    return own ? r[metric.key] / own.tps : null;
  };
  // what a feature adds: the engine's number over its raw row on the same machine and model
  const overRaw = (r, metric, raw) => {
    const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine);
    const key = metric.id === "throughput" ? "output_tok_s" : metric.key;
    return plain?.[key] ? r[metric.key] / plain[key] : null;
  };
  const times = (x) => `${x >= 10 ? Math.round(x) : x.toFixed(1)}×`;

  // under the comparison, a quiet second line on the feature views: what the feature adds over raw
  const subline = (c, metric, mode, raw) => {
    // Raw cells hold one number; how near the hardware limit each engine runs is in the hover card
    if (mode.limit) return "";
    const gain = overRaw(c.pie, metric, raw);
    // a row that did not speculate reads its own raw speed: nothing to add
    return "";  // the multiplier under the percentage is not shown
  };

  // a hover card: the setup as a title, every engine on its own aligned row (fastest first, pie in blue), one closing line
  const card = (title, sub, lines = [], foot = "") => `
    ${title ? `<div class="tip-title">${esc(title)}</div>` : ""}${sub ? `<div class="tip-sub">${esc(sub)}</div>` : ""}
    ${lines.length ? `<div class="tip-rows">${lines.join("")}</div>` : ""}${foot ? `<div class="tip-foot">${esc(foot)}</div>` : ""}`;
  // the day each engine's number was taken, from a release or a manual run alike: "Oct 13"
  const day = (r) => {
    const when = r.measured || r.stale?.measured || "";
    if (!when) return "";
    const [y, m, d] = when.slice(0, 10).split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  };
  const tip = (mac, model, metric, c, mode, raw) => {
    const limit = mode.limit;
    const ceiling = limit ? Pie.ceiling?.(c.pie, metric.id) : null;
    const batchBound = !limit && mode.workload === "throughput" ? batchedBound(mac, model, c.pie.scheme) : null;
    const batchPeak = batchBound ? batchBound.tps : null;
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    // Engines compares the engines only; Roofline adds each one's share of the bound, the bounds and the chart
    const roofline = compare === "ceiling";
    const lines = order.map((r, i) => {
      // Raw: each engine's share of the hardware limit; the others: what the feature adds over its raw row
      const extra = !roofline ? null : limit ? share(r, metric) : batchPeak ? r[metric.key] / batchPeak : overRaw(r, metric, raw);
      const note = extra === null ? "" : limit || batchPeak ? `${Math.round(extra * 100)}%` : times(extra);
      return `<div class="tip-row${r === c.pie ? " is-pie" : ""}">
      <span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}${i === 0 ? '<span class="tip-tag">Fastest</span>' : ""}</span>
      <span class="tip-value">${esc(value(r[metric.key], metric.unit))}${roofline ? `<span class="tip-share">${note}</span>` : ""}</span><span class="tip-when">${esc(day(r))}</span></div>`;
    });
    // the cell's row and column already name the setup, and the bar above the metric: the card is only the engines
    // the hardware limit closes the list as one more row, aligned with the engines': its speed at 100%, and a tag for
    // what sets it (bandwidth, compute, or the interconnect between devices), as a table's summary row reads
    // both bounds are listed, lower first; the lower one is the limit, so only it carries the 100% the engines are measured against
    // one group under one rule, as a summary reads: the gauge marks the binding row only, the other row is plain and dimmed
    const limitRow = (name, tps, binds) => `<div class="tip-row is-limit${binds ? "" : " is-slack"}">
      ${binds ? '<svg class="tip-limit-mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 11.5a5.5 5.5 0 1 1 11 0M8 11.5l2.6-3.4"/></svg>' : "<span></span>"}<span class="tip-name" title="${binds ? "What sets the limit" : "Not the limit: the other bound is lower"}">${name} bound</span>
      <span class="tip-value">${esc(value(tps, metric.unit))}</span><span class="tip-when"></span></div>`;
    const bounds = (b) => [["Bandwidth", b.bandwidth], ["Compute", b.compute]].filter(([, tps]) => tps).sort((x, y) => x[1] - y[1]);
    // Roofline complements Engines: no engine list, only the bounds and the chart, the engines as dots in their colours
    const both = roofline && (ceiling || batchBound);
    if (both) {
      // both bounds side by side, as a pair of stats: a small label over each number, memory first as the chart reads
      // left to right; the lower one is the limit, bright, the other dimmed
      // the two bounds as rows, the one that sets the limit first with the gauge, the other dimmed under it
      const head = `<div class="tip-rows">${bounds(both).map(([name, tps], i) => limitRow(name, tps, i === 0)).join("")}</div>`;
      return `<div class="rf-card">${head}${roofCard(order.map((r) => roofPoint(r, mode, metric)).filter(Boolean))}</div>`;
    }
    return card("", "", lines);
  };

  // a result on the roofline model (Williams et al., 2009): its pass's arithmetic intensity, the FLOPs it does per byte
  // it reads, and the FLOPs a second it achieved; and its machine's roof, memory bandwidth and peak FLOPS
  const roofPoint = (r, mode, metric) => {
    if (!r?.[metric.key]) return null;
    if (mode.limit) {
      const c = Pie.ceiling?.(r, metric.id);
      if (!c) return null;
      const flops = c.parts.mathS * c.parts.tflops * 1e12;
      const bytes = (c.parts.weightGB + c.parts.cacheGB) * 1e9;
      return { r, ai: flops / bytes, achieved: (r[metric.key] / c.parts.tokens) * flops, bw: c.parts.bw, peak: c.parts.tflops };
    }
    const b = Pie.batchedCeiling?.(r.hardware, r.model, r.scheme);
    const hw = Pie.store.index.hardware[r.hardware];
    if (!b || !hw) return null;
    const flops = b.parts.mathS * hw.tflops_fp16 * 1e12;
    const bytes = b.parts.readS * hw.bandwidth_gbs * 1e9;
    return { r, ai: flops / bytes, achieved: (r[metric.key] / b.parts.requests) * flops, bw: hw.bandwidth_gbs, peak: hw.tflops_fp16 };
  };

  // the card's roofline, a picture rather than a plot: the roof one line over a soft fade, the knee a ring named
  // beside it, each engine a dot in its own colour, pie on top; no axes, since the shape is the point
  const roofCard = (found) => {
    let points = found;
    if (!points.length) return "";
    const { bw, peak } = points[0];
    const knee = (peak * 1e12) / (bw * 1e9);
    // one model, one workload: every engine stands at the same place across, pie's (the first engine's when pie has
    // none); a dot's height is its share of its own bound, so it matches the percentage the grid shows for it
    const own = points.find((p) => p.r.engine === Pie.engines.primary) || points[0];
    const ai = own.ai;
    const shareOf = (p) => p.achieved / Math.min(p.bw * 1e9 * p.ai, p.peak * 1e12);
    points = points.map((p) => ({ ...p, ai, achieved: shareOf(p) * Math.min(bw * 1e9 * ai, peak * 1e12) }));
    const ais = [ai];
    // both axes linear. Across, a window around the dots; up, always from zero to just over the roof, so a dot's height
    // is its share of the bound. The knee and the compute roof show only when the window reaches them
    const aiLo = Math.min(...ais), aiHi = Math.max(...ais);
    const X0 = aiLo * 0.6;
    const X1 = aiHi * 1.4;
    // a dot's distance below the roof is its share of it: at 55% it sits about halfway between the floor and the roof
    const Y1 = Math.max(Math.min(bw * 1e9 * X1, peak * 1e12), ...points.map((p) => p.achieved)) * 1.06;
    const Y0 = 0;
    const W = 196, H = 80, L = 2, R = 2, T = 14, B = 2;  // about the card's own width, so the dots and the name keep their size
    const x = (v) => L + ((v - X0) / (X1 - X0)) * (W - L - R);
    const y = (v) => T + (1 - (v - Y0) / (Y1 - Y0)) * (H - T - B);
    const roof = (v) => Math.min(bw * 1e9 * v, peak * 1e12);
    const start = X0;
    // every dot exactly where its result is, never nudged: each engine the same small solid dot in its colour, ringed
    // in the card's colour so dots stay apart; pie drawn last, and the only one named
    const at = (p) => `cx="${x(p.ai).toFixed(1)}" cy="${y(p.achieved).toFixed(1)}"`;
    const isPie = (p) => p.r.engine === Pie.engines.primary;
    // the chart stretches with the card, but its marks keep their size on screen: the line keeps its weight
    // (non-scaling stroke), each dot is a round cap of a zero-length line (so it stays 7px across, as the Engines card's
    // dots), and the names are HTML laid over the chart at the right place, at the card's own type size
    const point = (cx, cy, cls, color = "") => `<line class="${cls}" x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy}"${color ? ` stroke="${color}"` : ""}/>`;
    const dots = [...points.filter((p) => !isPie(p)), ...points.filter(isPie)]
      .map((p) => point(x(p.ai).toFixed(1), y(p.achieved).toFixed(1), "rf-dot", Pie.engines.colorOf(p.r.engine))).join("");
    const pct = (vx, vy) => `left: ${((vx / W) * 100).toFixed(2)}%; top: ${((vy / H) * 100).toFixed(2)}%`;
    // only pie is named, beside its dot in its colour: to the right, or to the left near the right edge
    const labels = points.filter(isPie).map((p) => {
      const cx = x(p.ai), left = cx > W - 40;
      return `<span class="rf-name is-pie${left ? " is-left" : ""}" style="${pct(cx, y(p.achieved))}; color: ${Pie.engines.colorOf(p.r.engine)}">${esc(names().engine(p.r.engine))}</span>`;
    }).join("");
    const shown = knee > X0 && knee < X1;  // the knee, only when it falls inside the window
    const roofPts = (shown ? [start, knee, X1] : [start, X1]).map((v) => `${x(v).toFixed(1)},${y(roof(v)).toFixed(1)}`);
    const kx = x(knee), ky = y(peak * 1e12);
    return `
      <div class="tip-roof">
        <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`Roofline: knee at ${Math.round(knee)} FLOPs per byte`)}">
          <line class="rf-zero" x1="${L}" x2="${W - R}" y1="${y(0).toFixed(1)}" y2="${y(0).toFixed(1)}"/>
          <polyline class="rf-roof" points="${roofPts.join(" ")}"/>
          ${shown ? point(kx.toFixed(1), ky.toFixed(1), "rf-knee") + point(kx.toFixed(1), ky.toFixed(1), "rf-knee-hole") : ""}
          ${dots}
        </svg>
        ${shown ? `<span class="rf-tick-name${kx > W / 2 ? " is-left" : ""} is-above" style="${pct(kx, ky)}">Knee</span>` : ""}
        ${labels}
      </div>`;
  };

  Pie.platform = {
    element,
    batchedBound,

    // the Compare choice, kept per browser: "engines" or "ceiling"
    compare: () => compare,
    setCompare(value) {
      compare = COMPARES[value] ? value : "engines";
      try {
        localStorage.setItem("platformCompare", compare);
      } catch {
        // private windows can refuse storage
      }
    },

    // how many machines a platform has on the site (all platforms when none is named)
    machines(id) {
      return Pie.store.tables.hardware.filter((hw) => { const p = platformOf(hw); return p && (!id || p.id === id); }).length;
    },

    // the setups, for the pop-up in the bar
    metrics() {
      return MODES;
    },

    onChange(handler) {
      onChange = handler;
    },

    // returns the number of machines and models shown, for the toolbar subtitle
    render(state) {
      const all = Pie.store.snapshot(state.release);
      if (!MODES.some((m) => m.id === state.platform.mode)) state.platform.mode = "decode";
      const mode = MODES.find((m) => m.id === state.platform.mode);
      const metric = mode.metric;
      const base = Pie.engines.primary;
      const snapshot = all.filter((r) => r.workload === mode.workload);
      const raw = all.filter((r) => r.workload === "raw" && Pie.store.isMeasured(r));
      const rows = snapshot.filter(Pie.store.isMeasured);
      // a platform's own page lists its machines; All hardware lists every platform's, a header row each
      const only = Pie.schema[state.table]?.platform;
      const groups = PLATFORMS.filter((p) => !only || p.id === only)
        .map((p) => ({ platform: p, macs: Pie.store.tables.hardware.filter((hw) => platformOf(hw) === p).map((hw) => hw.id) }))
        .filter((g) => !only || g.macs.length);
      const macs = groups.flatMap((g) => g.macs);
      if (only && !macs.length) {
        const label = Pie.schema[state.table]?.label || "this platform";
        element.innerHTML = `<div class="platform-empty"><span class="sidebar-glyph" style="--tint: ${Pie.schema[state.table]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(state.table)}</span>
          <h2>No ${esc(label)} results yet</h2></div>`;
        return { macs: 0, models: 0, metric };
      }
      const query = state.query.trim().toLowerCase();
      const noFit = Pie.store.tables.no_fit || {};
      const p = state.platform;

      // every cell first: a comparison, or why there is none
      // grouped by maker; makers and models in the order the viewer dragged them, the rest alphabetical after
      const byName = (a, b) => a.localeCompare(b, undefined, { sensitivity: "base", numeric: true });
      const rank = (list, key) => { const i = (list || []).indexOf(key); return i < 0 ? Infinity : i; };
      const byRank = (list, a, b) => { const x = rank(list, a), y = rank(list, b); return x === y ? 0 : x < y ? -1 : 1; };
      // the search narrows both ways: machines whose name, chip, vendor or platform holds it, models whose name does;
      // a query that names only machines keeps every model, one that names only models keeps every machine
      const machineText = (mac) => {
        const hw = Pie.store.index.hardware[mac] || {};
        return [chipName(mac), hw.name, hw.full_name, hw.vendor, hw.id, platformOf(hw)?.label].filter(Boolean).join(" ").toLowerCase();
      };
      const suiteModels = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id)).filter((id) => !mode.has || mode.has(id));
      const modelHits = query ? suiteModels.filter((id) => names().model(id).toLowerCase().includes(query)) : suiteModels;
      const macHits = query ? macs.filter((mac) => machineText(mac).includes(query)) : macs;
      const narrowModels = query && (modelHits.length || !macHits.length);
      const narrowMacs = query && macHits.length > 0;
      if (narrowMacs) for (const g of groups) g.macs = g.macs.filter((mac) => macHits.includes(mac));
      const allModels = (narrowModels ? modelHits : suiteModels)
        .sort((a, b) => byRank(p.makerOrder, makerOf(a).name, makerOf(b).name) || byName(makerOf(a).name || "~", makerOf(b).name || "~")
          || byRank(p.modelOrder, a, b) || byName(names().model(a), names().model(b)));
      const grid = {};
      for (const mac of macs) {
        grid[mac] = {};
        for (const model of allModels) {
          const c = cell(rows.filter((r) => r.hardware === mac && r.model === model), metric, base);
          const needs = noFit[mac]?.[model]?.[base];
          const own = snapshot.find((r) => r.hardware === mac && r.model === model && r.engine === base);
          grid[mac][model] = { c, needs, why: needs ? `Doesn't fit: needs about ${Math.round(needs)} GB` : own?.note || (mode.workload === "raw" ? "No raw run yet" : "No data yet") };
        }
      }
      // Hide unavailable drops the models and machines with nothing to compare, as the results table does
      const hide = state.hideEmpty;
      const models = hide ? allModels.filter((model) => macs.some((mac) => grid[mac][model].c)) : allModels;
      const median = (list) => {
        const sorted = list.filter((g) => g !== undefined && g !== null).sort((a, b) => a - b);
        return sorted.length ? sorted[sorted.length >> 1] : null;
      };
      const overall = (mac) => median(models.map((model) => grid[mac][model].c?.gain));
      // no sort: the machines in the catalog's order, no arrow anywhere
      const sortKey = p.sort?.key || null;
      const dir = p.sort?.dir || 1;
      const order = (list) => {
        const named = [...list];
        if (!sortKey) return named;
        if (sortKey === "name") return named.sort((a, b) => dir * macName(a).localeCompare(macName(b), undefined, { numeric: true }));
        const val = (mac) => (sortKey === "overall" ? overall(mac) : grid[mac][sortKey]?.c?.gain ?? null);
        // empties sink to the bottom whichever way the column sorts
        return named.sort((a, b) => (val(a) === null) - (val(b) === null) || dir * ((val(a) ?? 0) - (val(b) ?? 0)));
      };
      const shownGroups = groups.map((g) => ({ ...g, macs: order(hide ? g.macs.filter((mac) => models.some((model) => grid[mac][model].c)) : g.macs) }))
        .filter((g) => (!only && !narrowMacs) || g.macs.length);  // a search hides the platforms it leaves empty

      const cells = [];
      const number = (gain) => {
        const kind = Math.abs(gain) < EVEN ? "is-even" : gain > 0 ? "is-ahead" : "is-behind";
        // the sign and the colour say ahead or behind, as Stocks shows a change; an even cell is the same number in grey
        return { kind, html: Math.round(gain * 100) ? signed(gain) : "0%" };
      };
      const machine = (mac, platform) => {
        const hw = Pie.store.index.hardware[mac];
        return `<th class="platform-row" scope="row"><span class="platform-chip"${hw ? ` data-tip="${esc(specSheet(hw))}"` : ""}><span>${esc(chipName(mac))}</span>${specOf(hw)}</span></th>`;
      };
      // a platform heads its machines with a row across the table, as Finder heads a group
      const folded = (id) => Boolean(p.collapsed?.[id]);
      const groupRow = (g) => `<tr class="platform-group-row${folded(g.platform.id) ? " is-collapsed" : ""}${g.macs.length ? "" : " is-empty"}"${g.macs.length ? ` data-group="${g.platform.id}"` : ""} aria-expanded="${!folded(g.platform.id)}"><th colspan="${models.length + 3}" scope="rowgroup">
        <span class="platform-group-bar">
          <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${esc(g.platform.sub)} · ${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}</span></span>
          <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
        </span></th></tr>`;
      // Roofline: every cell carries the mark of what limits it, after its number: two arrows for memory bandwidth,
      // a chip for compute; the hover card gives both bounds
      const MARK = {
        compute: { title: "Compute-bound: the share of the compute bound", path: "M4.5 4.5h7v7h-7zM6.5 2v2.5M9.5 2v2.5M6.5 11.5V14M9.5 11.5V14M2 6.5h2.5M2 9.5h2.5M11.5 6.5H14M11.5 9.5H14" },
        bandwidth: { title: "Bandwidth-bound: the share of the bandwidth bound", path: "M2 5.5h9M8.5 3l2.5 2.5L8.5 8M14 10.5H5M7.5 8 5 10.5 7.5 13" },
      };
      const body = shownGroups.map((g) => groupRow(g) + (folded(g.platform.id) ? [] : g.macs).map((mac, i) => {
        const o = overall(mac);
        const overallCell = o === null ? `<td class="is-overall"><span class="platform-cell is-empty">–</span></td>`
          : (() => { const n = number(o); n.html = Math.round(o * 100) ? signed(o) : "0%"; return `<td class="is-overall"><span class="platform-cell ${n.kind}" data-tip="${esc(card(macName(mac), Math.abs(o) < EVEN ? "On par with the next best" : `${Math.abs(Math.round(o * 100))}% ${o > 0 ? "faster" : "slower"} than the next best`))}">${n.html}</span></td>`; })();
        return `<tr>${machine(mac, g.platform)}${overallCell}${models.map((model) => {
          const { c, needs, why } = grid[mac][model];
          const sorted = sortKey === model ? " is-sorted" : "";
          if (c) {
            cells.push(c.gain);
            const ceil = compare === "ceiling" ? boundOf(mac, model, mode, metric, c.pie) : null;
            const n = compare === "ceiling"
              ? (() => {
                  // one neutral colour: the closest to the bound is bold, the furthest dimmed
                  if (!ceil) return { kind: "is-even", html: "–" };
                  const share = c.pie[metric.key] / ceil.tps;
                  const kind = share >= 0.25 ? "is-ahead" : "is-mid";
                  // a balanced cell takes the lower of its two bounds
                  const which = MARK[ceil.bound] ? ceil.bound : (ceil.bandwidth || Infinity) <= (ceil.compute || Infinity) ? "bandwidth" : "compute";
                  const mark = MARK[which];
                  return { kind, html: `${Math.round(share * 100)}%<svg class="platform-exception" viewBox="0 0 16 16" role="img" aria-label="${mark.title}"><title>${mark.title}</title><path d="${mark.path}"/></svg>` };
                })()
              : number(c.gain);
            return `<td class="${sorted}" data-col="${esc(model)}"><span class="platform-cell ${n.kind}" data-tip="${esc(tip(mac, model, metric, c, mode, raw))}"><span class="platform-main">${n.html}</span>${subline(c, metric, mode, raw)}</span></td>`;
          }
          return `<td class="${sorted}" data-col="${esc(model)}"><span class="platform-cell is-empty${needs ? " is-nofit" : ""}" data-tip="${esc(card("", "", [], why))}">${needs ? NOFIT : "–"}</span></td>`;
        }).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
      }).join("")).join("");

      const arrow = (key) => (sortKey === key ? `<span class="column-sort">${dir > 0 ? "↑" : "↓"}</span>` : "");
      // a maker heads its models with a band across them, as a platform heads its machines down the side
      const makers = [];
      for (const model of models) {
        const maker = makerOf(model);
        if (makers.length && makers[makers.length - 1].maker.name === maker.name) makers[makers.length - 1].n += 1;
        else makers.push({ maker, n: 1 });
      }
      const makerRow = `<tr class="platform-maker-row"><th class="platform-corner is-sortable" data-sort="name" aria-hidden="true"></th><th class="platform-corner is-sortable is-overall" data-sort="overall" aria-hidden="true"></th>${makers.map(({ maker, n }) =>
        `<th class="platform-maker" colspan="${n}" scope="colgroup" data-drop="maker" data-id="${esc(maker.name)}"><span class="platform-maker-name">${badge(maker)}<b>${esc(maker.name || "Other")}</b><span>${n} ${n === 1 ? "model" : "models"}</span></span></th>`).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      const head = `<tr class="platform-head-row">
        <th class="platform-corner is-sortable" scope="col" data-sort="name">Hardware${arrow("name")}</th>
        <th class="platform-corner is-sortable is-overall" scope="col" data-sort="overall"><span class="platform-model">Overall${arrow("overall")}</span><span class="platform-sub">Median</span></th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B active` : ""}` : "";
        const sub = size;
        return `<th class="is-sortable${sortKey === model ? " is-sorted" : ""}" scope="col" data-sort="${esc(model)}" data-drop="model" data-col="${esc(model)}" data-id="${esc(model)}" data-maker="${esc(makerOf(model).name)}" title="Sort by ${esc(names().model(model))}">
          <span class="platform-col"><span><span class="platform-model">${esc(names().model(model))}${arrow(model)}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      // the columns keep their width; a last empty column takes what is left, so rows and bars reach the edge as in Finder
      const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;

      element.innerHTML = `
        <div class="platform-bar">
          <span class="filter platform-setup">
            <button class="filter-button" id="platform-metric" type="button" aria-haspopup="menu" aria-label="${esc(`Setup: ${mode.label}`)}">${esc(mode.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </span>
          <span class="filter platform-compare-filter">
            <button class="filter-button" id="platform-compare" type="button" aria-haspopup="menu" aria-label="${esc(`Compare: ${COMPARES[compare]}`)}">${COMPARES[compare]}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </span>
          <button type="button" class="plain-button rules-button" data-rules aria-expanded="false"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg>Configuration</button>
          <span class="platform-bar-side is-end">
            <button type="button" class="plain-button platform-hide${hide ? " is-active" : ""}" data-hide aria-pressed="${hide}">Hide unavailable</button>
          </span>
        </div>
        <div class="platform-scroll">
          <table class="platform-table" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>
        </div>`;
      // the header bar spans what is visible, so its chevron sits at the right edge however wide the table is
      const scroller = element.querySelector(".platform-scroll");
      if (scroller) element.style.setProperty("--platform-visible", `${scroller.clientWidth}px`);
      const macsShown = shownGroups.reduce((n, g) => n + g.macs.length, 0);
      return { macs: macsShown, models: models.length, metric };
    },

    bind(state) {
      // drag a maker's band among the makers, or a model's head among its maker's models, as a column moves in Finder's
      // list view: the whole column (the head and every cell under it) slides sideways within its lane, and the columns
      // it passes slide aside to open its place, so the order shows as it will be. Letting go settles it there.
      // The head itself is the handle: a press that moves a few points drags, one that does not is a click and sorts.
      // The order is the viewer's, kept with the page's other choices
      const SETTLE = 180;
      let press = null;
      let drag = null;
      let dragged = false;
      // a unit that moves together: a model's column, or a maker's band with all of its models' columns
      const unitOf = (th) => {
        const cells = th.dataset.drop === "model"
          ? [...element.querySelectorAll(`[data-col="${CSS.escape(th.dataset.id)}"]`)]
          : [th, ...[...element.querySelectorAll(`[data-drop="model"][data-maker="${CSS.escape(th.dataset.id)}"]`)]
              .flatMap((head) => [...element.querySelectorAll(`[data-col="${CSS.escape(head.dataset.id)}"]`)])];
        const r = th.getBoundingClientRect();
        return { id: th.dataset.id, cells, left: r.left, width: r.width };
      };
      const shift = (unit, x, animate) => unit.cells.forEach((cell) => {
        cell.style.transition = animate ? `transform ${SETTLE}ms ease` : "none";
        cell.style.transform = x ? `translateX(${x}px)` : "";
      });
      element.addEventListener("pointerdown", (event) => {
        const th = event.target.closest("[data-drop]");
        if (!th || event.button !== 0 || drag) return;
        press = { th, x: event.clientX };
      });
      const lift = (event) => {
        const { th } = press;
        press = null;
        const kind = th.dataset.drop;
        const heads = [...element.querySelectorAll(`[data-drop="${kind}"]`)].filter((x) => kind === "maker" || x.dataset.maker === th.dataset.maker);
        if (heads.length < 2) return;
        const units = heads.map(unitOf);
        const index = heads.indexOf(th);
        const me = units[index];
        me.cells.forEach((cell) => cell.classList.add("is-moving"));
        th.setPointerCapture(event.pointerId);
        dragged = true;
        drag = { kind, units, index, me, x0: event.clientX, lane: [units[0].left, units.at(-1).left + units.at(-1).width], to: index };
      };
      element.addEventListener("pointermove", (event) => {
        if (press && Math.abs(event.clientX - press.x) > 4) lift(event);
        if (!drag) return;
        const { units, index, me, lane } = drag;
        // the column keeps to its lane: it cannot slide past the first or last of its peers
        const dx = Math.max(lane[0] - me.left, Math.min(lane[1] - me.width - me.left, event.clientX - drag.x0));
        shift(me, dx, false);
        // where it would land: past every peer whose middle its middle has reached (held at the lane's end, past the last)
        const middle = me.left + dx + me.width / 2;
        let to = index;
        units.forEach((u, i) => {
          if (i > index && middle >= u.left + u.width / 2) to = Math.max(to, i);
          if (i < index && middle <= u.left + u.width / 2) to = Math.min(to, i);
        });
        drag.to = to;
        // the peers it has passed slide aside by its width to open its place
        units.forEach((u, i) => {
          if (u === me) return;
          shift(u, i > index && i <= to ? -me.width : i < index && i >= to ? me.width : 0, true);
        });
      });
      const finish = () => {
        press = null;
        if (!drag) return;
        const { kind, units, index, me, to } = drag;
        drag = null;
        // settle into the opened place, then take the new order
        const place = to > index ? units.slice(index + 1, to + 1).reduce((w, u) => w + u.width, 0)
          : -units.slice(to, index).reduce((w, u) => w + u.width, 0);
        shift(me, place, true);
        setTimeout(() => {
          units.forEach((u) => { shift(u, 0, false); u.cells.forEach((cell) => cell.classList.remove("is-moving")); });
          if (to === index) return;
          const order = units.map((u) => u.id);
          order.splice(to, 0, order.splice(index, 1)[0]);
          const key = kind === "maker" ? "makerOrder" : "modelOrder";
          const rest = (state.platform[key] || []).filter((x) => !order.includes(x));
          state.platform[key] = kind === "maker" ? order.concat(rest) : rest.concat(order);
          onChange();
        }, SETTLE);
      };
      element.addEventListener("pointerup", finish);
      element.addEventListener("pointercancel", finish);
      element.addEventListener("click", (event) => {
        if (dragged) {
          dragged = false;  // the press lifted a head: it was a drag, not a click to sort
          return;
        }
        const button = event.target.closest("[data-metric]");
        if (button) {
          state.platform.metric = button.dataset.metric;
          onChange();
          return;
        }
        const tab = event.target.closest("[data-mode]");
        if (tab) {
          state.platform.mode = tab.dataset.mode;
          onChange();
          return;
        }
        const comparePicker = event.target.closest("#platform-compare");
        if (comparePicker) {
          event.stopPropagation();
          Pie.popover.open(comparePicker, Pie.popover.COMPARE, state);
          return;
        }
        const picker = event.target.closest("#platform-metric");
        if (picker) {
          event.stopPropagation();
          Pie.popover.open(picker, Pie.popover.METRIC, state);
          return;
        }
        if (event.target.closest("[data-hide]")) {
          // the same Hide unavailable as the results and quality tables: one choice for every page
          state.hideEmpty = !state.hideEmpty;
          try {
            localStorage.setItem("hideUnavailable", state.hideEmpty ? "1" : "0");
          } catch {
            // private windows can refuse storage
          }
          onChange();
          return;
        }
        // a platform's header row folds its machines away and back, as a Finder group does
        const group = event.target.closest("[data-group]");
        if (group) {
          const id = group.dataset.group;
          state.platform.collapsed = { ...(state.platform.collapsed || {}), [id]: !state.platform.collapsed?.[id] };
          onChange();
          return;
        }
        // a header cycles its column: ascending, then descending, then back to no sort
        const header = event.target.closest("[data-sort]");
        if (!header) return;
        const key = header.dataset.sort;
        const now = state.platform.sort;
        state.platform.sort = now?.key !== key ? { key, dir: 1 } : now.dir > 0 ? { key, dir: -1 } : null;
        onChange();
      });
      // a tap on a cell shows its card, as hovering does with a pointer
      element.addEventListener("click", (event) => {
        const mark = Pie.tapCard.isTouch() && event.target.closest("[data-tip]");
        if (mark) Pie.tapCard.toggle(mark, mark.dataset.tip, true);
      });
      element.addEventListener("pointermove", (event) => {
        if (event.pointerType !== "mouse") return;
        const mark = event.target.closest("[data-tip]");
        if (!mark) {
          tooltip.hidden = true;
          return;
        }
        // the card is markup this page built, every value escaped
        tooltip.innerHTML = mark.dataset.tip;
        tooltip.classList.add("is-card");
        tooltip.hidden = false;
        const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      });
      window.addEventListener("resize", () => {
        const scroller = element.querySelector(".platform-scroll");
        if (scroller) element.style.setProperty("--platform-visible", `${scroller.clientWidth}px`);
      });
      element.addEventListener("pointerleave", (event) => {
        if (event.pointerType !== "mouse") return;
        tooltip.hidden = true;
        tooltip.classList.remove("is-card");
      });
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
