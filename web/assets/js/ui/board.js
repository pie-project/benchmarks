window.Pie = window.Pie || {};

// The engine leaderboard, as Artificial Analysis lays out its models: one card per metric, the engines as bars. Engines
// are few and platforms fewer, so each card groups its bars by platform, one hand-picked machine each (the one where
// the most engines ran the model), and the model is the one choice left to the bar above
(() => {
  const element = document.getElementById("board");
  const esc = (text) => Pie.format.escape(text);
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", title: "Decode speed", sub: "Output tokens per second, one request · Higher is better", workload: "raw", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", title: "Prefill speed", sub: "Prompt tokens per second, one request · Higher is better", workload: "raw", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "throughput", title: "Throughput", sub: "Output tokens per second, 32 requests at once · Higher is better", workload: "throughput", key: "output_tok_s", unit: "tok/s", higher: true },
    { id: "ttft", title: "Time to first token", sub: "Milliseconds, one request · Lower is better", workload: "raw", key: "ttft_ms_p50", unit: "ms", higher: false },
  ];
  const PLATFORM_ORDER = ["mac", "nvidia", "tpu", "amd", "cerebras", "android", "web"];

  let state = null;
  let model = null;  // the picked model; none picked opens on the one the most engines and platforms ran

  const measured = () => Pie.store.snapshot(state.release).filter(Pie.store.isMeasured);
  const engineIds = () => Pie.store.tables.engines.map((e) => e.id);

  // the model with the widest coverage: most platforms, then most engines, then most runs
  const coverage = (rows, id) => {
    const own = rows.filter((r) => r.model === id && r.workload === "raw");
    const platforms = new Set(own.map((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {})));
    return [platforms.size, new Set(own.map((r) => r.engine)).size, own.length];
  };
  const byCoverage = (rows) => (a, b) => {
    const x = coverage(rows, a), y = coverage(rows, b);
    return y[0] - x[0] || y[1] - x[1] || y[2] - x[2];
  };
  const models = (rows) => [...new Set(rows.filter((r) => r.workload === "raw").map((r) => r.model))].sort(byCoverage(rows));

  // one machine per platform for the model: the one with the most engine and workload pairs, so every card has bars,
  // then the most runs
  const showcase = (rows, picked) => {
    const raw = rows.filter((r) => r.model === picked && (r.workload === "raw" || r.workload === "throughput"));
    const byPlatform = {};
    for (const r of raw) {
      const p = Pie.platformOf(Pie.store.index.hardware[r.hardware] || {});
      if (!p) continue;
      ((byPlatform[p] ||= {})[r.hardware] ||= new Set()).add(`${r.engine}/${r.workload}`);
    }
    return PLATFORM_ORDER.filter((p) => byPlatform[p]).map((p) => {
      const [hardware] = Object.entries(byPlatform[p]).sort((a, b) => b[1].size - a[1].size
        || raw.filter((r) => r.hardware === b[0]).length - raw.filter((r) => r.hardware === a[0]).length)[0];
      return { platform: p, hardware };
    });
  };

  const compact = (v) => (v === 0 ? "0" : v >= 10000 ? `${Math.round(v / 1000)}K` : v >= 1000 ? `${(v / 1000).toFixed(1)}K` : v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(0) : v.toFixed(1));
  const full = (v, unit) => `${v >= 100 ? Math.round(v).toLocaleString() : v.toFixed(1)} ${unit}`;
  const machineName = (id) => {
    const hw = Pie.store.index.hardware[id];
    return hw ? `${String(hw.name || id).replace(/^Apple\s+/, "")}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}` : id;
  };
  // a clean top for the axis: 1, 2 or 5 times a power of ten, at or above the largest bar
  const niceMax = (v) => {
    const p = 10 ** Math.floor(Math.log10(v));
    return [1, 2, 2.5, 5, 10].map((m) => m * p).find((m) => m >= v);
  };

  // a column with a rounded top and a square foot on the baseline
  const column = (x, y, w, h) => {
    const r = Math.min(4, h, w / 2);
    return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
  };
  // one bar as Health draws them: slim, a rounded top, its value above it in the label colour
  const bar = (x, top, w, base, color, value, tip) => `<g class="board-bar"><title>${esc(tip)}</title>
      <path d="${column(x, top, w, Math.max(base - top, 1))}" style="fill: ${color}"/>
      <text class="board-value" x="${x + w / 2}" y="${top - 6}">${value}</text>
      <rect class="board-hit" x="${x}" y="0" width="${w}" height="${base}"/></g>`;
  // quiet hairlines at a half and the top; every bar carries its number, so the axis needs none
  const lines = (L, R, y, top) => [top / 2, top].map((t) => `<line class="board-grid" x1="${L}" x2="${R}" y1="${y(t)}" y2="${y(t)}"/>`).join("");

  // one model: a group per platform, the engines side by side in it, across the card's full width
  const chart = (metric, rows, groups) => {
    const W = 1040, H = 230, L = 8, R = 8, T = 12, B = 46;
    let cells = groups.map((g) => ({
      ...g,
      bars: engineIds()
        .map((engine) => rows.find((r) => r.workload === metric.workload && r.model === model && r.hardware === g.hardware && r.engine === engine && r[metric.key]))
        .filter(Boolean),
    }));
    // a platform with no run for this card leaves the chart and is named under it instead
    const missing = cells.filter((c) => !c.bars.length).map((c) => Pie.schema[c.platform]?.short || c.platform);
    cells = cells.filter((c) => c.bars.length);
    const values = cells.flatMap((c) => c.bars.map((r) => r[metric.key]));
    if (!values.length) return `<p class="board-empty">No ${esc(metric.title.toLowerCase())} runs for this model yet</p>`;
    const top = niceMax(Math.max(...values));
    const base = H - B;
    const y = (v) => T + (base - T) * (1 - v / top);
    const slot = (W - L - R) / cells.length;
    const most = Math.max(...cells.map((c) => c.bars.length));
    const BW = Math.min(28, (slot * 0.6 - (most - 1) * 2) / most);
    const marks = cells.map((c, i) => {
      const width = c.bars.length * BW + (c.bars.length - 1) * 2;
      const left = L + slot * i + (slot - width) / 2;
      const bars = c.bars.map((r, j) => bar(left + j * (BW + 2), y(r[metric.key]), BW, base, Pie.engines.colorOf(r.engine), compact(r[metric.key]),
        `${names().engine(r.engine)} on ${machineName(c.hardware)}: ${full(r[metric.key], metric.unit)}`)).join("");
      const cx = L + slot * i + slot / 2;
      return `${bars}<text class="board-group" x="${cx}" y="${base + 18}">${esc(Pie.schema[c.platform]?.short || c.platform)}</text>
        <text class="board-machine" x="${cx}" y="${base + 33}">${esc(machineName(c.hardware))}</text>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${metric.title} by engine and platform`)}">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>${missing.length ? `<p class="board-note">Not measured yet on ${esc(missing.join(", "))}</p>` : ""}`;
  };

  // across every model: each machine and model where two or more engines ran Raw is one setup, and an engine is only
  // ever measured against the others on the same setup, so an engine that skips a platform is not marked down for it
  const setups = (rows, key) => {
    const by = {};
    for (const r of rows) if (r.workload === "raw" && r[key]) ((by[`${r.hardware}|${r.model}`] ||= {})[r.engine] = r[key]);
    return Object.values(by).filter((s) => Object.keys(s).length > 1);
  };
  const SUMMARY = [
    {
      id: "index", title: "Speed index", sub: "Decode speed against the fastest engine on each setup · 100 = always fastest",
      value: (rows, engine) => {
        const own = setups(rows, "decode_tok_s").filter((s) => s[engine]);
        if (!own.length) return null;
        const logs = own.map((s) => Math.log(s[engine] / Math.max(...Object.values(s))));
        return { v: 100 * Math.exp(logs.reduce((a, b) => a + b, 0) / logs.length), n: own.length };
      },
      label: (v) => Math.round(v),
    },
    {
      id: "wins", title: "Win rate", sub: "Share of setups where the engine decodes fastest · Higher is better",
      value: (rows, engine) => {
        const own = setups(rows, "decode_tok_s").filter((s) => s[engine]);
        if (!own.length) return null;
        return { v: (100 * own.filter((s) => s[engine] === Math.max(...Object.values(s))).length) / own.length, n: own.length };
      },
      label: (v) => `${Math.round(v)}%`,
    },
    {
      id: "coverage", title: "Coverage", sub: "Machine and model pairs the engine ran · Higher is broader",
      value: (rows, engine) => {
        const n = new Set(rows.filter((r) => r.workload === "raw" && r.engine === engine && r.decode_tok_s).map((r) => `${r.hardware}|${r.model}`)).size;
        return n ? { v: n, n } : null;
      },
      label: (v) => Math.round(v),
    },
  ];

  // every model: one bar per engine, best first, its name under it; how many setups it rests on is in its hover
  const ranking = (summary, rows) => {
    const W = 300, H = 190, L = 4, R = 4, T = 10, B = 28;
    const list = engineIds().map((engine) => ({ engine, ...summary.value(rows, engine) })).filter((e) => e.v !== undefined && e.v !== null)
      .sort((a, b) => b.v - a.v);
    if (!list.length) return `<p class="board-empty">No runs yet</p>`;
    const top = summary.id === "coverage" ? niceMax(list[0].v) : 100;
    const base = H - B;
    const y = (v) => T + (base - T) * (1 - v / top);
    const slot = (W - L - R) / list.length;
    const BW = Math.min(28, slot * 0.5);
    const marks = list.map((e, i) => {
      const x = L + slot * i + (slot - BW) / 2;
      const cx = x + BW / 2;
      const tip = `${names().engine(e.engine)}: ${summary.label(e.v)}${summary.id === "coverage" ? " setups" : `, over ${e.n} ${e.n === 1 ? "setup" : "setups"}`}`;
      return `${bar(x, y(e.v), BW, base, Pie.engines.colorOf(e.engine), summary.label(e.v), tip)}
        <text class="board-group" x="${cx}" y="${base + 20}">${esc(names().engine(e.engine))}</text>
`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${summary.title} by engine`)}">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>`;
  };

  // across model sizes: each platform's fastest machine and engine on each model, by its parameters; dense
  // models only, since a mixture of experts reads a fraction of its weights per token; both axes are logarithmic
  const SIZES = [
    { id: "size-decode", title: "Decode speed by model size", sub: "Output tokens per second, one request, against parameters · Higher is better", key: "decode_tok_s", unit: "tok/s" },
    { id: "size-prefill", title: "Prefill speed by model size", sub: "Prompt tokens per second, one request, against parameters · Higher is better", key: "prefill_tok_s", unit: "tok/s" },
  ];
  const sizeOf = (id) => {
    const m = Pie.store.index.models[id];
    return m?.architecture === "dense" ? m.params_b : null;
  };
  const sizeSeries = (rows, key) => {
    const raw = rows.filter((r) => r.workload === "raw" && r[key] && sizeOf(r.model));
    return PLATFORM_ORDER.map((platform) => {
      const own = raw.filter((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) === platform);
      // one point per size: the fastest run of that size on any of the platform's machines
      const best = {};
      for (const r of own) {
        const b = sizeOf(r.model);
        if (!best[b] || r[key] > best[b][key]) best[b] = r;
      }
      return { platform, points: Object.values(best).sort((a, b) => sizeOf(a.model) - sizeOf(b.model)) };
    }).filter((s) => s.points.length > 1);
  };
  const scatter = (metric, rows) => {
    const W = 1040, H = 260, L = 44, R = 90, T = 10, B = 30;
    const series = sizeSeries(rows, metric.key);
    if (!series.length) return `<p class="board-empty">No runs yet</p>`;
    const all = series.flatMap((s) => s.points);
    const xs = all.map((r) => sizeOf(r.model)), vs = all.map((r) => r[metric.key]);
    const [x0, x1] = [Math.log10(Math.min(...xs)) - 0.08, Math.log10(Math.max(...xs)) + 0.08];
    const [y0, y1] = [Math.floor(Math.log10(Math.min(...vs))), Math.ceil(Math.log10(Math.max(...vs)))];
    const x = (b) => L + (W - L - R) * (Math.log10(b) - x0) / (x1 - x0);
    const y = (v) => T + (H - B - T) * (1 - (Math.log10(v) - y0) / (y1 - y0));
    const grid = [];
    for (let e = y0; e <= y1; e++) grid.push(`<line class="board-grid" x1="${L}" x2="${W - R}" y1="${y(10 ** e)}" y2="${y(10 ** e)}"/><text class="board-tick is-y" x="${L - 8}" y="${y(10 ** e) + 4}">${compact(10 ** e)}</text>`);
    for (const b of [0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]) if (Math.log10(b) >= x0 && Math.log10(b) <= x1)
      grid.push(`<text class="board-tick" x="${x(b)}" y="${H - B + 18}">${b}B</text>`);
    // the platform names at the lines' ends, nudged apart where two would touch
    const ends = series.map((s) => { const r = s.points[s.points.length - 1]; return { s, y: y(r[metric.key]) + 4 }; }).sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 14);
    const lines = series.map((s) => {
      const color = Pie.schema[s.platform]?.tint;
      const label = Pie.schema[s.platform]?.short || s.platform;
      const path = s.points.map((r, i) => `${i ? "L" : "M"}${x(sizeOf(r.model))},${y(r[metric.key])}`).join("");
      const dots = s.points.map((r) => `<g class="board-point"><title>${esc(`${names().model(r.model)} on ${machineName(r.hardware)}, ${names().engine(r.engine)}: ${full(r[metric.key], metric.unit)}`)}</title>
          <circle class="board-hit" cx="${x(sizeOf(r.model))}" cy="${y(r[metric.key])}" r="10"/><circle class="board-dot-mark" cx="${x(sizeOf(r.model))}" cy="${y(r[metric.key])}" r="4" style="fill: ${color}"/></g>`).join("");
      const last = s.points[s.points.length - 1];
      return `<g class="board-series"><path class="board-line" d="${path}" style="stroke: ${color}"/>${dots}
          <text class="board-end" x="${x(sizeOf(last.model)) + 10}" y="${ends.find((e) => e.s === s).y}">${esc(label)}</text></g>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(metric.title)}">${grid.join("")}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/>${lines}</svg>`;
  };

  // scaling with chip count: each GPU run at more than one count is a line, its speed against its fewest chips; the
  // dashed diagonal is a perfect split, so the gap under it is what the interconnect and the split cost
  const SCALING = { id: "scaling", title: "Scaling with chip count", sub: "Decode speed against the fewest chips, one request · The dashed line is perfect scaling" };
  const scaling = (rows) => {
    const W = 1040, H = 240, L = 44, R = 230, T = 10, B = 30;
    const families = {};
    for (const r of rows) {
      const hw = Pie.store.index.hardware[r.hardware];
      if (r.workload !== "raw" || r.model !== model || !r.decode_tok_s || !hw?.count) continue;
      const f = (families[`${hw.full_name}|${hw.interconnect}`] ||= { hw, by: {} });
      if (!f.by[hw.count] || r.decode_tok_s > f.by[hw.count].decode_tok_s) f.by[hw.count] = r;
    }
    const series = Object.values(families).filter((f) => Object.keys(f.by).length > 1).map((f) => {
      const counts = Object.keys(f.by).map(Number).sort((a, b) => a - b);
      const base = f.by[counts[0]].decode_tok_s;
      return { hw: f.hw, points: counts.map((n) => ({ n, gain: f.by[n].decode_tok_s / base, row: f.by[n], base: counts[0] })) };
    });
    if (!series.length) return `<p class="board-empty">No machine ran this model at more than one chip count yet</p>`;
    const most = Math.max(...series.flatMap((s) => s.points.map((p) => p.n)));
    const top = Math.max(most, ...series.flatMap((s) => s.points.map((p) => p.gain)));
    const x = (n) => L + (W - L - R) * Math.log2(n) / Math.log2(most);
    const y = (g) => T + (H - B - T) * (1 - (g - 0.5) / (top - 0.5));
    const grid = [];
    for (let g = 1; g <= top; g *= 2) grid.push(`<line class="board-grid" x1="${L}" x2="${W - R}" y1="${y(g)}" y2="${y(g)}"/><text class="board-tick is-y" x="${L - 8}" y="${y(g) + 4}">${g}×</text>`);
    for (let n = 1; n <= most; n *= 2) grid.push(`<text class="board-tick" x="${x(n)}" y="${H - B + 18}">${n} ${n === 1 ? "chip" : "chips"}</text>`);
    const ideal = `<path class="board-ideal" d="M${x(1)},${y(1)}L${x(most)},${y(most)}"/>`;
    const ends = series.map((s) => ({ s, y: y(s.points[s.points.length - 1].gain) + 4 })).sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 14);
    const link = (hw) => ({ nvlink: "NVLink", pcie: "PCIe", ici: "ICI" })[hw.interconnect] || hw.interconnect || "";
    const lines = series.map((s) => {
      const color = Pie.schema[Pie.platformOf(s.hw)]?.tint;
      const name = String(s.hw.full_name || s.hw.name).replace(/^(NVIDIA|AMD|Google)\s+/, "").replace(/\s+Blackwell Server/, "");
      const path = s.points.map((p, i) => `${i ? "L" : "M"}${x(p.n)},${y(p.gain)}`).join("");
      const dots = s.points.map((p) => `<g class="board-point"><title>${esc(`${name} ×${p.n}, ${names().engine(p.row.engine)}: ${full(p.row.decode_tok_s, "tok/s")}, ${p.gain.toFixed(2)}× of ×${p.base}`)}</title>
          <circle class="board-hit" cx="${x(p.n)}" cy="${y(p.gain)}" r="10"/><circle class="board-dot-mark" cx="${x(p.n)}" cy="${y(p.gain)}" r="4" style="fill: ${color}"/></g>`).join("");
      const last = s.points[s.points.length - 1];
      return `<g class="board-series"><path class="board-line" d="${path}" style="stroke: ${color}"/>${dots}
          <text class="board-end" x="${x(last.n) + 10}" y="${ends.find((e) => e.s === s).y}">${esc(name)} · ${esc(link(s.hw))} · ${last.gain.toFixed(1)}×</text></g>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(SCALING.title)}">${grid.join("")}${ideal}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/>${lines}</svg>`;
  };

  // how much of the hardware each machine uses: the measured speed as a share of its roofline limit, so machines of any
  // size and any number of chips sit on one scale; decode is held by memory bandwidth, prefill mostly by compute
  const USE = { id: "use", title: "Share of the limit", sub: "Measured speed against each machine's roofline limit, fastest engine, one request · Higher uses more of the hardware" };
  const BOUND = { bandwidth: "memory bound", compute: "compute bound", balanced: "balanced", interconnect: "interconnect bound" };
  const use = (rows) => {
    const best = {};
    for (const key of ["decode_tok_s", "prefill_tok_s"])
      for (const r of rows) if (r.workload === "raw" && r.model === model && r[key] && (!(best[r.hardware] ||= {})[key] || r[key] > best[r.hardware][key][key])) best[r.hardware][key] = r;
    const share = (r, key, metric) => {
      const c = r && Pie.ceiling?.(r, metric);
      return c?.tps ? { v: Math.min(100, 100 * r[key] / c.tps), r, c, key } : null;
    };
    const list = Object.entries(best).map(([hardware, b]) => ({ hardware, decode: share(b.decode_tok_s, "decode_tok_s", "decode"), prefill: share(b.prefill_tok_s, "prefill_tok_s", "prefill") }))
      .filter((e) => e.decode || e.prefill).sort((a, b) => (b.decode?.v || 0) - (a.decode?.v || 0));
    if (!list.length) return `<p class="board-empty">No limit for this model yet</p>`;
    // a row per machine, as a Mac list: its name, then a bar for each of decode and prefill on the same 0 to 100 scale
    const W = 1040, ROW = 22, HEAD = 22, NAME = 220, GAP = 24, BAR = (W - NAME - GAP * 2) / 2;
    const H = HEAD + list.length * ROW;
    const cell = (s, x0, top, color) => {
      if (!s) return `<text class="board-machine is-start" x="${x0}" y="${top + 15}">Not measured</text>`;
      const w = Math.max(2, (BAR - 44) * s.v / 100);
      const tip = `${machineName(s.r.hardware)}, ${names().engine(s.r.engine)}: ${full(s.r[s.key], "tok/s")} of a ${full(s.c.tps, "tok/s")} limit, ${BOUND[s.c.bound] || s.c.bound}`;
      return `<g class="board-bar"><title>${esc(tip)}</title><rect x="${x0}" y="${top + 5}" width="${w}" height="12" rx="3" style="fill: ${color}"/>
          <text class="board-value is-start" x="${x0 + w + 6}" y="${top + 15}">${Math.round(s.v)}%</text><rect class="board-hit" x="${x0}" y="${top}" width="${BAR}" height="${ROW}"/></g>`;
    };
    const head = [["Decode", NAME + GAP], ["Prefill", NAME + GAP * 2 + BAR]].map(([t, x]) => `<text class="board-col" x="${x}" y="12">${t}</text>`).join("");
    const body = list.map((e, i) => {
      const top = HEAD + i * ROW;
      const hw = Pie.store.index.hardware[e.hardware] || {};
      const color = Pie.schema[Pie.platformOf(hw)]?.tint || "var(--color-label-tertiary)";
      return `${i % 2 ? "" : `<rect class="board-stripe" x="0" y="${top}" width="${W}" height="${ROW}" rx="5"/>`}
        <text class="board-row-name" x="8" y="${top + 15}"><tspan class="board-row-platform">${esc(Pie.schema[Pie.platformOf(hw)]?.short || "")}</tspan> ${esc(machineName(e.hardware).replace(/^TPU\s+/, ""))}</text>
        ${cell(e.decode, NAME + GAP, top, color)}${cell(e.prefill, NAME + GAP * 2 + BAR, top, color)}`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(USE.title)}">${head}${body}</svg>`;
  };

  const card = (id, title, sub, body) => `
      <section class="board-card" id="board-${id}">
        <h2>${esc(title)}</h2>
        <p class="board-sub">${esc(sub)}</p>
        ${body}
      </section>`;

  const page = () => {
    const rows = measured();
    const list = models(rows);
    if (!list.includes(model)) model = list[0] || null;
    if (!model) return `<div class="board-inner"><p class="board-empty">No runs in this release yet</p></div>`;
    const groups = showcase(rows, model);
    const shown = new Set(rows.filter((r) => r.model === model && groups.some((g) => g.hardware === r.hardware)).map((r) => r.engine));
    // the engines as a key once for the model's charts: a dot and a name, in the catalog's order
    const legend = engineIds().filter((id) => shown.has(id))
      .map((id) => `<span class="board-key"><span class="board-dot" style="background: ${Pie.engines.colorOf(id)}"></span>${esc(names().engine(id))}</span>`).join("");
    // the page's outline down the left, as Artificial Analysis lists its sections: a square each, the one in view filled
    const outline = [
      ["Across every model", SUMMARY.map((m) => [m.id, m.title])],
      ["Across model sizes", SIZES.map((m) => [m.id, m.title.replace(" by model size", "")])],
      ["On one model", [...METRICS.map((m) => [m.id, m.title]), [SCALING.id, "Chip scaling"], [USE.id, "Share of the limit"]]],
    ].map(([head, items]) => `<div class="board-outline-head">${esc(head)}</div>${items.map(([id, title]) =>
      `<button type="button" class="board-outline-item" data-board-go="${id}">${esc(title)}</button>`).join("")}`).join("");
    // the bar under the toolbar, as every page has one: the model picker and the engines' key
    return `
      <div class="platform-bar board-bar">
        <span class="filter platform-setup">
          <button class="filter-button" type="button" data-board-pick="model" aria-haspopup="menu" aria-label="Model">${esc(names().model(model))}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
        </span>
        <span class="board-legend">${legend}</span>
      </div>
      <div class="board-inner">
        <nav class="board-outline" aria-label="On this page">${outline}</nav>
        <div class="board-main">
          <h1 class="board-title">Across every model</h1>
          <p class="board-lede">Each engine against the others on every machine and model they share.</p>
          <div class="board-grid-cards is-three">${SUMMARY.map((m) => card(m.id, m.title, m.sub, ranking(m, rows))).join("")}</div>
          <h1 class="board-title">Across model sizes</h1>
          <p class="board-lede">Dense models on each platform's fastest machine and engine for that size.</p>
          <div class="board-stack">${SIZES.map((m) => card(m.id, m.title, m.sub, scatter(m, rows))).join("")}</div>
          <h1 class="board-title">On ${esc(names().model(model))}</h1>
          <p class="board-lede">The machine on each platform where the most engines ran it.</p>
          <div class="board-stack">${METRICS.map((m) => card(m.id, m.title, m.sub, chart(m, rows, groups))).join("")}
            ${card(SCALING.id, SCALING.title, SCALING.sub, scaling(rows))}
            ${card(USE.id, USE.title, USE.sub, use(rows))}</div>
        </div>
      </div>`;
  };

  // the outline follows the page: the last section whose top has passed the toolbar is the one marked, or the last at the bottom
  const follow = () => {
    const sections = [...element.querySelectorAll(".board-card")];
    const top = element.getBoundingClientRect().top + 80;
    // at the bottom of the page the last section is marked, though its top may never reach the toolbar
    const bottom = element.scrollTop + element.clientHeight >= element.scrollHeight - 2;
    const current = bottom ? sections[sections.length - 1] : sections.filter((s) => s.getBoundingClientRect().top <= top).pop() || sections[0];
    for (const item of element.querySelectorAll("[data-board-go]")) item.classList.toggle("is-current", current && item.dataset.boardGo === current.id.slice(6));
  };
  element.addEventListener("scroll", follow, { passive: true });

  element.addEventListener("click", (event) => {
    const go = event.target.closest("[data-board-go]");
    if (go) {
      element.querySelector(`#board-${go.dataset.boardGo}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const button = event.target.closest("[data-board-pick]");
    if (!button) return;
    event.stopPropagation();
    Pie.popover.open(button, `board:${button.dataset.boardPick}`, null);
  });

  Pie.board = {
    element,
    // the model menu: every model this release measured, the widest coverage first
    menu(k) {
      if (k !== "model" || !state) return [];
      return models(measured()).map((id) => ({ value: id, label: names().model(id), selected: id === model }));
    },
    pick(k, value) {
      if (k === "model") model = value;
      element.dataset.key = "";
    },
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "board";
      const key = `${model}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        element.innerHTML = page();
        element.dataset.key = `${model}@${state.release}`;
        follow();
      }
    },
  };
})();
