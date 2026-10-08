window.Pie = window.Pie || {};

// The overview: for one Mac and one workload, where pie stands against every other engine.
// Four answers, top to bottom: how often pie wins, against which engine, on which model, and the trend.
(() => {
  const element = document.getElementById("overview");
  const tooltip = document.getElementById("chart-tooltip");
  const WORKLOADS = [
    { id: "single", label: "Single request" },
    { id: "throughput", label: "Throughput" },
  ];
  const METRICS = [
    { id: "decode_tok_s", key: "decode_tok_s", label: "Decode" },
    { id: "prefill_tok_s", key: "prefill_tok_s", label: "Prefill" },
  ];
  let onChange = () => {};
  let onOpenMac = () => {};
  let onOpenWorkload = () => {};
  let onOpenMetric = () => {};

  const esc = (value) => Pie.format.escape(value);
  const names = () => Pie.store.names;
  const isPie = (row) => Pie.engines.isPrimary(row.engine);

  // "Apple M5 Max" + 64 GiB -> "M5 Max 64GB": two Macs share a chip, so the memory tells them apart
  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    if (!hw) return id;
    return `${String(hw.name).replace(/^Apple\s+/, "")}${hw.memory_gib ? ` ${hw.memory_gib}GB` : ""}`;
  };

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

  const section = (title, caption, body, extra = "", modifier = "") => `
    <section class="overview-section ${modifier}">
      <div class="section-head">
        <div>
          <h2 class="section-title">${esc(title)}</h2>
          ${caption ? `<div class="section-caption">${caption}</div>` : ""}
        </div>
        ${extra}
      </div>
      ${body}
    </section>`;

  // pie's median decode advantage per tag, oldest to newest, up to the picked release
  const releasePoints = (state, models) => {
    const tags = Pie.store.tables.tags || [];
    const upto = tags.findIndex((tag) => tag.id === state.release);
    const { hardware, workload } = state.overview;
    const points = [];
    for (const tag of tags.slice(Math.max(upto, 0)).reverse()) {
      const rows = Pie.store.snapshot(tag.id).filter((row) => row.hardware === hardware && row.workload === workload);
      if (!rows.some((row) => !row.stale)) continue;
      const list = comparisons(groupByModel(rows), models, "decode_tok_s");
      if (list.length) points.push({ tag: tag.id, date: tag.date, r: median(list.map((c) => c.r)), n: list.length });
    }
    return points;
  };

  // a line of those points, as tall as the ring: a dot per tag, its value above, the tag below
  const trend = (points) => {
    const height = 176, top = 36, bottom = 140;
    const logs = points.map((p) => Math.log(p.r));
    const lo = Math.min(0, ...logs), hi = Math.max(0, ...logs);
    const pad = (hi - lo) * 0.1 || 0.05;
    const y = (r) => bottom - ((Math.log(r) - (lo - pad)) / (hi - lo + 2 * pad)) * (bottom - top);
    const x = (i) => `${8 + (i * 84) / (points.length - 1)}%`;
    const parity = y(1).toFixed(1);
    const segments = points.slice(1).map((p, i) =>
      `<line class="trend-line" x1="${x(i)}" y1="${y(points[i].r).toFixed(1)}" x2="${x(i + 1)}" y2="${y(p.r).toFixed(1)}"/>`).join("");
    const marks = points.map((p, i) => {
      const tip = `${p.tag}${p.date ? `, ${Pie.format.date(p.date)}` : ""}\nMedian decode ${delta(p.r)} over ${p.n} comparisons`;
      const cy = y(p.r).toFixed(1);
      return `<g data-tip="${esc(tip)}">
          <circle class="trend-hit" cx="${x(i)}" cy="${cy}" r="16"/>
          <circle class="trend-dot" cx="${x(i)}" cy="${cy}" r="6"/>
          <text class="trend-value" x="${x(i)}" y="${(y(p.r) - 16).toFixed(1)}" text-anchor="middle">${delta(p.r)}</text>
          <text class="trend-tag" x="${x(i)}" y="${height - 6}" text-anchor="middle">${esc(p.tag)}</text>
        </g>`;
    }).join("");
    return `
      <svg class="trend" width="100%" height="${height}" role="img" aria-label="pie's median decode advantage by release">
        <line class="trend-parity" x1="0" x2="100%" y1="${parity}" y2="${parity}"/>
        ${segments}${marks}
      </svg>`;
  };

  // 5. Across releases: the last block, only once two tags have data
  const releases = (points) =>
    points.length >= 2 ? section("Across releases", "Median decode advantage", `<div class="trend-block">${trend(points)}</div>`) : "";

  // 1. Where we stand: Apple Fitness rings, one inside the other.
  // Outer, blue: the share of decode comparisons pie wins. Middle, green: median decode advantage.
  // Inner, teal: median prefill advantage. An advantage ring closes at 2× and laps past it,
  // the newest lap drawn over the last with a soft shadow; a deficit runs counter-clockwise in red.
  const standing = (decode, prefill) => {
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
      <div class="ring" role="img" aria-label="pie decodes faster in ${wins.length} of ${decode.length} comparisons">
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
      legend("pie leads", `${wins.length}<span>/${decode.length}</span>`, "fit-leads", false),
      legend("Median decode", decodeMid === null ? "—" : delta(decodeMid), dotOf(decodeMid, "decode"), decodeMid === null),
      legend("Median prefill", prefillMid === null ? "—" : delta(prefillMid), dotOf(prefillMid, "prefill"), prefillMid === null),
    ].join("");

    return section("Where we stand", "One model against one engine",
      `<div class="standing">${ring}<div class="stand-side">${side}</div></div>`);
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
  const fitNote = (gib) => `Needs about ${Math.round(gib)} GB${macMemory ? `; this Mac has ${macMemory} GB` : ""}`;
  // a small "no entry" mark: a hairline circle with a slash
  const noFitMark = (cx, cy) => `
    <circle class="nofit-mark" cx="${cx}" cy="${cy}" r="9"/>
    <line class="nofit-mark" x1="${cx - 6.4}" y1="${cy + 6.4}" x2="${cx + 6.4}" y2="${cy - 6.4}"/>`;

  const heatmap = (byModel, models, metric) => {
    const list = comparisons(byModel, models, metric.key);
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    const engines = [...new Set(Object.values(byModel).flat().filter((row) => !isPie(row)).map((row) => row.engine))]
      .sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
    const rowsShown = models.filter((id) => (byModel[id] || []).some(isPie) || misfit(id, Pie.engines.primary));
    if (!engines.length || !rowsShown.length) return "";

    const labelWidth = 136, col = 78, row = 64, head = 24;
    const width = labelWidth + engines.length * col;
    const height = head + rowsShown.length * row;
    const heads = engines.map((engine, j) =>
      `<text class="heat-head" x="${labelWidth + (j + 0.5) * col}" y="14" text-anchor="middle">${esc(names().engine(engine))}</text>`).join("");
    const body = rowsShown.map((model, i) => {
      const cy = head + i * row + row / 2;
      const label = `<text class="heat-label" x="0" y="${cy + 4}">${esc(names().model(model))}</text>`;
      // pie itself cannot load this model here: one quiet line across the row
      const pieNeeds = misfit(model, Pie.engines.primary);
      if (pieNeeds && !(byModel[model] || []).some(isPie)) {
        const mid = labelWidth + (engines.length * col) / 2;
        return label + `<g data-tip="${esc(`${names().model(model)}\nDoesn't fit. ${fitNote(pieNeeds)}`)}">
            <rect class="heat-hit" x="${labelWidth}" y="${cy - row / 2}" width="${engines.length * col}" height="${row}"/>
            ${noFitMark(mid - 52, cy)}
            <text class="nofit-text" x="${mid - 36}" y="${cy + 4}">Doesn't fit</text>
          </g>`;
      }
      return label + engines.map((engine, j) => {
        const cx = labelWidth + (j + 0.5) * col;
        const hit = `<rect class="heat-hit" x="${cx - col / 2}" y="${cy - row / 2}" width="${col}" height="${row}"/>`;
        const c = list.find((entry) => entry.model === model && entry.engine === engine);
        if (!c) {
          const needs = misfit(model, engine);
          if (needs) {
            return `<g data-tip="${esc(`${names().model(model)} vs ${names().engine(engine)}\n${names().engine(engine)} doesn't fit. ${fitNote(needs)}`)}">${hit}
              ${noFitMark(cx, cy)}</g>`;
          }
          return `<g data-tip="${esc(`${names().model(model)} vs ${names().engine(engine)}\nNo data`)}">${hit}
            <circle class="heat-empty" cx="${cx}" cy="${cy}" r="2.5"/></g>`;
        }
        const tip = [
          `${names().model(model)} vs ${names().engine(engine)}`,
          `${metric.label}: pie ${value(c.pie[metric.key])}, ${names().engine(engine)} ${value(c.other[metric.key])} tok/s`,
          c.other.stale ? `${names().engine(engine)}: ${when(c.other)}` : "",
          c.pie.stale ? `pie: ${when(c.pie)}` : "",
        ].filter(Boolean).join("\n");
        return `<g data-tip="${esc(tip)}">${hit}${miniRing(cx, cy, c.r)}</g>`;
      }).join("");
    }).join("");

    return section("Against each engine", `pie ÷ engine, ${metric.label.toLowerCase()} tok/s`, `
      <div class="heatmap">
        ${popup("overview-metric", "Speed", metric.label)}
        <svg class="heat-grid" viewBox="0 0 ${width} ${height}" width="${width}" role="img"
          aria-label="pie against each engine, ${metric.label.toLowerCase()}">
          <defs>
            <linearGradient id="heat-ahead" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" class="heat-stop-ahead-start"/><stop offset="1" class="heat-stop-ahead-end"/>
            </linearGradient>
            <linearGradient id="heat-behind" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" class="heat-stop-behind-start"/><stop offset="1" class="heat-stop-behind-end"/>
            </linearGradient>
          </defs>
          ${heads}${body}
        </svg>
      </div>`);
  };

  // 4. By model: one card per model, a lollipop per engine
  const figure = (model, rows) => {
    const pie = rows.find((row) => isPie(row) && row.decode_tok_s);
    const others = rows.filter((row) => !isPie(row) && row.decode_tok_s);
    const pieNeeds = misfit(model, Pie.engines.primary);
    if (!pie && pieNeeds) {
      return `<div class="figure is-empty">Doesn't fit</div><div class="figure-caption">${esc(fitNote(pieNeeds))}</div>`;
    }
    if (!pie || !others.length) {
      return `<div class="figure is-empty">—</div><div class="figure-caption">${pie ? "no other engine yet" : "no pie run yet"}</div>`;
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
            <div class="lollipop-row is-nofit${isPie({ engine }) ? " is-primary" : ""}" data-tip="${esc(`${names().engine(engine)}\nDoesn't fit. ${fitNote(tooBig[model][engine])}`)}">
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

  // macs with any row in this release, in catalog order
  const macsIn = (rows) => {
    const counts = {};
    for (const row of rows) counts[row.hardware] = (counts[row.hardware] || 0) + 1;
    const order = Pie.store.tables.hardware.map((hw) => hw.id);
    return Object.keys(counts).sort((a, b) => order.indexOf(a) - order.indexOf(b)).map((id) => ({ id, count: counts[id] }));
  };

  Pie.overview = {
    element,

    // the Macs for the pop-up menu, in catalog order
    macs(state) {
      return macsIn(Pie.store.snapshot(state.release)).map((mac) => ({ id: mac.id, label: macName(mac.id) }));
    },

    workloads() {
      return WORKLOADS;
    },

    onOpenMac(handler) {
      onOpenMac = handler;
    },

    onOpenWorkload(handler) {
      onOpenWorkload = handler;
    },

    metrics() {
      return METRICS;
    },

    onOpenMetric(handler) {
      onOpenMetric = handler;
    },

    // keep the hardware, workload and metric choice valid for the selected release
    settle(state) {
      const macs = macsIn(Pie.store.snapshot(state.release));
      if (!macs.some((mac) => mac.id === state.overview.hardware)) {
        state.overview.hardware = macs.reduce((a, b) => (b.count > a.count ? b : a), macs[0] || { id: null }).id;
      }
      if (!WORKLOADS.some((w) => w.id === state.overview.workload)) state.overview.workload = "single";
      if (!METRICS.some((m) => m.id === state.overview.metric)) state.overview.metric = "decode_tok_s";
    },

    // returns the number of models shown, for the toolbar subtitle
    render(state) {
      this.settle(state);
      const all = Pie.store.snapshot(state.release);
      const { hardware, workload } = state.overview;
      if (!macsIn(all).length) {
        element.innerHTML = `<div class="overview-empty">No results for this release yet.</div>`;
        return 0;
      }
      const query = state.query.trim().toLowerCase();
      const byModel = groupByModel(all.filter((row) => row.hardware === hardware && row.workload === workload));
      const models = Pie.store.tables.models
        .map((model) => model.id)
        .filter((id) => !query || names().model(id).toLowerCase().includes(query) || id.includes(query));
      tooBig = (Pie.store.tables.no_fit || {})[hardware] || {};
      macMemory = Pie.store.index.hardware[hardware]?.memory_gib || null;
      // measured models first, then the ones too big for this Mac
      const shown = [...models.filter((id) => byModel[id]), ...models.filter((id) => !byModel[id] && tooBig[id])];
      const missing = models.filter((id) => !byModel[id] && !tooBig[id]);
      const metric = METRICS.find((m) => m.id === state.overview.metric);

      const decode = comparisons(byModel, shown, "decode_tok_s");
      const missingNote = missing.length ? `No data yet: ${missing.map((id) => esc(names().model(id))).join(", ")}.` : "";
      const workloadLabel = WORKLOADS.find((w) => w.id === workload).label;

      element.innerHTML = `
        <div class="overview-inner">
          <div class="overview-controls">
            ${popup("overview-mac", "Mac", macName(hardware))}
            ${popup("overview-workload", "Workload", workloadLabel)}
          </div>
          ${decode.length
            ? standing(decode, comparisons(byModel, shown, "prefill_tok_s")) + heatmap(byModel, shown, metric)
            : `<div class="overview-none">No pie runs on this Mac yet.</div>`}
          ${shown.length ? section("By model", "", `<div class="model-grid">${shown.map((id) => card(id, byModel[id] || [])).join("")}</div>`) : ""}
          ${decode.length ? releases(releasePoints(state, shown)) : ""}
          ${missingNote ? `<p class="overview-footnote">${missingNote}</p>` : ""}
        </div>`;
      return shown.length;
    },

    onChange(handler) {
      onChange = handler;
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const button = event.target.closest("#overview-mac, #overview-workload, #overview-metric");
        if (!button) return;
        event.stopPropagation();
        ({ "overview-mac": onOpenMac, "overview-workload": onOpenWorkload, "overview-metric": onOpenMetric })[button.id](button);
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
    },
  };
})();
