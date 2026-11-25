const params = new URLSearchParams(location.search);
const name = params.get("engine");
const options = JSON.parse(params.get("options") || "{}");
let engine = null;
let progress = performance.now();
const tick = () => { progress = performance.now(); };

async function adapterInfo() {
  if (!navigator.gpu) throw new Error("this browser has no WebGPU (navigator.gpu is missing)");
  let adapter = null;
  for (let i = 0; i < 30 && !adapter; i++) {
    adapter = await navigator.gpu.requestAdapter({ powerPreference: "high-performance" });
    if (!adapter) await new Promise((r) => setTimeout(r, 500));
  }
  if (!adapter) throw new Error("WebGPU has no adapter");
  const i = adapter.info || {};
  const limits = {};
  for (const k of ["maxBufferSize", "maxStorageBufferBindingSize", "maxComputeWorkgroupStorageSize", "maxComputeInvocationsPerWorkgroup"]) limits[k] = adapter.limits[k];
  const out = { vendor: i.vendor, architecture: i.architecture, device: i.device, description: i.description, limits, features: [...adapter.features].sort() };
  if (/swiftshader|llvmpipe|lavapipe|software/i.test(`${i.vendor} ${i.architecture} ${i.description} ${i.device}`) || i.isFallbackAdapter) {
    throw new Error(`WebGPU gave a software adapter (${JSON.stringify(out)}), not the GPU`);
  }
  return out;
}

async function boot() {
  const adapter = await adapterInfo();
  const mod = await import(`./engines/${name}.mjs`);
  const t0 = performance.now();
  const loaded = await mod.load(options);
  engine = mod;
  return { engine: name, adapter, load_s: (performance.now() - t0) / 1000, ua: navigator.userAgent, ...loaded };
}

async function one(req, sampling) {
  const stamps = [];
  const send = performance.now();
  try {
    const r = await engine.generate({ ...req, ...sampling, onToken: (n = 1) => { const t = performance.now(); progress = t; for (let k = 0; k < n; k++) stamps.push(t); } });
    const end = performance.now();
    tick();
    const s = r.stamps || stamps;
    return { ok: true, send_ms: send, first_ms: r.first_ms ?? s[0] ?? null, end_ms: end, stamps_ms: s, prompt_tokens: r.prompt_tokens, output_tokens: r.output_tokens ?? s.length, text: r.text };
  } catch (e) {
    return { ok: false, send_ms: send, end_ms: performance.now(), error: String(e?.message ?? e) };
  }
}

async function pool(reqs, concurrency, sampling) {
  const out = new Array(reqs.length);
  let next = 0;
  const lane = async () => {
    while (next < reqs.length) {
      const i = next++;
      out[i] = await one(reqs[i], { ...sampling, timing: concurrency === 1 });
    }
  };
  await Promise.all(Array.from({ length: Math.max(1, Math.min(concurrency, reqs.length)) }, lane));
  return out;
}

async function run(job) {
  tick();
  const sampling = job.sampling || {};
  const warm = await pool(job.warmup || [], 1, sampling);
  const bad = warm.find((r) => !r.ok);
  if (bad) return { error: `warmup failed: ${bad.error}`, results: [] };
  const t0 = performance.now();
  const results = await pool(job.requests, job.concurrency || 1, sampling);
  const wall = (performance.now() - t0) / 1000;
  const rel = (ms) => (ms == null ? null : (ms - t0) / 1000);
  return {
    wall_s: wall,
    stats: engine.stats ? await engine.stats() : {},
    results: results.map((r) => ({ ...r, send_s: rel(r.send_ms), first_s: rel(r.first_ms), end_s: rel(r.end_ms), stamps_s: (r.stamps_ms || []).map(rel), stamps_ms: undefined })),
  };
}

window.bench = { boot, run, age: () => performance.now() - progress };
