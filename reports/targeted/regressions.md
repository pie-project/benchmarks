# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 32.37 | -2.4% | ±2.0% | 5eab5e00b6b2b92d4b9d83320abf0cf97249f5af |
