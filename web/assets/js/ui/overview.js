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

  const segmented = (name, items, selected, extra = "") => `
    <div class="segmented ${extra}" role="radiogroup" data-control="${name}">
      ${items.map((item) => `
        <button class="segment${item.id === selected ? " is-selected" : ""}" type="button" role="radio"
          aria-checked="${item.id === selected}" data-value="${esc(item.id)}">${esc(item.label)}</button>`).join("")}
    </div>`;

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

  // 1. Where we stand: an activity ring of wins, and three numbers beside it
  const standing = (decode, prefill) => {
    const wins = decode.filter((c) => c.r > 1);
    const share = decode.length ? wins.length / decode.length : 0;
    const size = 168, stroke = 20, radius = (size - stroke) / 2, length = 2 * Math.PI * radius;
    const ring = `
      <div class="ring" role="img" aria-label="pie decodes faster in ${wins.length} of ${decode.length} comparisons">
        <svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" aria-hidden="true">
          <circle class="ring-track" cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke-width="${stroke}"/>
          ${share > 0 ? `<circle class="ring-fill" cx="${size / 2}" cy="${size / 2}" r="${radius}" stroke-width="${stroke}"
            stroke-dasharray="${(length * share).toFixed(2)} ${length.toFixed(2)}" transform="rotate(-90 ${size / 2} ${size / 2})"/>` : ""}
        </svg>
        <div class="ring-center">
          <div class="ring-value">${wins.length}<span>/${decode.length}</span></div>
          <div class="ring-caption">pie leads</div>
        </div>
      </div>`;

    const tile = (figure, r, caption) => `
      <div class="stat-tile">
        <div class="stat-value ${r === null ? "is-empty" : tone(r)}">${figure}</div>
        <div class="stat-caption">${caption}</div>
      </div>`;
    const decodeMid = median(decode.map((c) => c.r));
    const prefillMid = median(prefill.map((c) => c.r));
    const best = wins.length ? wins.reduce((a, b) => (b.r > a.r ? b : a)) : null;
    const tiles = [
      tile(decodeMid === null ? "—" : delta(decodeMid), decodeMid, "median decode"),
      tile(prefillMid === null ? "—" : delta(prefillMid), prefillMid, "median prefill"),
      tile(best ? multiple(best.r) : "—", best ? best.r : null,
        best ? `${esc(names().model(best.model))} vs ${esc(names().engine(best.engine))}` : "no decode win yet"),
    ].join("");

    return section("Where we stand", "Decode, one model against one engine",
      `<div class="standing">${ring}<div class="stat-tiles">${tiles}</div></div>`);
  };

  // 2. Against each engine: models down, engines across, pie ÷ engine in every cell
  const HEAT_STEPS = [0.03, 0.15, 0.5]; // |change| thresholds for steps 1, 2, 3
  const heatStep = (r) => {
    const change = Math.abs(r - 1);
    const step = HEAT_STEPS.filter((t) => change >= t).length;
    return step === 0 ? "heat-0" : `heat-${r > 1 ? "p" : "n"}${step}`;
  };

  const heatmap = (byModel, models, metric) => {
    const list = comparisons(byModel, models, metric.key);
    const engineOrder = Pie.store.tables.engines.map((e) => e.id);
    const engines = [...new Set(Object.values(byModel).flat().filter((row) => !isPie(row)).map((row) => row.engine))]
      .sort((a, b) => engineOrder.indexOf(a) - engineOrder.indexOf(b));
    const rowsShown = models.filter((id) => (byModel[id] || []).some(isPie));
    const control = segmented("metric", METRICS, metric.id, "is-small");
    if (!engines.length || !rowsShown.length) return "";

    const cell = 44, gap = 2, n = engines.length;
    const colX = (j) => `${(j * 100) / n}%`;
    const colMid = (j) => `${((j + 0.5) * 100) / n}%`;
    const head = engines.map((engine, j) =>
      `<text class="heat-head" x="${colMid(j)}" y="14" text-anchor="middle">${esc(names().engine(engine))}</text>`).join("");
    const body = rowsShown.map((model, i) => {
      const y = 24 + i * cell;
      return engines.map((engine, j) => {
        const c = list.find((entry) => entry.model === model && entry.engine === engine);
        if (!c) {
          return `<rect class="heat-cell heat-empty" x="${colX(j)}" y="${y}" width="${100 / n}%" height="${cell}" rx="10"
            stroke-width="${gap * 2}" data-tip="${esc(`${names().model(model)} vs ${names().engine(engine)}\nNo data`)}"/>`;
        }
        const stale = c.pie.stale || c.other.stale;
        const tip = [
          `${names().model(model)} vs ${names().engine(engine)}`,
          `${metric.label}: pie ${value(c.pie[metric.key])}, ${names().engine(engine)} ${value(c.other[metric.key])} tok/s`,
          c.other.stale ? `${names().engine(engine)}: ${when(c.other)}` : "",
          c.pie.stale ? `pie: ${when(c.pie)}` : "",
        ].filter(Boolean).join("\n");
        return `<g class="${heatStep(c.r)}${stale ? " is-stale" : ""}" data-tip="${esc(tip)}">
            <rect class="heat-cell" x="${colX(j)}" y="${y}" width="${100 / n}%" height="${cell}" rx="10" stroke-width="${gap * 2}"/>
            <text class="heat-value" x="${colMid(j)}" y="${y + cell / 2 + 5}" text-anchor="middle">${delta(c.r)}</text>
          </g>`;
      }).join("");
    }).join("");
    const labels = rowsShown.map((model) => `<div class="heat-label">${esc(names().model(model))}</div>`).join("");
    const height = 24 + rowsShown.length * cell;

    return section("Against each engine", `pie ÷ engine, ${metric.label.toLowerCase()} tok/s`, `
      <div class="heatmap">
        <div class="heat-labels">${labels}</div>
        <svg class="heat-grid" width="100%" height="${height}" role="img"
          aria-label="pie against each engine, ${metric.label.toLowerCase()}">${head}${body}</svg>
      </div>`, control, "is-narrow");
  };

  // 3. By model: one card per model, a lollipop per engine
  const figure = (rows) => {
    const pie = rows.find((row) => isPie(row) && row.decode_tok_s);
    const others = rows.filter((row) => !isPie(row) && row.decode_tok_s);
    if (!pie || !others.length) {
      return `<div class="figure is-empty">—</div><div class="figure-caption">${pie ? "no other engine yet" : "no pie run yet"}</div>`;
    }
    const best = others.reduce((a, b) => (b.decode_tok_s > a.decode_tok_s ? b : a));
    const r = pie.decode_tok_s / best.decode_tok_s;
    return `<div class="figure ${tone(r)}">${delta(r)}</div>
      <div class="figure-caption">decode vs ${esc(names().engine(best.engine))}, the fastest other</div>`;
  };

  const lollipops = (rows, metric) => {
    const bars = rows.filter((row) => row[metric.key]).sort((a, b) => b[metric.key] - a[metric.key]);
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
      </figure>`;
  };

  const card = (model, rows) => `
    <article class="model-card">
      <h3>${esc(names().model(model))}</h3>
      ${figure(rows)}
      <div class="model-card-charts">${METRICS.map((metric) => lollipops(rows, metric)).join("")}</div>
    </article>`;

  // 4. Across releases: pie's median decode advantage per tag, oldest to newest, up to the picked release
  const releases = (state, models) => {
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
    if (points.length < 2) return "";

    const height = 150, top = 30, bottom = 118;
    const logs = points.map((p) => Math.log(p.r));
    const lo = Math.min(0, ...logs), hi = Math.max(0, ...logs);
    const pad = (hi - lo) * 0.15 || 0.05;
    const y = (r) => bottom - ((Math.log(r) - (lo - pad)) / (hi - lo + 2 * pad)) * (bottom - top);
    const inset = points.length > 1 ? 10 : 50;
    const x = (i) => `${inset + (i * (100 - 2 * inset)) / Math.max(points.length - 1, 1)}%`;
    const parity = y(1);
    const segments = points.slice(1).map((p, i) =>
      `<line class="trend-line" x1="${x(i)}" y1="${y(points[i].r).toFixed(1)}" x2="${x(i + 1)}" y2="${y(p.r).toFixed(1)}"/>`).join("");
    const marks = points.map((p, i) => {
      const tip = `${p.tag}${p.date ? `, ${Pie.format.date(p.date)}` : ""}\nMedian decode ${delta(p.r)} over ${p.n} comparisons`;
      return `<g data-tip="${esc(tip)}">
          <circle class="trend-hit" cx="${x(i)}" cy="${y(p.r).toFixed(1)}" r="14"/>
          <circle class="trend-dot" cx="${x(i)}" cy="${y(p.r).toFixed(1)}" r="5"/>
          <text class="trend-value" x="${x(i)}" y="${(y(p.r) - 13).toFixed(1)}" text-anchor="middle">${delta(p.r)}</text>
          <text class="trend-tag" x="${x(i)}" y="${height - 6}" text-anchor="middle">${esc(p.tag)}</text>
        </g>`;
    }).join("");
    const svg = `
      <svg class="trend" width="100%" height="${height}" role="img" aria-label="pie's median decode advantage by release">
        <line class="trend-parity" x1="0" x2="100%" y1="${parity.toFixed(1)}" y2="${parity.toFixed(1)}"/>
        <text class="trend-axis" x="0" y="${(parity - 5).toFixed(1)}">parity</text>
        ${segments}${marks}
      </svg>`;
    return section("Across releases", "Median decode advantage", svg);
  };

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
      const shown = models.filter((id) => byModel[id]);
      const missing = models.filter((id) => !byModel[id]);
      const metric = METRICS.find((m) => m.id === state.overview.metric);

      const decode = comparisons(byModel, shown, "decode_tok_s");
      const prefill = comparisons(byModel, shown, "prefill_tok_s");
      const stale = shown.some((id) => byModel[id].some((row) => row.stale));
      const notes = [
        stale ? "Lighter marks are from an earlier release." : "",
        missing.length ? `No data yet: ${missing.map((id) => esc(names().model(id))).join(", ")}.` : "",
      ].filter(Boolean);
      const workloadLabel = WORKLOADS.find((w) => w.id === workload).label;

      element.innerHTML = `
        <div class="overview-inner">
          <div class="overview-controls">
            ${popup("overview-mac", "Mac", macName(hardware))}
            ${popup("overview-workload", "Workload", workloadLabel)}
          </div>
          ${decode.length
            ? standing(decode, prefill) + heatmap(byModel, shown, metric)
            : `<div class="overview-none">No pie runs on this Mac yet.</div>`}
          ${shown.length ? section("By model", "", `<div class="model-grid">${shown.map((id) => card(id, byModel[id])).join("")}</div>`) : ""}
          ${releases(state, shown)}
          ${notes.length ? `<p class="overview-footnote">${notes.join(" ")}</p>` : ""}
        </div>`;
      return shown.length;
    },

    onChange(handler) {
      onChange = handler;
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const segment = event.target.closest(".segment");
        if (!segment) return;
        const control = segment.closest("[data-control]").dataset.control;
        state.overview[control] = segment.dataset.value;
        onChange();
      });

      element.addEventListener("click", (event) => {
        const button = event.target.closest("#overview-mac, #overview-workload");
        if (!button) return;
        event.stopPropagation();
        (button.id === "overview-mac" ? onOpenMac : onOpenWorkload)(button);
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
