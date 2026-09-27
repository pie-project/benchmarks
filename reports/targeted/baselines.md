# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 59.91 | 128.4 | 2.143× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 60.45 | 124.5 | 2.060× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 10.52 | 19.47 | 1.850× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 10.4 | 17.39 | 1.671× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 15.63 | 23.48 | 1.502× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 60.87 | 85.07 | 1.398× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 60.42 | 77.02 | 1.275× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 24.5 | 26.94 | 1.100× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 24.41 | 26.72 | 1.095× **pie trails** | **NO** | competitive |
