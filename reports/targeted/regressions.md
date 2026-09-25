# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-48g | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 245.7 | -6.8% | ±1.6% | d5ae100753997bf67e3ad05d5c5df3f5b0626a73 |
