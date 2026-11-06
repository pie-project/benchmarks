// The worker that holds llama.cpp (lw.mjs, built by llamacpp/build.sh): the GGUF is fetched as a Blob and
// mounted read-only (WORKERFS), so the weights stream from it to the GPU without a copy in the wasm heap.
// Requests come in by slot; one loop calls lw_step and posts each sampled token back as it is sampled.
let M = null;
let stepping = false;
const pending = new Map(); // slot -> true while generating

async function load(o) {
  const { default: createLw } = await import(new URL(o.module_url, location.href).href);
  M = await createLw({ print: (s) => console.log(`llama.cpp: ${s}`), printErr: (s) => console.log(`llama.cpp: ${s}`) });
  const blob = await (await fetch(new URL(o.model_url, location.href))).blob();
  M.FS.mkdir("/m");
  M.FS.mount(M.WORKERFS, { blobs: [{ name: "model.gguf", data: blob }] }, "/m");
  const t0 = performance.now();
  const rc = await M.ccall("lw_load", "number", ["string", "number", "number", "number", "number", "number"],
    ["/m/model.gguf", o.n_ctx, o.n_slots, o.n_batch, o.n_ubatch, o.flash_attn ?? -1], { async: true });
  if (rc !== 0) throw new Error(`llama.cpp could not load the model (lw_load ${rc})`);
  return { load_ms: performance.now() - t0, gguf_bytes: blob.size };
}

async function loop() {
  if (stepping) return;
  stepping = true;
  const cap = 4096;
  const out = M._malloc(cap * 8);
  try {
    while (M._lw_active() > 0) {
      const n = await M.ccall("lw_step", "number", ["number", "number"], [out, cap], { async: true });
      if (n < 0) throw new Error(`llama_decode failed (${n})`);
      const t = performance.now();
      const view = M.HEAP32.subarray(out >> 2, (out >> 2) + 2 * n);
      for (let i = 0; i < n; i++) postMessage({ ev: "tok", slot: view[2 * i], token: view[2 * i + 1], t });
    }
    postMessage({ ev: "idle" });
  } catch (e) {
    postMessage({ ev: "error", error: String(e?.message ?? e) });
  } finally {
    M._free(out);
    stepping = false;
  }
}

onmessage = async ({ data }) => {
  try {
    if (data.op === "load") {
      postMessage({ id: data.id, ok: true, value: await load(data.options) });
    } else if (data.op === "submit") {
      const ids = Int32Array.from(data.ids);
      const p = M._malloc(ids.length * 4);
      M.HEAP32.set(ids, p >> 2);
      const rc = M._lw_submit(data.slot, p, ids.length, data.max_tokens, data.temperature ?? 0, data.top_p ?? 1, data.seed ?? 0);
      M._free(p);
      if (rc !== 0) throw new Error(`slot ${data.slot} busy or bad request (${rc})`);
      postMessage({ id: data.id, ok: true });
      loop();
    }
  } catch (e) {
    postMessage({ id: data.id, ok: false, error: String(e?.message ?? e) });
  }
};
