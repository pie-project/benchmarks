window.Pie = window.Pie || {};

// Profiler: where a long agentic workload spends the hardware's time. A visitor opens a trace of their own run (.pie)
// with Open Trace… or by dropping it anywhere on the page, as a Mac app opens a document; Open Sample loads ours.
// The file is read here in the browser and never leaves the device. The trace (docs/pie-trace-format.md) is drawn as
// one timeline: a lane per agent, the scheduler's steps and the GPU's work under them, then each agent's KV memory
// and share of the GPU over the same time axis, so the gaps where the hardware waits stand out.
(() => {
  const element = document.getElementById("profiler");
  const tooltip = document.getElementById("chart-tooltip");
  const EXT = ".pie";
  const SAMPLE = "data/traces/sample-3-agents.pie";
  const PHASES = ["prefill", "decode", "tool", "queued"];
  const AGENT_COLORS = 8;  // --prof-agent-1 … 8, Apple's system colors in a fixed order; a ninth agent reuses the first

  const esc = (value) => Pie.format.escape(value);

  const EMPTY = `
    <section class="prof-drop">
      <svg class="prof-drop-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5v4a1 1 0 0 0 1 1h4"/><path d="M7.5 14h2.25l1.5-3.5 2 7 1.5-3.5h1.75"/></svg>
      <p class="prof-drop-title">No Traces</p>
      <p class="prof-drop-text">Record a trace with Pie, then open it here. It is read on this device and never uploaded.</p>
      <button class="prof-choose" type="button" data-open>Open Trace…</button>
      <button class="prof-sample" type="button" data-sample>Open Sample</button>
    </section>`;

  // ---------- reading a trace ----------

  // the index of the first item whose end is after t: items are sorted and do not overlap, so their ends are sorted too
  const firstEndingAfter = (items, t) => {
    let lo = 0;
    let hi = items.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (items[mid].end <= t) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  };

  // the item that holds t, or null
  const at = (items, t) => {
    const i = firstEndingAfter(items, t);
    return i < items.length && items[i].ts <= t ? items[i] : null;
  };

  // overlapping intervals joined into one sorted list
  const union = (items) => {
    const sorted = [...items].sort((a, b) => a.ts - b.ts);
    const out = [];
    for (const item of sorted) {
      const last = out[out.length - 1];
      if (last && item.ts <= last.end) last.end = Math.max(last.end, item.end);
      else out.push({ ts: item.ts, end: item.end });
    }
    return out;
  };

  const total = (intervals) => intervals.reduce((sum, interval) => sum + interval.end - interval.ts, 0);

  // a counter as a step function: each value holds from its time to the next one; integrals make column averages cheap
  const series = (points, keys) => {
    const ts = points.map((point) => point.ts);
    const values = {};
    const integrals = {};
    for (const key of keys) {
      const v = points.map((point) => Number(point.args?.[key]) || 0);
      const integral = [0];
      for (let i = 1; i < v.length; i += 1) integral.push(integral[i - 1] + v[i - 1] * (ts[i] - ts[i - 1]));
      values[key] = v;
      integrals[key] = integral;
    }
    // the last point at or before t, or -1 before the first
    const index = (t) => {
      let lo = 0;
      let hi = ts.length;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (ts[mid] <= t) lo = mid + 1;
        else hi = mid;
      }
      return lo - 1;
    };
    const integral = (key, t) => {
      const i = index(t);
      return i < 0 ? 0 : integrals[key][i] + values[key][i] * (t - ts[i]);
    };
    return {
      size: ts.length,
      value: (key, t) => {
        const i = index(t);
        return i < 0 ? 0 : values[key][i];
      },
      mean: (key, t0, t1) => (t1 > t0 ? (integral(key, t1) - integral(key, t0)) / (t1 - t0) : 0),
      max: (key) => Math.max(0, ...values[key]),
    };
  };

  class TraceError extends Error {}

  const parse = (text) => {
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      throw new TraceError("It isn’t a trace file.");
    }
    if (!data || data.format !== "pie-trace" || !Array.isArray(data.traceEvents)) throw new TraceError("It isn’t a Pie trace.");
    if (data.version !== 1) {
      throw new TraceError(Number(data.version) > 1 ? `It was recorded by a newer Pie (format ${esc(data.version)}). Update this page, then try again.` : "Its format version is unknown.");
    }
    const meta = data.meta && typeof data.meta === "object" ? data.meta : {};
    const agents = new Map();
    const agent = (tid) => {
      const id = Number(tid);
      if (!agents.has(id)) agents.set(id, { id, key: `agent-${id}`, label: `agent-${id}`, spans: [], start: null, end: null });
      return agents.get(id);
    };
    const steps = [];
    const gpus = [];
    const counters = { kv_pages: [], gpu_busy: [], gpu_share: [], memory: [] };
    const evicts = [];
    let duration = 0;

    for (const event of data.traceEvents) {
      if (!event || typeof event !== "object") continue;
      const ts = Number(event.ts) || 0;
      const end = ts + Math.max(0, Number(event.dur) || 0);
      if (event.ph !== "M") duration = Math.max(duration, end);
      if (event.pid === 1) {
        if (event.ph === "M" && event.name === "thread_name" && event.args?.name) agent(event.tid).label = String(event.args.name);
        else if (event.ph === "X" && PHASES.includes(event.name)) agent(event.tid).spans.push({ name: event.name, ts, end, args: event.args || {} });
        else if ((event.ph === "i" || event.ph === "I") && event.name === "start") agent(event.tid).start = ts;
        else if ((event.ph === "i" || event.ph === "I") && event.name === "end") agent(event.tid).end = ts;
      } else if (event.pid === 2) {
        if (event.ph === "X" && event.name === "step") steps.push({ ts, end, args: event.args || {} });
        else if (event.ph === "X" && event.name === "gpu") gpus.push({ ts, end, args: event.args || {} });
        else if (event.ph === "C" && counters[event.name]) counters[event.name].push({ ts, args: event.args || {} });
        else if ((event.ph === "i" || event.ph === "I") && event.name === "evict") evicts.push({ ts, args: event.args || {} });
      }
    }
    if (!agents.size) throw new TraceError("It has no agents in it.");
    const byTime = (a, b) => a.ts - b.ts;
    [steps, gpus, evicts, ...Object.values(counters)].forEach((list) => list.sort(byTime));

    const list = [...agents.values()].sort((a, b) => a.id - b.id);
    list.forEach((a, i) => {
      a.spans.sort(byTime);
      a.color = `var(--prof-agent-${(i % AGENT_COLORS) + 1})`;
      a.slot = (i % AGENT_COLORS) + 1;
      a.start ??= a.spans[0]?.ts ?? 0;
      a.end ??= a.spans.length ? Math.max(...a.spans.map((span) => span.end)) : duration;
      a.tools = a.spans.filter((span) => span.name === "tool");
      // a short label for tight places: "agent-1 (react)" -> "agent-1"
      a.short = a.label.replace(/\s*\(.*\)\s*$/, "") || a.label;
    });
    const agentById = (id) => agents.get(Number(id));
    return { meta, duration: Math.max(duration, 1), agents: list, agentById, steps, gpus, counters, evicts };
  };

  // the numbers the page leads with, worked out once per trace
  const summarize = (trace) => {
    const { agents, duration, meta } = trace;
    trace.busy = union(trace.gpus);
    const busyUs = total(trace.busy);

    // every live agent waiting on a tool: the stretches where only the tools are working
    const bounds = new Set([0, duration]);
    for (const a of agents) {
      bounds.add(a.start);
      bounds.add(a.end);
      for (const span of a.tools) {
        bounds.add(span.ts);
        bounds.add(span.end);
      }
    }
    const points = [...bounds].sort((x, y) => x - y);
    const waiting = [];
    for (let i = 0; i + 1 < points.length; i += 1) {
      const mid = (points[i] + points[i + 1]) / 2;
      const live = agents.filter((a) => a.start <= mid && mid < a.end);
      if (!live.length || !live.every((a) => at(a.tools, mid))) continue;
      const last = waiting[waiting.length - 1];
      if (last && last.end === points[i]) last.end = points[i + 1];
      else waiting.push({ ts: points[i], end: points[i + 1] });
    }
    // ... less whatever time the GPU was busy in them anyway
    const winBack = [];
    let j = 0;
    for (const span of waiting) {
      let from = span.ts;
      while (j < trace.busy.length && trace.busy[j].end <= from) j += 1;
      let k = j;
      while (k < trace.busy.length && trace.busy[k].ts < span.end) {
        if (trace.busy[k].ts > from) winBack.push({ ts: from, end: trace.busy[k].ts });
        from = Math.max(from, trace.busy[k].end);
        k += 1;
      }
      if (from < span.end) winBack.push({ ts: from, end: span.end });
    }
    trace.winBack = winBack.filter((span) => span.end - span.ts > 0);

    // each agent's GPU time: every step's gpu_us split by the agent's tokens in it
    const gpuOf = new Map(agents.map((a) => [a.id, 0]));
    let stepGpu = 0;
    for (const step of trace.steps) {
      const us = Number(step.args.gpu_us) || 0;
      const per = step.args.agents || {};
      const tokens = Object.values(per).reduce((sum, n) => sum + (Number(n.prefill) || 0) + (Number(n.decode) || 0), 0);
      stepGpu += us;
      if (!tokens) continue;
      for (const [id, n] of Object.entries(per)) {
        if (gpuOf.has(Number(id))) gpuOf.set(Number(id), gpuOf.get(Number(id)) + (us * ((Number(n.prefill) || 0) + (Number(n.decode) || 0))) / tokens);
      }
    }

    const keys = agents.map((a) => a.key);
    trace.kv = series(trace.counters.kv_pages, [...keys, "free"]);
    trace.share = series(trace.counters.gpu_share, keys);
    trace.busyPct = series(trace.counters.gpu_busy, ["pct"]);
    trace.memory = series(trace.counters.memory, ["allocated_gb"]);
    const pageBytes = Number(meta.kv_page_bytes) || 0;
    // without steps, the gpu_share counter integrated over the run tells the same split
    const shareGpu = (a) => (stepGpu ? gpuOf.get(a.id) : trace.share.mean(a.key, 0, duration) * duration);
    const gpuTotal = stepGpu || trace.busyPct.mean("pct", 0, duration) * duration || 1;

    for (const a of agents) {
      const time = Object.fromEntries(PHASES.map((phase) => [phase, 0]));
      for (const span of a.spans) time[span.name] += span.end - span.ts;
      const life = Math.max(0, a.end - a.start);
      time.idle = Math.max(0, life - PHASES.reduce((sum, phase) => sum + time[phase], 0));
      a.time = time;
      a.life = life;
      a.peakPages = trace.kv.size ? trace.kv.max(a.key) : 0;
      a.peakBytes = a.peakPages * pageBytes;
      a.gpuShare = shareGpu(a) / gpuTotal;
      a.gpuUs = shareGpu(a);
    }
    const poolPages = Number(meta.kv_pages_total) || 0;
    trace.poolBytes = poolPages * pageBytes;
    trace.pageBytes = pageBytes;
    trace.summary = {
      busyUs,
      busyShare: busyUs / duration,
      winBackUs: total(trace.winBack),
      peakKvBytes: trace.counters.kv_pages.reduce((peak, point) => Math.max(peak, keys.reduce((sum, key) => sum + (Number(point.args[key]) || 0), 0)), 0) * pageBytes,
    };
    return trace;
  };

  // ---------- numbers in words ----------

  const duration = (us) => {
    const a = Math.abs(us);
    if (a === 0) return "0 s";
    if (a < 1000) return `${Math.round(us)} µs`;
    if (a < 1e6) return `${(us / 1000).toFixed(a < 1e4 ? 1 : 0)} ms`;
    if (a < 6e7) return `${(us / 1e6).toFixed(a < 1e7 ? 2 : 1)} s`;
    const s = Math.round(us / 1e6);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };

  // a moment on the time axis: decimals enough to tell this tick from its neighbour
  const instant = (us, step) => {
    if (step >= 1e5) return `${(us / 1e6).toFixed(Math.max(0, -Math.floor(Math.log10(step / 1e6) + 1e-9)))} s`;
    if (step >= 100) return `${(us / 1000).toFixed(Math.max(0, -Math.floor(Math.log10(step / 1000) + 1e-9)))} ms`;
    return `${Math.round(us)} µs`;
  };

  const at3 = (us) => `${(us / 1e6).toFixed(3)} s`;

  const bytes = (n) => {
    if (n >= 1e9) return `${(n / 1e9).toFixed(n >= 1e10 ? 1 : 2)} GB`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(n >= 1e8 ? 0 : 1)} MB`;
    if (n >= 1e3) return `${Math.round(n / 1e3)} KB`;
    return `${Math.round(n)} B`;
  };

  const percent = (share) => `${share >= 0.1 || share === 0 ? Math.round(share * 100) : (share * 100).toFixed(1)}%`;
  const count = (n, one, many) => `${n.toLocaleString()} ${n === 1 ? one : many}`;

  // 1, 2 or 5 times a power of ten: a tick step near the one asked for
  const niceStep = (raw) => {
    const power = 10 ** Math.floor(Math.log10(raw));
    const scaled = raw / power;
    return (scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10) * power;
  };

  // ---------- the page ----------

  let trace = null;
  let fileName = "";
  const view = { t0: 0, t1: 1 };
  let hoverT = null;
  let colors = {};
  let frame = 0;

  const isPhone = () => element.clientWidth < 600;
  const gutter = () => (isPhone() ? 70 : 128);
  const LANE = 30;
  const ENGINE_LANE = 24;
  const AXIS = 26;

  const metaLine = (meta) => {
    const hw = meta.hardware || {};
    const machine = [hw.name, hw.memory_gb ? `${hw.memory_gb} GB` : ""].filter(Boolean).join(" ");
    const pie = meta.pie_version ? `Pie ${meta.pie_version}${meta.commit ? ` (${String(meta.commit).slice(0, 9)})` : ""}` : "";
    const when = meta.started_at ? new Date(meta.started_at) : null;
    const started = when && !Number.isNaN(when.getTime()) ? when.toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }) : "";
    return [meta.model, meta.scheme, machine, pie, started].filter(Boolean).map((part) => `<span>${esc(part)}</span>`).join("");
  };

  const stat = (label, value, note, modifier = "") => `
    <div class="prof-stat ${modifier}">
      <div class="prof-stat-label">${label}</div>
      <div class="prof-stat-value">${value}</div>
      <div class="prof-stat-note">${note}</div>
    </div>`;

  // an agent's life in one thin bar, shaded as on the timeline: prefill, decode, tool, queued, then idle
  const split = (a) => {
    const life = a.life || 1;
    return `<span class="prof-split" style="--agent: ${a.color}" aria-hidden="true">${[...PHASES, "idle"]
      .map((phase) => (a.time[phase] > 0 ? `<i class="is-${phase}" style="flex: ${a.time[phase] / life}"></i>` : ""))
      .join("")}</span>`;
  };

  const agentRows = () => trace.agents.map((a) => `
    <tr>
      <th scope="row"><span class="prof-agent"><i style="background: ${a.color}"></i>${esc(a.label)}</span></th>
      <td class="prof-split-cell">${split(a)}</td>
      ${[...PHASES, "idle"].map((phase) => `<td>${duration(a.time[phase])}</td>`).join("")}
      <td>${trace.pageBytes ? bytes(a.peakBytes) : `${a.peakPages.toLocaleString()} pages`}</td>
      <td>${percent(a.gpuShare)}</td>
    </tr>`).join("");

  const section = (title, caption, body, tint, icon) => `
    <section class="prof-section">
      <div class="section-head">
        <div class="section-heading">
          <span class="section-icon" style="--tint: ${tint}"><svg viewBox="0 0 24 24" aria-hidden="true">${icon}</svg></span>
          <div>
            <h2 class="section-title">${title}</h2>
            <div class="section-caption">${caption}</div>
          </div>
        </div>
      </div>
      ${body}
    </section>`;

  const legend = (items) => `<div class="prof-legend">${items.map(([swatch, label]) => `<span class="prof-key">${swatch}${label}</span>`).join("")}</div>`;
  const agentKeys = () => trace.agents.map((a) => [`<i class="prof-swatch" style="background: ${a.color}"></i>`, esc(a.short)]);
  const WAIT_KEY = ['<i class="prof-swatch is-wait"></i>', "GPU idle, every agent on a tool"];

  const traceView = () => {
    const s = trace.summary;
    const agents = trace.agents;
    const winShare = s.winBackUs / trace.duration;
    return `
      <header class="prof-head">
        <div class="prof-head-text">
          <p class="prof-eyebrow">Trace</p>
          <h1 class="prof-title">${esc(fileName)}</h1>
          <p class="prof-meta">${metaLine(trace.meta)}</p>
        </div>
        <div class="prof-actions">
          <button class="prof-choose" type="button" data-open>Open Trace…</button>
          <button class="prof-close" type="button" data-close>Close</button>
        </div>
      </header>

      <section class="prof-stats">
        ${stat("Duration", duration(trace.duration), `${count(agents.length, "agent", "agents")}, ${count(trace.steps.length, "step", "steps")}`)}
        ${stat("GPU busy", percent(s.busyShare), `${duration(s.busyUs)} of ${duration(trace.duration)}`)}
        ${stat('<i class="prof-swatch is-wait"></i>Time you can win back', duration(s.winBackUs), `The GPU sat idle while every agent waited on a tool: ${percent(winShare)} of the run.`, "is-headline")}
        ${stat("Peak KV cache", trace.pageBytes ? bytes(s.peakKvBytes) : "—", trace.poolBytes ? `of a ${bytes(trace.poolBytes)} pool, ${count(trace.evicts.length, "eviction", "evictions")}` : count(trace.evicts.length, "eviction", "evictions"))}
      </section>

      <section class="prof-agents">
        <div class="prof-table-scroll">
          <table class="prof-table">
            <thead><tr><th scope="col">Agent</th><th scope="col" class="prof-split-cell">Time</th><th scope="col">Prefill</th><th scope="col">Decode</th><th scope="col">Tool</th><th scope="col">Queued</th><th scope="col">Idle</th><th scope="col">Peak KV</th><th scope="col">GPU share</th></tr></thead>
            <tbody>${agentRows()}</tbody>
          </table>
        </div>
      </section>

      <div class="prof-zoom" role="group" aria-label="Zoom">
        <span class="prof-range" data-range></span>
        <span class="spacer"></span>
        <button class="prof-zoom-button" type="button" data-zoom="out" aria-label="Zoom out"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8h9"/></svg></button>
        <input class="prof-zoom-slider" type="range" min="0" max="1000" value="0" aria-label="Zoom" data-slider>
        <button class="prof-zoom-button" type="button" data-zoom="in" aria-label="Zoom in"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8h9M8 3.5v9"/></svg></button>
        <button class="prof-fit" type="button" data-zoom="fit">Fit</button>
      </div>

      ${section("Timeline", "Every agent, every tool call, every idle moment. Pinch or ⌘-scroll to zoom, drag to pan.",
        `${legend([
          ['<i class="prof-swatch is-prefill"></i>', "Prefill"],
          ['<i class="prof-swatch is-decode"></i>', "Decode"],
          ['<i class="prof-swatch is-tool"></i>', "Tool"],
          ['<i class="prof-swatch is-queued"></i>', "Queued"],
          ['<i class="prof-swatch is-idle"></i>', "Idle"],
          WAIT_KEY,
        ])}<div class="prof-panel"><canvas class="prof-canvas" data-panel="timeline" aria-label="Timeline of every agent, the scheduler and the GPU"></canvas></div>`,
        "#0a84ff", '<path d="M4 7h9M4 12h5M11 12h9M4 17h12"/>')}

      ${section("Memory by Agent", "The KV cache each agent holds, the free pages left in the pool, and the device memory allocated.",
        `${legend([...agentKeys(), ['<i class="prof-swatch is-free"></i>', "Free"], ['<i class="prof-swatch is-line"></i>', "Device memory"]])}<div class="prof-panel"><canvas class="prof-canvas" data-panel="memory" aria-label="KV cache memory by agent over time"></canvas></div>`,
        "#30d158", '<rect x="4" y="7" width="16" height="10" rx="1.5"/><path d="M8 7V5M12 7V5M16 7V5M8 19v-2M12 19v-2M16 19v-2"/>')}

      ${section("GPU by Agent", "Each agent’s share of the GPU’s time; the outline is the total. Where it falls to nothing, the GPU is idle.",
        `${legend([...agentKeys(), ['<i class="prof-swatch is-line is-strong"></i>', "GPU busy"], WAIT_KEY])}<div class="prof-panel"><canvas class="prof-canvas" data-panel="gpu" aria-label="GPU busy time by agent"></canvas></div>`,
        "#ff9f0a", '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>')}`;
  };

  // ---------- drawing ----------

  const readColors = () => {
    const style = getComputedStyle(element);
    const css = (name) => style.getPropertyValue(name).trim();
    colors = {
      label: css("--color-label"),
      secondary: css("--color-label-secondary"),
      tertiary: css("--color-label-tertiary"),
      quaternary: css("--color-label-quaternary"),
      grid: css("--color-separator-light"),
      separator: css("--color-separator"),
      fill: css("--color-fill"),
      wait: css("--color-warning"),
      background: css("--color-background"),
      font: getComputedStyle(document.body).fontFamily,
      agents: Array.from({ length: AGENT_COLORS }, (_, i) => css(`--prof-agent-${i + 1}`)),
    };
  };
  const colorOf = (a) => colors.agents[a.slot - 1];

  const panels = () => [...element.querySelectorAll("canvas[data-panel]")];

  // the canvas at its laid-out width and the given height, sharp on a Retina screen
  const prepare = (canvas, height) => {
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.parentElement.clientWidth;
    canvas.style.height = `${height}px`;
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.font = `11px ${colors.font}`;
    return { ctx, width, height, x0: gutter(), x1: width - 10 };
  };

  const xOf = (t, g) => g.x0 + ((t - view.t0) / (view.t1 - view.t0)) * (g.x1 - g.x0);
  const tOf = (x, g) => view.t0 + ((x - g.x0) / (g.x1 - g.x0)) * (view.t1 - view.t0);

  const ticks = (g) => {
    const step = niceStep((view.t1 - view.t0) / Math.max(2, (g.x1 - g.x0) / (isPhone() ? 70 : 100)));
    const out = [];
    for (let t = Math.ceil(view.t0 / step) * step; t <= view.t1; t += step) out.push(t);
    return { step, out };
  };

  const fitText = (ctx, text, room) => {
    if (ctx.measureText(text).width <= room) return text;
    let cut = text;
    while (cut.length > 1 && ctx.measureText(`${cut}…`).width > room) cut = cut.slice(0, -1);
    return `${cut}…`;
  };

  // vertical grid lines at the ticks, and their times along the top or bottom edge
  const grid = (g, top, bottom, labelY) => {
    const { ctx } = g;
    const { step, out } = ticks(g);
    ctx.lineWidth = 1;
    ctx.strokeStyle = colors.grid;
    ctx.fillStyle = colors.tertiary;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const t of out) {
      const x = Math.round(xOf(t, g)) + 0.5;
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.stroke();
      if (labelY !== undefined) ctx.fillText(instant(t, step), Math.min(Math.max(x, g.x0 + 14), g.x1 - 14), labelY);
    }
  };

  // the stretches where every agent waits on a tool and the GPU has nothing: a faint band through the panel
  const waitBands = (g, top, bottom) => {
    const { ctx } = g;
    ctx.fillStyle = colors.wait;
    ctx.globalAlpha = 0.12;
    const from = firstEndingAfter(trace.winBack, view.t0);
    for (let i = from; i < trace.winBack.length && trace.winBack[i].ts < view.t1; i += 1) {
      const x0 = Math.max(g.x0, xOf(trace.winBack[i].ts, g));
      const x1 = Math.min(g.x1, xOf(trace.winBack[i].end, g));
      ctx.fillRect(x0, top, Math.max(1, x1 - x0), bottom - top);
    }
    ctx.globalAlpha = 1;
  };

  const cursor = (g, top, bottom) => {
    if (hoverT === null || hoverT < view.t0 || hoverT > view.t1) return;
    const { ctx } = g;
    const x = Math.round(xOf(hoverT, g)) + 0.5;
    ctx.strokeStyle = colors.secondary;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();
  };

  const rounded = (ctx, x, y, w, h, r) => {
    ctx.beginPath();
    if (w > 2 * r + 1 && ctx.roundRect) ctx.roundRect(x, y, w, h, r);
    else ctx.rect(x, y, w, h);
  };

  // many small spans in one colour, joined where they fall within a pixel of each other so a long trace stays fast
  const runs = (g, items, y, h, color, alpha) => {
    const { ctx } = g;
    ctx.fillStyle = color;
    ctx.globalAlpha = alpha;
    let start = null;
    let end = null;
    const flush = () => {
      if (start !== null) ctx.fillRect(start, y, Math.max(1, end - start), h);
    };
    for (let i = firstEndingAfter(items, view.t0); i < items.length && items[i].ts < view.t1; i += 1) {
      const x0 = Math.max(g.x0, xOf(items[i].ts, g));
      const x1 = Math.min(g.x1, xOf(items[i].end, g));
      if (start !== null && x0 <= end + 0.75) end = Math.max(end, x1);
      else {
        flush();
        start = x0;
        end = x1;
      }
    }
    flush();
    ctx.globalAlpha = 1;
  };

  const laneLabel = (g, text, y, color, strong) => {
    const { ctx } = g;
    ctx.font = `${strong ? 500 : 400} ${isPhone() ? 11 : 12}px ${colors.font}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    let x = isPhone() ? 2 : 4;
    if (color) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x + 3.5, y, 3.5, 0, Math.PI * 2);
      ctx.fill();
      x += 12;
    }
    ctx.fillStyle = strong ? colors.label : colors.secondary;
    ctx.fillText(fitText(ctx, text, g.x0 - x - 10), x, y);
  };

  const timelineHeight = () => AXIS + trace.agents.length * LANE + 12 + 2 * ENGINE_LANE + 6;

  const drawTimeline = (canvas) => {
    const g = prepare(canvas, timelineHeight());
    const { ctx } = g;
    const lanesBottom = AXIS + trace.agents.length * LANE;
    const engineTop = lanesBottom + 12;
    const bottom = engineTop + 2 * ENGINE_LANE;
    grid(g, AXIS - 4, bottom, 11);
    waitBands(g, AXIS, bottom);

    // the agents, one lane each: the lifetime as a hairline, the phases on it
    trace.agents.forEach((a, i) => {
      const mid = AXIS + i * LANE + LANE / 2;
      const color = colorOf(a);
      laneLabel(g, isPhone() ? a.short : a.label, mid, color, true);
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.35;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(Math.max(g.x0, xOf(a.start, g)), Math.round(mid) + 0.5);
      ctx.lineTo(Math.min(g.x1, xOf(a.end, g)), Math.round(mid) + 0.5);
      ctx.stroke();
      ctx.globalAlpha = 1;
      for (let k = firstEndingAfter(a.spans, view.t0); k < a.spans.length && a.spans[k].ts < view.t1; k += 1) {
        const span = a.spans[k];
        const x0 = Math.max(g.x0, xOf(span.ts, g));
        const x1 = Math.min(g.x1, xOf(span.end, g));
        const w = Math.max(1, x1 - x0);
        if (span.name === "queued") {
          ctx.fillStyle = colors.tertiary;
          rounded(ctx, x0, mid - 3, w, 6, 3);
          ctx.fill();
        } else if (span.name === "tool") {
          ctx.fillStyle = color;
          ctx.globalAlpha = 0.14;
          rounded(ctx, x0, mid - 9, w, 18, 4);
          ctx.fill();
          if (w > 3) {
            ctx.globalAlpha = 0.6;
            ctx.strokeStyle = color;
            rounded(ctx, x0 + 0.5, mid - 8.5, w - 1, 17, 4);
            ctx.stroke();
          }
          ctx.globalAlpha = 1;
        } else {
          ctx.fillStyle = color;
          ctx.globalAlpha = span.name === "decode" ? 0.5 : 1;
          rounded(ctx, x0, mid - 9, w, 18, 4);
          ctx.fill();
          ctx.globalAlpha = 1;
        }
      }
    });

    // the engine under them: the scheduler's steps, then the GPU's work
    ctx.strokeStyle = colors.separator;
    ctx.beginPath();
    ctx.moveTo(0, lanesBottom + 6.5);
    ctx.lineTo(g.width, lanesBottom + 6.5);
    ctx.stroke();
    laneLabel(g, "Scheduler", engineTop + ENGINE_LANE / 2, null, false);
    runs(g, trace.steps, engineTop + 7, ENGINE_LANE - 14, colors.secondary, 0.55);
    laneLabel(g, "GPU", engineTop + ENGINE_LANE * 1.5, null, false);
    runs(g, trace.busy, engineTop + ENGINE_LANE + 5, ENGINE_LANE - 10, colors.label, 0.7);
    // evictions: a small mark on the scheduler lane
    ctx.fillStyle = colors.secondary;
    for (const evict of trace.evicts) {
      if (evict.ts < view.t0 || evict.ts > view.t1) continue;
      const x = xOf(evict.ts, g);
      ctx.beginPath();
      ctx.moveTo(x - 4, engineTop + 1);
      ctx.lineTo(x + 4, engineTop + 1);
      ctx.lineTo(x, engineTop + 6);
      ctx.fill();
    }
    cursor(g, AXIS - 4, bottom);
  };

  // stacked areas over the visible window: one column per pixel, each the mean of the counter over its span of time
  const stack = (g, data, keys, fills, top, bottom, max) => {
    const { ctx } = g;
    const n = Math.max(1, Math.round(g.x1 - g.x0));
    const dt = (view.t1 - view.t0) / n;
    const base = new Float64Array(n);
    const scale = (bottom - top) / (max || 1);
    keys.forEach((key, k) => {
      const tops = new Float64Array(n);
      for (let i = 0; i < n; i += 1) tops[i] = base[i] + data.mean(key, view.t0 + i * dt, view.t0 + (i + 1) * dt);
      const [fill, alpha, edge] = fills[k];
      ctx.beginPath();
      ctx.moveTo(g.x0, bottom - base[0] * scale);
      for (let i = 0; i < n; i += 1) {
        ctx.lineTo(g.x0 + i, bottom - tops[i] * scale);
        ctx.lineTo(g.x0 + i + 1, bottom - tops[i] * scale);
      }
      for (let i = n - 1; i >= 0; i -= 1) {
        ctx.lineTo(g.x0 + i + 1, bottom - base[i] * scale);
        ctx.lineTo(g.x0 + i, bottom - base[i] * scale);
      }
      ctx.closePath();
      ctx.fillStyle = fill;
      ctx.globalAlpha = alpha;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (edge) {
        ctx.strokeStyle = fill;
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i < n; i += 1) {
          if (tops[i] - base[i] <= 0) continue;
          ctx.moveTo(g.x0 + i, bottom - tops[i] * scale);
          ctx.lineTo(g.x0 + i + 1, bottom - tops[i] * scale);
        }
        ctx.stroke();
      }
      base.set(tops);
    });
  };

  const line = (g, data, key, top, bottom, max, color, width) => {
    const { ctx } = g;
    const n = Math.max(1, Math.round(g.x1 - g.x0));
    const dt = (view.t1 - view.t0) / n;
    const scale = (bottom - top) / (max || 1);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineJoin = "round";
    ctx.beginPath();
    for (let i = 0; i < n; i += 1) {
      const y = bottom - data.mean(key, view.t0 + i * dt, view.t0 + (i + 1) * dt) * scale;
      if (i === 0) ctx.moveTo(g.x0, y);
      else ctx.lineTo(g.x0 + i, y);
      ctx.lineTo(g.x0 + i + 1, y);
    }
    ctx.stroke();
  };

  // horizontal grid lines with their values in the gutter
  const yGrid = (g, top, bottom, max, steps, label) => {
    const { ctx } = g;
    ctx.font = `11px ${colors.font}`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= steps; i += 1) {
      const y = Math.round(bottom - ((bottom - top) * i) / steps) + 0.5;
      ctx.strokeStyle = i === 0 ? colors.separator : colors.grid;
      ctx.beginPath();
      ctx.moveTo(g.x0, y);
      ctx.lineTo(g.x1, y);
      ctx.stroke();
      ctx.fillStyle = colors.tertiary;
      ctx.fillText(label((max * i) / steps), g.x0 - 8, y);
    }
  };

  const MEMORY = { top: 10, plot: 150, gap: 22, strip: 44, axis: 22 };

  const drawMemory = (canvas) => {
    const m = MEMORY;
    const height = m.top + m.plot + m.gap + m.strip + m.axis;
    const g = prepare(canvas, height);
    const { ctx } = g;
    const bottom = m.top + m.plot;
    const keys = trace.agents.map((a) => a.key);
    const pageBytes = trace.pageBytes || 1;
    const poolPages = Number(trace.meta.kv_pages_total) || Math.max(1, ...trace.counters.kv_pages.map((p) => keys.reduce((s, k) => s + (Number(p.args[k]) || 0), 0) + (Number(p.args.free) || 0)));
    const stripTop = bottom + m.gap;
    const stripBottom = stripTop + m.strip;
    grid(g, m.top, stripBottom, stripBottom + 12);
    waitBands(g, m.top, bottom);
    yGrid(g, m.top, bottom, poolPages * pageBytes, 2, (v) => (trace.pageBytes ? bytes(v) : `${Math.round(v)}`));
    stack(g, { mean: (key, t0, t1) => trace.kv.mean(key, t0, t1) }, [...keys, "free"],
      [...trace.agents.map((a) => [colorOf(a), 0.7, true]), [colors.fill, 1, false]], m.top, bottom, poolPages);
    ctx.fillStyle = colors.secondary;
    for (const evict of trace.evicts) {
      if (evict.ts < view.t0 || evict.ts > view.t1) continue;
      const x = xOf(evict.ts, g);
      ctx.beginPath();
      ctx.moveTo(x - 4, m.top - 6);
      ctx.lineTo(x + 4, m.top - 6);
      ctx.lineTo(x, m.top - 1);
      ctx.fill();
    }
    // device memory: its own strip from zero, since it holds the weights too and dwarfs the KV pool
    const peak = trace.memory.size ? trace.memory.max("allocated_gb") : 0;
    laneLabel(g, "Device", stripTop + 8, null, false);
    ctx.font = `11px ${colors.font}`;
    ctx.fillStyle = colors.tertiary;
    ctx.textAlign = "left";
    if (peak) ctx.fillText(`${peak.toFixed(2)} GB`, isPhone() ? 2 : 4, stripTop + 24);
    ctx.strokeStyle = colors.separator;
    ctx.beginPath();
    ctx.moveTo(g.x0, stripBottom + 0.5);
    ctx.lineTo(g.x1, stripBottom + 0.5);
    ctx.stroke();
    if (peak) line(g, trace.memory, "allocated_gb", stripTop + 4, stripBottom, peak * 1.05, colors.secondary, 1.5);
    cursor(g, m.top, stripBottom);
  };

  const GPU = { top: 10, plot: 150, axis: 22 };

  const drawGpu = (canvas) => {
    const height = GPU.top + GPU.plot + GPU.axis;
    const g = prepare(canvas, height);
    const bottom = GPU.top + GPU.plot;
    grid(g, GPU.top, bottom, bottom + 12);
    waitBands(g, GPU.top, bottom);
    yGrid(g, GPU.top, bottom, 100, 2, (v) => `${Math.round(v)}%`);
    stack(g, trace.share, trace.agents.map((a) => a.key), trace.agents.map((a) => [colorOf(a), 0.7, false]), GPU.top, bottom, 100);
    if (trace.busyPct.size) line(g, trace.busyPct, "pct", GPU.top, bottom, 100, colors.label, 1.25);
    cursor(g, GPU.top, bottom);
  };

  const DRAW = { timeline: drawTimeline, memory: drawMemory, gpu: drawGpu };

  const draw = () => {
    frame = 0;
    if (!trace || element.hidden) return;
    for (const canvas of panels()) DRAW[canvas.dataset.panel](canvas);
    const range = element.querySelector("[data-range]");
    if (range) range.textContent = `${duration(view.t0)} – ${duration(view.t1)}`;
  };
  const redraw = () => {
    if (!frame) frame = requestAnimationFrame(draw);
  };

  // ---------- zoom and pan ----------

  const minSpan = () => Math.min(trace.duration, Math.max(200, trace.duration / 20000));
  const maxZoom = () => trace.duration / minSpan();

  const setView = (t0, t1) => {
    const span = Math.min(trace.duration, Math.max(minSpan(), t1 - t0));
    let start = Math.max(0, Math.min(t0, trace.duration - span));
    if (t1 - t0 !== span) start = Math.max(0, Math.min((t0 + t1) / 2 - span / 2, trace.duration - span));
    view.t0 = start;
    view.t1 = start + span;
    const slider = element.querySelector("[data-slider]");
    if (slider) slider.value = String(Math.round((1000 * Math.log(trace.duration / span)) / Math.log(Math.max(1.0001, maxZoom()))));
    redraw();
  };

  const zoomAt = (t, factor) => {
    const span = (view.t1 - view.t0) / factor;
    const share = (t - view.t0) / (view.t1 - view.t0);
    setView(t - share * span, t - share * span + span);
  };

  const geometryOf = (canvas) => ({ x0: gutter(), x1: canvas.clientWidth - 10 });

  // ---------- hover cards ----------

  const card = (title, sub, rows) => `
    <div class="tip-title">${title}</div>
    ${sub ? `<div class="tip-sub">${sub}</div>` : ""}
    ${rows.length ? `<div class="tip-rows">${rows.map(([label, value, color]) => `
      <div class="prof-tip-row"><span class="tip-name">${color ? `<i class="tip-dot" style="background: ${color}"></i>` : ""}${label}</span><span>${value}</span></div>`).join("")}</div>` : ""}`;

  const PHASE_NAMES = { prefill: "Prefill", decode: "Decode", tool: "Tool", queued: "Queued" };

  const spanCard = (a, span) => {
    const rows = [["Start", at3(span.ts)], ["Duration", duration(span.end - span.ts)]];
    if (span.name === "prefill") {
      rows.push(["Tokens", (Number(span.args.tokens) || 0).toLocaleString()]);
      if (span.args.cached_tokens !== undefined) rows.push(["Cached tokens", (Number(span.args.cached_tokens) || 0).toLocaleString()]);
      if (span.end > span.ts && span.args.tokens) rows.push(["Speed", `${Math.round((span.args.tokens * 1e6) / (span.end - span.ts)).toLocaleString()} tok/s`]);
    } else if (span.name === "decode") {
      rows.push(["Tokens", (Number(span.args.tokens) || 0).toLocaleString()]);
      if (span.end > span.ts && span.args.tokens) rows.push(["Speed", `${((span.args.tokens * 1e6) / (span.end - span.ts)).toFixed(1)} tok/s`]);
    } else if (span.name === "tool") {
      rows.push(["Tool", esc(span.args.tool || "—")]);
    }
    const title = span.name === "tool" && span.args.tool ? `Tool: ${esc(span.args.tool)}` : PHASE_NAMES[span.name];
    return card(title, `<span class="prof-tip-agent" style="--agent: ${a.color}">${esc(a.label)}</span>`, rows);
  };

  // the gap around t among sorted spans, bounded by [from, to]
  const gapAround = (items, t, from, to) => {
    const i = firstEndingAfter(items, t);
    return { ts: i > 0 ? Math.max(from, items[i - 1].end) : from, end: i < items.length ? Math.min(to, items[i].ts) : to };
  };

  const timelineHit = (canvas, x, y) => {
    const g = geometryOf(canvas);
    const t = tOf(x, g);
    const slop = (4 * (view.t1 - view.t0)) / (g.x1 - g.x0);  // a few pixels either side: a thin span can still be pointed at
    const near = (items) => at(items, t) || at(items, t - slop) || at(items, t + slop);
    const lane = Math.floor((y - AXIS) / LANE);
    if (lane >= 0 && lane < trace.agents.length) {
      const a = trace.agents[lane];
      const span = near(a.spans);
      if (span) return spanCard(a, span);
      if (t < a.start || t > a.end) return null;
      const gap = gapAround(a.spans, t, a.start, a.end);
      return card("Idle", `<span class="prof-tip-agent" style="--agent: ${a.color}">${esc(a.label)}</span>`, [["Start", at3(gap.ts)], ["Duration", duration(gap.end - gap.ts)]]);
    }
    const engineTop = AXIS + trace.agents.length * LANE + 12;
    if (y >= engineTop && y < engineTop + ENGINE_LANE) {
      const step = near(trace.steps);
      if (!step) return null;
      const args = step.args;
      const rows = [["Start", at3(step.ts)], ["Duration", duration(step.end - step.ts)], ["GPU", duration(Number(args.gpu_us) || 0)],
        ["Prefill tokens", (Number(args.prefill_tokens) || 0).toLocaleString()], ["Decode tokens", (Number(args.decode_tokens) || 0).toLocaleString()]];
      for (const [id, n] of Object.entries(args.agents || {})) {
        const a = trace.agentById(id);
        if (a) rows.push([esc(a.short), [n.prefill ? `${n.prefill} prefill` : "", n.decode ? `${n.decode} decode` : ""].filter(Boolean).join(", ") || "—", a.color]);
      }
      return card(`Step ${esc(args.step ?? "")}`, "Scheduler", rows);
    }
    if (y >= engineTop + ENGINE_LANE && y < engineTop + 2 * ENGINE_LANE) {
      const gpu = near(trace.gpus);
      if (gpu) return card("GPU busy", gpu.args.step !== undefined ? `Step ${esc(gpu.args.step)}` : "", [["Start", at3(gpu.ts)], ["Duration", duration(gpu.end - gpu.ts)]]);
      const gap = gapAround(trace.busy, t, 0, trace.duration);
      const waiting = at(trace.winBack, t);
      return card("GPU idle", waiting ? "Every agent is waiting on a tool" : "", [["Start", at3(gap.ts)], ["Duration", duration(gap.end - gap.ts)]]);
    }
    return null;
  };

  const memoryHit = (canvas, x) => {
    const t = tOf(x, geometryOf(canvas));
    if (t < 0 || t > trace.duration) return null;
    const unit = (pages) => (trace.pageBytes ? bytes(pages * trace.pageBytes) : `${pages.toLocaleString()} pages`);
    const rows = trace.agents.map((a) => [esc(a.short), unit(trace.kv.value(a.key, t)), a.color]);
    rows.push(["Free", unit(trace.kv.value("free", t))]);
    if (trace.memory.size) rows.push(["Device memory", `${trace.memory.value("allocated_gb", t).toFixed(2)} GB`]);
    const slop = (6 * (view.t1 - view.t0)) / (canvas.clientWidth - gutter());
    for (const evict of trace.evicts) {
      if (Math.abs(evict.ts - t) > slop) continue;
      const a = trace.agentById(evict.args.agent);
      rows.push([`Evicted ${esc(a ? a.short : `agent-${evict.args.agent}`)}`, unit(Number(evict.args.pages) || 0)]);
    }
    return card(at3(t), "KV cache", rows);
  };

  const gpuHit = (canvas, x) => {
    const t = tOf(x, geometryOf(canvas));
    if (t < 0 || t > trace.duration) return null;
    const rows = [["GPU busy", `${trace.busyPct.value("pct", t).toFixed(1)}%`]];
    for (const a of trace.agents) rows.push([esc(a.short), `${trace.share.value(a.key, t).toFixed(1)}%`, a.color]);
    return card(at3(t), at(trace.winBack, t) ? "Idle: every agent is waiting on a tool" : "Share of the last 10 ms", rows);
  };

  const HIT = { timeline: timelineHit, memory: memoryHit, gpu: gpuHit };

  const showTip = (html, cx, cy) => {
    if (!html) {
      hideTip();
      return;
    }
    tooltip.innerHTML = html;
    tooltip.classList.add("is-card");
    tooltip.hidden = false;
    const x = Math.min(cx + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(cy + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  };
  const hideTip = () => {
    tooltip.hidden = true;
    tooltip.classList.remove("is-card");
  };

  // every panel answers the same gestures, so the three move as one: pinch or ⌘/⌥-scroll zooms, a sideways
  // scroll or a drag pans, a double-click zooms in; a plain vertical scroll is left to the page
  const wirePanels = () => {
    const pointers = new Map();
    let pinch = null;
    let drag = null;

    for (const canvas of panels()) {
      const local = (event) => {
        const box = canvas.getBoundingClientRect();
        return { x: event.clientX - box.left, y: event.clientY - box.top };
      };
      canvas.addEventListener("wheel", (event) => {
        const { x } = local(event);
        const g = geometryOf(canvas);
        const dx = event.deltaMode === 1 ? event.deltaX * 16 : event.deltaX;
        const dy = event.deltaMode === 1 ? event.deltaY * 16 : event.deltaY;
        if (event.ctrlKey || event.metaKey || event.altKey) {
          event.preventDefault();
          zoomAt(tOf(Math.max(g.x0, x), g), Math.exp(-dy * 0.01));
        } else if (Math.abs(dx) > Math.abs(dy) || event.shiftKey) {
          event.preventDefault();
          const shift = ((event.shiftKey && !dx ? dy : dx) * (view.t1 - view.t0)) / (g.x1 - g.x0);
          setView(view.t0 + shift, view.t1 + shift);
        }
      }, { passive: false });

      canvas.addEventListener("pointerdown", (event) => {
        pointers.set(event.pointerId, local(event));
        canvas.setPointerCapture(event.pointerId);
        if (pointers.size === 2) {
          const [a, b] = [...pointers.values()];
          const g = geometryOf(canvas);
          pinch = { distance: Math.abs(a.x - b.x) || 1, t: tOf((a.x + b.x) / 2, g), t0: view.t0, t1: view.t1 };
          drag = null;
        } else {
          drag = { x: local(event).x, t0: view.t0, t1: view.t1, moved: false };
        }
      });
      canvas.addEventListener("pointermove", (event) => {
        const point = local(event);
        const g = geometryOf(canvas);
        if (pointers.has(event.pointerId)) pointers.set(event.pointerId, point);
        if (pinch && pointers.size === 2) {
          const [a, b] = [...pointers.values()];
          const factor = (Math.abs(a.x - b.x) || 1) / pinch.distance;
          const span = (pinch.t1 - pinch.t0) / factor;
          const share = (pinch.t - pinch.t0) / (pinch.t1 - pinch.t0);
          setView(pinch.t - share * span, pinch.t - share * span + span);
          hideTip();
          return;
        }
        if (drag && pointers.has(event.pointerId)) {
          const dx = point.x - drag.x;
          if (Math.abs(dx) > 3) drag.moved = true;
          if (drag.moved) {
            const shift = (-dx * (drag.t1 - drag.t0)) / (g.x1 - g.x0);
            setView(drag.t0 + shift, drag.t1 + shift);
            canvas.classList.add("is-dragging");
            hideTip();
            return;
          }
        }
        hoverT = point.x >= g.x0 && point.x <= g.x1 ? tOf(point.x, g) : null;
        redraw();
        showTip(hoverT === null ? null : HIT[canvas.dataset.panel](canvas, point.x, point.y), event.clientX, event.clientY);
      });
      const release = (event) => {
        pointers.delete(event.pointerId);
        if (pointers.size < 2) pinch = null;
        if (!pointers.size) drag = null;
        canvas.classList.remove("is-dragging");
      };
      canvas.addEventListener("pointerup", release);
      canvas.addEventListener("pointercancel", release);
      canvas.addEventListener("pointerleave", (event) => {
        if (event.pointerType !== "mouse") return;
        hoverT = null;
        hideTip();
        redraw();
      });
      canvas.addEventListener("dblclick", (event) => {
        const g = geometryOf(canvas);
        zoomAt(tOf(Math.max(g.x0, local(event).x), g), event.shiftKey ? 0.5 : 2);
      });
    }

    element.querySelector("[data-slider]").addEventListener("input", (event) => {
      const span = trace.duration / maxZoom() ** (Number(event.target.value) / 1000);
      const mid = (view.t0 + view.t1) / 2;
      setView(mid - span / 2, mid + span / 2);
    });
    element.querySelectorAll("[data-zoom]").forEach((button) => button.addEventListener("click", () => {
      const mid = (view.t0 + view.t1) / 2;
      if (button.dataset.zoom === "fit") setView(0, trace.duration);
      else zoomAt(mid, button.dataset.zoom === "in" ? 2 : 0.5);
    }));
  };

  // ---------- opening and closing ----------

  const inner = () => element.querySelector(".prof-inner");

  const showEmpty = (title, text) => {
    trace = null;
    hideTip();
    element.classList.remove("has-trace");
    inner().innerHTML = EMPTY;
    if (title) {
      inner().querySelector(".prof-drop-title").textContent = title;
      inner().querySelector(".prof-drop-text").innerHTML = text;
    }
  };

  const refuse = (name, reason) => showEmpty("Not a Pie Trace", `“${esc(name)}” can’t be opened. ${reason}`);

  const show = (text, name) => {
    let parsed;
    try {
      parsed = summarize(parse(text));
    } catch (error) {
      if (!(error instanceof TraceError)) console.error(error);
      refuse(name, error instanceof TraceError ? error.message : "It couldn’t be read.");
      return;
    }
    trace = parsed;
    fileName = name;
    hoverT = null;
    element.classList.add("has-trace");
    inner().innerHTML = traceView();
    element.scrollTop = 0;
    readColors();
    wirePanels();
    setView(0, trace.duration);
  };

  const open = (file) => {
    if (!file.name.toLowerCase().endsWith(EXT)) {
      refuse(file.name, `Choose a file that ends in ${EXT}.`);
      return;
    }
    file.text().then((text) => show(text, file.name), () => refuse(file.name, "It couldn’t be read."));
  };

  const openSample = () => {
    const name = SAMPLE.split("/").pop();
    fetch(SAMPLE)
      .then((response) => (response.ok ? response.text() : Promise.reject(new Error(response.statusText))))
      .then((text) => show(text, name), () => showEmpty("Sample Unavailable", "The sample trace couldn’t be loaded. Check your connection and try again."));
  };

  const wire = () => {
    const input = element.querySelector(".prof-input");
    element.addEventListener("click", (event) => {
      if (event.target.closest("[data-open]")) input.click();
      else if (event.target.closest("[data-sample]")) openSample();
      else if (event.target.closest("[data-close]")) showEmpty();
    });
    input.addEventListener("change", () => {
      if (input.files[0]) open(input.files[0]);
      input.value = "";
    });
    // the whole page is the drop target: it takes the accent ring while a file is held over it
    let depth = 0;
    const hasFile = (event) => [...(event.dataTransfer?.types || [])].includes("Files");
    element.addEventListener("dragenter", (event) => {
      if (!hasFile(event)) return;
      depth += 1;
      element.classList.add("is-dropping");
    });
    element.addEventListener("dragleave", () => {
      depth = Math.max(0, depth - 1);
      if (!depth) element.classList.remove("is-dropping");
    });
    element.addEventListener("dragover", (event) => {
      if (hasFile(event)) event.preventDefault();
    });
    element.addEventListener("drop", (event) => {
      event.preventDefault();
      depth = 0;
      element.classList.remove("is-dropping");
      const file = event.dataTransfer.files[0];
      if (file) open(file);
    });
    element.addEventListener("scroll", hideTip);
    // the panels follow the window's width and the light or dark appearance
    new ResizeObserver(redraw).observe(element);
    new MutationObserver(() => {
      if (!trace) return;
      readColors();
      redraw();
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  };

  Pie.profiler = {
    element,
    // for tests and the console: open a trace from its text, as a dropped file would
    openText: (text, name = "trace.pie") => show(text, name),
    render(state) {
      element.hidden = state.table !== "profiler";
      if (element.hidden) {
        hideTip();
        return;
      }
      if (element.dataset.ready === "1") {
        redraw();
        return;
      }
      element.innerHTML = `<div class="method-inner prof-inner"></div><input class="prof-input" type="file" accept="${EXT}" hidden>`;
      element.dataset.ready = "1";
      showEmpty();
      wire();
    },
  };
})();
