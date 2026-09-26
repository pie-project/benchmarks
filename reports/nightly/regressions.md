# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | output_tok_s | 9919 | -4.8% | ±4.4% | e12917c6cafe36afb146a403b853380b773593ba |
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | output_tok_s | 2144 | -3.3% | ±1.7% | e12917c6cafe36afb146a403b853380b773593ba |
| regression | pie | a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | decode_tok_s | 493.7 | -1.2% | ±1.1% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | pie | pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 647.5 | +1.1% | ±1.0% | 981b18774c08e001e92e7c627cb15956fc24180f |
| improvement | pie | a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 526.9 | +2.8% | ±1.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
