window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("board");
  const esc = (text) => Pie.format.escape(text);
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Single Decode", setup: "decode", title: "Decode speed", sub: "Output tokens per second, one request · Higher is better", workload: "raw", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Single Prefill", setup: "prefill", title: "Prefill speed", sub: "Prompt tokens per second, one request · Higher is better", workload: "raw", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "throughput", label: "Batched Decode", setup: "batching", title: "Throughput", sub: "Output tokens per second, 32 requests at once · Higher is better", workload: "throughput", key: "output_tok_s", unit: "tok/s", higher: true },
    { id: "pbatch", label: "Batched Prefill", setup: "pbatch", title: "Batched prefill", sub: "Prompt tokens per second, 256 prompts at once · Higher is better", workload: "prefill_batch", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "ttft", label: "TTFT", title: "TTFT", sub: "Milliseconds, one request with a 512-token prompt · Lower is better", workload: "raw", key: "ttft_ms_p50", unit: "ms", higher: false },
  ];
  const PLATFORM_ORDER = Pie.platformOrder;

  let state = null;
  let model = null;
  let ttftModel = null;
  const machineFor = { metric: {}, ttft: {} };
  let cmpPlatform = null;

  const measured = () => Pie.store.snapshot((state || Pie.state).release).filter(Pie.store.isMeasured);
  const engineIds = () => Pie.store.tables.engines.map((e) => e.id);

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

  const showcase = (rows, picked, sec = "metric") => {
    const raw = rows.filter((r) => r.model === picked && (r.workload === "raw" || r.workload === "throughput" || r.workload === "prefill_batch"));
    const byPlatform = {};
    for (const r of raw) {
      const p = Pie.platformOf(Pie.store.index.hardware[r.hardware] || {});
      if (!p) continue;
      ((byPlatform[p] ||= {})[r.hardware] ||= new Set()).add(`${r.engine}/${r.workload}`);
    }
    return PLATFORM_ORDER.filter((p) => byPlatform[p]).map((p) => {
      const [hardware] = Object.entries(byPlatform[p]).sort((a, b) => b[1].size - a[1].size
        || raw.filter((r) => r.hardware === b[0]).length - raw.filter((r) => r.hardware === a[0]).length)[0];
      const own = machineFor[sec]?.[p];
      return { platform: p, hardware: own && byPlatform[p][own] ? own : hardware, choices: Object.keys(byPlatform[p]).sort((a, b) => machineName(a).localeCompare(machineName(b), undefined, { numeric: true })) };
    });
  };

  const compact = (v) => (v === 0 ? "0" : v >= 10000 ? `${Math.round(v / 1000)}K` : v >= 1000 ? `${(v / 1000).toFixed(1)}K` : v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(0) : v.toFixed(1));
  const full = (v, unit) => `${v >= 100 ? Math.round(v).toLocaleString() : v.toFixed(1)} ${unit}`;
  const machineName = (id) => Pie.platform.machineName(id);
  const niceMax = (v) => {
    const p = 10 ** Math.floor(Math.log10(v));
    return [1, 2, 2.5, 5, 10].map((m) => m * p).find((m) => m >= v);
  };

  const column = (x, y, w, h) => {
    const r = Math.min(4, h, w / 2);
    return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
  };
  const bar = (x, top, w, base, color, value, tip, band = { x: x - 4, w: w + 8 }) => {
    const inside = w >= 20 && base - top >= 24;
    return `<g class="board-bar" aria-label="${esc(`${tip.head}: ${tip.value}`)}" data-tip-engine="${esc(tip.engine)}" data-tip-head="${esc(tip.head)}" data-tip-value="${esc(tip.value)}" data-tip-note="${esc(tip.note || "")}"${tip.rows?.length ? ` data-tip-rows="${esc(JSON.stringify(tip.rows))}"` : ""}>
      <rect class="board-band" x="${band.x}" y="0" width="${band.w}" height="${base}"/>
      <path d="${column(x, top, w, Math.max(base - top, 1))}" style="fill: ${color}"/>
      ${tip.top ? `<path class="board-sheen" d="${column(x, top, w, Math.max(base - top, 1))}"/>` : ""}
      <text class="board-value${inside ? " is-inside" : ""}" x="${x + w / 2}" y="${inside ? (top + base) / 2 : top - 6}">${value}</text>
</g>`;
  };
  const lines = (L, R, y, top) => [top / 2, top].map((t) => `<line class="board-grid" x1="${L}" x2="${R}" y1="${y(t)}" y2="${y(t)}"/>`).join("");

  const SUMMARY_KEY = "pieSummaryWorkload";
  const SUMMARY_WORKLOADS = [{ id: "raw", label: "Decode", setup: "decode" }, { id: "spec", label: "Spec Decode", setup: "spec" }];
  let summaryWorkload = (() => { try { const k = localStorage.getItem(SUMMARY_KEY); return SUMMARY_WORKLOADS.some((w) => w.id === k) ? k : "raw"; } catch { return "raw"; } })();
  const setups = (rows, key) => {
    const by = {};
    for (const r of rows) if ((r.workload === "raw" || r.workload === "spec") && r[key]) {
      const s = (by[`${r.hardware}|${r.model}`] ||= {});
      s[r.engine] = Math.max(s[r.engine] || 0, r[key]);
    }
    return Object.values(by).filter((s) => Object.keys(s).length > 1);
  };
  const onPlatform = (rows, ids) => rows.filter((r) => ids.includes(Pie.platformOf(Pie.store.index.hardware[r.hardware] || {})));
  const SUMMARY = [["index-mac", "Apple", ["mac"]], ["index-windows", "Windows", ["windows"]], ["index-gpu", "NVIDIA", ["nvidia"]], ["index-amd", "AMD", ["amd"]], ["index-tpu", "TPU", ["tpu"]], ["index-android", "Mobile", ["android"]], ["index-web", "Browser", ["web"]]].filter(([, , ids]) => !ids.some((p) => Pie.hiddenPlatforms.has(p))).map(([id, title, ids]) => ({
    id, title, ids, sub: "Chance to decode faster than an average engine",
    value: (rows, engine) => strengths(rows, ids)[engine] || null,
    label: (v) => `${Math.round(v)}%`,
  }));
  const GRID_KEY = "pieGridCards3";
  const gridCards = new Set(window.matchMedia("(max-width: 899px)").matches ? [] : (() => { try { return JSON.parse(localStorage.getItem(GRID_KEY)) ?? []; } catch { return []; } })());
  const BARS_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 13V8M8 13V3.5M12 13V6.5"/></svg>';
  const GRID_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="4.5" height="4.5" rx="1"/><rect x="9" y="2.5" width="4.5" height="4.5" rx="1"/><rect x="2.5" y="9" width="4.5" height="4.5" rx="1"/><rect x="9" y="9" width="4.5" height="4.5" rx="1"/></svg>';
  const viewToggle = (id, first = [BARS_ICON, "Bars"], grid = "Head-to-head grid") => `<span class="platform-compare board-view" role="group" aria-label="View">
      <button type="button" class="plain-button${gridCards.has(id) ? "" : " is-active"}" data-board-view="${id}" data-view="bars" aria-label="${first[1]}" title="${first[1]}">${first[0]}</button>
      <button type="button" class="plain-button${gridCards.has(id) ? " is-active" : ""}" data-board-view="${id}" data-view="grid" aria-label="${grid}" title="${grid}">${GRID_ICON}</button>
    </span>`;
  const CHECKS_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7"/></svg>';
  const btCache = new Map();
  const strengths = (rows, platforms) => {
    const key = platforms.join();
    if (btCache.get(key)?.rows === rows) return btCache.get(key).out;
    const all = setups(onPlatform(rows, platforms), "decode_tok_s");
    const ids = engineIds().filter((e) => all.some((s) => s[e]));
    const wins = {}, games = {};
    for (const a of ids) for (const b of ids) if (a !== b) {
      const met = all.filter((s) => s[a] && s[b]);
      if (!met.length) continue;
      wins[`${a}|${b}`] = met.filter((s) => s[a] > s[b]).length + .5;
      games[`${a}|${b}`] = met.length + 1;
    }
    let p = Object.fromEntries(ids.map((e) => [e, 1]));
    for (let step = 0; step < 200; step++) {
      const next = {};
      for (const a of ids) {
        const others = ids.filter((b) => games[`${a}|${b}`]);
        const w = others.reduce((n, b) => n + wins[`${a}|${b}`], 0);
        const d = others.reduce((n, b) => n + games[`${a}|${b}`] / (p[a] + p[b]), 0);
        next[a] = d ? w / d : p[a];
      }
      const g = Math.exp(ids.reduce((n, e) => n + Math.log(next[e]), 0) / ids.length);
      p = Object.fromEntries(ids.map((e) => [e, next[e] / g]));
    }
    const out = Object.fromEntries(ids.filter(() => ids.length > 1).map((e) => [e, { v: 100 * p[e] / (p[e] + 1), n: all.filter((s) => s[e]).length }]));
    btCache.set(key, { rows, out });
    return out;
  };
  const matrix = (summary, rows) => {
    const all = setups(onPlatform(rows, summary.ids), "decode_tok_s");
    const won = (a, b) => all.filter((s) => s[a] && s[b] && s[a] > s[b]).length;
    const played = (a, b) => all.filter((s) => s[a] && s[b]).length;
    const ids = engineIds().filter((e) => all.some((s) => s[e]));
    if (ids.length < 2) return `<p class="board-empty">No runs yet</p>`;
    const own = onPlatform(rows, summary.ids).filter((r) => r.decode_tok_s);
    const spec = new Set(ids.filter((e) => !own.some((r) => r.engine === e && r.workload === "raw")));
    const rate = (a) => { const r = ids.filter((b) => b !== a && played(a, b)).map((b) => won(a, b) / played(a, b)); return r.length ? r.reduce((x, y) => x + y, 0) / r.length : 0; };
    const order = [...ids].sort((a, b) => rate(b) - rate(a));
    const mark = (e) => `<svg class="board-matrix-logo${WIDE.has(e) ? " is-wide" : ""}" viewBox="${WIDE.has(e) ? "-6 0 28 16" : "0 0 16 16"}" aria-hidden="true">${e === "splash" ? '<image href="assets/img/engines/splash-glyph.png" width="16" height="16"/>' : logo(e, 0, 0, 16)}</svg>`;
    const name = (e) => `<span class="board-matrix-name">${esc(SHORT[e] || names().engine(e))}</span>`;
    const head = (e, row) => `<span class="board-matrix-engine${row ? "" : " is-col"}">${name(e)}<span class="board-matrix-slot">${mark(e)}</span></span>`;
    const cell = (a, b) => {
      if (a === b) return `<td class="is-self"></td>`;
      const w = won(a, b), n = played(a, b);
      if (!n) return `<td class="is-none">–</td>`;
      const share = w / n, step = Math.min(4, Math.floor(Math.abs(share - .5) * 20 + .5) >> 1);
      return `<td class="${step ? (share > .5 ? "is-win" : "is-loss") : ""}${spec.has(a) || spec.has(b) ? " is-spec" : ""}" data-step="${step}" data-tip-engine="${esc(a)}" data-tip-vs="${esc(b)}" data-tip-head="${esc(`${names().engine(a)} vs ${names().engine(b)}`)}" data-tip-value="${share.toFixed(2)}" data-tip-note="${w} of ${n}">${share.toFixed(2)}</td>`;
    };
    const key = `<span class="board-matrix-key" aria-hidden="true"><span class="board-matrix-tick">1</span><span class="board-matrix-bar">${[4, 3, 2, 1].map((k) => `<i class="is-win" data-step="${k}"></i>`).join("")}<i data-step="0"></i>${[1, 2, 3, 4].map((k) => `<i class="is-loss" data-step="${k}"></i>`).join("")}</span><span class="board-matrix-tick">0</span></span>`;
    return `<div class="board-matrix-frame"><span class="board-matrix-axis is-a"><span>Engine A</span></span><span class="board-matrix-axis is-b">Engine B</span>${key}${spec.size ? '<span class="board-matrix-spec"><i></i>Speculative</span>' : ""}<table class="board-matrix">
      <thead><tr><th></th>${order.map((e) => `<th scope="col">${head(e, false)}</th>`).join("")}</tr></thead>
      <tbody>${order.map((a) => `<tr><th scope="row">${head(a, true)}</th>${order.map((b) => cell(a, b)).join("")}</tr>`).join("")}</tbody>
    </table></div>`;
  };

  const GLYPHS = {
    trtllm: ["0 0 24 24", '<path fill="#76b900" d="M8.948 8.798v-1.43a6.7 6.7 0 0 1 .424-.018c3.922-.124 6.493 3.374 6.493 3.374s-2.774 3.851-5.75 3.851c-.398 0-.787-.062-1.158-.185v-4.346c1.528.185 1.837.857 2.747 2.385l2.04-1.714s-1.492-1.952-4-1.952a6.016 6.016 0 0 0-.796.035m0-4.735v2.138l.424-.027c5.45-.185 9.01 4.47 9.01 4.47s-4.08 4.964-8.33 4.964c-.37 0-.733-.035-1.095-.097v1.325c.3.035.61.062.91.062 3.957 0 6.82-2.023 9.593-4.408.459.371 2.34 1.263 2.73 1.652-2.633 2.208-8.772 3.984-12.253 3.984-.335 0-.653-.018-.971-.053v1.864H24V4.063zm0 10.326v1.131c-3.657-.654-4.673-4.46-4.673-4.46s1.758-1.944 4.673-2.262v1.237H8.94c-1.528-.186-2.73 1.245-2.73 1.245s.68 2.412 2.739 3.11M2.456 10.9s2.164-3.197 6.5-3.533V6.201C4.153 6.59 0 10.653 0 10.653s2.35 6.802 8.948 7.42v-1.237c-4.84-.6-6.492-5.936-6.492-5.936z"/>'],
    pie: ["0 0 67.89 67.89", '<path class="is-stroked" d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z" stroke-width="8"/>'],
    mlxlm: ["13 -42 414 224", '<g><path transform="translate(0 139.72)" d="M 13.9375 0 L 42.3125 0 L 42.3125 -91.796875 L 43.671875 -91.796875 L 78.71875 0 L 97.984375 0 L 133.03125 -91.796875 L 134.390625 -91.796875 L 134.390625 0 L 162.765625 0 L 162.765625 -139.71875 L 125.96875 -139.71875 L 88.984375 -42.015625 L 87.8125 -42.015625 L 50.734375 -139.71875 L 13.9375 -139.71875 Z M 13.9375 0"/><path transform="translate(176.682092 139.72)" d="M 13.9375 0 L 106.21875 0 L 106.21875 -26.046875 L 45.984375 -26.046875 L 45.984375 -139.71875 L 13.9375 -139.71875 Z M 13.9375 0"/></g><g class="is-faint"><path transform="translate(290.57 139.72)" d="M 6.296875 0 L 40.5625 0 L 69.515625 -47.34375 L 70.484375 -47.34375 L 99.625 0 L 135.84375 0 L 91.109375 -69.8125 L 91.109375 -70.296875 L 136.328125 -139.71875 L 100.703125 -139.71875 L 73 -90.71875 L 71.84375 -90.71875 L 43.953125 -139.71875 L 6.484375 -139.71875 L 49.96875 -70.6875 L 49.96875 -70.296875 Z M 6.296875 0"/></g>'],
  };
  GLYPHS["mlx-swift"] = GLYPHS.mlxlm;
  const WIDE = new Set(["mlxlm", "mlx-swift"]);
  const FILES = { vllm: "vllm.svg", "vllm-metal": "vllm.svg", sglang: "sglang.svg", llamacpp: "llamacpp.png", "llamacpp-webgpu": "llamacpp.png", webllm: "mlc.svg", mlc: "mlc.svg", splash: "splash.png", litert: "litert.svg", ollama: "ollama.png", atom: "atom.svg" };
  const logo = (engine, x, y, size) => GLYPHS[engine]
    ? `<svg class="board-glyph" x="${x}" y="${y}" width="${size}" height="${size}" viewBox="${GLYPHS[engine][0]}">${GLYPHS[engine][1]}</svg>`
    : FILES[engine] ? `<image class="board-logo" href="assets/img/engines/${FILES[engine]}" x="${x}" y="${y}" width="${size}" height="${size}"/>` : "";
  Pie.engines.logo = (engine) => (GLYPHS[engine]
    ? `<svg class="engine-logo is-glyph" viewBox="${GLYPHS[engine][0]}" aria-hidden="true">${GLYPHS[engine][1]}</svg>`
    : FILES[engine] ? `<img class="engine-logo${engine === "splash" ? " is-tile" : ""}" src="assets/img/engines/${FILES[engine]}" alt="" aria-hidden="true">` : "");
  const SHORT = { llamacpp: "Llama" };
  const paddlesFor = (row) => `<span class="platform-compare board-view board-carousel-nav" role="group" aria-label="Platforms" data-carousel-nav="${row}"><button type="button" class="plain-button" data-carousel="-1" data-carousel-for="${row}" aria-label="Previous platforms" title="Previous"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5"/></svg></button><button type="button" class="plain-button" data-carousel="1" data-carousel-for="${row}" aria-label="Next platforms" title="Next"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button></span>`;
  const ranking = (summary, rows) => {
    const W = summary.width || 456, H = 185, L = summary.left ?? 24, R = 4, T = 10, B = 44;
    const list = engineIds().map((engine) => ({ engine, ...summary.value(rows, engine) })).filter((e) => e.v !== undefined && e.v !== null)
      .sort((a, b) => (summary.ascending ? a.v - b.v : b.v - a.v));
    if (!list.length) return `<p class="board-empty">${esc(summary.empty || "No runs yet")}</p>`;
    const top = summary.top ? summary.top(list) : summary.id === "coverage" ? niceMax(list[0].v) : 100;
    const base = H - B;
    const y = (v) => T + (base - T) * (1 - v / top);
    const slot = (W - L - R) / list.length;
    const BW = Math.min(slot * .86, summary.widest || Infinity);
    const marks = list.map((e, i) => {
      const x = L + slot * i + (slot - BW) / 2;
      const cx = x + BW / 2;
      const tip = { top: i === 0, engine: e.engine, head: names().engine(e.engine), value: (summary.tip || summary.label)(e.v),
        note: e.detail || `Over ${e.n} ${e.n === 1 ? "setup" : "setups"}`, rows: e.rows };
      return `${bar(x, y(e.v), BW, base, Pie.engines.colorOf(e.engine), summary.label(e.v), tip, { x: L + slot * i, w: slot })}
        ${logo(e.engine, cx - 8, base + 6, 16)}
        <text class="board-group" x="${cx}" y="${base + 36}">${esc(SHORT[e.engine] || names().engine(e.engine))}</text>
`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${summary.title} by engine`)}">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>`;
  };

  const rowsChart = (summary, rows) => {
    const list = engineIds().map((engine) => ({ engine, ...summary.value(rows, engine) })).filter((e) => e.v !== undefined && e.v !== null)
      .sort((a, b) => (summary.ascending ? a.v - b.v : b.v - a.v));
    if (!list.length) return `<p class="board-empty">${esc(summary.empty || "No runs yet")}</p>`;
    const top = Math.max(...list.map((e) => e.v));
    return `<div class="speed-rows" role="list" aria-label="${esc(`${summary.title} by engine`)}">${list.map((e, i) => {
      const head = names().engine(e.engine), value = (summary.tip || summary.label)(e.v);
      return `<div class="board-bar speed-row${i === 0 ? " is-top" : ""}" role="listitem" aria-label="${esc(`${head}: ${value}`)}" data-tip-engine="${esc(e.engine)}" data-tip-head="${esc(head)}" data-tip-value="${esc(value)}" data-tip-note="${esc(e.detail || "")}">
        <span class="speed-name">${Pie.engines.logo(e.engine) || '<span class="engine-logo"></span>'}<span>${esc(head)}</span></span>
        <span class="speed-track"><span class="speed-fill" style="width: ${Math.max(1, (100 * e.v) / top).toFixed(2)}%; background: ${Pie.engines.colorOf(e.engine)}"></span></span>
        <span class="speed-value">${summary.label(e.v)}</span></div>`;
    }).join("")}</div>`;
  };

  const GAIN = { id: "gain", title: "Spread", sub: "Each engine's typical speed against the median of all engines on the same machine and model" };
  const GAIN_SETUPS = [
    { workload: "raw", key: "decode_tok_s", label: "Single decode", unit: "tok/s" },
    { workload: "raw", key: "prefill_tok_s", label: "Single prefill", unit: "tok/s" },
    { workload: "spec", key: "decode_tok_s", label: "Spec decode", unit: "tok/s" },
    { workload: "throughput", key: "output_tok_s", label: "Batched decode", unit: "tok/s" },
    { workload: "prefill_batch", key: "prefill_tok_s", label: "Batched prefill", unit: "tok/s" },
  ];
  const signedPct = (g) => `${g >= 0 ? "+" : "−"}${Math.abs(Math.round(g * 100))}%`;
  const GAIN_PICKS = [
    { id: "decode", label: "Single Decode", workload: "raw", key: "decode_tok_s" },
    { id: "prefill", label: "Single Prefill", workload: "raw", key: "prefill_tok_s" },
    { id: "batching", label: "Batched Decode", workload: "throughput", key: "output_tok_s" },
    { id: "pbatch", label: "Batched Prefill", workload: "prefill_batch", key: "prefill_tok_s" },
  ];
  const GAIN_KEY = "pieGainSetup";
  let gainSetup = (() => { try { const k = localStorage.getItem(GAIN_KEY); return GAIN_PICKS.some((g) => g.id === k) ? k : "decode"; } catch { return "decode"; } })();
  const limitOf = (pie, pick) => (pick.workload === "raw" ? Pie.ceiling?.(pie, pick.id)?.tps
    : pick.workload === "throughput" ? Pie.batchedCeiling?.(pie.hardware, pie.model, pie.scheme, pie.benchmark, pie)?.tps
    : pick.workload === "prefill_batch" ? Pie.ceiling?.(pie, "pbatch")?.tps : null) || null;
  let gainEngine = (() => { try { const e = localStorage.getItem("pieGainEngine"); return e && Pie.store.tables.engines.some((x) => x.id === e) ? e : "pie"; } catch { return "pie"; } })();
  const gainCells = (rows, only = null, subject = gainEngine) => {
    const cells = [];
    for (const s of GAIN_SETUPS.filter((g) => !only || (g.workload === only.workload && g.key === only.key))) {
      const by = {};
      for (const r of rows) if (r.workload === s.workload && r[s.key]) (by[`${r.hardware}|${r.model}|${r.miniature || ""}|${r.benchmark || ""}`] ||= []).push(r);
      for (const list of Object.values(by)) {
        const pie = list.find((r) => r.engine === subject);
        const others = list.filter((r) => r.engine !== subject);
        if (!pie || !others.length) continue;
        const best = others.reduce((a, b) => (b[s.key] > a[s.key] ? b : a));
        const limit = only ? limitOf(pie, only) : null;
        cells.push({ s, pie, best, gain: pie[s.key] / best[s.key] - 1, room: limit ? limit / best[s.key] - 1 : null, platform: Pie.platformOf(Pie.store.index.hardware[pie.hardware] || {}) });
      }
    }
    return cells;
  };
  const jitter = (text) => {
    let h = 2166136261;
    for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
    return ((h >>> 0) / 4294967295) * 2 - 1;
  };
  const pastLimit = (c) => !c.pie.miniature && c.room != null && c.gain > c.room;
  const isRed = (c) => c.gain < 0 || pastLimit(c);
  const SPREAD = 0.5;
  const gains = (rows) => {
    const pick = GAIN_PICKS.find((g) => g.id === gainSetup);
    const by = {};
    for (const r of rows) if (r.workload === pick.workload && r[pick.key]) (by[`${r.hardware}|${r.model}|${r.miniature || ""}|${r.benchmark || ""}`] ||= []).push(r);
    const dots = [];
    for (const list of Object.values(by)) {
      if (list.length < 2) continue;
      const v = list.map((r) => r[pick.key]).sort((x, y) => x - y), n = v.length;
      const med = n % 2 ? v[(n - 1) / 2] : (v[n / 2 - 1] + v[n / 2]) / 2;
      for (const r of list) {
        const limit = r.miniature ? null : limitOf(r, pick);
        dots.push({ r, d: r[pick.key] / med - 1, med, over: Boolean(limit && r[pick.key] > limit), platform: Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) });
      }
    }
    const mid = (v) => { const a = [...v].sort((p, q) => p - q), n = a.length; return n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2; };
    const order = engineIds();
    const groups = PLATFORM_ORDER.map((p) => {
      const mine = dots.filter((d) => d.platform === p);
      const engines = [...new Set(mine.map((d) => d.r.engine))].sort((x, y) => order.indexOf(x) - order.indexOf(y))
        .map((e) => { const ds = mine.filter((d) => d.r.engine === e); return { e, d: mid(ds.map((x) => x.d)), n: ds.length, over: ds.filter((x) => x.over).length }; });
      return { p, engines };
    }).filter((g) => g.engines.length);
    if (!groups.length) return `<p class="board-empty">No runs yet</p>`;
    const SCALE = 0.2;
    const W = 1040, ROW = 26, GAP = 18, NAME = 170, L = NAME + 16, R = 60, T = 6, B = 26;
    const H = T + groups.reduce((h, g) => h + g.engines.length * ROW + GAP, 0) + B;
    const x = (d) => L + (W - L - R) * (Math.max(-SCALE, Math.min(SCALE, d)) + SCALE) / (2 * SCALE);
    const pct = (d) => (Math.round(d * 100) ? `${d > 0 ? "+" : "−"}${Math.abs(Math.round(d * 100))}%` : "0%");
    let y = T;
    const body = groups.map((g) => {
      const head = `<text class="board-row-name" x="8" y="${y + 15}"><tspan class="board-row-platform">${esc(Pie.schema[g.p]?.short || g.p)}</tspan></text>`;
      const rows = g.engines.map((e, i) => {
        const top = y + i * ROW, cy = top + ROW / 2;
        const x0 = x(0), x1 = x(e.d), w = Math.max(2, Math.abs(x1 - x0));
        const note = `${e.n} ${e.n === 1 ? "cell" : "cells"}${e.over ? `, ${e.over} above the theoretical limit` : ""}`;
        return `<g class="board-bar" data-tip-engine="${esc(e.e)}" data-tip-head="${esc(names().engine(e.e))}" data-tip-value="${esc(pct(e.d))}" data-tip-rows="${esc(JSON.stringify([["Typical distance from the median", pct(e.d)], ["Over", note]]))}">
          <rect class="board-hit" x="0" y="${top}" width="${W}" height="${ROW}"/>
          <rect x="${NAME - 70}" y="${cy - 4}" width="8" height="8" rx="2" style="fill: ${Pie.engines.colorOf(e.e)}"/>
          <text class="board-machine is-start" x="${NAME - 56}" y="${cy + 4}">${esc(names().engine(e.e))}</text>
          <rect x="${Math.min(x0, x1)}" y="${cy - 7}" width="${w}" height="14" rx="3" style="fill: ${Pie.engines.colorOf(e.e)}"/>
          <text class="board-value is-start" x="${Math.max(x0, x1) + 6}" y="${cy + 4}">${pct(e.d)}</text></g>`;
      }).join("");
      const out = head + rows;
      y += g.engines.length * ROW + GAP;
      return out;
    }).join("");
    const ticks = [-SCALE, -SCALE / 2, 0, SCALE / 2, SCALE].map((t) => `<line class="board-grid" x1="${x(t)}" x2="${x(t)}" y1="${T}" y2="${H - B}"/><text class="board-tick" x="${x(t)}" y="${H - B + 18}">${t ? pct(t) : "Median"}</text>`).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(GAIN.title)}">${ticks}<line class="board-band-edge" x1="${x(0)}" x2="${x(0)}" y1="${T}" y2="${H - B}"/>${body}</svg>`;
  };

  const SIZES = [
    { id: "size-decode", label: "Decode", setup: "decode", title: "Decode speed by model size", sub: "Output tokens per second, one request, against parameters · Higher is better", key: "decode_tok_s", unit: "tok/s" },
    { id: "size-prefill", label: "Prefill", setup: "prefill", title: "Prefill speed by model size", sub: "Prompt tokens per second, one request, against parameters · Higher is better", key: "prefill_tok_s", unit: "tok/s" },
  ];
  const ENGINE_KEYS = { "use-engine": "pieUseEngine", "scale-engine": "pieScaleEngine" };
  const keptEngine = (k) => { try { const e = localStorage.getItem(ENGINE_KEYS[k]); return Pie.store.tables.engines.some((x) => x.id === e) ? e : null; } catch { return null; } };
  let useEngine = keptEngine("use-engine"), scaleEngine = keptEngine("scale-engine");
  const USE_MODES = [
    { id: "decode", label: "Single Decode", workload: "raw", key: "decode_tok_s" },
    { id: "prefill", label: "Single Prefill", workload: "raw", key: "prefill_tok_s" },
    { id: "batching", label: "Batched Decode", workload: "throughput", key: "output_tok_s" },
    { id: "pbatch", label: "Batched Prefill", workload: "prefill_batch", key: "prefill_tok_s" },
  ];
  const kept = (k, ok, fallback) => { try { const v = localStorage.getItem(k); return ok(v) ? v : fallback; } catch { return fallback; } };
  let useMode = kept("pieUseMode", (v) => USE_MODES.some((m) => m.id === v), "decode");
  const useModel = "";
  const engineMark = (engine) => engine ? `<svg class="board-pick-logo${WIDE.has(engine) ? " is-wide" : ""}" viewBox="${WIDE.has(engine) ? "-5.6 0 27.2 16" : "0 0 16 16"}" aria-hidden="true">${logo(engine, 0, 0, 16)}</svg>` : "";
  const enginePick = (k, engine) => `<button class="filter-button board-card-pick" type="button" data-board-pick="${k}" aria-haspopup="menu" aria-label="Engine">${engineMark(engine)}${engine === "mlxlm" ? "" : esc(engine ? names().engine(engine) : "Fastest engine")}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  const engineSub = (sub, engine) => (engine ? sub.replace("fastest engine", names().engine(engine)).replace("Decode speed against", `${names().engine(engine)}'s decode speed against`) : sub);
  const SPEEDS = METRICS.filter((m) => m.setup);
  const TTFT = METRICS.find((m) => m.id === "ttft");
  const metricIcon = (m) => Pie.platform.degree(m.setup);
  const gainPick = () => {
    const g = GAIN_PICKS.find((x) => x.id === gainSetup);
    const enginePickButton = `<button class="filter-button board-card-pick" type="button" data-board-pick="gain-engine" aria-haspopup="menu" aria-label="Engine">${engineMark(gainEngine)}${gainEngine === "mlxlm" ? "" : esc(names().engine(gainEngine))}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
    return `<span class="board-card-picks"><button class="filter-button board-card-pick" type="button" data-board-pick="gain-setup" aria-haspopup="menu" aria-label="Setup">${Pie.platform.degree(g.id)}${esc(g.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`;
  };
  const BY_MODEL = { mac: ["Apple", "#636366"], windows: ["Windows", "#0078D4"], nvidia: ["NVIDIA", "#76b900"], amd: ["AMD", "#ed1c24"], tpu: ["TPU", "#4285f4"], android: ["Mobile", "#1C1C1E"], web: ["Browser", "#8e8e93"] };
  const modelSummary = (metric, rows, g, m = model) => {
    const own = rows.filter((r) => r.workload === metric.workload && r.model === m && r.hardware === g.hardware && r[metric.key]);
    return { id: g.platform, title: `${metric.label} on ${machineName(g.hardware)}`, ascending: metric.higher === false,
      top: (list) => niceMax(Math.max(...list.map((e) => e.v))), label: compact, tip: (v) => full(v, metric.unit), empty: "No runs for this model yet",
      value: (_, engine) => {
        const r = own.find((x) => x.engine === engine);
        return r ? { v: r[metric.key], detail: `${names().model(m)} on ${machineName(g.hardware)}` } : {};
      } };
  };
  const fullRows = (rows) => rows.filter((r) => !r.miniature);
  const machinesOf = (rows, p) => [...new Set(fullRows(rows).filter((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) === p).map((r) => r.hardware))]
    .sort((a, b) => machineName(a).localeCompare(machineName(b), undefined, { numeric: true }));
  const comparePick = (rows) => {
    const list = PLATFORM_ORDER.filter((p) => machinesOf(rows, p).length);
    const best = showcase(fullRows(rows), model, "metric");
    const p = list.includes(cmpPlatform) ? cmpPlatform : best[0]?.platform || list[0];
    const machines = machinesOf(rows, p), own = machineFor.metric[p];
    return { list, p, machines, hw: machines.includes(own) ? own : best.find((g) => g.platform === p)?.hardware || machines[0] };
  };
  const specRows = (id) => {
    const hw = Pie.store.index.hardware[id];
    if (!hw) return [];
    const n = (v) => (v >= 100 ? Math.round(v).toLocaleString("en-US") : String(v));
    const chip = String(hw.name || id).replace(/^Apple\s+/, "");
    return [["Chip", hw.count > 1 ? `${hw.count}× ${chip}` : chip], hw.memory_gib && ["Memory", `${hw.memory_gib} GB${hw.interconnect === "uma" ? " unified" : hw.memory_type ? ` ${hw.memory_type}` : ""}`],
      hw.bandwidth_gbs && ["Bandwidth", `${n(hw.bandwidth_gbs)} GB/s`], hw.tflops_fp16 && ["Compute", `${n(hw.tflops_fp16)} FP16 TFLOPS`]].filter(Boolean);
  };
  const modelRows = (id) => {
    const m = Pie.store.index.models[id] || {};
    return [["Maker", Pie.platform?.makerName?.(id)], ["Architecture", m.architecture], ["Parameters", m.params_b && `${m.params_b}B`],
      ["Active", m.active_b && m.active_b !== m.params_b && `${m.active_b}B a token`], ["Layers", m.layers],
      ["Experts", m.experts && `${m.experts}${m.top_k ? `, ${m.top_k} a token` : ""}`], ["Context", m.context && `${Number(m.context).toLocaleString("en-US")} tokens`]]
      .filter(([, v]) => v).map(([k, v]) => [k, String(v)]);
  };
  const INFO = '<svg class="board-compare-info" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg>';
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>';
  const headPick = (k, label, title) => `<button class="filter-button board-title-pick is-text" type="button" data-board-pick="${k}" aria-haspopup="menu" aria-label="${label}" title="${esc(title)}">${label}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  const speedPanel = (metric, full, g) => {
    const ran = full.some((r) => r.workload === metric.workload && r.model === model && r.hardware === g.hardware && r[metric.key]);
    const head = `<div class="board-speed-head">${metricIcon(metric)}<b>${esc(metric.label)}</b></div>`;
    return `<div class="board-speed-cell">${head}${ran ? rowsChart(modelSummary(metric, full, g, model), full) : '<div class="board-compare-empty is-quiet"><span>Not measured yet</span></div>'}</div>`;
  };
  const SPEED_GRID = ["decode", "prefill", "throughput", "pbatch"].map((id) => SPEEDS.find((m) => m.id === id));
  const compareBlock = (rows, c) => {
    if (!c.p) return `<p class="board-empty">No runs for this model yet</p>`;
    const full = fullRows(rows), g = { platform: c.p, hardware: c.hw };
    const ran = SPEED_GRID.some((m) => full.some((r) => r.workload === m.workload && r.model === model && r.hardware === c.hw && r[m.key]));
    const needs = !ran && Object.values(Pie.store.tables.no_fit?.[c.hw]?.[model] || {}).find(Boolean);
    const body = ran ? `<div class="board-speed-grid">${SPEED_GRID.map((m) => speedPanel(m, full, g)).join("")}</div>`
      : `<div class="board-compare-empty">${needs ? `${NOFIT}<b>Doesn't fit on this machine</b><span>This model needs about ${Math.round(needs)} GB of memory.</span>` : "<b>Not measured yet</b><span>No results for this model on this machine.</span>"}</div>`;
    const spec = specRows(c.hw), name = esc(machineName(c.hw));
    const glyph = `<span class="sidebar-glyph" style="--tint: ${Pie.schema[c.p]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(c.p)}</span>`;
    const named = `${glyph}${spec.length ? `<span class="board-compare-name" tabindex="0" data-tip-head="${name}" data-tip-rows="${esc(JSON.stringify(spec))}">${name}${INFO}</span>` : name}<span class="board-compare-model">${Pie.platform?.makerBadge?.(model) || ""}<span class="board-compare-name" tabindex="0" data-tip-head="${esc(names().model(model))}" data-tip-rows="${esc(JSON.stringify(modelRows(model)))}">${esc(names().model(model))}${INFO}</span></span></h2>`;
    return card(`metric-${c.p}`, machineName(c.hw), "", body, "", false).replace('class="board-card"', 'class="board-card board-compare"').replace(`${name}</h2>`, named);
  };
  const SIZE_KEY = "pieSizeMetric";
  let sizeMetric = (() => { try { const k = localStorage.getItem(SIZE_KEY); return SIZES.some((m) => m.id === k) ? k : SIZES[0].id; } catch { return SIZES[0].id; } })();
  const sizePick = (k, m) => `<button class="filter-button board-card-pick" type="button" data-board-pick="${k}" aria-haspopup="menu" aria-label="Speed">${Pie.platform.degree(m.setup)}${esc(m.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  const sizeCard = (rows) => {
    const m = SIZES.find((x) => x.id === sizeMetric) || SIZES[0];
    return card("size", "Dense models by size", m.sub, scatter({ ...m, title: "Dense models by size" }, rows, sizeOf), sizePick("size", m));
  };
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
  const activeOf = (id) => {
    const m = Pie.store.index.models[id];
    return m && m.architecture !== "dense" ? m.active_b : null;
  };
  const sizeSeries = (rows, key, of) => {
    const raw = rows.filter((r) => r.workload === "raw" && r[key] && of(r.model));
    return PLATFORM_ORDER.map((platform) => {
      const own = raw.filter((r) => Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) === platform);
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

  const SCALING = { id: "scaling", title: "Scaling with chip count", sub: "Decode speed against the fewest chips, one request · The dashed line is perfect scaling" };
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

  const USE = { id: "use", title: "Share of the theoretical maximum" };
  const USE_CARDS = [["use", "Apple", "mac"], ["use-windows", "Windows", "windows"], ["use-nvidia", "NVIDIA", "nvidia"], ["use-amd", "AMD", "amd"], ["use-tpu", "TPU", "tpu"], ["use-android", "Mobile", "android"], ["use-web", "Browser", "web"]].filter(([, , p]) => !Pie.hiddenPlatforms.has(p));
  const useShares = (rows, platform) => {
    const mode = USE_MODES.find((m) => m.id === useMode);
    const out = {};
    const best = {};
    for (const r of rows) {
      if (r.workload !== mode.workload || !r[mode.key] || (useModel && r.model !== useModel)) continue;
      if (Pie.platformOf(Pie.store.index.hardware[r.hardware] || {}) !== platform) continue;
      const limit = limitOf(r, mode);
      if (!limit) continue;
      const k = `${r.engine}|${r.hardware}|${r.model}`;
      const v = Math.min(100, 100 * r[mode.key] / limit);
      if (!best[k] || v > best[k]) best[k] = v;
    }
    for (const [k, v] of Object.entries(best)) (out[k.split("|")[0]] ||= []).push(v);
    return out;
  };
  const useSummary = (id, title, platform, rows) => {
    const shares = useShares(rows, platform);
    const mid = (v) => { const a = [...v].sort((p, q) => p - q), n = a.length; return n ? (n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2) : null; };
    return { id, title, value: (_, engine) => (shares[engine] ? { v: mid(shares[engine]), n: shares[engine].length, detail: `Median over ${shares[engine].length} ${shares[engine].length === 1 ? "machine and model" : "machines and models"}` } : {}),
      label: (v) => `${Math.round(v)}%` };
  };
  const chevronMark = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
  const useSection = (rows) => {
    const mode = USE_MODES.find((m) => m.id === useMode);
    return `<div class="board-section-head is-apart">
            <div class="board-section-text"><h1 class="board-title">Kernel Efficiency</h1>
            <p class="board-lede">How close each engine gets to the theoretical limit.</p></div>
            <button class="filter-button board-title-pick is-text" type="button" data-board-pick="use-mode" aria-haspopup="menu" aria-label="Setup" title="${esc(mode.label)}">Setup${chevronMark}</button>${paddlesFor("use")}
          </div>
          <div class="board-carousel" data-carousel-id="use"><div class="board-grid-cards is-matrices">${USE_CARDS.map(([id, title, platform]) => card(id, title, "Share of the theoretical maximum", ranking(useSummary(id, title, platform, rows), rows), "", false)).join("")}</div></div>`;
  };

  const INSTALL_CARDS = [["install-mac", "Apple", "mac"], ["install-nvidia", "NVIDIA", "nvidia"], ["install-amd", "AMD", "amd"], ["install-tpu", "TPU", "tpu"], ["install-web", "Browser", "web"]].filter(([, , p]) => !Pie.hiddenPlatforms.has(p));
  const installRows = (platform) => (Pie.store.tables.install || []).filter((r) => r.platform === platform);
  const bytesLabel = (b) => (b >= 1e9 ? `${(b / 1e9).toFixed(1)} GB` : b >= 1e8 ? `${Math.round(b / 1e6)} MB` : `${(b / 1e6).toFixed(1)} MB`);
  const installSummary = (id, title, platform) => {
    const own = installRows(platform);
    return { id, title, ascending: true, top: (list) => niceMax(Math.max(...list.map((e) => e.v))), label: bytesLabel,
      value: (_, engine) => {
        const r = own.find((x) => x.engine === engine);
        return r ? { v: r.bytes, detail: `Version ${r.version}`, rows: r.parts.map(([k, n]) => [k, bytesLabel(n)]) } : {};
      } };
  };
  const installSection = () => {
    const cards = INSTALL_CARDS.filter(([, , p]) => installRows(p).length);
    if (!cards.length) return "";
    return `<div class="board-section-head is-apart">
            <div class="board-section-text"><h1 class="board-title">Install Size</h1>
            <p class="board-lede">Disk an engine needs before any model.</p></div>
            <button class="filter-button board-title-pick is-text" type="button" data-board-go-page="approach" data-chapter="install" title="What an install size counts">How we count</button>${paddlesFor("install")}
          </div>
          <div class="board-carousel" data-carousel-id="install"><div class="board-grid-cards is-matrices">${cards.map(([id, title, platform]) => card(id, title, "Binaries and libraries on disk · Lower is better", ranking(installSummary(id, title, platform), []), "", false)).join("")}</div></div>`;
  };

  const SUPPORT_TINTS = { mac: "#636366", nvidia: "#76b900", amd: "#ed1c24", tpu: "#4285f4", android: "#1C1C1E", web: "#8e8e93" };
  const FAMILY = { webllm: "mlc", "llamacpp-webgpu": "llamacpp", "vllm-metal": "vllm", "mlx-swift": "mlxlm" };
  const FAMILY_NAMES = { mlc: "MLC" };
  const BUILDS = { webllm: "WebLLM", mlc: "MLC LLM", "llamacpp-webgpu": "llama.cpp Web", "vllm-metal": "vLLM Metal", "mlx-swift": "MLX Swift" };
  const PLATFORM_OS = { mac: ["macos"], windows: ["windows"], nvidia: ["linux"], amd: ["linux"], tpu: ["linux"], cerebras: ["linux"], android: ["android", "ios"], web: ["linux"] };
  const PLATFORM_BACKEND = { mac: "metal", windows: "cuda", nvidia: "cuda", amd: "rocm", tpu: "xla", cerebras: "cerebras", web: "webgpu" };
  const canRun = (eng, p) => {
    const list = (v) => (v || "").split(",").map((x) => x.trim()).filter(Boolean);
    const os = list(eng.os), backends = list(eng.backends);
    if (!os.some((o) => PLATFORM_OS[p]?.includes(o))) return false;
    if (p === "web") return backends.includes("webgpu");
    return !backends.length || !PLATFORM_BACKEND[p] || backends.includes(PLATFORM_BACKEND[p]);
  };
  const supportOf = (rows) => {
    const ran = {}, all = {};
    for (const r of rows) {
      const p = Pie.platformOfAll(Pie.store.index.hardware[r.hardware] || {});
      if (!p) continue;
      const setup = `${r.hardware}|${r.model}|${r.workload}`;
      (all[p] ||= new Set()).add(setup);
      const on = ((ran[FAMILY[r.engine] || r.engine] ||= {})[p] ||= { setups: new Set(), models: new Set(), machines: new Set(), builds: new Set() });
      on.setups.add(setup);
      on.models.add(r.model);
      on.machines.add(r.hardware);
      on.builds.add(r.engine);
    }
    const able = {};
    for (const eng of Pie.store.tables.engines || []) {
      const fam = FAMILY[eng.id] || eng.id;
      for (const p of PLATFORM_ORDER) if (canRun(eng, p)) (able[fam] ||= new Set()).add(p);
      if (able[fam]) ran[fam] ||= {};
    }
    const platforms = [...PLATFORM_ORDER];
    const order = engineIds();
    const list = Object.keys(ran).filter((e) => order.includes(e)).map((e) => {
      const share = (p) => (ran[e][p] ? ran[e][p].setups.size / all[p].size : 0);
      return { e, ran: ran[e], able: able[e] || new Set(), on: platforms.filter((p) => ran[e][p]), reach: platforms.reduce((t, p) => t + share(p), 0), share };
    }).sort((a, b) => b.on.length - a.on.length || b.reach - a.reach || order.indexOf(a.e) - order.indexOf(b.e));
    return { platforms, list, all };
  };
  const SUPPORT_CHECK = '<svg class="board-support-check" viewBox="0 0 16 16" aria-label="Ran"><path d="M3.5 8.5l3 3 6-7"/></svg>';
  const supportTable = ({ platforms, list, all }, shares) => {
    const name = (e) => FAMILY_NAMES[e] || names().engine(e);
    const tip = (e, p, value, rows) => `data-tip-engine="${esc(e)}" data-tip-head="${esc(`${name(e)} on ${Pie.schema[p]?.short || p}`)}" data-tip-value="${esc(value)}" data-tip-rows="${esc(JSON.stringify(rows))}"`;
    const mark = (e) => `<svg class="board-matrix-logo" viewBox="0 0 16 16" aria-hidden="true">${e === "splash" ? '<image href="assets/img/engines/splash-glyph.png" width="16" height="16"/>' : logo(e, 0, 0, 16)}</svg>`;
    const row = (e) => `<span class="board-matrix-engine"><span class="board-matrix-name">${esc(SHORT[e] || name(e))}</span><span class="board-matrix-slot">${mark(e)}</span></span>`;
    const col = (p) => `<span class="board-matrix-engine is-col"><span class="board-matrix-name">${esc(Pie.schema[p]?.short || p)}</span><span class="board-matrix-slot"><span class="sidebar-glyph" style="--tint: ${SUPPORT_TINTS[p] || Pie.schema[p]?.tint}">${Pie.icon(p)}</span></span></span>`;
    const cell = (r, p) => {
      const on = r.ran[p];
      if (on) {
        const share = r.share(p), step = share >= .875 ? 4 : share >= .625 ? 3 : share >= .375 ? 2 : 1;
        const builds = [...on.builds].filter((x) => BUILDS[x]);
        const card = tip(r.e, p, `${Math.round(share * 100)}% of ${Pie.schema[p]?.short || p} benchmarks`, [["Ran", `${on.setups.size.toLocaleString("en-US")} of ${all[p].size.toLocaleString("en-US")}`], ["Models", String(on.models.size)], ["Machines", String(on.machines.size)], ...(builds.length ? [["As", builds.map((x) => BUILDS[x]).join(", ")]] : [])]);
        return shares ? `<td class="is-win" data-step="${step}" ${card}>${Math.round(share * 100) || "<1"}%</td>` : `<td class="is-ran" ${card}>${SUPPORT_CHECK}</td>`;
      }
      return r.able.has(p) ? `<td ${tip(r.e, p, "N/M", [["Supported", "no run yet"]])}></td>` : `<td class="is-self" ${tip(r.e, p, "Cannot run", [["Build", "none for this platform"]])}></td>`;
    };
    const key = `<span class="board-matrix-key" aria-hidden="true"><span class="board-matrix-tick">100%</span><span class="board-matrix-bar">${[4, 3, 2, 1].map((k) => `<i class="is-win" data-step="${k}"></i>`).join("")}<i data-step="0"></i></span><span class="board-matrix-tick">0</span></span>`;
    const legend = '<span class="board-support-keys"><span><i class="is-grey"></i>Not run yet</span><span><i class="is-blank"></i>Can\'t run</span></span>';
    return `<div class="board-matrix-frame is-support">${shares ? key : ""}${legend}<table class="board-matrix is-support" aria-label="Share of each platform's benchmarks each engine ran">
      <thead><tr><th></th>${platforms.map((p) => `<th scope="col">${col(p)}</th>`).join("")}<th scope="col" class="board-matrix-total">Platforms</th></tr></thead>
      <tbody>${list.map((r) => `<tr><th scope="row">${row(r.e)}</th>${platforms.map((p) => cell(r, p)).join("")}<td class="board-matrix-total">${r.on.length}/${platforms.length}</td></tr>`).join("")}</tbody>
    </table></div>`;
  };
  const supportSection = (rows) => {
    const support = supportOf(rows);
    if (!support.list.length) return "";
    return `<div class="board-section-head is-apart">
            <div class="board-section-text"><h1 class="board-title">Platform Support &amp; Coverage</h1>
            <p class="board-lede">Platforms each engine ran on here.</p></div>
            <button class="filter-button board-title-pick is-text" type="button" data-board-go-page="approach" data-chapter="add-engine" title="How a new engine joins the benchmark">Add Engine</button>${viewToggle("support", [CHECKS_ICON, "Checks"], "Share of benchmarks")}
          </div>
          ${card("support", "Platforms", gridCards.has("support") ? "Share of each platform's benchmarks run" : "Platforms each engine has run on", supportTable(support, gridCards.has("support")), "", false)}`;
  };

  let log = null;
  const changelog = () => log ||= (Pie.store.tables.tags || [])
    .filter((tag) => /^\d+\.\d+/.test(tag.id))
    .map((tag) => ({ kind: "New release measured", at: tag.date, run: tag, results: Pie.store.count(tag.id).measured }))
    .filter((e) => e.results)
    .sort((a, b) => b.at.localeCompare(a.at));
  const MONTH = new Intl.DateTimeFormat("en-US", { month: "short" });
  const DAY = { format: (d) => `${d.getDate()} ${MONTH.format(d)}` };
  const logItem = (e) => {
    const [mark, text] = [`<span class="board-log-glyph">${Pie.icon("bars")}</span>`, `${e.run.id} · ${e.results.toLocaleString()} results`];
    return `<li class="board-log-item">
        <div class="board-log-kind">${esc(e.kind)} · ${esc(DAY.format(new Date(e.at.replace(" ", "T"))))}</div>
        <div class="board-log-text">${mark}<span>${esc(text)}</span></div>
      </li>`;
  };
  const footer = () => {
    const at = Pie.store.tables.updated_at ? new Date(Pie.store.tables.updated_at) : null;
    const when = at ? at.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" }) : "";
    return `
      <footer class="board-footer">
        <div class="board-footer-simple">
          ${when ? `<span class="board-footer-updated">Updated ${esc(when)}</span>` : ""}
        </div>
      </footer>`;
  };
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
        <section class="board-log" aria-label="Changelog">
          <div class="board-log-head"><h2 class="board-log-title">Changelog</h2><form class="board-subscribe" hidden><input type="email" required placeholder="Email" aria-label="Email"><button type="submit" aria-label="Notify me" title="Notify me"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8h9M9 4.5 12.5 8 9 11.5"/></svg></button></form>
            <button class="board-log-bell${subscribed() ? " is-subscribed" : ""}" type="button" data-board-subscribe aria-label="Email me new releases" title="Email me new releases"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 11.5V7a4 4 0 0 1 8 0v4.5l1 1H3zM6.5 14a1.5 1.5 0 0 0 3 0"/></svg></button></div>
          <ol class="board-log-list">${changelog().map(logItem).join("")}</ol>
        </section>
      </div>`;

  const BADGES = {
    index:          ["#5E5CE6", '<circle cx="12" cy="12" r="9"/><path d="m12 12 2.6-5.2"/><circle cx="12" cy="12" r="1.6" fill="#fff" stroke="none"/><path d="M7 15.5h.01M6.5 11h.01M9 7h.01M17.5 11h.01M17 15.5h.01"/>'],
    "index-mac":    ["#636366"],
    use: ["#636366"], "use-windows": ["#0078D4"], "use-nvidia": ["#76b900"], "use-amd": ["#ed1c24"], "use-tpu": ["#4285f4"], "use-android": ["#1C1C1E"], "use-web": ["#8e8e93"],
    "install-mac": ["#636366"], "install-nvidia": ["#76b900"], "install-amd": ["#ed1c24"], "install-tpu": ["#4285f4"], "install-web": ["#8e8e93"],
    support:        ["#FF2D55"],
    ...Object.fromEntries(Object.entries(BY_MODEL).flatMap(([p, [, tint]]) => [[`metric-${p}`, [tint]], [`ttft-${p}`, [tint]]])),
    "index-gpu":    ["#76b900"],
    "index-amd":    ["#ed1c24"],
    "index-tpu":    ["#4285f4"],
    "index-android": ["#1C1C1E"],
    "index-web":    ["#8e8e93"],
    accuracy:       ["#34c759"],
    wins:           ["#FF9F0A", '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v6M8.5 19h7"/>'],
    coverage:       ["#30B0C7", Pie.icons.welcome],
    moe:            ["#5AC8FA", '<path d="M4 4v16h16"/><circle cx="9" cy="15" r="1.9" fill="#fff" stroke="none"/><circle cx="13" cy="11" r="1.9" fill="#fff" stroke="none"/><circle cx="17.5" cy="6.5" r="1.9" fill="#fff" stroke="none"/>'],
    size:           ["#32ADE6", '<path d="M4 4v16h16"/><circle cx="9" cy="15" r="1.9" fill="#fff" stroke="none"/><circle cx="13" cy="11" r="1.9" fill="#fff" stroke="none"/><circle cx="17.5" cy="6.5" r="1.9" fill="#fff" stroke="none"/>'],
    ttft:           ["#FF375F", '<circle cx="12" cy="13.5" r="7.5"/><path d="M12 10v3.5l2.5 2M10 2.5h4"/>'],
    metric:         ["#0A84FF", '<path d="M4 6h16M4 12h12M4 18h5"/><path d="M14.5 18.1v3.5"/>'],
    scaling:        ["#8E8E93", Pie.icons.hardware],
    gain:           ["#00C7BE"],
    load:           ["#FF9F0A"],
  };
  const TOOLS = (id) => `<button class="board-card-tool" type="button" data-board-link="${id}" aria-label="Copy a link to this chart" title="Copy a link to this chart"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.9 9.1a2.5 2.5 0 0 0 3.5 0l2.1-2.1a2.5 2.5 0 0 0-3.5-3.5l-.9.9"/><path d="M9.1 6.9a2.5 2.5 0 0 0-3.5 0L3.5 9a2.5 2.5 0 0 0 3.5 3.5l.9-.9"/></svg></button><button class="board-card-tool" type="button" data-board-save="${id}" aria-label="Save as image" title="Save as image"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.25" y="3" width="11.5" height="10" rx="2"/><circle cx="5.75" cy="6.25" r="1"/><path d="m2.5 11.5 3.2-3.2 2.3 2.3 2-2 3.5 3.5"/></svg></button><button class="board-card-tool" type="button" data-board-data="${id}" aria-label="Download the data" title="Download the data (log in)"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.25" y="3" width="11.5" height="10" rx="2"/><path d="M2.25 6.5h11.5M2.25 9.75h11.5M7 6.5V13"/></svg></button>`;
  const COVER_PLATFORMS = [["mac", "Mac"], ["nvidia", "NVIDIA"], ["amd", "AMD"], ["tpu", "TPU"]].filter(([p]) => !Pie.hiddenPlatforms.has(p));
  const coverage2 = (rows) => {
    const ran = new Set();
    for (const r of rows) {
      if (!(r.decode_tok_s || r.prefill_tok_s || r.output_tok_s)) continue;
      const p = Pie.platformOf(Pie.store.index.hardware[r.hardware] || {});
      ran.add(`${r.engine}|${r.model}|${p}`);
    }
    const engines = engineIds().filter((e) => [...ran].some((k) => k.startsWith(`${e}|`)));
    const models = (Pie.store.tables.models || []).map((m) => m.id)
      .sort((a, b) => (Pie.platform?.makerName(a) || "").localeCompare(Pie.platform?.makerName(b) || "") || names().model(a).localeCompare(names().model(b)));
    const on = (e, p) => models.filter((m) => ran.has(`${e}|${m}|${p}`));
    const W = 1040, H = 209, L = 8, R = 8, T = 12, B = 46;
    const cells = COVER_PLATFORMS.map(([p, l]) => ({ p, l, bars: engines.map((e) => ({ e, list: on(e, p) })).filter((b) => b.list.length) })).filter((c) => c.bars.length);
    if (!cells.length) return `<p class="board-empty">No runs yet</p>`;
    const top = niceMax(Math.max(...cells.flatMap((c) => c.bars.map((b) => b.list.length))));
    const base = H - B;
    const y = (v) => T + (base - T) * (1 - v / top);
    const slot = (W - L - R) / cells.length;
    const most = Math.max(...cells.map((c) => c.bars.length));
    const BW = Math.min(28, (slot * 0.6 - (most - 1) * 2) / most);
    const marks = cells.map((c, i) => {
      const width = c.bars.length * BW + (c.bars.length - 1) * 2;
      const left = L + slot * i + (slot - width) / 2;
      const bars = c.bars.map((b, j) => bar(left + j * (BW + 2), y(b.list.length), BW, base, Pie.engines.colorOf(b.e), String(b.list.length),
        { engine: b.e, head: `${names().engine(b.e)} on ${c.l}`, value: `${b.list.length} of ${models.length} models`, note: b.list.map((m) => names().model(m)).join(", ") },
        { x: left + j * (BW + 2) - 1, w: BW + 2 })).join("");
      const cx = L + slot * i + slot / 2;
      return `${bars}<text class="board-group" x="${cx}" y="${base + 18}">${esc(c.l)}</text>
        <text class="board-machine" x="${cx}" y="${base + 33}">${esc(`${new Set(c.bars.flatMap((b) => b.list)).size} models run`)}</text>`;
    }).join("");
    return `<svg class="board-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Models run by engine and platform">${lines(L, W - R, y, top)}<line class="board-axis" x1="${L}" x2="${W - R}" y1="${base}" y2="${base}"/>${marks}</svg>`;
  };
  const REL_KEY = "pieRelativeSetup";
  let relSetup = (() => { try { const k = localStorage.getItem(REL_KEY); return GAIN_PICKS.some((g) => g.id === k) ? k : "decode"; } catch { return "decode"; } })();
  const relTests = (rows, pick) => {
    if (pick.id === "decode") return setups(rows, "decode_tok_s");
    const by = {};
    for (const r of rows) if (r.workload === pick.workload && r[pick.key]) {
      const s = (by[`${r.hardware}|${r.model}`] ||= {});
      s[r.engine] = Math.max(s[r.engine] || 0, r[pick.key]);
    }
    return Object.values(by).filter((s) => Object.keys(s).length > 1);
  };
  const relHead = (pick) => `
          <div class="board-section-head is-apart" id="board-relative">
            <div class="board-section-text"><h1 class="board-title">Relative Throughput</h1>
            <p class="board-lede">Speed on every platform, against the fastest engine on each test.</p></div>
            <button class="filter-button board-title-pick is-text" type="button" data-board-pick="relative-setup" aria-haspopup="menu" aria-label="Setup" title="${esc(pick.label)}">Setup<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </div>`;
  const relativeSection = (rows) => {
    const pick = GAIN_PICKS.find((g) => g.id === relSetup) || GAIN_PICKS[0];
    const tests = relTests(rows, pick);
    const pie = Pie.engines.primary;
    const MIN_TESTS = 5;
    const count = (e) => tests.filter((s) => s[e]).length;
    const ids = engineIds().filter((e) => !e.endsWith("-webgpu") && count(e) >= MIN_TESTS);
    if (!tests.length || !ids.includes(pie)) return `${relHead(pick)}<p class="board-empty">No ${esc(pick.label.toLowerCase())} results to compare yet</p>`;
    const fastest = (s) => Math.max(...Object.values(s));
    const label = (e) => `${names().engine(e)}${e.endsWith("-webgpu") ? " Web" : ""}`;
    const COLS = [[0, "Fastest"], [.05, "Within 5%"], [.1, "Within 10%"], [.25, "Within 25%"], [.5, "Within 50%"]];
    const engines = ids.map((e) => {
      const short = tests.filter((s) => s[e]).map((s) => 1 - s[e] / fastest(s));
      return { e, name: label(e), color: Pie.engines.colorOf(e), shares: COLS.map(([d]) => short.filter((v) => v <= d + 1e-9).length / short.length) };
    });
    COLS.forEach((_, j) => [...engines].sort((a, b) => b.shares[j] - a.shares[j] || ids.indexOf(a.e) - ids.indexOf(b.e)).forEach((x, r) => { (x.ranks ||= [])[j] = r; }));
    const data = { cols: COLS.map(([, t]) => t), engines: engines.map(({ e, name, color, shares, ranks }) => ({ e, name, color, shares, ranks })) };
    const svg = `<div class="bump" data-bump="${esc(JSON.stringify(data))}" style="height: ${28 + 34 * engines.length}px" role="img" aria-label="Engines ranked by the share of their tests within each margin of the fastest engine"></div>`;
    return `
${relHead(pick)}
          <div class="board-grid-cards relative-cards">
            ${card("relative-profile", "", "", svg, "", false)}
          </div>`;
  };
  const card = (id, title, sub, body, aside = "", tools = true) => `
      <section class="board-card" id="board-${id}">
        <div class="board-card-head">
          <div class="board-card-titles">
            <h2>${BADGES[id] ? `<i class="board-title-dot" style="background: ${BADGES[id][0]}" aria-hidden="true"></i>` : ""}${esc(title)}</h2>
            ${sub ? `<p class="board-sub">${sub.split(" · ").map(esc).join("<br>")}</p>` : ""}
          </div>
          ${tools || aside ? `<div class="board-card-side">${tools ? `<span class="board-card-tools">${TOOLS(id)}</span>` : ""}${aside}</div>` : ""}
        </div>
        <div class="board-card-body">${body}</div>
      </section>`;

  const RUNS = 10000;
  const atLeast = (n) => (n < 1000 ? String(n) : `${(Math.round(n / 1000) * 1000).toLocaleString("en-US")}+`);
  const welcomeStat = () => {
    const n = (v) => v.toLocaleString("en-US");
    const busy = Pie.store.tables.totals?.machine_s;
    const time = !busy ? null : busy >= 3 * 86400 ? [`Days of compute`, n(Math.round(busy / 86400))] : [`Hours of compute`, n(Math.round(busy / 3600))];
    const stats = [["Runs", atLeast(Pie.store.tables.totals?.runs ?? RUNS)], time, ["Machines", n(Pie.platform?.machines?.() || 0)], ["Optimizations found", n(Pie.platform?.seconds?.(Pie.state)?.length || 0)], Pie.store.tables.totals?.submissions != null && ["Public contributions", n(Pie.store.tables.totals.submissions)]].filter((s) => s && (s[1] !== "0" || s[0] === "Public contributions"));
    return `<dl class="welcome-stats board-welcome-stats">${stats.filter(Boolean).map(([label, v]) => `<div><dt>${label}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>`;
  };

  const page = () => {
    const rows = measured();
    const list = models(rows);
    if (!list.includes(model)) model = list[0] || null;
    if (!model) return `<div class="board-scroll"><div class="board-inner"><p class="board-empty">No runs in this release yet</p></div></div>`;
    const cmp = comparePick(rows);
    const ran = new Set(rows.map((r) => r.engine));
    const legend = engineIds().filter((id) => ran.has(id))
      .map((id) => {
        const repo = Pie.store.index.engines[id]?.repo;
        const key = `<span class="board-dot" style="background: ${Pie.engines.colorOf(id)}"></span>${esc(names().engine(id))}`;
        return repo ? `<a class="board-key" href="https://github.com/${esc(repo)}" target="_blank" rel="noopener" draggable="false">${key}</a>` : `<span class="board-key">${key}</span>`;
      }).join("");
    const installed = INSTALL_CARDS.find(([, , p]) => installRows(p).length);
    const GROUPS = [["Speed", [[USE_CARDS[0][0], "Efficiency", "#34C759"], [SUMMARY[0].id, "Performance", "#FF9500"]]],
      ["", [["metric", "Find Your Speed", "#0A84FF"], ["relative", "Relative Throughput", "#AF52DE"]]],
      ["Deployment", [installed && [installed[0], "Install Size", "#30B0C7"], supportOf(rows).list.length && ["support", "Platforms", "#FF2D55"]]]];
    const outline = GROUPS.map(([head, items]) => [head, items.filter(Boolean)]).filter(([, items]) => items.length).map(([head, items]) =>
      `${head ? `<div class="board-outline-head">${esc(head)}</div>` : ""}${items.map(([id, title, tint]) =>
      `<button type="button" class="board-outline-item" data-board-go="${id}"><i class="board-outline-dot" style="background: ${tint}" aria-hidden="true"></i><span>${esc(title)}</span></button>`).join("")}`).join("");
    const SHEEN = `<svg class="board-defs" width="0" height="0" aria-hidden="true"><defs>
        <pattern id="board-sheen" width="6" height="6" patternUnits="userSpaceOnUse">
          <circle cx="3" cy="3" r="1" fill="#fff" fill-opacity=".28"/>
        </pattern></defs></svg>`;
    return `${SHEEN}
      <div class="platform-bar board-bar">
        <span class="board-legend">${legend}</span>
      </div>
      <div class="board-scroll"><div class="board-inner">
        <nav class="board-outline" aria-label="On this page">${outline}</nav>
        <div class="board-main">
          <section class="board-welcome" aria-label="About these benchmarks">
            <div class="board-section-head">
            <div class="board-section-text"><h1 class="board-title board-welcome-title">Open Inference Benchmark Initiative</h1><p class="board-welcome-sub">Open, fair, and reproducible results across every platform.</p></div>
            <div class="board-welcome-actions">
              <a class="board-welcome-primary" href="https://pypi.org/project/pie-bench/" target="_blank" rel="noopener" title="pip install pie-bench"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/></svg>pie-bench</a>
              <button type="button" class="board-welcome-secondary" data-board-go-page="approach" data-chapter="welcome">${Pie.icon("approach")}Bench Book</button>
            </div>
            </div>
            ${welcomeStat()}
          </section>
          ${useSection(rows)}
          <div class="board-section-head is-apart">
            <div class="board-section-text"><h1 class="board-title">Performance Head to Head</h1>
            <p class="board-lede">Each platform on its own: engines compared on the same machines and models.</p></div>
            ${viewToggle("summary")}${paddlesFor("summary")}
          </div>
          <div class="board-carousel" data-carousel-id="summary"><div class="board-grid-cards is-matrices">${SUMMARY.map((m) => card(m.id, m.title, gridCards.has("summary") ? "Head-to-head decode win rate" : m.sub, gridCards.has("summary") ? matrix(m, rows) : ranking(m, rows), "", false)).join("")}</div></div>
          <div class="board-section-head" id="board-metric">
            <div class="board-section-text"><h1 class="board-title">Find Your Speed</h1>
            <p class="board-lede">Tokens per second for every engine, one request and many at once.<br>Higher is better.</p></div>
            ${headPick("cmp-platform", "Platform", BY_MODEL[cmp.p]?.[0] || cmp.p || "")}${headPick("cmp-hw", "Hardware", cmp.hw ? machineName(cmp.hw) : "")}${headPick("model", "Model", names().model(model))}
          </div>
          ${compareBlock(rows, cmp)}
          ${relativeSection(rows)}
          ${""}${""}
          ${""}
          ${installSection()}
          ${supportSection(rows)}
          ${""}
          ${""}
          ${""}
        </div>
      </div>${footer()}</div>`;
  };

  const scroller = () => element.querySelector(".board-scroll") || element;
  let pinned = null;
  const unpin = () => { pinned = null; };
  for (const kind of ["wheel", "touchstart", "keydown", "pointerdown"]) element.addEventListener(kind, (event) => {
    if (kind === "pointerdown" && event.target.closest("[data-board-go]")) return;
    unpin();
  }, { passive: true });
  const follow = () => {
    const sections = [...element.querySelectorAll(".board-card")].filter((s) => !s.closest(".board-carousel") || !s.previousElementSibling);
    const view = scroller();
    const box = view.getBoundingClientRect();
    const line = box.top + box.height / 3;
    const STEP = 40;
    const turns = [];
    for (const s of sections) {
      const at = Math.max(0, s.getBoundingClientRect().top + view.scrollTop - line);
      turns.push(turns.length ? Math.max(at, turns[turns.length - 1] + STEP) : at);
    }
    const max = Math.max(0, view.scrollHeight - view.clientHeight - 2);
    const late = turns.findIndex((t) => t > max - STEP);
    if (late >= 0) {
      const from = late ? turns[late - 1] : 0, n = turns.length - late;
      for (let k = 0; k < n; k++) turns[late + k] = from + ((max - from) * (k + 1)) / n;
    }
    const bottom = view.scrollTop + view.clientHeight >= view.scrollHeight - 2;
    let index = 0;
    for (let k = 0; k < turns.length; k++) if (turns[k] <= view.scrollTop) index = k;
    const current = bottom ? sections[sections.length - 1] : sections[index];
    const id = pinned || current?.id.slice(6);
    const installFirst = INSTALL_CARDS.find(([, , p]) => installRows(p).length)?.[0];
    const groupOf = (card) => USE_CARDS.some(([u]) => u === card) ? USE_CARDS[0][0] : SUMMARY.some((m) => m.id === card) ? SUMMARY[0].id
      : INSTALL_CARDS.some(([u]) => u === card) ? installFirst : card === "support" ? card : String(card).startsWith("relative") ? "relative" : String(card).startsWith("ttft") ? "ttft" : "metric";
    for (const item of element.querySelectorAll("[data-board-go]")) item.classList.toggle("is-current", item.dataset.boardGo === groupOf(id));
    const outline = element.querySelector(".board-outline"), on = outline?.querySelector(".board-outline-item.is-current");
    if (!outline || !on) return;
    let thumb = outline.querySelector(":scope > .board-outline-thumb");
    if (!thumb) { thumb = document.createElement("span"); thumb.className = "board-outline-thumb"; thumb.setAttribute("aria-hidden", "true"); outline.prepend(thumb); }
    thumb.style.transform = `translateY(${on.offsetTop}px)`;
    thumb.style.height = `${on.offsetHeight}px`;
  };
  element.addEventListener("scroll", follow, { passive: true, capture: true });

  const NEAR = 24;
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
    let best = null, gap = NEAR / ctm.a;
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

  const tooltip = document.getElementById("chart-tooltip");
  const battleHtml = (g) => {
    const side = (e) => `<span>${esc(names().engine(e))}</span>`;
    return `<div class="board-tip-battle"><div class="board-tip-head">${side(g.dataset.tipEngine)}<span class="board-tip-vs">vs</span>${side(g.dataset.tipVs)}</div>
    <div class="board-tip-row"><span>Win rate</span><b>${esc(g.dataset.tipValue)}</b></div>
    <div class="board-tip-row"><span>Setups won</span><b>${esc(g.dataset.tipNote)}</b></div></div>`;
  };
  const tipHtml = (g) => {
    if (g.dataset.tipVs) return battleHtml(g);
    const engine = g.dataset.tipEngine;
    const wide = WIDE.has(engine);
    const head = wide ? g.dataset.tipHead.slice(names().engine(engine).length).trim() : g.dataset.tipHead;
    if (!engine) return `<div class="board-tip-battle">${JSON.parse(g.dataset.tipRows || "[]").map(([k, v, tone]) => `<div class="board-tip-row"><span>${esc(k)}</span><b${tone ? ` class="${tone}"` : ""}>${esc(v)}</b></div>`).join("")}</div>`;
    return `<div class="board-tip-head"><svg class="board-tip-logo" ${wide ? 'style="width: 18.7px" viewBox="0 0 27.2 16"' : 'viewBox="0 0 16 16"'} aria-hidden="true">${logo(engine, wide ? 5.6 : 0, 0, 16)}</svg>${esc(head)}</div>
    <div class="board-tip-value">${esc(g.dataset.tipValue)}</div>${g.dataset.tipNote ? `<div class="board-tip-note">${esc(g.dataset.tipNote)}</div>` : ""}${
      g.dataset.tipRows ? JSON.parse(g.dataset.tipRows).map(([k, v]) => `<div class="board-tip-row"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("") : ""}`;
  };
  let tipFor = null;
  element.addEventListener("pointermove", (event) => {
    if (Pie.tapCard.isTouch()) return;
    const g = event.target.closest?.(".board-bar[data-tip-head], .board-matrix td[data-tip-head], .support-table td[data-tip-head], .qc-mark[data-tip-html], .board-compare-name[data-tip-head]");
    if (!g) {
      if (tipFor) { tipFor = null; tooltip.hidden = true; tooltip.classList.remove("is-board", "is-card"); }
      return;
    }
    if (g !== tipFor) {
      tipFor = g;
      tooltip.innerHTML = g.dataset.tipHtml || tipHtml(g);
      const qc = !!g.dataset.tipHtml && tooltip.querySelector(".qc-tip-rows");
      tooltip.classList.toggle("is-board", !qc);
      tooltip.classList.toggle("is-card", !!qc);
      tooltip.hidden = false;
    }
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  });
  const hideTip = () => { tipFor = null; tooltip.hidden = true; tooltip.classList.remove("is-board", "is-card"); };
  element.addEventListener("pointerleave", hideTip);
  element.addEventListener("scroll", hideTip, { passive: true, capture: true });


  const SUBSCRIBED_KEY = "pieSubscribed";
  const subscribed = () => { try { return localStorage.getItem(SUBSCRIBED_KEY) === "1"; } catch { return false; } };
  let tug = null;
  element.addEventListener("pointerdown", (event) => {
    const grid = event.target.closest?.(".board-matrix, .board-chart, .board-legend");
    if (!grid || event.button !== 0 || event.target.closest("button, a, input, select")) return;
    const bar = grid.classList.contains("board-legend") ? grid.closest(".board-bar") : null;
    tug = { grid, x: event.clientX, y: event.clientY, id: event.pointerId, flat: !grid.classList.contains("board-matrix"), bar, left: bar?.scrollLeft || 0 };
    grid.setPointerCapture(event.pointerId);
    grid.style.transition = "none";
    grid.classList.add("is-tugged");
  });
  element.addEventListener("pointermove", (event) => {
    if (!tug || event.pointerId !== tug.id) return;
    const give = (d) => Math.sign(d) * 60 * (1 - Math.exp(-Math.abs(d) / 120));
    const max = tug.bar ? tug.bar.scrollWidth - tug.bar.clientWidth : 0;
    if (max > 1) {
      const want = tug.left - (event.clientX - tug.x);
      tug.bar.scrollLeft = Math.max(0, Math.min(max, want));
      tug.grid.style.transform = `translate(${give(want < 0 ? -want : want > max ? max - want : 0)}px, 0)`;
      return;
    }
    tug.grid.style.transform = `translate(${give(event.clientX - tug.x)}px, ${tug.flat ? 0 : give(event.clientY - tug.y)}px)`;
  });
  const letGo = (event) => {
    if (!tug || event.pointerId !== tug.id) return;
    tug.grid.style.transition = "transform .45s cubic-bezier(.3, 1.4, .5, 1)";
    tug.grid.style.transform = "";
    tug.grid.classList.remove("is-tugged");
    tug = null;
  };
  element.addEventListener("pointerup", letGo);
  element.addEventListener("pointercancel", letGo);

  const setSubscribe = (open) => {
    const form = element.querySelector(".board-subscribe");
    if (!form) return;
    form.hidden = !open;
    element.querySelector("[data-board-subscribe]")?.classList.toggle("is-on", open);
    form.closest(".board-log-head").classList.toggle("is-open", open);
    if (open) form.querySelector("input").focus({ preventScroll: true });
  };
  document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest?.(".board-log-head")) setSubscribe(false);
  });
  element.addEventListener("submit", (event) => {
    const form = event.target.closest(".board-subscribe");
    if (!form) return;
    event.preventDefault();
    const input = form.querySelector("input");
    input.value = "";
    setSubscribe(false);
    const title = element.querySelector(".board-log-title");
    title.innerHTML = '<svg class="board-log-check" viewBox="0 0 16 16" aria-hidden="true"><path d="m3.5 8.5 3 3 6-7"/></svg>Subscribed';
    setTimeout(() => { title.textContent = "Changelog"; }, 3000);
    try { localStorage.setItem(SUBSCRIBED_KEY, "1"); } catch { }
    element.querySelector("[data-board-subscribe]")?.classList.add("is-subscribed");
  });

  const paddles = () => element.querySelectorAll(".board-carousel[data-carousel-id]").forEach((carousel) => {
    const row = carousel.querySelector(".board-grid-cards"), nav = element.querySelector(`[data-carousel-nav="${carousel.dataset.carouselId}"]`);
    const [back, on] = nav ? nav.querySelectorAll("[data-carousel]") : [];
    if (!row || !back) return;
    nav.hidden = row.scrollWidth <= row.clientWidth + 2;
    back.disabled = row.scrollLeft < 2;
    on.disabled = row.scrollLeft + row.clientWidth > row.scrollWidth - 2;
  });
  element.addEventListener("click", (event) => {
    const paddle = event.target.closest("[data-carousel]");
    if (!paddle) return;
    const row = element.querySelector(`.board-carousel[data-carousel-id="${paddle.dataset.carouselFor}"] .board-grid-cards`), card = row?.querySelector(":scope > :not([hidden])");
    if (card) row.scrollBy({ left: Number(paddle.dataset.carousel) * (card.getBoundingClientRect().width + (parseFloat(getComputedStyle(row).columnGap) || 0)), behavior: "smooth" });
  });
  element.addEventListener("scroll", (event) => { if (event.target.classList?.contains("is-matrices")) paddles(); }, { passive: true, capture: true });
  window.addEventListener("resize", () => paddles());
  element.addEventListener("keydown", (event) => {
    if ((event.key === "Enter" || event.key === " ") && event.target.matches?.('[role="link"][data-board-go-page]')) { event.preventDefault(); event.target.click(); }
  });
  element.addEventListener("click", (event) => {
    const go = event.target.closest("[data-board-go-page]");
    if (go) event.preventDefault();
    if (go?.dataset.chapter) Pie.approach?.open(go.dataset.chapter);
    if (go) document.querySelector(`.sidebar-item[data-table="${go.dataset.boardGoPage}"]`)?.click();
  });
  element.addEventListener("click", (event) => {
  });
  const drawBumps = () => {
    for (const box of element.querySelectorAll(".bump")) {
      const W = box.clientWidth;
      if (!W || box.dataset.drawn === String(W)) continue;
      box.dataset.drawn = String(W);
      const { cols, engines } = JSON.parse(box.dataset.bump);
      const PILL = 128, TOP = 28, ROW = 34, n = cols.length;
      const x0 = PILL + 28, x1 = W - PILL - 28, x = (j) => x0 + ((x1 - x0) * j) / (n - 1), y = (r) => TOP + ROW * (r + .5);
      box._geo = { x0, x1, n, TOP, ROW, engines };
      box.dataset.focus = "";
      const pct = (v) => `${Math.round(v * 100)}%`;
      const guides = engines.map((_, r) => `<line class="bump-guide" x1="${x0}" x2="${x1}" y1="${y(r)}" y2="${y(r)}"/>`).join("");
      const lines = engines.map((g) => {
        let d = `M${x(0)},${y(g.ranks[0])}`;
        for (let j = 1; j < n; j++) { const a = x(j - 1), b = x(j), m = (a + b) / 2; d += `C${m},${y(g.ranks[j - 1])} ${m},${y(g.ranks[j])} ${b},${y(g.ranks[j])}`; }
        const nodes = g.ranks.map((r, j) => r < 3
          ? `<g class="bump-badge"><circle cx="${x(j)}" cy="${y(r)}" r="9" fill="${g.color}"/><text x="${x(j)}" y="${y(r) + 3.5}">${r + 1}</text><title>${esc(`${g.name}: ${pct(g.shares[j])} of its tests ${cols[j] === "Fastest" ? "fastest" : cols[j].toLowerCase()}`)}</title></g>`
          : `<circle class="bump-dot" cx="${x(j)}" cy="${y(r)}" r="3" fill="${g.color}"><title>${esc(`${g.name}: ${pct(g.shares[j])} of its tests ${cols[j] === "Fastest" ? "fastest" : cols[j].toLowerCase()}`)}</title></circle>`).join("");
        return `<g class="bump-engine" data-engine="${esc(g.e)}"><path class="bump-hit" d="${d}"/><path class="bump-line" d="${d}" stroke="${g.color}"/>${nodes}</g>`;
      }).join("");
      const pill = (g, side) => `<span class="bump-pill is-${side}" data-engine="${esc(g.e)}" data-color="${g.color}" style="top: ${y(g.ranks[side === "left" ? 0 : n - 1])}px">${engineMark(g.e)}${esc(g.name)}</span>`;
      box.innerHTML = `${cols.map((t, j) => `<span class="bump-col" style="left: ${x(j)}px">${esc(t)}</span>`).join("")}
        <svg class="bump-chart" width="${W}" height="${TOP + ROW * engines.length}">${guides}${lines}</svg>
        ${engines.map((g) => pill(g, "left") + pill(g, "right")).join("")}`;
    }
  };
  new ResizeObserver(() => drawBumps()).observe(element);
  const bumpFocus = (box, engine) => {
    if (box.dataset.focus === (engine || "")) return;
    box.dataset.focus = engine || "";
    box.classList.toggle("is-focused", Boolean(engine));
    for (const el of box.querySelectorAll("[data-engine]")) {
      const on = el.dataset.engine === engine;
      el.classList.toggle("is-active", on);
      if (el.classList.contains("bump-pill")) el.style.background = on ? el.dataset.color : "";
    }
  };
  const bumpY = (g, geo, px) => {
    const { x0, x1, n, TOP, ROW } = geo, yr = (r) => TOP + ROW * (r + .5), step = (x1 - x0) / (n - 1);
    if (px <= x0) return yr(g.ranks[0]);
    if (px >= x1) return yr(g.ranks[n - 1]);
    const j = Math.min(n - 1, Math.floor((px - x0) / step) + 1), a = x0 + step * (j - 1), b = a + step, m = (a + b) / 2;
    const ya = yr(g.ranks[j - 1]), yb = yr(g.ranks[j]);
    let lo = 0, hi = 1;
    for (let k = 0; k < 24; k++) {
      const t = (lo + hi) / 2, u = 1 - t;
      const xt = a * u * u * u + 3 * m * u * u * t + 3 * m * u * t * t + b * t * t * t;
      if (xt < px) lo = t; else hi = t;
    }
    const t = (lo + hi) / 2, u = 1 - t;
    return ya * (u * u * u + 3 * u * u * t) + yb * (3 * u * t * t + t * t * t);
  };
  element.addEventListener("pointermove", (event) => {
    const box = event.target.closest?.(".bump");
    if (!box) { for (const b of element.querySelectorAll(".bump.is-focused")) bumpFocus(b, null); return; }
    const geo = box._geo;
    if (!geo) return;
    const r = box.getBoundingClientRect(), px = event.clientX - r.left, py = event.clientY - r.top;
    let best = null, gap = Infinity;
    for (const g of geo.engines) { const d = Math.abs(bumpY(g, geo, px) - py); if (d < gap) { gap = d; best = g.e; } }
    bumpFocus(box, best);
  });
  element.addEventListener("pointerleave", () => { for (const box of element.querySelectorAll(".bump")) bumpFocus(box, null); });
  element.addEventListener("click", (event) => {
    const bell = event.target.closest("[data-board-subscribe]");
    if (bell) {
      setSubscribe(element.querySelector(".board-subscribe").hidden);
      return;
    }
    const go = event.target.closest("[data-board-go]");
    if (go) {
      pinned = go.dataset.boardGo;
      element.querySelector(`#board-${go.dataset.boardGo}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      follow();
      return;
    }
    const specs = event.target.closest(".board-compare-name");
    if (specs && Pie.tapCard.isTouch()) { tooltip.classList.add("is-board"); Pie.tapCard.toggle(specs, tipHtml(specs)); return; }
    const view = event.target.closest("[data-board-view]");
    if (view) {
      if (view.dataset.view === "grid") gridCards.add(view.dataset.boardView); else gridCards.delete(view.dataset.boardView);
      try { localStorage.setItem(GRID_KEY, JSON.stringify([...gridCards])); } catch { }
      delete element.dataset.key;
      const kept = [...element.querySelectorAll("[data-carousel-id] .board-grid-cards")].map((row) => [row.closest("[data-carousel-id]").dataset.carouselId, row.scrollLeft]);
      Pie.board.render(state);
      for (const [id, left] of kept) {
        const row = element.querySelector(`[data-carousel-id="${id}"] .board-grid-cards`);
        if (row) { row.style.scrollBehavior = "auto"; row.scrollLeft = left; row.style.scrollBehavior = ""; }
      }
      return;
    }
    const toggle = event.target.closest("[data-board-toggle]");
    if (toggle) {
      toggle.blur();
      Pie.board.pick("summary", summaryWorkload === "spec" ? "raw" : "spec");
      Pie.board.render(state);
      return;
    }
    const opens = event.target.closest("[data-board-open]");
    if (opens) {
      event.preventDefault();
      document.querySelector(`.sidebar-item[data-table="${opens.dataset.boardOpen}"]`)?.click();
      return;
    }
    event.target.closest(".board-card-tool")?.blur();
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
    const data = event.target.closest("[data-board-data]");
    if (data) {
      saveData(element.querySelector(`#board-${data.dataset.boardData}`));
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

  const STYLE = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity",
    "font-family", "font-size", "font-weight", "letter-spacing", "text-anchor", "dominant-baseline", "visibility"];
  const dataUrl = (src) => fetch(src).then((r) => r.blob()).then((blob) => new Promise((done) => {
    const reader = new FileReader();
    reader.onload = () => done(reader.result);
    reader.readAsDataURL(blob);
  }));
  const picture = (src) => new Promise((done, fail) => { const img = new Image(); img.onload = () => done(img); img.onerror = fail; img.src = src; });
  const ON_MODEL = new Set(["metric", USE.id, SCALING.id, "ttft"]);
  const named = (cardElement) => {
    const id = cardElement.id.replace(/^board-/, "");
    const title = [...cardElement.querySelector("h2").childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join("").trim();
    const pick = cardElement.querySelector("[data-board-pick]")?.textContent.trim();
    const on = id === SCALING.id ? scaleModelOf(measured()) : model;
    return { title, pick, model: ON_MODEL.has(id) && on ? names().model(on) : "" };
  };
  const fileName = (cardElement, ext) => {
    const { title, pick, model: on } = named(cardElement);
    const parts = ["Pie benchmarks", pick ? `${title} (${pick})` : title, on, new Date().toISOString().slice(0, 10)].filter(Boolean);
    return `${parts.join(" - ").replace(/[\\/:*?"<>|]/g, "")}.${ext}`;
  };
  const saveData = (cardElement) => {
    if (!cardElement) return;
    const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const bars = [...cardElement.querySelectorAll(".board-bar[data-tip-head]")].map((g) => [g.dataset.tipHead, g.dataset.tipValue,
      g.dataset.tipNote || (g.dataset.tipRows ? JSON.parse(g.dataset.tipRows).map(([k, v]) => `${k}: ${v}`).join("; ") : "")]);
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
      to[i].setAttribute("style", STYLE.map((k) => `${k}:${look.getPropertyValue(k)}`).join(";"));
    });
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
    footer: () => footer(),
    outliers() {
      const rows = measured();
      return GAIN_PICKS.flatMap((pick) => {
        const seen = new Set();
        return engineIds().flatMap((e) => gainCells(rows, pick, e)).filter((c) => pastLimit(c) && !seen.has(`${c.pie.engine}|${c.pie.hardware}|${c.pie.model}`) && seen.add(`${c.pie.engine}|${c.pie.hardware}|${c.pie.model}`)).map((c) => ({
          engine: c.pie.engine, measured: c.pie.measured || null,
          setup: pick.id, label: pick.label, workload: pick.workload, key: pick.key, unit: c.s.unit,
          hardware: c.pie.hardware, model: c.pie.model, miniature: c.pie.miniature || null,
          pie: c.pie[c.s.key], best: c.best.engine, bestValue: c.best[c.s.key], gain: c.gain, above: pastLimit(c),
        }));
      });
    },
    gaps(least = 0.5, all = false) {
      const rows = measured();
      return GAIN_PICKS.flatMap((pick) => {
        const by = {};
        for (const r of rows) if (r.workload === pick.workload && r[pick.key]) (by[`${r.hardware}|${r.model}|${r.miniature || ""}|${r.benchmark || ""}`] ||= []).push(r);
        return Object.values(by).filter((list) => new Set(list.map((r) => r.engine)).size > 1).map((list) => {
          const fast = list.reduce((a, b) => (b[pick.key] > a[pick.key] ? b : a));
          const slow = list.reduce((a, b) => (b[pick.key] < a[pick.key] ? b : a));
          return { setup: pick.id, label: pick.label, hardware: fast.hardware, model: fast.model, miniature: fast.miniature || null, engines: list.length,
            fast: fast.engine, fastValue: fast[pick.key], slow: slow.engine, slowValue: slow[pick.key], gap: fast[pick.key] / slow[pick.key] - 1,
            limit: limitOf(fast, pick), measured: fast.measured || null };
        }).map((g) => ({ ...g, spread: g.limit ? (g.fastValue - g.slowValue) / g.limit : null })).filter((g) => all || (g.spread >= least && g.fastValue <= g.limit));
      }).sort((a, b) => b.spread - a.spread);
    },
    menu(k) {
      if (k === "use-engine" || k === "scale-engine") {
        const current = k === "use-engine" ? useEngine : scaleEngine;
        const multi = (r) => k !== "scale-engine" || (Pie.store.index.hardware[r.hardware]?.count || 1) > 1;
        const ran = new Set(measured().filter((r) => r.workload === "raw" && r.decode_tok_s && multi(r)).map((r) => r.engine));
        return [{ value: "", label: "Fastest engine", selected: !current },
          ...engineIds().filter((e) => ran.has(e)).map((e) => ({ value: e, label: names().engine(e), selected: e === current, icon: engineMark(e) }))];
      }
      if (k === "gain-engine") {
        const ran = new Set(measured().map((r) => r.engine));
        return engineIds().filter((e) => ran.has(e)).map((e) => ({ value: e, label: names().engine(e), selected: e === gainEngine, icon: engineMark(e) }));
      }
      if (k === "use-mode") return USE_MODES.map((m) => ({ value: m.id, label: m.label, selected: m.id === useMode, icon: Pie.platform.degree(m.id) }));
      if (k === "scale") {
        const current = scaleModelOf(measured());
        return scaleModels(measured()).map((id) => ({ value: id, label: names().model(id), selected: id === current, icon: Pie.platform.makerBadge(id) }));
      }
      if (k === "accuracy-platform") {
        const acc = Pie.checks?.accuracyChart(state);
        return (acc?.platforms || []).map((p) => ({ value: p, label: Pie.schema[p]?.label || p, selected: p === acc.platform, icon: Pie.platform.badge(p) }));
      }
      if (k === "size" || k === "moe") return SIZES.map((m) => ({ value: m.id, label: m.label, selected: m.id === (k === "moe" ? moeMetric : sizeMetric), icon: Pie.platform.degree(m.setup) }));
      if (k === "gain-setup") return GAIN_PICKS.map((g) => ({ value: g.id, label: g.label, selected: g.id === gainSetup, icon: Pie.platform.degree(g.id) }));
      if (k === "relative-setup") return GAIN_PICKS.map((g) => ({ value: g.id, label: g.label, selected: g.id === relSetup, icon: Pie.platform.degree(g.id) }));
      if (k === "cmp-platform" && state) { const c = comparePick(measured()); return c.list.map((p) => ({ value: p, label: BY_MODEL[p]?.[0] || Pie.schema[p]?.short || p, selected: p === c.p,
        icon: `<span class="sidebar-glyph" style="--tint: ${Pie.schema[p]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(p)}</span>` })); }
      if (k === "cmp-hw" && state) { const c = comparePick(measured()); return c.machines.map((id) => ({ value: id, label: machineName(id), selected: id === c.hw })); }
      if ((k !== "model" && k !== "ttft-model") || !state) return [];
      const current = k === "ttft-model" ? ttftModel : model;
      return models(measured()).map((id) => ({ value: id, label: names().model(id), selected: id === current, icon: Pie.platform.makerBadge(id) }));
    },
    pick(k, value) {
      if (k === "model") model = value;
      if (k === "cmp-platform") { cmpPlatform = value; delete machineFor.metric[value]; }
      if (k === "cmp-hw") machineFor.metric[comparePick(measured()).p] = value;
      if (k === "ttft-model") ttftModel = value;
      if (k === "accuracy-platform") Pie.checks?.pick(value);
      if (k === "gain-engine" && Pie.store.tables.engines.some((x) => x.id === value)) { gainEngine = value; try { localStorage.setItem("pieGainEngine", value); } catch { } }
      if (k === "use-mode" && USE_MODES.some((m) => m.id === value)) { useMode = value; try { localStorage.setItem("pieUseMode", value); } catch { } }
      if (k === "relative-setup" && GAIN_PICKS.some((g) => g.id === value)) {
        relSetup = value;
        try { localStorage.setItem(REL_KEY, value); } catch { }
      }
      if (k === "gain-setup" && GAIN_PICKS.some((g) => g.id === value)) {
        gainSetup = value;
        try { localStorage.setItem(GAIN_KEY, value); } catch { }
      }
      if (k === "summary" && SUMMARY_WORKLOADS.some((w) => w.id === value)) {
        summaryWorkload = value;
        try { localStorage.setItem(SUMMARY_KEY, value); } catch { }
      }
      if (k === "use-engine" || k === "scale-engine") {
        const engine = value || null;
        if (k === "use-engine") useEngine = engine; else scaleEngine = engine;
        try { engine ? localStorage.setItem(ENGINE_KEYS[k], engine) : localStorage.removeItem(ENGINE_KEYS[k]); } catch { }
      }
      if (k === "scale") {
        scaleModel = value;
        try { localStorage.setItem(SCALE_KEY, value); } catch { }
      }
      if (k === "moe" && SIZES.some((m) => m.id === value)) {
        moeMetric = value;
        try { localStorage.setItem(MOE_KEY, value); } catch { }
      }
      if (k === "size" && SIZES.some((m) => m.id === value)) {
        sizeMetric = value;
        try { localStorage.setItem(SIZE_KEY, value); } catch { }
      }
      element.dataset.key = "";
    },
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "board";
      const key = `${model}|${ttftModel}|${cmpPlatform}|${JSON.stringify(machineFor.metric)}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        const was = element.querySelector(".board-scroll");
        const at = was ? [was.scrollTop, was.scrollLeft] : null;
        element.innerHTML = page();
        requestAnimationFrame(paddles);
        requestAnimationFrame(drawBumps);
        element.dataset.key = key;
        const now = element.querySelector(".board-scroll");
        if (at && now) [now.scrollTop, now.scrollLeft] = at;
        follow();
      }
    },
  };
})();
