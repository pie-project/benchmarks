window.Pie = window.Pie || {};

// The engine leaderboard, as Artificial Analysis lays out its models: one card per metric, the engines as bars. Engines
// are few and platforms fewer, so each card groups its bars by platform, one hand-picked machine each (the one where
// the most engines ran the model), and the model is the one choice left to the bar above
(() => {
  const element = document.getElementById("board");
  const esc = (text) => Pie.format.escape(text);
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Decode", setup: "decode", title: "Decode speed", sub: "Output tokens per second, one request · Higher is better", workload: "raw", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Prefill", setup: "prefill", title: "Prefill speed", sub: "Prompt tokens per second, one request · Higher is better", workload: "raw", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "throughput", label: "Throughput", setup: "batching", title: "Throughput", sub: "Output tokens per second, 32 requests at once · Higher is better", workload: "throughput", key: "output_tok_s", unit: "tok/s", higher: true },
    { id: "ttft", label: "Time to first token", title: "Time to first token", sub: "Milliseconds, one request with a 512-token prompt · Lower is better", workload: "raw", key: "ttft_ms_p50", unit: "ms", higher: false },
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
  // one bar as Health draws them: a rounded top, its value inside at the middle in white where the bar is wide and tall
  // enough to hold it, as Swift Charts sets an overlay annotation, otherwise above it in the label colour
  // hovered, a grey column fills its slot behind it, as Artificial Analysis marks one, and a card names it; no bar dims
  const bar = (x, top, w, base, color, value, tip, band = { x: x - 4, w: w + 8 }) => {
    const inside = w >= 20 && base - top >= 24;
    return `<g class="board-bar" aria-label="${esc(`${tip.head}: ${tip.value}`)}" data-tip-engine="${esc(tip.engine)}" data-tip-head="${esc(tip.head)}" data-tip-value="${esc(tip.value)}" data-tip-note="${esc(tip.note || "")}">
      <rect class="board-band" x="${band.x}" y="0" width="${band.w}" height="${base}"/>
      <path d="${column(x, top, w, Math.max(base - top, 1))}" style="fill: ${color}"/>
      ${Pie.engines.isPrimary(tip.engine) ? `<path class="board-sheen" d="${column(x, top, w, Math.max(base - top, 1))}"/>` : ""}
      <text class="board-value${inside ? " is-inside" : ""}" x="${x + w / 2}" y="${inside ? (top + base) / 2 : top - 6}">${value}</text>
</g>`;
  };
  // quiet hairlines at a half and the top; every bar carries its number, so the axis needs none
  const lines = (L, R, y, top) => [top / 2, top].map((t) => `<line class="board-grid" x1="${L}" x2="${R}" y1="${y(t)}" y2="${y(t)}"/>`).join("");

  // one model: a group per platform, the engines side by side in it, across the card's full width
  const chart = (metric, rows, groups) => {
    const W = 1040, H = 209, L = 8, R = 8, T = 12, B = 46;  // 20px shorter on screen than it was, as every card on the page
    let cells = groups.map((g) => ({
      ...g,
      bars: engineIds()
        .map((engine) => rows.find((r) => r.workload === metric.workload && r.model === model && r.hardware === g.hardware && r.engine === engine && r[metric.key]))
        .filter(Boolean),
    }));
    // a platform with no run for this card leaves the chart and is named under it instead
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
        { engine: r.engine, head: `${names().engine(r.engine)} on ${machineName(c.hardware)}`, value: full(r[metric.key], metric.unit) }, { x: left + j * (BW + 2) - 1, w: BW + 2 })).join("");
      const cx = L + slot * i + slot / 2;
      return `${bars}<text class="board-group" x="${cx}" y="${base + 18}">${esc(Pie.schema[c.platform]?.short || c.platform)}</text>
        <text class="board-machine" x="${cx}" y="${base + 33}">${esc(machineName(c.hardware))}</text>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${metric.title} by engine and platform`)}">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>`;
  };

  // across every model: each machine and model where two or more engines ran Raw is one setup, and an engine is only
  // ever measured against the others on the same setup, so an engine that skips a platform is not marked down for it
  // the rankings' runs: plain decode (Raw) or speculative decode (Spec), picked over the section and kept per browser;
  // each engine is still held only against the others on a machine and model both ran the same way
  const SUMMARY_KEY = "pieSummaryWorkload";
  const SUMMARY_WORKLOADS = [{ id: "raw", label: "Decode", setup: "decode" }, { id: "spec", label: "Spec Decode", setup: "spec" }];
  let summaryWorkload = (() => { try { const k = localStorage.getItem(SUMMARY_KEY); return SUMMARY_WORKLOADS.some((w) => w.id === k) ? k : "raw"; } catch { return "raw"; } })();
  const setups = (rows, key) => {
    const by = {};
    for (const r of rows) if (r.workload === summaryWorkload && r[key]) ((by[`${r.hardware}|${r.model}`] ||= {})[r.engine] = r[key]);
    return Object.values(by).filter((s) => Object.keys(s).length > 1);
  };
  const SUMMARY = [
    {
      id: "index", title: "Speed index", sub: "Decode speed against the fastest · 100 = always fastest",
      value: (rows, engine) => {
        const own = setups(rows, "decode_tok_s").filter((s) => s[engine]);
        if (!own.length) return null;
        const logs = own.map((s) => Math.log(s[engine] / Math.max(...Object.values(s))));
        return { v: 100 * Math.exp(logs.reduce((a, b) => a + b, 0) / logs.length), n: own.length };
      },
      label: (v) => Math.round(v),
    },
    {
      id: "wins", title: "Win rate", sub: "Decodes fastest · Higher is better",
      value: (rows, engine) => {
        const own = setups(rows, "decode_tok_s").filter((s) => s[engine]);
        if (!own.length) return null;
        return { v: (100 * own.filter((s) => s[engine] === Math.max(...Object.values(s))).length) / own.length, n: own.length };
      },
      label: (v) => `${Math.round(v)}%`,
    },
    {
      id: "coverage", title: "Coverage", sub: "Machine and model pairs · Higher is broader",
      value: (rows, engine) => {
        const own = rows.filter((r) => r.workload === summaryWorkload && r.engine === engine && r.decode_tok_s);
        const n = new Set(own.map((r) => `${r.hardware}|${r.model}`)).size;
        if (!n) return null;
        // how many platforms the pairs are on, for the bar's card
        const k = new Set(own.map((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}))).size;
        const detail = `${k} ${k === 1 ? "platform" : "platforms"}`;
        return { v: n, n, detail };
      },
      label: (v) => Math.round(v),
    },
  ];

  // every model: one bar per engine, best first, its name under it; how many setups it rests on is in its hover
  // an engine's logo with no tile behind it; the ones drawn in a single ink take the label colour, so they read in either theme
  const GLYPHS = {
    pie: ["0 0 67.89 67.89", '<path class="is-stroked" d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z" stroke-width="8"/>'],  // the sidebar's weight
    mlxlm: ["13 -42 414 224", '<g><path transform="translate(0 139.72)" d="M 13.9375 0 L 42.3125 0 L 42.3125 -91.796875 L 43.671875 -91.796875 L 78.71875 0 L 97.984375 0 L 133.03125 -91.796875 L 134.390625 -91.796875 L 134.390625 0 L 162.765625 0 L 162.765625 -139.71875 L 125.96875 -139.71875 L 88.984375 -42.015625 L 87.8125 -42.015625 L 50.734375 -139.71875 L 13.9375 -139.71875 Z M 13.9375 0"/><path transform="translate(176.682092 139.72)" d="M 13.9375 0 L 106.21875 0 L 106.21875 -26.046875 L 45.984375 -26.046875 L 45.984375 -139.71875 L 13.9375 -139.71875 Z M 13.9375 0"/></g><g class="is-faint"><path transform="translate(290.57 139.72)" d="M 6.296875 0 L 40.5625 0 L 69.515625 -47.34375 L 70.484375 -47.34375 L 99.625 0 L 135.84375 0 L 91.109375 -69.8125 L 91.109375 -70.296875 L 136.328125 -139.71875 L 100.703125 -139.71875 L 73 -90.71875 L 71.84375 -90.71875 L 43.953125 -139.71875 L 6.484375 -139.71875 L 49.96875 -70.6875 L 49.96875 -70.296875 Z M 6.296875 0"/></g>'],  // MLX's wordmark, its X in grey as the project draws it
  };
  const FILES = { vllm: "vllm.svg", sglang: "sglang.svg", llamacpp: "llamacpp.png", splash: "splash.png" };  // Splash's own tile, its stacked marks on coral
  const logo = (engine, x, y, size) => GLYPHS[engine]
    ? `<svg class="board-glyph" x="${x - (engine === "mlxlm" ? size * .35 : 0)}" y="${y}" width="${size * (engine === "mlxlm" ? 1.7 : 1)}" height="${size}" viewBox="${GLYPHS[engine][0]}">${GLYPHS[engine][1]}</svg>`
    : FILES[engine] ? `<image class="board-logo" href="assets/img/engines/${FILES[engine]}" x="${x}" y="${y}" width="${size}" height="${size}"/>` : "";
  // a shorter name where the engine's own would crowd its neighbours under a bar
  const SHORT = { llamacpp: "Llama" };
  const ranking = (summary, rows) => {
    const W = 300, H = 185, L = 24, R = 4, T = 10, B = 44;  // room under the bars for the logo and the name under it; the bars 20px shorter on screen
    const list = engineIds().map((engine) => ({ engine, ...summary.value(rows, engine) })).filter((e) => e.v !== undefined && e.v !== null)
      .sort((a, b) => b.v - a.v);
    if (!list.length) return `<p class="board-empty">No runs yet</p>`;
    const top = summary.id === "coverage" ? niceMax(list[0].v) : 100;
    const base = H - B;
    const y = (v) => T + (base - T) * (1 - v / top);
    const slot = (W - L - R) / list.length;
    const BW = slot * .86;  // wide bars with a narrow gap between them, as Artificial Analysis sets its rankings
    const marks = list.map((e, i) => {
      const x = L + slot * i + (slot - BW) / 2;
      const cx = x + BW / 2;
      const tip = { engine: e.engine, head: names().engine(e.engine), value: summary.label(e.v),
        note: e.detail || `Over ${e.n} ${e.n === 1 ? "setup" : "setups"}` };
      return `${bar(x, y(e.v), BW, base, Pie.engines.colorOf(e.engine), summary.label(e.v), tip, { x: L + slot * i, w: slot })}
        ${logo(e.engine, cx - 8, base + 6, 16)}
        <text class="board-group" x="${cx}" y="${base + 36}">${esc(SHORT[e.engine] || names().engine(e.engine))}</text>
`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${summary.title} by engine`)}">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>`;
  };

  // across model sizes: each platform's fastest machine and engine on each model, by its parameters; dense
  // models only, since a mixture of experts reads a fraction of its weights per token; both axes are logarithmic
  const SIZES = [
    { id: "size-decode", label: "Decode", setup: "decode", title: "Decode speed by model size", sub: "Output tokens per second, one request, against parameters · Higher is better", key: "decode_tok_s", unit: "tok/s" },
    { id: "size-prefill", label: "Prefill", setup: "prefill", title: "Prefill speed by model size", sub: "Prompt tokens per second, one request, against parameters · Higher is better", key: "prefill_tok_s", unit: "tok/s" },
  ];
  // a card's engine, picked in its corner as a card's measure is: the fastest engine on each machine, or one engine alone,
  // each with its logo; kept per browser, each card its own
  const ENGINE_KEYS = { "use-engine": "pieUseEngine", "scale-engine": "pieScaleEngine" };
  const keptEngine = (k) => { try { const e = localStorage.getItem(ENGINE_KEYS[k]); return Pie.store.tables.engines.some((x) => x.id === e) ? e : null; } catch { return null; } };
  let useEngine = keptEngine("use-engine"), scaleEngine = keptEngine("scale-engine");
  const engineMark = (engine) => engine ? `<svg class="board-pick-logo" viewBox="0 0 16 16" aria-hidden="true">${logo(engine, 0, 0, 16)}</svg>` : "";
  const enginePick = (k, engine) => `<button class="filter-button board-card-pick" type="button" data-board-pick="${k}" aria-haspopup="menu" aria-label="Engine">${engineMark(engine)}${esc(engine ? names().engine(engine) : "Fastest engine")}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  const engineSub = (sub, engine) => (engine ? sub.replace("fastest engine", names().engine(engine)).replace("Decode speed against", `${names().engine(engine)}'s decode speed against`) : sub);
  // the model's speeds as one card, Decode, Prefill or Throughput picked in its corner and kept per browser, each wearing
  // the setup control's degree mark; time to first token, a latency rather than a speed, keeps a card of its own
  const SPEEDS = METRICS.filter((m) => m.setup);
  const TTFT = METRICS.find((m) => m.id === "ttft");
  const METRIC_KEY = "pieModelMetric";
  let modelMetric = (() => { try { const k = localStorage.getItem(METRIC_KEY); return SPEEDS.some((m) => m.id === k) ? k : SPEEDS[0].id; } catch { return SPEEDS[0].id; } })();
  const metricIcon = (m) => Pie.platform.degree(m.setup);
  const metricCard = (rows, groups) => {
    const m = SPEEDS.find((x) => x.id === modelMetric) || SPEEDS[0];
    const pick = `<button class="filter-button board-card-pick" type="button" data-board-pick="metric" aria-haspopup="menu" aria-label="Measure">${metricIcon(m)}${esc(m.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
    return card("metric", "Performance", m.sub, chart(m, rows, groups), pick);
  };
  // the two as one card, Decode or Prefill picked in its corner and kept per browser
  const SIZE_KEY = "pieSizeMetric";
  let sizeMetric = (() => { try { const k = localStorage.getItem(SIZE_KEY); return SIZES.some((m) => m.id === k) ? k : SIZES[0].id; } catch { return SIZES[0].id; } })();
  const sizePick = (k, m) => `<button class="filter-button board-card-pick" type="button" data-board-pick="${k}" aria-haspopup="menu" aria-label="Speed">${Pie.platform.degree(m.setup)}${esc(m.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  const sizeCard = (rows) => {
    const m = SIZES.find((x) => x.id === sizeMetric) || SIZES[0];
    return card("size", "Dense models by size", m.sub, scatter({ ...m, title: "Dense models by size" }, rows, sizeOf), sizePick("size", m));
  };
  // the mixtures of experts the same way, on the parameters a token reads, with a pick of their own
  const MOE_KEY = "pieMoeMetric";
  let moeMetric = (() => { try { const k = localStorage.getItem(MOE_KEY); return SIZES.some((m) => m.id === k) ? k : SIZES[0].id; } catch { return SIZES[0].id; } })();
  const moeCard = (rows) => {
    const m = SIZES.find((x) => x.id === moeMetric) || SIZES[0];
    return card("moe", "MoE models by active size", m.sub.replace("against parameters", "against active parameters"), scatter({ ...m, title: "MoE models by active size" }, rows, activeOf), sizePick("moe", m));
  };
  const sizeOf = (id) => {
    const m = Pie.store.index.models[id];
    return m?.architecture === "dense" ? m.params_b : null;
  };
  // a mixture of experts sized by the parameters each token reads, its active ones: what its decode speed follows
  const activeOf = (id) => {
    const m = Pie.store.index.models[id];
    return m && m.architecture !== "dense" ? m.active_b : null;
  };
  const sizeSeries = (rows, key, of) => {
    const raw = rows.filter((r) => r.workload === "raw" && r[key] && of(r.model));
    return PLATFORM_ORDER.map((platform) => {
      const own = raw.filter((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) === platform);
      // one point per size: the fastest run of that size on any of the platform's machines
      const best = {};
      for (const r of own) {
        const b = of(r.model);
        if (!best[b] || r[key] > best[b][key]) best[b] = r;
      }
      return { platform, points: Object.values(best).sort((a, b) => of(a.model) - of(b.model)) };
    }).filter((s) => s.points.length > 1);
  };
  const scatter = (metric, rows, of = sizeOf) => {
    const W = 1040, H = 239, L = 44, R = 90, T = 10, B = 30;
    const series = sizeSeries(rows, metric.key, of);
    if (!series.length) return `<p class="board-empty">No runs yet</p>`;
    const all = series.flatMap((s) => s.points);
    const xs = all.map((r) => of(r.model)), vs = all.map((r) => r[metric.key]);
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
      const path = s.points.map((r, i) => `${i ? "L" : "M"}${x(of(r.model))},${y(r[metric.key])}`).join("");
      const dots = s.points.map((r) => `<g class="board-point"><title>${esc(`${names().model(r.model)} on ${machineName(r.hardware)}, ${names().engine(r.engine)}: ${full(r[metric.key], metric.unit)}`)}</title>
          <circle class="board-hit" cx="${x(of(r.model))}" cy="${y(r[metric.key])}" r="10"/><circle class="board-dot-mark" cx="${x(of(r.model))}" cy="${y(r[metric.key])}" r="4" style="fill: ${color}"/></g>`).join("");
      const last = s.points[s.points.length - 1];
      return `<g class="board-series"><path class="board-line" d="${path}" style="stroke: ${color}"/>${dots}
          <text class="board-end" x="${x(of(last.model)) + 10}" y="${ends.find((e) => e.s === s).y}">${esc(label)}</text></g>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(metric.title)}">${grid.join("")}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/>${lines}</svg>`;
  };

  // scaling with chip count: each GPU run at more than one count is a line, its speed against its fewest chips; the
  // dashed diagonal is a perfect split, so the gap under it is what the interconnect and the split cost
  const SCALING = { id: "scaling", title: "Scaling with chip count", sub: "Decode speed against the fewest chips, one request · The dashed line is perfect scaling" };
  // the models run at more than one chip count on some machine, the most machines first: the datacenter section's menu
  const scaleFamilies = (rows, id) => {
    const families = {};
    for (const r of rows) {
      const hw = Pie.store.index.hardware[r.hardware];
      if (r.workload !== "raw" || r.model !== id || !r.decode_tok_s || !hw?.count) continue;
      ((families[`${hw.full_name}|${hw.interconnect}`] ||= new Set())).add(hw.count);
    }
    return Object.values(families).filter((counts) => counts.size > 1).length;
  };
  const scaleModels = (rows) => [...new Set(rows.map((r) => r.model))].map((id) => [id, scaleFamilies(rows, id)])
    .filter(([, n]) => n).sort((a, b) => b[1] - a[1] || names().model(a[0]).localeCompare(names().model(b[0]))).map(([id]) => id);
  const SCALE_KEY = "pieScaleModel";
  let scaleModel = (() => { try { return localStorage.getItem(SCALE_KEY); } catch { return null; } })();
  const scaleModelOf = (rows) => { const list = scaleModels(rows); return list.includes(scaleModel) ? scaleModel : list[0] || model; };
  const scaling = (all, which = scaleModelOf(all)) => {
    const rows = scaleEngine ? all.filter((r) => r.engine === scaleEngine) : all;
    const W = 1040, H = 219, L = 44, R = 230, T = 10, B = 30;
    const families = {};
    for (const r of rows) {
      const hw = Pie.store.index.hardware[r.hardware];
      if (r.workload !== "raw" || r.model !== which || !r.decode_tok_s || !hw?.count) continue;
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
  const use = (all) => {
    const rows = useEngine ? all.filter((r) => r.engine === useEngine) : all;  // one engine, or the fastest on each machine
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
    // rows as tall as the site's tables set theirs (about 28px on screen), each row's name, bar and number on its middle
    const W = 1040, ROW = 30, HEAD = 24, NAME = 220, GAP = 24, BAR = (W - NAME - GAP * 2) / 2;
    const mid = (top) => top + ROW / 2 + 4;  // a line of 12px type, centred on the row
    const H = HEAD + list.length * ROW;
    const cell = (s, x0, top, color) => {
      if (!s) return `<text class="board-machine is-start" x="${x0}" y="${mid(top)}">Not measured</text>`;
      const w = Math.max(2, (BAR - 44) * s.v / 100);
      const tip = `${machineName(s.r.hardware)}, ${names().engine(s.r.engine)}: ${full(s.r[s.key], "tok/s")} of a ${full(s.c.tps, "tok/s")} limit, ${BOUND[s.c.bound] || s.c.bound}`;
      return `<g class="board-bar"><title>${esc(tip)}</title><rect x="${x0}" y="${top + (ROW - 18) / 2}" width="${w}" height="18" rx="4.5" style="fill: ${color}"/>
          <text class="board-value is-start" x="${x0 + w + 6}" y="${mid(top)}">${Math.round(s.v)}%</text><rect class="board-hit" x="${x0}" y="${top}" width="${BAR}" height="${ROW}"/></g>`;
    };
    const head = [["Decode", NAME + GAP], ["Prefill", NAME + GAP * 2 + BAR]].map(([t, x]) => `<text class="board-col" x="${x}" y="14">${t}</text>`).join("");
    const body = list.map((e, i) => {
      const top = HEAD + i * ROW;
      const hw = Pie.store.index.hardware[e.hardware] || {};
      const color = Pie.schema[Pie.platformOf(hw)]?.tint || "var(--color-label-tertiary)";
      return `${i % 2 ? "" : `<rect class="board-stripe" x="0" y="${top}" width="${W}" height="${ROW}" rx="5"/>`}
        <text class="board-row-name" x="8" y="${mid(top)}"><tspan class="board-row-platform">${esc(Pie.schema[Pie.platformOf(hw)]?.short || "")}</tspan> ${esc(machineName(e.hardware).replace(/^TPU\s+/, ""))}</text>
        ${cell(e.decode, NAME + GAP, top, color)}${cell(e.prefill, NAME + GAP * 2 + BAR, top, color)}`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(USE.title)}">${head}${body}</svg>`;
  };

  // the changelog: each release measured, newest first, read from the runs themselves; development runs are left out
  let log = null;
  const changelog = () => log ||= (Pie.store.tables.tags || [])
    .filter((tag) => /^\d+\.\d+/.test(tag.id))
    .map((tag) => ({ kind: "New release measured", at: tag.date, run: tag, results: Pie.store.snapshot(tag.id).filter(Pie.store.isMeasured).length }))
    .filter((e) => e.results)
    .sort((a, b) => b.at.localeCompare(a.at));
  // "21 Sep": the day, then the month in three letters
  const MONTH = new Intl.DateTimeFormat("en-US", { month: "short" });
  const DAY = { format: (d) => `${d.getDate()} ${MONTH.format(d)}` };
  const logItem = (e) => {
    const [mark, text] = [`<span class="board-log-glyph">${Pie.icon("board")}</span>`, `${e.run.id} · ${e.results.toLocaleString()} results`];
    return `<li class="board-log-item">
        <div class="board-log-kind">${esc(e.kind)} · ${esc(DAY.format(new Date(e.at.replace(" ", "T"))))}</div>
        <div class="board-log-text">${mark}<span>${esc(text)}</span></div>
      </li>`;
  };
  // the page's foot, as a Mac site closes its pages: a quiet band under a hairline, Pie's mark and a line, the site's
  // pages in small grey columns, and the year and the data's last update on the last line. A page link opens its page as
  // its sidebar row does; the project's links leave in a new tab
  const footer = () => {
    const page = (id) => Pie.schema[id] ? `<li><a href="#" data-board-open="${id}">${esc(Pie.schema[id].label)}</a></li>` : "";
    const out = (href, text) => `<li><a href="${href}" target="_blank" rel="noopener">${esc(text)}</a></li>`;
    const at = Pie.store.tables.updated_at ? new Date(Pie.store.tables.updated_at) : null;
    const when = at ? at.toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" }) : "";
    return `
      <footer class="board-footer">
        <div class="board-footer-inner">
          <div class="board-footer-brand">
            <svg viewBox="0 0 67.89 67.89" aria-hidden="true"><path d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z"/></svg>
            <div><div class="board-footer-name">Pie</div><div class="board-footer-line">AI that runs everywhere.</div></div>
          </div>
          <nav class="board-footer-cols" aria-label="Site">
            <div><h3>Benchmarks</h3><ul>${["board", "all_hardware", "speedups", "tps"].map(page).join("")}</ul></div>
            <div><h3>Platforms</h3><ul>${["mac", "nvidia", "tpu", "amd", "cerebras"].map(page).join("")}</ul></div>
            <div><h3>Pie</h3><ul>${out("https://pie-project.org", "Website")}${out("https://github.com/pie-project/pie", "GitHub")}</ul></div>
          </nav>
        </div>
        <div class="board-footer-base">
          <span>© ${new Date().getFullYear()} Pie Project<span class="board-footer-sep">·</span><a href="https://github.com/pie-project/pie/blob/main/LICENSE" target="_blank" rel="noopener">Open source · Apache 2.0</a></span>
          ${when ? `<span>updated ${esc(when)}</span>` : ""}
        </div>
      </footer>`;
  };
  // under the rankings, three blocks a third each: Pie's banner, the Hardware Recommender, and the changelog scrolling within its card
  const hero = (newest = changelog()[0]) => `
      <div class="board-hero">
        <div class="welcome-banner board-banner">
          <a class="board-banner-link" href="https://pie-project.org" target="_blank" rel="noopener" aria-label="Pie website">
            <span class="board-banner-go" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span>
          </a>
          <div class="board-banner-foot">
            ${newest ? `<span class="board-banner-badge">New</span>` : ""}
            <h2 class="board-banner-title">Programmable Inference Engine</h2>
          </div>
        </div>
        <div class="welcome-banner board-banner is-recommender">
          <a class="board-banner-link" href="#" data-board-open="tps" aria-label="Hardware Recommender">
            <span class="board-banner-go" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span>
          </a>
          <h2 class="board-banner-title is-top">Hardware Recommender</h2>
          <p class="board-banner-sub">Compare cost, hardware and models<br>for the throughput you need to serve</p>
        </div>
        <section class="board-log" aria-label="Changelog">
          <h2 class="board-log-title">Changelog</h2>
          <ol class="board-log-list">${changelog().map(logItem).join("")}</ol>
        </section>
      </div>`;

  // each card's title after a badge, as System Settings sets a pane's name after its icon: a white symbol on a rounded tile
  // in one of Apple's system colours, so the charts are told apart at a glance as Artificial Analysis marks them with squares
  const BADGES = {
    index:          ["#5E5CE6", '<circle cx="12" cy="12" r="9"/><path d="m12 12 2.6-5.2"/><circle cx="12" cy="12" r="1.6" fill="#fff" stroke="none"/><path d="M7 15.5h.01M6.5 11h.01M9 7h.01M17.5 11h.01M17 15.5h.01"/>'],  // indigo, a speedometer as SF Symbols draws gauge.with.needle: a dial, its needle just right of upright
    wins:           ["#FF9F0A", '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v6M8.5 19h7"/>'],  // orange, a trophy: its stem runs down into its base
    coverage:       ["#30B0C7", Pie.icons.welcome],  // teal, a grid of squares
    moe:            ["#5AC8FA", '<path d="M4 4v16h16"/><circle cx="9" cy="15" r="1.9" fill="#fff" stroke="none"/><circle cx="13" cy="11" r="1.9" fill="#fff" stroke="none"/><circle cx="17.5" cy="6.5" r="1.9" fill="#fff" stroke="none"/>'],  // a lighter cyan, the same scatter
    size:           ["#32ADE6", '<path d="M4 4v16h16"/><circle cx="9" cy="15" r="1.9" fill="#fff" stroke="none"/><circle cx="13" cy="11" r="1.9" fill="#fff" stroke="none"/><circle cx="17.5" cy="6.5" r="1.9" fill="#fff" stroke="none"/>'],  // cyan, a scatter of solid dots
    ttft:           ["#FF375F", '<circle cx="12" cy="13.5" r="7.5"/><path d="M12 10v3.5l2.5 2M10 2.5h4"/>'],  // pink, a timer
    metric:         ["#0A84FF", '<path d="M4 6h16M4 12h12M4 18h5"/><path d="M14.5 18.1v3.5"/>'],  // blue, text being written: three lines 6 apart, the cursor a clear step after the short last one
    scaling:        ["#8E8E93", Pie.icons.hardware],  // grey, a chip
    use:            ["#AC8E68", Pie.icons.methods],  // brown, a roofline
  };
  // a chart card's tools at its title's end, as Artificial Analysis sets them: a link to it, its image, its data
  const TOOLS = (id) => `<button class="board-card-tool" type="button" data-board-link="${id}" aria-label="Copy a link to this chart" title="Copy a link to this chart"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.9 9.1a2.5 2.5 0 0 0 3.5 0l2.1-2.1a2.5 2.5 0 0 0-3.5-3.5l-.9.9"/><path d="M9.1 6.9a2.5 2.5 0 0 0-3.5 0L3.5 9a2.5 2.5 0 0 0 3.5 3.5l.9-.9"/></svg></button><button class="board-card-tool" type="button" data-board-save="${id}" aria-label="Save as image" title="Save as image"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.25" y="3" width="11.5" height="10" rx="2"/><circle cx="5.75" cy="6.25" r="1"/><path d="m2.5 11.5 3.2-3.2 2.3 2.3 2-2 3.5 3.5"/></svg></button><button class="board-card-tool" type="button" data-board-data="${id}" aria-label="Download the data" title="Download the data (log in)"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.25" y="3" width="11.5" height="10" rx="2"/><path d="M2.25 6.5h11.5M2.25 9.75h11.5M7 6.5V13"/></svg></button>`;
  // a card: its badge and title, and under them what it measures, with how to read it ("Higher is better") on a line
  // of its own; at the far end its tools (link, image, data), and under them the pick of what the card shows
  const card = (id, title, sub, body, aside = "", tools = true) => `
      <section class="board-card" id="board-${id}">
        <div class="board-card-head">
          <div class="board-card-titles">
            <h2>${BADGES[id] ? `<i class="board-title-dot" style="background: ${BADGES[id][0]}" aria-hidden="true"></i>` : ""}${esc(title)}</h2>
            <p class="board-sub">${sub.split(" · ").map(esc).join("<br>")}</p>
          </div>
          ${tools || aside ? `<div class="board-card-side">${tools ? `<span class="board-card-tools">${TOOLS(id)}</span>` : ""}${aside}</div>` : ""}
        </div>
        ${body}
      </section>`;

  const page = () => {
    const rows = measured();
    const list = models(rows);
    if (!list.includes(model)) model = list[0] || null;
    if (!model) return `<div class="board-scroll"><div class="board-inner"><p class="board-empty">No runs in this release yet</p></div></div>`;
    const groups = showcase(rows, model);
    const shown = new Set(rows.filter((r) => r.model === model && groups.some((g) => g.hardware === r.hardware)).map((r) => r.engine));
    // the engines as a key once for the model's charts: a dot and a name, in the catalog's order
    const legend = engineIds().filter((id) => shown.has(id))
      .map((id) => `<span class="board-key"><span class="board-dot" style="background: ${Pie.engines.colorOf(id)}"></span>${esc(names().engine(id))}</span>`).join("");
    // the page's outline down the left, as Artificial Analysis lists its sections: a square each, the one in view filled
    const outline = [
      ["Across every model", SUMMARY.map((m) => [m.id, m.title])],
      ["Across model sizes", [["size", "Dense models"], ["moe", "MoE models"]]],
      ["On one model", [["metric", "Performance"], [TTFT.id, "Time to first token"], [USE.id, "Share of the limit"]]],
      ["At datacenter scale", [[SCALING.id, "Chip scaling"]]],
    ].map(([head, items]) => `<div class="board-outline-head">${esc(head)}</div>${items.map(([id, title]) =>
      `<button type="button" class="board-outline-item" data-board-go="${id}"><i class="board-outline-dot" style="background: ${BADGES[id]?.[0] || "var(--color-label-tertiary)"}" aria-hidden="true"></i><span>${esc(title)}</span></button>`).join("")}`).join("");
    // the bar under the toolbar, as every page has one: the engines' key; the model is picked in the one section it sets
    // pie's bars' texture, defined once for every chart on the page: fine diagonal lines in white over its colour, so
    // the project's own engine stands out from the ones it is measured against
    const SHEEN = `<svg class="board-defs" width="0" height="0" aria-hidden="true"><defs>
        <pattern id="board-sheen" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="1.6" height="5" fill="#fff" fill-opacity=".14"/>
        </pattern></defs></svg>`;
    return `${SHEEN}
      <div class="platform-bar board-bar">
        <span class="board-legend">${legend}</span>
      </div>
      <div class="board-scroll"><div class="board-inner">
        <nav class="board-outline" aria-label="On this page">${outline}</nav>
        <div class="board-main">
          <div class="board-section-head">
            <div class="board-section-text"><h1 class="board-title">Across every model</h1>
            <p class="board-lede">Every engine compared with the others on each machine and model they share.</p></div>
            <button class="board-toggle${summaryWorkload === "spec" ? " is-on" : ""}" type="button" data-board-toggle="spec" aria-pressed="${summaryWorkload === "spec"}" title="Rank on speculative decoding: each engine drafting with its own drafter"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3 4 4 4-4 4M8.5 4l4 4-4 4"/></svg>Speculation</button>
          </div>
          <div class="board-grid-cards is-three">${SUMMARY.map((m) => card(m.id, m.title, summaryWorkload === "spec" ? m.sub.replace("Decode speed", "Spec decode speed").replace("Decodes fastest", "Spec decodes fastest") : m.sub, ranking(m, rows), "", false)).join("")}</div>${hero()}
          <h1 class="board-title">Across model sizes</h1>
          <p class="board-lede">Dense models by their size, mixtures of experts by the parameters each token reads, on each platform's fastest machine and engine.</p>
          <div class="board-stack">${sizeCard(rows)}${moeCard(rows)}</div>
          <div class="board-section-head">
            <div class="board-section-text"><h1 class="board-title">On one model</h1>
            <p class="board-lede">Each platform is shown on the machine where the most engines ran this model.</p></div>
            <button class="filter-button board-title-pick" type="button" data-board-pick="model" aria-haspopup="menu" aria-label="Model">${Pie.platform.makerBadge(model)}${esc(names().model(model))}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </div>
          <div class="board-stack">${metricCard(rows, groups)}${card(TTFT.id, TTFT.title, TTFT.sub, chart(TTFT, rows, groups))}
            ${card(USE.id, USE.title, engineSub(USE.sub, useEngine), use(rows), enginePick("use-engine", useEngine))}</div>
          <div class="board-section-head">
            <div class="board-section-text"><h1 class="board-title">At datacenter scale</h1>
            <p class="board-lede">A model split across several GPUs, at each chip count, against a perfect split.</p></div>
            <button class="filter-button board-title-pick" type="button" data-board-pick="scale" aria-haspopup="menu" aria-label="Model">${Pie.platform.makerBadge(scaleModelOf(rows))}${esc(names().model(scaleModelOf(rows)))}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </div>
          <div class="board-stack">${card(SCALING.id, SCALING.title, engineSub(SCALING.sub, scaleEngine), scaling(rows), enginePick("scale-engine", scaleEngine))}</div>
        </div>
      </div>${footer()}</div>`;
  };

  // the page scrolls under its bar, as the other pages' grids do: the bar stays put above, only the content moves
  const scroller = () => element.querySelector(".board-scroll") || element;
  // the outline follows the page: the last section whose top has passed the bar is the one marked, or the last at the bottom
  // an outline item clicked stays marked while its card scrolls into place, until the viewer scrolls again: a card beside
  // others in a row would otherwise hand the mark to whichever of them the line falls on
  let pinned = null;
  const unpin = () => { pinned = null; };
  for (const kind of ["wheel", "touchstart", "keydown", "pointerdown"]) element.addEventListener(kind, (event) => {
    if (kind === "pointerdown" && event.target.closest("[data-board-go]")) return;
    unpin();
  }, { passive: true });
  const follow = () => {
    const sections = [...element.querySelectorAll(".board-card")];
    const view = scroller();
    // the section being read is the one whose top has passed a line a third of the way down the view, not the bar: a
    // card in sight is marked as it comes up, not only once it has reached the top
    const box = view.getBoundingClientRect();
    const line = box.top + box.height / 3;
    const passed = sections.filter((s) => s.getBoundingClientRect().top <= line);
    const last = passed.length ? Math.max(...passed.map((s) => s.getBoundingClientRect().top)) : null;
    // at the bottom of the page the last section is marked, though its top may never reach the line
    const bottom = view.scrollTop + view.clientHeight >= view.scrollHeight - 2;
    // cards side by side in a row share a top: the line's way down through the row hands the mark from the first to the
    // last, left to right, as the row is read, and the last keeps it until the next section comes up
    const row = passed.filter((s) => Math.abs(s.getBoundingClientRect().top - last) < 2);
    let current = bottom ? sections[sections.length - 1] : row[0] || sections[0];
    if (!bottom && row.length > 1) {
      // how far the row has moved up past the line since it could first reach it (at once, for a row the page opens on)
      const r = row[0].getBoundingClientRect();
      const start = Math.max(0, line - (r.top + view.scrollTop));
      const through = Math.min(0.999, Math.max(0, (line - r.top - start) / r.height));
      current = row[Math.floor(through * row.length)];
    }
    const id = pinned || current?.id.slice(6);
    for (const item of element.querySelectorAll("[data-board-go]")) item.classList.toggle("is-current", item.dataset.boardGo === id);
  };
  element.addEventListener("scroll", follow, { passive: true, capture: true });  // the scroller's, caught on the way down

  // a line chart lights the line nearest the pointer, within a finger's width of it, and fades the rest, as Stocks
  // picks a series; nowhere near a line, every line keeps its full colour
  const NEAR = 24;  // screen pixels
  const pointsOf = (path) => [...path.getAttribute("d").matchAll(/[ML]([-\d.]+),([-\d.]+)/g)].map((m) => [Number(m[1]), Number(m[2])]);
  const toSegment = (px, py, [ax, ay], [bx, by]) => {
    const dx = bx - ax, dy = by - ay;
    const t = dx || dy ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) : 0;
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
  };
  const nearest = (chart, event) => {
    const ctm = chart.getScreenCTM();
    if (!ctm) return null;
    const at = new DOMPoint(event.clientX, event.clientY).matrixTransform(ctm.inverse());
    let best = null, gap = NEAR / ctm.a;  // the reach in the chart's own units
    for (const series of chart.querySelectorAll(".board-series")) {
      const pts = pointsOf(series.querySelector(".board-line"));
      const d = pts.length === 1 ? Math.hypot(at.x - pts[0][0], at.y - pts[0][1])
        : Math.min(...pts.slice(1).map((q, i) => toSegment(at.x, at.y, pts[i], q)));
      if (d < gap) { gap = d; best = series; }
    }
    return best;
  };
  const light = (chart, series) => {
    chart.classList.toggle("has-near", Boolean(series));
    for (const s of chart.querySelectorAll(".board-series")) s.classList.toggle("is-near", s === series);
  };
  element.addEventListener("pointermove", (event) => {
    const chart = event.target.closest?.(".board-chart");
    for (const other of element.querySelectorAll(".board-chart.has-near")) if (other !== chart) light(other, null);
    if (chart?.querySelector(".board-series")) light(chart, nearest(chart, event));
  });
  element.addEventListener("pointerleave", () => { for (const c of element.querySelectorAll(".board-chart.has-near")) light(c, null); });

  // a hovered bar's card: its engine's logo and name, the value large, what it rests on in grey, beside the pointer
  const tooltip = document.getElementById("chart-tooltip");
  // a wordmark already spells the engine's name, so its card drops the name after it: MLX's reads "MLX on M4 Max", not "MLX MLX"
  const tipHtml = (g) => {
    const engine = g.dataset.tipEngine;
    const wide = engine === "mlxlm";
    const head = wide ? g.dataset.tipHead.slice(names().engine(engine).length).trim() : g.dataset.tipHead;
    return `<div class="board-tip-head"><svg class="board-tip-logo" ${wide ? 'style="width: 23.8px" viewBox="0 0 27.2 16"' : 'viewBox="0 0 16 16"'} aria-hidden="true">${logo(engine, wide ? 5.6 : 0, 0, 16)}</svg>${esc(head)}</div>
    <div class="board-tip-value">${esc(g.dataset.tipValue)}</div>${g.dataset.tipNote ? `<div class="board-tip-note">${esc(g.dataset.tipNote)}</div>` : ""}`;
  };
  let tipFor = null;
  element.addEventListener("pointermove", (event) => {
    if (Pie.tapCard.isTouch()) return;
    const g = event.target.closest?.(".board-bar[data-tip-head]");
    if (!g) {
      if (tipFor) { tipFor = null; tooltip.hidden = true; tooltip.classList.remove("is-board"); }
      return;
    }
    if (g !== tipFor) {
      tipFor = g;
      tooltip.innerHTML = tipHtml(g);
      tooltip.classList.add("is-board");
      tooltip.hidden = false;
    }
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  });
  const hideTip = () => { tipFor = null; tooltip.hidden = true; tooltip.classList.remove("is-board"); };
  element.addEventListener("pointerleave", hideTip);
  element.addEventListener("scroll", hideTip, { passive: true, capture: true });


  element.addEventListener("click", (event) => {
    const go = event.target.closest("[data-board-go]");
    if (go) {
      pinned = go.dataset.boardGo;
      element.querySelector(`#board-${go.dataset.boardGo}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      follow();
      return;
    }
    // the rankings' Speculation, on or off, as a toolbar's toggle: the three cards redraw on the runs it names
    const toggle = event.target.closest("[data-board-toggle]");
    if (toggle) {
      toggle.blur();
      Pie.board.pick("summary", summaryWorkload === "spec" ? "raw" : "spec");
      Pie.board.render(state);
      return;
    }
    // a block that opens a page of the site, as its sidebar row would (Hardware Recommender: Best TPS until it has its own)
    const opens = event.target.closest("[data-board-open]");
    if (opens) {
      event.preventDefault();
      document.querySelector(`.sidebar-item[data-table="${opens.dataset.boardOpen}"]`)?.click();
      return;
    }
    event.target.closest(".board-card-tool")?.blur();  // a click leaves no focus ring on the button
    // a link to the card: copied, and the button says so a moment with a check, as a Mac's Copy Link does
    const link = event.target.closest("[data-board-link]");
    if (link) {
      const url = `${location.origin}${location.pathname}#board/${link.dataset.boardLink}`;
      navigator.clipboard?.writeText(url).then(() => {
        const was = link.innerHTML;
        link.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3.5 8.5 3 3 6-7"/></svg>';
        link.title = "Copied";
        setTimeout(() => { link.innerHTML = was; link.title = "Copy a link to this chart"; }, 1400);
      }).catch(() => {});
      return;
    }
    // the data behind a card, as a table: for an account only, so one who is not logged in is asked to
    const data = event.target.closest("[data-board-data]");
    if (data) {
      if (!Pie.signedIn()) Pie.account.open();
      else saveData(element.querySelector(`#board-${data.dataset.boardData}`));
      return;
    }
    const save = event.target.closest("[data-board-save]");
    if (save) {
      saveImage(element.querySelector(`#board-${save.dataset.boardSave}`)).catch(() => {});
      return;
    }
    const button = event.target.closest("[data-board-pick]");
    if (!button) return;
    event.stopPropagation();
    Pie.popover.open(button, `board:${button.dataset.boardPick}`, null);
  });

  // a card as an image, as Artificial Analysis lets a chart be downloaded: the card's title and what it measures, the
  // chart as the page draws it in its present theme, and the site's name along the foot, at twice the screen's size.
  // The chart's look lives in the page's stylesheets, so each mark's drawn style is copied onto it; its logos are
  // pictures from the site, folded into the image so it stands alone
  const STYLE = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity",
    "font-family", "font-size", "font-weight", "letter-spacing", "text-anchor", "dominant-baseline", "visibility"];
  const dataUrl = (src) => fetch(src).then((r) => r.blob()).then((blob) => new Promise((done) => {
    const reader = new FileReader();
    reader.onload = () => done(reader.result);
    reader.readAsDataURL(blob);
  }));
  const picture = (src) => new Promise((done, fail) => { const img = new Image(); img.onload = () => done(img); img.onerror = fail; img.src = src; });
  // a download's name says what it holds, as a file one finds later: the site, the card, the pick shown in it, the model
  // for a card about one model, and the day it was saved, e.g. "Pie benchmarks - Performance (Decode) - gpt-oss-20b - 2026-10-26"
  const ON_MODEL = new Set(["metric", USE.id, SCALING.id, "ttft"]);
  // what a card shows, said in full: its title, the pick shown in it, and the model for a card about one model
  const named = (cardElement) => {
    const id = cardElement.id.replace(/^board-/, "");
    const title = [...cardElement.querySelector("h2").childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join("").trim();
    const pick = cardElement.querySelector("[data-board-pick]")?.textContent.trim();
    const on = id === SCALING.id ? scaleModelOf(measured()) : model;  // the datacenter section names its own model
    return { title, pick, model: ON_MODEL.has(id) && on ? names().model(on) : "" };
  };
  const fileName = (cardElement, ext) => {
    const { title, pick, model: on } = named(cardElement);
    const parts = ["Pie benchmarks", pick ? `${title} (${pick})` : title, on, new Date().toISOString().slice(0, 10)].filter(Boolean);
    return `${parts.join(" - ").replace(/[\\/:*?"<>|]/g, "")}.${ext}`;
  };
  // a card's numbers as a CSV file: every bar's name, value and note, or every point's own description on a line chart
  const saveData = (cardElement) => {
    if (!cardElement) return;
    const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const bars = [...cardElement.querySelectorAll(".board-bar[data-tip-head]")].map((g) => [g.dataset.tipHead, g.dataset.tipValue, g.dataset.tipNote]);
    const points = [...cardElement.querySelectorAll(".board-point > title, .board-bar > title")].map((t) => [t.textContent]);
    const rows = bars.length ? [["Name", "Value", "Note"], ...bars] : [["Point"], ...points];
    if (rows.length < 2) return;
    const link = document.createElement("a");
    link.download = fileName(cardElement, "csv");
    link.href = URL.createObjectURL(new Blob([rows.map((r) => r.map(cell).join(",")).join("\n")], { type: "text/csv" }));
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  };
  const saveImage = async (cardElement) => {
    const svg = cardElement?.querySelector("svg.board-chart");
    if (!svg) return;
    const box = svg.getBoundingClientRect();
    const copy = svg.cloneNode(true);
    const from = [svg, ...svg.querySelectorAll("*")], to = [copy, ...copy.querySelectorAll("*")];
    from.forEach((el, i) => {
      const look = getComputedStyle(el);
      // the drawn values only: a mark's own style names the page's colours by variable, which an image cannot look up
      to[i].setAttribute("style", STYLE.map((k) => `${k}:${look.getPropertyValue(k)}`).join(";"));
    });
    // the hover's grey column and the bars' texture: only what the page shows at rest
    for (const band of copy.querySelectorAll(".board-band")) band.remove();
    const defs = document.querySelector(".board-defs defs");
    if (defs) copy.prepend(defs.cloneNode(true));
    await Promise.all([...copy.querySelectorAll("image")].map(async (im) => im.setAttribute("href", await dataUrl(im.getAttribute("href")))));
    copy.setAttribute("width", box.width);
    copy.setAttribute("height", box.height);
    copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const chart = await picture(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(copy))}`);

    const page = getComputedStyle(document.documentElement);
    const ink = (name) => page.getPropertyValue(name).trim();
    // the picture's title says all a reader needs, as its file's name does: "Performance · Decode · gpt-oss-20b"
    const shown = named(cardElement);
    const name = [shown.title, shown.pick, shown.model].filter(Boolean).join(" · ");
    const lines = cardElement.querySelector(".board-sub").innerHTML.split("<br>").map((l) => { const t = document.createElement("span"); t.innerHTML = l; return t.textContent; });
    const pad = 28, scale = 2, W = Math.round(box.width + pad * 2);
    const head = 30 + lines.length * 18 + 18, foot = 34, H = Math.round(head + box.height + foot + pad);
    const canvas = document.createElement("canvas");
    canvas.width = W * scale; canvas.height = H * scale;
    const g = canvas.getContext("2d");
    g.scale(scale, scale);
    g.fillStyle = ink("--color-background") || "#fff";
    g.fillRect(0, 0, W, H);
    const font = getComputedStyle(document.body).fontFamily;
    g.fillStyle = ink("--color-label");
    g.font = `600 17px ${font}`;
    g.fillText(name, pad, pad + 14);
    g.fillStyle = ink("--color-label-secondary");
    g.font = `400 12px ${font}`;
    lines.forEach((l, i) => g.fillText(l, pad, pad + 38 + i * 18));
    g.drawImage(chart, pad, pad + head - 8, box.width, box.height);
    g.fillStyle = ink("--color-label-tertiary");
    g.font = `500 11px ${font}`;
    g.fillText("Pie benchmarks · benchmarks.pie-project.org", pad, H - 16);
    const link = document.createElement("a");
    link.download = fileName(cardElement, "png");
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  Pie.board = {
    element,
    // the model menu: every model this release measured, the widest coverage first
    menu(k) {
      if (k === "use-engine" || k === "scale-engine") {
        const current = k === "use-engine" ? useEngine : scaleEngine;
        // the datacenter card offers the engines that ran on more than one chip; a Mac's engines (llama.cpp, MLX) never do
        const multi = (r) => k !== "scale-engine" || (Pie.store.index.hardware[r.hardware]?.count || 1) > 1;
        const ran = new Set(measured().filter((r) => r.workload === "raw" && r.decode_tok_s && multi(r)).map((r) => r.engine));
        return [{ value: "", label: "Fastest engine", selected: !current },
          ...engineIds().filter((e) => ran.has(e)).map((e) => ({ value: e, label: names().engine(e), selected: e === current, icon: engineMark(e) }))];
      }
      if (k === "scale") {
        const current = scaleModelOf(measured());
        return scaleModels(measured()).map((id) => ({ value: id, label: names().model(id), selected: id === current, icon: Pie.platform.makerBadge(id) }));
      }
      if (k === "size" || k === "moe") return SIZES.map((m) => ({ value: m.id, label: m.label, selected: m.id === (k === "moe" ? moeMetric : sizeMetric), icon: Pie.platform.degree(m.setup) }));
      if (k === "metric") return SPEEDS.map((m) => ({ value: m.id, label: m.label, selected: m.id === modelMetric, icon: metricIcon(m) }));
      if (k !== "model" || !state) return [];
      return models(measured()).map((id) => ({ value: id, label: names().model(id), selected: id === model, icon: Pie.platform.makerBadge(id) }));
    },
    pick(k, value) {
      if (k === "model") model = value;
      if (k === "metric" && SPEEDS.some((m) => m.id === value)) {
        modelMetric = value;
        try { localStorage.setItem(METRIC_KEY, value); } catch { /* private windows can refuse storage */ }
      }
      if (k === "summary" && SUMMARY_WORKLOADS.some((w) => w.id === value)) {
        summaryWorkload = value;
        try { localStorage.setItem(SUMMARY_KEY, value); } catch { /* private windows can refuse storage */ }
      }
      if (k === "use-engine" || k === "scale-engine") {
        const engine = value || null;
        if (k === "use-engine") useEngine = engine; else scaleEngine = engine;
        try { engine ? localStorage.setItem(ENGINE_KEYS[k], engine) : localStorage.removeItem(ENGINE_KEYS[k]); } catch { /* private windows can refuse storage */ }
      }
      if (k === "scale") {
        scaleModel = value;
        try { localStorage.setItem(SCALE_KEY, value); } catch { /* private windows can refuse storage */ }
      }
      if (k === "moe" && SIZES.some((m) => m.id === value)) {
        moeMetric = value;
        try { localStorage.setItem(MOE_KEY, value); } catch { /* private windows can refuse storage */ }
      }
      if (k === "size" && SIZES.some((m) => m.id === value)) {
        sizeMetric = value;
        try { localStorage.setItem(SIZE_KEY, value); } catch { /* private windows can refuse storage */ }
      }
      element.dataset.key = "";
    },
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "board";
      const key = `${model}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        // a pick on the page (Decode or Prefill, the model) redraws it where the viewer is, not back at its top
        const was = element.querySelector(".board-scroll");
        const at = was ? [was.scrollTop, was.scrollLeft] : null;
        element.innerHTML = page();
        element.dataset.key = `${model}@${state.release}`;
        const now = element.querySelector(".board-scroll");
        if (at && now) [now.scrollTop, now.scrollLeft] = at;
        follow();
      }
    },
  };
})();
