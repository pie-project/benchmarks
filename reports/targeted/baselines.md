# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 9.797 | 19.47 | 1.987× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 54.41 | 85.07 | 1.563× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 15.12 | 23.48 | 1.553× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 23.81 | 26.94 | 1.131× **pie trails** | **NO** | competitive |
