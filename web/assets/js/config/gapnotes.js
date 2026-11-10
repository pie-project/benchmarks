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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "web-rtx4090|gemma-4-e4b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "web-rtx5090|gemma-4-e2b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "web-rtx4090|qwen3.5-4b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "web-rtx4090|muse-glimmer-30b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran single-threaded",
  "Our browser build of llama.cpp ran on one CPU thread (no pthreads, n_threads 1), and llama.cpp keeps some work on the CPU, e.g. Gemma-4's per-layer embeddings. Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; rerun 42897252344."
 ],
 "m3-16g|qwen3.8-27b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
 ],
 "m5-max-128g|gemma-4-e4b|batching": [
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
 ],
 "web-rtx5090|gemma-4-12b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "b200-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "SGLang adds per-request IPC",
  "Single prefill is 555 tokens over client TTFT, far below the compute bound. SGLang's TTFT runs 2-85 ms (median 12) above pie's: each request crosses its tokenizer, scheduler and detokenizer processes."
 ],
 "web-rtx4090|muse-glimmer-30b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "mi300x-x1|gpt-oss-20b|pbatch": [
  "plausible",
  "Rivals on generic ROCm Triton paths",
  "On ROCm the rivals serve these MoE, MLA and sparse-attention slices through generic Triton paths (vLLM 0.32.0 on MI300X, SGLang 0.5.22), and seat fewer requests at once."
 ],
 "web-rtx4090|gemma-4-31b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
 ],
 "m4-pro-48g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m3-16g|qwen3.5-9b|pbatch": [
  "rerun",
  "Noisy run: rounds disagree",
  "mlx-lm's repeat rounds differ by more than the 2% noise bar, so the number is not stable. Rerun before reading this gap."
 ],
 "m5-max-128g|qwen3.8-27b|batching": [
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
 ],
 "web-rtx4090|gpt-oss-120b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "web-rtx4090|qwen3.5-4b|decode": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx5090|muse-glimmer-30b|batching": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "l40s-x1|glm-5.3|batching": [
  "explained",
  "SGLang: DSA on fallback kernels",
  "Below sm_90 and on sm_120 the harness's SGLang runs GLM-5.3's DSA sparse MLA, indexer logits and top-k through Triton, TileLang and torch fallbacks instead of FlashMLA and DeepGEMM."
 ],
 "m5-max-128g|gemma-4-26b-a4b|batching": [
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
 ],
 "m4-pro-48g|qwen3.6-27b|prefill": [
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "web-rtx4090|gemma-4-26b-a4b|decode": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "m4-pro-48g|qwen3.5-9b|prefill": [
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
 ],
 "web-rtx4090|qwen3.6-27b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp Q4_K decode scales poorly",
  "llama-server batches the 32 slots, but its Metal Q4_K decode scales poorly with batch: per-request decode is 2-24 tok/s vs pie's 10-68 on the same Macs."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "m3-16g|gemma-4-12b|prefill": [
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "real",
  "llama.cpp faster on this Muse slice",
  "pie decodes this Muse-Spark slice slower than llama.cpp on the 16 GB M2 (22 vs 38 tok/s); cause not known."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "mi350x-x1|gpt-oss-20b|prefill": [
  "real",
  "Rivals use AITER MXFP4 kernels",
  "On gfx950 the rivals use AITER's MXFP4 MoE kernels (vLLM rows are AMD's 0.29.1 image), while pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "web-rtx5090|qwen3.8-27b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m5-max-64g|muse-glimmer-30b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
 ],
 "pro4500-x1|glm-5.3-flash|prefill": [
  "plausible",
  "vLLM prefill runs ungraphed",
  "Single prefill is 555 tokens over client TTFT. With max_num_seqs=1 vLLM graphs at most 2 tokens, so the prompt runs ungraphed; its TTFT sits 2-25 ms (median 12) above pie's, well below the compute bound."
 ],
 "m5-max-64g|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "pie's 4-bit Metal matmuls run nearer peak",
  "The gap scales with prompt compute (E2B on M5 Max 26 vs 34 ms, 12B on M2 4.9 vs 6.7 s): pie's 4-bit Metal matmuls run nearer the compute bound (median 47%) than mlx-lm's quantized matmul."
 ],
 "l40s-x1|gpt-oss-120b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "web-rtx4090|gpt-oss-20b|decode": [
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
 ],
 "h200-x1|qwen3.5-0.8b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
 ],
 "m5-max-64g|qwen3.8-27b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Row is mlx-vlm on a 2-bit checkpoint",
  "mlx-lm 0.32.2 has no qwen4_exp model, so this row is mlx-vlm 0.7.11's server on a 2-bit checkpoint; its decode runs 1.3-4x slower per request than pie's."
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
  "plausible",
  "pie's fused MoE decode does less work",
  "Batch-1 MoE decode on the M5 Max (166 vs 130 tok/s, pie at 47% of the bandwidth bound): pie's fused MoE decode path does less per-token work than mlx-lm's gather_qmm path."
 ],
 "m5-max-64g|qwen3.8-flash-next|decode": [
  "plausible",
  "Row is mlx-vlm on a 2-bit checkpoint",
  "mlx-lm 0.32.2 has no qwen4_exp model, so this row is mlx-vlm 0.7.11's server on a 2-bit checkpoint; its decode runs 1.3-4x slower per request than pie's."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "pie's fused MoE decode does less work",
  "Batch-1 MoE decode on the M5 Max (166 vs 130 tok/s, pie at 47% of the bandwidth bound): pie's fused MoE decode path does less per-token work than mlx-lm's gather_qmm path."
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
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been traced yet; it is being profiled on the hardware."
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
  "plausible",
  "llama.cpp WebGPU lacks fused kernels",
  "llama.cpp's WebGPU backend lacks the fused, tuned kernels its CUDA and Metal backends have, so the same Q4_K_M GGUF runs 1.3-4x slower in the tab than pie's WebGPU runtime."
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
