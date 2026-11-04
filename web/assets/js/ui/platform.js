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
  // the setups, picked from a pop-up in the bar and grouped by the kernel they measure: decode and prefill
  // run different kernels with different bottlenecks. Each group opens on its raw row (speculation off), held against
  // the hardware limit; the features under it are only those that change that phase, each shown as its gain over raw
  const MODES = [
    { id: "decode", group: "Decode", label: "Decode Latency", title: "Decode Latency", item: "Raw", icon: "M2 8h8M7 5l3 3-3 3M13 3v10", detail: "single request, speculation off", workload: "raw", metric: METRICS[0], limit: true },
    { id: "spec", group: "Decode", label: "Spec Decode", item: "Speculative", icon: "M2 8h5M5 5l3 3-3 3M9 8h5M12 5l3 3-3 3", detail: "single request, speculation on", workload: "spec", metric: METRICS[0] },
    { id: "prefill", group: "Prefill", label: "Prefill Latency", title: "Prefill Latency", item: "Raw", icon: "M3 4.5h10M3 8h10M3 11.5h6", detail: "single request, speculation off", workload: "raw", metric: METRICS[1], limit: true },
    { id: "batching", group: "Decode", label: "Decode Throughput", title: "Batched Decode Throughput", item: "Batched", icon: "M8 2.5l6 3-6 3-6-3zM2 8.5l6 3 6-3M2 11.5l6 3 6-3", detail: "32 requests at once", workload: "throughput", metric: { id: "throughput", label: "Throughput", key: "output_tok_s", unit: "tok/s", higher: true } },
    { id: "pbatch", group: "Prefill", label: "Prefill Throughput", title: "Batched Prefill Throughput", item: "Batched", icon: "M3 4.5h10M3 8h10M3 11.5h6", detail: "256 cold prompts at once, one token each", workload: "prefill_batch", metric: METRICS[1] },
  ];
  // the setups' segments show how much of the chip each pass fills, as a level fills: Decode one token at a time (a dot,
  // waiting on memory), Prefill the prompt's tokens in one row (a line, toward the compute roof but on some machines
  // still bound by memory), Peak FLOPs 32 requests' rows together (a block: the compute saturated)
  const mark = (x, y) => `<rect x="${x}" y="${y}" width="4.2" height="4.2" rx="1"/>`;
  const AT = [1, 5.9, 10.8];  // three places across, or down, 16 wide: cells large enough to read at 14px
  const DEGREE = {
    decode: mark(5.9, 5.9),
    spec: mark(3.45, 5.9) + mark(8.35, 5.9),  // the token and the draft checked with it
    prefill: AT.map((x) => mark(x, 5.9)).join(""),
    batching: AT.flatMap((y) => AT.map((x) => mark(x, y))).join(""),
    pbatch: [3.45, 8.35].flatMap((y) => AT.map((x) => mark(x, y))).join(""),  // many prompts' rows read together
  };
  // the setups as one segmented control, the grid's and the Roofline page's alike: each segment its degree and its name
  // the setups in two groups, each named in grey before it: Latency (one request at a time), then Throughput (many at
  // once); a segment says only its phase, Decode or Prefill, its full name in its tooltip
  const longSetupControl = (active, modes) => `<span class="platform-compare" role="group" aria-label="Setup">${modes.map((m, i) =>
    // the group's word only on the side that is picked (Latency or Throughput), so the switch says what it shows and stays short
    (m.id === "batching" ? `<span class="setup-divider" aria-hidden="true"></span>` : "") +
    (i === 0 && !["batching", "pbatch"].includes(active) ? `<span class="setup-group">Latency</span>` : "") +
    (m.id === "batching" && ["batching", "pbatch"].includes(active) ? `<span class="setup-group">Throughput</span>` : "") +
    `<button type="button" class="plain-button${m.id === active ? " is-active" : ""}" data-mode="${m.id}" aria-pressed="${m.id === active}" title="${esc(`${m.title || m.label}, ${m.id === "batching" ? "as many requests at once as the hardware needs to stay busy" : "one request"}`)}"><svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[m.id] || `<path d="${m.icon}"/>`}</svg>${esc(m.id === "spec" ? m.label : m.group)}</button>`).join("")}</span>`;
  // the setups take turns on their own, as a Smart Stack widget does: one every AUTO_MS, the numbers rolling up into the
  // next. Hovering the page pauses it; picking a setup stops it for good; no
  // turns for Reduce Motion or a tab in the background
  const AUTO_MS = 9000;
  const AUTO_ORDER = ["decode", "prefill", "batching", "pbatch"];
  const SETUP_NAMES = { decode: "Raw Decode", prefill: "Raw Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
  const stillMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const AUTO_KEY = "pieAutoTurns";  // the toolbar switch, kept per browser
  const auto = { stopped: localStorage.getItem(AUTO_KEY) === "off", paused: false, timer: null, started: 0, spent: 0, rolling: true };  // the first draw rolls in too, as the page opens
  const autoOn = () => !auto.stopped && !stillMotion.matches;
  // the setup as one button and its menu (Raw Decode, Raw Prefill, Batched Decode, Batched Prefill); a view with Spec keeps the long switch
  const setupControl = (active, modes) => {
    const ids = modes.map((m) => m.id);
    if (ids.includes("spec") || !ids.every((id) => ["decode", "prefill", "batching", "pbatch"].includes(id))) return longSetupControl(active, modes);
    // one button naming the setup with its mark, in the toolbar's view-button style; a click opens the four setups
    const NAMES = { decode: "Raw Decode", prefill: "Raw Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
    return `<span class="filter platform-setup"><button type="button" class="filter-button setup-pick label-rolls" data-grid-pick="setup" aria-haspopup="menu" title="Setup">${`<svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[active] || ""}</svg>`}<span>${esc(NAMES[active] || active)}</span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`;
  };
  let onChange = () => {};
  // after each draw: the numbers roll in if a turn drew them, and the next turn is set
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
  const afterDraw = () => {
    // a wave runs to its end: a redraw in the middle of it (a tag's data arriving, a second pick) picks it up where it
    // is, each cell's delay counted from the wave's start, rather than cutting it off or starting it again
    const now = performance.now();
    if (auto.rolling) {
      auto.rolling = false;
      clearTimeout(auto.waveTimer);
      auto.wave = { start: now, ghosts: auto.ghosts || [], longest: 0 };
      auto.ghosts = null;
      // the setup button's old name rolls up and out as the new one rises into its place
      const pick = element.querySelector(auto.labelOf || ".setup-pick");
      if (pick && auto.label) {
        pick.insertAdjacentHTML("afterbegin", `<span class="label-ghost" aria-hidden="true">${auto.label}</span>`);
        pick.classList.add("is-relabel");
        setTimeout(() => { pick.classList.remove("is-relabel"); pick.querySelector(".label-ghost")?.remove(); }, 1000);
      }
      auto.label = null;
    }
    const wave = auto.wave;
    if (wave) {
      const elapsed = now - wave.start;
      // a diagonal wave from the top-left cell to the bottom-right: each cell starts a step after the one above and left of it
      let longest = 0;
      for (const table of element.querySelectorAll(".platform-table")) {
        const rows = [...table.tBodies[0]?.rows || []];
        const span = rows.length + (rows[0]?.cells.length || 0);
        const step = Math.min(70, 1800 / Math.max(1, span));  // slow: the wave takes up to about two seconds
        rows.forEach((tr, r) => [...tr.cells].forEach((td, c) => {
          const wait = Math.round((r + c) * step);
          td.style.setProperty("--roll-wait", `${Math.round(wait - elapsed)}ms`);
          longest = Math.max(longest, wait);
        }));
      }
      wave.longest = Math.max(wave.longest, longest);
      // the old number in each cell leaves on the same beat, just ahead of the new one
      element.querySelectorAll(".platform-table").forEach((table, t) => [...(table.tBodies[0]?.rows || [])].forEach((tr, r) => [...tr.cells].forEach((td, c) => {
        const old = wave.ghosts[t]?.[r]?.[c];
        const cell = td.querySelector(".platform-cell");
        if (!old?.html || !cell) return;
        if (old.pill) {
          if (cell.outerHTML === old.html) return;
          td.insertAdjacentHTML("beforeend", `<span class="roll-ghost is-pill" aria-hidden="true">${old.html}</span>`);
          return;
        }
        if (td.querySelector(".platform-main")?.innerHTML === old.html) return;
        cell.insertAdjacentHTML("beforeend", `<span class="roll-ghost" aria-hidden="true">${old.html}</span>`);
      })));
      element.classList.add("is-rolling");
      clearTimeout(auto.waveTimer);
      auto.waveTimer = setTimeout(() => {
        if (auto.wave !== wave) return;
        auto.wave = null;
        element.classList.remove("is-rolling");
        element.querySelectorAll(".roll-ghost").forEach((g) => g.remove());
      }, Math.max(0, wave.longest + 1300 - elapsed));  // the last cell: its wait, the new number's 320 ms start and its .8 s rise
    }
    element.classList.toggle("is-auto-paused", auto.paused);
    // the toolbar switch shows while this page's setups can turn, on while they do
    const sw = document.getElementById("auto-switch");
    if (sw) { sw.hidden = stillMotion.matches || !element.querySelector(".setup-pick"); showAuto(); }
    nextTurn();
  };
  document.getElementById("auto-switch")?.addEventListener("click", () => {
    auto.stopped = !auto.stopped;
    showAuto();
    auto.spent = 0;
    localStorage.setItem(AUTO_KEY, auto.stopped ? "off" : "on");
    if (auto.stopped) clearTimeout(auto.timer); else nextTurn();
  });
  const pauseTurns = (on) => {
    if (on === auto.paused) return;
    if (on) { clearTimeout(auto.timer); auto.spent += performance.now() - auto.started; }
    auto.paused = on;
    element.classList.toggle("is-auto-paused", on);
    if (!on) nextTurn();
  };
  // paused while the pointer is on the tables or the setup controls, where someone is reading or about to pick
  element.addEventListener("pointermove", (event) => pauseTurns(Boolean(event.target.closest(".platform-scroll, .platform-setup"))));
  element.addEventListener("pointerleave", () => pauseTurns(false));
  document.addEventListener("visibilitychange", () => pauseTurns(document.hidden));
  // the numbers on screen before a turn redraws them, cell by cell, to fade out in the same wave as the new ones rise
  const captureGhosts = (button = ".setup-pick") => {
    // the picked button's mark and name (the setup's, or the view's), to roll up and away as the next one's roll in, as SwiftUI's numeric text does
    const pick = element.querySelector(button);
    auto.labelOf = button;
    auto.label = pick ? [...pick.children].filter((el) => !el.classList.contains("popup-chevron")).map((el) => el.outerHTML).join("") : null;
    // an Overall cell leaves whole, its coloured capsule with it; a model cell leaves its number
    auto.ghosts = [...element.querySelectorAll(".platform-table")].map((t) => [...(t.tBodies[0]?.rows || [])].map((tr) => [...tr.cells].map((td) =>
      (td.classList.contains("is-overall") ? { pill: true, html: td.querySelector(".platform-cell")?.outerHTML || "" } : { html: td.querySelector(".platform-main")?.innerHTML || "" }))));
  };
  // the viewer's own pick ends the turns
  const stopTurns = () => { auto.stopped = true; auto.spent = 0; clearTimeout(auto.timer); showAuto(); };
  // the toolbar button: pause while the setups turn, play while they rest
  function showAuto() {
    const sw = document.getElementById("auto-switch");
    if (!sw) return;
    sw.setAttribute("aria-pressed", String(!auto.stopped));
    sw.title = auto.stopped ? "Play" : "Pause";
    sw.setAttribute("aria-label", auto.stopped ? "Turn the setups automatically" : "Pause the setups' turn");
  }
  let openResults = () => {};

  // the platforms machines belong to, in the order the page lists them; Apple's logo is the simple-icons glyph (CC0)
  const PLATFORMS = [
    { id: "mac", label: "Apple Silicon", sub: "Metal", has: (hw) => Pie.platformOf(hw) === "mac" },
    { id: "nvidia", label: "NVIDIA GPU", sub: "CUDA", has: (hw) => Pie.platformOf(hw) === "nvidia" },
    { id: "amd", label: "AMD GPU", sub: "ROCm", has: (hw) => Pie.platformOf(hw) === "amd" },
    { id: "tpu", label: "Google TPU", sub: "Per slice", has: (hw) => Pie.platformOf(hw) === "tpu" },
    { id: "cerebras", label: "Cerebras", sub: "CSL", has: (hw) => Pie.platformOf(hw) === "cerebras" },
    { id: "android", label: "Mobile", sub: "Mobile GPU", has: (hw) => Pie.platformOf(hw) === "android" },
    { id: "web", label: "Browser", sub: "WebGPU", has: (hw) => Pie.platformOf(hw) === "web" },
  ];
  const platformOf = (hw) => PLATFORMS.find((p) => p.has(hw));
  // a platform's mark is the sidebar's: the same tinted squircle and glyph wherever it appears
  // a platform's scroll bar shows while its table scrolls and a moment after, then hides, as macOS's overlay scrollers do
  const hideAfter = new WeakMap();
  document.addEventListener("scroll", (event) => {
    const scroller = event.target;
    if (!scroller.classList?.contains("platform-section-scroll")) return;
    scroller.classList.add("is-scrolling");
    clearTimeout(hideAfter.get(scroller));
    hideAfter.set(scroller, setTimeout(() => scroller.classList.remove("is-scrolling"), 900));
  }, { capture: true, passive: true });
  // a miniature's striped cells draw their lines from the table's corner, not their own, so the lines run on unbroken from
  // cell to cell and move with the table as it scrolls
  const stripes = (root) => root.querySelectorAll("td:has(> .platform-cell.is-mini)").forEach((td) => {
    td.style.backgroundPosition = `${-td.offsetLeft}px ${-td.offsetTop}px`;
  });
  const badgeOf = (id) => `<span class="sidebar-glyph" style="--tint: ${Pie.schema[id]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(id)}</span>`;

  // a model's maker as a small app icon: its logo on a white tile (logos from LobeHub's icon set, MIT)
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
  // a miniature (nemotron-3-ultra-mini8) has no catalog family: its id names the maker
  const makerOf = (model) => { const id = model.split("~")[0]; const family = Pie.store.index.models[id]?.family || id.replace(/-/g, "_"); return MAKERS.find((m) => m.test.test(family)) || { name: "", logo: "" }; };
  // each maker's colour, taken from its logo, for the dot before its name in the makers menu; a black logo reads grey
  const MAKER_TINT = { Alibaba: "#615ced", DeepSeek: "#4d6bfe", Google: "#4285f4", Meta: "#0866ff", OpenAI: "#10a37f", Xiaomi: "#ff6900", "Z.ai": "#8e8e93", Moonshot: "#8e8e93", Tencent: "#0055e9", MiniMax: "#e73562", NVIDIA: "#76b900" };
  // a model with no maker logo in the set runs in the cloud: a cloud glyph on its tile
  const CLOUD = '<svg class="model-cloud" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 12.5a3 3 0 0 1-.4-6A4 4 0 0 1 11.8 6a3.25 3.25 0 0 1 .2 6.5z"/></svg>';
  const badge = (maker) => `<span class="model-badge" aria-hidden="true">${maker.logo ? `<img src="assets/img/models/${maker.logo}.svg" alt="">` : CLOUD}</span>`;

  const chipName = (id) => String(Pie.store.index.hardware[id]?.name || id).replace(/^Apple\s+/, "");
  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    return hw ? `${chipName(id)}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}` : id;
  };
  // "48 GB · 20-core GPU · 273 GB/s" on a quiet second line under the chip, the specs that set LLM speed; the CPU waits for the hover
  // a machine's row says only what tells it from its namesakes, its memory, as Apple lists a Mac; the full spec sheet
  // shows when the pointer rests on it, and grows as the catalog does (interconnect, power, more) without crowding the row
  const specOf = (hw) => (hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : "");
  const LINKS = { uma: "Unified memory", nvlink: "NVLink", pcie: "PCIe", tb5: "Thunderbolt 5" };
  const specSheet = (hw) => {
    const rows = [
      ["Memory", hw.memory_gib && `${hw.memory_gib} GB`],
      ["Bandwidth", hw.bandwidth_gbs && `${hw.bandwidth_gbs} GB/s`],
      ["GPU", hw.gpu_cores && `${hw.gpu_cores} cores`],
      ["CPU", hw.cpu_cores && `${hw.cpu_cores} cores`],
      ["Compute", hw.tflops_fp16 && `${hw.tflops_fp16} TFLOPS fp16`],
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
  const EVEN = 0.045;  // under 5%, as the cell rounds it, the engines are even: run-to-run spread, not a result
  // the 2026-10-26 miniature run: these models on these machines are being measured now; an empty cell among them is
  // pending, not missing (a local preview mark, until the run's last results land)
  const TODAY = {
    models: new Set(["deepseek-v4.1-flash", "glm-5.3-flash", "kimi-k3", "glm-5.3", "hy4-preview", "mimo-v2.6-flash-rl", "qwen3.8-flash-next",
      "muse-spark-open-816b-a42b", "nvidia-nemotron-3-ultra-550b-a55b", "minimax-m3.1-flash"]),
    // only machines the run can still fill: B300 and MI300X have no RunPod stock, pie's TPU engine serves none of these
    // models
    hardware: new Set(["h200-x1", "b200-x1", "pro6000-x1", "a100-sxm-x1", "h100-sxm-x1", "a40-x1", "l40s-x1", "rtx5090-x1", "rtx4090-x1"]),
  };
  const PENDING = '<svg class="platform-pending" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/><path d="M8 4.8V8l2.2 1.6"/></svg>';
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>';  // the slice mark's square, in its corner too
  const signed = (p) => {
    const pct = Math.round(p * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  // pie's advantage over the best other engine: a speed ratio, or the inverse for a time
  // Compare: "engines", named Speedup, shows each engine against the best other engine; "ceiling", named Efficiency, shows each engine's
  // share of its theoretical bound, the card drawing the roofline. The last choice is kept per browser
  const COMPARES = { engines: "Relative Speed", ceiling: "Kernel Efficiency", tps: "Tokens per Second" };
  // the views as Speed's switch names them, in its order: Relative first
  const SHORT_COMPARES = { engines: "Relative", tps: "Tokens per Second", ceiling: "Efficiency" };
  // each view wears the icon of the sidebar page that shows it for every machine
  const COMPARE_ICONS = { engines: "speedups", ceiling: "all_hardware", tps: "tps" };
  // each view's symbol, in its menu row and on the button when picked: a gear for Relative Speed, the solid rack for Tokens per Second, the f for Kernel Efficiency
  const viewIcon = (id) => `<svg class="view-icon" viewBox="0 0 24 24" aria-hidden="true">${id === "engines" ? '<g transform="scale(1.5)" stroke-width="1.2"><path stroke-linejoin="round" d="M14.15 6.63L14.15 9.37L12.81 8.94L12.06 10.74L13.32 11.38L11.38 13.32L10.74 12.06L8.94 12.81L9.37 14.15L6.63 14.15L7.06 12.81L5.26 12.06L4.62 13.32L2.68 11.38L3.94 10.74L3.19 8.94L1.85 9.37L1.85 6.63L3.19 7.06L3.94 5.26L2.68 4.62L4.62 2.68L5.26 3.94L7.06 3.19L6.63 1.85L9.37 1.85L8.94 3.19L10.74 3.94L11.38 2.68L13.32 4.62L12.06 5.26L12.81 7.06z"/><circle cx="8" cy="8" r="2"/></g>' : id === "tps" ? '<path class="is-filled" fill-rule="evenodd" d="M4.5 2.5h15A2 2 0 0 1 21.5 4.5v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V5.5zM4.5 12.5h15a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V15.5z"/>' : Pie.icons[COMPARE_ICONS[id]]}</svg>`;
  const nextCompare = (id) => { const ids = Object.keys(COMPARES); return ids[(ids.indexOf(id) + 1) % ids.length]; };
  // what the numbers in each view mean, as the help tag on its segment: a Mac explains a control where it is
  const CAPTIONS = {
    engines: "Speedup over the fastest other engine",
    ceiling: "Share of the hardware's theoretical peak",
    tps: "The engine's own speed",
  };
  // the view the viewer picked with the view button or V, kept across pages and reloads; Relative Speed until they pick.
  // The Kernel Efficiency, Relative Speed and Best TPS pages each show their own view without touching the pick
  const saved = (() => { try { return localStorage.getItem("platformCompare"); } catch { return null; } })();
  let chosen = COMPARES[saved] ? saved : "engines";
  let compare = chosen;
  // the theoretical bound for a cell: Raw's hardware limit, or for batched decode the lower of compute and bandwidth
  const boundOf = (mac, model, mode, metric, pie) => {
    if (mode.limit) return Pie.ceiling?.(pie, metric.id) || null;
    // Spec Decode: the best draft width at the Roofline page's acceptance
    if (mode.id === "spec") return (pie && Pie.specCeiling?.(pie)) || null;
    if (mode.workload !== "throughput") return null;
    return batchedBound(mac, model, pie?.scheme);
  };
  // batched decode: the lower of two bounds, in output tokens per second. Compute: peak FLOPS over the active parameters,
  // shared with the prompt tokens each request prefills at the same cost, so only output / (prompt + output) of it is output.
  // Bandwidth: each step reads the weights once, so the batch's tokens per second are batch x bandwidth / weight bytes.
  function batchedBound(mac, model, scheme) {
    // the architecture-based bound (methodology.js), the same one the Methods page explains
    return Pie.batchedCeiling?.(mac, model, scheme) || null;
  }
  // pie against the opponent picked in the bar, or the strongest other engine on the cell when none is picked
  const cell = (rows, metric, base, rival) => {
    const pie = rows.find((r) => r.engine === base && r[metric.key]);
    const others = rows.filter((r) => r.engine !== base && r[metric.key]);
    if (!pie) return null;
    const rivals = rival ? others.filter((r) => r.engine === rival) : others;
    // a machine where only pie runs (a TPU today) still shows pie's own number, with nothing to compare it to
    if (!rivals.length) return { pie, best: null, gain: null, all: [pie, ...others] };
    const best = rivals.reduce((a, b) => ((metric.higher ? b[metric.key] > a[metric.key] : b[metric.key] < a[metric.key]) ? b : a));
    const gain = metric.higher ? pie[metric.key] / best[metric.key] - 1 : best[metric.key] / pie[metric.key] - 1;
    return { pie, best, gain, all: [pie, ...others] };
  };

  // each engine's share of the hardware limit, against its own weights (Raw only: a drafter skips the passes the limit counts)
  const share = (r, metric) => {
    const own = r.workload === "spec" ? Pie.specCeiling?.(r) : Pie.ceiling?.(r, metric.id);
    return own ? r[metric.key] / own.tps : null;
  };
  // what a feature adds: the engine's number over its raw row on the same machine and model
  const overRaw = (r, metric, raw) => {
    const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine);
    const key = metric.id === "throughput" ? "output_tok_s" : metric.key;
    return plain?.[key] ? r[metric.key] / plain[key] : null;
  };
  const times = (x) => `${x >= 10 ? Math.round(x) : x.toFixed(1)}×`;

  // under the comparison, a quiet second line on the feature views: what the feature adds over raw
  const subline = (c, metric, mode, raw) => {
    // Raw cells hold one number; how near the hardware limit each engine runs is in the hover card
    if (mode.limit) return "";
    const gain = overRaw(c.pie, metric, raw);
    // a row that did not speculate reads its own raw speed: nothing to add
    return "";  // the multiplier under the percentage is not shown
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
  let lastAll = null;  // the release's rows, every status, for the hover cards
  // the engines with no number in a cell, each with why: not supported, does not fit, failed (its error), not measured yet
  const WHY = { unsupported: "Not supported", no_fit: "Does not fit", fail: "Failed", not_run: "Not measured yet", no_data: "Not measured yet" };
  const absentRows = (mac, model, mode, order) => {
    // only an engine that says why it gave nothing; one not measured yet is left out, as anything unnamed is
    const others = (lastAll || []).filter((r) => r.hardware === mac && r.model === model && r.workload === mode.workload && !order.some((o) => o.engine === r.engine) && ["unsupported", "no_fit", "fail"].includes(r.status));
    return [...new Map(others.map((r) => [r.engine, r])).values()].map((r) => `<div class="tip-row is-absent"${r.note ? ` title="${esc(r.note)}"` : ""}><span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}</span>
      <span class="tip-value">${esc(WHY[r.status] || "Not measured yet")}</span><span class="tip-when"></span></div>`);
  };
  const tip = (mac, model, metric, c, mode, raw) => {
    const limit = mode.limit;
    const ceiling = limit ? Pie.ceiling?.(c.pie, metric.id) : null;
    const batchBound = !limit && mode.workload === "throughput" ? batchedBound(mac, model, c.pie.scheme) : null;
    const batchPeak = batchBound ? batchBound.tps : null;
    // Spec Decode: the limit at the best draft width for this machine and model, at the bar's acceptance
    const specBound = mode.id === "spec" ? Pie.specCeiling?.(c.pie) : null;
    // Spec Decode in Efficiency: what drafting added to each engine's own Raw speed, or cost it
    const specGain = (r) => {
      const plain = raw.find((x) => x.hardware === r.hardware && x.model === r.model && x.engine === r.engine)?.[metric.key];
      if (!plain) return esc(value(r[metric.key], metric.unit));
      const delta = r[metric.key] - plain;
      const sign = delta >= 0 ? "+" : "−";
      return `<span class="tip-delta ${delta >= 0 ? "is-up" : "is-down"}">${sign}${esc(value(Math.abs(delta), metric.unit))}</span>`;
    };
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    // a miniature's tok/s is a cut model's, no real model's speed: its card reads each engine against pie, and the
    // fastest, never a rate or a bound
    const mini = Boolean(c.pie.miniature);
    // each engine as a share of Pie's speed, pie at 100%, as the cells speak in percents
    const relative = (r) => `${Math.round((metric.higher ? r[metric.key] / c.pie[metric.key] : c.pie[metric.key] / r[metric.key]) * 100)}%`;
    // Engines compares the engines only; Roofline adds each one's share of the bound, the bounds and the chart
    const roofline = compare === "ceiling" && !mini;
    const lines = order.map((r, i) => {
      // Raw: each engine's share of the hardware limit; the others: what the feature adds over its raw row
      const extra = !roofline ? null : limit ? share(r, metric) : specBound ? r[metric.key] / specBound.tps : batchPeak ? r[metric.key] / batchPeak : overRaw(r, metric, raw);
      const note = extra === null ? "" : limit || batchPeak || specBound ? `${Math.round(extra * 100)}%` : times(extra);
      return `<div class="tip-row${r === c.pie ? " is-pie" : ""}"${r === c.pie ? ` style="color: ${Pie.engines.colorOf(r.engine)}"` : ""}>
      <span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}${i === 0 ? '<span class="tip-tag">Fastest</span>' : ""}</span>
      <span class="tip-value">${mini ? esc(relative(r)) : specBound && roofline ? specGain(r) : `${esc(value(r[metric.key], metric.unit))}${roofline ? `<span class="tip-share">${note}</span>` : ""}`}</span><span class="tip-when">${esc(day(r))}</span></div>`;
    });
    // the cell's row and column already name the setup, and the bar above the metric: the card is only the engines
    // the hardware limit closes the list as one more row, aligned with the engines': its speed at 100%, and a tag for
    // what sets it (bandwidth, compute, or the interconnect between devices), as a table's summary row reads
    // both bounds are listed, lower first; the lower one is the limit, so only it carries the 100% the engines are measured against
    // one group under one rule, as a summary reads: the gauge marks the binding row only, the other row is plain and dimmed
    const limitRow = (name, tps, binds) => `<div class="tip-row is-limit${binds ? "" : " is-slack"}">
      ${binds ? '<svg class="tip-limit-mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 11.5a5.5 5.5 0 1 1 11 0M8 11.5l2.6-3.4"/></svg>' : "<span></span>"}<span class="tip-name" title="${binds ? "What sets the limit" : "Not the limit: the other bound is lower"}">${name} bound</span>
      <span class="tip-value">${esc(value(tps, metric.unit))}</span><span class="tip-when"></span></div>`;
    // every bound the machine has, lowest first: memory bandwidth, compute, and the link between GPUs when there are several
    const bounds = (b) => [["Bandwidth", b.bandwidth], ["Compute", b.compute], ["Interconnect", b.interconnect]].filter(([, tps]) => tps).sort((x, y) => x[1] - y[1]);
    // Roofline complements Engines: no engine list, only the bounds and the chart, the engines as dots in their colours
    const both = roofline && (ceiling || batchBound);
    if (both) {
      // both bounds side by side, as a pair of stats: a small label over each number, memory first as the chart reads
      // left to right; the lower one is the limit, bright, the other dimmed
      // the two bounds as rows, the one that sets the limit first with the gauge, the other dimmed under it
      const head = `<div class="tip-rows">${bounds(both).map(([name, tps], i) => limitRow(name, tps, i === 0)).join("")}</div>`;
      return `<div class="rf-card">${head}${roofCard(order.map((r) => roofPoint(r, mode, metric)).filter(Boolean))}</div>`;
    }
    if (specBound && roofline) lines.push(`<div class="tip-row is-limit">
      <svg class="tip-limit-mark" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 11.5a5.5 5.5 0 1 1 11 0M8 11.5l2.6-3.4"/></svg><span class="tip-name" title="The limit at the best draft width, at ${Pie.specAlpha}% acceptance">Spec Limit</span>
      <span class="tip-value">${esc(value(specBound.tps, metric.unit))}</span><span class="tip-when"></span></div>`);
    // Spec Decode in Kernel Efficiency: the roofline over the list, the picked engine's Raw run and its speculative one as
    // two dots, an arrow from the first to the second: drafting reads the weights once for several tokens, so the pass
    // moves right along the roof, and up by what it kept
    // the engines with no number here say why, in grey under the measured ones: not supported, does not fit, failed, or
    // not measured yet, so one engine alone reads as the only one that could run, or the only one run so far
    lines.push(...absentRows(mac, model, mode, order));
    if (specBound && roofline) {
      const moved = specMove(order, raw, specBound);
      if (moved) return `<div class="rf-move-card">${roofCard(moved, { move: true })}${card("", "", lines)}</div>`;
    }
    // a miniature's card says so at its head, in place of the browser's own tooltip that would cover it
    return mini ? card("Model slice", c.pie.miniature, lines) : card("", "", lines);
  };

  // a result on the roofline model (Williams et al., 2009): its pass's arithmetic intensity, the FLOPs it does per byte
  // it reads, and the FLOPs a second it achieved; and its machine's roof, memory bandwidth and peak FLOPS
  const roofPoint = (r, mode, metric) => {
    if (!r?.[metric.key] || mode.id === "spec") return null;
    if (mode.limit) {
      const c = Pie.ceiling?.(r, metric.id);
      if (!c?.parts.tflops) return null;  // a machine without a FLOPS figure has no intensity to place it at
      const flops = c.parts.mathS * c.parts.tflops * 1e12;
      const bytes = (c.parts.weightGB + c.parts.cacheGB) * 1e9;
      // several GPUs: the link between them caps the FLOPs a second this pass can reach, whatever its intensity
      return { r, ai: flops / bytes, achieved: (r[metric.key] / c.parts.tokens) * flops, bw: c.parts.bw, peak: c.parts.tflops,
        link: c.parts.linkS ? flops / c.parts.linkS : null };
    }
    // the machine's numbers as the bound used them: the catalog's, or its estimate where the catalog has none
    const b = Pie.batchedCeiling?.(r.hardware, r.model, r.scheme);
    if (!b?.parts.tflops) return null;
    const { bw, tflops } = b.parts;
    const flops = b.parts.mathS * tflops * 1e12;
    const bytes = b.parts.readS * bw * 1e9;
    return { r, ai: flops / bytes, achieved: (r[metric.key] / b.parts.requests) * flops, bw, peak: tflops,
      link: b.parts.linkS ? flops / b.parts.linkS : null };
  };

  // Spec Decode's two points for the picked engine (pie unless another is picked): its Raw pass where the grid places it,
  // and its speculative pass at the intensity of the best draft width (k drafted tokens and the one after them checked
  // in one read of the weights), each at its own share of its own limit, so the dots' heights match the grid's numbers
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

  // the card's roofline, a picture rather than a plot: the roof one line over a soft fade, the knee a ring named
  // beside it, each engine a dot in its own colour, pie on top; no axes, since the shape is the point
  const roofCard = (found, { move = false } = {}) => {
    let points = found;
    if (!points.length) return "";
    const { bw, peak } = points[0];
    const knee = (peak * 1e12) / (bw * 1e9);
    // one model, one workload: every engine stands at the same place across, pie's (the first engine's when pie has
    // none); a dot's height is its share of its own bound, so it matches the percentage the grid shows for it
    const focus = viewState?.platform.engine || Pie.engines.primary;  // the engine picked in the bar
    const own = points.find((p) => p.r.engine === focus) || points[0];
    const ai = own.ai;
    // the interconnect, when it binds, is a flat line under the roof: a dot is measured against the lowest bound
    const link = own.link && own.link < Math.min(bw * 1e9 * ai, peak * 1e12) ? own.link : null;
    const shareOf = (p) => p.achieved / Math.min(p.bw * 1e9 * p.ai, p.peak * 1e12, p.link || Infinity);
    // a move keeps each pass at its own intensity; otherwise every engine stands at the picked one's
    points = points.map((p) => ({ ...p, ai: move ? p.ai : ai, achieved: shareOf(p) * Math.min(bw * 1e9 * (move ? p.ai : ai), peak * 1e12, link || Infinity) }));
    const ais = move ? points.map((p) => p.ai) : [ai];
    // both axes linear. Across, a window around the dots; up, always from zero to just over the roof, so a dot's height
    // is its share of the bound. The knee and the compute roof show only when the window reaches them
    const aiLo = Math.min(...ais), aiHi = Math.max(...ais);
    const X0 = aiLo * 0.6;
    const X1 = aiHi * 1.4;
    // a dot's distance below the roof is its share of it: at 55% it sits about halfway between the floor and the roof
    const Y1 = Math.max(Math.min(bw * 1e9 * X1, peak * 1e12), ...points.map((p) => p.achieved)) * 1.06;
    const Y0 = 0;
    const W = 196, H = 80, L = 2, R = 2, T = 14, B = 2;  // about the card's own width, so the dots and the name keep their size
    const x = (v) => L + ((v - X0) / (X1 - X0)) * (W - L - R);
    const y = (v) => T + (1 - (v - Y0) / (Y1 - Y0)) * (H - T - B);
    const roof = (v) => Math.min(bw * 1e9 * v, peak * 1e12);
    const start = X0;
    // every dot exactly where its result is, never nudged: each engine the same small solid dot in its colour, ringed
    // in the card's colour so dots stay apart; the picked engine in its colour, drawn last and the only one named, the
    // others grey, as Stocks greys the series not in focus
    const at = (p) => `cx="${x(p.ai).toFixed(1)}" cy="${y(p.achieved).toFixed(1)}"`;
    const isPie = (p) => p.r.engine === focus && !p.ghost;
    // the chart stretches with the card, but its marks keep their size on screen: the line keeps its weight
    // (non-scaling stroke), each dot is a round cap of a zero-length line (so it stays 7px across, as the Engines card's
    // dots), and the names are HTML laid over the chart at the right place, at the card's own type size
    const point = (cx, cy, cls, color = "") => `<line class="${cls}" x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy}"${color ? ` stroke="${color}"` : ""}/>`;
    const dots = [...points.filter((p) => !isPie(p)), ...points.filter(isPie)]
      .map((p) => point(x(p.ai).toFixed(1), y(p.achieved).toFixed(1), isPie(p) ? "rf-dot" : "rf-dot is-other", isPie(p) ? Pie.engines.colorOf(p.r.engine) : "")).join("");
    const pct = (vx, vy) => `left: ${((vx / W) * 100).toFixed(2)}%; top: ${((vy / H) * 100).toFixed(2)}%`;
    // no engine is named on the chart: the picked one is the dot in its colour, and the list under it names them all
    const shown = knee > X0 && knee < X1;  // the knee, only when it falls inside the window
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

  // where the mouse last was over the grid, and how to redraw the card there after the grid redraws
  let pointer = null;
  let peeked = null;  // the chosen view while R is held, so it can come back
  let refreshCard = () => {};
  let viewState = null;  // the state the grid last drew, for the engine menu
  // model sizes, by total parameters as the catalog states them: the filter bar narrows the columns to a few at once
  const SIZES = [
    { id: "small", label: "Under 10B", test: (b) => b < 10 },
    { id: "medium", label: "10B to 40B", test: (b) => b >= 10 && b < 40 },
    { id: "large", label: "40B to 200B", test: (b) => b >= 40 && b < 200 },
    { id: "datacenter", label: "200B and up", test: (b) => b >= 200 },
  ];
  const paramsOf = (id) => (Pie.store.tables.models || []).find((m) => m.id === id)?.params_b;
  const sizeOf = (id) => { const b = paramsOf(id); return b == null ? null : SIZES.find((sz) => sz.test(b))?.id; };
  let pageMakers = [];  // the makers with a result on the page the grid last drew
  let pageModels = [];  // the models with a result on the page the grid last drew
  // a model's group in the Models menu: its maker, its size band, or Local (it fits a 128 GB Mac) and Cloud
  const groupOf = (id, by) => {
    const m = (Pie.store.tables.models || []).find((x) => x.id === id) || {};
    if (by === "size") return SIZES.find((sz) => sz.id === sizeOf(id))?.label || "Unknown size";
    if (by === "where") return m.needs_gib != null && m.needs_gib <= 128 ? "Local" : "Cloud";
    return makerOf(id).name || "Cloud";
  };
  let pagePlatforms = [];  // the platforms with a result in the setup the grid last drew

  Pie.platform = {
    // the next draw's numbers roll in, as a turn's do: a page drawn after its outline (boot/skeleton.js)
    roll() { auto.rolling = true; },

    refreshCard: () => refreshCard(),
    badge: (id) => badgeOf(id),
    // a model's card, as the Speed pages' model heads show it on hover
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

    // the Compare choice, kept per browser: "engines" or "ceiling"
    compare: () => compare,
    // a peek: while R is held the grid shows the other view; letting go returns to the chosen one, which a peek
    // never changes or saves
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
    // the setup control for another page, over the setups named, and a way to say a pick changed the setup
    setupControl: (active, ids) => setupControl(active, ids.map((id) => MODES.find((m) => m.id === id)).filter(Boolean)),
    changed: () => onChange(),
    // a model's maker as the grid draws it (its logo on a white tile), for other menus that name a model
    makerBadge: (model) => badge(makerOf(model)),
    makerName: (model) => makerOf(model).name || "Cloud",  // the band a model sits under in the grids
    // a setup's degree mark (one square for Decode, three for Prefill), for other controls that name a setup
    degree: (id) => `<svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[id] || ""}</svg>`,
    setCompare(value) {
      peeked = null;
      compare = chosen = COMPARES[value] ? value : "engines";
      try {
        localStorage.setItem("platformCompare", compare);
      } catch {
        // private windows can refuse storage
      }
    },

    // how many machines a platform has on the site (all platforms when none is named)
    machines(id) {
      return Pie.store.tables.hardware.filter((hw) => { const p = platformOf(hw); return p && (!id || p.id === id); }).length;
    },

    // the setups, for the pop-up in the bar. Raw Decode and Raw Prefill always; on a platform page, a feature beyond
    // raw (Speculative, Batched) only where this release measured it on one of the platform's machines. Roofline, with
    // no platform, keeps every chapter
    metrics(state) {
      if (!state || Pie.schema[state.table]?.view !== "platform") return MODES;
      const only = Pie.schema[state.table]?.platform;
      const ran = new Set(Pie.store.snapshot(state.release)
        .filter((r) => Pie.store.isMeasured(r) && (!only || platformOf(Pie.store.index.hardware[r.hardware] || {})?.id === only))
        .map((r) => r.workload));
      // the TPU shows Raw Decode and Raw Prefill only
      const HIDDEN = { tpu: ["spec", "batching", "pbatch"] };
      // Spec Decode lives in Raw Decode, a column beside each model it ran: no button of its own
      return MODES.filter((m) => m.id !== "spec" && (m.limit || m.id === "pbatch" || ran.has(m.workload)) && !(HIDDEN[only] || []).includes(m.id));
    },

    onChange(handler) {
      onChange = handler;
    },
    // a measured cell's click: the Results page, filtered to that run
    onOpenResults(handler) {
      openResults = handler;
    },
    // the engine menu: every engine, the picked one checked
    menu(k) {
      if (k === "platform" && viewState) {
        // All Platforms, then each platform with a result here, several at once
        const current = viewState.platform.platforms || [];
        const ids = PLATFORMS.map((pl) => pl.id).filter((id) => pagePlatforms.includes(id) || current.includes(id));
        return [{ value: "", label: "All Platforms", selected: !current.length }, { separator: true },
          ...ids.map((id) => ({ value: id, label: Pie.schema[id]?.short || id, selected: current.includes(id), check: true, dot: Pie.schema[id]?.tint }))];
      }
      if (k === "model" && viewState) {
        // All Models, then its groups and under each its models, smallest first; several can be checked at once, and a
        // group's row checks or clears all of its models
        // none picked shows them all, so every model is checked until one is cleared
        const picked = viewState.platform.models || [];
        const ids = [...new Set([...pageModels, ...picked])];
        const current = picked.length ? picked : ids;
        const by = viewState.platform.modelGroup || "maker";
        const groups = {};
        for (const id of ids) (groups[groupOf(id, by)] ||= []).push(id);
        const order = by === "maker" ? Object.keys(groups).sort() : by === "size" ? [...SIZES.map((sz) => sz.label), "Unknown size"] : ["Local", "Cloud"];
        // how the list groups, as Finder's Group By: one pick, the rest of the menu under it
        return [...[["maker", "By Maker"], ["size", "By Size"], ["where", "Local and Cloud"]].map(([id, label]) => ({ value: `by:${id}`, label, selected: by === id })),
          ...order.filter((name) => groups[name]).flatMap((name) => {
            const list = groups[name].sort((a, b) => (paramsOf(a) ?? Infinity) - (paramsOf(b) ?? Infinity) || names().model(a).localeCompare(names().model(b)));
            return [{ separator: true },
              { value: `group:${name}`, label: name, selected: list.every((id) => current.includes(id)), check: true, icon: by === "maker" ? badge(MAKERS.find((m) => m.name === name) || { logo: "" }) : "" },
              ...list.map((id) => ({ value: id, label: names().model(id), detail: paramsOf(id) ? `${paramsOf(id)}B` : "", selected: current.includes(id), check: true, indent: true, icon: badge(makerOf(id)) }))];
          })];
      }
      if (k === "maker" && viewState) {
        // All Makers, then under a separator every maker with a result on the page, each checked while shown; several
        // can be checked at once, as a Finder tag menu checks several tags
        const current = viewState.platform.makers || [];
        const makers = [...new Set([...pageMakers, ...current])].sort();
        return [{ value: "", label: "All Makers", selected: !current.length }, { separator: true },
          // each maker after its logo, as the grid heads its columns
          ...makers.map((name) => ({ value: name, label: name, selected: current.includes(name), check: true, icon: badge(MAKERS.find((m) => m.name === name) || { logo: "" }) }))];
      }
      if (k === "size" && viewState) {
        // All Sizes, then each size band, several at once, as the makers menu checks several makers
        const current = viewState.platform.sizes || [];
        return [{ value: "", label: "All Sizes", selected: !current.length }, { separator: true },
          ...SIZES.map((sz) => ({ value: sz.id, label: sz.label, selected: current.includes(sz.id), check: true }))];
      }
      if (k === "rival" && viewState) {
        // the strongest other engine on each cell, then each other engine with its dot, as the catalog marks it
        const base = viewState.platform.engine || Pie.engines.primary;
        const current = viewState.platform.rival !== base ? viewState.platform.rival || "" : "";
        return [{ value: "", label: "Strongest", selected: !current }, { separator: true },
          ...Pie.store.tables.engines.filter((e) => e.id !== base).map((e) => ({ value: e.id, label: Pie.store.names.engine(e.id), selected: e.id === current, dot: Pie.engines.colorOf(e.id) }))];
      }
      // the setup menu: the four setups, each after its mark, as the button shows the picked one
      if (k === "setup" && viewState) {
        const NAMES = { decode: "Raw Decode", prefill: "Raw Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
        const picked = viewState.platform.mode || "decode";
        return ["decode", "prefill", "batching", "pbatch"].map((id) => ({ value: id, label: NAMES[id], selected: id === picked, detail: id === "decode" || id === "prefill" ? "Latency" : "Throughput", icon: `<svg class="mode-icon" viewBox="0 0 16 16" aria-hidden="true">${DEGREE[id]}</svg>` }));
      }
      // the bar's one settings menu, as a Mac toolbar's View Options: the view, then pie's engine, then whom it is set against
      if (k === "options" && viewState) {
        const own = (key, items) => items.map((o) => (o.separator ? o : { ...o, key: `grid:${key}` }));
        const fixedView = Pie.schema[viewState.table]?.compare;
        return [
          ...(fixedView ? [] : [{ heading: "View" }, ...own("view", ["engines", "tps", "ceiling"].map((id) => ({ value: id, label: COMPARES[id], selected: id === compare, icon: viewIcon(id) }))), { separator: true }]),
          // the engine and its opponent are one row each, the pick in grey, their lists to the side, as Finder's View menu nests its Sort By
          { label: "Engine", detail: Pie.store.names.engine(viewState.platform.engine || Pie.engines.primary), submenu: own("engine", this.menu("engine")) },
        ];
      }
      if (k !== "engine" || !viewState) return [];
      const current = viewState.platform.engine || Pie.engines.primary;
      // each engine with its dot, as the catalog marks it
      return Pie.store.tables.engines.map((e) => ({ value: e.id, label: Pie.store.names.engine(e.id), selected: e.id === current, dot: Pie.engines.colorOf(e.id) }));
    },
    pick(k, value) {
      // a new view or engine redraws every number: it rolls in on the same diagonal wave a setup's turn does, the setup's name staying put
      // the turn's clock starts again too: a setup turning in right behind a picked view would roll the numbers twice
      const wave = (button) => { if (!viewState) return; captureGhosts(button); if (!button) auto.label = null; auto.rolling = true; auto.spent = 0; clearTimeout(auto.timer); };
      if (k === "view") { if (value !== compare) wave('[data-grid-pick="options"]'); Pie.platform.setCompare(value); return; }
      if (k === "engine" && viewState && value !== (viewState.platform.engine || Pie.engines.primary)) wave();
      if (k === "setup" && viewState) { stopTurns(); auto.rolling = value !== viewState.platform.mode; if (auto.rolling) captureGhosts(); viewState.platform.mode = value; return; }  // a picked setup rolls in as a turn does
      if (k === "engine" && viewState) viewState.platform.engine = value;
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
        const now = viewState.platform.models?.length ? viewState.platform.models : pageModels;
        const by = viewState.platform.modelGroup || "maker";
        const own = value.startsWith("group:") ? pageModels.filter((id) => groupOf(id, by) === value.slice(6)) : [value];
        const all = own.every((id) => now.includes(id));
        const next = all ? now.filter((id) => !own.includes(id)) : [...new Set([...now, ...own])];
        // every model checked again is no pick at all: the menu shows them all, and models added later show too
        viewState.platform.models = pageModels.every((id) => next.includes(id)) ? [] : next;
      }
      if (k === "maker" && viewState) {
        const now = viewState.platform.makers || [];
        viewState.platform.makers = !value ? [] : now.includes(value) ? now.filter((m) => m !== value) : [...now, value];
      }
    },

    // returns the number of machines and models shown, for the toolbar subtitle
    render(state) {
      viewState = state;
      // Speedup and Efficiency are one grid each: the page sets the comparison, and no switch is shown
      const fixed = Pie.schema[state.table]?.compare;
      if (fixed) { peeked = null; compare = fixed; }
      else if (!peeked) compare = chosen;  // a platform's page shows the viewer's pick, whatever page came before
      const all = Pie.store.snapshot(state.release);
      lastAll = all;  // the hover cards name the engines that left a cell empty
      const modes = Pie.platform.metrics(state);
      // the viewer's pick is kept as they made it: a page that does not offer it (the TPU has no Peak FLOPs, Spec Decode
      // is the Roofline page's) shows Decode without forgetting it, so the next page that has it opens on it again
      const mode = modes.find((m) => m.id === state.platform.mode) || modes.find((m) => m.id === "decode") || modes[0];
      const metric = mode.metric;
      // the engine every cell is about, picked in the bar; pie unless another is picked. The second pick is its
      // opponent: the strongest other engine on each cell unless one is picked
      const base = state.platform.engine || Pie.engines.primary;
      const rival = null;  // every cell is set against the strongest other engine
      const snapshot = all.filter((r) => r.workload === mode.workload);
      const raw = all.filter((r) => r.workload === "raw" && Pie.store.isMeasured(r));
      const rows = snapshot.filter(Pie.store.isMeasured);
      // a platform's own page lists its machines; All hardware lists every platform's, a header row each
      const only = Pie.schema[state.table]?.platform;
      // the Overview pages offer the platforms with a result in this setup, and any picked narrow the machines to theirs
      pagePlatforms = only ? [] : PLATFORMS.filter((pl) => rows.some((r) => platformOf(Pie.store.index.hardware[r.hardware] || {}) === pl)).map((pl) => pl.id);
      const picked = [];  // no platform filter: All Platforms shows every platform, each its own table
      const groups = PLATFORMS.filter((p) => (!only || p.id === only) && (!picked.length || picked.includes(p.id)))
        .map((p) => ({ platform: p, macs: Pie.store.tables.hardware.filter((hw) => platformOf(hw) === p)
          // multi-GPU machines (×2, ×4, ×8) hidden for now, to come back later: delete this line to show them again
          .filter((hw) => !(hw.class === "gpu" && hw.count > 1))
          // not shown: A100 PCIe, H100 PCIe and L4 are not evaluated
          .filter((hw) => !["a100-pcie-x1", "h100-pcie-x1", "l4-x1"].includes(hw.id))
          .map((hw) => hw.id) }))
        .filter((g) => !only || g.macs.length);
      const macs = groups.flatMap((g) => g.macs);
      // a platform with no measured result yet, machines or not, shows the empty screen rather than an empty table
      if (only && !all.some((r) => Pie.store.isMeasured(r) && macs.includes(r.hardware))) {
        const label = Pie.schema[state.table]?.label || "this platform";
        element.innerHTML = `<div class="platform-empty"><span class="sidebar-glyph" style="--tint: ${Pie.schema[state.table]?.tint || "var(--color-label-tertiary)"}">${Pie.icon(state.table)}</span>
          <h2>No ${esc(label)} results yet</h2></div>`;
        return { macs: 0, models: 0, metric };
      }
      const query = state.query.trim().toLowerCase();
      const noFit = Pie.store.tables.no_fit || {};
      const p = state.platform;

      // every cell first: a comparison, or why there is none
      // grouped by maker; makers and models in the order the viewer dragged them, the rest alphabetical after
      const byName = (a, b) => a.localeCompare(b, undefined, { sensitivity: "base", numeric: true });
      const rank = (list, key) => { const i = (list || []).indexOf(key); return i < 0 ? Infinity : i; };
      const byRank = (list, a, b) => { const x = rank(list, a), y = rank(list, b); return x === y ? 0 : x < y ? -1 : 1; };
      // the search narrows both ways: machines whose name, chip, vendor or platform holds it, models whose name does;
      // a query that names only machines keeps every model, one that names only models keeps every machine
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
      // by default the fullest first: the makers whose models ran on, or are known not to fit, the most machines here, then within each the model
      // that ran on the most; an order the viewer dragged still wins, and names break ties
      const fill = {};
      // counted over Raw and Batched, Decode and Prefill together: the columns keep one order whichever setup shows
      const SETUP_WORKLOADS = ["raw", "throughput", "prefill_batch"];
      const anySetup = all.filter((r) => SETUP_WORKLOADS.includes(r.workload) && Pie.store.isMeasured(r) && r.engine === base && macs.includes(r.hardware) && (r.decode_tok_s || r.prefill_tok_s || r.output_tok_s));
      for (const r of anySetup) (fill[r.model] ||= new Set()).add(r.hardware);
      // a model that does not fit a machine fills that cell too: the answer is known
      for (const mac of macs) for (const id of suiteModels) if (noFit[mac]?.[id]?.[base]) (fill[id] ||= new Set()).add(mac);
      const fillOf = (id) => fill[id]?.size || 0;
      // the makers menu offers only makers with a result on this page
      pageMakers = [...new Set(rows.filter((r) => r[metric.key] && macs.includes(r.hardware) && suiteModels.includes(r.model)).map((r) => makerOf(r.model).name || "Cloud"))].sort();
      pageModels = [...new Set(rows.filter((r) => r[metric.key] && macs.includes(r.hardware) && suiteModels.includes(r.model)).map((r) => r.model))];
      // a maker's fullness is its models' average, so one full model outranks eight half-empty ones
      const makerFill = {}, makerCount = {};
      for (const id of suiteModels) {
        const name = makerOf(id).name;
        makerFill[name] = (makerFill[name] || 0) + fillOf(id);
        makerCount[name] = (makerCount[name] || 0) + 1;
      }
      for (const name of Object.keys(makerFill)) makerFill[name] /= makerCount[name];
      // the maker picked in the bar narrows the columns to its models
      // the models picked in the bar narrow the columns to them
      const sortedModels = (narrowModels ? modelHits : suiteModels).filter((id) => !p.models?.length || p.models.includes(id))
        .sort((a, b) => byRank(p.makerOrder, makerOf(a).name, makerOf(b).name)
          || makerFill[makerOf(b).name] - makerFill[makerOf(a).name] || byName(makerOf(a).name || "~", makerOf(b).name || "~")
          || byRank(p.modelOrder, a, b) || fillOf(b) - fillOf(a) || byName(names().model(a), names().model(b)));
      // Decode: each engine at its best, speculating or not, in one column per model; a cell won by a speculative run
      // reads as one (its hover card and its roofline limit)
      const SPEC = MODES.find((m) => m.id === "spec");
      const specRows = mode.id === "decode" ? all.filter((r) => r.workload === "spec" && Pie.store.isMeasured(r) && macs.includes(r.hardware)) : [];
      const bestOf = (list) => {
        const by = {};
        for (const r of list) if (r[metric.key] && (!by[r.engine] || r[metric.key] > by[r.engine][metric.key])) by[r.engine] = r;
        return Object.values(by);
      };
      const allModels = sortedModels;
      const realOf = (id) => id;
      const modeOf = (c) => (c?.pie?.workload === "spec" ? SPEC : mode);
      // the models measured as miniatures (cut to fit one device) anywhere in the release
      const miniModels = new Set(snapshot.filter((r) => r.miniature).map((r) => r.model));
      const grid = {};
      for (const mac of macs) {
        grid[mac] = {};
        for (const model of allModels) {
          const id = realOf(model);
          const here = (r) => r.hardware === mac && r.model === id;
          let c = cell(specRows.length ? bestOf([...rows.filter(here), ...specRows.filter(here)]) : rows.filter(here), metric, base, rival);
          // a model that runs cut down to fit (a miniature) never "does not fit": where its miniature did not run, the cell
          // says that instead of the full model's size
          // only where this run measures (or measured) the model cut down: elsewhere the full model's "does not fit" stands
          const cut = (TODAY.models.has(id) && TODAY.hardware.has(mac)) || snapshot.some((r) => here(r) && r.miniature);
          let needs = cut ? null : noFit[mac]?.[id]?.[base];
          // Best TPS and Kernel Efficiency are the real model's speed and its share of the hardware, which a miniature is not: there the full model does not fit, whatever ran
          const fullNeeds = Pie.store.index.models[id]?.needs_gib;
          if ((compare === "tps" || compare === "ceiling") && cut) { c = null; needs = noFit[mac]?.[id]?.[base] || fullNeeds || 1; }
          const own = snapshot.find((r) => here(r) && r.engine === base);
          // a catalog model (a datacenter release, run in the cloud as a miniature) is never "does not fit" when engines
          // are compared: a machine its miniature has not reached reads "–", and a failed run "–" with the error on hover
          const cloud = Pie.store.index.models[id]?.catalog && compare === "engines";
          if (cloud) needs = null;
          const failed = own && own.status === "fail";
          if (cloud && failed && !c) { grid[mac][model] = { c: null, needs: null, failed: true, why: own.note ? `Failed: ${own.note}` : "The run failed" }; continue; }
          // an empty cell explains itself only when there is something to say: it does not fit, or its run failed
          grid[mac][model] = { c, needs, failed, why: needs ? ((compare === "tps" || compare === "ceiling") && cut ? `The full model does not fit one machine${fullNeeds ? `: needs about ${Math.round(fullNeeds)} GB` : ""}. Only a model slice ran` : `Needs about ${Math.round(needs)} GB`) : own?.note || "" };
        }
      }
      // Hide unavailable drops the models and machines with nothing to compare, as the results table does
      // picked platforms drop the models and machines with nothing to show, as a platform's own page reads
      const hide = state.hideEmpty || picked.length > 0;
      // a cell awaiting today's run (its clock) counts as something to show, so its row and column stay
      const awaiting = (mac, model) => !grid[mac][model].c && !grid[mac][model].needs && !grid[mac][model].failed && TODAY.models.has(realOf(model)) && TODAY.hardware.has(mac);
      const ranAny = new Set(anySetup.map((r) => `${r.hardware}|${r.model}`));
      // a machine and model measured in any of the four setups keeps its row and column, so a turn only changes numbers
      const shows = (mac, model) => grid[mac][model].c || awaiting(mac, model) || ranAny.has(`${mac}|${realOf(model)}`);
      const models = hide ? allModels.filter((model) => macs.some((mac) => shows(mac, model))) : allModels;
      const median = (list) => {
        const sorted = list.filter((g) => g !== undefined && g !== null).sort((a, b) => a - b);
        return sorted.length ? sorted[sorted.length >> 1] : null;
      };
      // Speed TPS: the fastest machine on each model wears a blue capsule, as the Overall column marks its numbers; the
      // rest stay plain, so the eye finds the best hardware for a model without a heat map
      const top = {};
      for (const model of models) {
        const vs = macs.map((mac) => grid[mac][model].c?.pie[metric.key]).filter((v) => v > 0);
        if (vs.length > 1) top[model] = Math.max(...vs);
      }
      const overall = (mac) => median(models.map((model) => (compare === "tps" ? grid[mac][model].c?.pie[metric.key] : grid[mac][model].c?.gain)));
      // no sort: the machines in the catalog's order, no arrow anywhere
      // each platform's table keeps its own sort: a click sorts only the table it is in
      const sortFor = (k) => p.sortBy?.[k] || null;
      // machines hidden with their eye keep only their name, at the foot of their list
      const hidden = new Set(p.hidden || []);
      const order = (list, k) => { const s = sorted(list, k); return [...s.filter((mac) => !hidden.has(mac)), ...s.filter((mac) => hidden.has(mac))]; };
      const sorted = (list, k) => {
        const { key: sortKey = null, dir = 1 } = sortFor(k) || {};
        const named = [...list];
        if (!sortKey) return named;
        if (sortKey === "name") return named.sort((a, b) => dir * macName(a).localeCompare(macName(b), undefined, { numeric: true }));
        const val = (mac) => (sortKey === "overall" ? overall(mac) : grid[mac][sortKey]?.c?.gain ?? null);
        // empties sink to the bottom whichever way the column sorts
        return named.sort((a, b) => (val(a) === null) - (val(b) === null) || dir * ((val(a) ?? 0) - (val(b) ?? 0)));
      };
      const grouped = groups.map((g) => ({ ...g, macs: order(hide ? g.macs.filter((mac) => models.some((model) => shows(mac, model))) : g.macs, g.platform.id) }))
        .filter((g) => (!only && !narrowMacs) || g.macs.length);  // a search hides the platforms it leaves empty
      // a platform's page is one list of machines; All Platforms gives each platform its own table, headed by its name
      // and its own maker and model heads, with only the models measured on it
      // a table's miniatures (cut to fit its machines) lead it, then its full models; a maker with both splits its band
      // a slice is read from the runs, not the cell drawn: Tokens per Second and Kernel Efficiency leave a slice's cell
      // empty, and the columns must keep the order Relative Speed gives them
      const sliced = new Set(all.filter((r) => r.miniature && r.engine === base).map((r) => `${r.hardware}|${r.model}`));
      const slicedOn = (list, model) => list.some((mac) => sliced.has(`${mac}|${model}`));
      const minisFirst = (list, ms) => {
        const mini = (model) => slicedOn(list, model);
        return [...ms.filter(mini), ...ms.filter((m) => !mini(m))];
      };
      const sections = only ? [{ platform: null, macs: order(grouped.flatMap((g) => g.macs), only), models: minisFirst(grouped.flatMap((g) => g.macs), models) }]
        : grouped.map((g) => ({ platform: g.platform, macs: g.macs, models: minisFirst(g.macs, models.filter((model) => g.macs.some((mac) => shows(mac, model)))) }))
          .filter((g) => g.macs.length && g.models.length);

      const cells = [];
      const number = (gain) => {
        const kind = Math.abs(gain) < EVEN ? "is-even" : gain > 0 ? "is-ahead" : "is-behind";
        // the sign and the colour say ahead or behind, as Stocks shows a change; an even cell is the same number in grey
        return { kind, html: Math.round(gain * 100) ? signed(gain) : "0%" };
      };
      // narrowed, a machine goes by the name people say, without its memory: no "RTX", and no SXM or PCIe unless that is all
      // that tells two apart on the page
      const terse = (name) => name.replace(/^RTX (PRO )?/, (m, pro) => (pro ? "PRO " : "")).replace(/ (SXM|PCIe)\b/, "");
      const pageNames = macs.map((mac) => chipName(mac));
      const shortOf = (mac) => {
        const name = chipName(mac);
        const short = terse(name);
        return pageNames.some((other) => other !== name && terse(other) === short) ? name.replace(/^RTX (PRO )?/, (m, pro) => (pro ? "PRO " : "")) : short;
      };
      const EYE = "M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z";
      const eye = (mac) => {
        const off = hidden.has(mac);
        const label = off ? "Show this machine's numbers" : "Hide this machine's numbers";
        return `<button type="button" class="platform-eye" data-hide-mac="${esc(mac)}" aria-pressed="${off}" aria-label="${label}" title="${label}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="${EYE}"/>${off ? '<path d="M3 13 13 3"/>' : '<circle cx="8" cy="8" r="2"/>'}</svg></button>`;
      };
      const machine = (mac, platform) => {
        const hw = Pie.store.index.hardware[mac];
        const short = shortOf(mac);
        return `<th class="platform-row" scope="row" data-hide-mac="${esc(mac)}"${hw ? ` data-tip="${esc(specSheet(hw))}"` : ""}><span class="platform-chip">${badgeOf(platformOf(hw || {})?.id)}<span class="platform-name">${esc(chipName(mac))}</span>${short !== chipName(mac) ? `<span class="platform-short">${esc(short)}</span>` : ""}${specOf(hw)}</span>${eye(mac)}</th>`;
      };
      // a platform heads its machines with a row across the table, as Finder heads a group
      const folded = (id) => Boolean(p.collapsed?.[id]);
      const groupRow = (g) => `<tr class="platform-group-row${folded(g.platform.id) ? " is-collapsed" : ""}${g.macs.length ? "" : " is-empty"}"${g.macs.length ? ` data-group="${g.platform.id}"` : ""} aria-expanded="${!folded(g.platform.id)}"><th colspan="${models.length + 3}" scope="rowgroup">
        <span class="platform-group-bar">
          <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${esc(g.platform.sub)} · ${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}</span></span>
          <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
        </span></th></tr>`;
      // Roofline: every cell carries the mark of what limits it, before its number as a leading symbol: two arrows for memory bandwidth,
      // a chip for compute; the hover card gives both bounds
      const MARK = {
        compute: { title: "Compute-bound: the share of the compute bound", path: "M4.5 4.5h7v7h-7zM6.5 2v2.5M9.5 2v2.5M6.5 11.5V14M9.5 11.5V14M2 6.5h2.5M2 9.5h2.5M11.5 6.5H14M11.5 9.5H14" },
        bandwidth: { title: "Bandwidth-bound: the share of the bandwidth bound", path: "M2 5.5h9M8.5 3l2.5 2.5L8.5 8M14 10.5H5M7.5 8 5 10.5 7.5 13" },
        interconnect: { title: "Interconnect-bound: the share of the bound set by the link between the GPUs", path: "M6.5 9.5l3-3M7.2 4.6l1.4-1.4a2.6 2.6 0 0 1 3.7 3.7l-1.4 1.4M8.8 11.4l-1.4 1.4a2.6 2.6 0 0 1-3.7-3.7l1.4-1.4" },
      };
      const tableOf = ({ macs: list, models, platform: own }, first = true) => {
      // each platform folds its own Hardware column: its choice kept by name, the old page-wide one until then
      const key = own?.id || only || "all";
      const { key: sortKey = null, dir = 1 } = sortFor(key) || {};
      const tight = p.narrowBy?.[key] ?? (p.narrow ?? true);
      const narrowLabel = tight ? "Show Overall and memory" : "Hide Overall and memory";
      const shownGroups = [{ platform: null, macs: list }];
      // a model slice's cell carries the slice mark in its top-left corner; its popover says how much of the model ran,
      // as the columns' (i) does
      const sliceMark = (cut, model) => {
        const all = Pie.store.index.models[realOf(model)]?.layers;
        const kept = parseInt(cut, 10);
        const experts = String(cut).match(/, (\d+) experts$/)?.[1];
        const how = (kept && all ? `${kept} of ${all} layers kept (${Math.round((kept / all) * 100)}%)` : String(cut).replace(/, \d+ experts$/, "")) + (experts ? `, the first ${experts} experts` : "");
        return `<span class="column-info slice-mark" tabindex="0" role="button" aria-label="Model slice"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg><span class="column-info-pop" role="tooltip">${esc(`Model slice: ${how}, to fit one device. For engine-to-engine comparison only, not the full model's speed.`)}</span></span>`;
      };
      const body = shownGroups.map((g) => (g.platform ? groupRow(g) : "") + (g.platform && folded(g.platform.id) ? [] : g.macs).map((mac, i) => {
        if (hidden.has(mac)) return `<tr class="is-hidden-row" data-empty="1">${machine(mac, g.platform)}<td class="is-overall" data-hide-mac="${esc(mac)}">${eye(mac)}</td>${models.map((model) => `<td data-col="${esc(model)}"></td>`).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
        const o = overall(mac);
        const overallCell = o === null ? `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell is-empty">–</span>${eye(mac)}</td>`
          : compare === "tps" ? `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell is-even"><span class="platform-main">${fmtNum(o)}<span class="platform-unit">${esc(metric.unit)}</span></span></span>${eye(mac)}</td>`
          : (() => { const n = number(o); n.html = Math.round(o * 100) ? signed(o) : "0%"; return `<td class="is-overall" data-hide-mac="${esc(mac)}"><span class="platform-cell ${n.kind}" data-tip="${esc(card(macName(mac), Math.abs(o) < EVEN ? "On par with the next best" : `${Math.abs(Math.round(o * 100))}% ${o > 0 ? "faster" : "slower"} than the next best`))}"><span class="platform-main">${n.html}</span></span>${eye(mac)}</td>`; })();
        return `<tr>${machine(mac, g.platform)}${overallCell}${models.map((model) => {
          const { c, needs, why } = grid[mac][model];
          const sorted = sortKey === model ? " is-sorted" : "";
          if (c) {
            cells.push(c.gain);
            const ceil = compare === "ceiling" ? boundOf(mac, realOf(model), modeOf(c), metric, c.pie) : null;
            const n = compare === "ceiling"
              ? (() => {
                  // one neutral colour: the closest to the bound is bold, the furthest dimmed
                  if (!ceil) return { kind: "is-even", html: "–" };
                  const share = c.pie[metric.key] / ceil.tps;
                  // past the roof (shown above 100%) is red: a result cannot beat a true limit, so an input or the run is off
                  const kind = Math.round(share * 100) > 100 ? "is-behind" : share >= 0.25 ? "is-ahead" : "is-mid";
                  // a balanced cell takes the lower of its two bounds
                  const which = MARK[ceil.bound] ? ceil.bound : (ceil.bandwidth || Infinity) <= (ceil.compute || Infinity) ? "bandwidth" : "compute";
                  const mark = MARK[which];
                  return { kind, html: `<svg class="platform-bound-mark" viewBox="0 0 16 16" role="img" aria-label="${mark.title}"><title>${mark.title}</title><path d="${mark.path}"/></svg>${Math.round(share * 100)}%` };
                })()
              : compare === "tps" ? { kind: "is-even", html: `${esc(fmtNum(c.pie[metric.key]))}<span class="platform-unit">${esc(metric.unit)}</span>` }
              // a miniature's own tok/s is a cut model's, no real speed: with no other engine to set it against, it shows none
              : c.gain === null ? { kind: "is-even", html: c.pie.miniature ? "–" : esc(value(c.pie[metric.key], metric.unit)) } : number(c.gain);
            // a click opens Results on this run: the machine, the model, the workload, and the engines the cell compares
            const PHASE = { decode: "raw_decode", prefill: "raw_prefill", spec: "spec_decode", batching: "throughput", pbatch: "prefill_batch" };
            const open = { hardware: [mac], model: [realOf(model)], workload: [PHASE[modeOf(c).id] || modeOf(c).workload],
              engine: compare === "engines" ? [...new Set((c.all || [c.pie]).map((r) => r.engine))] : [c.pie.engine] };
            return `<td class="${sorted} is-openable" data-col="${esc(model)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${n.kind}${c.pie.miniature ? " is-mini" : ""}${compare === "tps" && top[model] === c.pie[metric.key] ? " is-top" : ""}"${compare === "tps" ? "" : ` data-tip="${esc(tip(mac, realOf(model), metric, c, modeOf(c), raw))}"`}>${c.pie.miniature ? sliceMark(c.pie.miniature, model) : ""}<span class="platform-main">${n.html}</span>${subline(c, metric, modeOf(c), raw)}</span></td>`;
          }
          // an empty cell lists every engine that has a row here and why it gave no number, as a measured cell's card does
          // the engines that did measure here, though pie did not (the comparison needs pie): their numbers first
          const ranHere = [...new Map(rows.filter((r) => r.hardware === mac && r.model === realOf(model) && r[metric.key]).map((r) => [r.engine, r])).values()]
            .sort((a, b) => b[metric.key] - a[metric.key]);
          const absent = [...ranHere.map((r) => `<div class="tip-row"><span class="tip-dot" style="background: ${Pie.engines.colorOf(r.engine)}"></span><span class="tip-name">${esc(names().engine(r.engine))}</span>
            <span class="tip-value">${r.miniature ? "Model slice" : esc(value(r[metric.key], metric.unit))}</span><span class="tip-when">${esc(day(r))}</span></div>`), ...absentRows(mac, realOf(model), modeOf(null), ranHere)];
          const emptyTip = absent.length ? card("", "", absent) : why ? card("", "", [], why) : "";
          return `<td class="${sorted}" data-col="${esc(model)}"><span class="platform-cell is-empty${needs ? " is-nofit" : ""}"${emptyTip ? ` data-tip="${esc(emptyTip)}"` : ""}>${needs ? NOFIT : "–"}</span></td>`;
        }).join("")}<td class="platform-fill" aria-hidden="true"></td></tr>`;
      }).join("")).join("");

      const arrow = (key) => (sortKey === key ? `<span class="column-sort">${dir > 0 ? "↑" : "↓"}</span>` : "");
      // a maker heads its models with a band across them, as a platform heads its machines down the side
      const makers = [];
      // a maker's miniatures and its full models are two bands, as the miniatures lead the table
      const cut = (model) => slicedOn(list, model);
      for (const model of models) {
        const maker = makerOf(model);
        const last = makers[makers.length - 1];
        // a speculation column widens the band but is not another model
        if (last && last.maker.name === maker.name && last.cut === cut(model)) { last.n += 1; last.count += 1; }
        else makers.push({ maker, n: 1, count: 1, cut: cut(model) });
      }
      // each table's corner above Hardware narrows its own pinned column to each machine's mark and name, for room
      // for the models, and back: one button a platform
      const makerRow = `<tr class="platform-maker-row"><th class="platform-corner"><button type="button" class="platform-narrow" data-narrow="${esc(key)}" aria-pressed="${tight}" aria-label="${narrowLabel}" title="${narrowLabel}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M7.5 4 3.5 8l4 4M12.5 4l-4 4 4 4"/></svg></button></th><th class="platform-corner is-sortable is-overall" data-sort="overall" aria-hidden="true"></th>${makers.map(({ maker, n, count }) =>
        `<th class="platform-maker" colspan="${n}" scope="colgroup" data-drop="maker" data-id="${esc(maker.name)}"><span class="platform-maker-name">${badge(maker)}<b>${esc(maker.name || "Cloud")}</b><span>${count} ${count === 1 ? "model" : "models"}</span></span></th>`).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      const head = `<tr class="platform-head-row">
        <th class="platform-corner is-sortable" scope="col" data-sort="name">Hardware${arrow("name")}</th>
        <th class="platform-corner is-sortable is-overall" scope="col" data-sort="overall"><span class="platform-model">Overall${arrow("overall")}</span><span class="platform-sub">Median</span></th>${models.map((model) => {
        const m = Pie.store.index.models[realOf(model)] || {};
        const size = m.params_b ? `${m.params_b}B${m.active_b && m.active_b !== m.params_b ? ` · ${m.active_b}B` : ""}` : "";
        // the precision pie ran the model at on this table's machines, after its size
        const SCHEME = { affine_u4_g64: "4-bit", bf16: "BF16", fp8: "FP8", mxfp4: "MXFP4", gguf_q4_k_m: "Q4_K_M", mlx_2bit: "2-bit" };
        const precision = [...new Set(list.map((mac) => grid[mac]?.[model]?.c?.pie?.scheme).filter(Boolean).map((s) => SCHEME[s] || s))].join(" / ");
        // the speculative column says so under the model's name, where the other columns give its size
        const sub = size;
        // its card on hover, as a machine's: what the model is, and how pie ran it here
        const sheet = `<div class="tip-title">${esc(names().model(realOf(model)))}</div><div class="spec-rows">${[
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
          <span class="platform-col"><span><span class="platform-model">${esc(names().model(realOf(model)))}${arrow(model)}</span><span class="platform-sub">${esc(sub)}</span></span></span></th>`;
      }).join("")}<th class="platform-fill" aria-hidden="true"></th></tr>`;
      // the columns keep their width; a last empty column takes what is left, so rows and bars reach the edge as in Finder
      const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;
      return `<table class="platform-table${tight ? " is-tight" : ""}" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>`;
      };
      // each platform under its header bar, which folds it away as a Finder group does; its table scrolls sideways on its own
      const tables = only ? tableOf(sections[0] || { macs: [], models: [] }) : sections.map((g, i) => `<section class="platform-section">
        <div class="platform-group-row platform-section-bar${folded(g.platform.id) ? " is-collapsed" : ""}" data-group="${g.platform.id}" role="button" aria-expanded="${!folded(g.platform.id)}">
          <span class="platform-group-bar">
            <span class="platform-group-name">${badgeOf(g.platform.id)}<b>${esc(g.platform.label)}</b><span>${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}, ${g.models.length} ${g.models.length === 1 ? "model" : "models"}</span></span>
            <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
          </span>
        </div><div class="platform-section-body"${folded(g.platform.id) ? " hidden" : ""}><div class="platform-section-scroll">${tableOf(g, i === 0)}</div></div></section>`).join("");

      // a redraw keeps the reader where they were: the page's scroll down and each table's scroll across
      const keptPage = element.querySelector(".platform-scroll");
      const kept = keptPage ? { top: keptPage.scrollTop, left: keptPage.scrollLeft, lefts: [...element.querySelectorAll(".platform-section-scroll")].map((x) => x.scrollLeft) } : null;
      element.innerHTML = `
        <div class="platform-bar">
          ${setupControl(mode.id, modes)}${mode.id === "spec" && compare === "ceiling" ? `${Pie.specField?.() || ""}` : ""}
          <button type="button" class="plain-button rules-button" data-rules aria-expanded="false" aria-label="Test Conditions" title="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button>
          <span class="platform-bar-side is-end">
            <!-- the engines and models picked sit with the view, at the bar's right end, as a Mac toolbar groups its view options -->
            <span class="filter platform-setup"><button class="filter-button label-rolls" type="button" data-grid-pick="options" aria-haspopup="menu" aria-label="View Options" title="View, engine and opponent">${viewIcon(compare)}<span>${esc(COMPARES[compare])}</span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>
            <span class="filter platform-setup"><button class="filter-button" type="button" data-grid-pick="model" aria-haspopup="menu" aria-label="Models">${esc(!p.models?.length ? "All Models" : p.models.length <= 2 ? p.models.map((id) => names().model(id)).join(", ") : `${p.models.length} Models`)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>

          </span>
        </div>
        <div class="platform-scroll">
          ${tables}
        </div>`;
      // the header bar spans what is visible, so its chevron sits at the right edge however wide the table is
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
      return { macs: macsShown, models: new Set(sections.flatMap((g) => g.models).map(realOf)).size, metric };
    },

    bind(state) {
      // a redraw the viewer asked for leaves the page where it was: its height and each platform's sideways place
      const inPlace = (redraw) => {
        const page0 = element.querySelector(".platform-scroll");
        const top = page0?.scrollTop || 0;
        const left = page0?.scrollLeft || 0;  // one platform's page slides sideways in the page's own scroller
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
        if (cell && !event.target.closest(".column-info")) { openResults(JSON.parse(cell.dataset.open)); return; }
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
        // in place, no redraw of the page: the row greys out and goes last, or comes back before the hidden ones; a row
        // drawn hidden has no numbers to show, so showing it again redraws
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
        if (event.detail) button.blur();  // a click leaves no focus behind, so the arrow keys after it draw no ring
        // this platform's table alone; the others keep theirs
        const table = button.closest(".platform-table");
        const narrow = !table.classList.contains("is-tight");
        state.platform.narrowBy = { ...state.platform.narrowBy, [button.dataset.narrow]: narrow };
        Pie.saveView?.();
        const label = narrow ? "Show Overall and memory" : "Hide Overall and memory";
        table.classList.toggle("is-tight", narrow);
        stripes(element);  // the columns moved
        button.setAttribute("aria-pressed", String(narrow)); button.title = label; button.setAttribute("aria-label", label);
      }, true);

      // drag a maker's band among the makers, or a model's head among its maker's models, as a column moves in Finder's
      // list view: the whole column (the head and every cell under it) slides sideways within its lane, and the columns
      // it passes slide aside to open its place, so the order shows as it will be. Letting go settles it there.
      // The head itself is the handle: a press that moves a few points drags, one that does not is a click and sorts.
      // The order is the viewer's, kept with the page's other choices
      const SETTLE = 180;
      let press = null;
      let drag = null;
      let dragged = false;
      // a unit that moves together: a model's column, or a maker's band with all of its models' columns
      const unitOf = (th) => {
        // on All Platforms each platform is its own table: a column moves within its table
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
        document.documentElement.classList.add("is-dragging-column");  // the closed hand, wherever the pointer goes
        th.setPointerCapture(event.pointerId);
        dragged = true;
        drag = { kind, units, index, me, x0: event.clientX, lane: [units[0].left, units.at(-1).left + units.at(-1).width], to: index };
      };
      element.addEventListener("pointermove", (event) => {
        if (press && Math.abs(event.clientX - press.x) > 4) lift(event);
        if (!drag) return;
        const { units, index, me, lane } = drag;
        // the column keeps to its lane: it cannot slide past the first or last of its peers
        const dx = Math.max(lane[0] - me.left, Math.min(lane[1] - me.width - me.left, event.clientX - drag.x0));
        shift(me, dx, false);
        // where it would land: past every peer whose middle its middle has reached (held at the lane's end, past the last)
        const middle = me.left + dx + me.width / 2;
        let to = index;
        units.forEach((u, i) => {
          if (i > index && middle >= u.left + u.width / 2) to = Math.max(to, i);
          if (i < index && middle <= u.left + u.width / 2) to = Math.min(to, i);
        });
        drag.to = to;
        // the peers it has passed slide aside by its width to open its place
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
        // settle into the opened place, then take the new order
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
          const rest = (state.platform[key] || []).filter((x) => !order.includes(x));
          state.platform[key] = kind === "maker" ? order.concat(rest) : rest.concat(order);
          inPlace(onChange);
        }, SETTLE);
      };
      element.addEventListener("pointerup", finish);
      element.addEventListener("pointercancel", finish);
      element.addEventListener("click", (event) => {
        if (dragged) {
          dragged = false;  // the press lifted a head: it was a drag, not a click to sort
          return;
        }
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
        // a platform's header row folds its machines away and back, as a Finder group does
        const group = event.target.closest("[data-group]");
        if (group) {
          const id = group.dataset.group;
          const toggle = () => {
            state.platform.collapsed = { ...(state.platform.collapsed || {}), [id]: !state.platform.collapsed?.[id] };
            onChange();
          };
          // on All Platforms the table slides shut or open under its bar as the chevron turns, as a Finder group does;
          // it is folded in place, with no redraw, so the slide starts on the click
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
            stripes(body);  // laid out only now: folded, its cells had no place
            if (!reduce) body.animate([{ height: "0px" }, { height: `${body.offsetHeight}px` }], { duration: 250, easing: "cubic-bezier(.25, .1, .25, 1)" });
          }
          return;
        }
        // a header cycles its column: ascending, then descending, then back to no sort
        const header = event.target.closest("[data-sort]");
        if (!header) return;
        const key = header.dataset.sort;
        // the table's platform, as its corner button names it: the sort stays in that table
        const table = header.closest("table")?.querySelector("[data-narrow]")?.dataset.narrow || "all";
        const mine = state.platform.sortBy?.[table];
        state.platform.sortBy = { ...(state.platform.sortBy || {}), [table]: mine?.key !== key ? { key, dir: 1 } : mine.dir > 0 ? { key, dir: -1 } : null };
        onChange();
      });
      // Spec Decode's acceptance: the grid redraws at once, the field keeping its focus while it is typed in
      Pie.bindSpecField?.(element, () => {
        const typing = document.activeElement?.matches?.("[data-alpha]");
        onChange();
        const input = element.querySelector("[data-alpha]");
        if (input && typing) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
      });
      // a tap on a cell shows its card, as hovering does with a pointer
      element.addEventListener("click", (event) => {
        const mark = Pie.tapCard.isTouch() && event.target.closest("[data-tip]");
        if (mark) Pie.tapCard.toggle(mark, mark.dataset.tip, true);
      });
      // the card under the pointer: shown as the pointer moves, and again when the grid redraws beneath a still pointer
      // (R switching Performance and Roofline), so the card always matches the cell
      const showCard = (mark, cx, cy) => {
        if (!mark) {
          tooltip.hidden = true;
          return;
        }
        // the card is markup this page built, every value escaped
        tooltip.innerHTML = mark.dataset.tip;
        tooltip.classList.add("is-card");
        tooltip.hidden = false;
        const x = Math.min(cx + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(cy + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      };
      // a cell's card shows over the whole cell, its padding and edges too, not only over its number
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
