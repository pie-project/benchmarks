window.Pie = window.Pie || {};

(() => {
  const TFLOPS_PER_CORE = { apple8: 0.36, apple9: 0.42, apple10: 1.53 };
  const NEURAL_ENGINE = { pie: ["apple7", "apple8", "apple9"] };

  const machines = () => (Pie.store.rows("hardware") || []).map((h) => ({
    id: h.id,
    bw: h.bandwidth_gbs || 0,
    tflops: h.tflops_fp16 || (h.vendor === "Apple" || h.class === "mac" ? +(((TFLOPS_PER_CORE[h.arch] || 0.4) * (h.gpu_cores || 0)).toFixed(1)) : 0),
    tflops8: h.tflops_fp8 || 0,
    tflopsMx: h.tflops_mxfp8 || 0,
    ane: h.ane_tflops_fp16 || 0,
    arch: h.arch,
    devices: h.count || 1,
  }));

  const HYBRID = /qwen3_5|qwen3_6|qwen4/;
  const layersFor = (p) => (p <= 5 ? 32 : p <= 15 ? 40 : p <= 40 ? 64 : 80);
  const models = () => (Pie.store.rows("models") || []).filter((m) => m.params_b).map((m) => {
    const layers = m.layers || layersFor(m.params_b);
    return {
      id: m.id,
      total: m.params_b,
      active: m.active_b || m.params_b,
      layers,
      kvKB: Math.round(layers * 4 * (HYBRID.test(m.family || "") ? 0.25 : 1)),
      hidden: m.hidden_size || Math.round(Math.sqrt((m.params_b * 1e9) / (12 * layers))),
      family: m.family || "",
    };
  });

  const DRAFT_B = 0.5;
  const WIDEST = 16;

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
})();
