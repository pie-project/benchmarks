# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-128g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 273.6 | -2.9% | ±2.8% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| improvement | pie | m5-max-128g | qwen3.8-27b-mlx4 | ob-512-200 | text-completion-bench | tp1 | decode_tok_s | 32.81 | +5.7% | ±5.1% | 8dc5fdd14ec61f06c38f05c0ac4128079bad681e |
| improvement | pie | m5-max-128g | qwen3.8-27b-mlx4 | ob-story-200 | text-completion-bench | tp1 | decode_tok_s | 33.35 | +5.7% | ±4.1% | 8dc5fdd14ec61f06c38f05c0ac4128079bad681e |
| improvement | pie | m5-max-128g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | output_tok_s | 1146 | +8.1% | ±5.0% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| improvement | pie | m5-max-128g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | output_tok_s | 2287 | +17.9% | ±5.0% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| improvement | pie | m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | output_tok_s | 88.69 | +44.6% | ±43.9% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
