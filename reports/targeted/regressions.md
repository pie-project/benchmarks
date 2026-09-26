# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 249.7 | -4.6% | ±2.9% | 647abfcb7e6b4c99634c001241b2ba8751d42f16 |
