window.Pie = window.Pie || {};

// Each model's architecture, as the bounds need it, from its config.json and the parameter count of its original
// safetensors on Hugging Face (fetched 2026-10-18). Billions of parameters unless named otherwise:
//   total    every parameter of the text model, embeddings included; a multimodal checkpoint's vision and audio
//            encoders are left out (counted from the mlx-community safetensors, 2026-10-19): text never runs them. So is
//            Qwen3.5's multi-token-prediction layer (mtp_num_hidden_layers: 1, its fc, one attention layer and its MLP
//            or experts): a drafter, which decode without speculation never runs
//   emb      one embedding table, vocab x hidden; the input one is only looked up, the output head (the same table when
//            tied) is a full matmul for every token that needs logits
//   ple      Gemma's per-layer embedding tables: looked up, never read whole
//   routed   the mixture-of-experts weights (3 x hidden x expert width x experts x layers), of which k run per token
//   full / sliding / window   attention layers that read the whole context, and those that read only the last window
//   kvLayer  bytes of K and V per token per attention layer (kv heads x head dim x 2 x bf16)
//   kvFull   the same for the full-attention layers where they have their own geometry: Gemma 4's global layers have
//            global_head_dim 512 and num_global_key_value_heads (num_key_value_heads where the config has none); with
//            attention_k_eq_v their V is projected by K's weights but normed apart, and engines cache both
//   linear / state            linear-attention layers and the bytes of the fixed state each reads and writes per step
//   hidden                    the model width: the activations multi-GPU runs exchange every layer are tokens x hidden
//   layers / shared           all layers, and those that reuse an earlier layer's K and V (Gemma's KV sharing): a
//                             prompt token only fills the cache, so it never needs those layers
Pie.architectures = {
  "gemma-4-e2b": { total: 4.647, emb: 0.403, tied: true, ple: 2.349, routed: 0, k: 1, full: 7, sliding: 28, window: 512, kvLayer: 1024, kvFull: 2048, linear: 0, state: 0, layers: 35, shared: 20, hidden: 1536 },
  "gemma-4-e4b": { total: 7.518, emb: 0.671, tied: true, ple: 2.819, routed: 0, k: 1, full: 7, sliding: 35, window: 512, kvLayer: 2048, kvFull: 4096, linear: 0, state: 0, layers: 42, shared: 18, hidden: 2560 },
  "gemma-4-12b": { total: 11.908, emb: 1.007, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 40, window: 1024, kvLayer: 8192, kvFull: 2048, linear: 0, state: 0, layers: 48, shared: 0, hidden: 3840 },
  "gemma-4-26b-a4b": { total: 25.233, emb: 0.738, tied: true, ple: 0, routed: 22.838, k: 0.0625, full: 5, sliding: 25, window: 1024, kvLayer: 8192, kvFull: 4096, linear: 0, state: 0, layers: 30, shared: 0, hidden: 2816 },
  "gemma-4-31b": { total: 30.697, emb: 1.409, tied: true, ple: 0, routed: 0, k: 1, full: 10, sliding: 50, window: 1024, kvLayer: 16384, kvFull: 8192, linear: 0, state: 0, layers: 60, shared: 0, hidden: 5376 },
  "qwen3.5-4b": { total: 4.205, emb: 0.636, tied: true, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 2097152, layers: 32, shared: 0, hidden: 2560 },
  "qwen3.5-9b": { total: 8.954, emb: 1.017, tied: false, ple: 0, routed: 0, k: 1, full: 8, sliding: 0, window: 0, kvLayer: 4096, linear: 24, state: 2097152, layers: 32, shared: 0, hidden: 4096 },
  "qwen3.6-35b-a3b": { total: 34.661, emb: 0.509, tied: false, ple: 0, routed: 32.212, k: 0.03125, full: 10, sliding: 0, window: 0, kvLayer: 2048, linear: 30, state: 2097152, layers: 40, shared: 0, hidden: 2048 },
  "qwen3.8-27b": { total: 26.895, emb: 1.271, tied: false, ple: 0, routed: 0, k: 1, full: 16, sliding: 0, window: 0, kvLayer: 4096, linear: 48, state: 3145728, layers: 64, shared: 0, hidden: 5120 },
  "qwen3.8-flash-next": { total: 176.944, emb: 0.636, tied: false, ple: 51.2, routed: 120.796, k: 0.01953, full: 12, sliding: 0, window: 0, kvLayer: 2048, linear: 36, state: 3145728, layers: 48, shared: 0, hidden: 2560 },  // total without its 2.607 B MTP layer (run only when speculating); ple is its n-gram table (config ple_*: 16 hash heads of ~20M rows of 160, one row from each a token), a lookup like Gemma's; both from the safetensors headers, 2026-11-07
  "gpt-oss-20b": { total: 20.915, emb: 0.579, tied: false, ple: 0, routed: 19.11, k: 0.125, full: 12, sliding: 12, window: 128, kvLayer: 2048, linear: 0, state: 0, layers: 24, shared: 0, hidden: 2880 },
  "muse-glimmer-30b": { total: 27.855, emb: 1.345, tied: false, ple: 0, routed: 0, k: 1, full: 13, sliding: 39, window: 2048, kvLayer: 1024, linear: 0, state: 0, layers: 52, shared: 0, hidden: 6656 },
  "qwen3.5-0.8b": { total: 0.752, emb: 0.254, tied: true, ple: 0, routed: 0, k: 1, full: 6, sliding: 0, window: 0, kvLayer: 2048, linear: 18, state: 1048576, layers: 24, shared: 0, hidden: 1024 },
  "qwen3.6-27b": { total: 26.895, emb: 1.271, tied: false, ple: 0, routed: 0, k: 1, full: 16, sliding: 0, window: 0, kvLayer: 4096, linear: 48, state: 3145728, layers: 64, shared: 0, hidden: 5120 },
  "gpt-oss-120b": { total: 116.829, emb: 0.579, tied: false, ple: 0, routed: 114.662, k: 0.03125, full: 18, sliding: 18, window: 128, kvLayer: 2048, linear: 0, state: 0, layers: 36, shared: 0, hidden: 2880 },
  // Qwen/Qwen3-0.6B (fetched 2026-11-07): its safetensors hold 0.752 B, the tied 151936 x 1024 head stored a second
  // time as lm_head.weight; config.json ties it (tie_word_embeddings), so the model has 0.596 B, 0.440 B of them body
  "qwen3-0.6b": { total: 0.596, emb: 0.156, tied: true, ple: 0, routed: 0, k: 1, full: 28, sliding: 0, window: 0, kvLayer: 4096, linear: 0, state: 0, layers: 28, shared: 0, hidden: 1024 },
};
