# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5965 | 2.783e+04 | 4.665× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 3343 | 1.543e+04 | 4.614× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1859 | 8505 | 4.575× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5965 | 2.72e+04 | 4.560× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 245.5 | 1106 | 4.506× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 665.9 | 2982 | 4.478× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1859 | 8247 | 4.436× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3343 | 1.41e+04 | 4.216× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 784.9 | 2995 | 3.816× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2461 | 9323 | 3.789× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2461 | 9207 | 3.742× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1651 | 5811 | 3.519× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5585 | 1.818e+04 | 3.254× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5585 | 1.767e+04 | 3.164× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 839.1 | 2610 | 3.110× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3306 | 1.01e+04 | 3.056× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2230 | 6715 | 3.011× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4177 | 1.232e+04 | 2.950× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4177 | 1.185e+04 | 2.838× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 163.9 | 460.8 | 2.812× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 731 | 2033 | 2.782× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1651 | 4539 | 2.749× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.248e+04 | 5.406e+04 | 2.405× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3216 | 7667 | 2.384× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 724.1 | 1706 | 2.355× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1e+04 | 2.332e+04 | 2.332× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1950 | 4491 | 2.303× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 95.24 | 215.1 | 2.258× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3518 | 7783 | 2.213× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6001 | 1.322e+04 | 2.204× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 913.9 | 1950 | 2.134× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1950 | 4056 | 2.080× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1412 | 2906 | 2.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1164 | 2382 | 2.047× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1164 | 2370 | 2.037× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2526 | 5134 | 2.032× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.648e+04 | 3.203e+04 | 1.944× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 269 | 503.2 | 1.870× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.248e+04 | 4.19e+04 | 1.864× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6412 | 1.186e+04 | 1.850× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2230 | 4092 | 1.835× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2032 | 3711 | 1.826× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 826.9 | 1489 | 1.801× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6826 | 1.221e+04 | 1.788× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6653 | 1.173e+04 | 1.764× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 132.2 | 232.7 | 1.760× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 122.8 | 216.1 | 1.760× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.379e+04 | 2.423e+04 | 1.756× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1.113e+04 | 1.955e+04 | 1.756× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.287e+04 | 3.879e+04 | 1.697× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1023 | 1728 | 1.689× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1.113e+04 | 1.876e+04 | 1.685× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1755 | 2950 | 1.681× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4924 | 8214 | 1.668× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1047 | 1746 | 1.668× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1e+04 | 1.664e+04 | 1.664× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3.1e+04 | 5.153e+04 | 1.663× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6208 | 1.029e+04 | 1.657× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1630 | 2699 | 1.656× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 240.3 | 397.9 | 1.656× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 750.2 | 1237 | 1.649× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.859e+04 | 3.033e+04 | 1.631× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 342 | 553.8 | 1.619× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2526 | 4078 | 1.614× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 737.9 | 1187 | 1.609× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 364.2 | 585.3 | 1.607× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 113.5 | 179.5 | 1.582× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6826 | 1.077e+04 | 1.577× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 391.2 | 616.1 | 1.575× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 240.3 | 373.1 | 1.553× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 766.4 | 1187 | 1.549× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 913.9 | 1408 | 1.540× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 180 | 275.5 | 1.530× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 122.8 | 185.3 | 1.508× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 198.2 | 296.1 | 1.493× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4176 | 6235 | 1.493× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 370.9 | 553.2 | 1.491× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 207.5 | 309.4 | 1.491× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 342 | 509.2 | 1.489× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.049e+04 | 1.53e+04 | 1.458× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 217.1 | 316.4 | 1.458× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 180 | 261 | 1.450× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 172.3 | 248.9 | 1.445× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 170.3 | 245.9 | 1.444× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3518 | 5044 | 1.434× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 364.2 | 519.8 | 1.427× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 391.2 | 554.3 | 1.417× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 129.9 | 183.5 | 1.412× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 113.5 | 159.8 | 1.409× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5540 | 7780 | 1.404× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4121 | 5754 | 1.396× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 839.1 | 1169 | 1.393× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 318.6 | 440.1 | 1.381× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 280.3 | 386.9 | 1.381× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3487 | 4796 | 1.375× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 217.1 | 298.4 | 1.375× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 129.9 | 177.1 | 1.363× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 107.9 | 146.5 | 1.358× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 172.3 | 233 | 1.352× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 73.12 | 98.85 | 1.352× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 144.3 | 194.9 | 1.351× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2039 | 2749 | 1.349× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2032 | 2739 | 1.348× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 53.73 | 72.35 | 1.346× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.72 | 101.2 | 1.337× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.049e+04 | 1.401e+04 | 1.335× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 144.3 | 192.1 | 1.332× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.8 | 134.1 | 1.331× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2726 | 3619 | 1.328× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 9407 | 1.242e+04 | 1.321× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 9407 | 1.241e+04 | 1.320× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.449e+04 | 1.91e+04 | 1.318× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2544 | 3344 | 1.314× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 318.6 | 417.7 | 1.311× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 370.9 | 485.7 | 1.310× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 72.01 | 94.09 | 1.307× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4436 | 5754 | 1.297× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.713e+04 | 2.221e+04 | 1.296× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1073 | 1385 | 1.291× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 234.9 | 302.2 | 1.286× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 420.1 | 538.5 | 1.282× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 487.9 | 619.8 | 1.270× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 207.5 | 263.4 | 1.270× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4436 | 5631 | 1.269× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 122.5 | 154.8 | 1.264× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 196.7 | 248.6 | 1.264× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 74.33 | 93.83 | 1.262× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 280.3 | 353.3 | 1.261× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.713e+04 | 2.157e+04 | 1.259× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8482 | 1.065e+04 | 1.256× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 269 | 337.3 | 1.254× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 691.9 | 867.5 | 1.254× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6558 | 8213 | 1.252× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 35.68 | 44.29 | 1.241× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1365 | 1693 | 1.240× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4105 | 5085 | 1.239× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.34 | 108.1 | 1.237× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211.8 | 261.9 | 1.237× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.449e+04 | 1.773e+04 | 1.223× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8482 | 1.036e+04 | 1.221× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7480 | 9121 | 1.219× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 531.8 | 647.6 | 1.218× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 422.1 | 513.7 | 1.217× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2872 | 3488 | 1.214× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 133.4 | 159.9 | 1.199× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2872 | 3443 | 1.199× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 422.1 | 505.5 | 1.198× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 136.4 | 163.3 | 1.198× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 671.3 | 802.8 | 1.196× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3.1e+04 | 3.699e+04 | 1.193× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7287 | 8663 | 1.189× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.123e+04 | 1.335e+04 | 1.189× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 950 | 1125 | 1.185× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 38.65 | 45.57 | 1.179× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 573.7 | 675.7 | 1.178× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 487.9 | 574.4 | 1.177× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 208.4 | 244.7 | 1.174× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 115 | 134.5 | 1.170× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 53.73 | 62.83 | 1.169× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 550.8 | 639.8 | 1.162× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.09 | 99.98 | 1.161× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 98.67 | 114.6 | 1.161× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.8 | 116.7 | 1.158× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3467 | 4008 | 1.156× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 244.4 | 280.8 | 1.149× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7287 | 8341 | 1.145× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 39.93 | 45.51 | 1.140× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 428.5 | 487 | 1.137× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 531.8 | 601.3 | 1.131× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 737.6 | 834 | 1.131× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 208.4 | 235.3 | 1.129× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7480 | 8439 | 1.128× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 31.25 | 35.16 | 1.125× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 97.47 | 108.8 | 1.116× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 86.82 | 96.78 | 1.115× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 313.1 | 348.7 | 1.114× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 420.1 | 465.9 | 1.109× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 565.9 | 627.4 | 1.109× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.123e+04 | 1.244e+04 | 1.108× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 25.96 | 28.72 | 1.106× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 417 | 461 | 1.106× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 127 | 140.2 | 1.104× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 88.24 | 97.29 | 1.103× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 46.45 | 51.15 | 1.101× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.32 | 69.48 | 1.097× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.3 | 127.6 | 1.097× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.43 | 47.37 | 1.091× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.87 | 47.85 | 1.091× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 402.4 | 438.2 | 1.089× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 96.94 | 105.5 | 1.089× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 595.3 | 647.8 | 1.088× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.013e+04 | 1.101e+04 | 1.087× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 97.25 | 105.5 | 1.085× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 573.7 | 621.9 | 1.084× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 333.4 | 361.3 | 1.084× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 766.4 | 828.1 | 1.081× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 465.5 | 502.9 | 1.080× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.013e+04 | 1.087e+04 | 1.073× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 550.8 | 586.9 | 1.066× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.1 | 121.5 | 1.064× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 621 | 660.9 | 1.064× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 510.9 | 540.9 | 1.059× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 441.6 | 467.5 | 1.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 137.4 | 145.5 | 1.058× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 79.93 | 84.32 | 1.055× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211.8 | 223.2 | 1.054× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 655.8 | 691 | 1.054× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2726 | 2871 | 1.053× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 624.4 | 657.1 | 1.052× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1940 | 2041 | 1.052× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 46.47 | 48.83 | 1.051× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 214.8 | 225.5 | 1.049× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.2 | 370.6 | 1.049× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 462.4 | 485.2 | 1.049× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 431 | 452 | 1.049× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 135 | 141.3 | 1.047× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 212.4 | 222.3 | 1.047× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 327.9 | 343.1 | 1.046× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.26 | 94.21 | 1.044× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 46.4 | 48.29 | 1.041× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 406.5 | 422.4 | 1.039× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.49 | 90.87 | 1.039× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 655.8 | 680.9 | 1.038× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 580.1 | 602.2 | 1.038× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4940 | 5112 | 1.035× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 340 | 350.9 | 1.032× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6722 | 6933 | 1.031× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 588.2 | 606.6 | 1.031× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 522.1 | 536.9 | 1.028× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.939e+04 | 1.98e+04 | 1.021× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.52 | 92.39 | 1.021× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4325 | 4412 | 1.020× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2039 | 2076 | 1.018× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 438.8 | 446.3 | 1.017× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 89.37 | 90.86 | 1.017× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 363.8 | 369.6 | 1.016× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 676 | 686.5 | 1.015× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 621 | 630.5 | 1.015× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.4 | 358.8 | 1.015× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 125.6 | 127.5 | 1.015× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 107.9 | 109.3 | 1.013× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 347.5 | 352 | 1.013× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 624.4 | 631.9 | 1.012× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7156 | 7230 | 1.010× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 697.8 | 700.9 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 507.5 | 509.6 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 495.4 | 497.1 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6722 | 6729 | 1.001× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2731 | 2730 | 1.000× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 566.4 | 563 | 0.994× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 502.9 | 498.6 | 0.991× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 88.32 | 87.14 | 0.987× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 728.2 | 718.2 | 0.986× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.482e+04 | 1.453e+04 | 0.981× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 75.72 | 74.24 | 0.980× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 157.9 | 154.8 | 0.980× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.5 | 131.8 | 0.980× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 135.2 | 132.4 | 0.979× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1988 | 1943 | 0.978× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.2 | 152.5 | 0.976× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 482.2 | 469.3 | 0.973× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 211.2 | 204.7 | 0.969× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 671.3 | 647.3 | 0.964× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.18 | 83.94 | 0.963× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 244.3 | 235.2 | 0.963× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 244.3 | 235 | 0.962× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 676 | 650.1 | 0.962× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3145 | 3021 | 0.961× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2762 | 2650 | 0.959× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 313.1 | 299.2 | 0.955× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.726e+04 | 2.603e+04 | 0.955× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9118 | 8706 | 0.955× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 240.2 | 229.2 | 0.954× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.14 | 60.22 | 0.954× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 662.2 | 628.8 | 0.950× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 737.6 | 699.6 | 0.948× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 155.5 | 146.9 | 0.945× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 122.5 | 115.4 | 0.942× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 638.3 | 601.3 | 0.942× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 697.8 | 656.2 | 0.940× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1787 | 1679 | 0.939× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 255.7 | 239.7 | 0.937× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 522.1 | 487.1 | 0.933× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 240.2 | 223.4 | 0.930× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 66.64 | 61.87 | 0.929× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6112 | 5672 | 0.928× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4121 | 3824 | 0.928× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 9811 | 9089 | 0.926× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 728.2 | 669.6 | 0.920× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 650.2 | 597.6 | 0.919× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1826 | 1678 | 0.919× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 507.5 | 465.9 | 0.918× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 241.6 | 221.7 | 0.918× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.454e+04 | 2.248e+04 | 0.916× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4325 | 3960 | 0.916× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 110.8 | 101.1 | 0.912× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 333.4 | 303.5 | 0.910× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2302 | 2095 | 0.910× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 152.8 | 138.7 | 0.908× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3467 | 3145 | 0.907× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 232 | 210.1 | 0.905× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2458 | 2221 | 0.904× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.67 | 62.88 | 0.903× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.34 | 78.54 | 0.899× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.82 | 62.76 | 0.899× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 252.8 | 226.9 | 0.898× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 638.1 | 572.1 | 0.897× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 95.44 | 85.57 | 0.897× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 437.5 | 391.5 | 0.895× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2302 | 2054 | 0.892× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3487 | 3109 | 0.892× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.2 | 314.7 | 0.891× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 383.9 | 342 | 0.891× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 206.2 | 183.6 | 0.890× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1545 | 1375 | 0.890× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 126.6 | 112.3 | 0.887× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134 | 118.7 | 0.885× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 262.2 | 231.9 | 0.884× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 495.4 | 437.5 | 0.883× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.4 | 117.7 | 0.882× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 133.4 | 117.5 | 0.881× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 117.4 | 103.3 | 0.880× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.3 | 104 | 0.879× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 232 | 203.8 | 0.879× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 255.7 | 223.9 | 0.876× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 245.6 | 214.5 | 0.873× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 638.3 | 557.1 | 0.873× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.287e+04 | 1.992e+04 | 0.871× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.726e+04 | 2.374e+04 | 0.871× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 662.2 | 575.9 | 0.870× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5070 | 4404 | 0.869× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 241.6 | 208.7 | 0.864× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 252.8 | 218 | 0.862× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.71 | 72.99 | 0.862× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 417 | 357.5 | 0.857× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.6 | 105.9 | 0.857× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 437.5 | 374.6 | 0.856× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 262.2 | 223.6 | 0.853× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 105.1 | 89.45 | 0.851× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6968 | 5928 | 0.851× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.7 | 105.2 | 0.850× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 510.9 | 433.5 | 0.848× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7156 | 6064 | 0.847× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 340 | 287.8 | 0.847× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 245.6 | 207.6 | 0.845× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 650.2 | 548.8 | 0.844× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 638.1 | 532.5 | 0.835× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7879 | 6571 | 0.834× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 98.67 | 82.25 | 0.834× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 502.9 | 417.2 | 0.830× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 402.4 | 333.3 | 0.828× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 88.24 | 73.06 | 0.828× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 86.82 | 71.76 | 0.827× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.24e+04 | 1.845e+04 | 0.824× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 97.47 | 79.98 | 0.821× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 431 | 353.6 | 0.820× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.453e+04 | 1.183e+04 | 0.814× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 113 | 91.96 | 0.814× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5920 | 4818 | 0.814× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6968 | 5643 | 0.810× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 406.5 | 328.9 | 0.809× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 462.4 | 373.8 | 0.808× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 441.6 | 355.6 | 0.805× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 113.7 | 91.52 | 0.805× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4224 | 3401 | 0.805× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 39.93 | 31.76 | 0.795× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2120 | 1685 | 0.795× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 872.6 | 693 | 0.794× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 9811 | 7759 | 0.791× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 96.94 | 76.6 | 0.790× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.44e+04 | 1.122e+04 | 0.779× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.49 | 68.1 | 0.778× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1863 | 1449 | 0.778× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3.019e+04 | 2.347e+04 | 0.777× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5787 | 4485 | 0.775× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2544 | 1970 | 0.775× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 97.25 | 75.26 | 0.774× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1279 | 983.3 | 0.769× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 43.43 | 33.33 | 0.767× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.454e+04 | 1.882e+04 | 0.767× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.44e+04 | 1.105e+04 | 0.767× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2486 | 1898 | 0.764× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6838 | 5181 | 0.758× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.26 | 68.32 | 0.757× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3.019e+04 | 2.283e+04 | 0.756× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 214.5 | 162.2 | 0.756× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8803 | 6642 | 0.755× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 214.5 | 161.8 | 0.754× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 41.85 | 31.41 | 0.751× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 590.7 | 441.9 | 0.748× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 438.8 | 327.7 | 0.747× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 510.3 | 380.5 | 0.746× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 46.47 | 34.6 | 0.745× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1940 | 1438 | 0.741× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.52 | 66.8 | 0.738× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 89.37 | 65.79 | 0.736× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3376 | 2484 | 0.736× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4600 | 3382 | 0.735× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8800 | 6451 | 0.733× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 46.4 | 33.9 | 0.730× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 7092 | 5147 | 0.726× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.648e+04 | 1.196e+04 | 0.726× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 224.4 | 162.8 | 0.726× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.936e+04 | 1.396e+04 | 0.721× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 87.18 | 62.43 | 0.716× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.984e+04 | 1.419e+04 | 0.715× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 383.9 | 274.5 | 0.715× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9316 | 6643 | 0.713× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5523 | 3933 | 0.712× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 88.32 | 62.84 | 0.711× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 590.7 | 417.6 | 0.707× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.127e+04 | 7927 | 0.704× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.127e+04 | 7863 | 0.698× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 224.4 | 155.5 | 0.693× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7514 | 5170 | 0.688× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1411 | 968.4 | 0.686× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142 | 97.2 | 0.685× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5523 | 3743 | 0.678× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2421 | 1634 | 0.675× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3100 | 2087 | 0.673× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.005e+04 | 6732 | 0.670× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.984e+04 | 1.317e+04 | 0.664× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.652e+04 | 1.095e+04 | 0.663× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4237 | 2794 | 0.659× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.314e+04 | 8661 | 0.659× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9118 | 5949 | 0.652× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.26e+04 | 8206 | 0.651× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.26e+04 | 8155 | 0.647× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 7092 | 4575 | 0.645× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.682e+04 | 1.079e+04 | 0.642× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.482e+04 | 9470 | 0.639× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5630 | 3557 | 0.632× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.652e+04 | 1.038e+04 | 0.628× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2570 | 1606 | 0.625× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4838 | 3001 | 0.620× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2570 | 1593 | 0.620× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.12e+04 | 1.304e+04 | 0.615× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 337.3 | 206.9 | 0.613× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5920 | 3630 | 0.613× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2762 | 1689 | 0.611× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.364e+04 | 1.423e+04 | 0.602× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4717 | 2828 | 0.600× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.041e+04 | 6179 | 0.594× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9316 | 5499 | 0.590× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.364e+04 | 1.383e+04 | 0.585× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1250 | 731.3 | 0.585× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.041e+04 | 6085 | 0.585× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3549 | 2052 | 0.578× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 337.3 | 194.8 | 0.578× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.318e+04 | 7609 | 0.577× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7514 | 4321 | 0.575× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3549 | 2027 | 0.571× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.939e+04 | 1.096e+04 | 0.565× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9592 | 5408 | 0.564× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4457 | 2508 | 0.563× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 187 | 105 | 0.562× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.005e+04 | 5602 | 0.558× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9592 | 5241 | 0.546× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4337 | 2358 | 0.544× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2176 | 1183 | 0.544× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1601 | 868 | 0.542× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4206 | 2273 | 0.540× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6502 | 3490 | 0.537× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 285.8 | 152.5 | 0.533× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8800 | 4651 | 0.528× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5630 | 2974 | 0.528× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2270 | 1198 | 0.528× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 459.6 | 241.4 | 0.525× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2063 | 1045 | 0.506× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8008 | 4049 | 0.506× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.1e+04 | 5524 | 0.502× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.101e+04 | 1.052e+04 | 0.501× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3896 | 1948 | 0.500× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.314e+04 | 6523 | 0.497× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2297 | 1127 | 0.491× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6875 | 3372 | 0.491× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 459.6 | 222.6 | 0.484× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 285.8 | 136 | 0.476× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.458e+04 | 6756 | 0.463× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1345 | 622.8 | 0.463× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.749e+04 | 1.272e+04 | 0.463× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2822 | 1303 | 0.462× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3501 | 1612 | 0.460× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2421 | 1110 | 0.459× | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2260 | 1026 | 0.454× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 162.7 | 72.81 | 0.448× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9944 | 4415 | 0.444× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.749e+04 | 1.215e+04 | 0.442× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8854 | 3912 | 0.442× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 162.7 | 71.46 | 0.439× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9944 | 4364 | 0.439× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8860 | 3812 | 0.430× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2903 | 1246 | 0.429× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4629 | 1983 | 0.428× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 750.7 | 320.4 | 0.427× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2903 | 1232 | 0.424× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 308.7 | 129.7 | 0.420× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7037 | 2939 | 0.418× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 116.3 | 48.14 | 0.414× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.1e+04 | 4526 | 0.411× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5547 | 2280 | 0.411× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2996 | 1226 | 0.409× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5526 | 2258 | 0.409× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 174.7 | 71.4 | 0.409× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4224 | 1705 | 0.404× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.101e+04 | 8334 | 0.397× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1250 | 493.5 | 0.395× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.12e+04 | 8364 | 0.395× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2415 | 940.5 | 0.389× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 308.7 | 119.3 | 0.386× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5869 | 2264 | 0.386× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3100 | 1183 | 0.382× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8854 | 3360 | 0.379× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1601 | 604 | 0.377× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9475 | 3573 | 0.377× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 174.7 | 63.7 | 0.365× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7342 | 2669 | 0.364× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.085e+04 | 3931 | 0.362× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6875 | 2420 | 0.352× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2063 | 723.5 | 0.351× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1793 | 622.5 | 0.347× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.085e+04 | 3708 | 0.342× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.11e+04 | 3794 | 0.342× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2406 | 815.2 | 0.339× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5547 | 1859 | 0.335× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6691 | 2233 | 0.334× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2270 | 754.4 | 0.332× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2090 | 688.4 | 0.329× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3896 | 1282 | 0.329× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2822 | 923.6 | 0.327× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 244.4 | 78.44 | 0.321× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3552 | 1139 | 0.321× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3552 | 1139 | 0.321× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1815 | 570.5 | 0.314× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1345 | 422.5 | 0.314× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 374.1 | 116.9 | 0.312× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.458e+04 | 4539 | 0.311× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7037 | 2169 | 0.308× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.11e+04 | 3390 | 0.305× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4206 | 1283 | 0.305× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9475 | 2878 | 0.304× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2625 | 782.1 | 0.298× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1102 | 325.3 | 0.295× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2428 | 698.3 | 0.288× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 109.4 | 30.52 | 0.279× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4629 | 1282 | 0.277× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2460 | 680.5 | 0.277× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7342 | 1974 | 0.269× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 750.7 | 201.6 | 0.269× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 327.9 | 87.35 | 0.266× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.4 | 90.01 | 0.255× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 347.5 | 88.46 | 0.255× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 363.8 | 90.46 | 0.249× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1793 | 414 | 0.231× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1102 | 231.6 | 0.210× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4940 | 995.3 | 0.201× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 137.7 | 24.65 | 0.179× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1815 | 313.6 | 0.173× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.2 | 21.71 | 0.139× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 155.5 | 21.29 | 0.137× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142 | 18.17 | 0.128× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 109.4 | 11.64 | 0.106× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5869 | 524.3 | 0.089× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.936e+04 | 1575 | 0.081× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2176 | 159 | 0.073× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 214.8 | 12.24 | 0.057× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6502 | 369.2 | 0.057× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 212.4 | 11.72 | 0.055× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5526 | 288 | 0.052× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 211.2 | 10.28 | 0.049× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 206.2 | 9.099 | 0.044× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2996 | 120.1 | 0.040× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2428 | 95.16 | 0.039× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 187 | 5.338 | 0.029× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2297 | 47.11 | 0.021× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2486 | 23.39 | 0.009× | **NO** | competitive |
