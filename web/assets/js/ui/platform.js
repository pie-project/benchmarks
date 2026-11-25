window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("platform");
  const tooltip = document.getElementById("chart-tooltip");
  const esc = (s) => Pie.format.escape(String(s ?? ""));
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Decode", detail: "Tokens per second while answering", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Prefill", detail: "Tokens per second reading the prompt", key: "prefill_tok_s", unit: "tok/s", higher: true },
  ];
  const MODES = [
    { id: "decode", group: "Decode", label: "Decode Latency", title: "Decode Latency", item: "Single", icon: "M2 8h8M7 5l3 3-3 3M13 3v10", detail: "single request, speculation off", workload: "raw", metric: METRICS[0], limit: true },
    { id: "spec", group: "Decode", label: "Spec Decode", item: "Speculative", icon: "M2 8h5M5 5l3 3-3 3M9 8h5M12 5l3 3-3 3", detail: "single request, speculation on", workload: "spec", metric: METRICS[0] },
    { id: "prefill", group: "Prefill", label: "Prefill Latency", title: "Prefill Latency", item: "Single", icon: "M3 4.5h10M3 8h10M3 11.5h6", detail: "single request, speculation off", workload: "raw", metric: METRICS[1], limit: true },
    { id: "batching", group: "Decode", label: "Decode Throughput", title: "Batched Decode Throughput", item: "Batched", icon: "M8 2.5l6 3-6 3-6-3zM2 8.5l6 3 6-3M2 11.5l6 3 6-3", detail: "32 requests at once", workload: "throughput", metric: { id: "throughput", label: "Throughput", key: "output_tok_s", unit: "tok/s", higher: true } },
    { id: "pbatch", group: "Prefill", label: "Prefill Throughput", title: "Batched Prefill Throughput", item: "Batched", icon: "M3 4.5h10M3 8h10M3 11.5h6", detail: "256 cold prompts at once, one token each", workload: "prefill_batch", metric: METRICS[1] },
  ];
  const mark = (x, y) => `<rect x="${x}" y="${y}" width="4.2" height="4.2" rx="1"/>`;
  const AT = [1, 5.9, 10.8];
  const DEGREE = {
    decode: mark(5.9, 5.9),
    spec: mark(3.45, 5.9) + mark(8.35, 5.9),
    prefill: AT.map((x) => mark(x, 5.9)).join(""),
    batching: AT.flatMap((y) => AT.map((x) => mark(x, y))).join(""),
    pbatch: [3.45, 8.35].flatMap((y) => AT.map((x) => mark(x, y))).join(""),
  };
  const longSetupControl = (active, modes) => `<span class="platform-compare" role="group" aria-label="Setup">${modes.map((m, i) =>
    (m.id === "batching" ? `<span class="setup-divider" aria-hidden="true"></span>` : "") +
    (i === 0 && !["batching", "pbatch"].includes(active) ? `<span class="setup-group">Latency</span>` : "") +
    (m.id === "batching" && ["batching", "pbatch"].includes(active) ? `<span class="setup-group">Throughput</span>` : "") +
    `<button type="button" class="plain-button${m.id === active ? " is-active" : ""}" data-mode="${m.id}" aria-pressed="${m.id === active}" title="${esc(`${m.title || m.label}, ${m.id === "batching" ? "as many requests at once as the hardware needs to stay busy" : "one request"}`)}"><svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[m.id] || `<path d="${m.icon}"/>`}</svg>${esc(m.id === "spec" ? m.label : m.group)}</button>`).join("")}</span>`;
  const AUTO_MS = 9000;
  const AUTO_ORDER = ["decode", "prefill", "batching", "pbatch"];
  const stillMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const auto = { stopped: true, paused: false, timer: null, started: 0, spent: 0, rolling: false };
  const autoOn = () => !auto.stopped && !stillMotion.matches;
  const setupControl = (active, modes, tabs = false) => {
    const ids = modes.map((m) => m.id);
    if ((ids.includes("spec") && !tabs) || !ids.every((id) => ["decode", "spec", "prefill", "batching", "pbatch"].includes(id))) return longSetupControl(active, modes);
    const NAMES = { decode: "Single Decode", spec: "Speculative Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
    return `<span class="setup-row setup-pick platform-setup" role="group" aria-label="Setup">${ids.map((id) =>
      `<button type="button" class="filter-button setup-tab${id === active ? " is-active" : ""}" data-mode="${id}" aria-pressed="${id === active}" title="${esc(NAMES[id])}, ${["decode", "spec", "prefill"].includes(id) ? "latency" : "throughput"}"><svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[id] || ""}</svg><span>${esc(NAMES[id])}</span></button>`).join("")}</span>`;
  };
  let onChange = () => {};
  const nextTurn = () => {
    clearTimeout(auto.timer);
    const mode = viewState?.platform.mode || "decode";
    if (!autoOn() || auto.paused || document.hidden || element.hidden || !AUTO_ORDER.includes(mode) || !element.querySelector(".setup-pick")) return;
    auto.started = performance.now();
    auto.timer = setTimeout(() => {
      captureGhosts();
      viewState.platform.mode = AUTO_ORDER[(AUTO_ORDER.indexOf(mode) + 1) % AUTO_ORDER.length];
      auto.spent = 0;
      auto.rolling = true;
      onChange();
    }, Math.max(0, AUTO_MS - auto.spent));
  };
  const waveSpan = (tables) => {
    const offset = [];
    let rows = 0, cols = 0;
    for (const table of tables) {
      offset.push(rows);
      const body = [...table.tBodies[0]?.rows || []];
      rows += body.length;
      cols = Math.max(cols, body[0]?.cells.length || 0);
    }
    return { offset, step: Math.min(70, 1800 / Math.max(1, rows + cols)) };
  };
  const WAVE = false;
  const afterDraw = () => {
    if (!WAVE) { auto.rolling = false; auto.ghosts = null; auto.waves = []; }
    const now = performance.now();
    if (auto.rolling) {
      auto.rolling = false;
      auto.waves = auto.waves || [];
      auto.waves.push({ start: now, ghosts: auto.ghosts || [], at: {}, prev: {}, shown: null });
      auto.ghosts = null;
      const pick = element.querySelector(auto.labelOf || ".setup-pick");
      if (pick && auto.label) {
        pick.insertAdjacentHTML("afterbegin", `<span class="label-ghost" aria-hidden="true">${auto.label}</span>`);
        pick.classList.add("is-relabel");
        setTimeout(() => { pick.classList.remove("is-relabel"); pick.querySelector(".label-ghost")?.remove(); }, 1000);
      }
      auto.label = null;
    }
    const waves = auto.waves || [];
    if (waves.length) {
      const newest = waves[waves.length - 1];
      const tables = [...element.querySelectorAll(".platform-table")];
      const { offset, step } = waveSpan(tables);
      tables.forEach((table, t) => {
        const rows = [...table.tBodies[0]?.rows || []];
        rows.forEach((tr, r) => [...tr.cells].forEach((td, c) => {
          const key = `${t}|${r}|${c}`;
          if (!(key in newest.at)) {
            newest.prev[key] = cellAt[key];
            newest.at[key] = cellAt[key] = Math.max(newest.start + Math.round((offset[t] + r + c) * step), cellAt[key] != null ? cellAt[key] + RISE : -Infinity);
          }
          td.style.setProperty("--roll-wait", `${Math.round(newest.at[key] - now)}ms`);
        }));
      });
      waves.forEach((w) => {
        const first = !w.shown;
        if (first) w.shown = new Set();
        tables.forEach((table, t) => [...(table.tBodies[0]?.rows || [])].forEach((tr, r) => [...tr.cells].forEach((td, c) => {
          const key = `${t}|${r}|${c}`;
          const old = w.ghosts[t]?.[r]?.[c];
          const cell = td.querySelector(".platform-cell");
          if (!cell || w.at[key] == null) return;
          carryInto(td, old?.carry, now);
          if (!old?.html) return;
          const rising = w.prev[key] != null && w.prev[key] + RISE > w.start;
          if (first) {
            if (!rising && old.pill && td.classList.contains("is-overall") && cell.outerHTML === old.html) return;
            const main = td.querySelector(".platform-main");
            if (!rising && !old.pill && main?.innerHTML === old.html && look(main).style === old.style) return;
            w.shown.add(key);
          } else if (!w.shown.has(key)) return;
          td.insertAdjacentHTML("beforeend", ghostHtml(old, w.at[key], rising ? w.prev[key] + 320 : null, now));
        })));
      });
      element.classList.add("is-rolling");
      clearTimeout(auto.waveTimer);
      const end = Math.max(...waves.flatMap((w) => Object.values(w.at))) + RISE + 200;
      auto.waveTimer = setTimeout(() => {
        auto.waves = [];
        element.classList.remove("is-rolling");
        element.querySelectorAll(".roll-ghost").forEach((g) => g.remove());
      }, Math.max(0, end - now));
    }
    element.classList.toggle("is-auto-paused", auto.paused);
    nextTurn();
  };
  const pauseTurns = (on) => {
    if (on === auto.paused) return;
    if (on) { clearTimeout(auto.timer); auto.spent += performance.now() - auto.started; }
    auto.paused = on;
    element.classList.toggle("is-auto-paused", on);
    if (!on) nextTurn();
  };
  element.addEventListener("pointermove", (event) => pauseTurns(Boolean(event.target.closest(".platform-scroll, .platform-setup"))));
  element.addEventListener("pointerleave", () => pauseTurns(false));
  document.addEventListener("visibilitychange", () => pauseTurns(document.hidden));
  const LOOK = ["color", "background-color", "padding", "border-radius", "font-weight"];
  const look = (main) => {
    if (!main) return { html: "" };
    const cs = getComputedStyle(main);
    return { html: main.innerHTML, style: `display: inline-block; ${LOOK.map((k) => `${k}: ${cs.getPropertyValue(k)}`).join("; ")}` };
  };
  const captureGhosts = (button = ".setup-pick") => {
    const pick = element.querySelector(button);
    auto.labelOf = button;
    auto.label = pick?.tagName === "BUTTON" ? [...pick.children].filter((el) => !el.classList.contains("popup-chevron")).map((el) => el.outerHTML).join("") : null;
    auto.ghosts = ghostsOf(element);
  };
  const ghostsOf = (root) => [...root.querySelectorAll(".platform-table")].map((t) => [...(t.tBodies[0]?.rows || [])].map((tr) => [...tr.cells].map((td) => {
    const main = td.querySelector(":scope > .platform-cell .platform-main"), cell = td.querySelector(":scope > .platform-cell");
    const carry = [...td.querySelectorAll(":scope > .roll-ghost[data-out]")].filter((g) => +g.dataset.out + 500 > performance.now())
      .map((g) => ({ outer: g.outerHTML, out: +g.dataset.out, in: g.dataset.in ? +g.dataset.in : null }));
    const own = td.classList.contains("is-overall") ? { pill: true, html: cell?.outerHTML || "" }
      : main ? { ...look(main), right: td.getBoundingClientRect().right - main.getBoundingClientRect().right } : { pill: true, html: td.querySelector(".platform-cell.is-empty")?.outerHTML || "" };
    return { ...own, carry };
  })));
  const RISE = 1120;
  const cellAt = {};
  const ghostHtml = (old, outAt, inAt, now) => {
    const timing = `--roll-wait: ${Math.round(outAt - now)}ms;${inAt != null ? ` --in-wait: ${Math.round(inAt - now)}ms;` : ""}`;
    const kind = `roll-ghost${old.pill ? " is-pill" : ""}${inAt != null ? " is-chained" : ""}`;
    const data = `data-out="${Math.round(outAt)}"${inAt != null ? ` data-in="${Math.round(inAt)}"` : ""}`;
    return old.pill ? `<span class="${kind}" aria-hidden="true" ${data} style="${timing}">${old.html}</span>`
      : `<span class="${kind}" aria-hidden="true" ${data} style="${timing} padding: 0 ${old.right ?? 0}px 0 0"><span style="${old.style || ""}">${old.html}</span></span>`;
  };
  const carryInto = (td, carry, now) => {
    for (const g of carry || []) {
      td.insertAdjacentHTML("beforeend", g.outer);
      const el = td.lastElementChild;
      el.style.setProperty("--roll-wait", `${Math.round(g.out - now)}ms`);
      if (g.in != null) el.style.setProperty("--in-wait", `${Math.round(g.in - now)}ms`);
    }
  };
  const stopTurns = () => { auto.spent = 0; clearTimeout(auto.timer); };
  let openResults = () => {};
  let openGap = () => {};

  const PLATFORMS = [
    { id: "mac", label: "Apple Silicon", sub: "Metal", has: (hw) => Pie.platformOf(hw) === "mac" },
    { id: "windows", label: "Windows PC", sub: "CUDA", has: (hw) => Pie.platformOf(hw) === "windows" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", has: (hw) => Pie.platformOf(hw) === "nvidia" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", has: (hw) => Pie.platformOf(hw) === "amd" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", has: (hw) => Pie.platformOf(hw) === "tpu" },
    { id: "cerebras", label: "Cerebras", sub: "CSL", has: (hw) => Pie.platformOf(hw) === "cerebras" },
    { id: "android", label: "Mobile", sub: "Mobile GPU", has: (hw) => Pie.platformOf(hw) === "android" },
    { id: "web", label: "Browser", sub: "WebGPU", has: (hw) => Pie.platformOf(hw) === "web" },
  ].sort((a, b) => Pie.platformOrder.indexOf(a.id) - Pie.platformOrder.indexOf(b.id));
  const platformOf = (hw) => PLATFORMS.find((p) => p.has(hw));
  const hideAfter = new WeakMap();
  document.addEventListener("scroll", (event) => {
    const scroller = event.target;
    if (!scroller.classList?.contains("platform-section-scroll")) return;
    scroller.classList.add("is-scrolling");
    clearTimeout(hideAfter.get(scroller));
    hideAfter.set(scroller, setTimeout(() => scroller.classList.remove("is-scrolling"), 900));
  }, { capture: true, passive: true });
  const stripes = (root) => root.querySelectorAll("td:has(> .platform-cell.is-mini)").forEach((td) => {
    td.style.backgroundPosition = `${-td.offsetLeft}px ${-td.offsetTop}px`;
  });
  const badgeOf = (id) => `<span class="sidebar-glyph" style="--tint: ${Pie.schema[id]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(id)}</span>`;

  const MAKERS = [
    { test: /^qwen/, name: "Alibaba", logo: "qwen" },
    { test: /^gemma/, name: "Google", logo: "gemma" },
    { test: /^gpt_oss/, name: "OpenAI", logo: "openai" },
    { test: /^muse/, name: "Meta", logo: "meta" },
    { test: /^glm/, name: "Z.ai", logo: "zai" },
    { test: /^mimo/, name: "Xiaomi", logo: "xiaomi" },
    { test: /^deepseek/, name: "DeepSeek", logo: "deepseek" },
    { test: /^kimi/, name: "Moonshot", logo: "moonshot" },
    { test: /^hy/, name: "Tencent", logo: "hunyuan" },
    { test: /^minimax/, name: "MiniMax", logo: "minimax" },
    { test: /^nemotron/, name: "NVIDIA", logo: "nvidia" },
  ];
  const makerOf = (model) => { const id = model.split("~")[0]; const family = Pie.store.index.models[id]?.family || id.replace(/-/g, "_"); return MAKERS.find((m) => m.test.test(family)) || { name: "", logo: "" }; };
  const CLOUD = '<svg class="model-cloud" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 12.5a3 3 0 0 1-.4-6A4 4 0 0 1 11.8 6a3.25 3.25 0 0 1 .2 6.5z"/></svg>';
  const badge = (maker) => `<span class="model-badge" aria-hidden="true">${maker.logo ? `<img src="assets/img/models/${maker.logo}.svg" alt="">` : CLOUD}</span>`;

  const chipName = (id) => String(Pie.store.index.hardware[id]?.name || id).replace(/^Apple\s+/, "");
  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    if (!hw) return id;
    const [chip, ...rest] = chipName(id).split(" · ");
    return [`${chip}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}`, ...rest].join(" · ");
  };
  const specOf = (hw) => (hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : "");
  const LINKS = { uma: "Unified memory", nvlink: "NVLink", pcie: "PCIe", tb5: "Thunderbolt 5" };
  const specSheet = (hw) => {
    const rows = [
      ["Memory", hw.memory_gib && `${hw.memory_gib} GB`],
      ["Bandwidth", hw.bandwidth_gbs && `${hw.bandwidth_gbs} GB/s`],
      ["GPU", hw.gpu_cores && `${hw.gpu_cores} cores`],
      ["CPU", hw.cpu_cores && `${hw.cpu_cores} cores`],
      ["Compute", hw.tflops_fp16 && `${hw.tflops_fp16} TFLOPS fp16`],
      ["Neural Engine", hw.ane_tflops_fp16 && `${hw.ane_tflops_fp16} TFLOPS fp16`],
      ["Devices", hw.count > 1 && `${hw.count}`],
      ["Interconnect", hw.interconnect && (LINKS[hw.interconnect] || hw.interconnect)],
      ["Power", hw.power_w && `${hw.power_w} W at full load`],
    ].filter(([, v]) => v);
    return `<div class="tip-title">${esc(hw.name || hw.id)}</div><div class="spec-rows">${rows.map(([k, v]) => `<div class="spec-row"><span>${esc(k)}</span><span>${esc(v)}</span></div>`).join("")}</div>`;
  };
  const value = (n, unit) => {
    const v = n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
    return `${v} ${unit}`;
  };
  const fmtNum = (n) => (n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 }));
  const EVEN = 0.045;
  const TODAY = {
    models: new Set(["deepseek-v4.1-flash", "glm-5.3-flash", "kimi-k3", "glm-5.3", "hy4-preview", "mimo-v2.6-flash-rl", "qwen3.8-flash-next",
      "muse-spark-open-816b-a42b", "nvidia-nemotron-3-ultra-550b-a55b", "minimax-m3.1-flash"]),
    hardware: new Set(["h200-x1", "b200-x1", "pro6000-x1", "a100-sxm-x1", "h100-sxm-x1", "a40-x1", "l40s-x1", "rtx5090-x1", "rtx4090-x1"]),
  };
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>';
  const signed = (p) => {
    const pct = Math.round(p * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  const COMPARES = { engines: "Relative Speed", ceiling: "Kernel Efficiency", tps: "Tokens per Second" };
  const COMPARE_ICONS = { engines: "speedups", ceiling: "all_hardware", tps: "tps" };
  const viewIcon = (id) => `<svg class="view-icon" viewBox="0 0 24 24" aria-hidden="true">${id === "engines" ? '<g transform="scale(1.5)" stroke-width="1.2"><path stroke-linejoin="round" d="M14.15 6.63L14.15 9.37L12.81 8.94L12.06 10.74L13.32 11.38L11.38 13.32L10.74 12.06L8.94 12.81L9.37 14.15L6.63 14.15L7.06 12.81L5.26 12.06L4.62 13.32L2.68 11.38L3.94 10.74L3.19 8.94L1.85 9.37L1.85 6.63L3.19 7.06L3.94 5.26L2.68 4.62L4.62 2.68L5.26 3.94L7.06 3.19L6.63 1.85L9.37 1.85L8.94 3.19L10.74 3.94L11.38 2.68L13.32 4.62L12.06 5.26L12.81 7.06z"/><circle cx="8" cy="8" r="2"/></g>' : id === "tps" ? '<path class="is-filled" fill-rule="evenodd" d="M4.5 2.5h15A2 2 0 0 1 21.5 4.5v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V5.5zM4.5 12.5h15a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V15.5z"/>' : Pie.icons[COMPARE_ICONS[id]]}</svg>`;
  const nextCompare = (id) => { const ids = Object.keys(COMPARES); return ids[(ids.indexOf(id) + 1) % ids.length]; };
  const saved = (() => { try { return localStorage.getItem("platformCompare"); } catch { return null; } })();
  let chosen = COMPARES[saved] ? saved : "engines";
  let compare = chosen;
  const boundOf = (mac, model, mode, metric, pie) => {
    if (mode.limit) return Pie.ceiling?.(pie, metric.id) || null;
    if (mode.id === "spec") return (pie && Pie.specCeiling?.(pie)) || null;
    if (mode.id === "pbatch") return (pie && Pie.ceiling?.(pie, "pbatch")) || null;
    if (mode.workload !== "throughput") return null;
    return batchedBound(mac, model, pie?.scheme, pie?.benchmark, pie);
  };
  function batchedBound(mac, model, scheme, benchmark, row) {
    return Pie.batchedCeiling?.(mac, model, scheme, benchmark, row) || null;
  }
  const cell = (rows, metric, base) => {
    const pie = rows.find((r) => r.engine === base && r[metric.key]);
    const others = rows.filter((r) => r.engine !== base && r[metric.key]);
    if (!pie) return null;
    if (!others.length) return { pie, best: null, gain: null, all: [pie, ...others] };
    const best = others.reduce((a, b) => ((metric.higher ? b[metric.key] > a[metric.key] : b[metric.key] < a[metric.key]) ? b : a));
    const gain = metric.higher ? pie[metric.key] / best[metric.key] - 1 : best[metric.key] / pie[metric.key] - 1;
    return { pie, best, gain, all: [pie, ...others] };
  };
  const overLimitOf = (mac, model, mode, metric, c) => (c.all || [c.pie]).some((r) => {
    if (r.miniature || !r[metric.key]) return false;
    const b = mode.id === "pbatch" ? Pie.ceiling?.(r, "pbatch") : boundOf(mac, model, mode, metric, r);
    return b?.tps && r[metric.key] > b.tps;
  });
  const apart = (c) => c?.gain != null && c.pie.engine === Pie.engines.primary && Math.round(c.gain * 100) >= 25;
  const pairOf = (c, metric) => {
    const k = metric.key, up = metric.higher !== false, top = new Map();
    for (const r of c?.all || []) if (r[k] > 0 && (!top.has(r.engine) || (up ? r[k] > top.get(r.engine)[k] : r[k] < top.get(r.engine)[k]))) top.set(r.engine, r);
    const [first, second] = [...top.values()].sort((a, b) => (up ? b[k] - a[k] : a[k] - b[k]));
    const behind = second && (up ? first[k] / second[k] - 1 : second[k] / first[k] - 1);
    return second && Math.round(behind * 100) >= 25 ? { first, second, behind } : null;
  };
  let gapCache = { key: null, list: [] };

  const share = (r, metric) => {
    const own = r.workload === "spec" ? Pie.specCeiling?.(r) : Pie.ceiling?.(r, metric.id);
    return own ? r[metric.key] / own.tps : null;
  };
  const overRaw = (r, metric, raw) => {
    const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine);
    const key = metric.id === "throughput" ? "output_tok_s" : metric.key;
    return plain?.[key] ? r[metric.key] / plain[key] : null;
  };
  const times = (x) => `${x >= 10 ? Math.round(x) : x.toFixed(1)}×`;


  const card = (title, sub, lines = [], foot = "") => `
    ${title ? `<div class="tip-title">${esc(title)}</div>` : ""}${sub ? `<div class="tip-sub">${esc(sub)}</div>` : ""}
    ${lines.length ? `<div class="tip-rows">${lines.join("")}</div>` : ""}${foot ? `<div class="tip-foot">${esc(foot)}</div>` : ""}`;
  const day = (r) => {
    const when = r.measured || r.stale?.measured || "";
    if (!when) return "";
    const [y, m, d] = when.slice(0, 10).split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  };
  let lastAll = null;
  let shownEngine = null;
  const WHY = { unsupported: "N/S", no_fit: "Does not fit", fail: "Failed", not_run: "N/M", no_data: "N/M" };
  const absentRows = (mac, model, mode, order) => {
    const rank = { unsupported: 0, no_fit: 1, fail: 2 };
    const absent = new Map();
    const runs = new Set((lastAll || []).filter((r) => r.hardware === mac && r.status !== "unsupported").map((r) => r.engine));
    for (const r of lastAll || []) {
      if (r.hardware !== mac || !runs.has(r.engine) || order.some((o) => o.engine === r.engine)) continue;
      const here = r.model === model && r.workload === mode.workload ? r : null;
      const had = absent.get(r.engine);
      if (!had) absent.set(r.engine, here || { engine: r.engine, status: "not_run" });
      else if (here && (rank[here.status] ?? 9) < (rank[had.status] ?? 9)) absent.set(r.engine, here);
    }
    const never = (r) => r.status === "fail" && /checkpoint unavailable|HTTP Error|No space left|Connection|timed out|download/i.test(r.note || "");
    return [...absent.values()].map((r) => `<div class="tip-row is-absent"${r.note ? ` title="${esc(r.note)}"` : ""}><span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}</span>
      <span class="tip-value">${esc(never(r) ? "N/M" : WHY[r.status] || "N/M")}</span><span class="tip-when"></span></div>`);
  };
  const tip = (mac, model, metric, c, mode, raw) => {
    const limit = mode.limit;
    const ceiling = limit ? Pie.ceiling?.(c.pie, metric.id) : null;
    const batchBound = limit ? null : mode.workload === "throughput" ? batchedBound(mac, model, c.pie.scheme, c.pie.benchmark, c.pie)
      : mode.id === "pbatch" ? Pie.ceiling?.(c.pie, "pbatch") || null : null;
    const batchPeak = batchBound ? batchBound.tps : null;
    const specBound = mode.id === "spec" ? Pie.specCeiling?.(c.pie) : null;
    const specGain = (r) => {
      const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine)?.[metric.key];
      if (!plain) return esc(value(r[metric.key], metric.unit));
      const delta = r[metric.key] - plain;
      if (Math.abs(delta) < 0.05) return `<span class="tip-delta">0 ${esc(metric.unit)}</span>`;
      const sign = delta > 0 ? "+" : "−";
      return `<span class="tip-delta ${delta > 0 ? "is-up" : "is-down"}">${sign}${esc(value(Math.abs(delta), metric.unit))}</span>`;
    };
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    const mini = Boolean(c.pie.miniature);
    const relative = (r) => `${Math.round((metric.higher ? r[metric.key] / c.pie[metric.key] : c.pie[metric.key] / r[metric.key]) * 100)}%`;
    const roofline = compare === "ceiling" && !mini;
    const lines = order.map((r, i) => {
      const extra = !roofline ? null : limit ? share(r, metric) : specBound ? r[metric.key] / specBound.tps : batchPeak ? r[metric.key] / batchPeak : overRaw(r, metric, raw);
      const note = extra === null ? "" : limit || batchPeak || specBound ? `${Math.round(extra * 100)}%` : times(extra);
      return `<div class="tip-row${r === c.pie ? " is-pie" : ""}"${r === c.pie ? ` style="color: ${Pie.engines.colorOf(r.engine)}"` : ""}>
      <span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}${i === 0 ? '<span class="tip-tag">Fastest</span>' : ""}</span>
      <span class="tip-value">${mini ? esc(relative(r)) : specBound && roofline ? specGain(r) : `${esc(value(r[metric.key], metric.unit))}${roofline ? `<span class="tip-share">${note}</span>` : ""}`}</span><span class="tip-when">${esc(day(r))}</span></div>`;
    });
    const limitRow = (name, tps, binds) => `<div class="tip-row is-limit${binds ? "" : " is-slack"}">
      ${binds ? '<svg class="tip-limit-mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 11.5a5.5 5.5 0 1 1 11 0M8 11.5l2.6-3.4"/></svg>' : "<span></span>"}<span class="tip-name" title="${binds ? "What sets the limit" : "Not the limit: the other bound is lower"}">${name} bound</span>
      <span class="tip-value">${esc(value(tps, metric.unit))}</span><span class="tip-when"></span></div>`;
    const bounds = (b) => [["Bandwidth", b.bandwidth], ["Compute", b.compute], ["Interconnect", b.interconnect]].filter(([, tps]) => tps).sort((x, y) => x[1] - y[1]);
    const both = roofline && (ceiling || batchBound);
    if (both) {
      const head = `<div class="tip-rows">${bounds(both).map(([name, tps], i) => limitRow(name, tps, i === 0)).join("")}</div>`;
      return `<div class="rf-card">${head}${roofCard(order.map((r) => roofPoint(r, mode, metric)).filter(Boolean))}</div>`;
    }
    if (specBound && roofline) lines.push(`<div class="tip-row is-limit">
      <svg class="tip-limit-mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 11.5a5.5 5.5 0 1 1 11 0M8 11.5l2.6-3.4"/></svg><span class="tip-name" title="The limit at the best draft width, at ${Pie.specAlpha}% acceptance">Spec Limit</span>
      <span class="tip-value">${esc(value(specBound.tps, metric.unit))}</span><span class="tip-when"></span></div>`);
    lines.push(...absentRows(mac, model, mode, order));
    if (specBound && roofline) {
      const moved = specMove(order, raw, specBound);
      if (moved) return `<div class="rf-move-card">${roofCard(moved, { move: true })}${card("", "", lines)}</div>`;
    }
    const gap = order.length > 1 ? "" : (Pie.store.tables.speed_gaps || []).find((g) => [].concat(g.platform).includes(mac) && [].concat(g.model).includes(model))?.reason || "";
    return mini ? card("Model slice", c.pie.miniature, lines, gap) : card("", "", lines, gap);
  };

  const roofPoint = (r, mode, metric) => {
    if (!r?.[metric.key] || mode.id === "spec") return null;
    if (mode.limit || mode.id === "pbatch") {
      const c = Pie.ceiling?.(r, mode.limit ? metric.id : "pbatch");
      if (!c?.parts.tflops) return null;
      const flops = c.parts.mathS * c.parts.tflops * 1e12;
      const bytes = (c.parts.weightGB + c.parts.cacheGB) * 1e9;
      return { r, ai: flops / bytes, achieved: (r[metric.key] / c.parts.tokens) * flops, bw: c.parts.bw, peak: c.parts.tflops,
        link: c.parts.linkS ? flops / c.parts.linkS : null };
    }
    const b = Pie.batchedCeiling?.(r.hardware, r.model, r.scheme, r.benchmark, r);
    if (!b?.parts.tflops) return null;
    const { bw, tflops } = b.parts;
    const flops = b.parts.mathS * tflops * 1e12;
    const bytes = b.parts.readS * bw * 1e9;
    return { r, ai: flops / bytes, achieved: (r[metric.key] / b.parts.requests) * flops, bw, peak: tflops,
      link: b.parts.linkS ? flops / b.parts.linkS : null };
  };

  const specMove = (order, raw, specBound) => {
    const focus = viewState?.platform.engine || Pie.engines.primary;
    const spec = order.find((r) => r.engine === focus) || order[0];
    const plain = raw.find((x) => x.hardware === spec.hardware && x.model === spec.model && x.engine === spec.engine);
    const from = plain && roofPoint(plain, MODES[0], METRICS[0]);
    if (!from || !specBound.k) return null;
    const ai = from.ai * (specBound.k + 1);
    const roofAt = (v) => Math.min(from.bw * 1e9 * v, from.peak * 1e12, from.link || Infinity);
    const share = spec[METRICS[0].key] / specBound.tps;
    return [{ ...from, ghost: true }, { ...from, r: spec, ai, achieved: share * roofAt(ai) }];
  };

  const roofCard = (found, { move = false } = {}) => {
    let points = found;
    if (!points.length) return "";
    const { bw, peak } = points[0];
    const knee = (peak * 1e12) / (bw * 1e9);
    const focus = viewState?.platform.engine || Pie.engines.primary;
    const own = points.find((p) => p.r.engine === focus) || points[0];
    const ai = own.ai;
    const link = own.link && own.link < Math.min(bw * 1e9 * ai, peak * 1e12) ? own.link : null;
    const shareOf = (p) => p.achieved / Math.min(p.bw * 1e9 * p.ai, p.peak * 1e12, p.link || Infinity);
    points = points.map((p) => ({ ...p, ai: move ? p.ai : ai, achieved: shareOf(p) * Math.min(bw * 1e9 * (move ? p.ai : ai), peak * 1e12, link || Infinity) }));
    const ais = move ? points.map((p) => p.ai) : [ai];
    const aiLo = Math.min(...ais), aiHi = Math.max(...ais);
    const X0 = aiLo * 0.6;
    const X1 = aiHi * 1.4;
    const Y1 = Math.max(Math.min(bw * 1e9 * X1, peak * 1e12), ...points.map((p) => p.achieved)) * 1.06;
    const Y0 = 0;
    const W = 196, H = 80, L = 2, R = 2, T = 14, B = 2;
    const x = (v) => L + ((v - X0) / (X1 - X0)) * (W - L - R);
    const y = (v) => T + (1 - (v - Y0) / (Y1 - Y0)) * (H - T - B);
    const roof = (v) => Math.min(bw * 1e9 * v, peak * 1e12);
    const start = X0;
    const isPie = (p) => p.r.engine === focus && !p.ghost;
    const point = (cx, cy, cls, color = "") => `<line class="${cls}" x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy}"${color ? ` stroke="${color}"` : ""}/>`;
    const dots = [...points.filter((p) => !isPie(p)), ...points.filter(isPie)]
      .map((p) => point(x(p.ai).toFixed(1), y(p.achieved).toFixed(1), isPie(p) ? "rf-dot" : "rf-dot is-other", isPie(p) ? Pie.engines.colorOf(p.r.engine) : "")).join("");
    const pct = (vx, vy) => `left: ${((vx / W) * 100).toFixed(2)}%; top: ${((vy / H) * 100).toFixed(2)}%`;
    const shown = knee > X0 && knee < X1;
    const roofPts = (shown ? [start, knee, X1] : [start, X1]).map((v) => `${x(v).toFixed(1)},${y(roof(v)).toFixed(1)}`);
    const kx = x(knee), ky = y(peak * 1e12);
    return `
      <div class="tip-roof">
        <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`Roofline: knee at ${Math.round(knee)} FLOPs per byte`)}">
          <line class="rf-zero" x1="${L}" x2="${W - R}" y1="${y(0).toFixed(1)}" y2="${y(0).toFixed(1)}"/>
          <polyline class="rf-roof" points="${roofPts.join(" ")}"/>
          ${link ? `<line class="rf-link" x1="${L}" x2="${W - R}" y1="${y(link).toFixed(1)}" y2="${y(link).toFixed(1)}"/>` : ""}
          ${shown ? point(kx.toFixed(1), ky.toFixed(1), "rf-knee") + point(kx.toFixed(1), ky.toFixed(1), "rf-knee-hole") : ""}
          ${dots}
        </svg>
        ${shown ? `<span class="rf-tick-name${kx > W / 2 ? " is-left" : ""} is-above" style="${pct(kx, ky)}">Knee</span>` : ""}
      </div>`;
  };

  let pointer = null;
  let peeked = null;
  let refreshCard = () => {};
  let viewState = null;
  const SIZES = [
    { id: "small", label: "Under 10B", test: (b) => b < 10 },
    { id: "medium", label: "10B to 40B", test: (b) => b >= 10 && b < 40 },
    { id: "large", label: "40B to 200B", test: (b) => b >= 40 && b < 200 },
    { id: "datacenter", label: "200B and up", test: (b) => b >= 200 },
  ];
  const paramsOf = (id) => (Pie.store.tables.models || []).find((m) => m.id === id)?.params_b;
  const sizeOf = (id) => { const b = paramsOf(id); return b == null ? null : SIZES.find((sz) => sz.test(b))?.id; };
  let pageMakers = [];
  let pageModels = [];
  const groupOf = (id, by) => {
    const m = (Pie.store.tables.models || []).find((x) => x.id === id) || {};
    if (by === "size") return SIZES.find((sz) => sz.id === sizeOf(id))?.label || "Unknown size";
    if (by === "where") return m.needs_gib != null && m.needs_gib <= 128 ? "Local" : "Cloud";
    return makerOf(id).name || "Cloud";
  };
  let pagePlatforms = [];

  const wireColumnDrag = (element, settled) => {
    const SETTLE = 180;
    let press = null;
    let drag = null;
    let dragged = false;
    const unitOf = (th) => {
      const table = th.closest("table");
      const cells = th.dataset.drop === "model"
        ? [...table.querySelectorAll(`[data-col="${CSS.escape(th.dataset.id)}"]`)]
        : [th, ...[...table.querySelectorAll(`[data-drop="model"][data-maker="${CSS.escape(th.dataset.id)}"]`)]
            .flatMap((head) => [...table.querySelectorAll(`[data-col="${CSS.escape(head.dataset.id)}"]`)])];
      const r = th.getBoundingClientRect();
      return { id: th.dataset.id, cells, left: r.left, width: r.width };
    };
    const shift = (unit, x, animate) => unit.cells.forEach((cell) => {
      cell.style.transition = animate ? `transform ${SETTLE}ms ease` : "none";
      cell.style.transform = x ? `translateX(${x}px)` : "";
    });
    element.addEventListener("pointerdown", (event) => {
      const th = event.target.closest("[data-drop]");
      if (!th || event.button !== 0 || drag) return;
      press = { th, x: event.clientX };
    });
    const lift = (event) => {
      const { th } = press;
      press = null;
      const kind = th.dataset.drop;
      const heads = [...th.closest("table").querySelectorAll(`[data-drop="${kind}"]`)].filter((x) => kind === "maker" || x.dataset.maker === th.dataset.maker);
      if (heads.length < 2) return;
      const units = heads.map(unitOf);
      const index = heads.indexOf(th);
      const me = units[index];
      me.cells.forEach((cell) => cell.classList.add("is-moving"));
      document.documentElement.classList.add("is-dragging-column");
      th.setPointerCapture(event.pointerId);
      dragged = true;
      drag = { kind, units, index, me, x0: event.clientX, lane: [units[0].left, units.at(-1).left + units.at(-1).width], to: index };
    };
    element.addEventListener("pointermove", (event) => {
      if (press && Math.abs(event.clientX - press.x) > 4) lift(event);
      if (!drag) return;
      const { units, index, me, lane } = drag;
      const dx = Math.max(lane[0] - me.left, Math.min(lane[1] - me.width - me.left, event.clientX - drag.x0));
      shift(me, dx, false);
      const middle = me.left + dx + me.width / 2;
      let to = index;
      units.forEach((u, i) => {
        if (i > index && middle >= u.left + u.width / 2) to = Math.max(to, i);
        if (i < index && middle <= u.left + u.width / 2) to = Math.min(to, i);
      });
      drag.to = to;
      units.forEach((u, i) => {
        if (u === me) return;
        shift(u, i > index && i <= to ? -me.width : i < index && i >= to ? me.width : 0, true);
      });
    });
    const finish = () => {
      press = null;
      if (!drag) return;
      const { kind, units, index, me, to } = drag;
      drag = null;
      const place = to > index ? units.slice(index + 1, to + 1).reduce((w, u) => w + u.width, 0)
        : -units.slice(to, index).reduce((w, u) => w + u.width, 0);
      shift(me, place, true);
      setTimeout(() => {
        units.forEach((u) => { shift(u, 0, false); u.cells.forEach((cell) => cell.classList.remove("is-moving")); });
        document.documentElement.classList.remove("is-dragging-column");
        if (to === index) return;
        const order = units.map((u) => u.id);
        order.splice(to, 0, order.splice(index, 1)[0]);
        const key = kind === "maker" ? "makerOrder" : "modelOrder";
        const rest = (Pie.state.platform[key] || []).filter((x) => !order.includes(x));
        Pie.state.platform[key] = kind === "maker" ? order.concat(rest) : rest.concat(order);
        settled();
      }, SETTLE);
    };
    element.addEventListener("pointerup", finish);
    element.addEventListener("pointercancel", finish);
    return () => { const was = dragged; dragged = false; return was; };
  };
  const waveIn = (root, ghosts = null) => {
    if (!WAVE || stillMotion.matches) return;
    const now = performance.now();
    let end = now;
    const tables = [...root.querySelectorAll(".platform-table")];
    const { offset, step } = waveSpan(tables);
    tables.forEach((table, t) => [...table.tBodies[0]?.rows || []].forEach((tr, r) => [...tr.cells].forEach((td, c) => {
      const key = `${t}|${r}|${c}`;
      const prev = cellAt[key];
      const at = cellAt[key] = Math.max(now + Math.round((offset[t] + r + c) * step), prev != null ? prev + RISE : -Infinity);
      td.style.setProperty("--roll-wait", `${Math.round(at - now)}ms`);
      end = Math.max(end, at);
      const old = ghosts?.[t]?.[r]?.[c];
      if (!td.querySelector(".platform-cell")) return;
      carryInto(td, old?.carry, now);
      if (old?.html) td.insertAdjacentHTML("beforeend", ghostHtml(old, at, prev != null && prev + RISE > now ? prev + 320 : null, now));
    })));
    root.classList.add("is-rolling");
    clearTimeout(root.waveTimer);
    root.waveTimer = setTimeout(() => { root.classList.remove("is-rolling"); root.querySelectorAll(".roll-ghost").forEach((g) => g.remove()); }, end + RISE + 200 - now);
  };
  Pie.platform = {
    machineName: macName,
    wireColumnDrag,
    waveIn,
    wave: WAVE,
    left() { if (auto.table) auto.table = "away"; },
    ghostsOf,
    inherit(ghosts) { auto.inherited = ghosts; },
    specSheet: (mac) => { const hw = Pie.store.index.hardware[mac]; return hw ? specSheet(hw) : ""; },
    roll() { auto.rolling = true; },

    refreshCard: () => refreshCard(),
    badge: (id) => badgeOf(id),
    modelCard: (id, precision = "") => {
      const m = Pie.store.index.models[id] || {};
      return `<div class="tip-title">${esc(names().model(id))}</div><div class="spec-rows">${[
        ["Maker", makerOf(id).name],
        ["Architecture", m.architecture],
        ["Parameters", m.params_b && `${m.params_b}B`],
        ["Active", m.active_b && m.active_b !== m.params_b && `${m.active_b}B a token`],
        ["Layers", m.layers],
        ["Experts", m.experts && `${m.experts}${m.top_k ? `, ${m.top_k} a token` : ""}`],
        ["Context", m.context && `${Number(m.context).toLocaleString()} tokens`],
        ["Precision here", precision],
      ].filter(([, v]) => v).map(([k, v]) => `<div class="spec-row"><span>${esc(k)}</span><span>${esc(String(v))}</span></div>`).join("")}</div>`;
    },
    element,
    batchedBound,

    compare: () => compare,
    peek(on) {
      if (on && !peeked) {
        peeked = compare;
        compare = compare === "ceiling" ? "engines" : "ceiling";
      } else if (!on && peeked) {
        compare = peeked;
        peeked = null;
      } else return false;
      return true;
    },
    next: () => nextCompare(compare),
    setupControl: (active, ids, tabs) => setupControl(active, ids.map((id) => MODES.find((m) => m.id === id)).filter(Boolean), tabs),
    changed: () => onChange(),
    makerBadge: (model) => badge(makerOf(model)),
    makerName: (model) => makerOf(model).name,
    makerName: (model) => makerOf(model).name || "Cloud",
    degree: (id) => `<svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[id] || ""}</svg>`,
    setCompare(value) {
      peeked = null;
      const next = COMPARES[value] ? value : "engines";
      if (viewState && next !== compare) {
        const kept = (viewState.platform.viewEngines ||= {});
        kept[compare] = viewState.platform.engine || Pie.engines.primary;
        viewState.platform.engine = kept[next] || Pie.engines.primary;
      }
      compare = chosen = next;
      try {
        localStorage.setItem("platformCompare", compare);
      } catch {
      }
    },

    machines(id) {
      return Pie.store.tables.hardware.filter((hw) => { const p = platformOf(hw); return p && (!id || p.id === id); }).length;
    },

    metrics(state) {
      if (!state || Pie.schema[state.table]?.view !== "platform") return MODES;
      const only = Pie.schema[state.table]?.platform;
      const ran = new Set(Pie.store.snapshot(state.release)
        .filter((r) => Pie.store.isMeasured(r) && (!only || platformOf(Pie.store.index.hardware[r.hardware] || {})?.id === only))
        .map((r) => r.workload));
      const HIDDEN = { tpu: ["spec", "batching", "pbatch"] };
      return MODES.filter((m) => m.id !== "spec" && (m.limit || m.id === "pbatch" || ran.has(m.workload)) && !(HIDDEN[only] || []).includes(m.id));
    },

    onChange(handler) {
      onChange = handler;
    },
    onOpenResults(handler) {
      openResults = handler;
    },
    onOpenGap(handler) {
      openGap = handler;
    },
    gaps(state) {
      const key = `${state.release}|${state.suite}|${Pie.store.snapshot(state.release).length}`;
      if (gapCache.key === key) return gapCache.list;
      const kept = { viewState, compare, lastAll, shownEngine, pagePlatforms, pageMakers, pageModels, inherited: auto.inherited };
      const s = { ...state, table: "speedups", query: "", platform: { ...state.platform, engine: null } };
      const SPEC = MODES.find((m) => m.id === "spec");
      const run = (r) => ({ workload: r.workload, benchmark: r.benchmark || "", miniature: r.miniature || "" });
      const list = [], seconds = [];
      try {
        for (const mode of Pie.platform.metrics(s)) {
          s.platform = { ...s.platform, mode: mode.id };
          const { grid } = Pie.platform.render(s, true);
          for (const [mac, row] of Object.entries(grid)) {
            for (const [model, { c }] of Object.entries(row)) {
              const pair = c?.pie && pairOf(c, mode.metric);
              if (pair) {
                const t = c.pie.workload === "spec" ? SPEC : mode;
                seconds.push({ engine: pair.second.engine, rival: pair.first.engine, setup: t.id, label: t.id === "spec" ? t.label : `${t.item} ${t.group}`, hardware: mac, model, gap: pair.behind, miniature: c.pie.miniature || null, row: c.pie });
              }
              if (!apart(c)) continue;
              const m = c.pie.workload === "spec" ? SPEC : mode;
              const key = m.metric.key;
              list.push({ setup: m.id, label: m.id === "spec" ? m.label : `${m.item} ${m.group}`, hardware: mac, model, miniature: c.pie.miniature || null,
                engines: (c.all || []).length, gap: c.gain, overLimit: overLimitOf(mac, model, m, m.metric, c),
                pieValue: c.pie[key], pieAt: c.pie.measured || null, pieNoisy: c.pie.status === "noisy", pieRun: run(c.pie),
                rival: c.best.engine, rivalValue: c.best[key], rivalAt: c.best.measured || null, rivalNoisy: c.best.status === "noisy", rivalRun: run(c.best) });
            }
          }
        }
      } finally {
        ({ viewState, compare, lastAll, shownEngine, pagePlatforms, pageMakers, pageModels } = kept);
        auto.inherited = kept.inherited;
      }
      gapCache = { key, list: list.sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap)), seconds };
      return gapCache.list;
    },
    seconds(state) {
      Pie.platform.gaps(state);
      return gapCache.seconds;
    },
    menu(k) {
      if (k === "platform" && viewState) {
        const current = viewState.platform.platforms || [];
        const ids = PLATFORMS.map((pl) => pl.id).filter((id) => pagePlatforms.includes(id) || current.includes(id));
        return [{ value: "", label: "All Platforms", selected: !current.length }, { separator: true },
          ...ids.map((id) => ({ value: id, label: Pie.schema[id]?.short || id, selected: current.includes(id), check: true, dot: Pie.schema[id]?.tint }))];
      }
      if (k === "model" && viewState) {
        const picked = viewState.platform.models || [];
        const ids = [...new Set([...pageModels, ...picked])];
        const current = picked.length ? picked : ids;
        const by = viewState.platform.modelGroup || "maker";
        const groups = {};
        for (const id of ids) (groups[groupOf(id, by)] ||= []).push(id);
        const order = by === "maker" ? Object.keys(groups).sort() : by === "size" ? [...SIZES.map((sz) => sz.label), "Unknown size"] : ["Local", "Cloud"];
        const GROUPS = [["maker", "Maker"], ["size", "Size"], ["where", "Local or Cloud"]];
        return [{ value: "", label: "All Models", selected: !picked.length, check: true },
          { label: "Group by", detail: GROUPS.find(([id]) => id === by)?.[1] || "Maker", submenu: GROUPS.map(([id, label]) => ({ value: `by:${id}`, key: "grid:model", label, selected: by === id })) },
          ...order.filter((name) => groups[name]).flatMap((name) => {
            const list = groups[name].sort((a, b) => (paramsOf(a) ?? Infinity) - (paramsOf(b) ?? Infinity) || names().model(a).localeCompare(names().model(b)));
            return [{ separator: true },
              { value: `group:${name}`, label: name, selected: list.every((id) => current.includes(id)), check: true, icon: by === "maker" ? badge(MAKERS.find((m) => m.name === name) || { logo: "" }) : "" },
              ...list.map((id) => ({ value: id, label: names().model(id), detail: paramsOf(id) ? `${paramsOf(id)}B` : "", selected: current.includes(id), check: true, indent: true, icon: badge(makerOf(id)) }))];
          })];
      }
      if (k === "maker" && viewState) {
        const current = viewState.platform.makers || [];
        const makers = [...new Set([...pageMakers, ...current])].sort();
        return [{ value: "", label: "All Makers", selected: !current.length }, { separator: true },
          ...makers.map((name) => ({ value: name, label: name, selected: current.includes(name), check: true, icon: badge(MAKERS.find((m) => m.name === name) || { logo: "" }) }))];
      }
      if (k === "size" && viewState) {
        const current = viewState.platform.sizes || [];
        return [{ value: "", label: "All Sizes", selected: !current.length }, { separator: true },
          ...SIZES.map((sz) => ({ value: sz.id, label: sz.label, selected: current.includes(sz.id), check: true }))];
      }
      if (k === "rival" && viewState) {
        const base = viewState.platform.engine || Pie.engines.primary;
        const current = viewState.platform.rival !== base ? viewState.platform.rival || "" : "";
        return [{ value: "", label: "Strongest", selected: !current }, { separator: true },
          ...Pie.store.tables.engines.filter((e) => e.id !== base).map((e) => ({ value: e.id, label: Pie.store.names.engine(e.id), selected: e.id === current, dot: Pie.engines.colorOf(e.id) }))];
      }
      if (k === "setup" && viewState) {
        const NAMES = { decode: "Single Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
        const picked = viewState.platform.mode || "decode";
        return ["decode", "prefill", "batching", "pbatch"].map((id) => ({ value: id, label: NAMES[id], selected: id === picked, detail: id === "decode" || id === "prefill" ? "Latency" : "Throughput", icon: `<svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[id]}</svg>` }));
      }
      if (k === "options" && viewState) {
        const own = (key, items) => items.map((o) => (o.separator ? o : { ...o, key: `grid:${key}` }));
        const fixedView = Pie.schema[viewState.table]?.compare;
        const engineOf = (id) => (id === compare ? shownEngine || viewState.platform.engine : viewState.platform.viewEngines?.[id]) || Pie.engines.primary;
        return [
          ...(fixedView ? [] : [{ heading: "View" }, ...["engines", "tps", "ceiling"].map((id) => ({ value: id, key: "grid:view", label: COMPARES[id], selected: id === compare, icon: viewIcon(id),
            detail: Pie.store.names.engine(engineOf(id)),
            submenu: Pie.store.tables.engines.map((e) => ({ value: `${id}|${e.id}`, key: "grid:view-engine", label: Pie.store.names.engine(e.id), selected: e.id === engineOf(id), dot: Pie.engines.colorOf(e.id) })) }))]),
          ...(fixedView ? [{ label: "Engine", detail: Pie.store.names.engine(viewState.platform.engine || Pie.engines.primary), submenu: own("engine", this.menu("engine")) }] : []),
          ...(compare === "engines" ? [{ separator: true }, { value: "slices", key: "grid:slices", label: "Show Model Slices", selected: viewState.platform.slices !== false, check: true }] : []),
        ];
      }
      if (k !== "engine" || !viewState) return [];
      const current = viewState.platform.engine || Pie.engines.primary;
      return Pie.store.tables.engines.map((e) => ({ value: e.id, label: Pie.store.names.engine(e.id), selected: e.id === current, dot: Pie.engines.colorOf(e.id) }));
    },
    pick(k, value) {
      const wave = (button) => { if (!viewState) return; captureGhosts(button); if (!button) auto.label = null; auto.rolling = true; auto.spent = 0; clearTimeout(auto.timer); };
      if (k === "view") { if (value !== compare) wave('[data-grid-pick="options"]'); Pie.platform.setCompare(value); return; }
      if (k === "slices") { if (viewState) viewState.platform.slices = viewState.platform.slices === false; return; }
      if (k === "view-engine") {
        const [view, engine] = String(value).split("|");
        if (view !== compare) wave('[data-grid-pick="options"]');
        Pie.platform.setCompare(view);
        if (viewState) { viewState.platform.engine = engine; (viewState.platform.viewEngines ||= {})[view] = engine; }
        return;
      }
      if (k === "engine" && viewState && value !== (viewState.platform.engine || Pie.engines.primary)) wave();
      if (k === "setup" && viewState) { stopTurns(); auto.rolling = value !== viewState.platform.mode; if (auto.rolling) captureGhosts(); viewState.platform.mode = value; return; }
      if (k === "engine" && viewState) { viewState.platform.engine = value; (viewState.platform.viewEngines ||= {})[compare] = value; }
      if (k === "rival" && viewState) viewState.platform.rival = value || null;
      if (k === "platform" && viewState) {
        const now = viewState.platform.platforms || [];
        viewState.platform.platforms = !value ? [] : now.includes(value) ? now.filter((id) => id !== value) : [...now, value];
      }
      if (k === "size" && viewState) {
        const now = viewState.platform.sizes || [];
        viewState.platform.sizes = !value ? [] : now.includes(value) ? now.filter((v) => v !== value) : [...now, value];
      }
      if (k === "model" && viewState) {
        if (value.startsWith("by:")) { viewState.platform.modelGroup = value.slice(3); return; }
        if (!value) { viewState.platform.models = []; return; }
        const now = viewState.platform.models?.length ? viewState.platform.models : pageModels;
        const by = viewState.platform.modelGroup || "maker";
        const own = value.startsWith("group:") ? pageModels.filter((id) => groupOf(id, by) === value.slice(6)) : [value];
        const all = own.every((id) => now.includes(id));
        const next = all ? now.filter((id) => !own.includes(id)) : [...new Set([...now, ...own])];
        viewState.platform.models = pageModels.every((id) => next.includes(id)) ? [] : next;
      }
      if (k === "maker" && viewState) {
        const now = viewState.platform.makers || [];
        viewState.platform.makers = !value ? [] : now.includes(value) ? now.filter((m) => m !== value) : [...now, value];
      }
    },

    render(state, dry = false) {
      if (!dry && state.table !== auto.table) { if (auto.table) { auto.rolling = true; auto.waves = []; auto.ghosts = auto.inherited || null; auto.label = null; } auto.table = state.table; }
      auto.inherited = null;
      viewState = state;
      const fixed = Pie.schema[state.table]?.compare;
      if (fixed) { peeked = null; compare = fixed; }
      else if (dry) compare = "engines";
      else if (!peeked) compare = chosen;
      const sliceOn = dry || compare !== "engines" || state.platform.slices !== false;
      const every = Pie.store.snapshot(state.release);
      const all = every.filter((r) => sliceOn || !r.miniature);
      const slicedAt = new Set(), fullAt = new Set();
      for (const r of every) (r.miniature ? slicedAt : Pie.store.isMeasured(r) ? fullAt : null)?.add(`${r.hardware}|${r.model}`);
      lastAll = all;
      shownEngine = null;
      const modes = Pie.platform.metrics(state);
      const mode = modes.find((m) => m.id === state.platform.mode) || modes.find((m) => m.id === "decode") || modes[0];
      const metric = mode.metric;
      const base = (!dry && state.platform.engine) || Pie.engines.primary;
      const snapshot = all.filter((r) => r.workload === mode.workload);
      const raw = all.filter((r) => r.workload === "raw" && Pie.store.isMeasured(r));
      const rows = snapshot.filter(Pie.store.isMeasured);
      const only = Pie.schema[state.table]?.platform;
      pagePlatforms = only ? [] : PLATFORMS.filter((pl) => rows.some((r) => platformOf(Pie.store.index.hardware[r.hardware] || {}) === pl)).map((pl) => pl.id);
      const groups = PLATFORMS.filter((p) => !only || p.id === only)
        .map((p) => ({ platform: p, macs: Pie.store.tables.hardware.filter((hw) => platformOf(hw) === p)
          .filter((hw) => !(hw.class === "gpu" && hw.count > 1))
          .filter((hw) => !["a100-pcie-x1", "h100-pcie-x1", "l4-x1"].includes(hw.id))
          .filter((hw) => !["tpu-v5p-8"].includes(hw.id))
          .map((hw) => hw.id) }))
        .filter((g) => !only || g.macs.length);
      const macs = groups.flatMap((g) => g.macs);
      if (only && !all.some((r) => Pie.store.isMeasured(r) && macs.includes(r.hardware))) {
        const label = Pie.schema[state.table]?.label || "this platform";
        element.innerHTML = `<div class="platform-empty"><span class="sidebar-glyph" style="--tint: ${Pie.schema[state.table]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(state.table)}</span>
          <h2>No ${esc(label)} results yet</h2></div>`;
        return { macs: 0, models: 0, metric };
      }
      const measuredAll = all.filter(Pie.store.isMeasured);
      const platformBase = new Map(), macBase = new Map();
      for (const g of groups) {
        let engine = base;
        if (base === Pie.engines.primary) {
          const on = measuredAll.filter((r) => g.macs.includes(r.hardware));
          if (on.length && !on.some((r) => r.engine === base)) {
            const n = {};
            for (const r of on) n[r.engine] = (n[r.engine] || 0) + 1;
            engine = Object.keys(n).sort((a, b) => n[b] - n[a] || a.localeCompare(b))[0];
          }
        }
        platformBase.set(g.platform.id, engine);
        for (const mac of g.macs) macBase.set(mac, engine);
      }
      const baseOf = (mac) => macBase.get(mac) || base;
      const standIn = (id) => { const e = platformBase.get(id); return e && e !== base ? e : null; };
      shownEngine = only ? standIn(only) : null;
      const query = state.query.trim().toLowerCase();
      const noFit = Pie.store.tables.no_fit || {};
      const p = state.platform;

      const byName = (a, b) => a.localeCompare(b, undefined, { sensitivity: "base", numeric: true });
      const rank = (list, key) => { const i = (list || []).indexOf(key); return i < 0 ? Infinity : i; };
      const byRank = (list, a, b) => { const x = rank(list, a), y = rank(list, b); return x === y ? 0 : x < y ? -1 : 1; };
      const machineText = (mac) => {
        const hw = Pie.store.index.hardware[mac] || {};
        return [chipName(mac), hw.name, hw.full_name, hw.vendor, hw.id, platformOf(hw)?.label].filter(Boolean).join(" ").toLowerCase();
      };
      const suiteModels = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id)).filter((id) => !mode.has || mode.has(id));
      const modelHits = query ? suiteModels.filter((id) => names().model(id).toLowerCase().includes(query)) : suiteModels;
      const macHits = query ? macs.filter((mac) => machineText(mac).includes(query)) : macs;
      const narrowModels = query && (modelHits.length || !macHits.length);
      const narrowMacs = query && macHits.length > 0;
      if (narrowMacs) for (const g of groups) g.macs = g.macs.filter((mac) => macHits.includes(mac));
      const fill = {};
      const SETUP_WORKLOADS = ["raw", "throughput", "prefill_batch"];
      const anySetup = all.filter((r) => SETUP_WORKLOADS.includes(r.workload) && Pie.store.isMeasured(r) && r.engine === baseOf(r.hardware) && macs.includes(r.hardware) && (r.decode_tok_s || r.prefill_tok_s || r.output_tok_s));
      for (const r of anySetup) (fill[r.model] ||= new Set()).add(r.hardware);
      for (const mac of macs) for (const id of suiteModels) if (noFit[mac]?.[id]?.[baseOf(mac)]) (fill[id] ||= new Set()).add(mac);
      const fillOf = (id) => fill[id]?.size || 0;
      pageMakers = [...new Set(rows.filter((r) => r[metric.key] && macs.includes(r.hardware) && suiteModels.includes(r.model)).map((r) => makerOf(r.model).name || "Cloud"))].sort();
      pageModels = [...new Set(rows.filter((r) => r[metric.key] && macs.includes(r.hardware) && suiteModels.includes(r.model)).map((r) => r.model))];
      const makerFill = {}, makerCount = {};
      for (const id of suiteModels) {
        const name = makerOf(id).name;
        makerFill[name] = (makerFill[name] || 0) + fillOf(id);
        makerCount[name] = (makerCount[name] || 0) + 1;
      }
      for (const name of Object.keys(makerFill)) makerFill[name] /= makerCount[name];
      const sortedModels = (narrowModels ? modelHits : suiteModels).filter((id) => !p.models?.length || p.models.includes(id))
        .sort((a, b) => byRank(p.makerOrder, makerOf(a).name, makerOf(b).name)
          || makerFill[makerOf(b).name] - makerFill[makerOf(a).name] || byName(makerOf(a).name || "~", makerOf(b).name || "~")
          || byRank(p.modelOrder, a, b) || fillOf(b) - fillOf(a) || byName(names().model(a), names().model(b)));
      const SPEC = MODES.find((m) => m.id === "spec");
      const specRows = mode.id === "decode" ? all.filter((r) => r.workload === "spec" && Pie.store.isMeasured(r) && macs.includes(r.hardware)) : [];
      const bestOf = (list) => {
        const by = {};
        for (const r of list) if (r[metric.key] && (!by[r.engine] || r[metric.key] > by[r.engine][metric.key])) by[r.engine] = r;
        return Object.values(by);
      };
      const modeOf = (c) => (c?.pie?.workload === "spec" ? SPEC : mode);
      const grid = {};
      for (const mac of macs) {
        grid[mac] = {};
        for (const model of sortedModels) {
          const here = (r) => r.hardware === mac && r.model === model;
          const base = baseOf(mac);
          let c = cell(specRows.length ? bestOf([...rows.filter(here), ...specRows.filter(here)]) : rows.filter(here), metric, base);
          const cut = sliceOn && ((TODAY.models.has(model) && TODAY.hardware.has(mac)) || snapshot.some((r) => here(r) && r.miniature));
          const fullNeeds = Pie.store.index.models[model]?.needs_gib;
          const formula = noFit[mac]?.[model]?.[base];
          const sliceOnly = !formula && slicedAt.has(`${mac}|${model}`) && !fullAt.has(`${mac}|${model}`);
          let needs = formula || (sliceOnly ? fullNeeds || 1 : undefined);
          if ((compare === "tps" || compare === "ceiling") && cut) c = null;
          const own = snapshot.find((r) => here(r) && r.engine === base);
          const cloud = Pie.store.index.models[model]?.catalog && compare === "engines";
          const failed = own && own.status === "fail";
          if (cloud && failed && !c) { grid[mac][model] = { c: null, needs, failed: true, why: own.note ? `Failed: ${own.note}` : "The run failed" }; continue; }
          grid[mac][model] = { c, needs, failed, why: sliceOnly ? "The full model does not run on this machine; only a model slice ran here" : needs ? ((compare === "tps" || compare === "ceiling") && cut ? `The full model does not fit one machine${fullNeeds ? `: needs about ${Math.round(fullNeeds)} GB` : ""}. Only a model slice ran` : `Needs about ${Math.round(needs)} GB`) : (compare === "tps" || compare === "ceiling") && cut ? "Only a model slice ran here, which is not the full model's speed" : own?.note || "" };
        }
      }
      const hide = state.hideEmpty;
      const awaiting = (mac, model) => !grid[mac][model].c && !grid[mac][model].needs && !grid[mac][model].failed && TODAY.models.has(model) && TODAY.hardware.has(mac);
      const ranAny = new Set(anySetup.map((r) => `${r.hardware}|${r.model}`));
      const shows = (mac, model) => grid[mac][model].c || awaiting(mac, model) || ranAny.has(`${mac}|${model}`);
      const checked = new Set(dry ? (Pie.store.tables.quality_parity || []).filter((r) => !r.ref_unsupported && Number.isFinite(r.kl_mean)).map((r) => `${r.platform}|${r.model}`) : []);
      const hasData = (mac, model) => grid[mac][model].c || (sliceOn && (awaiting(mac, model) || checked.has(`${mac}|${model}`)));
      const engineRuns = new Map(), modelRows = new Map();
      for (const r of all) {
        if (r.status !== "unsupported") (engineRuns.get(r.hardware) || engineRuns.set(r.hardware, new Set()).get(r.hardware)).add(r.engine);
        if (r.workload === mode.workload) (modelRows.get(`${r.hardware}|${r.model}`) || modelRows.set(`${r.hardware}|${r.model}`, new Map()).get(`${r.hardware}|${r.model}`)).set(r.engine, r.status);
      }
      const comparable = (mac, model) => {
        if (checked.has(`${mac}|${model}`)) return true;
        const statuses = modelRows.get(`${mac}|${model}`) || new Map();
        return [...(engineRuns.get(mac) || [])].filter((e) => !["unsupported", "no_fit"].includes(statuses.get(e))).length >= 2;
      };
      const models = (hide ? sortedModels.filter((model) => macs.some((mac) => hasData(mac, model))) : sortedModels)
        .filter((model) => compare !== "engines" || macs.some((mac) => comparable(mac, model)));
      const median = (list) => {
        const sorted = list.filter((g) => g !== undefined && g !== null).sort((a, b) => a - b);
        return sorted.length ? sorted[sorted.length >> 1] : null;
      };
      const top = {};
      for (const model of models) {
        const vs = macs.map((mac) => grid[mac][model].c?.pie[metric.key]).filter((v) => v > 0);
        if (vs.length > 1) top[model] = Math.max(...vs);
      }
      const topOf = new Map();
      const topIn = (list, model) => {
        const key = `${list.join(",")}|${model}`;
        if (!topOf.has(key)) {
          const vs = list.map((mac) => grid[mac][model].c?.pie[metric.key]).filter((v) => v > 0);
          topOf.set(key, vs.length ? Math.max(...vs) : null);
        }
        return topOf.get(key);
      }
      const hideUnverified = compare === "engines" && p.showUnverified !== true;
      const unverified = (mac, model) => {
        const c = grid[mac]?.[model]?.c;
        if (!hideUnverified || !c) return false;
        const pair = pairOf(c, metric);
        if (!pair || pair.first.engine !== c.pie.engine || overLimitOf(mac, model, modeOf(c), metric, c)) return false;
        return !Pie.verifiedProfile?.(`${mac}|${model}|${modeOf(c).id}`);
      };
      const overall = (mac) => median(models.map((model) => (unverified(mac, model) ? null : compare === "tps" ? grid[mac][model].c?.pie[metric.key] : grid[mac][model].c?.gain)));
      const sortFor = (k) => p.sortBy?.[k] || null;
      const hidden = new Set(p.hidden || []);
      const order = (list, k) => { const s = sorted(list, k); return [...s.filter((mac) => !hidden.has(mac)), ...s.filter((mac) => hidden.has(mac))]; };
      const sorted = (list, k) => {
        const { key: sortKey = null, dir = 1 } = sortFor(k) || {};
        const named = [...list];
        if (!sortKey) return named;
        if (sortKey === "name") return named.sort((a, b) => dir * macName(a).localeCompare(macName(b), undefined, { numeric: true }));
        const val = (mac) => (sortKey === "overall" ? overall(mac) : unverified(mac, sortKey) ? null : grid[mac][sortKey]?.c?.gain ?? null);
        return named.sort((a, b) => (val(a) === null) - (val(b) === null) || dir * ((val(a) ?? 0) - (val(b) ?? 0)));
      };
      const grouped = groups.map((g) => ({ ...g, macs: order(hide ? g.macs.filter((mac) => models.some((model) => shows(mac, model))) : g.macs, g.platform.id) }))
        .filter((g) => (!only && !narrowMacs) || g.macs.length);
      const sliced = new Set(all.filter((r) => r.miniature && r.engine === baseOf(r.hardware)).map((r) => `${r.hardware}|${r.model}`));
      const slicedOn = (list, model) => list.some((mac) => sliced.has(`${mac}|${model}`));
      const slicedEvery = new Set(every.filter((r) => r.miniature && r.engine === baseOf(r.hardware)).map((r) => `${r.hardware}|${r.model}`));
      const minisFirst = (list, ms) => {
        const mini = (model) => list.some((mac) => slicedEvery.has(`${mac}|${model}`));
        const byMaker = new Map();
        for (const m of [...ms.filter(mini), ...ms.filter((m) => !mini(m))]) (byMaker.get(makerOf(m).name) || byMaker.set(makerOf(m).name, []).get(makerOf(m).name)).push(m);
        return [...byMaker.values()].flat();
      };
      const sections = only ? [{ platform: null, macs: order(grouped.flatMap((g) => g.macs), only), models: minisFirst(grouped.flatMap((g) => g.macs), models) }]
        : grouped.map((g) => ({ platform: g.platform, macs: g.macs, models: minisFirst(g.macs, models.filter((model) => g.macs.some((mac) => hasData(mac, model)) && (compare !== "engines" || g.macs.some((mac) => comparable(mac, model))))) }))
          .filter((g) => g.macs.length && g.models.length);
      if (dry) return { sections, sliced, grid };

      const cells = [];
      const number = (gain) => {
        const kind = Math.abs(gain) < EVEN ? "is-even" : gain > 0 ? "is-ahead" : "is-behind";
        return { kind, html: Math.round(gain * 100) ? signed(gain) : "0%" };
      };
      const terse = (name) => name.replace(/^RTX (PRO )?/, (_, pro) => (pro ? "PRO " : "")).replace(/ (SXM|PCIe)\b/, "");
      const pageNames = macs.map((mac) => chipName(mac));
      const shortOf = (mac) => {
        const name = chipName(mac);
        const short = terse(name);
        return pageNames.some((other) => other !== name && terse(other) === short) ? name.replace(/^RTX (PRO )?/, (_, pro) => (pro ? "PRO " : "")) : short;
      };
      const EYE = "M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z";
      const eye = (mac) => {
        const off = hidden.has(mac);
        const label = off ? "Show this machine's numbers" : "Hide this machine's numbers";
        return `<button type="button" class="platform-eye" data-hide-mac="${esc(mac)}" aria-pressed="${off}" aria-label="${label}" title="${label}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="${EYE}"/>${off ? '<path d="M3 13 13 3"/>' : '<circle cx="8" cy="8" r="2"/>'}</svg></button>`;
      };
      const machine = (mac) => {
        const hw = Pie.store.index.hardware[mac];
        const short = shortOf(mac);
        return `<th class="platform-row" scope="row" data-hide-mac="${esc(mac)}"${hw ? ` data-tip="${esc(specSheet(hw))}"` : ""}><span class="platform-chip">${badgeOf(platformOf(hw || {})?.id)}<span class="platform-name">${esc(chipName(mac))}</span>${short !== chipName(mac) ? `<span class="platform-short">${esc(short)}</span>` : ""}${specOf(hw)}</span>${eye(mac)}</th>`;
      };
      const folded = (id) => Boolean(p.collapsed?.[id]);
      const groupRow = (g) => `<tr class="platform-group-row${folded(g.platform.id) ? " is-collapsed" : ""}${g.macs.length ? "" : " is-empty"}"${g.macs.length ? ` data-group="${g.platform.id}"` : ""} aria-expanded="${!folded(g.platform.id)}"><th colspan="${models.length + 3}" scope="rowgroup">
        <span class="platform-group-bar">
          <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${esc(g.platform.sub)} · ${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}</span></span>
          <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
        </span></th></tr>`;
      const MARK = {
        compute: { title: "Compute-bound: the share of the compute bound", path: "M4.5 4.5h7v7h-7zM6.5 2v2.5M9.5 2v2.5M6.5 11.5V14M9.5 11.5V14M2 6.5h2.5M2 9.5h2.5M11.5 6.5H14M11.5 9.5H14" },
        bandwidth: { title: "Bandwidth-bound: the share of the bandwidth bound", path: "M2 5.5h9M8.5 3l2.5 2.5L8.5 8M14 10.5H5M7.5 8 5 10.5 7.5 13" },
        interconnect: { title: "Interconnect-bound: the share of the bound set by the link between the GPUs", path: "M6.5 9.5l3-3M7.2 4.6l1.4-1.4a2.6 2.6 0 0 1 3.7 3.7l-1.4 1.4M8.8 11.4l-1.4 1.4a2.6 2.6 0 0 1-3.7-3.7l1.4-1.4" },
      };
      const tableOf = ({ macs: list, models, platform: own }) => {
      const key = own?.id || only || "all";
      const { key: sortKey = null, dir = 1 } = sortFor(key) || {};
      const tight = p.narrowBy?.[key] ?? (p.narrow ?? false);
      const narrowLabel = tight ? "Show Overall and memory" : "Hide Overall and memory";
      const shownGroups = [{ platform: null, macs: list }];
      const sliceMark = (cut, model) => {
        const all = Pie.store.index.models[model]?.layers;
        const kept = parseInt(cut, 10);
        const experts = String(cut).match(/, (\d+) experts$/)?.[1];
        const how = (kept && all ? `${kept} of ${all} layers kept (${Math.round((kept / all) * 100)}%)` : String(cut).replace(/, \d+ experts$/, "")) + (experts ? `, the first ${experts} experts` : "");
        return `<span class="column-info slice-mark" tabindex="0" role="button" aria-label="Model slice"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg><span class="column-info-pop" role="tooltip">${esc(`Model slice: ${how}, to fit one device. For engine-to-engine comparison only, not the full model's speed.`)}</span></span>`;
      };
      const body = shownGroups.map((g) => (g.platform ? groupRow(g) : "") + (g.platform && folded(g.platform.id) ? [] : g.macs).map((mac) => {
        if (hidden.has(mac)) return `<tr class="is-hidden-row" data-empty="1">${machine(mac)}<td class="is-overall" data-hide-mac="${esc(mac)}">${eye(mac)}</td>${models.map((model) => `<td data-col="${esc(model)}"></td>`).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
        const o = overall(mac);
        const overallCell = o === null ? `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell is-empty">–</span>${eye(mac)}</td>`
          : compare === "tps" ? `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell is-even"><span class="platform-main">${fmtNum(o)}<span class="platform-unit">${esc(metric.unit)}</span></span></span>${eye(mac)}</td>`
          : (() => { const n = number(o); n.html = Math.round(o * 100) ? signed(o) : "0%"; return `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell ${n.kind}" data-tip="${esc(card(macName(mac), Math.abs(o) < EVEN ? "On par with the next best" : `${Math.abs(Math.round(o * 100))}% ${o > 0 ? "faster" : "slower"} than the next best`))}"><span class="platform-main">${n.html}</span></span>${eye(mac)}</td>`; })();
        return `<tr>${machine(mac)}${overallCell}${models.map((model) => {
          const { c, needs, why } = grid[mac][model];
          const sorted = sortKey === model ? " is-sorted" : "";
          if (c && unverified(mac, model)) {
            return `<td class="${sorted} is-unverified" data-col="${esc(model)}"><span class="platform-cell is-empty${needs ? " is-nofit" : ""}">${needs ? `${NOFIT}N/A` : ""}</span></td>`;
          }
          if (c) {
            cells.push(c.gain);
            const ceil = compare === "ceiling" ? boundOf(mac, model, modeOf(c), metric, c.pie) : null;
            const n = compare === "ceiling"
              ? (() => {
                  if (!ceil) return { kind: "is-even", html: "–" };
                  const share = c.pie[metric.key] / ceil.tps;
                  const kind = Math.round(share * 100) > 100 ? "is-behind" : share >= 0.25 ? "is-ahead" : "is-mid";
                  const which = MARK[ceil.bound] ? ceil.bound : (ceil.bandwidth || Infinity) <= (ceil.compute || Infinity) ? "bandwidth" : "compute";
                  const mark = MARK[which];
                  return { kind, html: `<svg class="platform-bound-mark" viewBox="0 0 16 16" role="img" aria-label="${mark.title}"><title>${mark.title}</title><path d="${mark.path}"/></svg>${Math.round(share * 100)}%` };
                })()
              : compare === "tps" ? { kind: "is-even", html: `${esc(fmtNum(c.pie[metric.key]))}<span class="platform-unit">${esc(metric.unit)}</span>` }
              : c.gain === null ? { kind: "is-even", html: c.pie.miniature ? "–" : esc(value(c.pie[metric.key], metric.unit)) } : number(c.gain);
            const PHASE = { decode: "raw_decode", prefill: "raw_prefill", spec: "spec_decode", batching: "throughput", pbatch: "prefill_batch" };
            const open = { hardware: [mac], model: [model], workload: [PHASE[modeOf(c).id] || modeOf(c).workload],
              engine: compare === "engines" ? [...new Set((c.all || [c.pie]).map((r) => r.engine))] : [c.pie.engine] };
            if (compare === "engines" && c.gain === null && c.pie.miniature) return `<td class="${sorted} is-openable" data-col="${esc(model)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell is-empty is-nofit" data-tip="${esc(tip(mac, model, metric, c, modeOf(c), raw))}">${NOFIT}N/A</span>${eye(mac)}</td>`;
            const overLimit = overLimitOf(mac, model, modeOf(c), metric, c);
            const pair = compare === "engines" ? pairOf(c, metric) : null;
            const flagged = !!pair && pair.first.engine === c.pie.engine && !overLimit;
            const profiled = (Pie.profiles || {})[`${mac}|${model}|${modeOf(c).id}`];
            const explained = flagged && Pie.verifiedProfile?.(`${mac}|${model}|${modeOf(c).id}`);
            const rerun = flagged && profiled && !explained;
            const reasonAt = explained ? ` data-gap="${esc(JSON.stringify({ engine: pair.second.engine, hardware: mac, model: model, setup: modeOf(c).id }))}"` : "";
            return `<td class="${sorted} is-openable${overLimit ? " is-over-limit" : explained ? " is-explained" : flagged ? " is-gap" : ""}"${reasonAt} data-col="${esc(model)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">${explained ? "See Reason" : "See Runs"}<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${n.kind}${c.pie.miniature ? " is-mini" : ""}${compare === "tps" && topIn(g.macs.filter((m) => !hidden.has(m)), model) === c.pie[metric.key] ? " is-top" : ""}"${compare === "tps" ? "" : ` data-tip="${esc(tip(mac, model, metric, c, modeOf(c), raw))}"`}>${c.pie.miniature ? sliceMark(c.pie.miniature, model) : ""}${explained ? `<span class="verified-mark" aria-hidden="true"><svg viewBox="0 0 16 16"><path class="shield" d="M8 1.6 2.6 3.7v3.8c0 3.3 2.3 6 5.4 7 3.1-1 5.4-3.7 5.4-7V3.7Z"/><path class="mark" d="M5.5 8.2l1.8 1.8 3.3-3.6"/></svg></span>` : rerun ? `<span class="verified-mark is-rerun" aria-hidden="true"><svg viewBox="0 0 16 16" aria-hidden="true"><path class="shield" d="M8 1.6 2.6 3.7v3.8c0 3.3 2.3 6 5.4 7 3.1-1 5.4-3.7 5.4-7V3.7Z"/><path class="mark" d="M8 5.2v3.3"/><circle class="dot" cx="8" cy="10.9" r=".95"/></svg></span>` : ""}<span class="platform-main">${n.html}</span></span></td>`;
          }
          const ranHere = [...new Map(rows.filter((r) => r.hardware === mac && r.model === model && r[metric.key]).map((r) => [r.engine, r])).values()]
            .sort((a, b) => b[metric.key] - a[metric.key]);
          const absent = [...ranHere.map((r) => `<div class="tip-row"><span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}</span>
            <span class="tip-value">${r.miniature ? "Model slice" : esc(value(r[metric.key], metric.unit))}</span><span class="tip-when">${esc(day(r))}</span></div>`), ...absentRows(mac, model, modeOf(null), ranHere)];
          const emptyTip = compare === "tps" || compare === "ceiling" ? "" : absent.length ? card("", "", absent) : why ? card("", "", [], why) : "";
          const EMPTY_PHASE = { decode: "raw_decode", prefill: "raw_prefill", spec: "spec_decode", batching: "throughput", pbatch: "prefill_batch" };
          const openEmpty = { hardware: [mac], model: [model], workload: [EMPTY_PHASE[state.platform.mode] || "raw_decode"], _unavailable: true };
          return `<td class="${sorted} is-openable" data-col="${esc(model)}" data-open="${esc(JSON.stringify(openEmpty))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell is-empty${needs ? " is-nofit" : ""}"${emptyTip ? ` data-tip="${esc(emptyTip)}"` : ""}>${needs ? `${NOFIT}N/A` : "–"}</span></td>`;
        }).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
      }).join("")).join("");

      const arrow = (key) => (sortKey === key ? `<span class="column-sort">${dir > 0 ? "↑" : "↓"}</span>` : "");
      const makers = [];
      const cut = (model) => slicedOn(list, model);
      for (const model of models) {
        const maker = makerOf(model);
        const last = makers[makers.length - 1];
        if (last && last.maker.name === maker.name) { last.n += 1; last.count += 1; }
        else makers.push({ maker, n: 1, count: 1, cut: cut(model) });
      }
      const makerRow = `<tr class="platform-maker-row"><th class="platform-corner"><button type="button" class="platform-narrow" data-narrow="${esc(key)}" aria-pressed="${tight}" aria-label="${narrowLabel}" title="${narrowLabel}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M7.5 4 3.5 8l4 4M12.5 4l-4 4 4 4"/></svg></button></th><th class="platform-corner is-sortable is-overall" data-sort="overall" aria-hidden="true"></th>${makers.map(({ maker, n, count }, i) =>
        `<th class="platform-maker" colspan="${n + (i === makers.length - 1 ? 1 : 0)}" scope="colgroup" data-drop="maker" data-id="${esc(maker.name)}"><span class="platform-maker-name">${badge(maker)}<b>${esc(maker.name || "Cloud")}</b><span>${count} ${count === 1 ? "model" : "models"}</span></span></th>`).join("")}${makers.length ? "" : '<th class="platform-fill" aria-hidden="true"></th>'}</tr>`;
      const head = `<tr class="platform-head-row">
        <th class="platform-corner is-sortable" scope="col" data-sort="name">Hardware${arrow("name")}</th>
        <th class="platform-corner is-sortable is-overall" scope="col" data-sort="overall"><span class="platform-model">Overall${arrow("overall")}</span><span class="platform-sub">Median</span></th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B` : ""}` : "";
        const SCHEME = { affine_u4_g64: "4-bit", bf16: "BF16", fp8: "FP8", mxfp4: "MXFP4", gguf_q4_k_m: "Q4_K_M", gguf_ud_q4_k_xl: "UD-Q4_K_XL", gguf_q8_0: "Q8_0", mlx_2bit: "2-bit" };
        const precision = [...new Set(list.map((mac) => grid[mac]?.[model]?.c?.pie?.scheme).filter(Boolean).map((s) => SCHEME[s] || s))].join(" / ");
        const sub = size;
        const sheet = `<div class="tip-title">${esc(names().model(model))}</div><div class="spec-rows">${[
          ["Maker", makerOf(model).name],
          ["Architecture", m.architecture],
          ["Parameters", m.params_b && `${m.params_b}B`],
          ["Active", m.active_b && m.active_b !== m.params_b && `${m.active_b}B a token`],
          ["Layers", m.layers],
          ["Experts", m.experts && `${m.experts}${m.top_k ? `, ${m.top_k} a token` : ""}`],
          ["Context", m.context && `${Number(m.context).toLocaleString()} tokens`],
          ["Precision here", precision],
        ].filter(([, v]) => v).map(([k, v]) => `<div class="spec-row"><span>${esc(k)}</span><span>${esc(String(v))}</span></div>`).join("")}</div>`;
        return `<th class="is-sortable${sortKey === model ? " is-sorted" : ""}" scope="col" data-sort="${esc(model)}" data-drop="model" data-col="${esc(model)}" data-id="${esc(model)}" data-maker="${esc(makerOf(model).name)}" data-tip="${esc(sheet)}">
          <span class="platform-col"><span><span class="platform-model">${esc(names().model(model))}${arrow(model)}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;
      return `<table class="platform-table${tight ? " is-tight" : ""}" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>`;
      };
      const tables = only ? tableOf(sections[0] || { macs: [], models: [] }) : sections.map((g, i) => `<section class="platform-section">
        <div class="platform-group-row platform-section-bar${folded(g.platform.id) ? " is-collapsed" : ""}" style="--stack: ${i}" data-group="${g.platform.id}" role="button" aria-expanded="${!folded(g.platform.id)}">
          <span class="platform-group-bar">
            <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}, ${g.models.length} ${g.models.length === 1 ? "model" : "models"}</span></span>
            <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
          </span>
        </div><div class="platform-section-body"${folded(g.platform.id) ? " hidden" : ""}><div class="platform-section-scroll">${tableOf(g)}</div></div></section>`).join("");

      const nothing = !sections.some((g) => g.macs.length && g.models.length);
      const keptPage = element.querySelector(".platform-scroll");
      const kept = keptPage ? { top: keptPage.scrollTop, left: keptPage.scrollLeft, lefts: [...element.querySelectorAll(".platform-section-scroll")].map((x) => x.scrollLeft) } : null;
      element.innerHTML = `
        <div class="platform-bar">
          ${setupControl(mode.id, modes)}${mode.id === "spec" && compare === "ceiling" ? `${Pie.specField?.() || ""}` : ""}
          <button type="button" class="plain-button rules-button" data-rules aria-expanded="false" aria-label="Test Conditions" title="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button>
          <span class="platform-bar-side is-end">
            <span class="platform-key" title="An engine on this cell measured above the hardware's theoretical limit"><i class="platform-key-swatch is-over-limit" aria-hidden="true"></i>Above Limit</span>
            <span class="platform-key" title="Pie is 25% or more faster than the strongest other engine on this cell, and a profile of both engines confirms it: Profiling shows the profile"><i class="platform-key-swatch is-explained" aria-hidden="true"></i>Explained</span>
            <span class="platform-key" title="Pie is 25% or more faster than the strongest other engine on this cell, with no traced cause yet: it needs study or a rerun"><i class="platform-key-swatch is-gap" aria-hidden="true"></i>Needs Review</span>
            <span class="platform-key" title="The full model does not fit one machine; a number beside the mark is a model slice&#39;s, for comparing engines">${NOFIT}Does not fit</span>
            ${compare === "engines" ? `<span class="filter platform-setup"><button type="button" class="filter-button" data-unverified aria-pressed="${p.showUnverified !== true}" title="${p.showUnverified !== true ? "Needs Review cells show no number: click to show them" : "Hide the numbers of Needs Review cells"}"><svg class="view-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12s-3.5 6.5-9.5 6.5S2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>${p.showUnverified !== true ? '<path d="M4 4l16 16"/>' : ""}</svg><span>Hide Unverified</span></button></span>` : ""}
            <span class="filter platform-setup"><button class="filter-button label-rolls" type="button" data-grid-pick="options" aria-haspopup="menu" aria-label="View Options" title="View, engine and opponent">${viewIcon(compare)}<span>${esc(COMPARES[compare])}</span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>
            <span class="filter platform-setup"><button class="filter-button" type="button" data-grid-pick="model" aria-haspopup="menu" aria-label="Models">${esc(!p.models?.length ? "All Models" : p.models.length <= 2 ? p.models.map((id) => names().model(id)).join(", ") : `${p.models.length} Models`)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>
            <span class="filter platform-setup platform-engine-now" title="Every cell compares ${esc(names().engine(shownEngine || p.engine || Pie.engines.primary))}; View Options changes it"><span class="filter-button">${Pie.engines.logo?.(shownEngine || p.engine || Pie.engines.primary) || ""}<span>${esc(names().engine(shownEngine || p.engine || Pie.engines.primary))}</span></span></span>

          </span>
        </div>
        <div class="platform-scroll">
          ${nothing ? '<div class="platform-nothing">Nothing matches these filters</div>' : tables}
        </div>`;
      const scroller = element.querySelector(".platform-scroll");
      if (scroller) element.style.setProperty("--platform-visible", `${scroller.clientWidth}px`);
      stripes(element);
      const macsShown = sections.reduce((n, g) => n + g.macs.length, 0);
      if (kept) {
        const put = () => {
          const page = element.querySelector(".platform-scroll");
          if (page) { page.scrollTop = kept.top; page.scrollLeft = kept.left; }
          element.querySelectorAll(".platform-section-scroll").forEach((x, n) => { x.scrollLeft = kept.lefts[n] || 0; });
        };
        put();
        requestAnimationFrame(put);
      }
      afterDraw();
      return { macs: macsShown, models: new Set(sections.flatMap((g) => g.models)).size };
    },

    bind(state) {
      const inPlace = (redraw) => {
        const page0 = element.querySelector(".platform-scroll");
        const top = page0?.scrollTop || 0;
        const left = page0?.scrollLeft || 0;
        const lefts = [...element.querySelectorAll(".platform-section-scroll")].map((s) => s.scrollLeft);
        const put = () => {
          const page = element.querySelector(".platform-scroll");
          if (page) { page.scrollTop = top; page.scrollLeft = left; }
          element.querySelectorAll(".platform-section-scroll").forEach((s, i) => { s.scrollLeft = lefts[i] || 0; });
        };
        redraw();
        put();
        requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(put)));
      };
      element.addEventListener("click", (event) => {
        const cell = event.target.closest("td[data-open]");
        if (cell && !event.target.closest(".column-info")) { if (cell.dataset.gap) openGap(JSON.parse(cell.dataset.gap)); else openResults(JSON.parse(cell.dataset.open)); return; }
      });
      element.addEventListener("click", (event) => {
        const button = event.target.closest("[data-hide-mac]");
        if (!button) return;
        event.stopPropagation();
        const mac = button.dataset.hideMac;
        const hidden = new Set(state.platform.hidden || []);
        if (hidden.has(mac)) hidden.delete(mac); else hidden.add(mac);
        state.platform.hidden = [...hidden];
        Pie.saveView?.();
        const off = hidden.has(mac);
        const rows = [...element.querySelectorAll("tbody tr")].filter((tr) => tr.querySelector(`th.platform-row[data-hide-mac="${CSS.escape(mac)}"]`));
        if (rows.length && (off || rows.every((tr) => !tr.dataset.empty))) {
          for (const tr of rows) {
            tr.classList.toggle("is-hidden-row", off);
            for (const b of tr.querySelectorAll(".platform-eye")) {
              b.setAttribute("aria-pressed", String(off));
              b.querySelector("svg").innerHTML = `<path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z"/>${off ? '<path d="M3 13 13 3"/>' : '<circle cx="8" cy="8" r="2"/>'}`;
            }
            const body = tr.parentElement;
            if (off) body.append(tr);
            else body.insertBefore(tr, [...body.children].find((r) => r !== tr && r.classList.contains("is-hidden-row")) || null);
          }
          return;
        }
        inPlace(() => document.dispatchEvent(new CustomEvent("pie:refresh")));
      }, true);
      element.addEventListener("click", (event) => {
        const button = event.target.closest("[data-narrow]");
        if (!button) return;
        event.stopPropagation();
        if (event.detail) button.blur();
        const table = button.closest(".platform-table");
        const narrow = !table.classList.contains("is-tight");
        state.platform.narrowBy = { ...state.platform.narrowBy, [button.dataset.narrow]: narrow };
        Pie.saveView?.();
        const label = narrow ? "Show Overall and memory" : "Hide Overall and memory";
        table.classList.toggle("is-tight", narrow);
        stripes(element);
        button.setAttribute("aria-pressed", String(narrow)); button.title = label; button.setAttribute("aria-label", label);
      }, true);

      const wasDrag = wireColumnDrag(element, () => inPlace(onChange));
      element.addEventListener("click", (event) => {
        if (wasDrag()) return;
        const button = event.target.closest("[data-metric]");
        if (button) {
          state.platform.metric = button.dataset.metric;
          onChange();
          return;
        }
        const tab = event.target.closest("[data-mode]");
        if (tab) {
          stopTurns();
          auto.rolling = tab.dataset.mode !== state.platform.mode;
          if (auto.rolling) captureGhosts();
          state.platform.mode = tab.dataset.mode;
          onChange();
          return;
        }
        const pick = event.target.closest("[data-grid-pick]");
        if (pick) {
          event.stopPropagation();
          Pie.popover.open(pick, `grid:${pick.dataset.gridPick}`, null);
          return;
        }
        const unverifiedToggle = event.target.closest("[data-unverified]");
        if (unverifiedToggle) {
          state.platform.showUnverified = state.platform.showUnverified !== true;
          onChange();
          return;
        }
        const view = event.target.closest("[data-compare]");
        if (view) {
          Pie.platform.setCompare(view.dataset.compare);
          onChange();
          return;
        }
        const picker = event.target.closest("#platform-metric");
        if (picker) {
          event.stopPropagation();
          Pie.popover.open(picker, Pie.popover.METRIC, state);
          return;
        }
        const group = event.target.closest("[data-group]");
        if (group) {
          const id = group.dataset.group;
          const toggle = () => {
            state.platform.collapsed = { ...(state.platform.collapsed || {}), [id]: !state.platform.collapsed?.[id] };
            onChange();
          };
          const bar = group.classList.contains("platform-section-bar") ? group : null;
          if (!bar) { toggle(); return; }
          const body = bar.nextElementSibling;
          const fold = !state.platform.collapsed?.[id];
          state.platform.collapsed = { ...(state.platform.collapsed || {}), [id]: fold };
          Pie.saveView?.();
          bar.classList.toggle("is-collapsed", fold);
          bar.setAttribute("aria-expanded", String(!fold));
          body.getAnimations().forEach((a) => a.cancel());
          const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
          if (fold) {
            if (reduce) { body.hidden = true; return; }
            body.animate([{ height: `${body.offsetHeight}px` }, { height: "0px" }], { duration: 250, easing: "cubic-bezier(.25, .1, .25, 1)" }).onfinish = () => { body.hidden = true; };
          } else {
            body.hidden = false;
            stripes(body);
            if (!reduce) body.animate([{ height: "0px" }, { height: `${body.offsetHeight}px` }], { duration: 250, easing: "cubic-bezier(.25, .1, .25, 1)" });
          }
          return;
        }
        const header = event.target.closest("[data-sort]");
        if (!header) return;
        const key = header.dataset.sort;
        const table = header.closest("table")?.querySelector("[data-narrow]")?.dataset.narrow || "all";
        const mine = state.platform.sortBy?.[table];
        state.platform.sortBy = { ...(state.platform.sortBy || {}), [table]: mine?.key !== key ? { key, dir: 1 } : mine.dir > 0 ? { key, dir: -1 } : null };
        onChange();
      });
      Pie.bindSpecField?.(element, () => {
        const typing = document.activeElement?.matches?.("[data-alpha]");
        onChange();
        const input = element.querySelector("[data-alpha]");
        if (input && typing) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
      });
      element.addEventListener("click", (event) => {
        const mark = Pie.tapCard.isTouch() && event.target.closest("[data-tip]");
        if (mark) Pie.tapCard.toggle(mark, mark.dataset.tip, true);
      });
      const showCard = (mark, cx, cy) => {
        if (!mark) {
          tooltip.hidden = true;
          return;
        }
        tooltip.innerHTML = mark.dataset.tip;
        tooltip.classList.add("is-card");
        tooltip.hidden = false;
        const x = Math.min(cx + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(cy + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      };
      const markOf = (el) => el?.closest("[data-tip]") || el?.closest("td, th")?.querySelector(":scope > [data-tip], :scope > .platform-chip > [data-tip]") || null;
      element.addEventListener("pointermove", (event) => {
        if (event.pointerType !== "mouse") return;
        pointer = { x: event.clientX, y: event.clientY };
        showCard(markOf(event.target), event.clientX, event.clientY);
      });
      refreshCard = () => {
        if (!pointer || tooltip.hidden) return;
        const under = document.elementFromPoint(pointer.x, pointer.y);
        showCard(element.contains(under) ? markOf(under) : null, pointer.x, pointer.y);
      };
      window.addEventListener("resize", () => {
        const scroller = element.querySelector(".platform-scroll");
        if (scroller) element.style.setProperty("--platform-visible", `${scroller.clientWidth}px`);
      });
      element.addEventListener("pointerleave", (event) => {
        if (event.pointerType !== "mouse") return;
        pointer = null;
        tooltip.hidden = true;
        tooltip.classList.remove("is-card");
      });
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
