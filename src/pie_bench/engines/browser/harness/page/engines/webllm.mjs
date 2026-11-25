import * as webllm from "/vendor/@mlc-ai/web-llm/lib/index.js";

let engine = null;
let id = null;

export async function load(o) {
  id = o.model_id;
  const record = { model: new URL(o.model_url, location.href).href, model_id: id, model_lib: new URL(o.model_lib, location.href).href, overrides: o.overrides || {} };
  if (o.required_features) record.required_features = o.required_features;
  if (o.model_manifest) record.model_manifest = o.model_manifest;
  if (o.buffer_size_required_bytes) record.buffer_size_required_bytes = o.buffer_size_required_bytes;
  let last = 0;
  engine = await webllm.CreateMLCEngine(id, {
    appConfig: { model_list: [record], useIndexedDBCache: false },
    initProgressCallback: (p) => {
      if (p.progress - last >= 0.1 || p.progress === 1) { last = p.progress; console.log(`webllm: ${p.text}`); }
    },
  }, o.chat_options || {});
  return { model_id: id, web_llm: webllm.version ?? null };
}

export async function generate({ prompt, max_tokens, temperature, top_p, seed, ignore_eos, onToken }) {
  const stream = await engine.completions.create({
    prompt, max_tokens, temperature, top_p, seed, stream: true, stream_options: { include_usage: true }, ignore_eos: ignore_eos !== false,
  });
  let usage = null;
  for await (const chunk of stream) {
    if (chunk.choices?.length) onToken();
    if (chunk.usage) usage = chunk.usage;
  }
  return { prompt_tokens: usage?.prompt_tokens, output_tokens: usage?.completion_tokens };
}

export async function stats() {
  try {
    return { runtime_stats: await engine.runtimeStatsText() };
  } catch {
    return {};
  }
}
