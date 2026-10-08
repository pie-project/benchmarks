window.Pie = window.Pie || {};

// The overview: for one Mac and one workload, how pie compares with every other engine, model by model.
(() => {
  const element = document.getElementById("overview");
  const tooltip = document.getElementById("chart-tooltip");
  const WORKLOADS = [
    { id: "single", label: "Single request" },
    { id: "throughput", label: "Throughput" },
  ];
  const METRICS = [
    { key: "decode_tok_s", label: "Decode" },
    { key: "prefill_tok_s", label: "Prefill" },
  ];
  let onChange = () => {};

  const esc = (value) => Pie.format.escape(value);
  const names = () => Pie.store.names;

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

  // near parity reads better as a percentage (4% faster), a wide gap as a multiple (2.3× faster)
  const faster = (r) => (r < 1.1 ? `${Math.round((r - 1) * 100)}% faster` : `${r >= 10 ? Math.round(r) : r.toFixed(1)}× faster`);
  const slower = (r) => (r > 0.5 ? `${Math.round((1 - r) * 100)}% slower` : `${(1 / r).toFixed(1)}× slower`);

  const segmented = (name, items, selected) => `
    <div class="segmented" role="radiogroup" data-control="${name}">
      ${items.map((item) => `
        <button class="segment${item.id === selected ? " is-selected" : ""}" type="button" role="radio"
          aria-checked="${item.id === selected}" data-value="${esc(item.id)}">${esc(item.label)}</button>`).join("")}
    </div>`;

  // pie's decode against the fastest other engine on the same model, Mac and workload
  const headline = (rows) => {
    const pie = rows.find((row) => Pie.engines.isPrimary(row.engine) && row.decode_tok_s);
    const others = rows.filter((row) => !Pie.engines.isPrimary(row.engine) && row.decode_tok_s);
    if (!pie && !others.length) return "";
    if (!pie) return `<span class="overview-headline-muted">No pie run on this Mac yet.</span>`;
    if (!others.length) return `<span class="overview-headline-muted">No other engine measured here yet.</span>`;
    const best = others.reduce((a, b) => (b.decode_tok_s > a.decode_tok_s ? b : a));
    const r = pie.decode_tok_s / best.decode_tok_s;
    const rival = esc(names().engine(best.engine));
    if (r >= 1.005) return `pie decodes <strong class="is-ahead">${faster(r)}</strong> than ${rival}, the fastest other engine.`;
    if (r > 0.995) return `pie decodes <strong>as fast as</strong> ${rival}, the fastest other engine.`;
    return `pie decodes <strong class="is-behind">${slower(r)}</strong> than ${rival}, the fastest other engine.`;
  };

  const chart = (rows, metric) => {
    const bars = rows
      .filter((row) => row[metric.key])
      .sort((a, b) => b[metric.key] - a[metric.key]);
    if (!bars.length) return "";
    const max = bars[0][metric.key];
    return `
      <figure class="bar-chart">
        <figcaption><span>${metric.label}</span><span class="bar-chart-unit">tok/s</span></figcaption>
        ${bars.map((row) => {
          const primary = Pie.engines.isPrimary(row.engine);
          const share = Math.max(row[metric.key] / max, 0.004);
          const tip = [
            names().engine(row.engine),
            `${metric.label}: ${value(row[metric.key])} tok/s`,
            row.version ? `Version: ${row.version}` : "",
            row.stale ? `From ${row.stale.tag}, ${Pie.format.date(row.stale.measured)}` : `Measured ${Pie.format.date(row.measured)}`,
          ].filter(Boolean).join("\n");
          return `
            <div class="bar-row${primary ? " is-primary" : ""}${row.stale ? " is-stale" : ""}" data-tip="${esc(tip)}">
              <span class="bar-label">${esc(names().engine(row.engine))}</span>
              <span class="bar-track">
                <span class="bar" style="--share: ${share.toFixed(4)}"></span>
                <span class="bar-value">${value(row[metric.key])}</span>
              </span>
            </div>`;
        }).join("")}
      </figure>`;
  };

  // one quiet line instead of a tag on every bar: which lighter bars come from which earlier release
  const staleNote = (rows) => {
    const tags = [...new Set(rows.filter((row) => row.stale).map((row) => row.stale.tag))];
    if (!tags.length) return "";
    const all = rows.every((row) => row.stale);
    return `<p class="model-card-note">${all ? "All bars are" : "Lighter bars are"} from ${tags.map(esc).join(", ")}, the newest earlier run.</p>`;
  };

  const card = (model, rows) => `
    <article class="model-card">
      <header class="model-card-head">
        <h2>${esc(names().model(model))}</h2>
        <span class="model-card-meta">${rows.length} ${rows.length === 1 ? "engine" : "engines"}</span>
      </header>
      <p class="overview-headline">${headline(rows)}</p>
      <div class="model-card-charts">${METRICS.map((metric) => chart(rows, metric)).join("")}</div>
      ${staleNote(rows)}
    </article>`;

  // on a phone six Macs don't fit a segmented control: a pop-up menu, as iOS does
  const popup = (name, items, selected) => `
    <label class="overview-popup">
      <select data-control="${name}" aria-label="Mac">
        ${items.map((item) => `<option value="${esc(item.id)}"${item.id === selected ? " selected" : ""}>${esc(item.label)}</option>`).join("")}
      </select>
      <svg viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>
    </label>`;

  // macs with any row in this release, most rows first
  const macsIn = (rows) => {
    const counts = {};
    for (const row of rows) counts[row.hardware] = (counts[row.hardware] || 0) + 1;
    const order = Pie.store.tables.hardware.map((hw) => hw.id);
    return Object.keys(counts).sort((a, b) => order.indexOf(a) - order.indexOf(b)).map((id) => ({ id, count: counts[id] }));
  };

  Pie.overview = {
    element,

    // keep the hardware and workload choice valid for the selected release
    settle(state) {
      const macs = macsIn(Pie.store.snapshot(state.release));
      if (!macs.some((mac) => mac.id === state.overview.hardware)) {
        state.overview.hardware = macs.reduce((a, b) => (b.count > a.count ? b : a), macs[0] || { id: null }).id;
      }
      if (!WORKLOADS.some((w) => w.id === state.overview.workload)) state.overview.workload = "single";
    },

    // models shown, for the toolbar subtitle
    render(state) {
      this.settle(state);
      const all = Pie.store.snapshot(state.release);
      const macs = macsIn(all);
      const { hardware, workload } = state.overview;
      if (!macs.length) {
        element.innerHTML = `<div class="overview-empty">No results for this release yet.</div>`;
        return 0;
      }
      const query = state.query.trim().toLowerCase();
      const rows = all.filter((row) => row.hardware === hardware && row.workload === workload);
      const byModel = {};
      for (const row of rows) (byModel[row.model] ||= []).push(row);
      const models = Pie.store.tables.models
        .map((model) => model.id)
        .filter((id) => !query || names().model(id).toLowerCase().includes(query) || id.includes(query));
      const shown = models.filter((id) => byModel[id]);
      const missing = models.filter((id) => !byModel[id]);

      // pie against each other engine, model by model: who decodes faster
      let lead = 0, total = 0;
      for (const id of shown) {
        const pie = byModel[id].find((row) => Pie.engines.isPrimary(row.engine) && row.decode_tok_s);
        if (!pie) continue;
        for (const row of byModel[id]) {
          if (Pie.engines.isPrimary(row.engine) || !row.decode_tok_s) continue;
          total += 1;
          if (pie.decode_tok_s > row.decode_tok_s) lead += 1;
        }
      }
      const workloadLabel = WORKLOADS.find((w) => w.id === workload).label.toLowerCase();
      const summary = total
        ? `pie decodes faster in <strong>${lead} of ${total}</strong> comparisons on the ${esc(macName(hardware))}, ${workloadLabel}.`
        : `No pie and competitor pair measured on the ${esc(macName(hardware))} yet.`;

      element.innerHTML = `
        <div class="overview-inner">
          <div class="overview-controls">
            ${segmented("hardware", macs.map((mac) => ({ id: mac.id, label: macName(mac.id) })), hardware)}
            ${popup("hardware", macs.map((mac) => ({ id: mac.id, label: macName(mac.id) })), hardware)}
            ${segmented("workload", WORKLOADS, workload)}
          </div>
          <div class="overview-summary">
            <p>${summary}</p>
            <div class="overview-legend" aria-hidden="true">
              <span><i class="swatch is-primary"></i>pie</span>
              <span><i class="swatch"></i>Other engines</span>
              <span><i class="swatch is-stale"></i>From an earlier release</span>
            </div>
          </div>
          <div class="model-grid">${shown.map((id) => card(id, byModel[id])).join("")}</div>
          ${missing.length ? `<p class="overview-missing">No data on this Mac yet: ${missing.map((id) => esc(names().model(id))).join(", ")}</p>` : ""}
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

      element.addEventListener("change", (event) => {
        const select = event.target.closest("select[data-control]");
        if (!select) return;
        state.overview[select.dataset.control] = select.value;
        onChange();
      });

      // one tooltip for every bar: engine, value, version and when it was measured
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
