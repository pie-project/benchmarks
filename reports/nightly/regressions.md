# Regressions / improvements

| kind | engine | platform | artifact | workload | program | mode | metric | value | Δ | threshold | commit/version |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | output_tok_s | 3467 | -9.2% | ±7.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| regression | pie | rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | output_tok_s | 1587 | -8.7% | ±8.6% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| regression | pie | l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | output_tok_s | 2039 | -8.0% | ±5.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| regression | pie | l40s-x2 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp2 | decode_tok_s | 102.2 | -5.2% | ±2.0% | 1655d32dc9e55347f81dcb2511b75baf1e0fb5f8 |
| regression | pie | l40s-x2 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp2 | decode_tok_s | 101.1 | -5.1% | ±3.6% | 1655d32dc9e55347f81dcb2511b75baf1e0fb5f8 |
| improvement | pie | a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | decode_tok_s | 526.9 | +2.8% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
| improvement | vllm | rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | cacheback-speculative-decoding | tp1,ngram | output_tok_s | 91.8 | +3.1% | ±2.0% | d89cedc09a48f25e58b9d587ce3ec8035a8212d7 |
