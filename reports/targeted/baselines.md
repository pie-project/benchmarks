# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 73.79 | 128.4 | 1.740× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 74.56 | 85.07 | 1.141× **pie trails** | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 29.87 | 26.94 | 0.902× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 29.1 | 23.48 | 0.807× | **NO** | competitive |
| m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | mlxlm 0.31.3 | output_tok_s | 28.59 | 19.47 | 0.681× | **NO** | competitive |
