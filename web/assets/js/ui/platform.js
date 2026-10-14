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
    { id: "ttft", label: "TTFT", detail: "Time to the first token", key: "ttft_ms_p50", unit: "ms", higher: false },
  ];
  let onChange = () => {};

  // the platforms machines belong to, in the order the page lists them; Apple's logo is the simple-icons glyph (CC0)
  const PLATFORMS = [
    { id: "mac", label: "Apple", sub: "Mac", has: (hw) => hw.class === "mac" || hw.vendor === "Apple" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", has: (hw) => hw.backend === "xla" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", has: (hw) => hw.vendor === "NVIDIA" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", has: (hw) => hw.vendor === "AMD" },
    { id: "cerebras", label: "Cerebras", sub: "Wafer-scale", has: (hw) => hw.vendor === "Cerebras" },
    { id: "android", label: "Android", sub: "Mobile GPU", has: (hw) => hw.class === "android" },
    { id: "web", label: "Web", sub: "In-browser", has: (hw) => hw.class === "web" },
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

  // a hover card: the setup as a title, every engine on its own aligned row (fastest first, pie in blue), one closing line
  const card = (title, sub, lines = [], foot = "") => `
    <div class="tip-title">${esc(title)}</div>${sub ? `<div class="tip-sub">${esc(sub)}</div>` : ""}
    ${lines.length ? `<div class="tip-rows">${lines.join("")}</div>` : ""}${foot ? `<div class="tip-foot">${esc(foot)}</div>` : ""}`;
  const tip = (mac, model, metric, c) => {
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    const pieName = names().engine(c.pie.engine);
    const foot = Math.abs(c.gain) < EVEN ? `${pieName} and ${names().engine(c.best.engine)} are even.`
      : `${pieName} is ${Math.abs(Math.round(c.gain * 100))}% ${c.gain > 0 ? "faster" : "slower"} than ${names().engine(c.best.engine)}.`;
    const lines = order.map((r, i) => `<div class="tip-row${r === c.pie ? " is-pie" : ""}">
      <span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}${i === 0 ? '<span class="tip-tag">Fastest</span>' : ""}</span>
      <span class="tip-value">${esc(value(r[metric.key], metric.unit))}</span></div>`);
    return card(`${names().model(model)} on ${macName(mac)}`, `${metric.label} · single request`, lines, foot);
  };

  Pie.platform = {
    element,

    // how many machines a platform has on the site (all platforms when none is named)
    machines(id) {
      return Pie.store.tables.hardware.filter((hw) => { const p = platformOf(hw); return p && (!id || p.id === id); }).length;
    },

    metrics() {
      return METRICS;
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
      const allModels = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id))
        .filter((id) => !query || names().model(id).toLowerCase().includes(query));
      const grid = {};
      for (const mac of macs) {
        grid[mac] = {};
        for (const model of allModels) {
          const c = cell(rows.filter((r) => r.hardware === mac && r.model === model), metric, base);
          const needs = noFit[mac]?.[model]?.[base];
          const own = snapshot.find((r) => r.hardware === mac && r.model === model && r.engine === base);
          grid[mac][model] = { c, needs, why: needs ? `Doesn't fit: needs about ${Math.round(needs)} GB` : own?.note || "No data yet" };
        }
      }
      // Hide unavailable drops the models and machines with nothing to compare, as the results table does
      const hide = state.hideEmpty;
      const models = hide ? allModels.filter((model) => macs.some((mac) => grid[mac][model].c)) : allModels;
      const overall = (mac) => {
        const gains = models.map((model) => grid[mac][model].c?.gain).filter((g) => g !== undefined).sort((a, b) => a - b);
        return gains.length ? gains[gains.length >> 1] : null;
      };
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
        .filter((g) => !only || g.macs.length);

      const cells = [];
      const number = (gain) => {
        const kind = Math.abs(gain) < EVEN ? "is-even" : gain > 0 ? "is-ahead" : "is-behind";
        const mark = kind === "is-even" ? "<i>≈</i>" : ARROW(kind === "is-ahead");
        return { kind, html: `${mark}${kind === "is-even" ? "0%" : signed(gain).replace(/^[+−]/, "")}` };
      };
      const machine = (mac, platform) => {
        const hw = Pie.store.index.hardware[mac];
        return `<th class="platform-row" scope="row"><span>${esc(chipName(mac))}</span>${hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : ""}</th>`;
      };
      // a platform heads its machines with a row across the table, as Finder heads a group
      const folded = (id) => Boolean(p.collapsed?.[id]);
      const groupRow = (g) => `<tr class="platform-group-row${folded(g.platform.id) ? " is-collapsed" : ""}${g.macs.length ? "" : " is-empty"}"${g.macs.length ? ` data-group="${g.platform.id}"` : ""} aria-expanded="${!folded(g.platform.id)}"><th colspan="${models.length + 2}" scope="rowgroup">
        <span class="platform-group-bar">
          <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${esc(g.platform.sub)} · ${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}</span></span>
          <svg class="platform-disclosure" viewBox="0 0 10 10" aria-hidden="true"><path d="M3 2l4 3-4 3"/></svg>
        </span></th></tr>`;
      const body = shownGroups.map((g) => groupRow(g) + (folded(g.platform.id) ? [] : g.macs).map((mac, i) => {
        const o = overall(mac);
        const overallCell = o === null ? `<td class="is-overall"><span class="platform-cell is-empty">–</span></td>`
          : (() => { const n = number(o); n.html = n.kind === "is-even" ? "0%" : signed(o); return `<td class="is-overall"><span class="platform-cell ${n.kind}" data-tip="${esc(card(macName(mac), Math.abs(o) < EVEN ? "On par with the next best" : `${Math.abs(Math.round(o * 100))}% ${o > 0 ? "faster" : "slower"} than the next best`))}">${n.html}</span></td>`; })();
        return `<tr>${machine(mac, g.platform)}${overallCell}${models.map((model) => {
          const { c, needs, why } = grid[mac][model];
          const sorted = sortKey === model ? " is-sorted" : "";
          if (c) {
            cells.push(c.gain);
            const n = number(c.gain);
            return `<td class="${sorted}"><span class="platform-cell ${n.kind}" data-tip="${esc(tip(mac, model, metric, c))}">${n.html}</span></td>`;
          }
          return `<td class="${sorted}"><span class="platform-cell is-empty${needs ? " is-nofit" : ""}" data-tip="${esc(card(`${names().model(model)} on ${macName(mac)}`, `${metric.label} · single request`, [], why))}">${needs ? NOFIT : "–"}</span></td>`;
        }).join("")}</tr>`;
      }).join("")).join("");

      const ahead = cells.filter((g) => g >= EVEN).length;
      const sortedGains = [...cells].sort((a, b) => a - b);
      const median = sortedGains.length ? sortedGains[sortedGains.length >> 1] : null;
      const arrow = (key) => (sortKey === key ? `<span class="column-sort">${dir > 0 ? "↑" : "↓"}</span>` : "");
      const head = `<tr>
        <th class="platform-corner is-sortable" scope="col" data-sort="name">Hardware${arrow("name")}</th>
        <th class="platform-corner is-sortable is-overall" scope="col" data-sort="overall"><span class="platform-model">Overall${arrow("overall")}</span><span class="platform-sub">Median</span></th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const maker = makerOf(model);
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B active` : ""}` : "";
        const sub = [maker.name, size].filter(Boolean).join(" · ");
        return `<th class="is-sortable${sortKey === model ? " is-sorted" : ""}" scope="col" data-sort="${esc(model)}" title="Sort by ${esc(names().model(model))}">
          <span class="platform-col">${badge(maker)}<span><span class="platform-model">${esc(names().model(model))}${arrow(model)}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}</tr>`;
      const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}</colgroup>`;

      element.innerHTML = `
        <div class="platform-bar">
          <span class="filter">
            <button class="filter-button" id="platform-metric" type="button" aria-haspopup="menu" title="Metric">${esc(metric.label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
          </span>
          <span class="platform-bar-side is-end">
            <button type="button" class="plain-button platform-hide${hide ? " is-active" : ""}" data-hide aria-pressed="${hide}">Hide unavailable</button>
          </span>
        </div>
        <div class="platform-scroll">
          <table class="platform-table">${cols}<thead>${head}</thead><tbody>${body}</tbody></table>
        </div>
        <div class="platform-status">${cells.length ? `${esc(names().engine(base))} is faster in ${ahead} of ${cells.length} comparisons. Median ${Math.abs(median) < EVEN ? "even" : `${Math.abs(Math.round(median * 100))}% ${median > 0 ? "faster" : "slower"}`}.` : ""}
        </div>`;
      // the header bar spans what is visible, so its chevron sits at the right edge however wide the table is
      const scroller = element.querySelector(".platform-scroll");
      if (scroller) element.style.setProperty("--platform-visible", `${scroller.clientWidth}px`);
      const macsShown = shownGroups.reduce((n, g) => n + g.macs.length, 0);
      return { macs: macsShown, models: models.length, metric };
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const button = event.target.closest("[data-metric]");
        if (button) {
          state.platform.metric = button.dataset.metric;
          onChange();
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
      element.addEventListener("pointermove", (event) => {
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
      element.addEventListener("pointerleave", () => {
        tooltip.hidden = true;
        tooltip.classList.remove("is-card");
      });
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
