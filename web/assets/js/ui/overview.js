window.Pie = window.Pie || {};

// The overview: for one Mac and one workload, where pie stands against every other engine.
// Four answers, top to bottom: how often pie wins, against which engine, on which model, and the trend.
(() => {
  const element = document.getElementById("overview");
  const tooltip = document.getElementById("chart-tooltip");
  const WORKLOADS = [
    { id: "raw", label: "Single" },
    { id: "spec", label: "Speculative" },
    { id: "throughput", label: "Batching saturated" },
  ];
  const METRICS = [
    { id: "decode_tok_s", key: "decode_tok_s", label: "Decode" },
    { id: "prefill_tok_s", key: "prefill_tok_s", label: "Prefill" },
  ];
  let onChange = () => {};
  let onOpenMac = () => {};
  let onOpenWorkload = () => {};
  let onOpenEngine = () => {};
  let onOpenHeatMac = () => {};
  let onOpenModel = () => {};
  let onOpenStandMac = () => {};
  let onOpenQualityEngine = () => {};

  const esc = (value) => Pie.format.escape(value);
  const names = () => Pie.store.names;
  // the engine every other one is measured against: the picked one, pie unless the viewer chose another
  let base = Pie.engines.primary;
  const baseName = () => names().engine(base);
  const isPie = (row) => row.engine === base;

  // "M5 Max 64 GB": two Macs share a chip, so the memory tells them apart
  const macName = (id) => Pie.platform.machineName(id);

  const value = (n) => {
    if (n === null || n === undefined) return "";
    return n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
  };

  // pie ÷ other as a signed change: +21%, −8%; from 2× up a multiple reads better than +468%
  const delta = (r) => {
    if (r >= 2) return `${r >= 10 ? Math.round(r) : r.toFixed(1)}×`;
    const pct = Math.round((r - 1) * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  const multiple = (r) => `${r >= 10 ? Math.round(r) : r.toFixed(r >= 2 ? 1 : 2)}×`;

  const tone = (r) => (r >= 1.005 ? "is-ahead" : r <= 0.995 ? "is-behind" : "");

  const median = (values) => {
    if (!values.length) return null;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = sorted.length >> 1;
    return sorted.length % 2 ? sorted[mid] : Math.sqrt(sorted[mid - 1] * sorted[mid]);
  };

  const when = (row) =>
    row.stale ? `From ${row.stale.tag}, ${Pie.format.date(row.stale.measured)}` : `Measured ${Pie.format.date(row.measured)}`;


  // a pop-up button: the same control as the release picker at the top right
  const popup = (id, label, current) => `
    <button class="release-picker overview-popup" id="${id}" type="button" aria-haspopup="menu">
      <span class="release-picker-label">${esc(label)}</span>
      <span class="release-picker-value">${esc(current)}</span>
      <svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>
    </button>`;

  // every pairing of pie with another engine on one model, for one metric
  const comparisons = (byModel, models, key) => {
    const out = [];
    for (const model of models) {
      const rows = byModel[model] || [];
      const pie = rows.find((row) => isPie(row) && row[key]);
      if (!pie) continue;
      for (const other of rows) {
        if (isPie(other) || !other[key]) continue;
        out.push({ model, engine: other.engine, pie, other, r: pie[key] / other[key] });
      }
    }
    return out;
  };

  const groupByModel = (rows) => {
    const byModel = {};
    for (const row of rows) (byModel[row.model] ||= []).push(row);
    return byModel;
  };

  // each section's mark: a white glyph on a tinted rounded square, as Apple's settings show theirs
  const SECTION_ICONS = {
    "Where we stand": ["#0a84ff", '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".6"/>'],
    "Against the best": ["#ff9f0a", '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M9 20h6"/>'],
    "Across Macs": ["#5e5ce6", '<rect x="4" y="5" width="16" height="11" rx="1.6"/><path d="M9 20h6M12 16v4"/>'],
    "Across models": ["#bf5af2", '<path d="M12 4 4 8l8 4 8-4-8-4z"/><path d="m4 12 8 4 8-4"/><path d="m4 16 8 4 8-4"/>'],
    "By model": ["#30d158", '<path d="M5 19V9M10 19V5M15 19v-7M20 19v-4"/>'],
    "Quality": ["#34c759", '<path d="m6 12.5 4 4 8-9"/>'],
    "Across releases": ["#ff9f0a", '<path d="M4 17l5-5 4 3 7-8"/><path d="M15 7h5v5"/>'],
  };
  const sectionIcon = (title) => {
    const icon = SECTION_ICONS[/^Where .* stands$/.test(title) ? "Where we stand" : title];
    return icon ? `<span class="section-icon" style="--tint: ${icon[0]}"><svg viewBox="0 0 24 24" aria-hidden="true">${icon[1]}</svg></span>` : "";
  };

  // the ring gradients every ring on the page paints with: drawn once, whatever each section shows
  const RING_DEFS = `
    <svg class="heat-defs" width="0" height="0" aria-hidden="true">
      <defs>
        <linearGradient id="heat-ahead" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" class="heat-stop-ahead-start"/><stop offset="1" class="heat-stop-ahead-end"/>
        </linearGradient>
        <linearGradient id="heat-behind" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" class="heat-stop-behind-start"/><stop offset="1" class="heat-stop-behind-end"/>
        </linearGradient>
      </defs>
    </svg>`;

  const section = (title, caption, body, extra = "", modifier = "") => `
    <section class="overview-section ${modifier}">
      <div class="section-head">
        <div class="section-heading">
          ${sectionIcon(title)}
          <div>
          <h2 class="section-title">${esc(title)}</h2>
          ${caption ? `<div class="section-caption">${caption}</div>` : ""}
          </div>
        </div>
        ${extra}
      </div>
      ${body}
    </section>`;

  // 1. Where we stand: Apple Fitness rings, one inside the other.
  // Outer, blue: the share of decode comparisons pie wins. Middle, green: median decode advantage.
  // Inner, teal: median prefill advantage. An advantage ring closes at 2× and laps past it,
  // the newest lap drawn over the last with a soft shadow; a deficit runs counter-clockwise in red.
  const standing = (decode, prefill, mac) => {
    const wins = decode.filter((c) => c.r > 1);
    const decodeMid = median(decode.map((entry) => entry.r));
    const prefillMid = median(prefill.map((entry) => entry.r));
    const size = 220, stroke = 22, gap = 3, c = size / 2;
    const rings = [
      { key: "leads", share: decode.length ? wins.length / decode.length : 0, ccw: false },
      { key: "decode", share: decodeMid === null ? 0 : Math.abs(Math.log2(decodeMid)), ccw: decodeMid !== null && decodeMid < 1, behind: decodeMid !== null && decodeMid < 0.995 },
      { key: "prefill", share: prefillMid === null ? 0 : Math.abs(Math.log2(prefillMid)), ccw: prefillMid !== null && prefillMid < 1, behind: prefillMid !== null && prefillMid < 0.995 },
    ];
    const arc = (radius, share, cls, ccw, shadow) => {
      const length = 2 * Math.PI * radius;
      const turn = `rotate(-90 ${c} ${c})`;
      return `<circle class="${cls}${shadow ? " is-lap" : ""}" cx="${c}" cy="${c}" r="${radius}" stroke-width="${stroke}"
        stroke-dasharray="${Math.max(length * share, 0.01).toFixed(2)} ${length.toFixed(2)}"
        transform="${ccw ? `translate(${2 * c} 0) scale(-1 1) ${turn}` : turn}"/>`;
    };
    const drawn = rings.map((ring, i) => {
      const radius = c - stroke / 2 - i * (stroke + gap);
      const kind = `fit-${ring.key}${ring.behind ? " is-behind" : ""}`;
      const laps = Math.min(ring.share, 3);
      const whole = Math.floor(laps);
      const rest = laps - whole;
      const marks = [];
      if (whole >= 1) marks.push(arc(radius, 1, `fit-arc ${kind}`, ring.ccw, false));
      if (rest > 0.002) marks.push(arc(radius, rest, `fit-arc ${kind}`, ring.ccw, whole >= 1));
      return `<circle class="fit-track ${kind}" cx="${c}" cy="${c}" r="${radius}" stroke-width="${stroke}"/>${marks.join("")}`;
    }).join("");

    const grad = (id, start, end) => `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" style="stop-color: var(${start})"/><stop offset="1" style="stop-color: var(${end})"/></linearGradient>`;
    const ring = `
      <div class="ring" role="img" aria-label="Pie decodes faster in ${wins.length} of ${decode.length} comparisons">
        <svg viewBox="0 0 ${size} ${size}" aria-hidden="true">
          <defs>
            ${grad("fit-leads", "--color-ring-start", "--color-engine-pie")}
            ${grad("fit-decode", "--color-heat-ahead-start", "--color-ring-decode")}
            ${grad("fit-prefill", "--color-ring-prefill-start", "--color-ring-prefill")}
            ${grad("fit-behind", "--color-heat-behind-start", "--color-negative")}
            <filter id="fit-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="1.6" flood-color="#000" flood-opacity=".28"/>
            </filter>
          </defs>
          ${drawn}
        </svg>
      </div>`;

    // numbers in plain ink, labels in grey; a dot in the ring's colour ties each one to its ring
    const legend = (label, figure, dot, empty) => `
      <div class="stand-metric">
        <div class="stand-label"><span class="stand-dot ${dot}"></span>${label}</div>
        <div class="stand-value${empty ? " is-empty" : ""}">${figure}</div>
      </div>`;
    const dotOf = (mid, key) => `fit-${key}${mid !== null && mid < 0.995 ? " is-behind" : ""}`;
    const side = [
      legend(`${baseName()} leads`, `${wins.length}<span>/${decode.length}</span>`, "fit-leads", false),
      legend("Median decode", decodeMid === null ? "—" : delta(decodeMid), dotOf(decodeMid, "decode"), decodeMid === null),
      legend("Median prefill", prefillMid === null ? "—" : delta(prefillMid), dotOf(prefillMid, "prefill"), prefillMid === null),
    ].join("");

    return section(`Where ${baseName()} stands`, "One model against one engine",
      `<div class="standing">${ring}<div class="stand-side">${side}</div></div>`, popup("overview-stand-mac", "Mac", macName(mac)));
  };

  // 3. Against each engine: models down, engines across, a small activity ring per pairing.
  // The arc closes at 2× (or ½×): clockwise and green where pie leads, counter-clockwise and red where it trails.
  const PARITY = 0.03;
  const miniRing = (cx, cy, r) => {
    const radius = 23, stroke = 4.5, length = 2 * Math.PI * radius;
    const near = Math.abs(r - 1) < PARITY;
    const kind = near ? "is-even" : r > 1 ? "is-ahead" : "is-behind";
    const share = Math.min(Math.abs(Math.log2(r)), 1);
    const turn = `rotate(-90 ${cx} ${cy})`;
    const arc = near ? "" : `<circle class="mini-arc" cx="${cx}" cy="${cy}" r="${radius}" stroke-width="${stroke}"
        stroke-dasharray="${Math.max(length * share, 0.01).toFixed(2)} ${length.toFixed(2)}"
        transform="${r < 1 ? `translate(${2 * cx} 0) scale(-1 1) ${turn}` : turn}"/>`;
    return `
        <circle class="mini-track ${kind}" cx="${cx}" cy="${cy}" r="${radius}" stroke-width="${stroke}"/>${arc ? arc.replace("mini-arc", `mini-arc ${kind}`) : ""}
        <text class="mini-value ${kind}" x="${cx}" y="${cy + 4}" text-anchor="middle">${delta(r)}</text>`;
  };

  // setups too big for the selected Mac: {model: {engine: GiB needed}}, from the planner's fit rule
  let tooBig = {};
  let macMemory = null;
  const misfit = (model, engine) => tooBig[model]?.[engine];
  const fitNote = (gib, model) => {
    // MoE models say whether their experts stream from the SSD; dense ones carry "n/a"
    const streaming = ["Without", "With"].includes(Pie.store.index.models[model]?.ssd_streaming) ? Pie.store.index.models[model].ssd_streaming : "";
    // a Mac's GPU can use about two thirds of its memory up to 36 GB and three quarters above (the planner's rule)
    const gpu = macMemory ? Math.round(macMemory * (macMemory <= 36 ? 2 / 3 : 0.75)) : null;
    return `Needs about ${Math.round(gib)} GB${streaming ? ` ${streaming.toLowerCase()} SSD streaming` : ""}${gpu ? `; this Mac's GPU can use about ${gpu} GB` : ""}`;
  };
  // a small "no entry" mark: a hairline circle with a slash
  const noFitMark = (cx, cy) => `
    <circle class="nofit-mark" cx="${cx}" cy="${cy}" r="9"/>
    <line class="nofit-mark" x1="${cx - 6.4}" y1="${cy + 6.4}" x2="${cx + 6.4}" y2="${cy - 6.4}"/>`;

  // the grid reads like an Apple inset table: one rounded group per speed, a row per model,
  // the model name flush left, one even column per engine, hairlines between rows
  const CELL = 52;
  const cellSvg = (inner) => `<svg class="heat-cell-svg" viewBox="0 0 ${CELL} ${CELL}" width="${CELL}" height="${CELL}" aria-hidden="true">${inner}</svg>`;

  // one ring cell: the ring, a "doesn't fit" mark, or a quiet dot where nothing was measured
  const heatCell = (byModel, model, engine, metric, list, extra = "") => {
    const mid = CELL / 2;
    const c = list.find((entry) => entry.model === model && entry.engine === engine);
    if (!c) {
      const needs = misfit(model, engine);
      if (needs) {
        return `<div class="heat-cell${extra}" role="cell" data-tip="${esc(`${names().model(model)} vs ${names().engine(engine)}\n${names().engine(engine)} doesn't fit. ${fitNote(needs, model)}`)}">
          ${cellSvg(noFitMark(mid, mid))}</div>`;
      }
      return `<div class="heat-cell${extra}" role="cell" data-tip="${esc(`${names().model(model)} vs ${names().engine(engine)}\n${metric.label}: no data`)}">
        ${cellSvg(noFitMark(mid, mid))}</div>`;
    }
    const tip = [
      `${names().model(model)} vs ${names().engine(engine)}`,
      `${metric.label}: ${baseName()} ${value(c.pie[metric.key])}, ${names().engine(engine)} ${value(c.other[metric.key])} tok/s`,
      c.other.stale ? `${names().engine(engine)}: ${when(c.other)}` : "",
      c.pie.stale ? `${baseName()}: ${when(c.pie)}` : "",
    ].filter(Boolean).join("\n");
    return `<div class="heat-cell${extra}" role="cell" data-tip="${esc(tip)}">${cellSvg(miniRing(mid, mid, c.r))}</div>`;
  };

  // the wide layout: one table, the model names once on the left, Decode and Prefill side by side
  const wideTable = (byModel, rowsShown, engines) => {
    const lists = METRICS.map((metric) => comparisons(byModel, rowsShown, metric.key));
    const n = engines.length;
    const groups = `<div class="heat-row heat-group-row" role="row"><div></div>${METRICS.map((metric, g) =>
      `<div class="heat-group-head${g ? " is-group-start" : ""}" role="columnheader" style="grid-column: span ${n}">${metric.label}</div>`).join("")}</div>`;
    const head = `<div class="heat-row heat-head-row" role="row"><div role="columnheader"></div>${METRICS.map((_, g) =>
      engines.map((engine, j) => `<div class="heat-head${g && !j ? " is-group-start" : ""}" role="columnheader">${esc(names().engine(engine))}</div>`).join("")).join("")}</div>`;
    const rows = rowsShown.map((model) => {
      const label = `<div class="heat-label" role="rowheader" title="${esc(names().model(model))}">${esc(names().model(model))}</div>`;
      const pieNeeds = misfit(model, base);
      if (pieNeeds && !(byModel[model] || []).some(isPie)) {
        const tip = esc(`${names().model(model)}\nDoesn't fit. ${fitNote(pieNeeds, model)}`);
        const cells = METRICS.map((_, g) => g).map((g) => engines.map((_, j) => `<div class="heat-cell${g && !j ? " is-group-start" : ""}" role="cell" data-tip="${tip}">${cellSvg(noFitMark(CELL / 2, CELL / 2))}</div>`).join("")).join("");
        return `<div class="heat-row" role="row">${label}${cells}</div>`;
      }
      const cells = METRICS.map((metric, g) =>
        engines.map((engine, j) => heatCell(byModel, model, engine, metric, lists[g], g && !j ? " is-group-start" : "")).join("")).join("");
      return `<div class="heat-row" role="row">${label}${cells}</div>`;
    }).join("");
    return `<div class="heat-table is-wide" role="table" aria-label="Pie against each engine, decode and prefill"
      style="--engines: ${n * METRICS.length}">${groups}${head}${rows}</div>`;
  };

  const heatTable = (byModel, rowsShown, engines, metric) => {
    const list = comparisons(byModel, rowsShown, metric.key);
    const head = `<div class="heat-row heat-head-row" role="row"><div role="columnheader"></div>${engines.map((engine) =>
      `<div class="heat-head" role="columnheader">${esc(names().engine(engine))}</div>`).join("")}</div>`;
    const rows = rowsShown.map((model) => {
      const label = `<div class="heat-label" role="rowheader" title="${esc(names().model(model))}">${esc(names().model(model))}</div>`;
      // pie itself cannot load this model here: one quiet line across the row
      const pieNeeds = misfit(model, base);
      if (pieNeeds && !(byModel[model] || []).some(isPie)) {
        const tip = esc(`${names().model(model)}\nDoesn't fit. ${fitNote(pieNeeds, model)}`);
        const cells = [0].map((g) => engines.map((_, j) => `<div class="heat-cell${g && !j ? " is-group-start" : ""}" role="cell" data-tip="${tip}">${cellSvg(noFitMark(CELL / 2, CELL / 2))}</div>`).join("")).join("");
        return `<div class="heat-row" role="row">${label}${cells}</div>`;
      }
      const cells = engines.map((engine) => heatCell(byModel, model, engine, metric, list)).join("");
      return `<div class="heat-row" role="row">${label}${cells}</div>`;
    }).join("");
    return `
      <div class="heat-group">
        <div class="heat-group-title">${metric.label}</div>
        <div class="heat-table" role="table" aria-label="Pie against each engine, ${metric.label.toLowerCase()}"
          style="--engines: ${engines.length}">${head}${rows}</div>
      </div>`;
  };

  // a section's view: rings of the picked engine against each other, or bars of every engine's tok/s
  const viewToggle = (key, current, options = [["rings", "Rings"], ["bars", "Bars"]]) => `
    <div class="view-toggle" role="group" aria-label="View">
      ${options.map(([id, label]) =>
        `<button type="button" class="${current === id ? "is-active" : ""}" data-view-key="${key}" data-view="${id}" aria-pressed="${current === id}">${label}</button>`).join("")}
    </div>`;
  const tools = (...parts) => `<div class="section-tools">${parts.join("")}</div>`;

  // one entry per row (a model or a Mac): Decode and Prefill, a bar per engine, longest bar = fastest in that row
  const barsBlock = (entries, engines) => {
    const order = [base, ...engines.filter((e) => e !== base)];
    const body = entries.map(({ label, rows, note }) => {
      if (note) return `<div class="bars-row"><div class="bars-label">${esc(label)}</div><div class="bars-note">${esc(note)}</div></div>`;
      const groups = METRICS.map((metric) => {
        const lines = order.map((engine) => ({ engine, v: rows.find((r) => r.engine === engine)?.[metric.key] })).filter((x) => x.v);
        if (!lines.length) return `<div class="bars-group"><div class="bars-head">${metric.label}</div><div class="bars-empty">no data</div></div>`;
        const top = Math.max(...lines.map((x) => x.v));
        return `<div class="bars-group"><div class="bars-head">${metric.label} <span>tok/s</span></div>${lines.map(({ engine, v }) => `
          <div class="bars-line${engine === base ? " is-primary" : ""}">
            <span class="bars-name">${esc(names().engine(engine))}</span>
            <span class="bars-track"><span class="bars-fill" style="width: ${(100 * v / top).toFixed(1)}%"></span></span>
            <span class="bars-value">${value(v)}</span>
          </div>`).join("")}</div>`;
      }).join("");
      return `<div class="bars-row"><div class="bars-label">${esc(label)}</div>${groups}</div>`;
    }).join("");
    return `<div class="bars-table">${body}</div>`;
  };

  // against the best: models down, Macs across; each cell is the picked engine against the fastest other engine there
  const bestOf = (rows, model, mac, key) => {
    const here = rows.filter((row) => row.model === model && row.hardware === mac);
    const pie = here.find((row) => isPie(row) && row[key]);
    const others = here.filter((row) => !isPie(row) && row[key]);
    if (!pie || !others.length) return null;
    const best = others.reduce((a, b) => (b[key] > a[key] ? b : a));
    return { pie, best, r: pie[key] / best[key] };
  };
  const bestMissing = (model, mac) => {
    const needs = ((Pie.store.tables.no_fit || {})[mac] || {})[model]?.[base];
    return needs ? `${baseName()} doesn't fit (needs about ${Math.round(needs)} GB)` : "no data";
  };
  const bestTip = (model, mac, metric, c) => `${names().model(model)} on ${macName(mac)}\n${metric.label}: ${baseName()} ${value(c.pie[metric.key])}, ` +
    `fastest other ${names().engine(c.best.engine)} ${value(c.best[metric.key])} tok/s`;
  const bestCell = (rows, model, mac, metric, extra = "") => {
    const mid = CELL / 2;
    const c = bestOf(rows, model, mac, metric.key);
    if (!c) {
      return `<div class="heat-cell${extra}" role="cell" data-tip="${esc(`${names().model(model)} on ${macName(mac)}\n${metric.label}: ${bestMissing(model, mac)}`)}">${cellSvg(noFitMark(mid, mid))}</div>`;
    }
    return `<div class="heat-cell${extra}" role="cell" data-tip="${esc(bestTip(model, mac, metric, c))}">${cellSvg(miniRing(mid, mid, c.r))}</div>`;
  };
  // "M5 Max" over "128GB": the column stays narrow enough for twelve of them
  const macHead = (mac) => {
    const name = macName(mac);
    const at = name.lastIndexOf(" ");
    return at > 0 ? `${esc(name.slice(0, at))}<br><span>${esc(name.slice(at + 1))}</span>` : esc(name);
  };
  const bestSection = (all, models, workload, view) => {
    const rows = all.filter((row) => row.workload === workload);
    const macs = Pie.store.tables.hardware.map((hw) => hw.id).filter((mac) => all.some((row) => row.hardware === mac));
    if (!macs.length || !models.length) return "";
    const head = tools(viewToggle("bestView", view));
    const caption = `${esc(baseName())} against the fastest other engine`;
    const label = (model) => `<div class="heat-label" role="rowheader" title="${esc(names().model(model))}">${esc(names().model(model))}</div>`;
    if (view === "bars") {
      const body = models.map((model) => `<div class="bars-row"><div class="bars-label">${esc(names().model(model))}</div>${METRICS.map((metric) => {
        const lines = macs.map((mac) => ({ mac, c: bestOf(rows, model, mac, metric.key) }));
        return `<div class="bars-group"><div class="bars-head">${metric.label} <span>vs the fastest</span></div>${lines.map(({ mac, c }) => c ? `
          <div class="bars-line best-line ${c.r >= 1 ? "is-ahead" : "is-behind"}" data-tip="${esc(bestTip(model, mac, metric, c))}">
            <span class="bars-name">${esc(macName(mac))}</span>
            <span class="bars-track"><span class="bars-fill" style="width: ${(50 * Math.min(c.r, 2)).toFixed(1)}%"></span></span>
            <span class="bars-value">${delta(c.r)}</span>
          </div>` : `
          <div class="bars-line best-line" data-tip="${esc(`${names().model(model)} on ${macName(mac)}\n${metric.label}: ${bestMissing(model, mac)}`)}">
            <span class="bars-name">${esc(macName(mac))}</span><span class="bars-track"></span><span class="bars-value">—</span>
          </div>`).join("")}</div>`;
      }).join("")}</div>`).join("");
      return section("Against the best", caption, `<div class="bars-table best-bars">${body}</div>`, head);
    }
    const n = macs.length;
    const groups = `<div class="heat-row heat-group-row" role="row"><div></div>${METRICS.map((metric, g) =>
      `<div class="heat-group-head${g ? " is-group-start" : ""}" role="columnheader" style="grid-column: span ${n}">${metric.label}</div>`).join("")}</div>`;
    const headRow = (g0) => `<div class="heat-row heat-head-row" role="row"><div role="columnheader"></div>${(g0 === null ? METRICS.map((_, g) => g) : [g0]).map((g) =>
      macs.map((mac, j) => `<div class="heat-head best-head${g && !j && g0 === null ? " is-group-start" : ""}" role="columnheader">${macHead(mac)}</div>`).join("")).join("")}</div>`;
    const wide = models.map((model) => `<div class="heat-row" role="row">${label(model)}${METRICS.map((metric, g) =>
      macs.map((mac, j) => bestCell(rows, model, mac, metric, g && !j ? " is-group-start" : "")).join("")).join("")}</div>`).join("");
    const stacked = METRICS.map((metric, g) => `
      <div class="heat-group">
        <div class="heat-group-title">${metric.label}</div>
        <div class="heat-table" role="table" style="--engines: ${n}">${headRow(g)}${models.map((model) =>
          `<div class="heat-row" role="row">${label(model)}${macs.map((mac) => bestCell(rows, model, mac, metric)).join("")}</div>`).join("")}</div>
      </div>`).join("");
    return section("Against the best", caption, `
      <div class="heatmap">
        <div class="heat-wide"><div class="heat-table is-wide" role="table" aria-label="${esc(baseName())} against the fastest other engine"
          style="--engines: ${n * METRICS.length}">${groups}${headRow(null)}${wide}</div></div>
        <div class="heat-stacked">${stacked}</div>
      </div>`, head);
  };

  const heatmap = (byModel, models, mac, view, others) => {
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    const engines = [...new Set(Object.values(byModel).flat().filter((row) => !isPie(row)).map((row) => row.engine))]
      .sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
    if (!engines.length) engines.push(...others);
    // every model of the suite has its row: measured, too big, or crossed out until it is measured
    const rowsShown = models;
    if (!engines.length || !rowsShown.length) return "";

    const head = tools(viewToggle("modelsView", view), popup("overview-heat-mac", "Mac", macName(mac)));
    if (view === "bars") {
      const entries = rowsShown.map((id) => ({ label: names().model(id), rows: byModel[id] || [],
        note: (byModel[id] || []).some(isPie) ? "" : misfit(id, base) ? `Doesn't fit. ${fitNote(misfit(id, base), id)}` : "No data yet" }));
      return section("Across models", `How ${baseName()}’s speed compares on one Mac, model by model`, barsBlock(entries, engines), head);
    }
    return section("Across models", `How ${baseName()}’s speed compares on one Mac, model by model`, `
      <div class="heatmap">
        <div class="heat-wide">${wideTable(byModel, rowsShown, engines)}</div>
        <div class="heat-stacked">${METRICS.map((metric) => heatTable(byModel, rowsShown, engines, metric)).join("")}</div>
      </div>`, head);
  };

  // across Macs: one model, a row per Mac, the picked engine against each other engine
  const macCell = (rows, mac, engine, metric, model) => {
    const mid = CELL / 2;
    const title = `${macName(mac)}: ${baseName()} vs ${names().engine(engine)}`;
    const mine = rows.find(isPie);
    const other = rows.find((row) => row.engine === engine);
    if (!mine?.[metric.key] || !other?.[metric.key]) {
      const needs = ((Pie.store.tables.no_fit || {})[mac] || {})[model]?.[mine ? engine : base];
      if (needs) {
        return `<div class="heat-cell" role="cell" data-tip="${esc(`${title}\nDoesn't fit (needs about ${Math.round(needs)} GB)`)}">${cellSvg(noFitMark(mid, mid))}</div>`;
      }
      return `<div class="heat-cell" role="cell" data-tip="${esc(`${title}\n${metric.label}: no data`)}">
        ${cellSvg(noFitMark(mid, mid))}</div>`;
    }
    const r = mine[metric.key] / other[metric.key];
    const tip = `${title}\n${metric.label}: ${baseName()} ${value(mine[metric.key])}, ${names().engine(engine)} ${value(other[metric.key])} tok/s`;
    return `<div class="heat-cell" role="cell" data-tip="${esc(tip)}">${cellSvg(miniRing(mid, mid, r))}</div>`;
  };

  // the engines the release compares against, for a model with no numbers of its own
  const competitors = (all) => {
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    return [...new Set(all.filter((row) => !isPie(row)).map((row) => row.engine))].sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
  };

  const acrossMacs = (all, workload, model, view) => {
    if (!model) return "";
    const rows = all.filter((row) => row.model === model && row.workload === workload);
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    const engines = [...new Set(rows.filter((row) => !isPie(row)).map((row) => row.engine))]
      .sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
    if (!engines.length) engines.push(...competitors(all));
    const known = Pie.store.tables.hardware.map((hw) => hw.id);
    const measured = known.filter((mac) => rows.some((row) => row.hardware === mac) || ((Pie.store.tables.no_fit || {})[mac] || {})[model]);
    const macs = measured.length ? measured : known.filter((mac) => all.some((row) => row.hardware === mac));
    if (!engines.length || !macs.length) return "";
    const head = tools(viewToggle("macsView", view), popup("overview-model", "Model", names().model(model)));
    if (view === "bars") {
      const entries = macs.map((mac) => {
        const here = rows.filter((row) => row.hardware === mac);
        const needs = ((Pie.store.tables.no_fit || {})[mac] || {})[model]?.[base];
        return { label: macName(mac), rows: here, note: !here.some(isPie) && needs ? `Doesn't fit (needs about ${Math.round(needs)} GB)` : "" };
      });
      return section("Across Macs", `How ${baseName()}’s speed compares on each Mac, for one model`, barsBlock(entries, engines), head);
    }
    const n = engines.length;
    const groups = `<div class="heat-row heat-group-row" role="row"><div></div>${METRICS.map((metric, g) =>
      `<div class="heat-group-head${g ? " is-group-start" : ""}" role="columnheader" style="grid-column: span ${n}">${metric.label}</div>`).join("")}</div>`;
    const heads = `<div class="heat-row heat-head-row" role="row"><div role="columnheader"></div>${METRICS.map((_, g) =>
      engines.map((engine, j) => `<div class="heat-head${g && !j ? " is-group-start" : ""}" role="columnheader">${esc(names().engine(engine))}</div>`).join("")).join("")}</div>`;
    const body = macs.map((mac) => {
      const here = rows.filter((row) => row.hardware === mac);
      const cells = METRICS.map((metric, g) => engines.map((engine, j) => {
        const cell = macCell(here, mac, engine, metric, model);
        return g && !j ? cell.replace('class="heat-cell"', 'class="heat-cell is-group-start"') : cell;
      }).join("")).join("");
      return `<div class="heat-row" role="row"><div class="heat-label" role="rowheader">${esc(macName(mac))}</div>${cells}</div>`;
    }).join("");
    return section("Across Macs", `How ${baseName()}’s speed compares on each Mac, for one model`, `
      <div class="heatmap"><div class="heat-table is-wide" role="table" aria-label="${esc(baseName())} against each engine on each Mac"
        style="--engines: ${n * METRICS.length}">${groups}${heads}${body}</div></div>`, head);
  };

  // 4. By model: one card per model, a lollipop per engine
  // quality against each engine: a model matches an engine when, on every task both scored, pie's
  // 95% interval reaches the engine's (the same questions, so a gap outside both intervals is real)
  const qualityMark = (cx, cy, ok, text) => {
    const kind = ok ? "is-ahead" : "is-behind";
    return `<circle class="mini-track ${kind}" cx="${cx}" cy="${cy}" r="23" stroke-width="4.5"/>
      <circle class="mini-arc ${kind}" cx="${cx}" cy="${cy}" r="23" stroke-width="4.5"/>
      <text class="mini-value ${kind}" x="${cx}" y="${cy + 4}" text-anchor="middle">${text}</text>`;
  };

  const TASK_NAMES = { gsm8k: "GSM8K", ifeval: "IFEval", mmlu: "MMLU", arc: "ARC", math500: "MATH-500" };

  // where each model lands on the accuracy scale: its mean over the benchmarks, the picked engine's scores
  // each model: the engines' average accuracy as the bar, their spread as the whisker, the picked engine as the mark
  const qualityRanking = (rows, models, pick) => {
    const ranked = models.map((model) => {
      const mine = rows.filter((r) => r.model === model);
      const engines = [...new Set(mine.map((r) => r.engine))];
      // the tasks every engine answered, so each engine's mean is over the same questions
      const shared = Object.keys(TASK_NAMES).filter((task) => engines.every((e) => mine.some((r) => r.engine === e && r.task === task)));
      const means = engines.map((engine) => {
        const own = mine.filter((r) => r.engine === engine && (!shared.length || shared.includes(r.task)));
        return { engine, mean: own.reduce((sum, r) => sum + r.score, 0) / own.length };
      });
      const avg = means.reduce((sum, m) => sum + m.mean, 0) / means.length;
      return { model, avg, means, low: Math.min(...means.map((m) => m.mean)), high: Math.max(...means.map((m) => m.mean)),
        mark: means.find((m) => m.engine === pick), tasks: shared.length ? shared : null };
    }).filter((x) => x.means.length).sort((a, b) => b.avg - a.avg);
    if (!ranked.length) return "";
    // a zoomed scale, so a few points of difference show
    const floor = Math.max(0, Math.floor((Math.min(...ranked.map((x) => x.low)) - 0.05) * 20) / 20);
    const at = (v) => `${(((v - floor) / (1 - floor)) * 100).toFixed(1)}%`;
    const pct = (v) => `${(v * 100).toFixed(1)}%`;
    const columns = ranked.map(({ model, avg, means, low, high, mark, tasks }) => {
      const tip = [names().model(model), `Average of ${means.length} ${means.length === 1 ? "engine" : "engines"}: ${pct(avg)}`,
        ...means.map((m) => `${names().engine(m.engine)}: ${pct(m.mean)}`),
        tasks ? `Over ${tasks.map((t) => TASK_NAMES[t]).join(", ")}` : ""].filter(Boolean).join("\n");
      return `<div class="rank-col" data-tip="${esc(tip)}">
        <span class="rank-value${mark ? "" : " is-quiet"}">${mark ? `${Math.round(mark.mean * 100)}%` : "—"}</span>
        <span class="rank-bar">
          <span class="rank-fill" style="height: ${at(avg)}"></span>
          ${means.length > 1 ? `<span class="rank-range" style="bottom: ${at(low)}; height: calc(${at(high)} - ${at(low)})"></span>` : ""}
          ${mark ? `<span class="rank-mark" style="bottom: ${at(mark.mean)}"></span>` : ""}
        </span>
        <span class="rank-name">${esc(names().model(model))}</span>
      </div>`;
    }).join("");
    return `<div class="rank-chart" role="img" aria-label="Average accuracy per model across engines, with ${esc(names().engine(pick))} marked">
        <span class="rank-axis rank-axis-top">100%</span><span class="rank-axis rank-axis-bottom">${Math.round(floor * 100)}%</span>
        ${columns}
      </div>
      <div class="rank-legend">
        <span><i class="is-bar"></i>Average of all engines</span>
        <span><i class="is-range"></i>Range across engines</span>
        <span><i class="is-mark"></i>${esc(names().engine(pick))}</span>
      </div>`;
  };

  const qualityTable = (state) => {
    const rows = Pie.store.qualitySnapshot(state.release).filter((r) => typeof r.score === "number");
    const modelOrder = Pie.store.tables.models.map((m) => m.id);
    const models = [...new Set(rows.map((r) => r.model))].sort((a, b) => modelOrder.indexOf(a) - modelOrder.indexOf(b));
    if (!models.length) return "";
    const pick = state.overview.qualityEngine || base;
    return section("Quality", "Average accuracy", qualityRanking(rows, models, pick),
      tools(popup("overview-quality-engine", "Engine", names().engine(pick))));
  };

  const figure = (model, rows) => {
    const pie = rows.find((row) => isPie(row) && row.decode_tok_s);
    const others = rows.filter((row) => !isPie(row) && row.decode_tok_s);
    const pieNeeds = misfit(model, base);
    if (!pie && pieNeeds) {
      return `<div class="figure is-empty">Doesn't fit</div><div class="figure-caption">${esc(fitNote(pieNeeds, model))}</div>`;
    }
    if (!pie || !others.length) {
      return `<div class="figure is-empty">—</div><div class="figure-caption">${pie ? "no other engine yet" : `no ${baseName()} run yet`}</div>`;
    }
    const best = others.reduce((a, b) => (b.decode_tok_s > a.decode_tok_s ? b : a));
    const r = pie.decode_tok_s / best.decode_tok_s;
    return `<div class="figure ${tone(r)}">${delta(r)}</div>
      <div class="figure-caption">decode vs ${esc(names().engine(best.engine))}, the fastest other</div>`;
  };

  const lollipops = (model, rows, metric) => {
    const bars = rows.filter((row) => row[metric.key]).sort((a, b) => b[metric.key] - a[metric.key]);
    // engines that cannot load the model on this Mac get a row of their own, below the measured ones
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    const misfits = Object.keys(tooBig[model] || {})
      .filter((engine) => !rows.some((row) => row.engine === engine))
      .sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
    if (!bars.length) return "";
    const max = bars[0][metric.key];
    return `
      <figure class="lollipop-chart">
        <figcaption>${metric.label} <span>tok/s</span></figcaption>
        ${bars.map((row) => {
          const tip = [
            names().engine(row.engine),
            `${metric.label}: ${value(row[metric.key])} tok/s`,
            row.version ? `Version ${row.version}` : "",
            when(row),
          ].filter(Boolean).join("\n");
          const classes = ["lollipop-row", isPie(row) ? "is-primary" : "", row.stale ? "is-stale" : ""].filter(Boolean).join(" ");
          const x = `${(Math.max(row[metric.key] / max, 0.01) * 100).toFixed(2)}%`;
          return `
            <div class="${classes}" data-tip="${esc(tip)}">
              <span class="lollipop-label">${esc(names().engine(row.engine))}</span>
              <svg class="lollipop" width="100%" height="12" aria-hidden="true">
                <line x1="0" y1="6" x2="${x}" y2="6"/>
                <circle cx="${x}" cy="6" r="4"/>
              </svg>
              <span class="lollipop-value">${value(row[metric.key])}</span>
            </div>`;
        }).join("")}
        ${misfits.map((engine) => `
            <div class="lollipop-row is-nofit${isPie({ engine }) ? " is-primary" : ""}" data-tip="${esc(`${names().engine(engine)}\nDoesn't fit. ${fitNote(tooBig[model][engine], model)}`)}">
              <span class="lollipop-label">${esc(names().engine(engine))}</span>
              <span class="lollipop-nofit">Doesn't fit</span>
              <span class="lollipop-value"></span>
            </div>`).join("")}
      </figure>`;
  };

  const card = (model, rows) => `
    <article class="model-card">
      <h3>${esc(names().model(model))}</h3>
      ${figure(model, rows)}
      <div class="model-card-charts">${METRICS.map((metric) => lollipops(model, rows, metric)).join("")}</div>
    </article>`;

  // an Apple-style gallery: one model card at a time with the next one peeking in, snapping as it scrolls,
  // page dots below and round arrow buttons beside them
  const carousel = (cards) => `
    <div class="carousel">
      <div class="carousel-track" tabindex="0" aria-label="Models">${cards.join("")}</div>
      ${cards.length > 1 ? `
        <div class="carousel-controls">
          <div class="carousel-dots" role="tablist">${cards.map((_, i) =>
            `<button class="carousel-dot${i === 0 ? " is-current" : ""}" type="button" role="tab" aria-label="Model ${i + 1}" data-index="${i}"></button>`).join("")}</div>
          <div class="carousel-paddles">
            <button class="carousel-paddle" type="button" data-step="-1" aria-label="Previous model" disabled>
              <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5"/></svg></button>
            <button class="carousel-paddle" type="button" data-step="1" aria-label="Next model">
              <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button>
          </div>
        </div>` : ""}
    </div>`;

  // which card sits at the track's left edge, and the dots and paddles to match
  const syncCarousel = (track) => {
    const cards = [...track.children];
    if (!cards.length) return;
    const left = track.getBoundingClientRect().left;
    let current = 0;
    cards.forEach((card, i) => {
      if (Math.abs(card.getBoundingClientRect().left - left) < Math.abs(cards[current].getBoundingClientRect().left - left)) current = i;
    });
    const root = track.closest(".carousel");
    root.querySelectorAll(".carousel-dot").forEach((dot, i) => dot.classList.toggle("is-current", i === current));
    const [prev, next] = root.querySelectorAll(".carousel-paddle");
    if (prev) prev.disabled = track.scrollLeft <= 2;
    if (next) next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
  };

  const scrollToCard = (track, index) => {
    const card = track.children[Math.max(0, Math.min(index, track.children.length - 1))];
    if (card) track.scrollTo({ left: card.offsetLeft - track.offsetLeft, behavior: "smooth" });
  };

  // macs with any row in this release, in catalog order
  // Where <engine> stands, on its own Mac
  const standSection = (state, all, models, workload) => {
    const mac = state.overview.standMac || state.overview.hardware;
    const byModel = groupByModel(all.filter((row) => row.hardware === mac && row.workload === workload));
    const shown = models.filter((id) => byModel[id]);
    const decode = comparisons(byModel, shown, "decode_tok_s");
    if (!decode.length) {
      return section(`Where ${baseName()} stands`, "One model against one engine",
        `<div class="overview-none">No ${esc(baseName())} runs on this Mac yet.</div>`, popup("overview-stand-mac", "Mac", macName(mac)));
    }
    return standing(decode, comparisons(byModel, shown, "prefill_tok_s"), mac);
  };

  // Against each engine on its own Mac: the no-fit marks follow that Mac, then return to the page's
  const heatSection = (state, all, models, workload) => {
    const mac = state.overview.heatMac || state.overview.hardware;
    const byModel = groupByModel(all.filter((row) => row.hardware === mac && row.workload === workload));
    const keep = [tooBig, macMemory];
    tooBig = (Pie.store.tables.no_fit || {})[mac] || {};
    macMemory = Pie.store.index.hardware[mac]?.memory_gib || null;
    const html = heatmap(byModel, models, mac, state.overview.modelsView || "rings", competitors(all));
    [tooBig, macMemory] = keep;
    return html;
  };

  // "Updated 2 hr ago", the way Apple's apps date their data; the full time on hover
  const updated = () => {
    const at = Pie.store.tables.updated_at ? new Date(Pie.store.tables.updated_at) : null;
    if (!at || Number.isNaN(at.getTime())) return "";
    const minutes = Math.max(0, Math.round((Date.now() - at.getTime()) / 60000));
    const when = minutes < 1 ? "just now" : minutes < 60 ? `${minutes} min ago` : minutes < 24 * 60 ? `${Math.round(minutes / 60)} hr ago`
      : at.toLocaleDateString(undefined, { month: "short", day: "numeric", year: at.getFullYear() === new Date().getFullYear() ? undefined : "numeric" });
    const full = at.toLocaleString(undefined, { dateStyle: "long", timeStyle: "short" });
    return `<span class="overview-updated" title="${esc(full)}">Updated ${esc(when)}</span>`;
  };

  const macsIn = (rows) => {
    const counts = {};
    for (const row of rows) if (Pie.store.isMeasured(row)) counts[row.hardware] = (counts[row.hardware] || 0) + 1;
    const order = Pie.store.tables.hardware.map((hw) => hw.id);
    return Object.keys(counts).sort((a, b) => order.indexOf(a) - order.indexOf(b)).map((id) => ({ id, count: counts[id] }));
  };

  Pie.overview = {
    element,

    // every Mac we operate, in catalog order (a Mac with no run in this release still shows in the menu)
    macs() {
      return Pie.store.tables.hardware.map((hw) => ({ id: hw.id, label: macName(hw.id) }));
    },

    workloads() {
      return WORKLOADS;
    },

    // engines with numbers in this release, in the catalog's order
    engines(state) {
      const ran = new Set(Pie.store.snapshot(state.release).filter(Pie.store.isMeasured).map((r) => r.engine));
      return Pie.store.tables.engines.filter((e) => ran.has(e.id)).map((e) => ({ id: e.id, label: names().engine(e.id) }));
    },

    onOpenEngine(handler) {
      onOpenEngine = handler;
    },

    onOpenHeatMac(handler) {
      onOpenHeatMac = handler;
    },

    onOpenModel(handler) {
      onOpenModel = handler;
    },

    onOpenStandMac(handler) {
      onOpenStandMac = handler;
    },

    onOpenQualityEngine(handler) {
      onOpenQualityEngine = handler;
    },

    // engines with quality scores in this release, for the Quality section's picker
    qualityEngines(state) {
      const scored = new Set(Pie.store.qualitySnapshot(state.release).filter((r) => typeof r.score === "number").map((r) => r.engine));
      return Pie.store.tables.engines.filter((e) => scored.has(e.id)).map((e) => ({ id: e.id, label: names().engine(e.id) }));
    },

    onOpenMac(handler) {
      onOpenMac = handler;
    },

    onOpenWorkload(handler) {
      onOpenWorkload = handler;
    },


    // keep the hardware and workload choice valid for the selected release
    settle(state) {
      const macs = macsIn(Pie.store.snapshot(state.release));
      const known = Pie.store.tables.hardware.map((hw) => hw.id);
      if (!known.includes(state.overview.hardware)) {
        state.overview.hardware = macs.reduce((a, b) => (b.count > a.count ? b : a), macs[0] || { id: known[0] }).id;
      }
      if (!WORKLOADS.some((w) => w.id === state.overview.workload)) state.overview.workload = "raw";
      const ran = new Set(Pie.store.snapshot(state.release).filter(Pie.store.isMeasured).map((r) => r.engine));
      if (!state.overview.engine || !ran.has(state.overview.engine)) state.overview.engine = Pie.engines.primary;
      if (!macs.some((m) => m.id === state.overview.heatMac)) state.overview.heatMac = state.overview.hardware;
      if (!macs.some((m) => m.id === state.overview.standMac)) state.overview.standMac = state.overview.hardware;
      const models = this.models(state).map((m) => m.id);
      if (!models.includes(state.overview.model)) state.overview.model = models[0] || null;
    },

    // the suite's models, in the catalog's order, for the Across Macs picker
    models(state) {
      return Pie.store.tables.models.filter((m) => Pie.store.inSuite(m.id)).map((m) => ({ id: m.id, label: names().model(m.id) }));
    },

    // returns the number of models shown, for the toolbar subtitle
    render(state) {
      this.settle(state);
      base = state.overview.engine || Pie.engines.primary;
      const all = Pie.store.snapshot(state.release).filter(Pie.store.isMeasured);
      const { hardware, workload } = state.overview;
      // the Mac and workload pickers stay on every path, so a Mac with no runs can still be left for another one
      const controls = () => `
        <div class="overview-controls">
          ${popup("overview-workload", "Workload", (Pie.overview.workloads().find((w) => w.id === workload) || { label: workload }).label)}
          ${popup("overview-engine", "Engine", baseName())}
          ${updated()}
        </div>`;
      if (!all.some((row) => row.hardware === hardware)) {
        element.innerHTML = `<div class="overview-inner">${controls()}<div class="overview-empty">No runs on this Mac for this release yet.</div></div>`;
        return 0;
      }
      if (!macsIn(all).length) {
        element.innerHTML = `<div class="overview-inner">${controls()}<div class="overview-empty">No results for this release yet.</div></div>`;
        return 0;
      }
      const query = state.query.trim().toLowerCase();
      const byModel = groupByModel(all.filter((row) => row.hardware === hardware && row.workload === workload));
      // the picked suite's models only
      const models = Pie.store.tables.models
        .map((model) => model.id)
        .filter((id) => Pie.store.inSuite(id))
        .filter((id) => !query || names().model(id).toLowerCase().includes(query) || id.includes(query));
      tooBig = (Pie.store.tables.no_fit || {})[hardware] || {};
      macMemory = Pie.store.index.hardware[hardware]?.memory_gib || null;
      // measured models first, then the ones too big for this Mac
      const shown = [...models.filter((id) => byModel[id]), ...models.filter((id) => !byModel[id] && tooBig[id])];

      const decode = comparisons(byModel, shown, "decode_tok_s");
      const workloadLabel = (Pie.overview.workloads().find((w) => w.id === workload) || { label: workload }).label;

      element.innerHTML = `
        <div class="overview-inner">
          ${RING_DEFS}
          <div class="overview-controls">
            ${popup("overview-workload", "Workload", workloadLabel)}
            ${popup("overview-engine", "Engine", baseName())}
            ${updated()}
          </div>
          ${decode.length
            ? standSection(state, all, models, workload) + bestSection(all, models, workload, state.overview.bestView || "rings") + acrossMacs(all, workload, state.overview.model, state.overview.macsView || "rings") + heatSection(state, all, models, workload)
            : `<div class="overview-none">${all.some((row) => row.workload === workload) ? `No ${esc(baseName())} runs on this Mac yet.` : `No results for ${esc(workloadLabel)} yet.`}</div>`}
          ${qualityTable(state)}
        </div>`;
      return shown.length;
    },

    onChange(handler) {
      onChange = handler;
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const toggle = event.target.closest("[data-view-key]");
        if (toggle) {
          state.overview[toggle.dataset.viewKey] = toggle.dataset.view;
          onChange();
          return;
        }
        const button = event.target.closest("#overview-mac, #overview-workload, #overview-engine, #overview-heat-mac, #overview-model, #overview-stand-mac, #overview-quality-engine");
        if (!button) return;
        event.stopPropagation();
        ({ "overview-mac": onOpenMac, "overview-workload": onOpenWorkload, "overview-engine": onOpenEngine,
          "overview-heat-mac": onOpenHeatMac, "overview-model": onOpenModel, "overview-stand-mac": onOpenStandMac,
          "overview-quality-engine": onOpenQualityEngine })[button.id](button);
      });

      // one tooltip for every mark: what it compares, the values, and when they were measured
      element.addEventListener("pointermove", (event) => {
        const row = event.target.closest("[data-tip]");
        if (!row) {
          tooltip.hidden = true;
          return;
        }
        tooltip.textContent = row.dataset.tip;
        tooltip.hidden = false;
        const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      });
      element.addEventListener("pointerleave", () => (tooltip.hidden = true));
      element.addEventListener("scroll", () => (tooltip.hidden = true));

      // the model gallery: dots jump to a card, paddles step one card, scrolling keeps both in sync
      element.addEventListener("click", (event) => {
        const control = event.target.closest(".carousel-dot, .carousel-paddle");
        if (!control) return;
        const track = control.closest(".carousel").querySelector(".carousel-track");
        const current = [...control.closest(".carousel").querySelectorAll(".carousel-dot")].findIndex((dot) => dot.classList.contains("is-current"));
        scrollToCard(track, control.dataset.index !== undefined ? Number(control.dataset.index) : current + Number(control.dataset.step));
      });
      element.addEventListener("scroll", (event) => {
        if (event.target.classList?.contains("carousel-track")) {
          tooltip.hidden = true;
          syncCarousel(event.target);
        }
      }, true);
      element.addEventListener("keydown", (event) => {
        const track = event.target.closest?.(".carousel-track");
        if (!track || (event.key !== "ArrowLeft" && event.key !== "ArrowRight")) return;
        event.preventDefault();
        const current = [...track.closest(".carousel").querySelectorAll(".carousel-dot")].findIndex((dot) => dot.classList.contains("is-current"));
        scrollToCard(track, current + (event.key === "ArrowRight" ? 1 : -1));
      });
    },
  };
})();
