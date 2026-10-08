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
  let onOpenMac = () => {};

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

  // pie against the fastest other engine: a wide gap as a multiple (1.6×), a near one as a percentage (+4%, −21%)
  const delta = (r) => {
    if (r >= 1.1 || r <= 0.5) return `${r >= 10 ? Math.round(r) : r.toFixed(1)}×`;
    const pct = Math.round((r - 1) * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  const segmented = (name, items, selected) => `
    <div class="segmented" role="radiogroup" data-control="${name}">
      ${items.map((item) => `
        <button class="segment${item.id === selected ? " is-selected" : ""}" type="button" role="radio"
          aria-checked="${item.id === selected}" data-value="${esc(item.id)}">${esc(item.label)}</button>`).join("")}
    </div>`;

  // the Mac pop-up button: the same control as the release picker at the top right
  const macButton = (hardware) => `
    <button class="release-picker overview-mac" id="overview-mac" type="button" aria-haspopup="menu">
      <span class="release-picker-label">Mac</span>
      <span class="release-picker-value">${esc(macName(hardware))}</span>
      <svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>
    </button>`;

  // the card's one number: pie's decode against the fastest other engine
  const figure = (rows) => {
    const pie = rows.find((row) => Pie.engines.isPrimary(row.engine) && row.decode_tok_s);
    const others = rows.filter((row) => !Pie.engines.isPrimary(row.engine) && row.decode_tok_s);
    if (!pie || !others.length) {
      return `<div class="figure is-empty">—</div><div class="figure-caption">${pie ? "no other engine yet" : "no pie run yet"}</div>`;
    }
    const best = others.reduce((a, b) => (b.decode_tok_s > a.decode_tok_s ? b : a));
    const r = pie.decode_tok_s / best.decode_tok_s;
    const tone = r >= 1.005 ? "is-ahead" : r <= 0.995 ? "is-behind" : "";
    return `<div class="figure ${tone}">${delta(r)}</div>
      <div class="figure-caption">decode vs ${esc(names().engine(best.engine))}</div>`;
  };

  const chart = (rows, metric) => {
    const bars = rows.filter((row) => row[metric.key]).sort((a, b) => b[metric.key] - a[metric.key]);
    if (!bars.length) return "";
    const max = bars[0][metric.key];
    return `
      <figure class="bar-chart">
        <figcaption>${metric.label} <span>tok/s</span></figcaption>
        ${bars.map((row) => {
          const tip = [
            names().engine(row.engine),
            `${metric.label}: ${value(row[metric.key])} tok/s`,
            row.version ? `Version ${row.version}` : "",
            row.stale ? `From ${row.stale.tag}, ${Pie.format.date(row.stale.measured)}` : `Measured ${Pie.format.date(row.measured)}`,
          ].filter(Boolean).join("\n");
          const classes = ["bar-row", Pie.engines.isPrimary(row.engine) ? "is-primary" : "", row.stale ? "is-stale" : ""].filter(Boolean).join(" ");
          return `
            <div class="${classes}" data-tip="${esc(tip)}">
              <span class="bar-label">${esc(names().engine(row.engine))}</span>
              <span class="bar-track"><span class="bar" style="--share: ${Math.max(row[metric.key] / max, 0.01).toFixed(4)}"></span></span>
              <span class="bar-value">${value(row[metric.key])}</span>
            </div>`;
        }).join("")}
      </figure>`;
  };

  const card = (model, rows) => `
    <article class="model-card">
      <h2>${esc(names().model(model))}</h2>
      ${figure(rows)}
      <div class="model-card-charts">${METRICS.map((metric) => chart(rows, metric)).join("")}</div>
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

    onOpenMac(handler) {
      onOpenMac = handler;
    },

    // keep the hardware and workload choice valid for the selected release
    settle(state) {
      const macs = macsIn(Pie.store.snapshot(state.release));
      if (!macs.some((mac) => mac.id === state.overview.hardware)) {
        state.overview.hardware = macs.reduce((a, b) => (b.count > a.count ? b : a), macs[0] || { id: null }).id;
      }
      if (!WORKLOADS.some((w) => w.id === state.overview.workload)) state.overview.workload = "single";
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
      const stale = shown.some((id) => byModel[id].some((row) => row.stale));
      const notes = [
        stale ? "Lighter bars are from an earlier release." : "",
        missing.length ? `No data yet: ${missing.map((id) => esc(names().model(id))).join(", ")}.` : "",
      ].filter(Boolean);

      element.innerHTML = `
        <div class="overview-inner">
          <div class="overview-controls">
            ${macButton(hardware)}
            ${segmented("workload", WORKLOADS, workload)}
          </div>
          <div class="overview-stat">
            <div class="overview-stat-value">${total ? `${lead} of ${total}` : "—"}</div>
            <div class="overview-stat-caption">comparisons where pie decodes faster</div>
          </div>
          <div class="model-grid">${shown.map((id) => card(id, byModel[id])).join("")}</div>
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
        const button = event.target.closest("#overview-mac");
        if (!button) return;
        event.stopPropagation();
        onOpenMac(button);
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
