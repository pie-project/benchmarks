window.Pie = window.Pie || {};
// Engine Gaps conclusions by "hardware|model|setup" as [conclusion, short note, detail on hover]: a quick smoke
// classification of every cell where pie and the strongest other engine are 25% or more apart (2026-11-10).
// explained: a known cause; plausible: inside the hardware limit, cause not traced; rerun: the numbers look wrong;
// real: pie is slower. A slice keeps the full model's layer shapes, so its gap is classified like any other.
Pie.gapNotes = {
 "web-rtx5090|gemma-4-e4b|prefill": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx4090|gemma-4-e4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx5090|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "h200-x1|glm-5.3|pbatch": [
  "rerun",
  "Old pie row was 15x too high",
  "Bad old run. Rerun on an H200, pie reads 108k prompt tok/s, not 1.6M; SGLang reads 89k on the same machine, so pie leads by 22%."
 ],
 "m5-max-128g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|decode": [
  "rerun",
  "vLLM decodes MiMo at 6 tok/s",
  "vLLM 0.32.0 decodes this MiMo slice at 6 tok/s on MI300X (pie 94; SGLang 160 on MI350X), likely a slow fallback kernel. Not confirmed."
 ],
 "m5-max-64g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "m3-16g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "m4-pro-48g|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "tpu-v5e-1|deepseek-v4-flash|decode": [
  "explained",
  "vLLM-TPU has no SparseCore on v5e",
  "The v5e has no SparseCore, so vLLM-TPU runs DeepSeek-V4's sparse-attention lookup as a plain gather and its compressor with slow reference code."
 ],
 "m5-max-128g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-e2b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "web-rtx5090|gemma-4-e2b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-sxm-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "web-rtx4090|gemma-4-e4b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "tpu-v6e-1|deepseek-v4-flash|decode": [
  "explained",
  "vLLM-TPU copies its RoPE table every token",
  "vLLM-TPU copies DeepSeek-V4's 256 MiB position table 15 times per token just to change its layout: 9.5 of its 12.2 ms per token. Without the copies it would take 3.4 ms; pie takes 2.6."
 ],
 "a100-sxm-x1|glm-5.3-flash|decode": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "tpu-v6e-1|glm-5.3|prefill": [
  "explained",
  "sglang-jax's FP8 matmul is slow",
  "sglang-jax runs GLM-5.3's FP8 weights through a matmul at only 8-14% of the chip's peak (27 TFLOP/s on v5e, 71 on v6e) and pads the 546-token prompt to 1024. That matmul is 62-70% of its prefill."
 ],
 "tpu-v5e-1|glm-5.3|prefill": [
  "explained",
  "sglang-jax's FP8 matmul is slow",
  "sglang-jax runs GLM-5.3's FP8 weights through a matmul at only 8-14% of the chip's peak (27 TFLOP/s on v5e, 71 on v6e) and pads the 546-token prompt to 1024. That matmul is 62-70% of its prefill."
 ],
 "a100-pcie-x1|glm-5.3-flash|decode": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "web-rtx5090|gemma-4-e4b|decode": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "l40s-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "b200-x1|gemma-4-e4b|prefill": [
  "explained",
  "SGLang runs Gemma-4 prefill without graphs",
  "Gemma-4 is not on SGLang's list of models with prefill graphs, so SGLang 0.5.22 launches its prefill kernels one by one: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "l40s-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "m3-16g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-26b-a4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|batching": [
  "rerun",
  "vLLM decodes MiMo at 6 tok/s",
  "vLLM 0.32.0 decodes this MiMo slice at 6 tok/s on MI300X (pie 94; SGLang 160 on MI350X), likely a slow fallback kernel. Not confirmed."
 ],
 "m2-16g|qwen3.8-flash-next|batching": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "web-rtx4090|gemma-4-12b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "rtx4090-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "a100-sxm-x1|glm-5.3|decode": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "web-rtx4090|gemma-4-31b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang runs Gemma-4 prefill without graphs",
  "Gemma-4 is not on SGLang's list of models with prefill graphs, so SGLang 0.5.22 launches its prefill kernels one by one: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "b200-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "web-rtx5090|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "mi355x-x1|deepseek-v4.1-flash|prefill": [
  "rerun",
  "Bad SGLang run",
  "SGLang's TTFT here (174 ms) is 7x its own MI350X figure (23 ms) for the same model, so this SGLang run looks bad."
 ],
 "web-rtx4090|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|muse-glimmer-30b|prefill": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "rtx5090-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx5090|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "plausible",
  "SGLang launches attention outside its graph",
  "Not traced on this GPU. On H200 the cause was SGLang launching attention outside its prefill graph. Here its TTFT is 2-85 ms above pie's."
 ],
 "web-rtx4090|gemma-4-12b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "mi355x-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "mi300x-x1|deepseek-v4-flash|batching": [
  "plausible",
  "vLLM uses fallback kernels on AMD",
  "AMD has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse attention on Triton fallbacks; its decode is half pie's speed."
 ],
 "a40-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "web-rtx5090|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|muse-glimmer-30b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m3-16g|qwen3.8-27b|pbatch": [
  "explained",
  "Pie also uses the Neural Engine",
  "Pie runs 47% of the prefill matmuls on the Neural Engine as well as the GPU; the other engine uses the GPU only. Measured cold, pie prefills this model 1.7x faster (240 vs 141-145 tok/s); the site's 2.5-3.1x also includes the MacBook Air throttling."
 ],
 "mi300x-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "web-rtx4090|qwen3.5-9b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "a40-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "mi300x-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "mi300x-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "web-rtx4090|qwen3.8-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m5-max-64g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx5090|gemma-4-26b-a4b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m5-max-64g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Every decode step vllm-metal copies each request's Mamba-2 state (8.4 MB per layer) out of its pool and back. On M3 a Mamba layer takes 30.4 ms in vllm-metal vs 16.2 in mlx-lm, and a step 200 vs 147 ms."
 ],
 "mi300x-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "web-rtx4090|gpt-oss-120b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gpt-oss-120b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m4-pro-48g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx4090|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m5-max-128g|gemma-4-e2b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp uses a slower matmul, so a step costs 2.5x a 16-request step (M5 Max 12.9 to 31.9 ms); with more than one slot it also stops skipping Gemma's shared-KV layers on prompts (3734 to 1358 tok/s)."
 ],
 "web-rtx4090|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m3-16g|qwen3.8-27b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m5-max-128g|qwen3.5-4b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "m5-max-128g|gemma-4-e4b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp uses a slower matmul, so a step costs 2.5x a 16-request step (M5 Max 12.9 to 31.9 ms); with more than one slot it also stops skipping Gemma's shared-KV layers on prompts (3734 to 1358 tok/s)."
 ],
 "mi350x-x1|qwen3.5-0.8b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "m5-max-128g|qwen3.8-flash-next|batching": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Without a seed mlx-lm is 4.7x faster (Qwen3.5-4B, M5 Max: 138 to 600-653 tok/s). Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx4090|gpt-oss-20b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx4090|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m3-16g|qwen3.6-27b|batching": [
  "rerun",
  "The MacBook Air throttled llama.cpp's run",
  "llama.cpp's c8 run lasts about 160 s, past the ~95 s after which the fanless Air slows down; pie's ~60 s run stays cool."
 ],
 "web-rtx5090|gemma-4-12b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "b200-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx4090|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "h200-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "tpu-v5e-1|glm-5.3|pbatch": [
  "plausible",
  "sglang-jax TTFT 6x pie's",
  "Not traced. sglang-jax is an early TPU port (0.1.0rc0); its TTFT on this cell is 6x pie's."
 ],
 "h100-pcie-x1|gemma-4-e4b|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "h200-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "tpu-v5e-1|deepseek-v4-flash|prefill": [
  "explained",
  "vLLM-TPU has no SparseCore on v5e",
  "The v5e has no SparseCore, so vLLM-TPU runs DeepSeek-V4's sparse-attention lookup as a plain gather and its compressor with slow reference code."
 ],
 "web-rtx5090|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx4090|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "mi350x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "a100-sxm-x1|glm-5.3|batching": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "web-rtx5090|gemma-4-12b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m5-max-128g|qwen3.5-9b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "h100-sxm-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "SGLang launches attention outside its graph",
  "Not traced on this GPU. On H200 the cause was SGLang launching attention outside its prefill graph. Here its TTFT is 2-85 ms above pie's."
 ],
 "b200-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx4090|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "mi300x-x1|gpt-oss-20b|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "web-rtx4090|gemma-4-31b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "m3-16g|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "mi355x-x1|qwen3-0.6b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "h100-sxm-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "mi300x-x1|qwen3-0.6b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi300x-x1|gemma-4-26b-a4b|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "mi355x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "tpu-v5e-1|gpt-oss-20b|decode": [
  "explained",
  "vLLM-TPU's MoE kernel and table copy",
  "Each token vLLM-TPU spends 4.5 ms in its int8 expert matmul and 2.1 ms copying the whole 1.16 GB embedding table into a new layout (v5e: 4.5 and 3.6 of 11 ms). Pie's whole token takes 4.7 ms on v6e."
 ],
 "m3-16g|qwen3.8-27b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "Pie runs 47% of the prefill matmuls on the Neural Engine as well as the GPU; the other engine uses the GPU only. Measured cold, pie prefills this model 1.7x faster (240 vs 141-145 tok/s); the site's 2.5-3.1x also includes the MacBook Air throttling."
 ],
 "tpu-v5e-1|gpt-oss-120b|decode": [
  "explained",
  "vLLM-TPU's MoE kernel and table copy",
  "Each token vLLM-TPU spends 4.5 ms in its int8 expert matmul and 2.1 ms copying the whole 1.16 GB embedding table into a new layout (v5e: 4.5 and 3.6 of 11 ms). Pie's whole token takes 4.7 ms on v6e."
 ],
 "mi300x-x1|deepseek-v4.1-flash|batching": [
  "plausible",
  "vLLM uses fallback kernels on AMD",
  "AMD has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse attention on Triton fallbacks; its decode is half pie's speed."
 ],
 "mi350x-x1|qwen3-0.6b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "b200-x1|qwen3.8-flash-next|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "tpu-v5e-1|gpt-oss-20b|batching": [
  "explained",
  "vLLM-TPU fits only ~50 of 256 requests",
  "vLLM-TPU stores gpt-oss's experts as int8 (13.03 GiB vs the 7.49 GiB checkpoint), which leaves room for only 15,018 cached tokens, so about 50 of the 256 requests run at once."
 ],
 "tpu-v5e-1|gpt-oss-120b|batching": [
  "explained",
  "vLLM-TPU fits only ~50 of 256 requests",
  "vLLM-TPU stores gpt-oss's experts as int8 (13.03 GiB vs the 7.49 GiB checkpoint), which leaves room for only 15,018 cached tokens, so about 50 of the 256 requests run at once."
 ],
 "mi300x-x1|deepseek-v4.1-flash|decode": [
  "plausible",
  "vLLM uses fallback kernels on AMD",
  "AMD has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse attention on Triton fallbacks; its decode is half pie's speed."
 ],
 "tpu-v5e-1|glm-5.3|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m5-max-128g|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "m4-pro-48g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Every decode step vllm-metal copies each request's Mamba-2 state (8.4 MB per layer) out of its pool and back. On M3 a Mamba layer takes 30.4 ms in vllm-metal vs 16.2 in mlx-lm, and a step 200 vs 147 ms."
 ],
 "web-rtx4090|gemma-4-e2b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "pro4500-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|pbatch": [
  "real",
  "llama.cpp's MoE prefill is slow",
  "llama.cpp's MoE prefill gives each expert only about 16 tokens per 512-token batch: 820 tok/s on M4 Pro vs pie's 1171. Its server matches its own kernel benchmark, so this is llama.cpp's kernel speed."
 ],
 "m3-16g|qwen3.5-9b|pbatch": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m5-max-128g|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "web-rtx4090|gpt-oss-120b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx4090|qwen3.5-4b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "m2-16g|qwen3.6-27b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h100-sxm-x1|gemma-4-e4b|prefill": [
  "explained",
  "SGLang runs Gemma-4 prefill without graphs",
  "Gemma-4 is not on SGLang's list of models with prefill graphs, so SGLang 0.5.22 launches its prefill kernels one by one: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "mi355x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "m5-max-128g|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "tpu-v5e-1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM-TPU has no SparseCore on v5e",
  "The v5e has no SparseCore, so vLLM-TPU runs DeepSeek-V4's sparse-attention lookup as a plain gather and its compressor with slow reference code."
 ],
 "m2-16g|qwen3.6-35b-a3b|decode": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m2-16g|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx4090|gpt-oss-20b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "rtx4090-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "mi350x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "web-rtx5090|gemma-4-26b-a4b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "web-rtx5090|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "web-rtx5090|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m5-max-128g|gemma-4-12b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "h200-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "pro6000-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx5090|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "m3-16g|qwen3.5-9b|batching": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx5090|gemma-4-e2b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "web-rtx5090|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx5090|gpt-oss-120b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "web-rtx5090|gpt-oss-120b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "h200-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "mi300x-x1|deepseek-v4-flash|decode": [
  "plausible",
  "vLLM uses fallback kernels on AMD",
  "AMD has no FlashMLA or DeepGEMM, so vLLM runs DeepSeek-V4's sparse attention on Triton fallbacks; its decode is half pie's speed."
 ],
 "l4-x1|deepseek-v4-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "web-rtx5090|muse-glimmer-30b|prefill": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|gpt-oss-20b|prefill": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|qwen3.8-27b|decode": [
  "explained",
  "The MacBook Air throttles llama.cpp's run",
  "The fanless MacBook Air slows down after about 95 s of load. llama.cpp's longer run crosses that point, so its median is the throttled 7.1 tok/s. Measured cold: pie 15.0, llama.cpp 13.5 tok/s."
 ],
 "m3-16g|qwen3.6-35b-a3b|batching": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi350x-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "a100-x2|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "rtx4090-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "h100-sxm-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m3-16g|gemma-4-31b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m2-16g|gpt-oss-120b|decode": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx4090|qwen3.5-4b|prefill": [
  "rerun",
  "Noisy run",
  "WebLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi355x-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "a100-sxm-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|glm-5.3|prefill": [
  "plausible",
  "SGLang uses a PyTorch top-k for GLM-5.3",
  "On B200 SGLang falls back to a PyTorch top-k for GLM-5.3's sparse attention, because these cut-down models do not select 2048 tokens."
 ],
 "rtx5090-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "m2-16g|qwen3.8-27b|pbatch": [
  "explained",
  "Pie also uses the Neural Engine",
  "Pie runs 47% of the prefill matmuls on the Neural Engine as well as the GPU; the other engine uses the GPU only. Measured cold, pie prefills this model 1.7x faster (240 vs 141-145 tok/s); the site's 2.5-3.1x also includes the MacBook Air throttling."
 ],
 "mi300x-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "a40-x1|glm-5.3-flash|decode": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx5090|qwen3.6-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|mimo-v2.6-flash-rl|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "web-rtx5090|qwen3.5-9b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "web-rtx5090|qwen3.8-27b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|batching": [
  "explained",
  "llama.cpp runs experts one token at a time",
  "Below 32 tokens llama.cpp's Metal backend runs the experts once per token, so a step grows with the batch (Qwen3.6-35B-A3B, M4 Pro: 18 ms at 1, 213 ms at 31). Its UD GGUF also reads 1.55x pie's bytes per token."
 ],
 "web-rtx5090|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "l40s-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "tpu-v6e-1|qwen3.5-0.8b|decode": [
  "explained",
  "vLLM-TPU's chip waits on Python",
  "vLLM-TPU prepares every token in Python (7 input copies, 7 program launches) in 2.0-3.0 ms, longer than the chip's 1.2-1.5 ms of work on v6e (2.3-2.6 on v5e), so the chip sits idle 0.8-1.8 ms every token."
 ],
 "rtx5090-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Every decode step vllm-metal copies each request's Mamba-2 state (8.4 MB per layer) out of its pool and back. On M3 a Mamba layer takes 30.4 ms in vllm-metal vs 16.2 in mlx-lm, and a step 200 vs 147 ms."
 ],
 "b200-x1|glm-5.3-flash|prefill": [
  "plausible",
  "SGLang uses a PyTorch top-k for GLM-5.3",
  "On B200 SGLang falls back to a PyTorch top-k for GLM-5.3's sparse attention, because these cut-down models do not select 2048 tokens."
 ],
 "mi300x-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "web-rtx5090|muse-glimmer-30b|pbatch": [
  "rerun",
  "Harness bug: llama.cpp ran on one thread",
  "Our browser build of llama.cpp ran on one CPU thread, and llama.cpp keeps some work on the CPU (e.g. Gemma-4's per-layer embeddings). Threaded it is 3.6x faster on TTFT. Fixed in benchmarks #1678; this row predates the fix."
 ],
 "b200-x1|deepseek-v4-flash|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "tpu-v6e-1|gpt-oss-20b|decode": [
  "explained",
  "vLLM-TPU's MoE kernel and table copy",
  "Each token vLLM-TPU spends 4.5 ms in its int8 expert matmul and 2.1 ms copying the whole 1.16 GB embedding table into a new layout (v5e: 4.5 and 3.6 of 11 ms). Pie's whole token takes 4.7 ms on v6e."
 ],
 "tpu-v6e-1|gpt-oss-120b|decode": [
  "explained",
  "vLLM-TPU's MoE kernel and table copy",
  "Each token vLLM-TPU spends 4.5 ms in its int8 expert matmul and 2.1 ms copying the whole 1.16 GB embedding table into a new layout (v5e: 4.5 and 3.6 of 11 ms). Pie's whole token takes 4.7 ms on v6e."
 ],
 "a40-x1|glm-5.3|pbatch": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "mi355x-x1|qwen3.5-9b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "mi300x-x1|glm-5.3|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "web-rtx5090|qwen3.5-4b|pbatch": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m5-max-128g|gemma-4-31b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "rtx5090-x1|glm-5.3|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "m2-16g|qwen3.6-27b|pbatch": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|qwen3.6-35b-a3b|decode": [
  "explained",
  "llama.cpp's GGUF reads 1.55x more bytes",
  "The unsloth UD-Q4_K_M GGUF keeps attention and SSM layers at 8 bits: 2.56 GB read per token vs pie's 1.65 GB. Requantized to 4 bits llama.cpp goes from 24.5 to 36.3 tok/s; pie runs 44.8."
 ],
 "tpu-v5p-8|qwen3.5-0.8b|decode": [
  "explained",
  "vLLM-TPU's chip waits on Python",
  "vLLM-TPU prepares every token in Python (7 input copies, 7 program launches) in 2.0-3.0 ms, longer than the chip's 1.2-1.5 ms of work on v6e (2.3-2.6 on v5e), so the chip sits idle 0.8-1.8 ms every token."
 ],
 "mi350x-x1|qwen3.5-9b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "mi300x-x1|gpt-oss-120b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "tpu-v5e-1|glm-5.3|decode": [
  "explained",
  "sglang-jax reads weights at 14% bandwidth",
  "sglang-jax's FP8 matmul reads GLM-5.3's weights at 116 GB/s, 14% of the v5e's memory bandwidth: 16.0 of its 20.9 ms step. Pie's token takes 11.3 ms."
 ],
 "h200-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "rtx5090-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "b200-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "l40s-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "web-rtx4090|qwen3.5-9b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "web-rtx5090|qwen3.8-27b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi300x-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "mi350x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "h100-pcie-x1|qwen3-0.6b|prefill": [
  "rerun",
  "Noisy run",
  "SGLang's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "rtx5090-x1|glm-5.3|batching": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "mi355x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "m2-16g|qwen3.5-9b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi350x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "mi355x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "mi300x-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "mi300x-x1|minimax-m3.1-flash|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "web-rtx4090|qwen3.5-9b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "tpu-v5e-1|gpt-oss-20b|prefill": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "h100-sxm-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "h100-sxm-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "plausible",
  "TRT-LLM's TTFT 5-40 ms above pie's",
  "Not traced. TRT-LLM's single-request TTFT is 5-40 ms above pie's, mostly on the Nemotron-3 hybrid Mamba models."
 ],
 "pro4500-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "m3-16g|qwen3.6-35b-a3b|pbatch": [
  "explained",
  "The MacBook Air throttled llama.cpp's run",
  "llama.cpp's site run followed hot rounds and slowed as the fanless Air throttled. Measured cold it reaches 386 tok/s, not 268; pie's 476 is still 1.23x faster."
 ],
 "web-rtx5090|muse-glimmer-30b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "l40s-x1|glm-5.3|batching": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "m5-max-128g|gemma-4-26b-a4b|batching": [
  "explained",
  "llama.cpp runs experts one token at a time",
  "Below 32 tokens llama.cpp's Metal backend runs the experts once per token, so a step grows with the batch (Qwen3.6-35B-A3B, M4 Pro: 18 ms at 1, 213 ms at 31). Its UD GGUF also reads 1.55x pie's bytes per token."
 ],
 "tpu-v5e-1|gpt-oss-120b|prefill": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "b200-x1|muse-spark-open-816b-a42b|batching": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|qwen3-0.6b|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "rtx5090-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx4090-x1|glm-5.3|batching": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "mi350x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "pro4500-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "tpu-v6e-1|deepseek-v4-flash|prefill": [
  "explained",
  "vLLM-TPU copies its RoPE table every step",
  "vLLM-TPU copies DeepSeek-V4's 256 MiB position table 15 times per step just to change its layout: 9.3 of its 29 ms prefill."
 ],
 "web-rtx5090|gemma-4-31b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "pro4500-x1|glm-5.3|batching": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|decode": [
  "explained",
  "vLLM-TPU's chip waits on Python",
  "vLLM-TPU prepares every token in Python (7 input copies, 7 program launches) in 2.0-3.0 ms, longer than the chip's 1.2-1.5 ms of work on v6e (2.3-2.6 on v5e), so the chip sits idle 0.8-1.8 ms every token."
 ],
 "pro4500-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "mi355x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "tpu-v6e-1|glm-5.3|pbatch": [
  "explained",
  "sglang-jax's FP8 matmul is slow",
  "sglang-jax's batched prefill uses the same slow FP8 matmul: its 19.1k tok/s works out to 69 TFLOP/s, 8% of the v6e's peak."
 ],
 "a100-sxm-x1|glm-5.3|pbatch": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "h100-sxm-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang runs Gemma-4 prefill without graphs",
  "Gemma-4 is not on SGLang's list of models with prefill graphs, so SGLang 0.5.22 launches its prefill kernels one by one: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "pro6000-x1|glm-5.3|batching": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "pro6000-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "pro4500-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "tpu-v5p-8|qwen3.5-0.8b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m3-16g|gpt-oss-120b|batching": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v5e-1|qwen3-0.6b|decode": [
  "explained",
  "vLLM-TPU's chip waits on Python",
  "vLLM-TPU prepares every token in Python (7 input copies, 7 program launches) in 2.0-3.0 ms, longer than the chip's 1.2-1.5 ms of work on v6e (2.3-2.6 on v5e), so the chip sits idle 0.8-1.8 ms every token."
 ],
 "m2-16g|muse-glimmer-30b|decode": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m4-pro-48g|qwen3.8-27b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "m4-pro-48g|qwen3.6-27b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "l40s-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "b200-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "mi350x-x1|deepseek-v4.1-flash|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "tpu-v6e-1|gemma-4-26b-a4b|decode": [
  "explained",
  "vLLM-TPU pads one token to 16 rows",
  "vLLM-TPU runs gemma-4-26B-A4B's experts in bf16 and pads the single token to 16 rows: 7.9 of 12.5 ms per token on v6e, 4.9 of 9.1 on v5e. Pie's whole token takes 7.4 and 5.7 ms."
 ],
 "mi300x-x1|qwen3.6-35b-a3b|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "m2-16g|qwen3.8-flash-next|prefill": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "a40-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "b200-x1|muse-glimmer-30b|prefill": [
  "plausible",
  "SGLang launches attention outside its graph",
  "Not traced on this GPU. On H200 the cause was SGLang launching attention outside its prefill graph. Here its TTFT is 2-85 ms above pie's."
 ],
 "m5-max-128g|muse-glimmer-30b|prefill": [
  "rerun",
  "Old rows from Oct 20-21",
  "Both numbers are from Oct 20-21 (pie 903, llama.cpp 541 tok/s). On the M3 the same model's cold prefill is level (pie 160, llama.cpp 154)."
 ],
 "mi300x-x1|kimi-k3|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx4090-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "a100-sxm-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "rtx5090-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "tpu-v6e-1|qwen3-0.6b|decode": [
  "explained",
  "vLLM-TPU's chip waits on Python",
  "vLLM-TPU prepares every token in Python (7 input copies, 7 program launches) in 2.0-3.0 ms, longer than the chip's 1.2-1.5 ms of work on v6e (2.3-2.6 on v5e), so the chip sits idle 0.8-1.8 ms every token."
 ],
 "mi300x-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "pro4500-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "tpu-v6e-1|glm-5.3|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "b200-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|gpt-oss-120b|pbatch": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "m2-16g|muse-glimmer-30b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "rtx4090-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "h100-sxm-x4|gpt-oss-120b|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "a40-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "vLLM uses fallback kernels for MiniMax",
  "On these GPUs vLLM runs MiniMax-M3's sparse attention on Triton, and its MXFP8 weights need fallback kernels."
 ],
 "b200-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "mi355x-x1|nvidia-nemotron-3-super-120b-a12b|pbatch": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "m3-16g|qwen3.6-27b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "vllm-metal prefills like mlx-lm, with 96% of the time in GPU matmuls at 2.76 TFLOPS (M3, Qwen3.5-9B). On M1-M4 pie also runs part of its prefill matmuls on the Neural Engine in int8."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "web-rtx4090|gemma-4-26b-a4b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "m4-pro-48g|qwen3.5-9b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "web-rtx4090|qwen3.6-27b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "tpu-v5e-1|gemma-4-26b-a4b|decode": [
  "explained",
  "vLLM-TPU pads one token to 16 rows",
  "vLLM-TPU runs gemma-4-26B-A4B's experts in bf16 and pads the single token to 16 rows: 7.9 of 12.5 ms per token on v6e, 4.9 of 9.1 on v5e. Pie's whole token takes 7.4 and 5.7 ms."
 ],
 "m5-max-128g|gemma-4-e2b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx4090|qwen3.8-27b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "m3-16g|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "m2-16g|qwen3.6-35b-a3b|prefill": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|qwen3.5-9b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "tpu-v5e-1|qwen3-0.6b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "m2-16g|gemma-4-12b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|qwen3-0.6b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a40-x1|glm-5.3|batching": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "pro6000-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "tpu-v5e-1|gemma-4-12b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "pro4500-x1|glm-5.3|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "pro6000-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "mi300x-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "h200-x1|deepseek-v4-flash|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "mi300x-x1|gpt-oss-20b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "mi300x-x1|muse-spark-open-816b-a42b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m4-pro-48g|qwen3.6-27b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "m2-16g|gemma-4-26b-a4b|decode": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v5p-8|qwen3-0.6b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h100-sxm-x4|qwen3.6-27b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "pro4500-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "rtx4090-x1|glm-5.3-flash|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "a100-sxm-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "mi355x-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "m5-max-64g|gemma-4-26b-a4b|batching": [
  "explained",
  "MLX reads 117 of 128 experts per step",
  "At 32 requests the 30 MoE layers touch 117 of 128 experts per step (32.8 ms), and MLX's split matmul skips the M5's neural accelerators on the dense layers (11.1 vs 5.7 ms). Step 55.2 ms vs pie's 35.8."
 ],
 "rtx4090-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "pro6000-x4|glm-5.3-flash|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "m2-16g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "mi355x-x1|gpt-oss-120b|batching": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "b200-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "tpu-v5e-1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "web-rtx5090|qwen3.5-9b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "b200-x1|hy4-preview|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|gemma-4-31b|prefill": [
  "explained",
  "SGLang runs Gemma-4 prefill without graphs",
  "Gemma-4 is not on SGLang's list of models with prefill graphs, so SGLang 0.5.22 launches its prefill kernels one by one: TTFT 42-70 ms vs pie's 15-28 ms."
 ],
 "web-rtx5090|qwen3.6-27b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "h100-sxm-x1|kimi-k3|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "l40s-x1|glm-5.3|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "h100-sxm-x4|gpt-oss-20b|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "m4-pro-48g|qwen3.8-27b|batching": [
  "explained",
  "llama.cpp slows down above 16 requests",
  "With 17-32 requests llama.cpp's Metal backend switches to a slower general matmul, so a step costs 1.5-2.5x a 16-request step and 32 requests run no faster than 16 (Qwen3.5-4B, M4 Pro: 62.8 ms at 16, 122.6 ms at 32)."
 ],
 "tpu-v5p-8|qwen3.6-27b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx5090-x1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "b200-x1|qwen3-0.6b|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "web-rtx5090|gpt-oss-20b|batching": [
  "explained",
  "llama.cpp web slows down at 32 requests",
  "With 32 requests, llama.cpp's browser build takes 250-400 ms per decode step vs 23 ms with 1 (Gemma-4-12B, RTX 4090). Above 4 rows it switches from its fast kernel to a slow general matmul, then samples all 32 on one CPU thread."
 ],
 "m3-16g|gemma-4-12b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "mi300x-x1|glm-5.3-flash|pbatch": [
  "real",
  "Rival faster on this AMD cell",
  "Not traced. The rival is faster than pie here; no harness issue found."
 ],
 "m2-16g|qwen3.5-4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "tpu-v6e-1|muse-glimmer-30b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "web-rtx5090|qwen3.5-4b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "h200-x4|qwen3.8-flash-next|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "mi355x-x1|nvidia-nemotron-3-ultra-550b-a55b|pbatch": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "l40s-x1|glm-5.3|pbatch": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "pro6000-x1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a40-x1|glm-5.3|prefill": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|qwen3.5-4b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "mi355x-x1|gpt-oss-20b|pbatch": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "tpu-v5e-1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "mi300x-x1|glm-5.3-flash|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "pro6000-x4|gpt-oss-120b|decode": [
  "explained",
  "vLLM's MXFP4 expert kernel is slow",
  "vLLM's GPU is busy 2.88 of each 3.07 ms token (H200, gpt-oss-20b); its MXFP4 expert matmul alone takes 1.20 ms, reading at about 1 TB/s of the 4.8 available. Pie's whole token takes 2.28 ms."
 ],
 "tpu-v6e-1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "h200-x1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "mi355x-x1|gpt-oss-20b|batching": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "b200-x1|glm-5.3-flash|decode": [
  "plausible",
  "SGLang uses a PyTorch top-k for GLM-5.3",
  "On B200 SGLang falls back to a PyTorch top-k for GLM-5.3's sparse attention, because these cut-down models do not select 2048 tokens."
 ],
 "mi350x-x1|deepseek-v4.1-flash|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "a40-x1|minimax-m3.1-flash|pbatch": [
  "plausible",
  "vLLM uses fallback kernels for MiniMax",
  "On these GPUs vLLM runs MiniMax-M3's sparse attention on Triton, and its MXFP8 weights need fallback kernels."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|decode": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "m5-max-128g|gpt-oss-120b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi355x-x1|deepseek-v4.1-flash|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "h100-sxm-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "tpu-v6e-1|qwen3.6-35b-a3b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "m3-16g|muse-glimmer-30b|batching": [
  "rerun",
  "Noisy run",
  "llama.cpp's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v5e-1|qwen3.8-27b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "tpu-v5e-1|qwen3.6-27b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "rtx5090-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m2-16g|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "m4-pro-48g|qwen3.5-4b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "m2-16g|gemma-4-31b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "h100-sxm-x1|deepseek-v4-flash|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "tpu-v5e-1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "a100-sxm-x1|glm-5.3-flash|pbatch": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h200-x1|deepseek-v4.1-flash|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "web-rtx5090|qwen3.5-9b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "pro4500-x1|qwen3.8-27b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|qwen3.8-flash-next|pbatch": [
  "rerun",
  "Noisy run",
  "SGLang's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h100-sxm-x1|deepseek-v4-flash|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "m2-16g|qwen3.6-27b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|kimi-k3|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx5090|qwen3.5-4b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "l4-x1|deepseek-v4-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "h200-x1|deepseek-v4.1-flash|decode": [
  "plausible",
  "vLLM batch-1 decode far below the limit",
  "Not traced. vLLM's batch-1 decode here runs at 15-30% of the memory-bandwidth limit."
 ],
 "m3-16g|gemma-4-12b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "m2-16g|gemma-4-e2b|batching": [
  "real",
  "Pie faster on both phases",
  "Pie leads both phases on M2: prompts 2.3 vs 3.4 s (pie also uses the Neural Engine on M1-M4) and decode steps 97 vs 140 ms."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "b200-x1|mimo-v2.6-flash-rl|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-sxm-x1|glm-5.3-flash|batching": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "a40-x1|deepseek-v4.1-flash|prefill": [
  "plausible",
  "vLLM runs the 555-token prompt without graphs",
  "Not traced on this GPU. On H200 the cause was vLLM using CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one. Here its TTFT is 2-25 ms above pie's."
 ],
 "pro4500-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h100-sxm-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx4090-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "b200-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "l40s-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx4090-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h200-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|gpt-oss-120b|prefill": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "h200-x1|qwen3.5-0.8b|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "h100-sxm-x1|hy4-preview|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m2-16g|gemma-4-e4b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "b200-x1|deepseek-v4-flash|batching": [
  "rerun",
  "Noisy run",
  "SGLang's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m2-16g|qwen3.8-flash-next|decode": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "web-rtx5090|gpt-oss-20b|decode": [
  "rerun",
  "Noisy run",
  "llama.cpp WebGPU's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "rtx4090-x1|qwen3.5-9b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m3-16g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "pro6000-x1|glm-5.3|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "m3-16g|muse-glimmer-30b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v5p-8|qwen3-0.6b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-pcie-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m5-max-128g|gemma-4-26b-a4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "b200-x1|muse-spark-open-816b-a42b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|gpt-oss-20b|prefill": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "m2-16g|muse-spark-open-816b-a42b|decode": [
  "explained",
  "Pie's slice reads a larger output head",
  "Same cut, but pie's slice keeps the output head in bf16 (3157 MiB) where the GGUF uses Q6_K (1295 MiB): 4.08 vs 2.34 GB read per token. With a bf16 head llama.cpp gets 17-20 tok/s."
 ],
 "h200-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "h100-sxm-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m3-16g|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "explained",
  "vllm-metal copies Mamba state every step",
  "Every decode step vllm-metal copies each request's Mamba-2 state (8.4 MB per layer) out of its pool and back. On M3 a Mamba layer takes 30.4 ms in vllm-metal vs 16.2 in mlx-lm, and a step 200 vs 147 ms."
 ],
 "mi350x-x1|gpt-oss-20b|prefill": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "web-rtx5090|qwen3.8-27b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "a40-x1|minimax-m3.1-flash|batching": [
  "plausible",
  "vLLM uses fallback kernels for MiniMax",
  "On these GPUs vLLM runs MiniMax-M3's sparse attention on Triton, and its MXFP8 weights need fallback kernels."
 ],
 "a100-sxm-x1|deepseek-v4-flash|decode": [
  "explained",
  "vLLM uses fallback kernels for DeepSeek-V4",
  "FlashMLA and DeepGEMM need an H100 or newer, so on this GPU vLLM runs DeepSeek-V4's sparse attention on Triton and PyTorch fallbacks, without CUDA graphs for decode."
 ],
 "a40-x1|glm-5.3|decode": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi300x-x1|gpt-oss-20b|batching": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "pro6000-x4|gemma-4-e4b|decode": [
  "plausible",
  "vLLM batch-1 decode far below the limit",
  "Not traced. vLLM's batch-1 decode here runs at 15-30% of the memory-bandwidth limit."
 ],
 "m2-16g|gemma-4-e4b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v6e-1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "mi350x-x1|gpt-oss-120b|prefill": [
  "real",
  "Rivals use AMD's MXFP4 kernels",
  "On MI350X/MI355X the rivals use AMD's AITER MXFP4 expert kernels; pie runs MXFP4 experts on bf16 matrix cores."
 ],
 "l40s-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "m5-max-128g|gpt-oss-120b|pbatch": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h200-x1|deepseek-v4.1-flash|pbatch": [
  "real",
  "vLLM's FlashMLA prefill is faster",
  "On H100/H200 vLLM uses FlashMLA and DeepGEMM FP8 kernels and prefills 256 DeepSeek-V4.1 prompts 30-40% faster than pie."
 ],
 "a40-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h100-sxm-x1|qwen3.8-flash-next|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "a100-sxm-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h100-sxm-x1|qwen3.5-0.8b|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "pro6000-x4|qwen3.5-0.8b|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "web-rtx5090|qwen3.8-27b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "h100-pcie-x1|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "vLLM's gpt-oss MXFP4 prefill beats pie's 4-bit-weight experts on A40, A100 x2 and H100 PCIe: TTFT 52-120 ms vs pie's 70-168 ms."
 ],
 "rtx5090-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "h100-sxm-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "pro4500-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "a100-pcie-x1|qwen3.5-0.8b|prefill": [
  "rerun",
  "Noisy run",
  "SGLang's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "l4-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a40-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "mi300x-x1|qwen3.8-flash-next|batching": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "l40s-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m2-16g|gemma-4-12b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|muse-glimmer-30b|decode": [
  "explained",
  "The MacBook Air throttles llama.cpp's run",
  "The fanless MacBook Air slows down after about 95 s of load. llama.cpp's longer run crosses that point, so its median is the throttled 7.1 tok/s. Measured cold: pie 15.0, llama.cpp 13.5 tok/s."
 ],
 "pro6000-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "m3-16g|gemma-4-e2b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "web-rtx5090|qwen3.6-27b|prefill": [
  "explained",
  "WebLLM computes GDN one token at a time",
  "WebLLM runs Qwen3.5's gated delta net layers (75% of the model) as a loop over every prompt token, with the state in GPU memory. Qwen3.5-9B prefill: WebLLM 658/863 tok/s, pie 1180/1327 (RTX 4090/5090)."
 ],
 "h200-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "l4-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "mi355x-x1|deepseek-v4-flash|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "h100-sxm-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "pro4500-x1|nvidia-nemotron-3-ultra-550b-a55b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "b200-x1|glm-5.3|pbatch": [
  "rerun",
  "TRT-LLM slower here, cause unknown",
  "TensorRT-LLM 1.4's batched prefill of this GLM-5.3 model on B200 is 27% slower than pie's; no harness setting or fallback kernel found."
 ],
 "rtx5090-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "pro4500-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "tpu-v5e-1|qwen3.6-35b-a3b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "m3-16g|gemma-4-31b|batching": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi350x-x1|deepseek-v4-flash|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "pro6000-x1|deepseek-v4-flash|prefill": [
  "explained",
  "SGLang runs DeepSeek-V4 prefill without graphs",
  "SGLang 0.5.22 turns prefill graphs off for DeepSeek-V4 to save memory, so the 555-token prompt launches its kernels one by one: TTFT 23-53 ms vs pie's 8-22 ms."
 ],
 "l4-x1|mimo-v2.6-flash-rl|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx4090-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "mi300x-x1|qwen3.8-flash-next|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-sxm-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "rtx5090-x1|gpt-oss-120b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "pro6000-x1|kimi-k3|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx5090-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "web-rtx5090|gpt-oss-120b|decode": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "h200-x1|nvidia-nemotron-3-super-120b-a12b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a40-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|qwen3.6-35b-a3b|batching": [
  "real",
  "Rival faster on this AMD cell",
  "Not traced. The rival is faster than pie here; no harness issue found."
 ],
 "rtx5090-x1|qwen3.8-flash-next|pbatch": [
  "rerun",
  "Old pie row",
  "Pie's row is from Oct 27 (TTFT 1.64 s vs TRT-LLM's 0.23 s) and predates later pie batched-prefill work."
 ],
 "a40-x1|gpt-oss-120b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "tpu-v6e-1|gemma-4-e2b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "tpu-v6e-1|gemma-4-31b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "mi300x-x1|muse-spark-open-816b-a42b|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "rtx5090-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "mi300x-x1|gemma-4-e4b|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "h200-x1|gpt-oss-120b|pbatch": [
  "rerun",
  "Noisy run",
  "vLLM's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "pro6000-x4|gpt-oss-20b|decode": [
  "explained",
  "vLLM's MXFP4 expert kernel is slow",
  "vLLM's GPU is busy 2.88 of each 3.07 ms token (H200, gpt-oss-20b); its MXFP4 expert matmul alone takes 1.20 ms, reading at about 1 TB/s of the 4.8 available. Pie's whole token takes 2.28 ms."
 ],
 "a100-sxm-x1|qwen3.5-0.8b|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "h200-x1|gpt-oss-120b|decode": [
  "explained",
  "vLLM's MXFP4 expert kernel is slow",
  "vLLM's GPU is busy 2.88 of each 3.07 ms token (H200, gpt-oss-20b); its MXFP4 expert matmul alone takes 1.20 ms, reading at about 1 TB/s of the 4.8 available. Pie's whole token takes 2.28 ms."
 ],
 "pro6000-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h200-x1|deepseek-v4-flash|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "a100-x2|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "vLLM's gpt-oss MXFP4 prefill beats pie's 4-bit-weight experts on A40, A100 x2 and H100 PCIe: TTFT 52-120 ms vs pie's 70-168 ms."
 ],
 "pro4500-x1|hy4-preview|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "m5-max-128g|gemma-4-e4b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "b200-x1|muse-spark-open-816b-a42b|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "a100-pcie-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "h200-x1|qwen3-0.6b|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "h200-x1|gpt-oss-20b|decode": [
  "explained",
  "vLLM's MXFP4 expert kernel is slow",
  "vLLM's GPU is busy 2.88 of each 3.07 ms token (H200, gpt-oss-20b); its MXFP4 expert matmul alone takes 1.20 ms, reading at about 1 TB/s of the 4.8 available. Pie's whole token takes 2.28 ms."
 ],
 "rtx5090-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "h200-x1|hy4-preview|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "web-rtx4090|qwen3.8-27b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "m5-max-64g|muse-glimmer-30b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "a100-sxm-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "rtx4090-x1|glm-5.3|prefill": [
  "explained",
  "SGLang uses fallback kernels for GLM-5.3",
  "On pre-Hopper GPUs and Blackwell RTX cards SGLang has no FlashMLA or DeepGEMM, so GLM-5.3's sparse attention runs on generic Triton, TileLang and PyTorch fallback kernels."
 ],
 "m2-16g|gemma-4-e2b|prefill": [
  "rerun",
  "Noisy run",
  "mlx-lm's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "tpu-v5p-8|gemma-4-e4b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "tpu-v6e-1|gpt-oss-20b|prefill": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "tpu-v5p-8|gemma-4-e2b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a40-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "b200-x1|minimax-m3.1-flash|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-sxm-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "h100-sxm-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "SGLang launches attention outside its graph",
  "Not traced on this GPU. On H200 the cause was SGLang launching attention outside its prefill graph. Here its TTFT is 2-85 ms above pie's."
 ],
 "m5-max-64g|gemma-4-e2b|prefill": [
  "explained",
  "mlx-lm runs the last prompt token separately",
  "mlx-lm prefills all but the last prompt token, clears its cache, then runs that token as a separate step: 20.4 + 2.5 + 6.4 ms plus ~7 ms of server time = 37 ms (Gemma-4-E2B, M5 Max). Pie: 26 ms."
 ],
 "mi300x-x1|nvidia-nemotron-3-super-120b-a12b|pbatch": [
  "real",
  "Pie's AMD Mamba-2 prefill is serial",
  "Pie's AMD Mamba-2 prefill processes the prompt one token at a time (on NVIDIA it uses 16-token chunks), so Nemotron-3 prefill is 2-6x slower than vLLM or SGLang on AMD."
 ],
 "l40s-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h100-sxm-x1|deepseek-v4.1-flash|pbatch": [
  "real",
  "vLLM's FlashMLA prefill is faster",
  "On H100/H200 vLLM uses FlashMLA and DeepGEMM FP8 kernels and prefills 256 DeepSeek-V4.1 prompts 30-40% faster than pie."
 ],
 "pro6000-x1|qwen3.8-flash-next|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "a40-x1|qwen3.5-0.8b|batching": [
  "explained",
  "vLLM's step waits on the CPU",
  "At 256 requests vLLM's step takes 6.5 ms with the GPU idle a third of it (H200), and its fp32 GDN state kernel takes 2.4 ms. Pie keeps that state in bf16, half the bytes."
 ],
 "mi300x-x1|hy4-preview|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "rtx5090-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "m2-16g|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "rtx4090-x1|hy4-preview|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "a100-sxm-x1|deepseek-v4-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "tpu-v5e-1|gemma-4-e2b|prefill": [
  "explained",
  "vLLM-TPU pads the prompt to 1024 tokens",
  "vLLM-TPU rounds each prompt up to a power-of-two size, so the 555-token prompt is computed as 1024 tokens, about 1.8x the work. Its TTFT trails pie's by 30-80%."
 ],
 "l40s-x1|qwen3.6-35b-a3b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "pro6000-x1|glm-5.3-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "pro4500-x1|qwen3.6-27b|prefill": [
  "plausible",
  "TRT-LLM's TTFT 5-40 ms above pie's",
  "Not traced. TRT-LLM's single-request TTFT is 5-40 ms above pie's, mostly on the Nemotron-3 hybrid Mamba models."
 ],
 "m3-16g|gemma-4-e4b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "l40s-x1|deepseek-v4.1-flash|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h200-x4|qwen3.8-flash-next|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi350x-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "m3-16g|gemma-4-e2b|prefill": [
  "explained",
  "Pie also uses the Neural Engine",
  "On M2-M4 pie runs 47-74% of the prefill matmuls on the Neural Engine as well as the GPU. mlx-lm uses the GPU only, at about 80% of its peak (M3 2.7 of 3.4 TFLOPS, M4 Pro 6.5 of 7.9)."
 ],
 "pro4500-x1|glm-5.3-flash|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "m5-max-64g|gemma-4-31b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "pro6000-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "h200-x1|mimo-v2.6-flash-rl|prefill": [
  "real",
  "Pie's 48-layer MiMo prefill is slower",
  "This row is the 48-layer MiMo cut (other GPUs use 6 layers). On it pie's 552-token prefill takes 113 ms vs vLLM's 78 ms."
 ],
 "m5-max-128g|gemma-4-e2b|prefill": [
  "explained",
  "mlx-lm runs the last prompt token separately",
  "mlx-lm prefills all but the last prompt token, clears its cache, then runs that token as a separate step: 20.4 + 2.5 + 6.4 ms plus ~7 ms of server time = 37 ms (Gemma-4-E2B, M5 Max). Pie: 26 ms."
 ],
 "l40s-x1|gpt-oss-120b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "web-rtx4090|gpt-oss-20b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "h200-x1|qwen3.5-0.8b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m5-max-64g|qwen3.8-27b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "m5-max-128g|gpt-oss-20b|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "rtx5090-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "m5-max-64g|qwen3.6-27b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "a40-x1|glm-5.3-flash|pbatch": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "a40-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m4-pro-48g|qwen3.8-flash-next|decode": [
  "explained",
  "mlx-vlm's GPU waits on Python",
  "mlx-vlm builds each token's work in Python (2.4-3.3 ms) and waits for the GPU once mid-step, so it cannot overlap that with 1.5 ms of GPU work. M5 Max: 253 tok/s, pie 345."
 ],
 "tpu-v5p-8|gemma-4-12b|prefill": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi300x-x1|gemma-4-e4b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "mi355x-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "SGLang runs prefill without graphs on AMD",
  "SGLang 0.5.22 enables prefill graphs only on NVIDIA. On AMD every prefill launches its kernels one by one, so its TTFT for the 555-token prompt is 7-37 ms above pie's."
 ],
 "h100-sxm-x1|glm-5.3-flash|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "pro4500-x1|qwen3.5-9b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m5-max-64g|qwen3.6-35b-a3b|decode": [
  "explained",
  "mlx-lm launches 1,797 kernels per token",
  "mlx-lm launches 1,797 GPU kernels per token at about 2.5 us each, so its step takes 7.3 ms while reading the weights takes about 2.8 ms (M5 Max). Pie's step takes 6.0 ms."
 ],
 "m5-max-64g|qwen3.8-flash-next|decode": [
  "explained",
  "mlx-vlm's GPU waits on Python",
  "mlx-vlm builds each token's work in Python (2.4-3.3 ms) and waits for the GPU once mid-step, so it cannot overlap that with 1.5 ms of GPU work. M5 Max: 253 tok/s, pie 345."
 ],
 "pro6000-x1|gpt-oss-120b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "h100-pcie-x1|gpt-oss-20b|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "m2-16g|muse-glimmer-30b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "pro4500-x1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a40-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m5-max-64g|qwen3.5-9b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "h100-sxm-x1|gpt-oss-120b|batching": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "b200-x1|gpt-oss-120b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi355x-x1|qwen3.5-0.8b|batching": [
  "real",
  "Rival faster on this AMD cell",
  "Not traced. The rival is faster than pie here; no harness issue found."
 ],
 "pro6000-x4|qwen3.5-0.8b|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "a40-x1|gpt-oss-120b|prefill": [
  "real",
  "vLLM's MXFP4 prefill is faster",
  "vLLM's gpt-oss MXFP4 prefill beats pie's 4-bit-weight experts on A40, A100 x2 and H100 PCIe: TTFT 52-120 ms vs pie's 70-168 ms."
 ],
 "mi300x-x1|gemma-4-26b-a4b|prefill": [
  "plausible",
  "Rivals' TTFT 7-200 ms above pie's",
  "Not traced. The 555-token prompt is far below what the GPU can compute, and the rivals' TTFT runs 7-200 ms above pie's. vLLM rows on MI350X/MI355X use AMD's 0.29.1 image."
 ],
 "web-rtx4090|qwen3.6-27b|decode": [
  "explained",
  "WebLLM sorts the whole vocabulary every token",
  "WebLLM waits for the GPU every token and sorts all 248k vocabulary entries to pick one, even at temperature 0. Qwen3.5-9B on RTX 5090: WebLLM 60, pie 88 tok/s."
 ],
 "m2-16g|qwen3.8-flash-next|pbatch": [
  "rerun",
  "Harness bug: mlx-lm ran one at a time",
  "Our bench sent a fixed seed with every request, and mlx-lm 0.32's server runs seeded requests one at a time, so these 32 requests ran one by one. Fixed in benchmarks #1672; this row predates the fix."
 ],
 "a40-x1|hy4-preview|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h200-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi350x-x1|mimo-v2.6-flash-rl|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "h100-sxm-x1|gpt-oss-20b|batching": [
  "real",
  "SGLang faster here",
  "Not traced. SGLang beats pie on these batched cells; no harness issue found."
 ],
 "pro4500-x1|qwen3.6-27b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi300x-x1|qwen3.5-0.8b|batching": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "tpu-v6e-1|gpt-oss-120b|prefill": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "pro4500-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "b200-x1|qwen3.8-27b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "b200-x1|qwen3.5-9b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "m2-16g|gemma-4-31b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "l40s-x1|qwen3-0.6b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "pro6000-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "m5-max-128g|qwen3.6-35b-a3b|decode": [
  "explained",
  "mlx-lm launches 1,797 kernels per token",
  "mlx-lm launches 1,797 GPU kernels per token at about 2.5 us each, so its step takes 7.3 ms while reading the weights takes about 2.8 ms (M5 Max). Pie's step takes 6.0 ms."
 ],
 "rtx4090-x1|glm-5.3-flash|batching": [
  "real",
  "SGLang faster here",
  "Not traced. SGLang beats pie on these batched cells; no harness issue found."
 ],
 "mi300x-x1|qwen3.6-27b|prefill": [
  "rerun",
  "Noisy run",
  "pie's repeated runs differ by more than 2%, so this number is not reliable yet."
 ],
 "mi355x-x1|mimo-v2.6-flash-rl|decode": [
  "real",
  "SGLang's AMD MLA decode is faster",
  "SGLang uses AMD's AITER MLA decode kernels on MI350X/MI355X: 537-750 tok/s vs pie's 279-467."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|pbatch": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "h100-pcie-x1|qwen3.5-0.8b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "rtx5090-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "tpu-v5e-1|gpt-oss-20b|pbatch": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "a100-sxm-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "rtx5090-x1|gpt-oss-20b|batching": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "m5-max-64g|gemma-4-12b|batching": [
  "explained",
  "MLX skips the M5's matmul units",
  "vllm-metal's 32-request step is plain MLX, and MLX 0.32.4 splits these 4-bit matmuls into a kernel that cannot use the M5's neural accelerators: about 10 of the 38.7 ms step (Qwen3.5-9B)."
 ],
 "pro6000-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "a100-pcie-x1|hy4-preview|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a100-pcie-x1|gemma-4-e4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "pro6000-x1|muse-spark-open-816b-a42b|batching": [
  "explained",
  "vLLM uses a generic MoE kernel",
  "On Blackwell RTX and RTX PRO cards vLLM runs Muse Spark's bf16 experts through its generic Triton MoE kernel, not a tuned one."
 ],
 "h200-x1|glm-5.3-flash|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ],
 "h100-sxm-x1|gpt-oss-20b|decode": [
  "explained",
  "vLLM's MXFP4 expert kernel is slow",
  "vLLM's GPU is busy 2.88 of each 3.07 ms token (H200, gpt-oss-20b); its MXFP4 expert matmul alone takes 1.20 ms, reading at about 1 TB/s of the 4.8 available. Pie's whole token takes 2.28 ms."
 ],
 "tpu-v6e-1|qwen3.6-35b-a3b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "pro6000-x1|gemma-4-26b-a4b|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "tpu-v5p-8|gemma-4-12b|decode": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "mi300x-x1|qwen3.8-flash-next|pbatch": [
  "plausible",
  "Rivals use generic kernels on AMD",
  "On AMD the rivals run these MoE, MLA and sparse-attention models through generic Triton kernels (vLLM 0.32.0 on MI300X, SGLang 0.5.22) and run fewer requests at once."
 ],
 "a40-x1|gemma-4-31b|batching": [
  "real",
  "SGLang faster here",
  "Not traced. SGLang beats pie on these batched cells; no harness issue found."
 ],
 "pro6000-x1|gemma-4-31b|prefill": [
  "plausible",
  "TRT-LLM's TTFT 5-40 ms above pie's",
  "Not traced. TRT-LLM's single-request TTFT is 5-40 ms above pie's, mostly on the Nemotron-3 hybrid Mamba models."
 ],
 "tpu-v5e-1|gpt-oss-120b|pbatch": [
  "explained",
  "vLLM-TPU's int8 MoE kernel",
  "vLLM-TPU pads the 606-token prompt to 1024 tokens and spends 54-71% of its prefill in its int8 expert matmul."
 ],
 "tpu-v5e-1|gemma-4-e2b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "Not traced. vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "tpu-v5e-1|qwen3.5-0.8b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "Not traced. vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "h100-sxm-x1|nvidia-nemotron-3-ultra-550b-a55b|prefill": [
  "plausible",
  "TRT-LLM's TTFT 5-40 ms above pie's",
  "Not traced. TRT-LLM's single-request TTFT is 5-40 ms above pie's, mostly on the Nemotron-3 hybrid Mamba models."
 ],
 "l40s-x1|hy4-preview|pbatch": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "web-rtx5090|muse-glimmer-30b|decode": [
  "explained",
  "llama.cpp web spends ~20 ms per token",
  "llama.cpp in the browser spends about 20 ms per token on any model or GPU (RTX 4090: Qwen3.5-4B 19.8, 9B 19.5, Gemma-4-12B 22.7 ms): every step makes a round trip to the CPU and samples the full vocabulary on one thread."
 ],
 "mi300x-x1|qwen3.8-27b|prefill": [
  "real",
  "Rival faster on this AMD cell",
  "Not traced. The rival is faster than pie here; no harness issue found."
 ],
 "a100-pcie-x1|mimo-v2.6-flash-rl|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a100-sxm-x1|qwen3.8-flash-next|batching": [
  "explained",
  "SGLang pauses decoding for new prompts",
  "SGLang reads new prompts as separate 8k-token batches and stops all other requests while it does, so tokens stall: p99 time between tokens 64-375 ms."
 ],
 "tpu-v6e-1|gemma-4-31b|pbatch": [
  "real",
  "vLLM-TPU batched prefill is faster",
  "Not traced. vLLM-TPU's batched prefill beats pie's on these dense v5e/v6e cells by about 26%."
 ],
 "pro4500-x1|minimax-m3.1-flash|prefill": [
  "plausible",
  "vLLM uses fallback kernels for MiniMax",
  "On these GPUs vLLM runs MiniMax-M3's sparse attention on Triton, and its MXFP8 weights need fallback kernels."
 ],
 "pro4500-x1|kimi-k3|prefill": [
  "explained",
  "vLLM runs the 555-token prompt without graphs",
  "vLLM uses CUDA graphs only up to 512 tokens, so the 555-token prompt launches every kernel one by one: 3 ms of GPU work inside an 18 ms TTFT (H200, Qwen3-0.6B). With graphs up to 1024 tokens it would take 12.4 ms."
 ],
 "a40-x1|muse-spark-open-816b-a42b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "h200-x4|glm-5.3-flash|prefill": [
  "real",
  "Pie's 4-GPU prefill is slower",
  "Pie's 4-GPU tensor-parallel prefill trails SGLang: TTFT 37-110 ms vs 19-58 ms (rows from Oct 18-22)."
 ],
 "a100-sxm-x1|glm-5.3|prefill": [
  "explained",
  "vLLM runs GLM-5.3 without full graphs",
  "On A100 and A40, vLLM 0.32 serves GLM-5.3's sparse attention with a portable backend that cannot use full CUDA graphs: the A100 runs the whole model without graphs, the A40 partly graphed."
 ],
 "rtx4090-x1|gemma-4-31b|batching": [
  "plausible",
  "Not traced yet",
  "The cause of this gap has not been measured yet."
 ],
 "l40s-x1|minimax-m3.1-flash|pbatch": [
  "plausible",
  "SGLang prefills 256 prompts slower",
  "Not traced. SGLang prefills the 256 prompts 25-120% slower than pie on these Blackwell and Ada GPUs; no harness setting explains it."
 ],
 "h200-x1|gemma-4-26b-a4b|decode": [
  "explained",
  "SGLang's step is 384 small kernels",
  "SGLang's batch-1 step runs 384 small kernels and keeps the GPU busy 1.42 of its 1.56 ms (H200, Qwen3-0.6B). Pie's whole step takes 1.12 ms."
 ],
 "pro4500-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "pro6000-x1|gpt-oss-20b|pbatch": [
  "real",
  "TRT-LLM's MXFP4 expert kernels are faster",
  "TensorRT-LLM 1.4 uses fused MXFP4 expert kernels; pie runs its experts as 4-bit weights with 16-bit math. TRT-LLM is 25-37% faster at batch on Blackwell RTX/PRO and H100."
 ],
 "b200-x1|qwen3.6-27b|prefill": [
  "explained",
  "SGLang launches attention outside its graph",
  "SGLang's prefill graph covers only the matmuls; attention and GDN kernels launch one by one between them, so the GPU waits between kernels: 2.7 ms of work stretched over 6.9 ms (H200, Qwen3-0.6B). A full graph would cut its TTFT from 10.5 to 8.0 ms."
 ]
};
