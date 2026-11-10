window.Pie = window.Pie || {};
// Engine Gaps conclusions by "hardware|model|setup" as [conclusion, short note, detail on hover]: a quick smoke
// classification of every cell where pie and the strongest other engine are 25% or more apart (2026-11-10).
// explained: a known cause; plausible: inside the hardware limit, cause not traced; rerun: the numbers look wrong;
// real: pie is slower. A slice keeps the full model's layer shapes, so its gap is classified like any other.
Pie.gapNotes = {
 "web-rtx5090|gemma-4-e4b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx4090|gemma-4-e4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx5090|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "h200-x1|glm-5.3|pbatch": [
  "rerun",
  "pie row above the card's limit",
  "pie's 1.6M tok/s is 5.6x above this card's compute bound (289k), with a 74 ms TTFT for 256 prompts. The pie row cannot be right; rerun it."
 ],
 "m5-max-128g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx4090|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|decode": [
  "rerun",
  "vLLM MiMo decode at 6 tok/s",
  "vLLM 0.32.0 decodes this MiMo slice at 6 tok/s on MI300X (pie 94; SGLang reaches 160 on MI350X). Likely a slow fallback kernel in vLLM's ROCm path; not confirmed."
 ],
 "m5-max-64g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "m3-16g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "m4-pro-48g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "tpu-v5e-1|deepseek-v4-flash|decode": [
  "explained",
  "No SparseCore on v5e: plain gather",
  "A v5e has no SparseCore, so DeepSeek-V4's sparse-attention gather runs as a plain XLA gather and its compressor as tpu-inference's reference code, at a 0.65 HBM share."
 ],
 "m5-max-128g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx4090|gemma-4-e2b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx5090|gemma-4-e2b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "web-rtx4090|gemma-4-e4b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "tpu-v6e-1|deepseek-v4-flash|decode": [
  "plausible",
  "vLLM-TPU experimental V4 kernels",
  "vLLM-TPU serves DeepSeek-V4 through tpu-inference's experimental kernels and a 0.75 HBM share on v6e; decode runs 78 vs pie's 387 tok/s."
 ],
 "a100-sxm-x1|glm-5.3-flash|decode": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "tpu-v6e-1|glm-5.3|prefill": [
  "rerun",
  "sglang-jax GLM prefill slow, unknown",
  "sglang-jax 0.1.0rc0 takes 97-228 ms for the 555-token prompt vs pie's 21-50 ms. Its GLM-5 path runs with DSA off by default, which does not matter at this length; cause not found."
 ],
 "tpu-v5e-1|glm-5.3|prefill": [
  "rerun",
  "sglang-jax GLM prefill slow, unknown",
  "sglang-jax 0.1.0rc0 takes 97-228 ms for the 555-token prompt vs pie's 21-50 ms. Its GLM-5 path runs with DSA off by default, which does not matter at this length; cause not found."
 ],
 "a100-pcie-x1|glm-5.3-flash|decode": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "web-rtx5090|gemma-4-e4b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "l40s-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "b200-x1|gemma-4-e4b|prefill": [
  "explained",
  "SGLang prefill graph off for Gemma-4",
  "Gemma-4 is multimodal and not on SGLang's breakable-graph allowlist, so SGLang 0.5.22 runs its prefill eager: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "l40s-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "m3-16g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx4090|gemma-4-26b-a4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|batching": [
  "rerun",
  "vLLM MiMo decode at 6 tok/s",
  "vLLM 0.32.0 decodes this MiMo slice at 6 tok/s on MI300X (pie 94; SGLang reaches 160 on MI350X). Likely a slow fallback kernel in vLLM's ROCm path; not confirmed."
 ],
 "m2-16g|qwen3.8-flash-next|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "web-rtx4090|gemma-4-12b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "rtx4090-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "a100-sxm-x1|glm-5.3|decode": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "web-rtx4090|gemma-4-31b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang prefill graph off for Gemma-4",
  "Gemma-4 is multimodal and not on SGLang's breakable-graph allowlist, so SGLang 0.5.22 runs its prefill eager: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "b200-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "web-rtx5090|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "mi355x-x1|deepseek-v4.1-flash|prefill": [
  "rerun",
  "SGLang run 7x off its own MI350X",
  "SGLang's TTFT here (174 ms) is 7x its own MI350X figure (23 ms) for the same slice, so this SGLang run looks bad."
 ],
 "web-rtx4090|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|muse-glimmer-30b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "rtx5090-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx5090|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|gemma-4-12b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "mi355x-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "mi300x-x1|deepseek-v4-flash|batching": [
  "plausible",
  "vLLM ROCm: Triton sparse MLA",
  "ROCm has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse MLA and indexer logits through its Triton fallbacks; decode trails pie 2x."
 ],
 "a40-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "web-rtx5090|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|muse-glimmer-30b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m3-16g|qwen3.8-27b|pbatch": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "Cold, pie prefills this slice 1.7x faster (240 vs 141-145 tok/s, pf8 236 vs 135), not from the quant mix: on M2-M4 pie runs 47% of the dense prefill matmuls on the Neural Engine. The site's 2.5-3.1x adds Air throttling."
 ],
 "mi300x-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "web-rtx4090|qwen3.5-9b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "a40-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "mi300x-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "web-rtx4090|qwen3.8-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m5-max-64g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx5090|gemma-4-26b-a4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m5-max-64g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Each decode step vllm-metal gathers every request's fp32 Mamba-2 state (8.4 MB per layer) out of its slot pool and scatters it back. Real slice on M3: Mamba layer 30.4 vs 16.2 ms in mlx-lm, step 200 vs 147 ms."
 ],
 "mi300x-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "web-rtx4090|gpt-oss-120b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gpt-oss-120b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m4-pro-48g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx4090|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m5-max-128g|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp: 17+ row cliff, no KV prune",
  "Two llama.cpp limits: a step with 17-32 sequences runs kernel_mul_mm and costs 2.5x a 16-row step (M5 Max 12.9 to 31.9 ms), and with >1 slot it stops skipping the KV-shared layers for prompts (3734 to 1358 tok/s)."
 ],
 "web-rtx4090|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m3-16g|qwen3.8-27b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m5-max-128g|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "m5-max-128g|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp: 17+ row cliff, no KV prune",
  "Two llama.cpp limits: a step with 17-32 sequences runs kernel_mul_mm and costs 2.5x a 16-row step (M5 Max 12.9 to 31.9 ms), and with >1 slot it stops skipping the KV-shared layers for prompts (3734 to 1358 tok/s)."
 ],
 "mi350x-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "m5-max-128g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 requests ran one at a time. Without a seed mlx-lm reaches 4.7x more (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx4090|gpt-oss-20b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx4090|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m3-16g|qwen3.6-27b|batching": [
  "rerun",
  "c8 rounds outlast the Air's cool window",
  "On the fanless 16 GB Airs llama.cpp's c8 round runs about 160 s, past the ~95 s after which the m3 throttles (measured on these slices); pie's ~60 s round stays cool. Not re-measured at c8: rerun with cooling."
 ],
 "web-rtx5090|gemma-4-12b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "b200-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "h200-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "tpu-v5e-1|glm-5.3|pbatch": [
  "plausible",
  "sglang-jax: early TPU port",
  "sglang-jax is an early TPU port (0.1.0rc0, or main for Gated DeltaNet models) and pays more per request; its TTFT runs 6x pie's on this cell."
 ],
 "h100-pcie-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "h200-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "tpu-v5e-1|deepseek-v4-flash|prefill": [
  "explained",
  "No SparseCore on v5e: plain gather",
  "A v5e has no SparseCore, so DeepSeek-V4's sparse-attention gather runs as a plain XLA gather and its compressor as tpu-inference's reference code, at a 0.65 HBM share."
 ],
 "web-rtx5090|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "mi350x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "a100-sxm-x1|glm-5.3|batching": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "web-rtx5090|gemma-4-12b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m5-max-128g|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "h100-sxm-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "mi300x-x1|gpt-oss-20b|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "web-rtx4090|gemma-4-31b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "m3-16g|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "mi355x-x1|qwen3-0.6b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "h100-sxm-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi300x-x1|qwen3-0.6b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi300x-x1|gemma-4-26b-a4b|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "mi355x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "tpu-v5e-1|gpt-oss-20b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "m3-16g|qwen3.8-27b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "Cold, pie prefills this slice 1.7x faster (240 vs 141-145 tok/s, pf8 236 vs 135), not from the quant mix: on M2-M4 pie runs 47% of the dense prefill matmuls on the Neural Engine. The site's 2.5-3.1x adds Air throttling."
 ],
 "tpu-v5e-1|gpt-oss-120b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "mi300x-x1|deepseek-v4.1-flash|batching": [
  "plausible",
  "vLLM ROCm: Triton sparse MLA",
  "ROCm has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse MLA and indexer logits through its Triton fallbacks; decode trails pie 2x."
 ],
 "mi350x-x1|qwen3-0.6b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "b200-x1|qwen3.8-flash-next|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "tpu-v5e-1|gpt-oss-20b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v5e-1|gpt-oss-120b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi300x-x1|deepseek-v4.1-flash|decode": [
  "plausible",
  "vLLM ROCm: Triton sparse MLA",
  "ROCm has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse MLA and indexer logits through its Triton fallbacks; decode trails pie 2x."
 ],
 "tpu-v5e-1|glm-5.3|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m5-max-128g|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "m4-pro-48g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Each decode step vllm-metal gathers every request's fp32 Mamba-2 state (8.4 MB per layer) out of its slot pool and scatters it back. Real slice on M3: Mamba layer 30.4 vs 16.2 ms in mlx-lm, step 200 vs 147 ms."
 ],
 "web-rtx4090|gemma-4-e2b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro4500-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|pbatch": [
  "real",
  "llama.cpp MoE batched prefill slower",
  "llama-server matches its own kernels here (M4 Pro: batched-bench 812-824 tok/s, site pf32 820), so the gap is llama.cpp's MoE prefill (mul_mm_id, ~16 tokens per expert per 512 ubatch). pie: 1171 on M4 Pro."
 ],
 "m3-16g|qwen3.5-9b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m5-max-128g|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "web-rtx4090|gpt-oss-120b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx4090|qwen3.5-4b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "m2-16g|qwen3.6-27b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h100-sxm-x1|gemma-4-e4b|prefill": [
  "explained",
  "SGLang prefill graph off for Gemma-4",
  "Gemma-4 is multimodal and not on SGLang's breakable-graph allowlist, so SGLang 0.5.22 runs its prefill eager: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "mi355x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "m5-max-128g|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "tpu-v5e-1|deepseek-v4-flash|batching": [
  "explained",
  "No SparseCore on v5e: plain gather",
  "A v5e has no SparseCore, so DeepSeek-V4's sparse-attention gather runs as a plain XLA gather and its compressor as tpu-inference's reference code, at a 0.65 HBM share."
 ],
 "m2-16g|qwen3.6-35b-a3b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m2-16g|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx4090|gpt-oss-20b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "rtx4090-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "mi350x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "web-rtx5090|gemma-4-26b-a4b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "web-rtx5090|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "web-rtx5090|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m5-max-128g|gemma-4-12b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "h200-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "pro6000-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx5090|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "m3-16g|qwen3.5-9b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx5090|gemma-4-e2b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx5090|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx5090|gpt-oss-120b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "web-rtx5090|gpt-oss-120b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "h200-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "mi300x-x1|deepseek-v4-flash|decode": [
  "plausible",
  "vLLM ROCm: Triton sparse MLA",
  "ROCm has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse MLA and indexer logits through its Triton fallbacks; decode trails pie 2x."
 ],
 "l4-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "web-rtx5090|muse-glimmer-30b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|gpt-oss-20b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|qwen3.8-27b|decode": [
  "explained",
  "Fanless Air throttles llama.cpp's round",
  "The fanless Air throttles after ~95 s of load. llama.cpp's longer round crosses that at request 3 of 6, so its median is the throttled 7.1 tok/s. Cold: pie 15.0, llama.cpp 13.5 (14.6 at pie's bytes)."
 ],
 "m3-16g|qwen3.6-35b-a3b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi350x-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "a100-x2|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "rtx4090-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "h100-sxm-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m3-16g|gemma-4-31b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m2-16g|gpt-oss-120b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx4090|qwen3.5-4b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "WebLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi355x-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "a100-sxm-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|glm-5.3|prefill": [
  "plausible",
  "SGLang: torch top-k for DSA",
  "On sm_100 the harness's SGLang uses a torch top-k for DSA when index_topk is not 2048, as in these GLM-5.3 slices."
 ],
 "rtx5090-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m2-16g|qwen3.8-27b|pbatch": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "Cold, pie prefills this slice 1.7x faster (240 vs 141-145 tok/s, pf8 236 vs 135), not from the quant mix: on M2-M4 pie runs 47% of the dense prefill matmuls on the Neural Engine. The site's 2.5-3.1x adds Air throttling."
 ],
 "mi300x-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "a40-x1|glm-5.3-flash|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx5090|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|mimo-v2.6-flash-rl|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "web-rtx5090|qwen3.5-9b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "web-rtx5090|qwen3.8-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|batching": [
  "explained",
  "llama.cpp MoE: per-token expert matvecs",
  "Below 32 tokens ggml-metal runs experts as per-token mat-vecs (mul_mv_id), so the step grows with batch: Qwen3.6-35B-A3B on M4 Pro 18 ms at 1, 213 ms at 31, 169 ms at 32. The UD GGUF also reads 1.55x pie's bytes."
 ],
 "web-rtx5090|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "l40s-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "tpu-v6e-1|qwen3.5-0.8b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "rtx5090-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Each decode step vllm-metal gathers every request's fp32 Mamba-2 state (8.4 MB per layer) out of its slot pool and scatters it back. Real slice on M3: Mamba layer 30.4 vs 16.2 ms in mlx-lm, step 200 vs 147 ms."
 ],
 "b200-x1|glm-5.3-flash|prefill": [
  "plausible",
  "SGLang: torch top-k for DSA",
  "On sm_100 the harness's SGLang uses a torch top-k for DSA when index_topk is not 2048, as in these GLM-5.3 slices."
 ],
 "mi300x-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "web-rtx5090|muse-glimmer-30b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "b200-x1|deepseek-v4-flash|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "tpu-v6e-1|gpt-oss-20b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "tpu-v6e-1|gpt-oss-120b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "a40-x1|glm-5.3|pbatch": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "mi355x-x1|qwen3.5-9b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "mi300x-x1|glm-5.3|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "web-rtx5090|qwen3.5-4b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|qwen3.6-35b-a3b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-128g|gemma-4-31b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "rtx5090-x1|glm-5.3|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m2-16g|qwen3.6-27b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|qwen3.6-35b-a3b|decode": [
  "explained",
  "UD GGUF reads 1.55x more bytes per token",
  "The unsloth UD-Q4_K_M GGUF keeps attention/SSM in Q8_0: 2.56 GB per token vs 1.65 GB for pie's MLX 4-bit. Requantized to pure Q4_K, llama.cpp goes 24.5 -> 36.3 tok/s; pie's 44.8 leaves a real 1.24x."
 ],
 "tpu-v5p-8|qwen3.5-0.8b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "mi350x-x1|qwen3.5-9b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "mi300x-x1|gpt-oss-120b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "tpu-v5e-1|glm-5.3|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "rtx5090-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "b200-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "l40s-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "web-rtx4090|qwen3.5-9b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "web-rtx5090|qwen3.8-27b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi300x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "mi350x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "h100-pcie-x1|qwen3-0.6b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "SGLang's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "rtx5090-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "mi355x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "m2-16g|qwen3.5-9b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi350x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "mi355x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "mi300x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "mi300x-x1|minimax-m3.1-flash|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx4090|qwen3.5-9b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "tpu-v5e-1|gpt-oss-20b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "h100-sxm-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "h100-sxm-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "plausible",
  "TRT-LLM host path at one request",
  "Few cells: TRT-LLM's single-request TTFT runs 5-40 ms above pie's (PyTorch-backend host path), most on the Nemotron-3 hybrid Mamba slices."
 ],
 "pro4500-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m3-16g|qwen3.6-35b-a3b|pbatch": [
  "explained",
  "Throttled pf8 round on a fanless Air",
  "Cold, llama.cpp's harness-shaped pf8 reaches 386 tok/s, not the site's 268: the site round followed hot c8 rounds and its waves slowed from 12 s to 16-18 s as the Air throttled. Cold gap to pie (476) is 1.23x."
 ],
 "web-rtx5090|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "l40s-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m5-max-128g|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp MoE: per-token expert matvecs",
  "Below 32 tokens ggml-metal runs experts as per-token mat-vecs (mul_mv_id), so the step grows with batch: Qwen3.6-35B-A3B on M4 Pro 18 ms at 1, 213 ms at 31, 169 ms at 32. The UD GGUF also reads 1.55x pie's bytes."
 ],
 "tpu-v5e-1|gpt-oss-120b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "b200-x1|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|qwen3-0.6b|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "rtx5090-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "mi350x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "pro4500-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "tpu-v6e-1|deepseek-v4-flash|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "web-rtx5090|gemma-4-31b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "pro4500-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "pro4500-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "mi355x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "tpu-v6e-1|glm-5.3|pbatch": [
  "plausible",
  "sglang-jax: early TPU port",
  "sglang-jax is an early TPU port (0.1.0rc0, or main for Gated DeltaNet models) and pays more per request; its TTFT runs 6x pie's on this cell."
 ],
 "a100-sxm-x1|glm-5.3|pbatch": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "h100-sxm-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang prefill graph off for Gemma-4",
  "Gemma-4 is multimodal and not on SGLang's breakable-graph allowlist, so SGLang 0.5.22 runs its prefill eager: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "pro6000-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "pro6000-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "pro4500-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "tpu-v5p-8|qwen3.5-0.8b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "m3-16g|gpt-oss-120b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v5e-1|qwen3-0.6b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "m2-16g|muse-glimmer-30b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m4-pro-48g|qwen3.8-27b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "m4-pro-48g|qwen3.6-27b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "l40s-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "b200-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi350x-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "tpu-v6e-1|gemma-4-26b-a4b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "mi300x-x1|qwen3.6-35b-a3b|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "m2-16g|qwen3.8-flash-next|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "a40-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "b200-x1|muse-glimmer-30b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-128g|muse-glimmer-30b|prefill": [
  "rerun",
  "Stale Oct 20-21 rows",
  "Both numbers are from Oct 20-21 (pie 903, llama.cpp b11756 541). On the m3 the same dense model's cold prefill is level (pie 160, llama.cpp 154). Rerun on current builds."
 ],
 "mi300x-x1|kimi-k3|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "a100-sxm-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "rtx5090-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "tpu-v6e-1|qwen3-0.6b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "mi300x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "pro4500-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "tpu-v6e-1|glm-5.3|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "b200-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|gpt-oss-120b|pbatch": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "m2-16g|muse-glimmer-30b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "rtx4090-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "h100-sxm-x4|gpt-oss-120b|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "a40-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "vLLM: MiniMax MSA on Triton",
  "MiniMax-M3's sparse attention (MSA) runs on vLLM's Triton path below sm_100, and the MXFP8 weights need fallbacks on these cards."
 ],
 "b200-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "mi355x-x1|nvidia-nemotron-3-super-120b-a12b|pbatch": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "m3-16g|qwen3.6-27b|prefill": [
  "explained",
  "MLX prefill on GPU only; pie adds ANE",
  "vllm-metal prefills like mlx-lm on M3 (9 models within 5%). MLX spends 96% of a 554-token Qwen3.5-9B prefill in GPU qmm at 2.76 TFLOPS; pie sends part of its prefill matmuls to the Neural Engine in int8 on M1-M4."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "web-rtx4090|gemma-4-26b-a4b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "m4-pro-48g|qwen3.5-9b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "web-rtx4090|qwen3.6-27b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "tpu-v5e-1|gemma-4-26b-a4b|decode": [
  "plausible",
  "vLLM-TPU per-step host work",
  "Batch-1 decode well below the bandwidth bound: vLLM-TPU's per-step host work (Python scheduler, input prep, JAX dispatch) is not hidden at one request."
 ],
 "m5-max-128g|gemma-4-e2b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx4090|qwen3.8-27b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "m3-16g|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "m2-16g|qwen3.6-35b-a3b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|qwen3.5-9b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "tpu-v5e-1|qwen3-0.6b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "m2-16g|gemma-4-12b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|qwen3-0.6b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a40-x1|glm-5.3|batching": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "pro6000-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "tpu-v5e-1|gemma-4-12b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "pro4500-x1|glm-5.3|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "pro6000-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi300x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "h200-x1|deepseek-v4-flash|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "mi300x-x1|gpt-oss-20b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "mi300x-x1|muse-spark-open-816b-a42b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m4-pro-48g|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "m2-16g|gemma-4-26b-a4b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v5p-8|qwen3-0.6b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "h100-sxm-x4|qwen3.6-27b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "pro4500-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "rtx4090-x1|glm-5.3-flash|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "a100-sxm-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "mi355x-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "m5-max-64g|gemma-4-26b-a4b|batching": [
  "explained",
  "MLX MoE experts + split-K at 32 rows",
  "Step 55.2 ms vs pie's 35.8: mlx-lm's own 32-row forward is 48.7. Its 30 MoE layers touch 117/128 experts and read them at 358 GB/s (32.8 ms); dense linears take MLX's non-NAX split-K (11.1 vs 5.7 ms)."
 ],
 "rtx4090-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "pro6000-x4|glm-5.3-flash|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "m2-16g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "mi355x-x1|gpt-oss-120b|batching": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "b200-x1|muse-spark-open-816b-a42b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v5e-1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "web-rtx5090|qwen3.5-9b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "b200-x1|hy4-preview|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|gemma-4-31b|prefill": [
  "explained",
  "SGLang prefill graph off for Gemma-4",
  "Gemma-4 is multimodal and not on SGLang's breakable-graph allowlist, so SGLang 0.5.22 runs its prefill eager: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "web-rtx5090|qwen3.6-27b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "h100-sxm-x1|kimi-k3|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "l40s-x1|glm-5.3|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "h100-sxm-x4|gpt-oss-20b|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "m4-pro-48g|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp Metal: 17-32 row matmul cliff",
  "At 17-32 sequences ggml-metal leaves its few-row MMA matmuls for kernel_mul_mm (64x32 tiles); a step costs 1.5-2.5x the 16-row step, so 32 slots decode no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 vs 122.6 ms)."
 ],
 "tpu-v5p-8|qwen3.6-27b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "rtx5090-x1|qwen3.6-35b-a3b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "b200-x1|qwen3-0.6b|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "web-rtx5090|gpt-oss-20b|batching": [
  "explained",
  "llama.cpp tab: 32-row steps in tile GEMM",
  "c32 decode steps take 250-400 ms (Gemma-4-12B 397 vs 22.7 ms for one): 32 rows miss the 4-row mat-vec path, so each step is a low-occupancy tile GEMM plus 32 full-vocab samples on one wasm thread."
 ],
 "m3-16g|gemma-4-12b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "mi300x-x1|glm-5.3-flash|pbatch": [
  "real",
  "Rival faster on this AMD cell",
  "The rival is faster than pie on these AMD cells; no harness issue found."
 ],
 "m2-16g|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "tpu-v6e-1|muse-glimmer-30b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "web-rtx5090|qwen3.5-4b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "h200-x4|qwen3.8-flash-next|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "mi355x-x1|nvidia-nemotron-3-ultra-550b-a55b|pbatch": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "l40s-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro6000-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a40-x1|glm-5.3|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|qwen3.5-4b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "mi355x-x1|gpt-oss-20b|pbatch": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "tpu-v5e-1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "mi300x-x1|glm-5.3-flash|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "pro6000-x4|gpt-oss-120b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "tpu-v6e-1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "h200-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi355x-x1|gpt-oss-20b|batching": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "b200-x1|glm-5.3-flash|decode": [
  "plausible",
  "SGLang: torch top-k for DSA",
  "On sm_100 the harness's SGLang uses a torch top-k for DSA when index_topk is not 2048, as in these GLM-5.3 slices."
 ],
 "mi350x-x1|deepseek-v4.1-flash|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "a40-x1|minimax-m3.1-flash|pbatch": [
  "plausible",
  "vLLM: MiniMax MSA on Triton",
  "MiniMax-M3's sparse attention (MSA) runs on vLLM's Triton path below sm_100, and the MXFP8 weights need fallbacks on these cards."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|decode": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "m5-max-128g|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi355x-x1|deepseek-v4.1-flash|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "h100-sxm-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v6e-1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "m3-16g|muse-glimmer-30b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v5e-1|qwen3.8-27b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "tpu-v5e-1|qwen3.6-27b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "rtx5090-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m2-16g|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "m4-pro-48g|qwen3.5-4b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "m2-16g|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "h100-sxm-x1|deepseek-v4-flash|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "tpu-v5e-1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "a100-sxm-x1|glm-5.3-flash|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h200-x1|deepseek-v4.1-flash|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx5090|qwen3.5-9b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "pro4500-x1|qwen3.8-27b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|qwen3.8-flash-next|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "SGLang's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h100-sxm-x1|deepseek-v4-flash|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m2-16g|qwen3.6-27b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|kimi-k3|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx5090|qwen3.5-4b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "l4-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "h200-x1|deepseek-v4.1-flash|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "m3-16g|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "m2-16g|gemma-4-e2b|batching": [
  "real",
  "pie faster on both c32 phases on M2/M3",
  "Not traced on M2 (machine reserved). pie leads both phases: TTFT 2.3 vs 3.4 s (its ANE int8 prefill on M1-M4) and decode step 97 vs 140 ms. On M4 Pro and M5, vllm-metal's c32 step equals MLX's own forward."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "b200-x1|mimo-v2.6-flash-rl|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|glm-5.3-flash|batching": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "a40-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "pro4500-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "b200-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "l40s-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|gpt-oss-120b|prefill": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "h200-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h100-sxm-x1|hy4-preview|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m2-16g|gemma-4-e4b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "b200-x1|deepseek-v4-flash|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "SGLang's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m2-16g|qwen3.8-flash-next|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "web-rtx5090|gpt-oss-20b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "llama.cpp WebGPU's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "rtx4090-x1|qwen3.5-9b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m3-16g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "pro6000-x1|glm-5.3|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m3-16g|muse-glimmer-30b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v5p-8|qwen3-0.6b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-pcie-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-128g|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "b200-x1|muse-spark-open-816b-a42b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|gpt-oss-20b|prefill": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "m2-16g|muse-spark-open-816b-a42b|decode": [
  "explained",
  "pie reads a bf16 head, llama.cpp Q6_K",
  "Same cut (2 layers, 8 experts), but pie's MLX slice keeps a bf16 lm_head (3157 MiB) where the GGUF has Q6_K (1295 MiB): 4.08 vs 2.34 GB per token, both near 90 GB/s. With a bf16 head llama.cpp gets 17-20 tok/s."
 ],
 "h200-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "h100-sxm-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m3-16g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Each decode step vllm-metal gathers every request's fp32 Mamba-2 state (8.4 MB per layer) out of its slot pool and scatters it back. Real slice on M3: Mamba layer 30.4 vs 16.2 ms in mlx-lm, step 200 vs 147 ms."
 ],
 "mi350x-x1|gpt-oss-20b|prefill": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "web-rtx5090|qwen3.8-27b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "a40-x1|minimax-m3.1-flash|batching": [
  "plausible",
  "vLLM: MiniMax MSA on Triton",
  "MiniMax-M3's sparse attention (MSA) runs on vLLM's Triton path below sm_100, and the MXFP8 weights need fallbacks on these cards."
 ],
 "a100-sxm-x1|deepseek-v4-flash|decode": [
  "explained",
  "vLLM: no FlashMLA/DeepGEMM below sm_90",
  "FlashMLA's sparse kernels and DeepGEMM need sm_90/sm_100, so here vLLM runs DeepSeek-V4's sparse MLA and indexer on Triton and torch fallbacks without its decoder CUDA graphs."
 ],
 "a40-x1|glm-5.3|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi300x-x1|gpt-oss-20b|batching": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "pro6000-x4|gemma-4-e4b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "m2-16g|gemma-4-e4b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v6e-1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "mi350x-x1|gpt-oss-120b|prefill": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "l40s-x1|glm-5.3-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m5-max-128g|gpt-oss-120b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h200-x1|deepseek-v4.1-flash|pbatch": [
  "real",
  "vLLM's FlashMLA prefill is faster",
  "On Hopper vLLM's FlashMLA sparse and DeepGEMM FP8 path prefills a 256-prompt batch of DeepSeek-V4.1 30-40% faster than pie."
 ],
 "a40-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h100-sxm-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h100-sxm-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro6000-x4|qwen3.5-0.8b|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "web-rtx5090|qwen3.8-27b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "h100-pcie-x1|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "pie's gpt-oss MXFP4 prefill trails vLLM on A40, A100 x2 and H100 PCIe (TTFT 70-168 ms vs 52-120 ms). pie serves the experts W4A16."
 ],
 "rtx5090-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "h100-sxm-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro4500-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "a100-pcie-x1|qwen3.5-0.8b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "SGLang's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "l4-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a40-x1|muse-spark-open-816b-a42b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "mi300x-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "l40s-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m2-16g|gemma-4-12b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|muse-glimmer-30b|decode": [
  "explained",
  "Fanless Air throttles llama.cpp's round",
  "The fanless Air throttles after ~95 s of load. llama.cpp's longer round crosses that at request 3 of 6, so its median is the throttled 7.1 tok/s. Cold: pie 15.0, llama.cpp 13.5 (14.6 at pie's bytes)."
 ],
 "pro6000-x1|glm-5.3-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m3-16g|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "web-rtx5090|qwen3.6-27b|prefill": [
  "explained",
  "WebLLM Qwen: GDN runs token by token",
  "MLC compiles Qwen3.5's gated delta net (75% of layers) as a loop over every prompt token, one workgroup per head (32 on 9B), state in global memory. 9B prefill 658/863 tok/s vs pie 1180/1327 (4090/5090)."
 ],
 "h200-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "l4-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi355x-x1|deepseek-v4-flash|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "h100-sxm-x1|muse-spark-open-816b-a42b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "pro4500-x1|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "b200-x1|glm-5.3|pbatch": [
  "rerun",
  "TRT-LLM batched prefill slow, unknown",
  "TensorRT-LLM 1.4's batched prefill of this GLM-5.3 slice on B200 is 27% slower than pie's; no harness setting or kernel fallback found to explain it."
 ],
 "rtx5090-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "tpu-v5e-1|qwen3.6-35b-a3b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m3-16g|gemma-4-31b|batching": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi350x-x1|deepseek-v4-flash|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "pro6000-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang prefill graph off for V4",
  "SGLang 0.5.22 turns its prefill CUDA graph off for DeepSeek-V4 (capture-pool memory), so the 555-token prompt runs eager: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "l4-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|muse-spark-open-816b-a42b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "mi300x-x1|qwen3.8-flash-next|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "rtx5090-x1|gpt-oss-120b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "pro6000-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx5090-x1|glm-5.3-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "web-rtx5090|gpt-oss-120b|decode": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "h200-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a40-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|qwen3.6-35b-a3b|batching": [
  "real",
  "Rival faster on this AMD cell",
  "The rival is faster than pie on these AMD cells; no harness issue found."
 ],
 "rtx5090-x1|qwen3.8-flash-next|pbatch": [
  "rerun",
  "pie row predates batched-prefill work",
  "pie's row is from Oct 27 with a 1.64 s TTFT against TRT-LLM's 0.23 s; it predates later pie batched-prefill work and should be rerun."
 ],
 "a40-x1|gpt-oss-120b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v6e-1|gemma-4-e2b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "tpu-v6e-1|gemma-4-31b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "mi300x-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "rtx5090-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "mi300x-x1|gemma-4-e4b|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "h200-x1|gpt-oss-120b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "vLLM's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "pro6000-x4|gpt-oss-20b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "a100-sxm-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x1|gpt-oss-120b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "pro6000-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x1|deepseek-v4-flash|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-x2|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "pie's gpt-oss MXFP4 prefill trails vLLM on A40, A100 x2 and H100 PCIe (TTFT 70-168 ms vs 52-120 ms). pie serves the experts W4A16."
 ],
 "pro4500-x1|hy4-preview|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m5-max-128g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "b200-x1|muse-spark-open-816b-a42b|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "a100-pcie-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "h200-x1|qwen3-0.6b|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "h200-x1|gpt-oss-20b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "rtx5090-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "h200-x1|hy4-preview|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|qwen3.8-27b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "m5-max-64g|muse-glimmer-30b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "a100-sxm-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "rtx4090-x1|glm-5.3|prefill": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m2-16g|gemma-4-e2b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "tpu-v5p-8|gemma-4-e4b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "tpu-v6e-1|gpt-oss-20b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "tpu-v5p-8|gemma-4-e2b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "a40-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "b200-x1|minimax-m3.1-flash|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "h100-sxm-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-64g|gemma-4-e2b|prefill": [
  "explained",
  "mlx-lm runs the last prompt token apart",
  "mlx-lm prefills all but the last prompt token, calls mx.clear_cache, then runs that token as its own decode step. E2B, M5 Max: 20.4 ms prefill + 2.5 ms clear + 6.4 ms last step + ~7 ms server = 37 ms (site 34); pie 26."
 ],
 "mi300x-x1|nvidia-nemotron-3-super-120b-a12b|pbatch": [
  "real",
  "pie's ROCm Mamba-2 prefill is serial",
  "pie's ROCm Mamba-2 prefill walks the prompt token by token (CUDA uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "l40s-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|pbatch": [
  "real",
  "vLLM's FlashMLA prefill is faster",
  "On Hopper vLLM's FlashMLA sparse and DeepGEMM FP8 path prefills a 256-prompt batch of DeepSeek-V4.1 30-40% faster than pie."
 ],
 "pro6000-x1|qwen3.8-flash-next|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "a40-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi300x-x1|hy4-preview|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "rtx5090-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "rtx4090-x1|hy4-preview|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v5e-1|gemma-4-e2b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "l40s-x1|qwen3.6-35b-a3b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro6000-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro4500-x1|qwen3.6-27b|prefill": [
  "plausible",
  "TRT-LLM host path at one request",
  "Few cells: TRT-LLM's single-request TTFT runs 5-40 ms above pie's (PyTorch-backend host path), most on the Nemotron-3 hybrid Mamba slices."
 ],
 "m3-16g|gemma-4-e4b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "l40s-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x4|qwen3.8-flash-next|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi350x-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "m3-16g|gemma-4-e2b|prefill": [
  "explained",
  "pie adds the Neural Engine to prefill",
  "On M2-M4 pie offloads 47-74% of dense prefill matmuls to the Neural Engine. mlx-lm stays on the GPU at ~80% of peak (M3 2.72 of 3.4 TFLOPS, M4 Pro 6.49 of 7.9); pie's TTFT implies 3.7 and 8.6, above the GPU alone."
 ],
 "pro4500-x1|glm-5.3-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m5-max-64g|gemma-4-31b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "pro6000-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "h200-x1|mimo-v2.6-flash-rl|prefill": [
  "rerun",
  "Both engines slow on this H200 run",
  "Both engines are 6-11x slower here than on the H100 (pie TTFT 113 ms vs 10 ms there), and pie leads by 82% on the H100. Something in this H200 run is off."
 ],
 "m5-max-128g|gemma-4-e2b|prefill": [
  "explained",
  "mlx-lm runs the last prompt token apart",
  "mlx-lm prefills all but the last prompt token, calls mx.clear_cache, then runs that token as its own decode step. E2B, M5 Max: 20.4 ms prefill + 2.5 ms clear + 6.4 ms last step + ~7 ms server = 37 ms (site 34); pie 26."
 ],
 "l40s-x1|gpt-oss-120b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx4090|gpt-oss-20b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "h200-x1|qwen3.5-0.8b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m5-max-64g|qwen3.8-27b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "m5-max-128g|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "rtx5090-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "m5-max-64g|qwen3.6-27b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "a40-x1|glm-5.3-flash|pbatch": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "a40-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m4-pro-48g|qwen3.8-flash-next|decode": [
  "explained",
  "mlx-vlm decode step is host-bound",
  "mlx-vlm's Qwen3.8 step is host-bound: Python builds each token's graph in 2.4-3.3 ms and syncs once mid-step for the n-gram lookup, so it cannot overlap 1.5 ms of GPU. M5 Max: 253 tok/s, 294 without the sync; pie 345."
 ],
 "tpu-v5p-8|gemma-4-12b|prefill": [
  "rerun",
  "Stale v5p rows from Oct 21",
  "These v5p-8 rows date from Oct 21 (pie bea673037, vLLM-TPU 0.30.0). On v5e and v6e today pie leads vLLM-TPU in prefill by 30-80%, so rerun on v5p."
 ],
 "mi300x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "mi355x-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "SGLang ROCm prefill runs eager",
  "SGLang 0.5.22 turns breakable prefill CUDA graphs on only for CUDA; on ROCm every prefill runs eager, so its TTFT for the 555-token prompt runs 7-37 ms above pie's."
 ],
 "h100-sxm-x1|glm-5.3-flash|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "pro4500-x1|qwen3.5-9b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-64g|qwen3.6-35b-a3b|decode": [
  "explained",
  "mlx-lm MoE decode is dispatch-bound",
  "mlx-lm's batch-1 step is dispatch-bound: 1,797 Metal kernels per token at about 2.5 us each. M5 Max: 7.3 ms GPU step (MoE 3.8, GDN 2.4, attention 0.8, head 0.7 ms) for 1.67 GB that streams in about 2.8 ms; pie 6.0 ms."
 ],
 "m5-max-64g|qwen3.8-flash-next|decode": [
  "explained",
  "mlx-vlm decode step is host-bound",
  "mlx-vlm's Qwen3.8 step is host-bound: Python builds each token's graph in 2.4-3.3 ms and syncs once mid-step for the n-gram lookup, so it cannot overlap 1.5 ms of GPU. M5 Max: 253 tok/s, 294 without the sync; pie 345."
 ],
 "pro6000-x1|gpt-oss-120b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "h100-pcie-x1|gpt-oss-20b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m2-16g|muse-glimmer-30b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "pro4500-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a40-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m5-max-64g|qwen3.5-9b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "h100-sxm-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "b200-x1|gpt-oss-120b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi355x-x1|qwen3.5-0.8b|batching": [
  "real",
  "Rival faster on this AMD cell",
  "The rival is faster than pie on these AMD cells; no harness issue found."
 ],
 "pro6000-x4|qwen3.5-0.8b|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "a40-x1|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "pie's gpt-oss MXFP4 prefill trails vLLM on A40, A100 x2 and H100 PCIe (TTFT 70-168 ms vs 52-120 ms). pie serves the experts W4A16."
 ],
 "mi300x-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "Rivals add per-request overhead",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound; the rivals' TTFT runs 7-200 ms above pie's. gfx950 vLLM rows are AMD's 0.29.1 image."
 ],
 "web-rtx4090|qwen3.6-27b|decode": [
  "explained",
  "WebLLM: sync + full-vocab argsort/token",
  "WebLLM syncs the GPU every token and samples on the GPU with a full-vocab argsort even at temperature 0 (248k tokens). Qwen3.5-9B 60 vs pie 88 tok/s on the 5090; 27B slices 41-60 vs 55-91."
 ],
 "m2-16g|qwen3.8-flash-next|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent seed 0 with every request, and mlx-lm 0.32's server runs any seeded request alone, so these 32 prompts were prefilled one at a time. Fixed in benchmarks #1672; needs a rerun."
 ],
 "a40-x1|hy4-preview|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi350x-x1|mimo-v2.6-flash-rl|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "h100-sxm-x1|gpt-oss-20b|batching": [
  "real",
  "SGLang faster here",
  "SGLang beats pie on these batched-decode cells (gpt-oss-20b and MiMo on H100, a Gemma-4-31B slice on A40, GLM-5.3-Flash on RTX 4090); no harness issue found."
 ],
 "pro4500-x1|qwen3.6-27b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi300x-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "tpu-v6e-1|gpt-oss-120b|prefill": [
  "explained",
  "vLLM-TPU pads 555 to 1024 tokens",
  "vLLM-TPU pads each step to a power-of-two token bucket, so the 555-token prompt runs as 1024 tokens, about 1.8x the work; TTFT trails pie's by 30-80%."
 ],
 "pro4500-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "b200-x1|qwen3.8-27b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "b200-x1|qwen3.5-9b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "m2-16g|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "l40s-x1|qwen3-0.6b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "pro6000-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|decode": [
  "explained",
  "mlx-lm MoE decode is dispatch-bound",
  "mlx-lm's batch-1 step is dispatch-bound: 1,797 Metal kernels per token at about 2.5 us each. M5 Max: 7.3 ms GPU step (MoE 3.8, GDN 2.4, attention 0.8, head 0.7 ms) for 1.67 GB that streams in about 2.8 ms; pie 6.0 ms."
 ],
 "rtx4090-x1|glm-5.3-flash|batching": [
  "real",
  "SGLang faster here",
  "SGLang beats pie on these batched-decode cells (gpt-oss-20b and MiMo on H100, a Gemma-4-31B slice on A40, GLM-5.3-Flash on RTX 4090); no harness issue found."
 ],
 "mi300x-x1|qwen3.6-27b|prefill": [
  "rerun",
  "Noisy run: rounds disagree",
  "pie's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "mi355x-x1|mimo-v2.6-flash-rl|decode": [
  "real",
  "SGLang's AITER MLA decode is faster",
  "SGLang's AITER MLA decode on MI350X/MI355X beats pie's ROCm decode for these MLA slices (537-750 vs 279-467 tok/s)."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "h100-pcie-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "tpu-v5e-1|gpt-oss-20b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "a100-sxm-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx5090-x1|gpt-oss-20b|batching": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "m5-max-64g|gemma-4-12b|batching": [
  "explained",
  "MLX split-K qmm skips M5 matmul units",
  "vllm-metal's c32 step is plain MLX (Qwen3.5-9B 38.7 ms = mlx-lm's own 32-row forward). MLX 0.32.4 runs 32-row 4-bit matmuls with N under 16K as qmm_splitk, which skips M5's NAX units: about 10 of 38.7 ms."
 ],
 "pro6000-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "a100-pcie-x1|hy4-preview|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a100-pcie-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "pro6000-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM: generic Triton MoE on sm_120",
  "On sm_120 the harness's vLLM runs Muse Spark's BF16 MoE through the generic Triton path, not a tuned kernel."
 ],
 "h200-x1|glm-5.3-flash|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "h100-sxm-x1|gpt-oss-20b|decode": [
  "plausible",
  "vLLM per-step host work at batch 1",
  "Batch-1 decode at 15-30% of the bandwidth bound: the gap is per-step host work (AsyncLLM's engine-core IPC, scheduling, sampling, streaming) rather than kernel speed."
 ],
 "tpu-v6e-1|qwen3.6-35b-a3b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "pro6000-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "tpu-v5p-8|gemma-4-12b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi300x-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "a40-x1|gemma-4-31b|batching": [
  "real",
  "SGLang faster here",
  "SGLang beats pie on these batched-decode cells (gpt-oss-20b and MiMo on H100, a Gemma-4-31B slice on A40, GLM-5.3-Flash on RTX 4090); no harness issue found."
 ],
 "pro6000-x1|gemma-4-31b|prefill": [
  "plausible",
  "TRT-LLM host path at one request",
  "Few cells: TRT-LLM's single-request TTFT runs 5-40 ms above pie's (PyTorch-backend host path), most on the Nemotron-3 hybrid Mamba slices."
 ],
 "tpu-v5e-1|gpt-oss-120b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v5e-1|gemma-4-e2b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "h100-sxm-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "plausible",
  "TRT-LLM host path at one request",
  "Few cells: TRT-LLM's single-request TTFT runs 5-40 ms above pie's (PyTorch-backend host path), most on the Nemotron-3 hybrid Mamba slices."
 ],
 "l40s-x1|hy4-preview|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx5090|muse-glimmer-30b|decode": [
  "explained",
  "llama.cpp tab: ~20 ms floor per token",
  "llama.cpp in the tab pays a near-fixed ~20 ms per token on any model or GPU (4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): a host round trip per step plus single-thread wasm sampling over the full vocab."
 ],
 "mi300x-x1|qwen3.8-27b|prefill": [
  "real",
  "Rival faster on this AMD cell",
  "The rival is faster than pie on these AMD cells; no harness issue found."
 ],
 "a100-pcie-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a100-sxm-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "tpu-v6e-1|gemma-4-31b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "pro4500-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "vLLM: MiniMax MSA on Triton",
  "MiniMax-M3's sparse attention (MSA) runs on vLLM's Triton path below sm_100, and the MXFP8 weights need fallbacks on these cards."
 ],
 "pro4500-x1|kimi-k3|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "a40-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "h200-x4|glm-5.3-flash|prefill": [
  "real",
  "pie's 4-GPU TP prefill trails",
  "pie's 4-GPU tensor-parallel single prefill trails SGLang (TTFT 37-110 ms vs 19-58 ms). These rows date from Oct 18-22."
 ],
 "a100-sxm-x1|glm-5.3|prefill": [
  "explained",
  "vLLM: portable sparse MLA, eager",
  "On sm_8x vLLM 0.32 serves GLM-5.3's sparse MLA with XPU_MLA_SPARSE, a portable backend with no full CUDA graph support: the A100 runs the whole model eager, the A40 piecewise."
 ],
 "rtx4090-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "l40s-x1|minimax-m3.1-flash|pbatch": [
  "plausible",
  "SGLang reads cold prompts slower",
  "SGLang reads the 256 cold prompts 25-120% slower than pie (TTFT p50 2.5-3.5x pie's) on these Blackwell and Ada cells; no hobbling setting found, so this reads as kernel and scheduling speed."
 ],
 "h200-x1|gemma-4-26b-a4b|decode": [
  "plausible",
  "SGLang streams tokens via ZMQ",
  "Batch-1 steps of 1-2 ms where host work dominates: SGLang streams every token through a separate detokenizer process over ZMQ, which pie does not."
 ],
 "pro4500-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "pro6000-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 MoE is faster",
  "TensorRT-LLM 1.4's fused MXFP4 MoE kernels beat pie's W4A16 experts at batch on Blackwell RTX/PRO and H100 (25-37% faster)."
 ],
 "b200-x1|qwen3.6-27b|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ]
};
