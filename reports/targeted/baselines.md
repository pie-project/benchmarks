# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-48g | gemma-4-26b-a4b-mlx4 | cache-2k | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 34.11 | 97.56 | 2.861× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 24.81 | 48.15 | 1.941× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 24.81 | 38.67 | 1.559× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 84.78 | 128.4 | 1.515× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 51.26 | 71.28 | 1.391× **pie trails** | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 112.5 | 122.8 | 1.092× **pie trails** | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-512-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 112.5 | 115.8 | 1.030× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 88.69 | 85.07 | 0.959× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 171.5 | 157.9 | 0.921× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 211.4 | 193.5 | 0.915× | yes | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 140.5 | 127.3 | 0.906× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-short-100 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 140.5 | 123.1 | 0.876× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.9 | 26.15 | 0.874× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-short-100 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.66 | 28.38 | 0.869× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 31.11 | 26.94 | 0.866× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-story-200 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 137.1 | 113.6 | 0.829× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 130.3 | 107.8 | 0.827× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 252.4 | 208.7 | 0.827× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | cache-2k | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 29.89 | 24.71 | 0.827× | yes | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ob-512-200 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 32.5 | 26.67 | 0.821× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 211.4 | 170.7 | 0.807× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.51 | 23.48 | 0.770× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1068 | 783.6 | 0.734× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | ob-advanced-500 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 130.3 | 90.9 | 0.698× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.11 | 19.47 | 0.646× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 252.4 | 158.7 | 0.629× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1068 | 602.3 | 0.564× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama 0.34.4 | output_tok_s | 306.8 | 172.8 | 0.563× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-4k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 28.6 | 13.71 | 0.479× | yes | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-gguf-bf16 10270 (071327508) | output_tok_s | 1957 | 810.2 | 0.414× | **NO** | competitive |
| m5-max-48g | gemma-4-26b-a4b-mlx4 | c4 | text-completion-bench | tp1 | gemma-4-26b-a4b-ollama-mlx 0.34.4 | output_tok_s | 306.8 | 122.6 | 0.400× | **NO** | competitive |
| m5-max-48g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | qwen3.5-0.8b-mlx-bf16 0.31.3 | output_tok_s | 1957 | 692.8 | 0.354× | **NO** | competitive |
| m5-max-48g | muse-glimmer-30b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | muse-glimmer-30b-ollama 0.34.4 | output_tok_s | 27.95 | 9.652 | 0.345× | yes | competitive |
