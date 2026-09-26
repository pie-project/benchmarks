# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | output_tok_s | 3467 | -9.2% | ±7.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| regression | pie | rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | output_tok_s | 1587 | -8.7% | ±8.6% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | output_tok_s | 2039 | -8.0% | ±5.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | pie | l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | decode_tok_s | 65.7 | +2.7% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | pie | a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 526.9 | +2.8% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | vllm | rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | cacheback-speculative-decoding | tp1,ngram | output_tok_s | 91.8 | +3.1% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | pie | l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | decode_tok_s | 58.78 | +14.5% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
