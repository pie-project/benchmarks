# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rtx5090-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 699.7 | 2982 | 4.262× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 451.8 | 1898 | 4.201× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 713.4 | 2995 | 4.199× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 552 | 2087 | 3.781× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1396 | 5127 | 3.674× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1953 | 6642 | 3.401× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6076 | 2.018e+04 | 3.321× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2881 | 9323 | 3.236× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5811 | 1.818e+04 | 3.128× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3418 | 1.01e+04 | 2.956× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.08e+04 | 3.033e+04 | 2.810× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1575 | 4418 | 2.804× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4291 | 1.183e+04 | 2.757× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 171.7 | 460.8 | 2.683× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 870.6 | 2333 | 2.680× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8428 | 2.248e+04 | 2.667× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1396 | 3715 | 2.661× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1575 | 4033 | 2.560× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9393 | 2.332e+04 | 2.482× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4966 | 1.221e+04 | 2.458× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 636 | 1548 | 2.434× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.19 | 72.87 | 2.414× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 30.19 | 71.38 | 2.364× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3590 | 8444 | 2.352× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1974 | 4539 | 2.299× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8428 | 1.882e+04 | 2.233× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 558.1 | 1226 | 2.197× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 894.1 | 1953 | 2.184× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.499e+04 | 5.406e+04 | 2.163× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 552 | 1184 | 2.145× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8982 | 1.91e+04 | 2.127× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7591 | 1.613e+04 | 2.125× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2447 | 5140 | 2.101× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1194 | 2508 | 2.100× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3590 | 7475 | 2.082× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5672 | 1.174e+04 | 2.070× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3787 | 7783 | 2.055× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 982.5 | 1983 | 2.018× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1231 | 2484 | 2.017× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2603 | 5170 | 1.986× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 465.1 | 918.7 | 1.975× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8982 | 1.773e+04 | 1.974× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3974 | 7780 | 1.958× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5870 | 1.146e+04 | 1.953× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4211 | 8214 | 1.951× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 262.6 | 505.6 | 1.925× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.259e+04 | 2.423e+04 | 1.924× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3428 | 6571 | 1.917× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 680.9 | 1303 | 1.914× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1916 | 3619 | 1.889× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1008 | 1900 | 1.885× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.07 | 162.4 | 1.865× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.07 | 162.2 | 1.863× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 674.5 | 1237 | 1.834× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4734 | 8671 | 1.832× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3780 | 6756 | 1.787× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2913 | 5163 | 1.772× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9393 | 1.664e+04 | 1.772× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 122.4 | 216.1 | 1.765× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1226 | 2095 | 1.710× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1988 | 3372 | 1.696× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.499e+04 | 4.19e+04 | 1.677× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1226 | 2053 | 1.675× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1618 | 2699 | 1.668× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2447 | 4082 | 1.668× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4936 | 8213 | 1.664× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2603 | 4324 | 1.661× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5228 | 8663 | 1.657× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 720.4 | 1187 | 1.648× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 726.2 | 1186 | 1.633× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 534.4 | 867.5 | 1.623× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5228 | 8341 | 1.596× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 546.1 | 868 | 1.589× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 204.8 | 325.3 | 1.588× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 883.3 | 1385 | 1.568× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 97.37 | 152.5 | 1.566× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 946 | 1449 | 1.531× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.611e+04 | 2.464e+04 | 1.529× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 55.17 | 83.94 | 1.521× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121.7 | 183.6 | 1.508× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.224e+04 | 1.845e+04 | 1.507× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4410 | 6643 | 1.506× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1916 | 2871 | 1.498× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7842 | 1.173e+04 | 1.496× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 70.33 | 105 | 1.493× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7591 | 1.126e+04 | 1.484× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 138.2 | 204.7 | 1.481× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 150.1 | 222.3 | 1.481× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 43.33 | 63.95 | 1.476× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 870.6 | 1281 | 1.472× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 154.1 | 225.5 | 1.463× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 234.9 | 342 | 1.456× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 73.34 | 105.6 | 1.441× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.45 | 90.87 | 1.432× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 118.9 | 169.1 | 1.422× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3390 | 4796 | 1.415× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 51.13 | 72.09 | 1.410× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2488 | 3488 | 1.402× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 145.5 | 203.8 | 1.401× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7607 | 1.065e+04 | 1.400× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 97.37 | 136 | 1.397× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 273 | 380.5 | 1.394× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2139 | 2979 | 1.392× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.33 | 59.59 | 1.375× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.9 | 163.2 | 1.372× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2442 | 3347 | 1.370× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6023 | 8206 | 1.363× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7607 | 1.036e+04 | 1.361× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 182.9 | 248.9 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.52 | 97.29 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 461.3 | 627.4 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1950 | 2650 | 1.359× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 107.9 | 146.5 | 1.358× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.29 | 96.78 | 1.357× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 222.1 | 300.8 | 1.354× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6023 | 8155 | 1.354× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1200 | 1624 | 1.353× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 38.65 | 52.11 | 1.348× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 421.9 | 563 | 1.334× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3787 | 5044 | 1.332× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 473.6 | 629.5 | 1.329× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 443.8 | 586.8 | 1.322× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.6 | 133 | 1.322× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.9 | 440.1 | 1.318× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.51 | 93.83 | 1.312× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 179.7 | 235 | 1.308× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 982.5 | 1282 | 1.305× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 461.7 | 602.2 | 1.304× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.3 | 129.7 | 1.293× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7065 | 9121 | 1.291× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1726 | 2214 | 1.283× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2144 | 2749 | 1.282× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 506.6 | 647.8 | 1.279× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4507 | 5754 | 1.277× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 163.6 | 208.7 | 1.276× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 182.9 | 233 | 1.274× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 76.39 | 97.2 | 1.272× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 175.9 | 223.4 | 1.270× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 122.5 | 154.8 | 1.264× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 127.8 | 161.5 | 1.264× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 295.4 | 373.1 | 1.263× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 74.81 | 94.09 | 1.258× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 444.7 | 557.6 | 1.254× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.9 | 417.7 | 1.251× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4507 | 5633 | 1.250× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 210 | 261.9 | 1.247× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.3 | 194.9 | 1.247× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4410 | 5499 | 1.247× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 230.4 | 287 | 1.246× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 51.13 | 63.7 | 1.246× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 413.7 | 513.7 | 1.242× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4515 | 5590 | 1.238× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8352 | 1.029e+04 | 1.232× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.3 | 192.1 | 1.229× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.089e+04 | 1.335e+04 | 1.226× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 195.7 | 239.7 | 1.225× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.75 | 99.98 | 1.223× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.7 | 505.5 | 1.222× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 507.4 | 619.8 | 1.221× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 197.8 | 241.4 | 1.220× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1988 | 2420 | 1.217× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 127.8 | 155.5 | 1.216× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.837e+04 | 2.221e+04 | 1.209× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 374.2 | 452 | 1.208× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3780 | 4539 | 1.201× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 133.4 | 159.9 | 1.199× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 136.4 | 163.3 | 1.198× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7065 | 8439 | 1.194× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3734 | 4452 | 1.192× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 180.5 | 215.1 | 1.192× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.3 | 119.3 | 1.190× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4295 | 5109 | 1.190× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 217.9 | 258.5 | 1.187× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5033 | 5934 | 1.179× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 550.6 | 647.6 | 1.176× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.837e+04 | 2.157e+04 | 1.174× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 195.7 | 229.6 | 1.173× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 443.8 | 519.8 | 1.171× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 473.6 | 554.3 | 1.171× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 37.88 | 44.29 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 274.5 | 1.169× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4123 | 4818 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2913 | 3404 | 1.168× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 38.95 | 45.51 | 1.168× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 359.1 | 419.3 | 1.168× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6198 | 7230 | 1.166× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 152.1 | 177.1 | 1.165× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 115.5 | 134.5 | 1.165× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 24.34 | 28.32 | 1.163× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.95 | 105.5 | 1.161× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.6 | 116.7 | 1.160× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 238 | 275.7 | 1.159× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1726 | 1999 | 1.158× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 201 | 232.7 | 1.158× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 240.2 | 277.6 | 1.156× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 271.4 | 1.155× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3887 | 4485 | 1.154× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 91.55 | 105.5 | 1.153× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 587.2 | 675.7 | 1.151× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121 | 138.7 | 1.146× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5378 | 6152 | 1.144× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.089e+04 | 1.244e+04 | 1.143× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 411 | 467.5 | 1.137× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.96 | 35.16 | 1.136× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1479 | 1678 | 1.135× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 507.4 | 574.4 | 1.132× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 55.17 | 62.43 | 1.132× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 204.8 | 231.6 | 1.131× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.15 | 51.01 | 1.130× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 581.8 | 657.1 | 1.129× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 197.8 | 222.6 | 1.125× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 218.7 | 245.9 | 1.124× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 429.7 | 483.1 | 1.124× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.6 | 47.85 | 1.123× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.39 | 47.37 | 1.117× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 25.54 | 28.43 | 1.113× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 313 | 348.5 | 1.113× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 575 | 639.8 | 1.113× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 392.1 | 436.1 | 1.112× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9919 | 1.101e+04 | 1.110× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 193.3 | 214.5 | 1.110× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 546.1 | 604 | 1.106× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.1 | 146.9 | 1.104× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 622.5 | 686.5 | 1.103× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 127.1 | 140.2 | 1.103× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 217.9 | 240 | 1.102× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 50.77 | 55.8 | 1.099× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 206.7 | 226.9 | 1.098× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.9 | 604.5 | 1.097× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 67.71 | 74.24 | 1.096× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9919 | 1.087e+04 | 1.096× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.8 | 125.6 | 1.094× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 227.5 | 248.6 | 1.092× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 444.7 | 485.7 | 1.092× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.6 | 601.3 | 1.092× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 657.7 | 718.2 | 1.092× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.66 | 69.48 | 1.092× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1873 | 2042 | 1.090× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 581.8 | 631.9 | 1.086× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3693 | 4010 | 1.086× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 469.1 | 508.8 | 1.085× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3022 | 3277 | 1.084× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 646.8 | 700.9 | 1.084× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1509 | 1634 | 1.083× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.25 | 48.83 | 1.079× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 425 | 458 | 1.078× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 335.4 | 360.6 | 1.075× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 63.45 | 68.1 | 1.073× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.7 | 154.8 | 1.070× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.2 | 441.9 | 1.069× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1287 | 1375 | 1.069× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 321.2 | 343.1 | 1.068× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142.8 | 152.5 | 1.068× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 109.5 | 116.9 | 1.068× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 509.3 | 543.4 | 1.067× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.26 | 48.29 | 1.067× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 454.7 | 485.2 | 1.067× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 225 | 239.7 | 1.065× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 28.71 | 30.52 | 1.063× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 210 | 223.2 | 1.063× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 421.3 | 446.3 | 1.059× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 79.6 | 84.32 | 1.059× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 587.2 | 621.9 | 1.059× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1938 | 2052 | 1.059× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 193.3 | 204.6 | 1.058× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.8 | 121.5 | 1.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 137.5 | 145.5 | 1.058× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 238 | 251.6 | 1.057× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 399 | 421.7 | 1.057× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1938 | 2042 | 1.054× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 426.1 | 447.6 | 1.050× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 451.6 | 474 | 1.050× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.029e+04 | 1.079e+04 | 1.049× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 234.9 | 246.4 | 1.049× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 438.6 | 460.1 | 1.049× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.6 | 370.8 | 1.049× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 135.1 | 141.3 | 1.046× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.8 | 369.6 | 1.045× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 622.5 | 650.1 | 1.044× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 284.5 | 296.7 | 1.043× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 344.6 | 359.1 | 1.042× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 338.3 | 352 | 1.040× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 206.7 | 214.1 | 1.036× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3796 | 3927 | 1.034× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 339.4 | 351 | 1.034× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 230.4 | 237.1 | 1.029× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1151 | 1183 | 1.028× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 557 | 572.1 | 1.027× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 71.52 | 73.06 | 1.022× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 575 | 586.9 | 1.021× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 76.98 | 78.54 | 1.020× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 657.7 | 669.6 | 1.018× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 227.9 | 231.9 | 1.018× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.105e+04 | 1.122e+04 | 1.016× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 646.8 | 656.2 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 589.6 | 597.6 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 107.9 | 109.3 | 1.013× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.1 | 127.5 | 1.011× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 413.2 | 417.6 | 1.011× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 623.2 | 628.8 | 1.009× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 71.29 | 71.76 | 1.007× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 24.55 | 24.65 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 600.2 | 601.3 | 1.002× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.105e+04 | 1.105e+04 | 1.000× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 410.6 | 409.8 | 0.998× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 225 | 223.9 | 0.995× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.6 | 131.8 | 0.979× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6198 | 6064 | 0.978× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 7951 | 7759 | 0.976× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 136 | 132.4 | 0.974× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 128.2 | 124.2 | 0.969× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 227.9 | 220.3 | 0.967× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4566 | 4404 | 0.965× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2144 | 2058 | 0.960× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 85.68 | 82.23 | 0.960× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2009 | 1926 | 0.958× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 62.95 | 60.22 | 0.957× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 313 | 299.2 | 0.956× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1758 | 1678 | 0.955× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 557 | 531.6 | 0.954× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.537e+04 | 1.453e+04 | 0.946× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 374.2 | 353.6 | 0.945× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 84.86 | 79.98 | 0.943× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 122.5 | 115.4 | 0.942× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 589.6 | 550.7 | 0.934× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 600.2 | 554.9 | 0.924× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 66.93 | 61.87 | 0.924× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3066 | 2828 | 0.922× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 623.2 | 573.5 | 0.920× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 359.1 | 329.3 | 0.917× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3390 | 3109 | 0.917× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 110.4 | 100.8 | 0.913× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6216 | 5672 | 0.913× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.58 | 68.66 | 0.908× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9544 | 8661 | 0.907× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 335.4 | 303.5 | 0.905× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.76 | 62.88 | 0.901× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 95.35 | 85.57 | 0.897× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.98 | 62.76 | 0.897× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1884 | 1685 | 0.895× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.913e+04 | 2.603e+04 | 0.894× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.6 | 314.7 | 0.890× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.4 | 112.3 | 0.888× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1677 | 1483 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.9 | 103.3 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.2 | 117.7 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.3 | 118.7 | 0.883× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 133.4 | 117.5 | 0.881× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4123 | 3630 | 0.880× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 117.9 | 103.7 | 0.880× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.96 | 71.59 | 0.873× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1950 | 1689 | 0.866× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 411 | 355.6 | 0.865× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.75 | 72.84 | 0.860× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.2 | 105.9 | 0.859× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 122.4 | 105 | 0.858× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1134 | 971.6 | 0.857× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3693 | 3145 | 0.852× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 105.1 | 89.45 | 0.851× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 339.4 | 287.8 | 0.848× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 392.1 | 332.3 | 0.847× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.91 | 73.49 | 0.846× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.95 | 76.6 | 0.842× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.15 | 73.21 | 0.840× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 425 | 354.3 | 0.834× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 454.7 | 373.8 | 0.822× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 91.55 | 75.26 | 0.822× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7860 | 6460 | 0.822× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 38.95 | 31.76 | 0.815× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.913e+04 | 2.374e+04 | 0.815× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 113.2 | 91.96 | 0.812× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7860 | 6303 | 0.802× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.4 | 91.52 | 0.800× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.004e+04 | 1.589e+04 | 0.793× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 42.39 | 33.33 | 0.786× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.116e+04 | 1.658e+04 | 0.784× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 421.3 | 327.7 | 0.778× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 904.9 | 693 | 0.766× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1873 | 1433 | 0.765× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.25 | 34.6 | 0.765× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.299e+04 | 9874 | 0.760× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.116e+04 | 1.593e+04 | 0.753× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 41.92 | 31.44 | 0.750× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.26 | 33.9 | 0.749× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3734 | 2783 | 0.745× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 410.6 | 302.3 | 0.736× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1509 | 1110 | 0.736× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.914e+04 | 1.393e+04 | 0.728× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5709 | 4107 | 0.720× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 222.1 | 158.4 | 0.713× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.145e+04 | 7921 | 0.692× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1404 | 967.6 | 0.689× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5067 | 3490 | 0.689× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5709 | 3929 | 0.688× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.145e+04 | 7863 | 0.687× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.611e+04 | 1.103e+04 | 0.685× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.299e+04 | 8888 | 0.684× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9544 | 6523 | 0.684× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.202e+04 | 8208 | 0.683× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.126e+04 | 1.419e+04 | 0.668× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 550.9 | 367.3 | 0.667× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 936 | 622.8 | 0.665× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6090 | 4049 | 0.665× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5694 | 3778 | 0.663× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7835 | 5181 | 0.661× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3650 | 2358 | 0.646× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.729e+04 | 1.095e+04 | 0.633× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3593 | 2258 | 0.629× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.126e+04 | 1.317e+04 | 0.620× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1851 | 1127 | 0.609× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4986 | 3001 | 0.602× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.729e+04 | 1.038e+04 | 0.600× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.456e+04 | 8698 | 0.598× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6269 | 3728 | 0.595× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.331e+04 | 7597 | 0.571× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2244 | 1246 | 0.555× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5090 | 2761 | 0.542× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3343 | 1768 | 0.529× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5661 | 2939 | 0.519× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.014e+04 | 5241 | 0.517× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2063 | 1045 | 0.506× | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2246 | 1125 | 0.501× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7473 | 3606 | 0.483× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3287 | 1578 | 0.480× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6269 | 2974 | 0.474× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1758 | 822.1 | 0.468× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 359 | 162.5 | 0.453× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 409.9 | 185.5 | 0.453× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 936 | 422.5 | 0.451× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.8 | 176.5 | 0.447× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 440.5 | 190.7 | 0.433× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.029e+04 | 4415 | 0.429× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 748.3 | 320.4 | 0.428× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.029e+04 | 4364 | 0.424× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 114.8 | 48.14 | 0.419× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3129 | 1293 | 0.413× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9567 | 3931 | 0.411× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3129 | 1282 | 0.410× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3243 | 1323 | 0.408× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5635 | 2285 | 0.406× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 28.71 | 11.64 | 0.405× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9781 | 3912 | 0.400× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5661 | 2169 | 0.383× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6000 | 2264 | 0.377× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3026 | 1139 | 0.376× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3026 | 1139 | 0.376× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1404 | 520.3 | 0.370× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2593 | 940.5 | 0.363× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1983 | 698.3 | 0.352× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2063 | 723.5 | 0.351× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9781 | 3360 | 0.343× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5635 | 1859 | 0.330× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 240.2 | 78.44 | 0.327× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2559 | 815.2 | 0.319× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8337 | 2641 | 0.317× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1687 | 528.2 | 0.313× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6281 | 1965 | 0.313× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.323e+04 | 4137 | 0.313× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2312 | 680.5 | 0.294× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 321.2 | 87.35 | 0.272× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 748.3 | 201.6 | 0.269× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 338.3 | 88.46 | 0.261× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 344.6 | 90.01 | 0.261× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.8 | 90.46 | 0.256× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2454 | 624.2 | 0.254× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 399 | 96.35 | 0.242× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 76.39 | 18.17 | 0.238× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 426.1 | 99.66 | 0.234× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 438.6 | 102 | 0.233× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4295 | 995.3 | 0.232× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 359 | 83.09 | 0.231× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 451.6 | 101.6 | 0.225× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4515 | 987.6 | 0.219× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 558.1 | 120.1 | 0.215× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4720 | 858.4 | 0.182× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 133.1 | 21.29 | 0.160× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142.8 | 21.71 | 0.152× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1151 | 159 | 0.138× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.323e+04 | 1411 | 0.107× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6000 | 524.3 | 0.087× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.914e+04 | 1575 | 0.082× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3593 | 288 | 0.080× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 154.1 | 12.24 | 0.079× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 150.1 | 11.72 | 0.078× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 70.33 | 5.338 | 0.076× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 121.7 | 9.099 | 0.075× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 138.2 | 10.28 | 0.074× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5067 | 369.2 | 0.073× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 451.8 | 23.39 | 0.052× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1983 | 95.16 | 0.048× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1851 | 47.11 | 0.025× | **NO** | competitive |
