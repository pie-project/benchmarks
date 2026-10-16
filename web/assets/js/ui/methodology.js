window.Pie = window.Pie || {};

// The Methods page: a ceiling estimator on top, then the roofline behind it, written as one page.
(() => {
  const element = document.getElementById("methodology");

  // GPU fp16 matmul TFLOPS per core. Apple10 is measured on the M5 Max (47 TFLOPS on 40 cores, with its neural accelerators);
  // the older ones are ALU count × clock. Estimates, editable in the specs.
  const TFLOPS_PER_CORE = { apple8: 0.36, apple9: 0.42, apple10: 1.17 };
  const BITS = { 4: 4.5, 8: 8.5, 16: 16 };  // bits per weight, with the quantization scales
  const CONTEXTS = [1024, 4096, 16384, 32768, 131072];
  const BATCHES = [1, 2, 4, 8, 16, 32, 64];
  const LINKS = { none: ["One device", 0, 0], tb5: ["Thunderbolt 5", 10, 30], pcie5: ["PCIe 5.0 ×16", 64, 10], nvlink: ["NVLink", 900, 3] };
  const USABLE = 0.75;  // the share of unified memory macOS lets the GPU wire by default

  const eq = (...lines) => `<pre class="methods-eq">${lines.join("\n")}</pre>`;
  const table = (head, body) => `<table class="methods-table">
      <thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>
      <tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>`;
  const cite = (href, name) => `<a href="${href}" target="_blank" rel="noopener">${name}</a>`;
  const kTok = (n) => (n >= 1024 ? `${Math.round(n / 1024)}K` : `${n}`);

  const machines = () => (Pie.store.rows("hardware") || []).map((h) => ({
    id: h.id,
    label: `${h.name} · ${h.memory_gib} GB`,
    bw: h.bandwidth_gbs || 0,
    tflops: +(((TFLOPS_PER_CORE[h.arch] || 0.4) * (h.gpu_cores || 0)).toFixed(1)),
    mem: h.memory_gib || 0,
    devices: h.count || 1,
    specs: [h.bandwidth_gbs && `${h.bandwidth_gbs} GB/s`, h.gpu_cores && `${h.gpu_cores}-core GPU`, h.cpu_cores && `${h.cpu_cores}-core CPU`, h.memory_gib && `${h.memory_gib} GB unified memory`].filter(Boolean).join(" · "),
  }));

  // hybrid families keep a fixed-size state in most layers: about a quarter of the cache of full attention
  const HYBRID = /qwen3_5|qwen3_6|qwen4/;
  const layersFor = (p) => (p <= 5 ? 32 : p <= 15 ? 40 : p <= 40 ? 64 : 80);
  const models = () => (Pie.store.rows("models") || []).filter((m) => m.params_b).map((m) => {
    const layers = layersFor(m.params_b);
    return {
      id: m.id,
      label: m.name,
      total: m.params_b,
      active: m.active_b || m.params_b,
      layers,
      // 8 KV heads × 128 dims × K and V × 2 bytes per layer
      kvKB: Math.round(layers * 4 * (HYBRID.test(m.family || "") ? 0.25 : 1)),
    };
  });

  const calculator = `
    <section class="methods-calc" aria-label="Theoretical ceiling estimator">
      <div class="calc-controls">
        <label class="calc-field is-wide"><span>Machine</span><select data-k="machine"></select></label>
        <label class="calc-field is-wide"><span>Model</span><select data-k="model"></select></label>
        <label class="calc-field"><span>Weights</span><select data-k="bits"><option value="4">4-bit</option><option value="8">8-bit</option><option value="16">16-bit</option></select></label>
        <label class="calc-field"><span>Context</span><select data-k="context">${CONTEXTS.map((c) => `<option value="${c}"${c === 4096 ? " selected" : ""}>${kTok(c)} tokens</option>`).join("")}</select></label>
        <label class="calc-field"><span>Requests</span><select data-k="batch">${BATCHES.map((b) => `<option value="${b}"${b === 8 ? " selected" : ""}>${b}</option>`).join("")}</select></label>
      </div>
      <p class="calc-specs" data-out="specs"></p>
      <div class="calc-results">
        <div class="calc-result"><span class="calc-label">Decode, one request</span><span class="calc-value" data-out="d1"></span><span class="calc-note" data-out="d1n"></span></div>
        <div class="calc-result"><span class="calc-label" data-out="dbl"></span><span class="calc-value" data-out="db"></span><span class="calc-note" data-out="dbn"></span></div>
        <div class="calc-result"><span class="calc-label">Prefill</span><span class="calc-value" data-out="pf"></span><span class="calc-note" data-out="pfn"></span></div>
      </div>
      <p class="calc-fit" data-out="fit"></p>
      <details class="calc-more">
        <summary>Specs used</summary>
        <div class="calc-inputs">
          <label><span>Memory bandwidth</span><input type="number" min="1" data-k="bw"><em>GB/s</em></label>
          <label><span>GPU compute (fp16)</span><input type="number" min="0.1" step="0.1" data-k="tflops"><em>TFLOPS</em></label>
          <label><span>Memory</span><input type="number" min="1" data-k="mem"><em>GB</em></label>
          <label><span>Devices</span><input type="number" min="1" max="64" data-k="devices"><em></em></label>
          <label><span>Interconnect</span><select data-k="link">${Object.entries(LINKS).map(([id, [name]]) => `<option value="${id}">${name}</option>`).join("")}</select><em></em></label>
          <label><span>Total parameters</span><input type="number" min="0.1" step="0.1" data-k="total"><em>B</em></label>
          <label><span>Active parameters</span><input type="number" min="0.1" step="0.1" data-k="active"><em>B</em></label>
          <label><span>Cache per token</span><input type="number" min="1" data-k="kvKB"><em>KB</em></label>
        </div>
        <p class="calc-footnote">Compute is estimated from the GPU core count: about 1.17 TFLOPS per core on M5-generation GPUs, as measured on the M5 Max, and 0.36–0.42 on earlier ones. Cache per token assumes 8 KV heads of 128 dimensions, a quarter of that for hybrid models. Without speculative decoding or SSD streaming.</p>
      </details>
    </section>`;

  // attainable FLOP/s against arithmetic intensity, log-log: the sloped memory roof meets the flat compute roof at the ridge
  const plot = `
    <figure class="methods-figure">
      <svg viewBox="0 0 640 330" role="img" aria-label="Roofline: attainable compute rises with arithmetic intensity until the ridge, then stays flat at peak compute. Decode at one request sits on the sloped, memory-bound part; batched decode and prefill sit on the flat, compute-bound part.">
        <path class="axis" d="M50 20V290H630"/>
        <path class="ridge" d="M372 60V290"/>
        <path class="roof" d="M142 290 372 60H625"/>
        <circle cx="152" cy="280" r="5"/><circle cx="430" cy="60" r="5"/><circle cx="590" cy="60" r="5"/>
        <text x="60" y="30">attainable FLOP/s (log)</text>
        <text x="630" y="314" text-anchor="end">arithmetic intensity, FLOP per byte (log)</text>
        <text x="170" y="284">decode, one request</text>
        <text x="430" y="48" text-anchor="middle">batched decode</text>
        <text x="590" y="48" text-anchor="middle">prefill</text>
        <text x="380" y="270">ridge = FLOPS ÷ BW</text>
        <text x="212" y="160" class="label" transform="rotate(-45 212 160)">memory-bound</text>
        <text x="500" y="80" class="label">compute-bound</text>
      </svg>
      <figcaption>Left of the ridge a step is limited by bandwidth; right of it, by compute.</figcaption>
    </figure>`;

  const content = `
    <div class="methods">
      <header class="methods-hero">
        <h1>Methods</h1>
        <p class="methods-lede">No magic. Trust, but check your provider.</p>
      </header>
      ${calculator}

      <section class="methods-section">
        <h2>The bound on one step.</h2>
        <p>Each step of the model takes at least the slowest of three times:</p>
        ${eq("step time ≥ max( bytes moved ÷ memory bandwidth,",
             "                 arithmetic ÷ peak compute,",
             "                 bytes exchanged ÷ interconnect )",
             "tokens/s  = tokens produced per step ÷ step time")}
        <p>The interconnect term applies only when a model spans several devices. The ratio of arithmetic to bytes is the step’s arithmetic intensity; where it equals peak compute ÷ bandwidth, the two roofs meet (${cite("https://doi.org/10.1145/1498765.1498785", "Williams et al., 2009")}).</p>
        ${plot}
      </section>

      <section class="methods-section">
        <h2>Decoding many requests.</h2>
        <p>Decode B requests at once, each with C tokens of context. The weights are read once per step and shared by all B; each request reads its own cache.</p>
        ${eq("bytes      ≈ W + B · C · k",
             "arithmetic ≈ 2 · P · B",
             "max tok/s  = B ÷ max( (W + B·C·k) ÷ BW,  2·P·B ÷ FLOPS )")}
        ${table(["Symbol", "Meaning"], [
          ["W", "Active weight bytes, read once per step"],
          ["k", "Cache bytes per token of context"],
          ["P", "Active parameters"],
          ["BW, FLOPS", "Memory bandwidth and peak compute of the device"],
        ])}
      </section>

      <section class="methods-section">
        <h2>Three regimes.</h2>
        <p>Which term dominates depends on the batch and the context length.</p>
        ${table(["Workload", "Limited by", "Ceiling"], [
          ["One request, short context", "Memory bandwidth (weights)", "BW ÷ W"],
          ["Many requests, short context", "Compute", "FLOPS ÷ 2P"],
          ["Long context, any batch", "Memory bandwidth (the cache)", "BW ÷ (C·k) per request, so batching stops helping"],
        ])}
      </section>

      <section class="methods-section">
        <h2>Prefill is compute-bound.</h2>
        <p>Reading the prompt handles hundreds of tokens per weight read, so prefill sits far right of the ridge:</p>
        ${eq("prefill tok/s ≈ FLOPS ÷ 2P")}
        <p>The workload that reaches the ceiling is a dense model with short contexts, large batches (or prefill) and no idle time. That is the clean benchmark case, where engines get closest to the ceiling.</p>
      </section>

      <section class="methods-section">
        <h2>What the number depends on.</h2>
        <p>Seven layers lie between the hardware and a finished task. Layers 1–2 set the ceiling, layer 3 is efficiency within one step, and layers 4–7 decide how much of the ceiling a workload actually reaches.</p>
        ${table(["Layer", "What it sets", "Further reading"], [
          ["1 · Hardware", "Bandwidth, compute, memory capacity, interconnect", ""],
          ["2 · Model shape", "Active parameters (P, W), cache bytes per token (k), MoE sparsity, linear-attention layers", cite("https://arxiv.org/abs/2412.06464", "Gated DeltaNet")],
          ["3 · Forward pass", "The share of the ceiling each step achieves: the kernels", `${cite("https://arxiv.org/abs/2205.14135", "FlashAttention")}, ${cite("https://arxiv.org/abs/2408.11743", "Marlin")}`],
          ["4 · Batch formation", "Tokens per step: concurrent requests, branches, speculative tokens; capped by memory and latency targets", `${cite("https://arxiv.org/abs/2309.06180", "PagedAttention")}, ${cite("https://arxiv.org/abs/2403.02310", "Sarathi-Serve")}, ${cite("https://arxiv.org/abs/2401.15077", "EAGLE")}`],
          ["5 · Time utilization", "Idle gaps between steps and during tool calls", `${cite("https://arxiv.org/abs/2502.13965", "Autellix")}, ${cite("https://arxiv.org/abs/2402.01869", "InferCept")}`],
          ["6 · Reuse", "Prefill avoided through caching", `${cite("https://arxiv.org/abs/2312.07104", "SGLang")}, ${cite("https://arxiv.org/abs/2411.19379", "Marconi")}`],
          ["7 · Usefulness", "Tokens that actually help finish the task", cite("https://arxiv.org/abs/2412.20993", "Certaindex")],
        ])}
      </section>

      <section class="methods-section">
        <h2>Adjusting the bound for agents.</h2>
        <p>The basic bound assumes an endless supply of short, independent requests. Agents break that in five ways, and each adds a term:</p>
        ${table(["What agents change", "The term to add"], [
          ["Long, growing contexts (30–100K tokens)", "Memory capacity caps the batch: B ≤ (memory − W) ÷ (C·k). Few long conversations fit, and the cache term C·k dominates the bytes, so the step is memory-bound again even with batching."],
          [`Mostly prefill (about 21× a chatbot’s, per ${cite("https://arxiv.org/abs/2606.16824", "CacheWise")})`, "Time splits between compute-bound prefill and memory-bound decode, weighted by the workload’s mix."],
          ["Tool waits", "Multiply by the duty cycle (1 − tool fraction), unless other work fills the gap."],
          ["Repeated history", "Multiply prefill cost by (1 − reuse rate)."],
          ["Sequential steps with latency targets", "One agent cannot batch with itself. The batch comes only from parallel agents or branches, and latency targets cap it."],
        ])}
        <p>For agents the useful ceiling is therefore roughly:</p>
        ${eq("useful tok/s ≈ min( compute ceiling,",
             "                    bandwidth ceiling with long-context cache,",
             "                    memory-capacity ceiling )",
             "               × (1 − idle share) × reuse factor × usefulness")}
        <p>For hybrid models such as Qwen3.6 and Qwen3.8, k is small, because most layers keep a fixed-size state instead of a growing cache. That loosens the capacity limit for long agent contexts, and it is why state checkpointing in the manner of ${cite("https://arxiv.org/abs/2411.19379", "Marconi")} matters.</p>
      </section>
    </div>`;

  const fmt = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const gb = (n) => (n >= 10 ? n.toFixed(0) : n.toFixed(1));

  // the roofline for one step of `batch` tokens: the slowest of bytes, arithmetic and interconnect
  const step = (s, batch) => {
    const bytesPerParam = BITS[s.bits] / 8;
    // a MoE step touches more experts as the batch grows; a dense model reads all of its weights at any batch
    const share = s.active / s.total;
    const weightGB = s.total * bytesPerParam * (share >= 1 ? 1 : 1 - (1 - share) ** batch);
    const cacheGB = batch * s.context * s.kvKB / 1e6;
    const bw = s.bw * s.devices;
    const flops = s.tflops * s.devices * 1e12;
    const memory = (weightGB + cacheGB) / bw;
    const compute = (2 * s.active * 1e9 * batch) / flops;
    // tensor parallel: two all-reduces of the hidden state per layer, each paying the link's latency
    const [, linkGBs, latencyUs] = LINKS[s.link];
    const hidden = Math.sqrt((s.total * 1e9) / (12 * s.layers));
    const link = s.devices > 1 && linkGBs ? 2 * s.layers * (latencyUs * 1e-6 + (batch * hidden * 2 * (s.devices - 1) / s.devices) / (linkGBs * 1e9)) : 0;
    const t = Math.max(memory, compute, link);
    const bound = t === link && link ? "interconnect-bound" : t === compute ? "compute-bound" : "bandwidth-bound";
    return { tps: batch / t, bound };
  };

  const state = {};
  const read = () => {
    element.querySelectorAll("[data-k]").forEach((input) => {
      const k = input.dataset.k;
      state[k] = ["machine", "model", "link"].includes(k) ? input.value : Number(input.value);
    });
  };
  const fill = (values) => Object.entries(values).forEach(([k, v]) => {
    const input = element.querySelector(`[data-k="${k}"]`);
    if (input) input.value = v;
  });

  const update = () => {
    read();
    const out = (k, html) => { element.querySelector(`[data-out="${k}"]`).innerHTML = html; };
    const machine = machines().find((m) => m.id === state.machine);
    const model = models().find((m) => m.id === state.model);
    state.layers = model ? model.layers : layersFor(state.total);
    out("specs", machine ? machine.specs : "");

    const one = step(state, 1);
    const many = step(state, state.batch);
    const prefill = (state.tflops * state.devices * 1e12) / (2 * state.active * 1e9);
    out("d1", `${fmt(one.tps)}<small>tok/s</small>`);
    out("d1n", one.bound);
    out("dbl", `Decode, ${state.batch} requests`);
    out("db", `${fmt(many.tps)}<small>tok/s</small>`);
    out("dbn", `${many.bound} · ${fmt(many.tps / state.batch)} tok/s each`);
    out("pf", `${fmt(prefill)}<small>tok/s</small>`);
    out("pfn", "compute-bound");

    const usable = state.mem * state.devices * USABLE;
    const weights = state.total * BITS[state.bits] / 8;
    const cache = state.batch * state.context * state.kvKB / 1e6;
    const most = Math.max(0, Math.floor((usable - weights) / (state.context * state.kvKB / 1e6)));
    const fits = weights + cache <= usable;
    element.querySelector(".calc-results").classList.toggle("is-over", !fits);
    out("fit", fits
      ? `Weights ${gb(weights)} GB and cache ${gb(cache)} GB fit in about ${gb(usable)} GB the GPU can use. Up to ${most.toLocaleString("en-US")} requests fit at ${kTok(state.context)} tokens of context.`
      : weights > usable
        ? `<b>Does not fit.</b> The weights alone take ${gb(weights)} GB of about ${gb(usable)} GB the GPU can use.`
        : `<b>Does not fit.</b> ${state.batch} requests need ${gb(weights + cache)} GB of about ${gb(usable)} GB the GPU can use; at most ${most.toLocaleString("en-US")} fit at ${kTok(state.context)} tokens.`);
  };

  const bind = () => {
    const list = machines();
    const mods = models();
    element.querySelector('[data-k="machine"]').innerHTML = list.map((m) => `<option value="${m.id}">${m.label}</option>`).join("");
    element.querySelector('[data-k="model"]').innerHTML = mods.map((m) => `<option value="${m.id}">${m.label}</option>`).join("");
    const pickMachine = (id) => {
      const m = list.find((x) => x.id === id);
      if (m) fill({ bw: m.bw, tflops: m.tflops, mem: m.mem, devices: m.devices, link: m.devices > 1 ? "pcie5" : "none" });
    };
    const pickModel = (id) => {
      const m = mods.find((x) => x.id === id);
      if (m) fill({ total: m.total, active: m.active, kvKB: m.kvKB });
    };
    fill({ machine: list.find((m) => m.id === "m5-max-128g")?.id || list[0]?.id, model: mods.find((m) => m.id === "qwen3.8-27b")?.id || mods[0]?.id });
    pickMachine(element.querySelector('[data-k="machine"]').value);
    pickModel(element.querySelector('[data-k="model"]').value);
    element.addEventListener("input", (event) => {
      const k = event.target.dataset?.k;
      if (k === "machine") pickMachine(event.target.value);
      if (k === "model") pickModel(event.target.value);
      if (k) update();
    });
    update();
  };

  Pie.methodology = {
    element,
    render(state) {
      element.hidden = state.table !== "methodology";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        bind();
        element.dataset.ready = "1";
      }
    },
  };
})();
