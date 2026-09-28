# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-48g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | decode_tok_s | 30.82 | -6.1% | ±5.3% | f9214a104dcd6da921debdf103f7688aa95fbb79 |
| regression | pie | m5-max-48g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 33.22 | -3.9% | ±2.0% | f9214a104dcd6da921debdf103f7688aa95fbb79 |
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | decode_tok_s | 31.73 | -3.4% | ±3.3% | f9214a104dcd6da921debdf103f7688aa95fbb79 |
