# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 442.2 | 1898 | 4.292× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 699.7 | 2982 | 4.262× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 713.4 | 2995 | 4.199× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1396 | 5127 | 3.674× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4320 | 1.179e+04 | 2.729× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 171.7 | 460.8 | 2.683× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 870.6 | 2333 | 2.680× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1396 | 3715 | 2.661× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9393 | 2.332e+04 | 2.482× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4999 | 1.196e+04 | 2.393× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.499e+04 | 5.406e+04 | 2.163× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7591 | 1.613e+04 | 2.125× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.438e+04 | 3.033e+04 | 2.109× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8940 | 1.875e+04 | 2.098× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3787 | 7783 | 2.055× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.254e+04 | 2.564e+04 | 2.044× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4243 | 8444 | 1.990× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 671 | 1303 | 1.942× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1281 | 2484 | 1.939× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4022 | 7780 | 1.934× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3436 | 6571 | 1.913× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.002e+04 | 1.91e+04 | 1.906× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1904 | 3619 | 1.901× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 308.7 | 563 | 1.824× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1256 | 2237 | 1.781× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9393 | 1.664e+04 | 1.772× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.002e+04 | 1.773e+04 | 1.770× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4243 | 7475 | 1.762× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1938 | 3372 | 1.740× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.485e+04 | 2.527e+04 | 1.701× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.499e+04 | 4.19e+04 | 1.677× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 200.4 | 325.3 | 1.623× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 51.96 | 83.94 | 1.616× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 540.1 | 868 | 1.607× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.274e+04 | 3.632e+04 | 1.597× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 61.35 | 96.78 | 1.577× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 98.03 | 152.5 | 1.555× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 423.4 | 647.8 | 1.530× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 59.78 | 90.87 | 1.520× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121.6 | 183.6 | 1.510× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 70.2 | 105 | 1.496× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 137.6 | 204.7 | 1.487× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7591 | 1.126e+04 | 1.484× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3498 | 5163 | 1.476× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 43.33 | 63.95 | 1.476× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 150.8 | 222.3 | 1.474× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 870.6 | 1281 | 1.472× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 154.2 | 225.5 | 1.462× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 990.9 | 1449 | 1.462× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 237.7 | 342 | 1.439× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5721 | 8214 | 1.436× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1872 | 2664 | 1.423× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 118.9 | 169.1 | 1.422× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 267.5 | 380.5 | 1.422× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3390 | 4796 | 1.415× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3583 | 5047 | 1.409× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7607 | 1.065e+04 | 1.400× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 98.03 | 136 | 1.388× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1175 | 1624 | 1.381× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.33 | 59.59 | 1.375× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 70.83 | 97.29 | 1.374× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.9 | 163.2 | 1.372× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7607 | 1.036e+04 | 1.361× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 182.9 | 248.9 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.362e+04 | 1.845e+04 | 1.354× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1969 | 2650 | 1.346× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3787 | 5044 | 1.332× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 452.3 | 602.2 | 1.331× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4271 | 5679 | 1.330× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 474.5 | 627.4 | 1.322× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.9 | 440.1 | 1.318× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5356 | 7044 | 1.315× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.51 | 93.83 | 1.312× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7065 | 9121 | 1.291× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1726 | 2214 | 1.283× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 182.9 | 233 | 1.274× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 74.81 | 94.09 | 1.258× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 77.06 | 96.84 | 1.257× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6551 | 8203 | 1.252× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.9 | 417.7 | 1.251× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.3 | 194.9 | 1.247× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4371 | 5429 | 1.242× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 413.7 | 513.7 | 1.242× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8352 | 1.029e+04 | 1.232× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.3 | 192.1 | 1.229× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 195.7 | 239.7 | 1.225× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.75 | 99.98 | 1.223× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.7 | 505.5 | 1.222× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 507.4 | 619.8 | 1.221× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.837e+04 | 2.221e+04 | 1.209× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 51.96 | 62.43 | 1.202× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 376.7 | 452 | 1.200× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7065 | 8439 | 1.194× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 217.9 | 258.5 | 1.187× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 367.9 | 433.6 | 1.179× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 550.6 | 647.6 | 1.176× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.837e+04 | 2.157e+04 | 1.174× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 195.7 | 229.6 | 1.173× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 61.35 | 71.76 | 1.170× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 37.88 | 44.29 | 1.169× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6198 | 7230 | 1.166× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.5 | 116.9 | 1.164× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.95 | 105.5 | 1.161× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 238 | 275.7 | 1.159× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1726 | 1999 | 1.158× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 271.4 | 1.155× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 237.7 | 274.5 | 1.155× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 425.1 | 490.5 | 1.154× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 91.55 | 105.5 | 1.153× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 587.2 | 675.7 | 1.151× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.62 | 35.16 | 1.148× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 59.78 | 68.1 | 1.139× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 120.7 | 137.5 | 1.139× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1479 | 1678 | 1.135× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5426 | 6152 | 1.134× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 302.7 | 343.1 | 1.133× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 507.4 | 574.4 | 1.132× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 581.8 | 657.1 | 1.129× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 374.1 | 421.7 | 1.127× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1455 | 1634 | 1.123× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 418.5 | 467.5 | 1.117× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 311.9 | 347.6 | 1.114× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 575 | 639.8 | 1.113× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 401 | 445.8 | 1.112× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 409.9 | 455.6 | 1.111× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 62.71 | 69.48 | 1.108× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 622.5 | 686.5 | 1.103× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 132.8 | 146.4 | 1.102× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 217.9 | 240 | 1.102× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.284e+04 | 1.41e+04 | 1.098× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4103 | 4485 | 1.093× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4371 | 4776 | 1.093× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.6 | 601.3 | 1.092× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 657.7 | 718.2 | 1.092× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 429.2 | 466.9 | 1.088× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 581.8 | 631.9 | 1.086× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3694 | 4006 | 1.085× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 646.8 | 700.9 | 1.084× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 332.9 | 359.8 | 1.081× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 327.5 | 352 | 1.075× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 414.3 | 444.8 | 1.074× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 143.9 | 154.5 | 1.074× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 141.5 | 151.9 | 1.073× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 549.4 | 586.6 | 1.068× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 347.4 | 369.6 | 1.064× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 587.2 | 621.9 | 1.059× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.8 | 121.5 | 1.058× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 238 | 251.6 | 1.057× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 461.1 | 485.2 | 1.052× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 450.4 | 472.9 | 1.050× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 234.9 | 246.4 | 1.049× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 29.4 | 30.81 | 1.048× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.4 | 370.4 | 1.048× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 622.5 | 650.1 | 1.044× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 343.9 | 359.1 | 1.044× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 367.9 | 383.2 | 1.042× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 431 | 446.3 | 1.036× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.268e+04 | 2.347e+04 | 1.035× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.568e+04 | 1.62e+04 | 1.033× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 70.83 | 73.06 | 1.032× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 554.7 | 569.2 | 1.026× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 575 | 586.9 | 1.021× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 657.7 | 669.6 | 1.018× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 646.8 | 656.2 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 587.4 | 594.3 | 1.012× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.1 | 127.5 | 1.011× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 24.48 | 24.65 | 1.007× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.17 | 75.18 | 1.000× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 627.8 | 627.5 | 0.999× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1142 | 1137 | 0.996× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4573 | 4527 | 0.990× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 340.4 | 335.6 | 0.986× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 401 | 394.5 | 0.984× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.6 | 131.8 | 0.979× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6198 | 6064 | 0.978× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 607.1 | 593.6 | 0.978× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 422.1 | 411.6 | 0.975× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 136 | 132.4 | 0.974× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3498 | 3404 | 0.973× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.158e+04 | 1.122e+04 | 0.969× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2924 | 2828 | 0.967× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.416e+04 | 1.368e+04 | 0.966× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.71 | 78.02 | 0.955× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.158e+04 | 1.105e+04 | 0.954× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.254e+04 | 1.196e+04 | 0.953× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 429.2 | 407.8 | 0.950× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2427 | 2299 | 0.947× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1454 | 1375 | 0.946× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 376.7 | 353.6 | 0.939× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 587.4 | 548.4 | 0.934× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2216 | 2068 | 0.933× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3390 | 3109 | 0.917× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6216 | 5672 | 0.913× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 607.1 | 552.3 | 0.910× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 95.18 | 85.57 | 0.899× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.913e+04 | 2.603e+04 | 0.894× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 311.9 | 276.5 | 0.886× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4573 | 3993 | 0.873× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5356 | 4672 | 0.872× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.243e+04 | 1.079e+04 | 0.868× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.73 | 59.74 | 0.857× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 418.5 | 355.6 | 0.850× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 105.4 | 89.45 | 0.849× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.95 | 76.6 | 0.842× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 332.9 | 278.7 | 0.837× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.4 | 294.3 | 0.833× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 91.55 | 75.26 | 0.822× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7860 | 6460 | 0.822× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.913e+04 | 2.374e+04 | 0.815× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 113.4 | 91.96 | 0.811× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 461.1 | 373.8 | 0.811× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7860 | 6303 | 0.802× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.9 | 91.52 | 0.797× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.284e+04 | 1.012e+04 | 0.788× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.116e+04 | 1.658e+04 | 0.784× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 904.9 | 693 | 0.766× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1455 | 1110 | 0.763× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 431 | 327.7 | 0.760× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.116e+04 | 1.593e+04 | 0.753× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.485e+04 | 1.103e+04 | 0.743× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.4e+04 | 1.027e+04 | 0.734× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6043 | 4404 | 0.729× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 422.1 | 304.3 | 0.721× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5709 | 4107 | 0.720× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9215 | 6523 | 0.708× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4850 | 3431 | 0.708× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5709 | 3929 | 0.688× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3694 | 2511 | 0.680× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.202e+04 | 8150 | 0.678× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.126e+04 | 1.419e+04 | 0.668× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.146e+04 | 7437 | 0.649× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.146e+04 | 7291 | 0.636× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.729e+04 | 1.095e+04 | 0.633× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3454 | 2183 | 0.632× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6465 | 4049 | 0.626× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 997.1 | 622.8 | 0.625× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.126e+04 | 1.317e+04 | 0.620× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2216 | 1361 | 0.614× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1841 | 1127 | 0.612× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4986 | 3001 | 0.602× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.729e+04 | 1.038e+04 | 0.600× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.116e+04 | 1.266e+04 | 0.598× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.208e+04 | 6846 | 0.567× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4513 | 2358 | 0.523× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5921 | 2939 | 0.496× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3121 | 1505 | 0.482× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5541 | 2659 | 0.480× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 359 | 166.4 | 0.463× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.014e+04 | 4696 | 0.463× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.8 | 180.2 | 0.456× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 440.5 | 193 | 0.438× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5224 | 2264 | 0.433× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.029e+04 | 4415 | 0.429× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.029e+04 | 4364 | 0.424× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 997.1 | 422.5 | 0.424× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.146e+04 | 4742 | 0.414× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3129 | 1293 | 0.413× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3129 | 1282 | 0.410× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3243 | 1310 | 0.404× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9781 | 3912 | 0.400× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 29.4 | 11.64 | 0.396× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6896 | 2704 | 0.392× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1677 | 642.3 | 0.383× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1788 | 680.5 | 0.381× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5921 | 2169 | 0.366× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1990 | 687.8 | 0.346× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9781 | 3360 | 0.343× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6896 | 2333 | 0.338× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1872 | 624.2 | 0.333× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2079 | 688.4 | 0.331× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2559 | 815.2 | 0.319× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8337 | 2630 | 0.315× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.323e+04 | 4134 | 0.312× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 302.7 | 87.35 | 0.289× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3583 | 995.3 | 0.278× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 327.5 | 88.46 | 0.270× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 343.9 | 90.01 | 0.262× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 347.4 | 90.46 | 0.260× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 374.1 | 96.35 | 0.258× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 414.3 | 99.66 | 0.241× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 77.06 | 18.17 | 0.236× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 359 | 83.09 | 0.231× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4271 | 987.6 | 0.231× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 449.5 | 102 | 0.227× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 450.4 | 101.6 | 0.226× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 549.4 | 120.1 | 0.219× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.4e+04 | 3024 | 0.216× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4720 | 873.8 | 0.185× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 132.8 | 21.29 | 0.160× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 141.5 | 21.71 | 0.153× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1142 | 159 | 0.139× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.323e+04 | 1411 | 0.107× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5224 | 524.3 | 0.100× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3454 | 288 | 0.083× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4850 | 369.2 | 0.076× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 442.2 | 23.39 | 0.053× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1990 | 95.16 | 0.048× | **NO** | competitive |
