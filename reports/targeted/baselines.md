# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 55.36 | 128.4 | 2.319× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 10.47 | 19.47 | 1.860× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 9.506 | 17.39 | 1.829× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 55.25 | 85.07 | 1.540× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 16.25 | 23.48 | 1.445× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 56.07 | 77.02 | 1.374× **pie trails** | **NO** | competitive |
| m5-max-48g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 22.05 | 26.72 | 1.212× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 24.59 | 26.94 | 1.096× **pie trails** | **NO** | competitive |
