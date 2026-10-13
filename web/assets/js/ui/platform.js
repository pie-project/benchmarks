window.Pie = window.Pie || {};

// A platform page: its machines down, the suite's models across, each cell the picked engine against the
// fastest other engine on that machine (single request). Hovering a cell lists every engine's number.
(() => {
  const element = document.getElementById("platform");
  const tooltip = document.getElementById("chart-tooltip");
  const esc = (s) => Pie.format.escape(String(s ?? ""));
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Decode", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Prefill", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "ttft", label: "TTFT", key: "ttft_ms_p50", unit: "ms", higher: false },
  ];
  let onChange = () => {};

  // the platforms machines belong to, in the order the page lists them; Apple's logo is the simple-icons glyph (CC0)
  const APPLE = '<svg class="platform-logo" viewBox="0 0 24 24" aria-hidden="true"><path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg>';
  const PLATFORMS = [
    { id: "mac", label: "Apple", sub: "Mac", icon: APPLE, has: (hw) => hw.class === "mac" || hw.vendor === "Apple" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", icon: "", has: (hw) => hw.backend === "xla" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", icon: "", has: (hw) => hw.vendor === "NVIDIA" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", icon: "", has: (hw) => hw.vendor === "AMD" },
    { id: "android", label: "Android", sub: "Mobile GPU", icon: "", has: (hw) => hw.class === "android" },
    { id: "web", label: "Web", sub: "In-browser", icon: "", has: (hw) => hw.class === "web" },
  ];
  const platformOf = (hw) => PLATFORMS.find((p) => p.has(hw));

  // a model's maker as a small app-icon badge: a monogram on the maker's tint, no borrowed logos
  const MAKERS = [
    { test: /^qwen/, name: "Alibaba", mark: "Q", tint: ["#7b61ff", "#5b3fe6"] },
    { test: /^gemma/, name: "Google", mark: "G", tint: ["#4f8bff", "#2563eb"] },
    { test: /^gpt_oss/, name: "OpenAI", mark: "O", tint: ["#636366", "#3a3a3c"] },
    { test: /^muse/, name: "Meta", mark: "M", tint: ["#2f8cff", "#0866ff"] },
  ];
  const makerOf = (model) => MAKERS.find((m) => m.test.test(Pie.store.index.models[model]?.family || "")) || { name: "", mark: "•", tint: ["#8e8e93", "#636366"] };
  const badge = (maker) => `<span class="model-badge" style="--from: ${maker.tint[0]}; --to: ${maker.tint[1]}" aria-hidden="true">${maker.mark}</span>`;

  const chipName = (id) => String(Pie.store.index.hardware[id]?.name || id).replace(/^Apple\s+/, "");
  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    return hw ? `${chipName(id)}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}` : id;
  };
  const value = (n, unit) => {
    const v = n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
    return `${v} ${unit}`;
  };
  const EVEN = 0.02;  // within ±2% the engines are even: noise, not a result
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/><path d="M3.8 12.2 12.2 3.8"/></svg>';
  const ARROW = (up) => `<svg class="platform-arrow" viewBox="0 0 10 12" aria-hidden="true"><path d="${up ? "M5 10.5V1.8M1.6 5.2 5 1.8l3.4 3.4" : "M5 1.5v8.7M1.6 6.8 5 10.2l3.4-3.4"}"/></svg>`;
  const signed = (p) => {
    const pct = Math.round(p * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  // pie's advantage over the best other engine: a speed ratio, or the inverse for a time
  const cell = (rows, metric, base) => {
    const pie = rows.find((r) => r.engine === base && r[metric.key]);
    const others = rows.filter((r) => r.engine !== base && r[metric.key]);
    if (!pie || !others.length) return null;
    const best = others.reduce((a, b) => ((metric.higher ? b[metric.key] > a[metric.key] : b[metric.key] < a[metric.key]) ? b : a));
    const gain = metric.higher ? pie[metric.key] / best[metric.key] - 1 : best[metric.key] / pie[metric.key] - 1;
    return { pie, best, gain, all: [pie, ...others] };
  };

  const tip = (mac, model, metric, c) => {
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    return [`${names().model(model)} on ${macName(mac)}`, `${metric.label}, single request`,
      ...order.map((r) => `${names().engine(r.engine)}  ${value(r[metric.key], metric.unit)}${r === c.best ? "  (fastest other)" : ""}`)].join("\n");
  };

  Pie.platform = {
    element,

    // how many machines a platform has on the site (all platforms when none is named)
    machines(id) {
      return Pie.store.tables.hardware.filter((hw) => { const p = platformOf(hw); return p && (!id || p.id === id); }).length;
    },

    onChange(handler) {
      onChange = handler;
    },

    // returns the number of machines and models shown, for the toolbar subtitle
    render(state) {
      const metric = METRICS.find((m) => m.id === state.platform.metric) || METRICS[0];
      const base = Pie.engines.primary;
      const snapshot = Pie.store.snapshot(state.release).filter((r) => r.workload === "single");
      const rows = snapshot.filter(Pie.store.isMeasured);
      // a platform's own page lists its machines; All hardware lists every platform's, grouped
      const only = Pie.schema[state.table]?.platform;
      const groups = PLATFORMS.filter((p) => !only || p.id === only)
        .map((p) => ({ platform: p, macs: Pie.store.tables.hardware.filter((hw) => platformOf(hw) === p).map((hw) => hw.id) }))
        .filter((g) => g.macs.length);
      const macs = groups.flatMap((g) => g.macs);
      const grouped = !only;
      if (!macs.length) {
        const label = Pie.schema[state.table]?.label || "this platform";
        element.innerHTML = `<div class="platform-empty"><span class="sidebar-glyph" style="--tint: ${Pie.schema[state.table]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(state.table)}</span>
          <h2>No ${esc(label)} results yet</h2><p>Machines on this platform will appear here once they are measured.</p></div>`;
        return { macs: 0, models: 0, metric };
      }
      const query = state.query.trim().toLowerCase();
      const models = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id))
        .filter((id) => !query || names().model(id).toLowerCase().includes(query));
      const noFit = Pie.store.tables.no_fit || {};

      const cells = [];
      const machine = (mac, platform) => {
        const hw = Pie.store.index.hardware[mac];
        return `<th class="platform-row" scope="row">${platform.icon}<span>${esc(chipName(mac))}</span>${hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : ""}</th>`;
      };
      const groupCell = (g) => `<th class="platform-group" scope="rowgroup" rowspan="${g.macs.length}">
        <span class="platform-group-name">${g.platform.icon}${esc(g.platform.label)}</span><span class="platform-group-sub">${esc(g.platform.sub)}</span></th>`;
      const body = groups.map((g) => g.macs.map((mac, i) => `<tr${i === 0 ? ' class="is-group-start"' : ""}>${grouped && i === 0 ? groupCell(g) : ""}${machine(mac, g.platform)}${models.map((model) => {
        const here = rows.filter((r) => r.hardware === mac && r.model === model);
        const c = cell(here, metric, base);
        if (c) {
          cells.push(c.gain);
          const kind = Math.abs(c.gain) < EVEN ? "is-even" : c.gain > 0 ? "is-ahead" : "is-behind";
          const mark = kind === "is-even" ? "<i>≈</i>" : ARROW(kind === "is-ahead");
          const text = kind === "is-even" ? "0%" : signed(c.gain).replace(/^[+−]/, "");
          return `<td><span class="platform-cell ${kind}" data-tip="${esc(tip(mac, model, metric, c))}">${mark}${text}</span></td>`;
        }
        const needs = noFit[mac]?.[model]?.[base];
        // why there is nothing: too big, or the reason the results table gives for pie's row
        const own = snapshot.find((r) => r.hardware === mac && r.model === model && r.engine === base);
        const why = needs ? `Doesn't fit: needs about ${Math.round(needs)} GB` : own?.note || "No data yet";
        return `<td><span class="platform-cell is-empty${needs ? " is-nofit" : ""}" data-tip="${esc(`${names().model(model)} on ${macName(mac)}\n${why}`)}">${needs ? NOFIT : "–"}</span></td>`;
      }).join("")}</tr>`).join("")).join("");

      const ahead = cells.filter((g) => g >= 0).length;
      const sorted = [...cells].sort((a, b) => a - b);
      const median = sorted.length ? sorted[sorted.length >> 1] : null;
      const head = `<tr>${grouped ? '<th class="platform-corner platform-group-head" scope="col">Platform</th>' : ""}<th class="platform-corner${grouped ? " is-second" : ""}" scope="col">Hardware</th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const maker = makerOf(model);
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B active` : ""}` : "";
        const sub = [maker.name, size].filter(Boolean).join(" · ");
        return `<th scope="col"><span class="platform-col">${badge(maker)}<span><span class="platform-model">${esc(names().model(model))}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}</tr>`;

      element.innerHTML = `
        <div class="platform-bar">
          <div class="view-toggle" role="group" aria-label="Metric">
            ${METRICS.map((m) => `<button type="button" class="${m === metric ? "is-active" : ""}" data-metric="${m.id}" aria-pressed="${m === metric}">${m.label}</button>`).join("")}
          </div>
          <span class="platform-key is-ahead">${ARROW(true)}${esc(names().engine(base))} faster</span>
          <span class="platform-key is-behind">${ARROW(false)}${esc(names().engine(base))} slower</span>
          <span class="platform-key"><i>≈</i>Within 2%</span>
          <span class="platform-key">${NOFIT}Doesn't fit</span>
          <span class="platform-summary">${cells.length ? `${esc(names().engine(base))} ahead in <b>${ahead}</b> of ${cells.length} · median <b>${signed(median)}</b>` : ""}</span>
        </div>
        <div class="platform-scroll">
          <table class="platform-table${grouped ? " is-grouped" : ""}"><thead>${head}</thead><tbody>${body}</tbody></table>
        </div>`;
      return { macs: macs.length, models: models.length, metric };
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const button = event.target.closest("[data-metric]");
        if (!button) return;
        state.platform.metric = button.dataset.metric;
        onChange();
      });
      element.addEventListener("pointermove", (event) => {
        const mark = event.target.closest("[data-tip]");
        if (!mark) {
          tooltip.hidden = true;
          return;
        }
        tooltip.textContent = mark.dataset.tip;
        tooltip.hidden = false;
        const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      });
      element.addEventListener("pointerleave", () => (tooltip.hidden = true));
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
