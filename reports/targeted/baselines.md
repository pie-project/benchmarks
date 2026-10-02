# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-48g | gemma-4-26b-a4b-mlx4 | cache-2k | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 34.11 | 97.56 | 2.861× **pie trails** | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 29.17 | 52.66 | 1.805× **pie trails** | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 29.17 | 51.6 | 1.769× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 27.87 | 48.15 | 1.727× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 27.87 | 46.65 | 1.674× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 30.17 | 47.23 | 1.566× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 84.78 | 128.4 | 1.515× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 28.83 | 41.81 | 1.450× **pie trails** | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 52.1 | 74.19 | 1.424× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 27.87 | 38.67 | 1.387× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 52.21 | 71.28 | 1.365× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 52.21 | 67.9 | 1.301× **pie trails** | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 29.17 | 35.86 | 1.229× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 27.87 | 33.38 | 1.198× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 112.6 | 122.8 | 1.091× **pie trails** | yes | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.83 | 29.91 | 1.037× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 29.98 | 31.02 | 1.035× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 112.6 | 115.8 | 1.029× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 30.17 | 30.81 | 1.021× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.86 | 29.44 | 1.020× **pie trails** | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 111.6 | 112.6 | 1.009× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 30.14 | 30.39 | 1.008× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.98 | 29.16 | 1.006× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 30.05 | 29.55 | 0.983× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 52.1 | 50.02 | 0.960× | yes | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 88.69 | 85.07 | 0.959× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 112.6 | 107.4 | 0.954× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 52.21 | 48.64 | 0.932× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 171.5 | 157.9 | 0.921× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 211.4 | 193.5 | 0.915× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 140.5 | 127.3 | 0.906× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 150.9 | 136.2 | 0.903× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 139.6 | 126 | 0.903× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 136.6 | 122 | 0.893× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.39 | 26.15 | 0.890× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.24 | 25.68 | 0.878× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 140.5 | 123.1 | 0.876× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.6 | 28.38 | 0.870× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 30.34 | 26.38 | 0.869× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 31.11 | 26.94 | 0.866× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 32.49 | 27.89 | 0.858× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 137.6 | 116.6 | 0.847× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 155.1 | 131.3 | 0.847× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 30.34 | 25.51 | 0.841× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 136.6 | 113.3 | 0.829× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 252.4 | 208.7 | 0.827× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | cache-2k | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.89 | 24.71 | 0.827× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 137.6 | 113.6 | 0.826× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.44 | 26.67 | 0.822× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 158.1 | 129.9 | 0.822× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 29.98 | 24.48 | 0.817× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.49 | 26.29 | 0.809× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 211.4 | 170.7 | 0.807× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 134 | 107.8 | 0.804× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 111.6 | 89.36 | 0.800× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 133.3 | 106.7 | 0.800× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 155.4 | 123.7 | 0.796× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 139.6 | 111 | 0.795× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.39 | 22.79 | 0.775× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.51 | 23.48 | 0.770× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.24 | 22.46 | 0.768× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 30.14 | 22.97 | 0.762× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 155.1 | 117.9 | 0.760× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 30.71 | 23.3 | 0.759× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 140.5 | 106.6 | 0.759× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.6 | 24.54 | 0.753× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 30.17 | 22.52 | 0.746× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.98 | 21.53 | 0.743× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.83 | 21.37 | 0.741× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 30.71 | 22.57 | 0.735× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1068 | 783.6 | 0.734× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.86 | 20.43 | 0.708× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 136.6 | 95.83 | 0.701× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 30.05 | 20.95 | 0.697× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 140.5 | 96.41 | 0.686× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 139.6 | 95.27 | 0.682× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 150.9 | 102.9 | 0.682× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 134 | 90.9 | 0.678× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 133.3 | 88.96 | 0.667× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.11 | 19.47 | 0.646× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 284 | 182.6 | 0.643× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 137.6 | 88.26 | 0.641× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 155.1 | 98.34 | 0.634× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 134 | 84.95 | 0.634× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 252.4 | 158.7 | 0.629× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 80.53 | 50.39 | 0.626× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 72.03 | 45.03 | 0.625× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 150.9 | 94.16 | 0.624× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 304.6 | 189.5 | 0.622× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 28.83 | 17.93 | 0.622× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 155.4 | 95.06 | 0.612× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 80.53 | 49.21 | 0.611× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 284 | 172.8 | 0.608× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 158.1 | 95.6 | 0.605× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1068 | 602.3 | 0.564× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 79.71 | 41.7 | 0.523× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 71.96 | 36.37 | 0.505× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 28.85 | 14.55 | 0.504× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.49 | 13.71 | 0.499× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 28.85 | 14.29 | 0.495× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.35.0 | output_tok_s | 304.6 | 143.7 | 0.472× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.49 | 12.8 | 0.466× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 409.1 | 177.3 | 0.433× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 284 | 122.6 | 0.432× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 284 | 121.4 | 0.428× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1957 | 810.2 | 0.414× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 304.6 | 121.8 | 0.400× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 71.96 | 28.61 | 0.398× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 79.71 | 29.92 | 0.375× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 304.6 | 111.4 | 0.366× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 79.71 | 28.25 | 0.354× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 28.16 | 9.979 | 0.354× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1957 | 692.8 | 0.354× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.35 | 9.652 | 0.353× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.35 | 8.888 | 0.325× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 409.1 | 132.6 | 0.324× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 409.1 | 114.7 | 0.280× | **NO** | competitive |
