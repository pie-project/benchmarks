# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-128g | gemma-4-26b-a4b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | decode_tok_s | 98.31 | -12.7% | ±2.0% | cfa839f152ab97caab2dacd297d84e52e23a8f23 |
| regression | pie | m5-max-128g | qwen3.8-27b-mlx4 | ob-short-100 | text-completion-bench | tp1 | decode_tok_s | 30.09 | -11.2% | ±8.4% | cfa839f152ab97caab2dacd297d84e52e23a8f23 |
| regression | pie | m5-max-128g | qwen3.8-27b-mlx4 | control-aa | text-completion-bench | tp1 | decode_tok_s | 29.41 | -8.6% | ±7.3% | cfa839f152ab97caab2dacd297d84e52e23a8f23 |
| regression | pie | m5-max-128g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 273.6 | -2.9% | ±2.8% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| regression | pie | m5-max-128g | qwen3.6-35b-a3b-mlx4 | ctx-8k-256 | text-completion-bench | tp1 | decode_tok_s | 128.9 | -2.4% | ±2.0% | cfa839f152ab97caab2dacd297d84e52e23a8f23 |
| improvement | pie | m5-max-128g | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | output_tok_s | 1146 | +8.1% | ±5.0% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| improvement | pie | m5-max-128g | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | output_tok_s | 2287 | +17.9% | ±5.0% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
| improvement | pie | m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | output_tok_s | 88.69 | +44.6% | ±43.9% | 29965cf7bcaa2ab8354c340a5d212c4ebc2bdb86 |
