# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rtx4090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 777.6 | 5005 | 6.437× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5965 | 2.783e+04 | 4.665× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 3343 | 1.543e+04 | 4.614× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1859 | 8505 | 4.575× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5965 | 2.72e+04 | 4.560× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1859 | 8247 | 4.436× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3343 | 1.41e+04 | 4.216× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1912 | 7975 | 4.171× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 840.8 | 3282 | 3.904× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2461 | 9323 | 3.789× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 552.4 | 2087 | 3.779× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2461 | 9207 | 3.742× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 413.6 | 1483 | 3.586× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1651 | 5811 | 3.519× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5799 | 1.98e+04 | 3.414× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5585 | 1.818e+04 | 3.254× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5585 | 1.767e+04 | 3.164× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 839.1 | 2610 | 3.110× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3306 | 1.01e+04 | 3.056× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2192 | 6642 | 3.031× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2230 | 6715 | 3.011× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4177 | 1.232e+04 | 2.950× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.76e+04 | 5.153e+04 | 2.928× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 456.9 | 1300 | 2.845× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4177 | 1.185e+04 | 2.838× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8080 | 2.248e+04 | 2.782× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1592 | 4412 | 2.771× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1651 | 4539 | 2.749× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 572.1 | 1548 | 2.706× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1592 | 3960 | 2.487× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4992 | 1.221e+04 | 2.445× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.19 | 72.81 | 2.412× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1717 | 4108 | 2.393× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3216 | 7667 | 2.384× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 30.19 | 71.46 | 2.367× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.642e+04 | 3.879e+04 | 2.363× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 724.1 | 1706 | 2.355× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8080 | 1.882e+04 | 2.330× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1950 | 4491 | 2.303× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.4e+04 | 3.203e+04 | 2.288× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 416.9 | 933.5 | 2.239× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 882.1 | 1950 | 2.211× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4992 | 1.077e+04 | 2.157× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 552.4 | 1183 | 2.142× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5590 | 1.186e+04 | 2.122× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 581.1 | 1226 | 2.110× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2436 | 5134 | 2.107× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.76e+04 | 3.699e+04 | 2.102× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5480 | 1.146e+04 | 2.092× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.161e+04 | 2.423e+04 | 2.086× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1204 | 2508 | 2.083× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1950 | 4056 | 2.080× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1412 | 2906 | 2.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1164 | 2382 | 2.047× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2534 | 5170 | 2.041× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1164 | 2370 | 2.037× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 992.8 | 1983 | 1.997× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 739.7 | 1471 | 1.989× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6063 | 1.183e+04 | 1.951× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7894 | 1.53e+04 | 1.938× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2385 | 4617 | 1.935× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4510 | 8706 | 1.930× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 262.6 | 503.2 | 1.916× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2392 | 4526 | 1.893× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5799 | 1.096e+04 | 1.891× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.1 | 162.2 | 1.862× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.1 | 161.8 | 1.857× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2230 | 4092 | 1.835× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6399 | 1.173e+04 | 1.834× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2032 | 3711 | 1.826× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 721.4 | 1303 | 1.806× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.686e+04 | 3.033e+04 | 1.799× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 121.7 | 216.1 | 1.776× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7894 | 1.401e+04 | 1.774× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2041 | 3619 | 1.773× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6024 | 1.065e+04 | 1.768× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1.113e+04 | 1.955e+04 | 1.756× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.091e+04 | 1.91e+04 | 1.751× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6024 | 1.036e+04 | 1.719× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1224 | 2095 | 1.711× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5076 | 8663 | 1.707× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2534 | 4321 | 1.705× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 725.9 | 1237 | 1.704× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1023 | 1728 | 1.689× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1.113e+04 | 1.876e+04 | 1.685× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1224 | 2054 | 1.678× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2436 | 4078 | 1.674× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1047 | 1746 | 1.668× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1770 | 2950 | 1.666× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1630 | 2699 | 1.656× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 240.3 | 397.9 | 1.656× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 717.4 | 1187 | 1.655× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6574 | 1.084e+04 | 1.649× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5076 | 8341 | 1.643× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.091e+04 | 1.773e+04 | 1.625× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5063 | 8213 | 1.622× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 342 | 553.8 | 1.619× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.53e+04 | 2.464e+04 | 1.610× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 364.2 | 585.3 | 1.607× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 95.35 | 152.5 | 1.599× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5142 | 8214 | 1.597× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 882.1 | 1408 | 1.596× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 749.4 | 1187 | 1.584× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 113.5 | 179.5 | 1.582× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 391.2 | 616.1 | 1.575× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5371 | 8444 | 1.572× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3058 | 4796 | 1.568× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 240.3 | 373.1 | 1.553× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4317 | 6643 | 1.539× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 212.1 | 325.3 | 1.534× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 180 | 275.5 | 1.530× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2257 | 3372 | 1.494× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 198.2 | 296.1 | 1.493× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 67.8 | 101.2 | 1.493× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 370.9 | 553.2 | 1.491× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 207.5 | 309.4 | 1.491× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 342 | 509.2 | 1.489× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 232 | 342 | 1.474× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 217.1 | 316.4 | 1.458× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 144.9 | 210.1 | 1.450× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 180 | 261 | 1.450× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.536e+04 | 2.221e+04 | 1.446× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5023 | 7230 | 1.439× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 962.5 | 1385 | 1.439× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6574 | 9450 | 1.437× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5711 | 8206 | 1.437× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 49.92 | 71.4 | 1.430× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5711 | 8155 | 1.428× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 364.2 | 519.8 | 1.427× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 95.35 | 136 | 1.427× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 391.2 | 554.3 | 1.417× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1825 | 2585 | 1.417× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 614.1 | 868 | 1.413× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 129.9 | 183.5 | 1.412× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1255 | 1768 | 1.410× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 113.5 | 159.8 | 1.409× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.548e+04 | 2.18e+04 | 1.409× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.9 | 203.8 | 1.407× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2041 | 2871 | 1.406× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.536e+04 | 2.157e+04 | 1.404× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4682 | 6571 | 1.403× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 77.03 | 108.1 | 1.403× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 839.1 | 1169 | 1.393× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5371 | 7475 | 1.392× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 316.3 | 440.1 | 1.391× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 217.1 | 298.4 | 1.375× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2545 | 3488 | 1.371× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142.9 | 194.9 | 1.364× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 129.9 | 177.1 | 1.363× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 107.9 | 146.5 | 1.358× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 163.7 | 221.7 | 1.355× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2545 | 3443 | 1.353× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 73.12 | 98.85 | 1.352× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2039 | 2749 | 1.349× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2480 | 3344 | 1.348× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2032 | 2739 | 1.348× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 53.73 | 72.35 | 1.346× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4153 | 5590 | 1.346× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4794 | 6451 | 1.346× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142.9 | 192.1 | 1.344× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 85.68 | 114.6 | 1.337× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.8 | 134.1 | 1.331× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.548e+04 | 2.059e+04 | 1.330× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.4 | 206.9 | 1.323× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 9407 | 1.242e+04 | 1.321× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 316.3 | 417.7 | 1.321× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 9407 | 1.241e+04 | 1.320× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 64.04 | 83.94 | 1.311× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 370.9 | 485.7 | 1.310× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 179.9 | 235.2 | 1.307× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 179.9 | 235 | 1.306× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 176.2 | 229.2 | 1.301× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2041 | 2650 | 1.298× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4436 | 5754 | 1.297× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3721 | 4818 | 1.295× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3443 | 4452 | 1.293× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 992.8 | 1282 | 1.291× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.7 | 162.8 | 1.286× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 262.6 | 337.3 | 1.285× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 420.1 | 538.5 | 1.282× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 721.4 | 923.6 | 1.280× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 297.4 | 380.5 | 1.279× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 49.92 | 63.7 | 1.276× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 163.7 | 208.7 | 1.275× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4317 | 5499 | 1.274× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 486.9 | 619.8 | 1.273× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 207.5 | 263.4 | 1.270× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 85.7 | 108.8 | 1.269× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4436 | 5631 | 1.269× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 176.2 | 223.4 | 1.268× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 102.3 | 129.7 | 1.267× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 122.5 | 154.8 | 1.264× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 830.5 | 1049 | 1.264× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 239.8 | 302.2 | 1.260× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 77.61 | 97.2 | 1.252× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.4 | 194.8 | 1.246× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 285 | 353.3 | 1.240× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4105 | 5085 | 1.239× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 232 | 287 | 1.237× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 277.3 | 343.1 | 1.237× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211.8 | 261.9 | 1.237× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.08e+04 | 1.335e+04 | 1.236× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 317.4 | 391.5 | 1.234× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 200.2 | 245.9 | 1.228× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 126.7 | 155.5 | 1.228× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 531.8 | 647.6 | 1.218× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 371.3 | 452 | 1.217× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 198.8 | 241.4 | 1.214× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.642e+04 | 1.992e+04 | 1.214× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 177.4 | 215.1 | 1.212× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.13 | 90.87 | 1.209× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5023 | 6064 | 1.207× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1613 | 1943 | 1.205× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 233.9 | 280.8 | 1.200× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 133.4 | 159.9 | 1.199× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4264 | 5112 | 1.199× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 136.4 | 163.3 | 1.198× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 671.3 | 802.8 | 1.196× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 232 | 274.5 | 1.183× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 541.6 | 639.8 | 1.181× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 572.3 | 675.7 | 1.181× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 317.4 | 374.6 | 1.180× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 486.9 | 574.4 | 1.180× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 38.65 | 45.57 | 1.179× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 208.4 | 244.7 | 1.174× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5055 | 5928 | 1.173× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 88.89 | 104.2 | 1.173× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 115 | 134.5 | 1.170× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 53.73 | 62.83 | 1.169× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 361.5 | 422.4 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 482.5 | 563 | 1.167× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 102.3 | 119.3 | 1.166× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 39.05 | 45.51 | 1.165× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.8 | 116.7 | 1.158× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3467 | 4008 | 1.156× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 717.4 | 828.1 | 1.154× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.08e+04 | 1.244e+04 | 1.152× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 203.8 | 232.7 | 1.142× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 121.7 | 138.7 | 1.140× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 428 | 487 | 1.138× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 412.4 | 467.5 | 1.134× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 85.46 | 96.78 | 1.132× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 737.6 | 834 | 1.131× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 531.8 | 601.3 | 1.131× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.08 | 97.29 | 1.130× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 208.4 | 235.3 | 1.129× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 533.7 | 602.2 | 1.128× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 31.19 | 35.16 | 1.127× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.4 | 162.5 | 1.125× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.091e+04 | 2.347e+04 | 1.122× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4610 | 5163 | 1.120× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 449.2 | 502.9 | 1.120× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 198.8 | 222.6 | 1.119× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.42 | 47.37 | 1.117× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5055 | 5643 | 1.116× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 313.1 | 348.7 | 1.114× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 394.1 | 438.2 | 1.112× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 50.28 | 55.8 | 1.110× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 420.1 | 465.9 | 1.109× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 193.5 | 214.5 | 1.109× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 25.98 | 28.72 | 1.105× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 127 | 140.2 | 1.104× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5576 | 6152 | 1.103× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 569.4 | 627.4 | 1.102× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 226.1 | 248.6 | 1.099× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.6 | 146.9 | 1.099× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 46.55 | 51.15 | 1.099× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 453.7 | 497.1 | 1.096× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 554 | 606.6 | 1.095× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 67.8 | 74.24 | 1.095× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.7 | 47.85 | 1.095× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1867 | 2041 | 1.093× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.091e+04 | 2.283e+04 | 1.092× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 212.1 | 231.6 | 1.092× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 162 | 176.5 | 1.090× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 594.8 | 647.8 | 1.089× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.013e+04 | 1.101e+04 | 1.087× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 572.3 | 621.9 | 1.087× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 26.21 | 28.43 | 1.085× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.4 | 361.3 | 1.084× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 541.6 | 586.9 | 1.084× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 64.13 | 69.48 | 1.083× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 426.7 | 461 | 1.080× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.29 | 48.83 | 1.078× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.3 | 127.6 | 1.078× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211 | 226.9 | 1.076× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1912 | 2052 | 1.073× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.013e+04 | 1.087e+04 | 1.073× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 193.5 | 207.6 | 1.073× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2257 | 2420 | 1.072× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.6 | 154.8 | 1.070× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 178.3 | 190.7 | 1.070× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 506.6 | 540.9 | 1.068× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 45.23 | 48.29 | 1.068× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142.9 | 152.5 | 1.067× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 455.7 | 485.2 | 1.065× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.3 | 419.7 | 1.065× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 621 | 660.9 | 1.064× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 279 | 296.7 | 1.063× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 416.4 | 441.9 | 1.061× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 420.3 | 445.7 | 1.060× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1912 | 2027 | 1.060× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3581 | 3794 | 1.059× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 137.4 | 145.5 | 1.058× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 175.4 | 185.5 | 1.058× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 227 | 239.7 | 1.056× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 447.5 | 472.4 | 1.056× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2107 | 2221 | 1.054× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 80.02 | 84.32 | 1.054× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211.8 | 223.2 | 1.054× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 655.8 | 691 | 1.054× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1551 | 1634 | 1.053× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 433.9 | 456 | 1.051× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 485 | 509.6 | 1.051× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.2 | 370.6 | 1.049× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 221.5 | 231.9 | 1.047× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.1 | 369.6 | 1.047× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 135 | 141.3 | 1.047× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 515.1 | 536.9 | 1.042× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 29.3 | 30.52 | 1.042× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 112.3 | 116.9 | 1.041× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3780 | 3933 | 1.041× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 338.4 | 352 | 1.040× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 655.8 | 680.9 | 1.038× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 30.54 | 31.68 | 1.037× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 346.8 | 359.1 | 1.035× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 431.7 | 446.3 | 1.034× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211 | 218 | 1.033× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 340 | 350.9 | 1.032× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6722 | 6933 | 1.031× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5991 | 6161 | 1.028× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 557.1 | 572.1 | 1.027× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2662 | 2730 | 1.025× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 584.5 | 597.6 | 1.022× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 232 | 237.1 | 1.022× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 77.03 | 78.54 | 1.020× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2039 | 2076 | 1.018× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3058 | 3109 | 1.017× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 592 | 601.3 | 1.016× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 621 | 630.5 | 1.015× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 410.9 | 416.6 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 107.9 | 109.3 | 1.013× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 620.6 | 628.8 | 1.013× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 221.5 | 223.6 | 1.009× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2684 | 2700 | 1.006× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 495.7 | 498.6 | 1.006× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.84e+04 | 1.845e+04 | 1.003× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 416.4 | 417.6 | 1.003× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6722 | 6729 | 1.001× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1187 | 1183 | 0.997× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 125.1 | 124.2 | 0.993× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3780 | 3743 | 0.990× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 227 | 223.9 | 0.986× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.477e+04 | 1.453e+04 | 0.984× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 614.1 | 604 | 0.983× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3721 | 3630 | 0.976× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 64.04 | 62.43 | 0.975× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 481.7 | 469.3 | 0.974× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4794 | 4651 | 0.970× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 671.3 | 647.3 | 0.964× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 453.7 | 437.5 | 0.964× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.166e+04 | 1.122e+04 | 0.963× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3145 | 3021 | 0.961× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 85.68 | 82.25 | 0.960× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 557.1 | 532.5 | 0.956× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 313.1 | 299.2 | 0.955× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 371.3 | 353.6 | 0.952× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.41 | 60.22 | 0.950× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 737.6 | 699.6 | 0.948× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.166e+04 | 1.105e+04 | 0.948× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3581 | 3390 | 0.947× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 515.1 | 487.1 | 0.946× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1779 | 1679 | 0.944× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 122.5 | 115.4 | 0.942× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 592 | 557.1 | 0.941× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 584.5 | 548.8 | 0.939× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 85.7 | 79.98 | 0.933× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 620.6 | 575.9 | 0.928× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 9811 | 9089 | 0.926× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 66.8 | 61.87 | 0.926× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 74.95 | 69.23 | 0.924× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 110.8 | 101.1 | 0.912× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.4 | 303.5 | 0.910× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 361.5 | 328.9 | 0.910× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3467 | 3145 | 0.907× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 75.13 | 68.1 | 0.906× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.74 | 62.88 | 0.902× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 70.06 | 62.76 | 0.896× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.2 | 314.7 | 0.891× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.7 | 112.3 | 0.886× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.1 | 118.7 | 0.885× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 81.34 | 71.87 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.2 | 117.7 | 0.883× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 96.99 | 85.57 | 0.882× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 117.2 | 103.3 | 0.882× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 133.4 | 117.5 | 0.881× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.3 | 104 | 0.879× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.894e+04 | 1.658e+04 | 0.876× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.492e+04 | 1.304e+04 | 0.874× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1933 | 1685 | 0.872× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1581 | 1375 | 0.870× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.56 | 72.99 | 0.863× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 412.4 | 355.6 | 0.862× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.29 | 74.02 | 0.858× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.6 | 105.9 | 0.856× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 506.6 | 433.5 | 0.856× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.263e+04 | 1.079e+04 | 0.855× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.4e+04 | 1.196e+04 | 0.854× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.44 | 73.63 | 0.852× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.8 | 105.2 | 0.850× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 86.08 | 73.06 | 0.849× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 340 | 287.8 | 0.847× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 394.1 | 333.3 | 0.846× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 495.7 | 417.2 | 0.842× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.894e+04 | 1.593e+04 | 0.841× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 85.46 | 71.76 | 0.840× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 426.7 | 357.5 | 0.838× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 107.2 | 89.45 | 0.834× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6239 | 5181 | 0.830× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2041 | 1689 | 0.827× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1195 | 983.3 | 0.823× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.931e+04 | 1.589e+04 | 0.823× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1717 | 1411 | 0.822× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5365 | 4404 | 0.821× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 455.7 | 373.8 | 0.820× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 39.05 | 31.76 | 0.813× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.071e+04 | 8661 | 0.809× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3443 | 2783 | 0.808× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 115.5 | 91.96 | 0.796× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2480 | 1970 | 0.794× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 9811 | 7759 | 0.791× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.2 | 91.52 | 0.788× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.301e+04 | 1.023e+04 | 0.786× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 42.42 | 33.33 | 0.786× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7889 | 6179 | 0.783× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7889 | 6085 | 0.771× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1867 | 1438 | 0.770× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.29 | 34.6 | 0.764× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.294e+04 | 9874 | 0.763× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 431.7 | 327.7 | 0.759× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.881e+04 | 1.423e+04 | 0.757× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 45.23 | 33.9 | 0.749× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.15 | 31.41 | 0.745× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 410.9 | 305 | 0.742× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4610 | 3404 | 0.738× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.881e+04 | 1.383e+04 | 0.735× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.741e+04 | 1.272e+04 | 0.731× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 7092 | 5147 | 0.726× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.53e+04 | 1.103e+04 | 0.721× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1551 | 1110 | 0.716× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.127e+04 | 7927 | 0.704× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.127e+04 | 7863 | 0.698× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.294e+04 | 8888 | 0.687× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1431 | 968.4 | 0.677× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.622e+04 | 1.095e+04 | 0.675× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5216 | 3490 | 0.669× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6263 | 4049 | 0.646× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 7092 | 4575 | 0.645× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 968.1 | 622.8 | 0.643× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.64e+04 | 1.052e+04 | 0.641× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.622e+04 | 1.038e+04 | 0.640× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6012 | 3812 | 0.634× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5630 | 3557 | 0.632× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5370 | 3382 | 0.630× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2570 | 1606 | 0.625× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.394e+04 | 8698 | 0.624× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2570 | 1593 | 0.620× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3648 | 2258 | 0.619× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.071e+04 | 6523 | 0.609× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.301e+04 | 7737 | 0.595× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1231 | 731.3 | 0.594× | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1930 | 1125 | 0.583× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 144.4 | 83.09 | 0.575× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9592 | 5408 | 0.564× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.35e+04 | 7609 | 0.564× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.492e+04 | 8364 | 0.560× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2232 | 1246 | 0.558× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2232 | 1232 | 0.552× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9592 | 5241 | 0.546× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5630 | 2974 | 0.528× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.64e+04 | 8334 | 0.508× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2063 | 1045 | 0.506× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.116e+04 | 5602 | 0.502× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6064 | 2939 | 0.485× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3326 | 1612 | 0.485× | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2260 | 1026 | 0.454× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8647 | 3912 | 0.452× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 968.1 | 422.5 | 0.436× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8231 | 3573 | 0.434× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 749.4 | 320.4 | 0.428× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6811 | 2905 | 0.427× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1646 | 680.5 | 0.413× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9552 | 3931 | 0.412× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5547 | 2280 | 0.411× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 118.3 | 48.14 | 0.407× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1231 | 493.5 | 0.401× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6677 | 2669 | 0.400× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 29.3 | 11.64 | 0.397× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8647 | 3360 | 0.389× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9552 | 3708 | 0.388× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5931 | 2264 | 0.382× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3088 | 1139 | 0.369× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3088 | 1139 | 0.369× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2625 | 940.5 | 0.358× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6064 | 2169 | 0.358× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2437 | 858.4 | 0.352× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2063 | 723.5 | 0.351× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8231 | 2878 | 0.350× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2034 | 698.3 | 0.343× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 233.9 | 78.44 | 0.335× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5547 | 1859 | 0.335× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1604 | 532.3 | 0.332× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2140 | 688.4 | 0.322× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 277.3 | 87.35 | 0.315× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6677 | 1974 | 0.296× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2705 | 782.1 | 0.289× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 749.4 | 201.6 | 0.269× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2385 | 624.2 | 0.262× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 338.4 | 88.46 | 0.261× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 346.8 | 90.01 | 0.260× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.1 | 90.46 | 0.256× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 394.3 | 96.35 | 0.244× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4153 | 987.6 | 0.238× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 420.3 | 99.66 | 0.237× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 433.9 | 102 | 0.235× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 77.61 | 18.17 | 0.234× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4264 | 995.3 | 0.233× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 447.5 | 101.6 | 0.227× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 581.1 | 120.1 | 0.207× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 133.6 | 21.29 | 0.159× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142.9 | 21.71 | 0.152× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1187 | 159 | 0.134× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5931 | 524.3 | 0.088× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6811 | 539 | 0.079× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3648 | 288 | 0.079× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5216 | 369.2 | 0.071× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2034 | 95.16 | 0.047× | **NO** | competitive |
