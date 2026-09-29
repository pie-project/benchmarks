# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | decode_tok_s | 30.71 | -6.3% | ±4.2% | e5db756f2efb5447e4d67f0340db5d88d82395aa |
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 31.3 | -5.5% | ±2.2% | e5db756f2efb5447e4d67f0340db5d88d82395aa |
