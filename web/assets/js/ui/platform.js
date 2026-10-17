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
  ];
  // the tabs, one per setup, as a browser keeps its tabs. Decode and prefill are the raw rows (speculation off),
  // held against the hardware limit; every feature after them shows what it adds over the same engine's raw row
  const MODES = [
    { id: "decode", label: "Decode", detail: "single request, speculation off", workload: "raw", metric: METRICS[0], limit: true },
    { id: "prefill", label: "Prefill", detail: "single request, speculation off", workload: "raw", metric: METRICS[1], limit: true },
    { id: "speculation", label: "Speculation", detail: "single request, speculation where the engine has a drafter", workload: "single", metric: METRICS[0] },
    { id: "batching", label: "Batching", detail: "32 requests at once", workload: "throughput", metric: { id: "throughput", label: "Throughput", key: "output_tok_s", unit: "tok/s", higher: true } },
  ];
  let onChange = () => {};

  // the platforms machines belong to, in the order the page lists them; Apple's logo is the simple-icons glyph (CC0)
  const PLATFORMS = [
    { id: "mac", label: "Apple Silicon", sub: "Metal", has: (hw) => hw.class === "mac" || hw.vendor === "Apple" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", has: (hw) => hw.backend === "xla" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", has: (hw) => hw.vendor === "NVIDIA" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", has: (hw) => hw.vendor === "AMD" },
    { id: "cerebras", label: "Cerebras", sub: "Wafer-scale", has: (hw) => hw.vendor === "Cerebras" },
    { id: "android", label: "Android", sub: "Mobile GPU", has: (hw) => hw.class === "android" },
    { id: "web", label: "WebGPU", sub: "In-browser", has: (hw) => hw.class === "web" },
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
  // "48 GB · 20-core GPU · 273 GB/s" on a quiet second line under the chip, the specs that set LLM speed; the CPU waits for the hover
  const specOf = (hw) => {
    // bandwidth is the chip tier's, not something memory and cores give: the M4 Max ships at 410 or 546 GB/s by its bin
    const parts = [hw?.memory_gib && `${hw.memory_gib} GB`, hw?.gpu_cores && `${hw.gpu_cores}-core GPU`, hw?.bandwidth_gbs && `${hw.bandwidth_gbs} GB/s`].filter(Boolean);
    const full = [...parts, hw?.cpu_cores && `${hw.cpu_cores}-core CPU`].filter(Boolean).join(" · ");
    return parts.length ? `<span class="platform-mem" title="${esc(full)}">${parts.join(" · ")}</span>` : "";
  };
  const value = (n, unit) => {
    const v = n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
    return `${v} ${unit}`;
  };
  const EVEN = 0.045;  // under 5%, as the cell rounds it, the engines are even: run-to-run spread, not a result
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

  // each engine's share of the hardware limit, against its own weights (Raw only: a drafter skips the passes the limit counts)
  const share = (r, metric) => {
    const own = Pie.ceiling?.(r, metric.id);
    return own ? r[metric.key] / own.tps : null;
  };
  // what a feature adds: the engine's number over its raw row on the same machine and model
  const overRaw = (r, metric, raw) => {
    const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine);
    const key = metric.id === "throughput" ? "output_tok_s" : metric.key;
    return plain?.[key] ? r[metric.key] / plain[key] : null;
  };
  const times = (x) => `${x >= 10 ? Math.round(x) : x.toFixed(1)}×`;

  // under the comparison, a quiet second line: the share of the hardware limit as a meter, or the gain over raw
  const subline = (c, metric, mode, raw) => {
    if (mode.limit) {
      const own = share(c.pie, metric);
      if (own === null) return "";
      const best = share(c.best, metric);
      const pct = (f) => Math.min(100, Math.round(f * 100));
      const tick = best === null ? "" : `<b style="left: ${pct(best)}%"></b>`;
      return `<span class="platform-sub-line"><span class="limit-meter" aria-hidden="true"><i style="width: ${pct(own)}%"></i>${tick}</span>${Math.round(own * 100)}%</span>`;
    }
    const gain = overRaw(c.pie, metric, raw);
    // a row that did not speculate reads its own raw speed: nothing to add
    return gain === null || Math.abs(gain - 1) < EVEN ? "" : `<span class="platform-sub-line">${times(gain)} raw</span>`;
  };

  // a hover card: the setup as a title, every engine on its own aligned row (fastest first, pie in blue), one closing line
  const card = (title, sub, lines = [], foot = "") => `
    ${title ? `<div class="tip-title">${esc(title)}</div>` : ""}${sub ? `<div class="tip-sub">${esc(sub)}</div>` : ""}
    ${lines.length ? `<div class="tip-rows">${lines.join("")}</div>` : ""}${foot ? `<div class="tip-foot">${esc(foot)}</div>` : ""}`;
  // the day each engine's number was taken, from a release or a manual run alike: "Oct 13"
  const day = (r) => {
    const when = r.measured || r.stale?.measured || "";
    if (!when) return "";
    const [y, m, d] = when.slice(0, 10).split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  };
  const tip = (mac, model, metric, c, mode, raw) => {
    const limit = mode.limit;
    const ceiling = limit ? Pie.ceiling?.(c.pie, metric.id) : null;
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    const lines = order.map((r, i) => {
      // Raw: each engine's share of the hardware limit; the others: what the feature adds over its raw row
      const extra = limit ? share(r, metric) : overRaw(r, metric, raw);
      const note = extra === null ? "" : limit ? `${Math.round(extra * 100)}%` : times(extra);
      return `<div class="tip-row${r === c.pie ? " is-pie" : ""}">
      <span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}${i === 0 ? '<span class="tip-tag">Fastest</span>' : ""}</span>
      <span class="tip-value">${esc(value(r[metric.key], metric.unit))}${note ? `<span class="tip-share">${note}</span>` : ""}</span><span class="tip-when">${esc(day(r))}</span></div>`;
    });
    // the cell's row and column already name the setup, and the bar above the metric: the card is only the engines
    const foot = ceiling ? `Hardware limit ${value(ceiling.tps, metric.unit)}, ${ceiling.bound === "balanced" ? "bandwidth and compute balanced" : `${ceiling.bound}-bound`}, from the spec sheet.` : "";
    return card("", "", lines, foot);
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
      const all = Pie.store.snapshot(state.release);
      // Raw first once it has rows; until then the page opens on Speculation, the single request as measured so far
      if (!MODES.some((m) => m.id === state.platform.mode)) state.platform.mode = all.some((r) => r.workload === "raw" && Pie.store.isMeasured(r)) ? "decode" : "speculation";
      const mode = MODES.find((m) => m.id === state.platform.mode);
      const metric = mode.metric;
      const base = Pie.engines.primary;
      const snapshot = all.filter((r) => r.workload === mode.workload);
      const raw = all.filter((r) => r.workload === "raw" && Pie.store.isMeasured(r));
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
      // grouped by maker, makers and models each in alphabetical order
      const byName = (a, b) => a.localeCompare(b, undefined, { sensitivity: "base", numeric: true });
      const allModels = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id))
        .filter((id) => !query || names().model(id).toLowerCase().includes(query))
        .sort((a, b) => byName(makerOf(a).name || "~", makerOf(b).name || "~") || byName(names().model(a), names().model(b)));
      const grid = {};
      for (const mac of macs) {
        grid[mac] = {};
        for (const model of allModels) {
          const c = cell(rows.filter((r) => r.hardware === mac && r.model === model), metric, base);
          const needs = noFit[mac]?.[model]?.[base];
          const own = snapshot.find((r) => r.hardware === mac && r.model === model && r.engine === base);
          grid[mac][model] = { c, needs, why: needs ? `Doesn't fit: needs about ${Math.round(needs)} GB` : own?.note || (mode.workload === "raw" ? "No raw run yet" : "No data yet") };
        }
      }
      // Hide unavailable drops the models and machines with nothing to compare, as the results table does
      const hide = state.hideEmpty;
      const models = hide ? allModels.filter((model) => macs.some((mac) => grid[mac][model].c)) : allModels;
      const median = (list) => {
        const sorted = list.filter((g) => g !== undefined && g !== null).sort((a, b) => a - b);
        return sorted.length ? sorted[sorted.length >> 1] : null;
      };
      const overall = (mac) => median(models.map((model) => grid[mac][model].c?.gain));
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
        // an even cell still says its number, in grey: within the spread, but not hidden
        if (kind === "is-even") return { kind, html: Math.round(gain * 100) ? signed(gain) : "0%" };
        return { kind, html: `${ARROW(kind === "is-ahead")}${signed(gain).replace(/^[+−]/, "")}` };
      };
      const machine = (mac, platform) => {
        const hw = Pie.store.index.hardware[mac];
        return `<th class="platform-row" scope="row"><span class="platform-chip"><span>${esc(chipName(mac))}</span>${specOf(hw)}</span></th>`;
      };
      // a platform heads its machines with a row across the table, as Finder heads a group
      const folded = (id) => Boolean(p.collapsed?.[id]);
      const groupRow = (g) => `<tr class="platform-group-row${folded(g.platform.id) ? " is-collapsed" : ""}${g.macs.length ? "" : " is-empty"}"${g.macs.length ? ` data-group="${g.platform.id}"` : ""} aria-expanded="${!folded(g.platform.id)}"><th colspan="${models.length + 3}" scope="rowgroup">
        <span class="platform-group-bar">
          <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${esc(g.platform.sub)} · ${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}</span></span>
          <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
        </span></th></tr>`;
      const body = shownGroups.map((g) => groupRow(g) + (folded(g.platform.id) ? [] : g.macs).map((mac, i) => {
        const o = overall(mac);
        const overallCell = o === null ? `<td class="is-overall"><span class="platform-cell is-empty">–</span></td>`
          : (() => { const n = number(o); n.html = Math.round(o * 100) ? signed(o) : "0%"; return `<td class="is-overall"><span class="platform-cell ${n.kind}" data-tip="${esc(card(macName(mac), Math.abs(o) < EVEN ? "On par with the next best" : `${Math.abs(Math.round(o * 100))}% ${o > 0 ? "faster" : "slower"} than the next best`))}">${n.html}</span></td>`; })();
        return `<tr>${machine(mac, g.platform)}${overallCell}${models.map((model) => {
          const { c, needs, why } = grid[mac][model];
          const sorted = sortKey === model ? " is-sorted" : "";
          if (c) {
            cells.push(c.gain);
            const n = number(c.gain);
            return `<td class="${sorted}"><span class="platform-cell ${n.kind}" data-tip="${esc(tip(mac, model, metric, c, mode, raw))}"><span class="platform-main">${n.html}</span>${subline(c, metric, mode, raw)}</span></td>`;
          }
          return `<td class="${sorted}"><span class="platform-cell is-empty${needs ? " is-nofit" : ""}" data-tip="${esc(card("", "", [], why))}">${needs ? NOFIT : "–"}</span></td>`;
        }).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
      }).join("")).join("");

      const arrow = (key) => (sortKey === key ? `<span class="column-sort">${dir > 0 ? "↑" : "↓"}</span>` : "");
      // a maker heads its models with a band across them, as a platform heads its machines down the side
      const makers = [];
      for (const model of models) {
        const maker = makerOf(model);
        if (makers.length && makers[makers.length - 1].maker.name === maker.name) makers[makers.length - 1].n += 1;
        else makers.push({ maker, n: 1 });
      }
      const makerRow = `<tr class="platform-maker-row"><th class="platform-corner" aria-hidden="true"></th><th class="platform-corner is-overall" aria-hidden="true"></th>${makers.map(({ maker, n }) =>
        `<th class="platform-maker" colspan="${n}" scope="colgroup"><span class="platform-maker-name">${badge(maker)}<b>${esc(maker.name || "Other")}</b><span>${n} ${n === 1 ? "model" : "models"}</span></span></th>`).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      const head = `<tr class="platform-head-row">
        <th class="platform-corner is-sortable" scope="col" data-sort="name">Hardware${arrow("name")}</th>
        <th class="platform-corner is-sortable is-overall" scope="col" data-sort="overall"><span class="platform-model">Overall${arrow("overall")}</span><span class="platform-sub">Median</span></th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B active` : ""}` : "";
        const sub = size;
        return `<th class="is-sortable${sortKey === model ? " is-sorted" : ""}" scope="col" data-sort="${esc(model)}" title="Sort by ${esc(names().model(model))}">
          <span class="platform-col"><span><span class="platform-model">${esc(names().model(model))}${arrow(model)}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      // the columns keep their width; a last empty column takes what is left, so rows and bars reach the edge as in Finder
      const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;

      element.innerHTML = `
        <div class="platform-bar">
          <span class="platform-bar-side is-end">
            <button type="button" class="plain-button platform-hide${hide ? " is-active" : ""}" data-hide aria-pressed="${hide}">Hide unavailable</button>
          </span>
        </div>
        <div class="platform-tabs" role="tablist" aria-label="Setup">${MODES.map((m) =>
          `<button type="button" role="tab" class="platform-tab${m === mode ? " is-active" : ""}" data-mode="${m.id}" aria-selected="${m === mode}" title="${esc(`${m.metric.label}: ${m.detail}`)}">${m.label}</button>`).join("")}</div>
        <div class="platform-scroll">
          <table class="platform-table" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>
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
        const tab = event.target.closest("[data-mode]");
        if (tab) {
          state.platform.mode = tab.dataset.mode;
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
      // a tap on a cell shows its card, as hovering does with a pointer
      element.addEventListener("click", (event) => {
        const mark = Pie.tapCard.isTouch() && event.target.closest("[data-tip]");
        if (mark) Pie.tapCard.toggle(mark, mark.dataset.tip, true);
      });
      element.addEventListener("pointermove", (event) => {
        if (event.pointerType !== "mouse") return;
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
      element.addEventListener("pointerleave", (event) => {
        if (event.pointerType !== "mouse") return;
        tooltip.hidden = true;
        tooltip.classList.remove("is-card");
      });
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
