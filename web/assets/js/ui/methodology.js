window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("methodology");

  const TFLOPS_PER_CORE = { apple8: 0.36, apple9: 0.42, apple10: 1.53 };
  const BITS = { 4: 4.5, 8: 8.5, 16: 16 };
  const CONTEXTS = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072];
  const BATCHES = [1, 2, 4, 8, 16, 32, 64, 128, 256];
  const LINKS = { none: ["One device", 0, 0], tb5: ["Thunderbolt 5", 10, 30], pcie5: ["PCIe 5.0 ×16", 64, 15], nvlink: ["NVLink", 900, 15] };
  const USABLE = 0.75;
  const NEURAL_ENGINE = { pie: ["apple7", "apple8", "apple9"] };

  const kTok = (n) => (n >= 1024 ? `${Math.round(n / 1024)}K` : `${n}`);

  const machines = () => (Pie.store.rows("hardware") || []).map((h) => ({
    id: h.id,
    label: Pie.platform.machineName(h.id),
    bw: h.bandwidth_gbs || 0,
    tflops: h.tflops_fp16 || (h.vendor === "Apple" || h.class === "mac" ? +(((TFLOPS_PER_CORE[h.arch] || 0.4) * (h.gpu_cores || 0)).toFixed(1)) : 0),
    tflops8: h.tflops_fp8 || 0,
    tflopsMx: h.tflops_mxfp8 || 0,
    ane: h.ane_tflops_fp16 || 0,
    arch: h.arch,
    mem: h.memory_gib || 0,
    devices: h.count || 1,
    ssd: h.arch === "apple10" ? (h.gpu_cores >= 30 ? 14 : 7) : h.gpu_cores >= 16 ? 7 : 3,
    specs: [h.bandwidth_gbs && `${h.bandwidth_gbs} GB/s`, h.gpu_cores && `${h.gpu_cores}-core GPU`, h.cpu_cores && `${h.cpu_cores}-core CPU`, h.memory_gib && `${h.memory_gib} GB unified memory`].filter(Boolean).join(" · "),
  }));

  const HYBRID = /qwen3_5|qwen3_6|qwen4/;
  const layersFor = (p) => (p <= 5 ? 32 : p <= 15 ? 40 : p <= 40 ? 64 : 80);
  const models = () => (Pie.store.rows("models") || []).filter((m) => m.params_b).map((m) => {
    const layers = m.layers || layersFor(m.params_b);
    return {
      id: m.id,
      label: m.name,
      total: m.params_b,
      active: m.active_b || m.params_b,
      layers,
      kvKB: Math.round(layers * 4 * (HYBRID.test(m.family || "") ? 0.25 : 1)),
      draft: String(m.draft) === "true",
      ssd: Boolean(m.ssd_streaming) && m.ssd_streaming !== "n/a",
      hidden: m.hidden_size || Math.round(Math.sqrt((m.params_b * 1e9) / (12 * layers))),
      family: m.family || "",
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
      </div>
      <div hidden>${["bw", "tflops", "mem", "devices", "link", "total", "active", "kvKB"].map((k) => `<input type="hidden" data-k="${k}">`).join("")}</div>
    </section>`;


  const opts = (values, selected, label) => values.map((v, i) => `<option value="${i}"${v === selected ? " selected" : ""}>${label(v)}</option>`).join("");
  const range = (from, to, by) => Array.from({ length: Math.floor((to - from) / by) + 1 }, (_, i) => from + i * by);
  const settingsBar = `
    <div class="platform-bar limit-bar" aria-label="Settings">
      <button class="filter-button limit-pick" type="button" data-pick="model" aria-haspopup="menu" aria-label="Model"><span data-pick-label="model"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="model" hidden></select>
      <button class="filter-button limit-pick" type="button" data-pick="machine" aria-haspopup="menu" aria-label="Machine"><span data-pick-label="machine"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="machine" hidden></select>
      <button class="filter-button limit-pick" type="button" data-pick="bits" aria-haspopup="menu" aria-label="Weights"><span data-pick-label="bits"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="bits" hidden>${[4, 8, 16].map((b) => `<option value="${b}"${b === 4 ? " selected" : ""}>${b}-bit</option>`).join("")}</select>
      <button class="filter-button limit-pick" type="button" data-pick="contextIdx" aria-haspopup="menu" aria-label="Context"><span data-pick-label="contextIdx"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="contextIdx" hidden>${opts(CONTEXTS, 4096, (c) => `${kTok(c)} context`)}</select>
      <button class="filter-button limit-pick" type="button" data-pick="batchIdx" aria-haspopup="menu" aria-label="Requests at once"><span data-pick-label="batchIdx"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="batchIdx" hidden>${opts(BATCHES, 8, (b) => `${b} ${b === 1 ? "request" : "requests"}`)}</select>
      <button type="button" class="plain-button rules-button" data-rules aria-expanded="false" aria-label="Test Conditions" title="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button>
      <label class="plain-button limit-toggle" data-supports="draft"><input type="checkbox" data-k="spec">Speculative decoding</label>
      <span class="limit-sub" data-out-row="spec" hidden>
        <button class="filter-button limit-pick" type="button" data-pick="specK" aria-haspopup="menu" aria-label="Draft tokens per step"><span data-pick-label="specK"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="specK" hidden><option value="0" selected>Best width</option>${range(1, 16, 1).map((v) => `<option value="${v}">${v} ${v === 1 ? "draft" : "drafts"}</option>`).join("")}</select>
        <button class="filter-button limit-pick" type="button" data-pick="specBlock" aria-haspopup="menu" aria-label="Drafter"><span data-pick-label="specBlock"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="specBlock" hidden><option value="1" selected>Block drafter</option><option value="0">Token drafter</option></select>
        <button class="filter-button limit-pick" type="button" data-pick="specA" aria-haspopup="menu" aria-label="Acceptance rate"><span data-pick-label="specA"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="specA" hidden>${range(50, 95, 5).map((v) => `<option value="${v}"${v === 70 ? " selected" : ""}>${v}% accepted</option>`).join("")}</select>
      </span>
      <label class="plain-button limit-toggle" data-supports="ssd"><input type="checkbox" data-k="ssd">SSD streaming</label>
      <span class="limit-sub" data-out-row="ssd" hidden>
        <button class="filter-button limit-pick" type="button" data-pick="ssdGBs" aria-haspopup="menu" aria-label="SSD read speed"><span data-pick-label="ssdGBs"></span><svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button><select class="limit-select" data-k="ssdGBs" hidden>${range(1, 20, 1).map((v) => `<option value="${v}"${v === 7 ? " selected" : ""}>${v} GB/s SSD</option>`).join("")}</select>
      </span>
      <span hidden><b data-out="ctxv"></b><b data-out="batv"></b><b data-out="speckv"></b><b data-out="specav"></b><b data-out="ssdv"></b></span>
    </div>`;

  const content = `
    <div class="methods">
      ${calculator}

    </div>`;

  const cap = (text) => text[0].toUpperCase() + text.slice(1);
  const fmt = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const gb = (n) => (n >= 10 ? n.toFixed(0) : n.toFixed(1));

  const DRAFT_B = 0.5;
  const kept = (k, a) => (1 - a ** (k + 1)) / (1 - a);
  const WIDEST = 16;

  const step = (s, batch) => {
    const plain = width(s, batch, 0);
    if (!s.spec) return plain;
    const widths = s.specK ? [s.specK] : range(1, WIDEST, 1);
    const best = widths.map((k) => width(s, batch, k)).reduce((x, y) => (y.tps > x.tps ? y : x));
    return s.specK || best.tps > plain.tps ? best : { ...plain, k: 0 };
  };

  const width = (s, batch, k) => {
    const spec = k ? { k, a: s.specA / 100 } : null;
    const tokensPerPass = spec ? spec.k + 1 : 1;
    const bytesPerParam = BITS[s.bits] / 8;
    const share = s.active / s.total;
    const weightGB = s.total * bytesPerParam * (share >= 1 ? 1 : 1 - (1 - share) ** batch);
    const cacheGB = batch * s.context * s.kvKB / 1e6;
    const bw = s.bw * s.devices;
    const flops = s.tflops * s.devices * 1e12;
    const totalGB = (s.total + (s.spec ? DRAFT_B : 0)) * bytesPerParam;
    const resident = Math.max(0, Math.min(totalGB, s.mem * s.devices * USABLE - cacheGB));
    const streamed = s.ssd && totalGB > resident ? 1 - resident / totalGB : 0;
    const ssd = streamed ? (weightGB * streamed) / s.ssdGBs : 0;
    const memory = (weightGB * (1 - streamed) + cacheGB) / bw;
    const compute = (2 * s.active * 1e9 * batch * tokensPerPass) / flops;
    const [, linkGBs, latencyUs] = LINKS[s.link];
    const hidden = Math.sqrt((s.total * 1e9) / (12 * s.layers));
    const link = s.devices > 1 && linkGBs ? 2 * s.layers * (latencyUs * 1e-6 + (batch * hidden * 2 * (s.devices - 1) / s.devices) / (linkGBs * 1e9)) : 0;
    const verify = Math.max(memory, compute, link, ssd);
    const bound = verify === ssd && ssd ? "SSD-bound" : verify === link && link ? "interconnect-bound" : verify === compute ? "compute-bound" : "bandwidth-bound";
    if (!spec) return { tps: batch / verify, bound };
    const draftRead = (DRAFT_B * bytesPerParam + batch * s.context * s.kvKB / 1e6 * .05) / bw;
    const draft = s.specBlock
      ? Math.max(draftRead, (2 * DRAFT_B * 1e9 * batch * tokensPerPass) / flops)
      : spec.k * Math.max(draftRead, (2 * DRAFT_B * 1e9 * batch) / flops);
    const perStep = kept(spec.k, spec.a);
    return { tps: (batch * perStep) / (verify + draft), bound, perStep, k };
  };

  const state = {};
  const read = () => {
    element.querySelectorAll("[data-k]").forEach((input) => {
      const k = input.dataset.k;
      state[k] = input.type === "checkbox" ? input.checked : ["machine", "model", "link"].includes(k) ? input.value : Number(input.value);
      if (input.type === "range") input.style.setProperty("--fill", `${(100 * (input.value - input.min)) / (input.max - input.min)}%`);
    });
    const radio = element.querySelector('input[name="calc-bits"]:checked');
    if (radio) state.bits = Number(radio.value);
    state.context = CONTEXTS[state.contextIdx];
    element.querySelectorAll("[data-pick-label]").forEach((label) => {
      const select = element.querySelector(`select[data-k="${label.dataset.pickLabel}"]`);
      label.textContent = select?.options[select.selectedIndex]?.text || "";
    });
    state.batch = BATCHES[state.batchIdx];
  };
  const fill = (values) => Object.entries(values).forEach(([k, v]) => {
    const input = element.querySelector(`[data-k="${k}"]`);
    if (!input) return;
    if (input.tagName === "SELECT" && ![...input.options].some((o) => o.value === String(v))) {
      const near = [...input.options].reduce((a, o) => (Math.abs(Number(o.value) - v) < Math.abs(Number(a.value) - v) ? o : a), input.options[0]);
      input.value = near ? near.value : v;
    } else input.value = v;
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
    const gain = (r, batch) => (!plain ? "" : r.k ? ` · ${(r.tps / step(plain, batch).tps).toFixed(1)}× from ${r.k} ${r.k === 1 ? "draft" : "drafts"}` : " · drafts don’t pay here");
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
    const resident = state.ssd ? Math.max(0, Math.min(weights, usable - cache)) : weights;
    const fromSsd = weights - resident;
    const fits = state.ssd ? cache < usable : weights + cache <= usable;
    element.querySelector(".calc-results").classList.toggle("is-over", !fits);
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
      element.querySelectorAll("[data-supports]").forEach((row) => {
        const supported = m[row.dataset.supports];
        row.hidden = !supported;
        if (!supported) row.querySelector("input").checked = false;
      });
    };
    fill({ machine: list.find((m) => m.id === "m5-max-128g")?.id || list[0]?.id, model: mods.find((m) => m.id === "qwen3.8-27b")?.id || mods[0]?.id });
    pickMachine(element.querySelector('[data-k="machine"]').value);
    pickModel(element.querySelector('[data-k="model"]').value);
    element.addEventListener("click", (event) => {
      const button = event.target.closest("[data-pick]");
      if (!button) return;
      event.stopPropagation();
      Pie.popover.open(button, `limit:${button.dataset.pick}`, null);
    });
    element.addEventListener("input", (event) => {
      const k = event.target.dataset?.k;
      if (k === "machine") pickMachine(event.target.value);
      if (k === "model") pickModel(event.target.value);
      if (k || event.target.name === "calc-bits") update();
    });
    update();
  };

  const bitsOf = (scheme = "") => {
    if (/mlx_2bit/.test(scheme)) return { bits: 4.5, experts: 2.25, head: 4.5 };
    if (/q2_k/.test(scheme)) return { bits: 2.625, experts: (2 * 2.625 + 3.4375) / 3, head: 6.5625 };
    const bits = /bf16|f16/.test(scheme) ? 16 : /mxfp4/.test(scheme) ? 4.25 : /8/.test(scheme) ? 8.5 : /q4_k/.test(scheme) ? 4.85 : 4.5;
    return { bits, experts: bits, head: bits };
  };

  const pass = (a, { bits, tokens, logits, requests, context, touched = null }) => {
    const body = a.total - a.emb * (a.tied ? 1 : 2) - a.ple;
    const activeBody = body - a.routed * (1 - a.k);
    const touchedExperts = a.routed * (a.k >= 1 ? 1 : touched ?? 1 - (1 - a.k) ** tokens);
    const weightGB = ((body - a.routed) * bits.bits + touchedExperts * bits.experts + a.emb * bits.head) / 8;
    const cacheGB = (requests * (a.full * context * (a.kvFull || a.kvLayer) + a.sliding * Math.min(context, a.window) * a.kvLayer
      + a.linear * a.state * 2)) / 1e9;
    const skip = a.shared && tokens > logits ? (a.shared / a.layers) * (tokens - logits) : 0;
    const bodyFlops = 2e9 * activeBody * (tokens - skip);
    const flops = bodyFlops + 2e9 * a.emb * logits;
    return { weightGB, cacheGB, flops, bodyFlops, body: activeBody, head: a.emb, experts: a.routed * a.k };
  };

  const A8_FAMILY = /^deepseek_v4/;
  const narrow = (machine, scheme = "", p, family = "") => {
    if (/(^|_)fp8/.test(scheme) && machine.tflops8) return { share: 1, tflops: machine.tflops8 };
    if (/mxfp4/.test(scheme) && A8_FAMILY.test(family) && (machine.tflopsMx || machine.tflops8)) return { share: 1, tflops: machine.tflopsMx || machine.tflops8 };
    if (/mxfp4/.test(scheme) && machine.tflopsMx) return { share: p.experts && p.body ? Math.min(1, p.experts / p.body) : 1, tflops: machine.tflopsMx };
    return { share: 0, tflops: 0 };
  };
  const mathTime = (flops, bodyFlops, tflops, share = 0, tflopsNarrow = 0) => {
    if (!tflops) return 0;
    const fast = share && tflopsNarrow ? bodyFlops * share : 0;
    return (flops - fast) / (tflops * 1e12) + (fast ? fast / (tflopsNarrow * 1e12) : 0);
  };

  const archOf = (id) => {
    const own = Pie.architectures?.[id];
    if (own) return own;
    const m = models().find((x) => x.id === id);
    if (!m?.total) return null;
    return { total: m.total, emb: 0, tied: true, ple: 0, routed: m.total, k: m.active / m.total, full: m.layers, sliding: 0, window: 0,
      kvLayer: (m.kvKB / m.layers) * 1e3, linear: 0, state: 0, layers: m.layers, shared: 0, hidden: m.hidden };
  };

  const ALL_REDUCE_US = 15;
  const A100_ALL_REDUCE_US = 35;
  const linkOf = (id) => {
    const hw = Pie.store.index.hardware[id];
    if (!hw || (hw.count || 1) < 2) return null;
    const name = `${hw.name} ${hw.full_name || ""}`;
    const us = /A100/.test(name) ? A100_ALL_REDUCE_US : ALL_REDUCE_US;
    if (hw.interconnect === "nvlink") return /H100|H200|H800/.test(name) ? { gbs: 450, us, name: "NVLink 4" } : { gbs: 300, us, name: "NVLink 3" };
    const gen5 = /PRO 6000|PRO 4500|5090|H100|H200|B200|Blackwell/.test(name);
    return gen5 ? { gbs: 64, us, name: "PCIe 5.0" } : { gbs: 32, us, name: "PCIe 4.0" };
  };
  const linkTime = (a, link, devices, tokens) => {
    if (!link) return 0;
    const bytes = tokens * a.hidden * 2 * 2 * (devices - 1) / devices;
    return 2 * a.layers * (link.us * 1e-6 + bytes / (link.gbs * 1e9));
  };

  const miniArch = (row) => {
    const base = archOf(row.model);
    if (!base || !row.mini_params_b) return null;
    const s = row.mini_layers / base.layers;
    const k = row.mini_k < 1 ? row.mini_k : 0;
    return { ...base, routes: null, total: row.mini_params_b, emb: row.mini_emb_b / 2, tied: false, ple: 0,
      routed: (row.mini_params_b - row.mini_active_b) / (1 - k), k, layers: row.mini_layers, shared: 0,
      full: Math.round(base.full * s), sliding: Math.round(base.sliding * s), linear: Math.round(base.linear * s) };
  };
  const archOfRow = (row) => (row?.miniature ? miniArch(row) : archOf(row.model));

  const shapeOf = (workload, benchmark) => {
    const w = Pie.store.index.workloads?.[workload];
    const own = benchmark && w?.shapes?.[benchmark];
    return own ? { ...w, ...own } : w;
  };
  Pie.shapeOf = shapeOf;

  Pie.ceiling = (row, metric) => {
    const machine = machines().find((m) => m.id === row.hardware);
    const model = models().find((m) => m.id === row.model);
    const workload = shapeOf(row.workload, row.benchmark);
    const a = archOfRow(row);
    if (!machine?.bw || !model || !workload || !a) return null;
    const bits = bitsOf(row.scheme);
    const prompt = row.prompt_per_request || workload.prompt_tokens;
    const batch = metric === "pbatch" ? (workload.concurrency || 1) : 1;
    const prefill = metric === "prefill" || metric === "pbatch";
    const ane = prefill && machine.ane && NEURAL_ENGINE[row.engine]?.includes(machine.arch) && row.scheme === "affine_u4_g64" && !a.routed ? machine.ane : 0;
    const bw = machine.bw * machine.devices;
    const tflops = (machine.tflops + ane) * machine.devices;
    const tokens = prefill ? prompt * batch : 1;
    const context = prefill ? prompt : prompt + workload.output_tokens / 2;
    const p = pass(a, { bits, tokens, logits: batch, requests: batch, context });
    const memory = (p.weightGB + p.cacheGB) / bw;
    const n = narrow(machine, row.scheme, p, model.family);
    const tflopsNarrow = n.tflops * machine.devices;
    const compute = mathTime(p.flops, p.bodyFlops, tflops, n.share, tflopsNarrow);
    const link = linkOf(row.hardware);
    const linkS = linkTime(a, link, machine.devices, tokens);
    const slowest = Math.max(memory, compute, linkS);
    const bound = linkS === slowest && linkS ? "interconnect" : memory > compute * 1.1 ? "bandwidth" : compute > memory * 1.1 ? "compute" : "balanced";
    const parts = { weightGB: p.weightGB, cacheGB: p.cacheGB, readS: memory, mathS: compute, linkS, link, bw,
      tflops: compute && n.share ? p.flops / compute / 1e12 : tflops, tflops16: tflops, tflopsNarrow, narrow: n.share, ane,
      devices: machine.devices, body: p.body, head: p.head, bits: bits.bits, expertBits: bits.experts, headBits: bits.head,
      bytes: bits.bits / 8, tokens, context, flopsPerToken: 2e9 * (p.body + p.head) };
    return { tps: tokens / slowest, bound, bandwidth: tokens / memory, compute: compute ? tokens / compute : null, interconnect: linkS ? tokens / linkS : null, parts };
  };

  const ALPHA_KEY = "pie.specAlpha";
  const ALPHA_MIN = 50, ALPHA_MAX = 95;
  const ALPHA_DEFAULT = 70;
  Pie.specAlpha = (() => {
    try {
      const kept = Number(localStorage.getItem(ALPHA_KEY));
      return kept >= ALPHA_MIN && kept <= ALPHA_MAX ? kept : ALPHA_DEFAULT;
    } catch { return ALPHA_DEFAULT; }
  })();
  Pie.specCeiling = (row, percent = Pie.specAlpha) => {
    const plain = Pie.ceiling(row, "decode");
    if (!plain) return null;
    const a = archOfRow(row);
    const workload = Pie.store.index.workloads[row.workload];
    const { bw, tflops16: tflops, tflopsNarrow, narrow: share, context } = plain.parts;
    const bits = bitsOf(row.scheme);
    const alpha = Math.min(percent, 99) / 100;
    const draftS = Math.max((DRAFT_B * bits.bits / 8) / bw, tflops ? (2 * DRAFT_B * 1e9) / (tflops * 1e12) : 0);
    let best = { tps: plain.tps, k: 0, kept: 1, bound: plain.bound };
    for (let k = 1; k <= WIDEST; k++) {
      const p = pass(a, { bits, tokens: k + 1, logits: k + 1, requests: 1, context });
      const memory = (p.weightGB + p.cacheGB) / bw;
      const compute = mathTime(p.flops, p.bodyFlops, tflops, share, tflopsNarrow);
      const kept = (1 - alpha ** (k + 1)) / (1 - alpha);
      const tps = kept / (Math.max(memory, compute) + draftS);
      if (tps > best.tps) best = { tps, k, kept, bound: memory > compute * 1.1 ? "bandwidth" : compute > memory * 1.1 ? "compute" : "balanced" };
    }
    return { ...best, gain: best.tps / plain.tps, plain: plain.tps, workload: workload?.id };
  };

  Pie.specField = () => `
        <span class="spec-field" role="group" aria-label="Acceptance per draft">
          <span class="spec-field-label">Acceptance</span>
          <input type="text" inputmode="numeric" value="${Pie.specAlpha}" data-alpha aria-label="Acceptance per draft, percent"><span class="spec-unit">%</span>
          <span class="spec-stepper"><button type="button" data-alpha-step="1" aria-label="More" tabindex="-1"><svg viewBox="0 0 8 5" aria-hidden="true"><path d="M1 4l3-3 3 3"/></svg></button><button type="button" data-alpha-step="-1" aria-label="Less" tabindex="-1"><svg viewBox="0 0 8 5" aria-hidden="true"><path d="M1 1l3 3 3-3"/></svg></button></span>
        </span>`;
  Pie.setSpecAlpha = (value) => {
    Pie.specAlpha = Math.min(ALPHA_MAX, Math.max(ALPHA_MIN, Math.round(Number.isFinite(value) ? value : Pie.specAlpha)));
    try { localStorage.setItem(ALPHA_KEY, String(Pie.specAlpha)); } catch { }
    return Pie.specAlpha;
  };
  Pie.bindSpecField = (root, changed) => {
    root.addEventListener("input", (event) => {
      if (!event.target.matches("[data-alpha]")) return;
      const typed = parseFloat(event.target.value);
      if (typed >= ALPHA_MIN && typed <= ALPHA_MAX) { Pie.setSpecAlpha(typed); changed(); }
    });
    root.addEventListener("change", (event) => {
      if (!event.target.matches("[data-alpha]")) return;
      const before = Pie.specAlpha;
      Pie.setSpecAlpha(parseFloat(event.target.value));
      event.target.value = Pie.specAlpha;
      if (Pie.specAlpha !== before) changed();
    });
    root.addEventListener("keydown", (event) => {
      if (!event.target.matches("[data-alpha]") || !["ArrowUp", "ArrowDown"].includes(event.key)) return;
      event.preventDefault();
      Pie.setSpecAlpha(Pie.specAlpha + (event.key === "ArrowUp" ? 1 : -1) * (event.shiftKey ? 10 : 1));
      changed();
    });
    root.addEventListener("click", (event) => {
      const step = event.target.closest("[data-alpha-step]");
      if (!step) return;
      Pie.setSpecAlpha(Pie.specAlpha + Number(step.dataset.alphaStep));
      changed();
    });
  };

  const routeShare = (a, requests) => {
    const r = a.routes;
    if (!r?.length || a.k >= 1) return null;
    if (requests <= r[0][0]) return r[0][1];
    for (let i = 1; i < r.length; i++) {
      const [n0, s0] = r[i - 1], [n1, s1] = r[i];
      if (requests <= n1) return s0 + ((s1 - s0) * Math.log2(requests / n0)) / Math.log2(n1 / n0);
    }
    return r[r.length - 1][1];
  };

  Pie.batchedCeiling = (hardware, modelId, scheme = "affine_u4_g64", benchmark = null, row = null) => {
    const machine = machines().find((m) => m.id === hardware);
    const workload = shapeOf("throughput", benchmark);
    const a = row?.miniature ? miniArch(row) : archOf(modelId);
    if (!machine?.bw || !workload || !a) return null;
    const bw = machine.bw * machine.devices;
    const tflops = machine.tflops * machine.devices;
    const requests = workload.concurrency || 1;
    const bits = bitsOf(scheme);
    const prompt = workload.prompt_tokens, answer = workload.output_tokens;
    const p = pass(a, { bits, tokens: requests, logits: requests, requests, context: prompt + answer / 2, touched: routeShare(a, requests) });
    const pre = pass(a, { bits, tokens: prompt, logits: 1, requests: 1, context: prompt });
    const steps = answer > 1 ? (answer - 1) / answer : 1;
    const readS = ((p.weightGB + p.cacheGB) / bw) * steps;
    const flops = p.flops * steps + (requests * pre.flops) / answer;
    const n = narrow(machine, scheme, p, models().find((m) => m.id === modelId)?.family);
    const tflopsNarrow = n.tflops * machine.devices;
    const mathS = mathTime(flops, p.bodyFlops * steps + (requests * pre.bodyFlops) / answer, tflops, n.share, tflopsNarrow);
    const link = linkOf(hardware);
    const linkS = link ? linkTime(a, link, machine.devices, requests) * steps + linkTime(a, link, machine.devices, requests * prompt / answer) - 2 * a.layers * link.us * 1e-6 * (1 - 1 / answer) : 0;
    const bandwidth = requests / readS;
    const compute = mathS ? requests / mathS : null;
    const interconnect = linkS ? requests / linkS : null;
    const tps = Math.min(bandwidth, compute || Infinity, interconnect || Infinity);
    const bound = tps === interconnect ? "interconnect" : tps === compute ? "compute" : "bandwidth";
    const peak = mathS && n.share ? flops / mathS / 1e12 : tflops;
    return { tps, bound, compute, bandwidth, interconnect, parts: { weightGB: p.weightGB, cacheGB: p.cacheGB, readS, mathS, linkS, link, requests, bw,
      tflops: peak, tflops16: tflops, tflopsNarrow, narrow: n.share, devices: machine.devices } };
  };

  Pie.methodology = {
    menu(k) {
      const select = element.querySelector(`select[data-k="${k}"]`);
      return select ? [...select.options].map((o) => ({ value: o.value, label: o.text, selected: o.selected })) : [];
    },
    pick(k, value) {
      const select = element.querySelector(`select[data-k="${k}"]`);
      if (!select) return;
      select.value = value;
      select.dispatchEvent(new Event("input", { bubbles: true }));
    },
    element,
    render(state) {
      element.hidden = state.table !== "methodology";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `${settingsBar}<div class="method-inner">${content}</div>`;
        bind();
        element.dataset.ready = "1";
      }
    },
  };
})();
