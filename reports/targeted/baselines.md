# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-48g | gemma-4-26b-a4b-mlx4 | cache-2k | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 34.11 | 97.56 | 2.861× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 27.87 | 48.15 | 1.727× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 27.87 | 46.65 | 1.674× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 78.7 | 130 | 1.652× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 29.26 | 47.23 | 1.614× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 84.78 | 128.4 | 1.515× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-splash 1.1.0 | output_tok_s | 28.83 | 41.81 | 1.450× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 27.87 | 38.67 | 1.387× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 52.21 | 71.28 | 1.365× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 52.21 | 67.9 | 1.301× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 27.87 | 33.38 | 1.198× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 112.6 | 122.8 | 1.091× **pie trails** | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 29.26 | 30.81 | 1.053× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.83 | 29.91 | 1.037× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 112.6 | 115.8 | 1.029× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.86 | 29.44 | 1.020× **pie trails** | yes | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.98 | 29.16 | 1.006× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 30.79 | 30.39 | 0.987× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 88.69 | 85.07 | 0.959× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 32.41 | 31.02 | 0.957× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 112.6 | 107.4 | 0.954× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 31.29 | 29.55 | 0.944× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 52.21 | 48.64 | 0.932× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 171.5 | 157.9 | 0.921× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 211.4 | 193.5 | 0.915× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 140.5 | 127.3 | 0.906× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 151 | 136.2 | 0.902× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 140.9 | 126 | 0.894× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.39 | 26.15 | 0.890× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.24 | 25.68 | 0.878× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 140.5 | 123.1 | 0.876× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 30.25 | 26.38 | 0.872× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.6 | 28.38 | 0.870× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 31.11 | 26.94 | 0.866× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 142.7 | 122 | 0.855× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 32.83 | 27.89 | 0.849× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 137.6 | 116.6 | 0.847× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 30.25 | 25.51 | 0.843× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 156.6 | 131.3 | 0.839× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 135.3 | 112.6 | 0.833× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 252.4 | 208.7 | 0.827× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | cache-2k | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.89 | 24.71 | 0.827× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 137.6 | 113.6 | 0.826× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.44 | 26.67 | 0.822× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 159.2 | 129.9 | 0.816× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 211.4 | 170.7 | 0.807× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 134 | 107.8 | 0.804× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.83 | 26.29 | 0.801× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 142.7 | 113.3 | 0.794× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 156.3 | 123.7 | 0.791× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 135.3 | 106.7 | 0.788× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 140.9 | 111 | 0.788× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.39 | 22.79 | 0.775× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.51 | 23.48 | 0.770× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 29.26 | 22.52 | 0.770× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-story-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 29.24 | 22.46 | 0.768× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 140.5 | 106.6 | 0.759× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 32.41 | 24.48 | 0.755× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.6 | 24.54 | 0.753× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-mlxlm 0.31.3 | output_tok_s | 156.6 | 117.9 | 0.753× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 30.79 | 22.97 | 0.746× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.98 | 21.53 | 0.743× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.83 | 21.37 | 0.741× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1068 | 783.6 | 0.734× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 32.31 | 23.3 | 0.721× | yes | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.86 | 20.43 | 0.708× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 32.31 | 22.57 | 0.699× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 140.5 | 96.41 | 0.686× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 151 | 102.9 | 0.681× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 134 | 90.9 | 0.678× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 140.9 | 95.27 | 0.676× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 142.7 | 95.83 | 0.671× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 31.29 | 20.95 | 0.670× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 135.3 | 89.36 | 0.661× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 135.3 | 88.96 | 0.657× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.11 | 19.47 | 0.646× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 284 | 182.6 | 0.643× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 137.6 | 88.26 | 0.641× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 134 | 84.95 | 0.634× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 252.4 | 158.7 | 0.629× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-short-100 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 156.6 | 98.34 | 0.628× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 72.03 | 45.03 | 0.625× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 151 | 94.16 | 0.624× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 28.83 | 17.93 | 0.622× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 120.5 | 74.19 | 0.616× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 81.89 | 50.39 | 0.615× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 284 | 172.8 | 0.608× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-512-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 156.3 | 95.06 | 0.608× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | c4 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 81.89 | 49.21 | 0.601× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ob-story-200 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 159.2 | 95.6 | 0.600× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 28.16 | 15.92 | 0.565× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1068 | 602.3 | 0.564× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 344.7 | 189.5 | 0.550× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 78.7 | 41.7 | 0.530× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 28.16 | 14.24 | 0.506× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 71.96 | 36.37 | 0.505× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.35.0 | output_tok_s | 28.92 | 14.55 | 0.503× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.49 | 13.71 | 0.499× | yes | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 28.92 | 14.29 | 0.494× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 28.16 | 13.79 | 0.490× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 109.1 | 52.66 | 0.483× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 141 | 67.74 | 0.480× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 141 | 67.69 | 0.480× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 109.1 | 51.6 | 0.473× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.49 | 12.8 | 0.466× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 26.92 | 11.81 | 0.439× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 284 | 122.6 | 0.432× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 284 | 121.4 | 0.428× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.35.0 | output_tok_s | 344.7 | 143.7 | 0.417× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 120.5 | 50.02 | 0.415× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1957 | 810.2 | 0.414× | **NO** | competitive |
| m5-max-48g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 71.96 | 28.61 | 0.398× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-mlxlm 0.31.3 | output_tok_s | 78.7 | 29.92 | 0.380× | **NO** | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-llamacpp b11312 | output_tok_s | 26.92 | 9.925 | 0.369× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | c4 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 78.7 | 28.25 | 0.359× | **NO** | competitive |
| m5-max-128g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 28.11 | 9.979 | 0.355× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1957 | 692.8 | 0.354× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-mlxlm 0.31.3 | output_tok_s | 344.7 | 121.8 | 0.353× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.35 | 9.652 | 0.353× | yes | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-ollama 0.35.0 | output_tok_s | 128.3 | 44.29 | 0.345× | **NO** | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-llamacpp b11312 | output_tok_s | 109.1 | 35.86 | 0.329× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-llamacpp b11312 | output_tok_s | 27.35 | 8.888 | 0.325× | yes | competitive |
| m5-max-128g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.35.0 | output_tok_s | 344.7 | 111.4 | 0.323× | **NO** | competitive |
| m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.6-35b-a3b-llamacpp b11312 | output_tok_s | 128.3 | 39.83 | 0.310× | yes | competitive |
| m5-max-128g | qwen3.8-27b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | qwen3.8-27b-ollama 0.35.0 | output_tok_s | 26.92 | 7.716 | 0.287× | **NO** | competitive |
