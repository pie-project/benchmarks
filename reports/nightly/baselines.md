# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1859 | 8505 | 4.575× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5965 | 2.72e+04 | 4.560× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1866 | 7975 | 4.275× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 699.7 | 2982 | 4.262× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3343 | 1.41e+04 | 4.216× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 451.8 | 1898 | 4.201× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 713.4 | 2995 | 4.199× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 805.8 | 3282 | 4.073× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2364 | 9323 | 3.944× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2364 | 9207 | 3.895× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 552 | 2087 | 3.781× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1396 | 5127 | 3.674× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 412.8 | 1483 | 3.592× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1632 | 5811 | 3.561× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5799 | 1.98e+04 | 3.414× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1953 | 6642 | 3.401× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5380 | 1.818e+04 | 3.379× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5380 | 1.767e+04 | 3.285× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 839.1 | 2610 | 3.110× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2230 | 6715 | 3.011× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3360 | 1.01e+04 | 3.007× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4177 | 1.232e+04 | 2.950× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4177 | 1.185e+04 | 2.838× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.08e+04 | 3.033e+04 | 2.810× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1575 | 4412 | 2.801× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1632 | 4539 | 2.782× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4291 | 1.183e+04 | 2.757× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 475.4 | 1300 | 2.734× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 171.7 | 460.8 | 2.683× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 870.6 | 2333 | 2.680× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8428 | 2.248e+04 | 2.667× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1396 | 3715 | 2.661× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 606.5 | 1548 | 2.553× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1575 | 3960 | 2.514× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9393 | 2.332e+04 | 2.482× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4966 | 1.221e+04 | 2.458× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.19 | 72.81 | 2.412× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 390.3 | 933.5 | 2.392× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 30.19 | 71.46 | 2.367× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.642e+04 | 3.879e+04 | 2.363× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 722.5 | 1706 | 2.361× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3590 | 8444 | 2.352× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1950 | 4491 | 2.303× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1795 | 4108 | 2.289× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.4e+04 | 3.203e+04 | 2.288× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8428 | 1.882e+04 | 2.233× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 558.1 | 1226 | 2.197× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 894.1 | 1950 | 2.182× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4966 | 1.077e+04 | 2.168× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.499e+04 | 5.406e+04 | 2.163× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 552 | 1183 | 2.143× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8982 | 1.91e+04 | 2.127× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7591 | 1.613e+04 | 2.125× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5590 | 1.186e+04 | 2.122× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1194 | 2508 | 2.100× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2447 | 5134 | 2.098× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3590 | 7475 | 2.082× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1950 | 4056 | 2.080× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.166e+04 | 2.423e+04 | 2.079× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5546 | 1.146e+04 | 2.067× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3787 | 7783 | 2.055× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1164 | 2382 | 2.047× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2538 | 5170 | 2.037× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1164 | 2370 | 2.037× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1231 | 2484 | 2.017× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1003 | 1983 | 1.976× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8982 | 1.773e+04 | 1.974× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3974 | 7780 | 1.958× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4211 | 8214 | 1.951× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4510 | 8706 | 1.930× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7962 | 1.53e+04 | 1.922× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3428 | 6571 | 1.917× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 262.6 | 503.2 | 1.916× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 680.9 | 1303 | 1.914× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2392 | 4526 | 1.893× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5799 | 1.096e+04 | 1.891× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1916 | 3619 | 1.889× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2465 | 4617 | 1.873× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.07 | 162.2 | 1.863× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.07 | 161.8 | 1.858× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6336 | 1.173e+04 | 1.852× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2006 | 3711 | 1.849× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 674.5 | 1237 | 1.834× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3780 | 6756 | 1.787× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 121.4 | 216.1 | 1.780× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2913 | 5163 | 1.772× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9393 | 1.664e+04 | 1.772× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7962 | 1.401e+04 | 1.759× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1.113e+04 | 1.955e+04 | 1.756× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.43e+04 | 2.464e+04 | 1.723× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1226 | 2095 | 1.709× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1581 | 2699 | 1.708× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2538 | 4321 | 1.703× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1988 | 3372 | 1.696× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1744 | 2950 | 1.692× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.499e+04 | 4.19e+04 | 1.677× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1226 | 2054 | 1.676× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5173 | 8663 | 1.675× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1032 | 1728 | 1.674× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2447 | 4078 | 1.667× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4936 | 8213 | 1.664× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 240.7 | 397.9 | 1.653× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 720.4 | 1187 | 1.648× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 726.2 | 1187 | 1.635× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 341.8 | 553.8 | 1.621× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 361.5 | 585.3 | 1.619× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5173 | 8341 | 1.612× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 546.1 | 868 | 1.589× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 204.8 | 325.3 | 1.588× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 113.5 | 179.5 | 1.582× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 391 | 616.1 | 1.576× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 894.1 | 1408 | 1.575× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 883.3 | 1385 | 1.568× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 97.37 | 152.5 | 1.566× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 240.7 | 373.1 | 1.550× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 360.7 | 553.2 | 1.534× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 946 | 1449 | 1.531× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 180 | 275.5 | 1.530× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 55.17 | 83.94 | 1.521× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4372 | 6643 | 1.519× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121.7 | 183.6 | 1.508× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.224e+04 | 1.845e+04 | 1.507× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1916 | 2871 | 1.498× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 67.71 | 101.2 | 1.495× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 198.2 | 296.1 | 1.493× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 70.33 | 105 | 1.493× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 207.5 | 309.4 | 1.491× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 341.8 | 509.2 | 1.490× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8879 | 1.322e+04 | 1.489× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7591 | 1.126e+04 | 1.484× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 138.2 | 204.7 | 1.481× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 150.1 | 222.3 | 1.481× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 43.33 | 63.95 | 1.476× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 870.6 | 1281 | 1.472× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 154.1 | 225.5 | 1.463× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 217.1 | 316.4 | 1.458× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 234.9 | 342 | 1.456× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 180 | 261 | 1.450× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6543 | 9450 | 1.444× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1229 | 1768 | 1.438× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 361.5 | 519.8 | 1.438× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.45 | 90.87 | 1.432× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 49.9 | 71.4 | 1.431× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 118.9 | 169.1 | 1.422× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 391 | 554.3 | 1.418× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3390 | 4796 | 1.415× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 130.1 | 183.5 | 1.410× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 113.5 | 159.8 | 1.409× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 76.98 | 108.1 | 1.404× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 145.5 | 203.8 | 1.401× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7607 | 1.065e+04 | 1.400× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 97.37 | 136 | 1.397× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 273 | 380.5 | 1.394× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 839.1 | 1169 | 1.393× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1879 | 2585 | 1.376× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.33 | 59.59 | 1.375× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 217.1 | 298.4 | 1.375× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.9 | 163.2 | 1.372× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2442 | 3344 | 1.369× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 9092 | 1.242e+04 | 1.366× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 9092 | 1.241e+04 | 1.365× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2006 | 2739 | 1.365× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6023 | 8206 | 1.363× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7607 | 1.036e+04 | 1.361× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 130.1 | 177.1 | 1.361× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 222.1 | 302.2 | 1.361× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 182.9 | 248.9 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.52 | 97.29 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 461.3 | 627.4 | 1.360× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1950 | 2650 | 1.359× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 107.9 | 146.5 | 1.358× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.29 | 96.78 | 1.357× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2570 | 3488 | 1.357× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6023 | 8155 | 1.354× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2039 | 2749 | 1.349× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 73.31 | 98.85 | 1.348× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 360.7 | 485.7 | 1.346× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 53.73 | 72.35 | 1.346× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4824 | 6481 | 1.343× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2570 | 3443 | 1.340× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4175 | 5590 | 1.339× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 85.68 | 114.6 | 1.337× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4601 | 6152 | 1.337× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 421.9 | 563 | 1.334× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.545e+04 | 2.059e+04 | 1.333× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3787 | 5044 | 1.332× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.8 | 134.1 | 1.331× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.9 | 440.1 | 1.318× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 71.51 | 93.83 | 1.312× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 179.7 | 235 | 1.308× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 461.7 | 602.2 | 1.304× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4436 | 5754 | 1.297× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7065 | 9121 | 1.291× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.6 | 162.8 | 1.286× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 262.6 | 337.3 | 1.284× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3469 | 4452 | 1.283× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1726 | 2214 | 1.283× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.86 | 108.8 | 1.282× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 420.1 | 538.5 | 1.282× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 506.6 | 647.8 | 1.279× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1003 | 1282 | 1.278× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 49.9 | 63.7 | 1.277× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 101.7 | 129.7 | 1.276× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 163.6 | 208.7 | 1.276× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 182.9 | 233 | 1.274× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 76.39 | 97.2 | 1.272× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 175.9 | 223.4 | 1.270× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 207.5 | 263.4 | 1.270× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4436 | 5631 | 1.269× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 122.5 | 154.8 | 1.264× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4372 | 5499 | 1.258× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 74.81 | 94.09 | 1.258× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.9 | 417.7 | 1.251× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 155.9 | 194.8 | 1.250× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.3 | 194.9 | 1.247× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 413.7 | 513.7 | 1.242× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3886 | 4818 | 1.240× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 277.3 | 343.1 | 1.237× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211.8 | 261.9 | 1.237× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 232.6 | 287 | 1.234× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8352 | 1.029e+04 | 1.232× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.3 | 192.1 | 1.229× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 126.6 | 155.5 | 1.228× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 195.7 | 239.7 | 1.225× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.75 | 99.98 | 1.223× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.7 | 505.5 | 1.222× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 507.4 | 619.8 | 1.221× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 197.8 | 241.4 | 1.220× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1988 | 2420 | 1.217× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.1e+04 | 1.335e+04 | 1.213× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.837e+04 | 2.221e+04 | 1.209× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 374.2 | 452 | 1.208× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 870.3 | 1049 | 1.206× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4369 | 5248 | 1.201× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3780 | 4539 | 1.201× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 233.9 | 280.8 | 1.200× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 133.4 | 159.9 | 1.199× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4264 | 5112 | 1.199× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 136.4 | 163.3 | 1.198× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 179.7 | 215.1 | 1.197× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7065 | 8439 | 1.194× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 206.2 | 245.9 | 1.192× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 217.9 | 258.5 | 1.187× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 196.7 | 232.7 | 1.183× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 38.64 | 45.57 | 1.179× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 317.9 | 374.6 | 1.178× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5033 | 5928 | 1.178× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 550.6 | 647.6 | 1.176× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 208.4 | 244.7 | 1.174× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.837e+04 | 2.157e+04 | 1.174× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 101.7 | 119.3 | 1.174× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 195.7 | 229.6 | 1.173× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 88.97 | 104.2 | 1.172× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 37.88 | 44.29 | 1.169× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 53.73 | 62.83 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 274.5 | 1.169× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 361.5 | 422.4 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2913 | 3404 | 1.168× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 38.95 | 45.51 | 1.168× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6198 | 7230 | 1.166× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 115.6 | 134.5 | 1.164× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.95 | 105.5 | 1.161× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 238 | 275.7 | 1.159× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.8 | 116.7 | 1.158× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1726 | 1999 | 1.158× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3467 | 4008 | 1.156× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 271.4 | 1.155× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3887 | 4485 | 1.154× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 91.55 | 105.5 | 1.153× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 587.2 | 675.7 | 1.151× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 720.4 | 828.1 | 1.150× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 44.58 | 51.15 | 1.147× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121 | 138.7 | 1.146× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 411 | 467.5 | 1.137× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.96 | 35.16 | 1.136× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 429.1 | 487 | 1.135× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1479 | 1678 | 1.135× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 507.4 | 574.4 | 1.132× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 55.17 | 62.43 | 1.132× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.1e+04 | 1.244e+04 | 1.131× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 204.8 | 231.6 | 1.131× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 581.8 | 657.1 | 1.129× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 197.8 | 222.6 | 1.125× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.7 | 162.5 | 1.123× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5033 | 5643 | 1.121× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.39 | 47.37 | 1.117× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 313.1 | 348.7 | 1.114× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 575 | 639.8 | 1.113× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 394.3 | 438.2 | 1.111× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 50.38 | 55.8 | 1.107× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 193.7 | 214.5 | 1.107× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 546.1 | 604 | 1.106× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.1 | 146.9 | 1.104× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 622.5 | 686.5 | 1.103× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 127.1 | 140.2 | 1.102× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 217.9 | 240 | 1.102× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.9 | 606.6 | 1.101× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 226 | 248.6 | 1.100× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 67.71 | 74.24 | 1.096× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 453.8 | 497.1 | 1.095× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.76 | 47.85 | 1.094× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2498 | 2730 | 1.093× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.6 | 601.3 | 1.092× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 657.7 | 718.2 | 1.092× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.66 | 69.48 | 1.092× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1873 | 2041 | 1.089× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 162.1 | 176.5 | 1.089× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 26.37 | 28.72 | 1.089× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.013e+04 | 1.101e+04 | 1.087× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 581.8 | 631.9 | 1.086× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.4 | 361.3 | 1.084× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 646.8 | 700.9 | 1.084× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1509 | 1634 | 1.083× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 26.27 | 28.43 | 1.082× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 427.1 | 461 | 1.080× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.25 | 48.83 | 1.079× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.3 | 127.6 | 1.078× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211 | 226.9 | 1.076× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 468.4 | 502.9 | 1.074× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 63.45 | 68.1 | 1.073× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.013e+04 | 1.087e+04 | 1.073× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1914 | 2052 | 1.072× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 193.7 | 207.6 | 1.072× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6543 | 7001 | 1.070× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.7 | 154.8 | 1.070× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 178.3 | 190.7 | 1.070× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.2 | 441.9 | 1.069× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1287 | 1375 | 1.069× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142.8 | 152.5 | 1.068× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 109.5 | 116.9 | 1.068× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.26 | 48.29 | 1.067× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 454.7 | 485.2 | 1.067× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 621 | 660.9 | 1.064× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.7 | 419.7 | 1.063× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 28.71 | 30.52 | 1.063× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 509.2 | 540.9 | 1.062× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 420.2 | 445.7 | 1.061× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 421.3 | 446.3 | 1.059× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 587.2 | 621.9 | 1.059× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1914 | 2027 | 1.059× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 175.3 | 185.5 | 1.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 137.5 | 145.5 | 1.058× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.8 | 121.5 | 1.058× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 238 | 251.6 | 1.057× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 280.8 | 296.7 | 1.057× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 227 | 239.7 | 1.056× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211.8 | 223.2 | 1.054× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 655.8 | 691 | 1.054× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 80.06 | 84.32 | 1.053× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 484.5 | 509.6 | 1.052× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.2 | 370.6 | 1.049× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.029e+04 | 1.079e+04 | 1.049× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 234.9 | 246.4 | 1.049× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 221.3 | 231.9 | 1.048× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.1 | 369.6 | 1.047× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 436.4 | 456 | 1.045× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 622.5 | 650.1 | 1.044× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 135.4 | 141.3 | 1.044× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 515.1 | 536.9 | 1.042× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 338.4 | 352 | 1.040× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 655.8 | 680.9 | 1.038× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.53 | 31.68 | 1.038× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3796 | 3933 | 1.036× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 346.8 | 359.1 | 1.035× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211 | 218 | 1.034× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 340 | 350.9 | 1.032× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6722 | 6933 | 1.031× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 455.8 | 469.3 | 1.030× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1151 | 1183 | 1.028× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 557 | 572.1 | 1.027× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 71.52 | 73.06 | 1.022× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 575 | 586.9 | 1.021× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 76.98 | 78.54 | 1.020× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 232.6 | 237.1 | 1.020× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 657.7 | 669.6 | 1.018× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2039 | 2076 | 1.018× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.105e+04 | 1.122e+04 | 1.016× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 621 | 630.5 | 1.015× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 646.8 | 656.2 | 1.014× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 410.7 | 416.6 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 589.6 | 597.6 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 107.9 | 109.3 | 1.013× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.1 | 127.5 | 1.011× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 413.2 | 417.6 | 1.011× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 221.3 | 223.6 | 1.010× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 623.2 | 628.8 | 1.009× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 494.3 | 498.6 | 1.009× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 71.29 | 71.76 | 1.007× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 24.55 | 24.65 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 600.2 | 601.3 | 1.002× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6722 | 6729 | 1.001× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.105e+04 | 1.105e+04 | 1.000× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.456e+04 | 1.453e+04 | 0.998× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 227 | 223.9 | 0.986× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3796 | 3743 | 0.986× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.6 | 131.8 | 0.979× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6198 | 6064 | 0.978× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 127 | 124.2 | 0.978× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 136 | 132.4 | 0.974× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2009 | 1943 | 0.967× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4566 | 4404 | 0.965× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 671.3 | 647.3 | 0.964× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.648e+04 | 1.589e+04 | 0.964× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4824 | 4651 | 0.964× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 62.62 | 60.22 | 0.962× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 85.68 | 82.25 | 0.960× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 557 | 532.5 | 0.956× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 313.1 | 299.2 | 0.955× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1758 | 1679 | 0.955× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.545e+04 | 1.47e+04 | 0.952× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3582 | 3407 | 0.951× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 737.6 | 699.6 | 0.948× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 374.2 | 353.6 | 0.945× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 84.86 | 79.98 | 0.943× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 122.5 | 115.4 | 0.942× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3886 | 3630 | 0.934× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 589.6 | 548.8 | 0.931× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 600.2 | 557.1 | 0.928× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 66.71 | 61.87 | 0.928× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 623.2 | 575.9 | 0.924× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3066 | 2828 | 0.922× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.11 | 69.23 | 0.922× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3390 | 3109 | 0.917× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6216 | 5672 | 0.913× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 110.9 | 101.1 | 0.911× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.4 | 303.5 | 0.910× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 361.5 | 328.9 | 0.910× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9544 | 8661 | 0.907× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3467 | 3145 | 0.907× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.71 | 62.88 | 0.902× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.72 | 62.76 | 0.900× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1872 | 1685 | 0.900× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 95.35 | 85.57 | 0.897× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.913e+04 | 2.603e+04 | 0.894× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.2 | 314.7 | 0.891× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.4 | 112.3 | 0.888× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.9 | 103.3 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.2 | 117.7 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.3 | 118.7 | 0.883× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.38 | 71.87 | 0.883× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 133.4 | 117.5 | 0.881× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.4 | 104 | 0.878× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.492e+04 | 1.304e+04 | 0.874× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1950 | 1689 | 0.866× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 411 | 355.6 | 0.865× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.75 | 72.99 | 0.861× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.31 | 74.02 | 0.858× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.7 | 105.9 | 0.856× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.4e+04 | 1.196e+04 | 0.854× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.43 | 73.63 | 0.852× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 105.1 | 89.45 | 0.851× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1157 | 983.3 | 0.850× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.8 | 105.2 | 0.850× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 340 | 287.8 | 0.847× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6127 | 5181 | 0.846× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.3 | 333.3 | 0.845× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.95 | 76.6 | 0.842× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 427.1 | 357.5 | 0.837× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 454.7 | 373.8 | 0.822× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 91.55 | 75.26 | 0.822× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7860 | 6460 | 0.822× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 38.95 | 31.76 | 0.815× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.913e+04 | 2.374e+04 | 0.815× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 113.2 | 91.96 | 0.812× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2442 | 1970 | 0.807× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3469 | 2783 | 0.802× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7860 | 6303 | 0.802× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.4 | 91.52 | 0.800× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.288e+04 | 1.023e+04 | 0.794× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 42.39 | 33.33 | 0.786× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1795 | 1411 | 0.786× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.116e+04 | 1.658e+04 | 0.784× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7927 | 6179 | 0.779× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 421.3 | 327.7 | 0.778× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.43e+04 | 1.103e+04 | 0.772× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1873 | 1438 | 0.768× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7927 | 6085 | 0.768× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 904.9 | 693 | 0.766× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.25 | 34.6 | 0.765× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.304e+04 | 9874 | 0.757× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.116e+04 | 1.593e+04 | 0.753× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 41.92 | 31.41 | 0.749× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.26 | 33.9 | 0.749× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 410.7 | 305 | 0.743× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1509 | 1110 | 0.736× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.884e+04 | 1.383e+04 | 0.734× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 7092 | 5147 | 0.726× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5709 | 4107 | 0.720× | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4226 | 3036 | 0.718× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.127e+04 | 7927 | 0.704× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.127e+04 | 7863 | 0.698× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1404 | 968.4 | 0.690× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5067 | 3490 | 0.689× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5709 | 3929 | 0.688× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9544 | 6523 | 0.684× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.304e+04 | 8888 | 0.681× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.284e+04 | 8698 | 0.677× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.126e+04 | 1.419e+04 | 0.668× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 936 | 622.8 | 0.665× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6090 | 4049 | 0.665× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3650 | 2358 | 0.646× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 7092 | 4575 | 0.645× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5532 | 3557 | 0.643× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6017 | 3812 | 0.633× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.729e+04 | 1.095e+04 | 0.633× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3593 | 2258 | 0.629× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2570 | 1606 | 0.625× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2570 | 1593 | 0.620× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.126e+04 | 1.317e+04 | 0.620× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1851 | 1127 | 0.609× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4986 | 3001 | 0.602× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.729e+04 | 1.038e+04 | 0.600× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1223 | 731.3 | 0.598× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 144.7 | 83.09 | 0.574× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9592 | 5408 | 0.564× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.35e+04 | 7609 | 0.564× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2244 | 1246 | 0.555× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9592 | 5241 | 0.546× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5532 | 2974 | 0.538× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5661 | 2939 | 0.519× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2063 | 1045 | 0.506× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.653e+04 | 8334 | 0.504× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.134e+04 | 5602 | 0.494× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 936 | 422.5 | 0.451× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6526 | 2905 | 0.445× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.029e+04 | 4415 | 0.429× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 748.3 | 320.4 | 0.428× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.029e+04 | 4364 | 0.424× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8496 | 3573 | 0.421× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3129 | 1293 | 0.413× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1646 | 680.5 | 0.413× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5547 | 2280 | 0.411× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9567 | 3931 | 0.411× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3129 | 1282 | 0.410× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 118.3 | 48.14 | 0.407× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 28.71 | 11.64 | 0.405× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6672 | 2669 | 0.400× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9781 | 3912 | 0.400× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9567 | 3708 | 0.388× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5661 | 2169 | 0.383× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5931 | 2264 | 0.382× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3011 | 1139 | 0.378× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3011 | 1139 | 0.378× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2593 | 940.5 | 0.363× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1983 | 698.3 | 0.352× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2438 | 858.4 | 0.352× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2063 | 723.5 | 0.351× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9781 | 3360 | 0.343× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1364 | 466.8 | 0.342× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1587 | 532.3 | 0.336× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 233.9 | 78.44 | 0.335× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5547 | 1859 | 0.335× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2559 | 815.2 | 0.319× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 277.3 | 87.35 | 0.315× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2541 | 782.1 | 0.308× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6672 | 1974 | 0.296× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 748.3 | 201.6 | 0.269× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 338.4 | 88.46 | 0.261× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 346.8 | 90.01 | 0.260× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.1 | 90.46 | 0.256× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2465 | 624.2 | 0.253× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 394.7 | 96.35 | 0.244× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 76.39 | 18.17 | 0.238× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 420.2 | 99.66 | 0.237× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4175 | 987.6 | 0.237× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.884e+04 | 4426 | 0.235× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 436.4 | 102 | 0.234× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4264 | 995.3 | 0.233× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 558.1 | 120.1 | 0.215× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 133.1 | 21.29 | 0.160× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142.8 | 21.71 | 0.152× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1151 | 159 | 0.138× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5931 | 524.3 | 0.088× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6526 | 539 | 0.083× | **NO** | competitive |
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
