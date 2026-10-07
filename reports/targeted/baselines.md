# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-48g | gemma-4-26b-a4b-mlx4 | cache-2k | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 34.11 | 97.56 | 2.861× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 27.87 | 48.15 | 1.727× **pie trails** | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 77.09 | 130 | 1.686× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 27.87 | 46.65 | 1.674× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 29.15 | 47.23 | 1.620× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 84.78 | 128.4 | 1.515× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 28.83 | 41.81 | 1.450× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 27.87 | 38.67 | 1.387× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 52.21 | 71.28 | 1.365× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 52.21 | 67.9 | 1.301× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 27.87 | 33.38 | 1.198× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 112.6 | 122.8 | 1.091× **pie trails** | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 29.15 | 30.81 | 1.057× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.83 | 29.91 | 1.037× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 112.6 | 115.8 | 1.029× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.86 | 29.44 | 1.020× **pie trails** | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 30.47 | 31.02 | 1.018× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 29.98 | 30.39 | 1.014× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.98 | 29.16 | 1.006× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 29.48 | 29.55 | 1.002× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 88.69 | 85.07 | 0.959× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 112.6 | 107.4 | 0.954× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 52.21 | 48.64 | 0.932× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 171.5 | 157.9 | 0.921× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 211.4 | 193.5 | 0.915× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 140.5 | 127.3 | 0.906× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 151.1 | 136.2 | 0.902× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 140.9 | 126 | 0.895× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.39 | 26.15 | 0.890× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.24 | 25.68 | 0.878× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 140.5 | 123.1 | 0.876× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.6 | 28.38 | 0.870× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 31.11 | 26.94 | 0.866× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 142.2 | 122 | 0.858× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 32.9 | 27.89 | 0.848× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 137.6 | 116.6 | 0.847× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 31.61 | 26.38 | 0.835× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 135 | 112.6 | 0.834× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 252.4 | 208.7 | 0.827× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | cache-2k | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.89 | 24.71 | 0.827× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 137.6 | 113.6 | 0.826× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.44 | 26.67 | 0.822× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 159.1 | 129.9 | 0.816× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 211.4 | 170.7 | 0.807× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 31.61 | 25.51 | 0.807× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 153.6 | 123.7 | 0.805× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 134 | 107.8 | 0.804× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 30.47 | 24.48 | 0.803× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.9 | 26.29 | 0.799× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 142.2 | 113.3 | 0.796× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 135.2 | 106.7 | 0.789× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 140.9 | 111 | 0.788× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.39 | 22.79 | 0.775× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 29.15 | 22.52 | 0.772× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.51 | 23.48 | 0.770× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.24 | 22.46 | 0.768× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 29.98 | 22.97 | 0.766× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 140.5 | 106.6 | 0.759× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.6 | 24.54 | 0.753× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.98 | 21.53 | 0.743× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.83 | 21.37 | 0.741× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1068 | 783.6 | 0.734× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 32.53 | 23.3 | 0.716× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 29.48 | 20.95 | 0.711× | yes | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.86 | 20.43 | 0.708× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.53 | 22.57 | 0.694× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 140.5 | 96.41 | 0.686× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 151.1 | 102.9 | 0.681× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 134 | 90.9 | 0.678× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 140.9 | 95.27 | 0.676× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 142.2 | 95.83 | 0.674× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 135 | 89.36 | 0.662× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 135.2 | 88.96 | 0.658× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.11 | 19.47 | 0.646× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 284 | 182.6 | 0.643× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 137.6 | 88.26 | 0.641× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 134 | 84.95 | 0.634× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 252.4 | 158.7 | 0.629× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 72.03 | 45.03 | 0.625× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 151.1 | 94.16 | 0.623× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 28.83 | 17.93 | 0.622× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 153.6 | 95.06 | 0.619× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 120.2 | 74.19 | 0.617× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 284 | 172.8 | 0.608× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 83.65 | 50.39 | 0.602× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 159.1 | 95.6 | 0.601× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 83.65 | 49.21 | 0.588× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 27.94 | 15.92 | 0.570× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1068 | 602.3 | 0.564× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 342.2 | 189.5 | 0.554× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 77.09 | 41.7 | 0.541× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 27.94 | 14.24 | 0.509× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 71.96 | 36.37 | 0.505× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 29.13 | 14.55 | 0.499× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.49 | 13.71 | 0.499× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 27.94 | 13.79 | 0.494× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.13 | 14.29 | 0.491× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 109 | 52.66 | 0.483× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 140.5 | 67.74 | 0.482× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 140.5 | 67.69 | 0.482× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 109 | 51.6 | 0.473× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.49 | 12.8 | 0.466× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 26.88 | 11.81 | 0.439× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 284 | 122.6 | 0.432× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 284 | 121.4 | 0.428× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.35.0 | output_tok_s | 342.2 | 143.7 | 0.420× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 120.2 | 50.02 | 0.416× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 427.4 | 177.3 | 0.415× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1957 | 810.2 | 0.414× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 71.96 | 28.61 | 0.398× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 77.09 | 29.92 | 0.388× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 26.88 | 9.925 | 0.369× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 77.09 | 28.25 | 0.366× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.76 | 9.979 | 0.359× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 342.2 | 121.8 | 0.356× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1957 | 692.8 | 0.354× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.35 | 9.652 | 0.353× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 128.4 | 44.29 | 0.345× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 109 | 35.86 | 0.329× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 342.2 | 111.4 | 0.325× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.35 | 8.888 | 0.325× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 128.4 | 39.83 | 0.310× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 427.4 | 132.6 | 0.310× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 26.88 | 7.716 | 0.287× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 427.4 | 114.7 | 0.268× | **NO** | competitive |
