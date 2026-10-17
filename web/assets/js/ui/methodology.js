window.Pie = window.Pie || {};

// The Methods page: a ceiling estimator on top, then the roofline behind it, written as one page.
(() => {
  const element = document.getElementById("methodology");

  // GPU fp16 matmul TFLOPS per core. Apple10 is measured on the M5 Max (47 TFLOPS on 40 cores, with its neural accelerators);
  // the older ones are ALU count × clock. Estimates, editable in the specs.
  const TFLOPS_PER_CORE = { apple8: 0.36, apple9: 0.42, apple10: 1.17 };
  const BITS = { 4: 4.5, 8: 8.5, 16: 16 };  // bits per weight, with the quantization scales
  const CONTEXTS = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072];
  const BATCHES = [1, 2, 4, 8, 16, 32, 64, 128, 256];
  const LINKS = { none: ["One device", 0, 0], tb5: ["Thunderbolt 5", 10, 30], pcie5: ["PCIe 5.0 ×16", 64, 10], nvlink: ["NVLink", 900, 3] };
  const USABLE = 0.75;  // the share of unified memory macOS lets the GPU wire by default

  const kTok = (n) => (n >= 1024 ? `${Math.round(n / 1024)}K` : `${n}`);

  const machines = () => (Pie.store.rows("hardware") || []).map((h) => ({
    id: h.id,
    label: `${h.name} · ${h.memory_gib} GB`,
    bw: h.bandwidth_gbs || 0,
    // the catalog's fp16 compute where it has one, else the per-core estimate
    tflops: h.tflops_fp16 || +(((TFLOPS_PER_CORE[h.arch] || 0.4) * (h.gpu_cores || 0)).toFixed(1)),
    mem: h.memory_gib || 0,
    devices: h.count || 1,
    // internal SSD read speed, estimated by chip class: the Max chips read about twice as fast as the Pro, the Pro twice the base
    ssd: h.arch === "apple10" ? (h.gpu_cores >= 30 ? 14 : 7) : h.gpu_cores >= 16 ? 7 : 3,
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
      // what the catalog says the model supports: a paired drafter, and SSD streaming of its experts
      draft: String(m.draft) === "true",
      ssd: Boolean(m.ssd_streaming) && m.ssd_streaming !== "n/a",
    };
  });

  const calculator = `
    <section class="methods-calc" aria-label="Theoretical ceiling estimator">
      <div class="calc-body">
        <div class="calc-main">
          <p class="calc-title" data-out="title"></p>
          <div class="calc-results">
            <div class="calc-result"><span class="calc-value" data-out="d1"></span><span class="calc-label">Decode, one request</span><span class="calc-note" data-out="d1n"></span></div>
            <div class="calc-result" data-out-row="many"><span class="calc-value" data-out="db"></span><span class="calc-label" data-out="dbl"></span><span class="calc-note" data-out="dbn"></span></div>
            <div class="calc-result"><span class="calc-value" data-out="pf"></span><span class="calc-label">Prefill</span><span class="calc-note" data-out="pfn"></span></div>
          </div>
          <div class="calc-foot">
            <div class="calc-memory" data-out="fit" role="status"></div>
          </div>
        </div>
        <div class="calc-settings" aria-label="Settings">
          <label class="calc-setting"><span>Model</span><select data-k="model"></select></label>
          <label class="calc-setting"><span>Machine</span><select data-k="machine"></select></label>
          <div class="calc-setting" role="radiogroup" aria-label="Weights"><span>Weights</span>
            <div class="calc-segments">${[4, 8, 16].map((b) => `<label><input type="radio" name="calc-bits" value="${b}"${b === 4 ? " checked" : ""}><span>${b}-bit</span></label>`).join("")}</div>
          </div>
          <label class="calc-setting"><span>Context <b data-out="ctxv"></b></span><input type="range" min="0" max="${CONTEXTS.length - 1}" step="1" value="${CONTEXTS.indexOf(4096)}" data-k="contextIdx"></label>
          <label class="calc-setting"><span>Requests at once <b data-out="batv"></b></span><input type="range" min="0" max="${BATCHES.length - 1}" step="1" value="${BATCHES.indexOf(8)}" data-k="batchIdx"></label>
          <label class="calc-setting calc-switch-row" data-supports="draft"><span>Speculative decoding</span><span class="calc-switch"><input type="checkbox" role="switch" data-k="spec"><i aria-hidden="true"></i></span></label>
          <div class="calc-spec" data-out-row="spec" hidden>
            <label class="calc-setting"><span>Draft tokens per step <b data-out="speckv"></b></span><input type="range" min="1" max="8" step="1" value="4" data-k="specK"></label>
            <label class="calc-setting"><span>Acceptance rate <b data-out="specav"></b></span><input type="range" min="50" max="95" step="5" value="70" data-k="specA"></label>
          </div>
          <label class="calc-setting calc-switch-row" data-supports="ssd"><span>SSD streaming</span><span class="calc-switch"><input type="checkbox" role="switch" data-k="ssd"><i aria-hidden="true"></i></span></label>
          <div class="calc-spec" data-out-row="ssd" hidden>
            <label class="calc-setting"><span>SSD read speed <b data-out="ssdv"></b></span><input type="range" min="1" max="20" step="1" value="7" data-k="ssdGBs"></label>
          </div>
        </div>
      </div>
      <div hidden>${["bw", "tflops", "mem", "devices", "link", "total", "active", "kvKB"].map((k) => `<input type="hidden" data-k="${k}">`).join("")}</div>
    </section>`;


  const content = `
    <div class="methods">
      <header class="methods-hero">
        <h1>Theoretical maximum.</h1>
        <p class="methods-lede">Trust, but check your provider.</p>
      </header>
      ${calculator}

    </div>`;

  const cap = (text) => text[0].toUpperCase() + text.slice(1);
  const fmt = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const gb = (n) => (n >= 10 ? n.toFixed(0) : n.toFixed(1));

  // the roofline for one step of `batch` tokens: the slowest of bytes, arithmetic and interconnect
  // a draft model of this size proposes the tokens; small enough that its own reads are the cost
  const DRAFT_B = 0.5;
  // expected tokens a verify step keeps when each of k drafts is accepted with probability a (Leviathan et al., 2023)
  const kept = (k, a) => (1 - a ** (k + 1)) / (1 - a);

  const step = (s, batch) => {
    // with speculation one verify pass checks k drafts plus one token per request, after k draft passes
    const spec = s.spec ? { k: s.specK, a: s.specA / 100 } : null;
    const tokensPerPass = spec ? spec.k + 1 : 1;
    const bytesPerParam = BITS[s.bits] / 8;
    // a MoE step touches more experts as the batch grows; a dense model reads all of its weights at any batch
    const share = s.active / s.total;
    const weightGB = s.total * bytesPerParam * (share >= 1 ? 1 : 1 - (1 - share) ** batch);
    const cacheGB = batch * s.context * s.kvKB / 1e6;
    const bw = s.bw * s.devices;
    const flops = s.tflops * s.devices * 1e12;
    // SSD streaming: what does not fit stays on the SSD and is read again every step, beside the resident part
    const totalGB = (s.total + (s.spec ? DRAFT_B : 0)) * bytesPerParam;
    const resident = Math.max(0, Math.min(totalGB, s.mem * s.devices * USABLE - cacheGB));
    const streamed = s.ssd && totalGB > resident ? 1 - resident / totalGB : 0;
    const ssd = streamed ? (weightGB * streamed) / s.ssdGBs : 0;
    const memory = (weightGB * (1 - streamed) + cacheGB) / bw;
    const compute = (2 * s.active * 1e9 * batch * tokensPerPass) / flops;
    // tensor parallel: two all-reduces of the hidden state per layer, each paying the link's latency
    const [, linkGBs, latencyUs] = LINKS[s.link];
    const hidden = Math.sqrt((s.total * 1e9) / (12 * s.layers));
    const link = s.devices > 1 && linkGBs ? 2 * s.layers * (latencyUs * 1e-6 + (batch * hidden * 2 * (s.devices - 1) / s.devices) / (linkGBs * 1e9)) : 0;
    const verify = Math.max(memory, compute, link, ssd);
    const bound = verify === ssd && ssd ? "SSD-bound" : verify === link && link ? "interconnect-bound" : verify === compute ? "compute-bound" : "bandwidth-bound";
    if (!spec) return { tps: batch / verify, bound };
    const draft = spec.k * Math.max((DRAFT_B * bytesPerParam + batch * s.context * s.kvKB / 1e6 * .05) / bw, (2 * DRAFT_B * 1e9 * batch) / flops);
    const perStep = kept(spec.k, spec.a);
    return { tps: (batch * perStep) / (verify + draft), bound, perStep };
  };

  const state = {};
  const read = () => {
    element.querySelectorAll("[data-k]").forEach((input) => {
      const k = input.dataset.k;
      state[k] = input.type === "checkbox" ? input.checked : ["machine", "model", "link"].includes(k) ? input.value : Number(input.value);
      // a slider's fill follows its knob
      if (input.type === "range") input.style.setProperty("--fill", `${(100 * (input.value - input.min)) / (input.max - input.min)}%`);
    });
    state.bits = Number(element.querySelector('input[name="calc-bits"]:checked').value);
    state.context = CONTEXTS[state.contextIdx];
    state.batch = BATCHES[state.batchIdx];
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
    out("title", `${model ? model.label : "Custom model"}<span>on ${machine ? machine.label : "custom hardware"}</span>`);
    out("ctxv", `${kTok(state.context)} tokens`);
    out("batv", `${state.batch}`);
    element.querySelector('[data-out-row="spec"]').hidden = !state.spec;
    out("speckv", `${state.specK}`);
    out("specav", `${state.specA}%`);
    element.querySelector('[data-out-row="ssd"]').hidden = !state.ssd;
    out("ssdv", `${state.ssdGBs} GB/s`);
    element.querySelector('[data-out-row="many"]').hidden = state.batch === 1;

    const one = step(state, 1);
    const many = step(state, state.batch);
    // prefill reads the weights once per chunk of the prompt; streamed weights cost one SSD pass per chunk
    const flopsAll = state.tflops * state.devices * 1e12;
    const chunk = Math.min(state.context, 2048);
    const usableGB = state.mem * state.devices * USABLE;
    const allWeights = (state.total + (state.spec ? DRAFT_B : 0)) * BITS[state.bits] / 8;
    const onSsd = state.ssd ? Math.max(0, allWeights - Math.max(0, usableGB - state.context * state.kvKB / 1e6)) : 0;
    const pfCompute = (2 * state.active * 1e9 * chunk) / flopsAll;
    const pfSsd = onSsd / state.ssdGBs;
    const prefill = chunk / Math.max(pfCompute, pfSsd);
    out("d1", `<span class="calc-num">${fmt(one.tps)}</span><small>tok/s</small>`);
    const plain = state.spec ? { ...state, spec: false } : null;
    const gain = (r, batch) => (plain ? ` · ${(r.tps / step(plain, batch).tps).toFixed(1)}× from drafts` : "");
    out("d1n", `${cap(one.bound)}${gain(one, 1)}`);
    out("dbl", `Decode, ${state.batch} ${state.batch === 1 ? "request" : "requests"}`);
    out("db", `<span class="calc-num">${fmt(many.tps)}</span><small>tok/s</small>`);
    out("dbn", `${cap(many.bound)} · ${fmt(many.tps / state.batch)} tok/s each${gain(many, state.batch)}`);
    out("pf", `<span class="calc-num">${fmt(prefill)}</span><small>tok/s</small>`);
    out("pfn", pfSsd > pfCompute ? "SSD-bound" : "Compute-bound");

    const usable = state.mem * state.devices * USABLE;
    const weights = (state.total + (state.spec ? DRAFT_B : 0)) * BITS[state.bits] / 8;
    const cache = state.batch * state.context * state.kvKB / 1e6;
    const most = Math.max(0, Math.floor((usable - weights) / (state.context * state.kvKB / 1e6)));
    // with SSD streaming only the cache has to fit; the weights that do not are read from the SSD
    const resident = state.ssd ? Math.max(0, Math.min(weights, usable - cache)) : weights;
    const fromSsd = weights - resident;
    const fits = state.ssd ? cache < usable : weights + cache <= usable;
    element.querySelector(".calc-results").classList.toggle("is-over", !fits);
    // memory as macOS Storage shows it: one bar of what the GPU can use, filled by the weights and the cache
    const pct = (gbs) => `${Math.min(100, (100 * gbs) / usable).toFixed(2)}%`;
    element.querySelector(".calc-memory").classList.toggle("is-over", !fits);
    const room = fits
      ? fromSsd > 0 ? `${gb(fromSsd)} GB read from the SSD every step` : `Room for ${most.toLocaleString("en-US")} requests at ${kTok(state.context)}`
      : weights > usable && !state.ssd ? "The weights alone don’t fit · try SSD streaming" : "The cache doesn’t fit";
    out("fit", `
      <div class="calc-memory-head">
        <span>Memory</span>
        <span>${fits ? `${gb(resident + cache)} GB of ${gb(usable)} GB` : `Needs ${gb(weights + cache)} GB of ${gb(usable)} GB`}</span>
      </div>
      <div class="calc-memory-bar"><i class="is-weights" style="width:${pct(resident)}"></i><i class="is-cache" style="width:${pct(cache)}"></i></div>
      <div class="calc-memory-legend">
        <span><i class="is-weights"></i>Weights ${gb(resident)} GB</span>
        <span><i class="is-cache"></i>Cache ${gb(cache)} GB</span>
        ${fromSsd > 0 ? `<span><i class="is-ssd"></i>On SSD ${gb(fromSsd)} GB</span>` : ""}
        <span>${room}</span>
      </div>`);
  };

  const bind = () => {
    const list = machines();
    const mods = models();
    element.querySelector('[data-k="machine"]').innerHTML = list.map((m) => `<option value="${m.id}">${m.label}</option>`).join("");
    element.querySelector('[data-k="model"]').innerHTML = mods.map((m) => `<option value="${m.id}">${m.label}</option>`).join("");
    const pickMachine = (id) => {
      const m = list.find((x) => x.id === id);
      if (m) fill({ bw: m.bw, tflops: m.tflops, mem: m.mem, devices: m.devices, link: m.devices > 1 ? "pcie5" : "none", ssdGBs: m.ssd });
    };
    const pickModel = (id) => {
      const m = mods.find((x) => x.id === id);
      if (!m) return;
      fill({ total: m.total, active: m.active, kvKB: m.kvKB });
      // an option the model does not support is hidden and switched off
      element.querySelectorAll("[data-supports]").forEach((row) => {
        const supported = m[row.dataset.supports];
        row.hidden = !supported;
        if (!supported) row.querySelector("input").checked = false;
      });
    };
    fill({ machine: list.find((m) => m.id === "m5-max-128g")?.id || list[0]?.id, model: mods.find((m) => m.id === "qwen3.8-27b")?.id || mods[0]?.id });
    pickMachine(element.querySelector('[data-k="machine"]').value);
    pickModel(element.querySelector('[data-k="model"]').value);
    element.addEventListener("input", (event) => {
      const k = event.target.dataset?.k;
      if (k === "machine") pickMachine(event.target.value);
      if (k === "model") pickModel(event.target.value);
      if (k || event.target.name === "calc-bits") update();
    });
    update();
  };

  // bits per weight a result's scheme stores, with its scales
  const bitsOf = (scheme = "") => (/bf16|f16/.test(scheme) ? 16 : /8/.test(scheme) ? 8.5 : /q4_k/.test(scheme) ? 4.85 : 4.5);

  // the hardware limit for one measured result, from the spec sheet: the slower of reading the bytes and doing the math.
  // decode is one token at the middle of the answer; prefill is the whole prompt in one pass
  Pie.ceiling = (row, metric) => {
    const machine = machines().find((m) => m.id === row.hardware);
    const model = models().find((m) => m.id === row.model);
    const workload = Pie.store.index.workloads[row.workload];
    if (!machine?.bw || !machine.tflops || !model || !workload) return null;
    const bytes = bitsOf(row.scheme) / 8;
    const flops = machine.tflops * 1e12;
    const share = model.active / model.total;
    const prompt = workload.prompt_tokens;
    const tokens = metric === "prefill" ? prompt : 1;
    const context = metric === "prefill" ? prompt : prompt + workload.output_tokens / 2;
    // a MoE pass touches more experts the more tokens it carries
    const weightGB = model.total * bytes * (share >= 1 ? 1 : 1 - (1 - share) ** tokens);
    const memory = (weightGB + context * model.kvKB / 1e6) / machine.bw;
    const compute = (2 * model.active * 1e9 * tokens) / flops;
    const bound = memory > compute * 1.1 ? "bandwidth" : compute > memory * 1.1 ? "compute" : "balanced";
    return { tps: tokens / Math.max(memory, compute), bound };
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
