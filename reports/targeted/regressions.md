# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | m5-max-48g | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 273.2 | -2.7% | ±1.4% | ca2d8f78d82696e9f023a56a39681b87c82525c6 |
