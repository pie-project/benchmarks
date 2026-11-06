// llama.cpp's WebGPU backend in the tab (a worker, llamacpp-worker.mjs), on the same GGUF the native llama.cpp rows
// load. Every request takes a free slot; the worker batches the slots' decodes and prompt chunks as llama-server does.
let worker = null;
let next = 0;
const calls = new Map();
const lanes = new Map(); // slot -> { onToken, n, resolve }
const free = [];

export async function load(o) {
  worker = new Worker(new URL("./llamacpp-worker.mjs", import.meta.url), { type: "module", name: "llama.cpp" });
  worker.onmessage = ({ data }) => {
    if (data.id != null) {
      const c = calls.get(data.id);
      calls.delete(data.id);
      return data.ok ? c.resolve(data.value) : c.reject(new Error(data.error));
    }
    if (data.ev === "tok") {
      const lane = lanes.get(data.slot);
      if (!lane) return;
      lane.n++;
      lane.onToken();
      if (lane.n >= lane.max) {
        lanes.delete(data.slot);
        free.push(data.slot);
        lane.resolve({ output_tokens: lane.n });
      }
    } else if (data.ev === "error") {
      for (const [slot, lane] of lanes) { lane.reject(new Error(data.error)); lanes.delete(slot); free.push(slot); }
    }
  };
  worker.onerror = (e) => console.log(`llama.cpp worker: ${e.message}`);
  const value = await call("load", { options: o });
  for (let i = 0; i < o.n_slots; i++) free.push(i);
  return value;
}

function call(op, body) {
  const id = ++next;
  return new Promise((resolve, reject) => {
    calls.set(id, { resolve, reject });
    worker.postMessage({ id, op, ...body });
  });
}

export async function generate({ ids, max_tokens, temperature, top_p, seed, onToken }) {
  if (!ids) throw new Error("llama.cpp here is sent token ids");
  const slot = free.shift();
  if (slot == null) throw new Error("no free slot: more requests at once than the context was sized for");
  const done = new Promise((resolve, reject) => lanes.set(slot, { onToken, n: 0, max: max_tokens, resolve, reject }));
  await call("submit", { slot, ids, max_tokens, temperature, top_p, seed });
  const r = await done;
  return { prompt_tokens: ids.length, output_tokens: r.output_tokens };
}
