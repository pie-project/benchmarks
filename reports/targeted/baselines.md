# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 78.17 | 128.4 | 1.643× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 76.04 | 124.5 | 1.638× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 76.58 | 77.02 | 1.006× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 86.91 | 85.07 | 0.979× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.63 | 26.94 | 0.880× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 30.16 | 23.48 | 0.779× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 29.82 | 19.47 | 0.653× | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 28.49 | 17.39 | 0.610× | **NO** | competitive |
