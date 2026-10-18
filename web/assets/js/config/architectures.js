window.Pie = window.Pie || {};

// Each model's architecture, as the bounds need it, from its config.json and the parameter count of its original
// safetensors on Hugging Face (fetched 2026-10-18). Billions of parameters unless named otherwise:
//   total    every parameter, embeddings included
//   emb      one embedding table, vocab x hidden; the input one is only looked up, the output head (the same table when
//            tied) is a full matmul for every token that needs logits
//   ple      Gemma's per-layer embedding tables: looked up, never read whole
//   routed   the mixture-of-experts weights (3 x hidden x expert width x experts x layers), of which k run per token
//   full / sliding / window   attention layers that read the whole context, and those that read only the last window
//   kvLayer  bytes of K and V per token per attention layer (kv heads x head dim x 2 x bf16)
//   linear / state            linear-attention layers and the bytes of the fixed state each reads and writes per step
//   layers / shared           all layers, and those that reuse an earlier layer's K and V (Gemma's KV sharing): a
//                             prompt token only fills the cache, so it never needs those layers
Pie.architectures = {
  "gemma-4-e2b": { total: 5.123, emb: 0.403, tied: true, ple: 2.349, routed: 0, k: 1, full: 7, sliding: 28, window: 512, kvLayer: 1024, linear: 0, state: 0, layers: 35, shared: 20 },
  "gemma-4-e4b": { total: 7.996, emb: 0.671, tied: true, ple: 2.819, routed: 0, k: 1, full: 7, sliding: 35, window: 512, kvLayer: 2048, linear: 0, state: 0, layers: 42, shared: 18 },
  "gemma-4-12b": { total: 11.96, emb: 1.007, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 40, window: 1024, kvLayer: 8192, linear: 0, state: 0, layers: 48, shared: 0 },
  "gemma-4-26b-a4b": { total: 25.806, emb: 0.738, tied: true, ple: 0, routed: 22.838, k: 0.0625, full: 5, sliding: 25, window: 1024, kvLayer: 8192, linear: 0, state: 0, layers: 30, shared: 0 },
  "gemma-4-31b": { total: 31.273, emb: 1.409, tied: true, ple: 0, routed: 0, k: 1, full: 10, sliding: 50, window: 1024, kvLayer: 16384, linear: 0, state: 0, layers: 60, shared: 0 },
  "qwen3.5-4b": { total: 4.66, emb: 0.636, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 2097152, layers: 32, shared: 0 },
  "qwen3.5-9b": { total: 9.653, emb: 1.017, tied: false, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 2097152, layers: 32, shared: 0 },
  "qwen3.6-35b-a3b": { total: 35.952, emb: 0.509, tied: false, ple: 0, routed: 32.212, k: 0.03125, full: 10, sliding: 0, window: 0, kvLayer: 2048, linear: 30, state: 2097152, layers: 40, shared: 0 },
  "qwen3.8-27b": { total: 27.781, emb: 1.271, tied: false, ple: 0, routed: 0, k: 1, full: 16, sliding: 0, window: 0, kvLayer: 4096, linear: 48, state: 3145728, layers: 64, shared: 0 },
  "qwen3.8-flash-next": { total: 180.0, emb: 0.636, tied: false, ple: 0, routed: 120.796, k: 0.01953, full: 12, sliding: 0, window: 0, kvLayer: 2048, linear: 36, state: 3145728, layers: 48, shared: 0 },
  "gpt-oss-20b": { total: 20.915, emb: 0.579, tied: false, ple: 0, routed: 19.11, k: 0.125, full: 12, sliding: 12, window: 128, kvLayer: 2048, linear: 0, state: 0, layers: 24, shared: 0 },
  "muse-glimmer-30b": { total: 29.777, emb: 1.345, tied: false, ple: 0, routed: 0, k: 1, full: 13, sliding: 39, window: 2048, kvLayer: 1024, linear: 0, state: 0, layers: 52, shared: 0 },
};
