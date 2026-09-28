# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-48g | qwen3.6-27b-mlx4 | control-aa | text-completion-bench | tp1 | decode_tok_s | 32.53 | -5.8% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 32.83 | -4.9% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| regression | pie | m5-max-48g | qwen3.6-27b-mlx4 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 31.58 | -4.8% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | control-aa | text-completion-bench | tp1 | decode_tok_s | 32.82 | -4.7% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| regression | pie | m5-max-48g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | decode_tok_s | 31.32 | -4.6% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| regression | pie | m5-max-128g | qwen3.6-27b-mlx4 | lc-2k-128 | text-completion-bench | tp1 | decode_tok_s | 31.9 | -2.9% | ±2.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| improvement | pie | m5-max-48g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | output_tok_s | 76.04 | +23.4% | ±5.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| improvement | pie | m5-max-48g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | output_tok_s | 76.58 | +23.5% | ±5.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| improvement | pie | m5-max-128g | qwen3.6-27b-mlx4 | c32 | text-completion-bench | tp1 | output_tok_s | 78.17 | +26.1% | ±5.3% | ce1e0015cf1acbce51c7a3133219f01378020760 |
| improvement | pie | m5-max-128g | qwen3.6-27b-mlx4 | c8 | text-completion-bench | tp1 | output_tok_s | 86.91 | +38.5% | ±8.0% | ce1e0015cf1acbce51c7a3133219f01378020760 |
