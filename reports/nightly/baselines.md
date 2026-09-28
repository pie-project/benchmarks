# pie vs baselines (latest, best-of-recipe)

| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 3927 | 2.783e+04 | 7.087× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1448 | 1.01e+04 | 6.978× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3927 | 2.72e+04 | 6.928× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 580.2 | 2995 | 5.162× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2436 | 1.242e+04 | 5.099× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2436 | 1.241e+04 | 5.096× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4224 | 1.955e+04 | 4.630× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4224 | 1.876e+04 | 4.443× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1229 | 5191 | 4.224× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2244 | 9089 | 4.050× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5585 | 1.818e+04 | 3.254× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1622 | 5248 | 3.236× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5585 | 1.767e+04 | 3.164× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 839.1 | 2610 | 3.110× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4177 | 1.232e+04 | 2.950× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1153 | 3282 | 2.848× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4177 | 1.185e+04 | 2.838× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 585.7 | 1548 | 2.643× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2318 | 5811 | 2.507× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6223 | 1.543e+04 | 2.479× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3216 | 7667 | 2.384× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1950 | 4491 | 2.303× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 5591 | 1.287e+04 | 2.302× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6223 | 1.41e+04 | 2.265× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 95.24 | 215.1 | 2.258× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 5591 | 1.223e+04 | 2.187× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1312 | 2855 | 2.176× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 271.7 | 585.3 | 2.154× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 294.5 | 616.1 | 2.092× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1950 | 4056 | 2.080× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4969 | 1.029e+04 | 2.070× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 453.1 | 933.5 | 2.060× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1412 | 2906 | 2.058× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1164 | 2382 | 2.047× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6492 | 1.322e+04 | 2.037× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1164 | 2370 | 2.037× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 271.6 | 553.2 | 2.036× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4178 | 8505 | 2.036× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1353 | 2699 | 1.995× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 3216 | 6349 | 1.974× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4178 | 8247 | 1.974× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2318 | 4539 | 1.958× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.648e+04 | 3.203e+04 | 1.944× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.87e+04 | 5.406e+04 | 1.884× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6412 | 1.186e+04 | 1.850× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 815.4 | 1489 | 1.826× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6705 | 1.221e+04 | 1.821× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6653 | 1.173e+04 | 1.764× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 132.2 | 232.7 | 1.760× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.265e+04 | 3.879e+04 | 1.713× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 237.4 | 397.9 | 1.676× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1047 | 1746 | 1.668× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3.1e+04 | 5.153e+04 | 1.663× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9821 | 1.613e+04 | 1.642× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6705 | 1.077e+04 | 1.606× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 777 | 1237 | 1.592× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3244 | 5134 | 1.583× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 113.5 | 179.5 | 1.582× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.918e+04 | 3.033e+04 | 1.582× **pie trails** | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 1149 | 1808 | 1.574× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 237.4 | 373.1 | 1.572× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1918 | 2982 | 1.554× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.583e+04 | 2.423e+04 | 1.531× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 180 | 275.5 | 1.530× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1412 | 2147 | 1.520× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5435 | 8214 | 1.511× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 198.2 | 296.1 | 1.493× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 207.5 | 309.4 | 1.491× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4242 | 6235 | 1.470× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.87e+04 | 4.19e+04 | 1.460× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.049e+04 | 1.53e+04 | 1.458× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 217.1 | 316.4 | 1.458× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 180 | 261 | 1.450× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 170.3 | 245.9 | 1.444× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 113.5 | 159.8 | 1.409× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4121 | 5754 | 1.396× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 839.1 | 1169 | 1.393× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5610 | 7780 | 1.387× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 217.1 | 298.4 | 1.375× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2150 | 2950 | 1.372× **pie trails** | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2608 | 3557 | 1.364× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 107.9 | 146.5 | 1.358× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5890 | 7975 | 1.354× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4191 | 5672 | 1.354× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 53.73 | 72.35 | 1.346× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.049e+04 | 1.401e+04 | 1.335× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.457e+04 | 1.91e+04 | 1.312× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2787 | 3619 | 1.298× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 73.59 | 94.09 | 1.279× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 680.6 | 867.5 | 1.275× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 207.5 | 263.4 | 1.270× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 122.5 | 154.8 | 1.264× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 196.7 | 248.6 | 1.264× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1345 | 1693 | 1.258× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3244 | 4078 | 1.257× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6558 | 8213 | 1.252× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 4105 | 5085 | 1.239× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.457e+04 | 1.773e+04 | 1.217× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 1047 | 1264 | 1.208× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1149 | 1385 | 1.206× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 36.91 | 44.29 | 1.200× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 133.4 | 159.9 | 1.199× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 136.4 | 163.3 | 1.198× **pie trails** | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3.1e+04 | 3.699e+04 | 1.193× **pie trails** | **NO** | competitive |
| l40s-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 950 | 1125 | 1.185× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 53.73 | 62.83 | 1.169× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 419.3 | 485.2 | 1.157× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 584.8 | 675.7 | 1.155× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 562.6 | 647.6 | 1.151× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 244.4 | 280.8 | 1.149× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9821 | 1.126e+04 | 1.147× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 559 | 639.8 | 1.145× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1795 | 2033 | 1.132× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 101.2 | 114.6 | 1.132× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 31.33 | 35.16 | 1.122× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 561 | 619.8 | 1.105× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 26.13 | 28.72 | 1.099× **pie trails** | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 46.56 | 51.15 | 1.099× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.3 | 127.6 | 1.097× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 43.87 | 47.85 | 1.091× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 64.2 | 69.48 | 1.082× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 89.53 | 96.78 | 1.081× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 101.2 | 108.8 | 1.075× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.75 | 97.29 | 1.072× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 586.8 | 627.4 | 1.069× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 562.6 | 601.3 | 1.069× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 101.3 | 108.1 | 1.067× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 607.7 | 647.8 | 1.066× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 584.8 | 621.9 | 1.063× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 114.3 | 121.5 | 1.063× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 79.93 | 84.32 | 1.055× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 438.1 | 461 | 1.052× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 343.7 | 361.3 | 1.051× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 559 | 586.9 | 1.050× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2097 | 2200 | 1.049× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.8 | 105.5 | 1.047× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 327.9 | 343.1 | 1.046× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 447 | 467.5 | 1.046× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 517.6 | 540.9 | 1.045× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 101 | 105.5 | 1.045× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.26 | 94.21 | 1.044× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 662.5 | 691 | 1.043× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 800.6 | 834 | 1.042× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 355.8 | 370.6 | 1.041× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 214 | 222.3 | 1.039× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 217.3 | 225.5 | 1.038× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 774.8 | 802.8 | 1.036× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4940 | 5112 | 1.035× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 437.1 | 452 | 1.034× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 6722 | 6933 | 1.031× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 47.36 | 48.83 | 1.031× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2787 | 2871 | 1.030× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 522.1 | 536.9 | 1.028× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 662.5 | 680.9 | 1.028× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 47.03 | 48.29 | 1.027× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 561 | 574.4 | 1.024× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 342.8 | 350.9 | 1.024× **pie trails** | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 341.1 | 348.7 | 1.022× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.52 | 92.39 | 1.021× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4329 | 4412 | 1.019× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 430.2 | 438.2 | 1.019× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 591.3 | 602.2 | 1.018× **pie trails** | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 89.37 | 90.86 | 1.017× **pie trails** | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.186e+04 | 2.221e+04 | 1.016× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 363.8 | 369.6 | 1.016× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 353.4 | 358.8 | 1.015× **pie trails** | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 125.6 | 127.5 | 1.015× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 480.3 | 487 | 1.014× **pie trails** | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 107.9 | 109.3 | 1.013× **pie trails** | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 347.5 | 352 | 1.013× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3302 | 3344 | 1.013× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 441.3 | 446.3 | 1.011× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 497.5 | 502.9 | 1.011× **pie trails** | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 100.4 | 101.2 | 1.008× **pie trails** | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 90.21 | 90.87 | 1.007× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 507.5 | 509.6 | 1.004× **pie trails** | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 47.19 | 47.37 | 1.004× **pie trails** | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 495.4 | 497.1 | 1.004× **pie trails** | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 99.73 | 99.98 | 1.003× **pie trails** | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 421.4 | 422.4 | 1.002× **pie trails** | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.458e+04 | 2.464e+04 | 1.002× **pie trails** | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 6722 | 6729 | 1.001× **pie trails** | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2731 | 2730 | 1.000× | **NO** | competitive |
| pro6000-x2 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 45.66 | 45.57 | 0.998× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 475.5 | 472.4 | 0.994× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 28.64 | 28.43 | 0.993× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.352e+04 | 2.332e+04 | 0.991× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 502.9 | 498.6 | 0.991× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2250 | 2221 | 0.987× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 88.32 | 87.14 | 0.987× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.186e+04 | 2.157e+04 | 0.987× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.9 | 132.4 | 0.981× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 714.7 | 700.9 | 0.981× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 134.4 | 131.8 | 0.980× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 157.9 | 154.8 | 0.980× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 426.3 | 416.6 | 0.977× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 156.2 | 152.5 | 0.976× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 467.7 | 456 | 0.975× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 577.5 | 563 | 0.975× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6329 | 6161 | 0.973× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 741.3 | 718.2 | 0.969× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 47.14 | 45.51 | 0.965× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 286.2 | 275.7 | 0.963× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 244.7 | 235.2 | 0.961× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c32 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 3145 | 3021 | 0.961× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 244.7 | 235 | 0.960× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2026 | 1943 | 0.959× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 58.22 | 55.8 | 0.958× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 191.8 | 183.5 | 0.957× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 214.5 | 204.7 | 0.954× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 98.4 | 93.83 | 0.954× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9131 | 8706 | 0.953× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 200.1 | 190.7 | 0.953× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 63.23 | 60.22 | 0.953× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2787 | 2650 | 0.951× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 494 | 469.3 | 0.950× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 662.2 | 628.8 | 0.950× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 723.2 | 686.5 | 0.949× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1770 | 1678 | 0.948× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 470.6 | 445.7 | 0.947× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 155.5 | 146.9 | 0.945× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 122.5 | 115.4 | 0.942× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 638.3 | 601.3 | 0.942× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 255.7 | 239.7 | 0.937× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 89.82 | 83.94 | 0.935× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 522.1 | 487.1 | 0.933× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 199.4 | 185.5 | 0.930× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4121 | 3824 | 0.928× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 66.76 | 61.87 | 0.927× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2264 | 2095 | 0.925× | **NO** | competitive |
| pro6000-x2 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 191.8 | 177.1 | 0.924× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 248.3 | 229.2 | 0.923× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 294.3 | 271.4 | 0.922× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 650.2 | 597.6 | 0.919× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 507.5 | 465.9 | 0.918× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 714.7 | 656.2 | 0.918× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 715.8 | 657.1 | 0.918× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.454e+04 | 2.248e+04 | 0.916× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 242.1 | 221.7 | 0.916× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 282.5 | 258.5 | 0.915× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4329 | 3960 | 0.915× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 75.8 | 69.23 | 0.913× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 110.8 | 101.1 | 0.912× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.865e+04 | 2.603e+04 | 0.908× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 152.8 | 138.7 | 0.908× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2264 | 2054 | 0.907× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 463.6 | 419.7 | 0.905× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 741.3 | 669.6 | 0.903× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.68 | 62.88 | 0.903× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 733.7 | 660.9 | 0.901× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 248.3 | 223.4 | 0.900× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 69.8 | 62.76 | 0.899× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 723.2 | 650.1 | 0.899× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 252.8 | 226.9 | 0.898× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 638.1 | 572.1 | 0.897× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5758 | 5163 | 0.897× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 437.5 | 391.5 | 0.895× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 125.6 | 112.3 | 0.894× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 419.3 | 373.8 | 0.892× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 198.2 | 176.5 | 0.891× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 132.3 | 117.7 | 0.890× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 236.2 | 210.1 | 0.889× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 435.4 | 386.9 | 0.889× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 133.7 | 118.7 | 0.887× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 262.2 | 231.9 | 0.884× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 355.8 | 314.7 | 0.884× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.9 | 103.3 | 0.884× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 497.9 | 440.1 | 0.884× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 495.4 | 437.5 | 0.883× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 343.7 | 303.5 | 0.883× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 715.8 | 631.9 | 0.883× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 208.2 | 183.6 | 0.882× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 133.4 | 117.5 | 0.881× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.265e+04 | 1.992e+04 | 0.880× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 97.29 | 85.57 | 0.879× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 118.3 | 104 | 0.879× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 286.2 | 251.6 | 0.879× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 341.1 | 299.2 | 0.877× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 255.7 | 223.9 | 0.876× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 800.6 | 699.6 | 0.874× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 82.27 | 71.87 | 0.874× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 245.6 | 214.5 | 0.873× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 638.3 | 557.1 | 0.873× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 392.2 | 342 | 0.872× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 662.2 | 575.9 | 0.870× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 136.4 | 118.2 | 0.867× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 276.9 | 239.7 | 0.866× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 236.2 | 203.8 | 0.863× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 84.59 | 72.99 | 0.863× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 252.8 | 218 | 0.862× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 242.1 | 208.7 | 0.862× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 733.7 | 630.5 | 0.859× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.6 | 105.9 | 0.857× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 437.5 | 374.6 | 0.856× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1608 | 1375 | 0.855× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 262.2 | 223.6 | 0.853× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6968 | 5928 | 0.851× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.02 | 74.02 | 0.851× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 123.7 | 105.2 | 0.850× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 282.5 | 240 | 0.849× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 245.6 | 207.6 | 0.845× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 192.4 | 162.5 | 0.844× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 650.2 | 548.8 | 0.844× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 87.33 | 73.63 | 0.843× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 311.1 | 261.9 | 0.842× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 342.8 | 287.8 | 0.840× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 497.9 | 417.7 | 0.839× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 517.6 | 433.5 | 0.838× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 294.3 | 246.4 | 0.837× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 106.8 | 89.45 | 0.837× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 774.8 | 647.3 | 0.835× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 638.1 | 532.5 | 0.835× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 502.9 | 417.2 | 0.830× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 276.9 | 229.6 | 0.829× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.865e+04 | 2.374e+04 | 0.829× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.336e+04 | 1.101e+04 | 0.824× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1276 | 1049 | 0.822× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 438.1 | 357.5 | 0.816× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.336e+04 | 1.087e+04 | 0.814× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 101.2 | 82.25 | 0.813× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 435.4 | 353.3 | 0.812× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8104 | 6571 | 0.811× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6968 | 5643 | 0.810× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 437.1 | 353.6 | 0.809× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4224 | 3401 | 0.805× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.75 | 73.06 | 0.805× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.809e+04 | 1.453e+04 | 0.804× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 89.53 | 71.76 | 0.802× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 447 | 355.6 | 0.796× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-512-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 115.7 | 91.96 | 0.795× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2120 | 1685 | 0.795× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.681e+04 | 1.335e+04 | 0.794× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 101.2 | 79.98 | 0.790× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 116.2 | 91.52 | 0.787× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.51e+04 | 1.183e+04 | 0.783× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.361e+04 | 1.845e+04 | 0.781× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-2k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 421.4 | 328.9 | 0.780× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6586 | 5127 | 0.778× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3.019e+04 | 2.347e+04 | 0.777× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 101.3 | 78.54 | 0.776× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-1k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 430.2 | 333.3 | 0.775× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 668.2 | 513.7 | 0.769× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.454e+04 | 1.882e+04 | 0.767× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1896 | 1449 | 0.764× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2197 | 1679 | 0.764× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.47e+04 | 1.122e+04 | 0.763× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5880 | 4485 | 0.763× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 377.1 | 287 | 0.761× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.8 | 76.6 | 0.760× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 213.8 | 162.2 | 0.759× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6838 | 5181 | 0.758× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.26 | 68.32 | 0.757× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 213.8 | 161.8 | 0.757× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1462 | 1106 | 0.757× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 668.2 | 505.5 | 0.757× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3.019e+04 | 2.283e+04 | 0.756× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1302 | 983.3 | 0.755× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.21 | 68.1 | 0.755× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.47e+04 | 1.105e+04 | 0.751× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 590.7 | 441.9 | 0.748× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 42.11 | 31.41 | 0.746× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 101 | 75.26 | 0.745× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2555 | 1898 | 0.743× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 441.3 | 327.7 | 0.743× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.681e+04 | 1.244e+04 | 0.740× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 100.4 | 74.24 | 0.739× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 90.52 | 66.8 | 0.738× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 89.37 | 65.79 | 0.736× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8800 | 6451 | 0.733× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 47.36 | 34.6 | 0.731× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 524 | 380.5 | 0.726× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.648e+04 | 1.196e+04 | 0.726× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 224.4 | 162.8 | 0.726× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3431 | 2484 | 0.724× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.936e+04 | 1.396e+04 | 0.721× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 47.03 | 33.9 | 0.721× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 311.1 | 223.2 | 0.717× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c64 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 4105 | 2938 | 0.716× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | ss-128-64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 426.3 | 305 | 0.716× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9300 | 6642 | 0.714× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.186e+04 | 8444 | 0.712× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 88.32 | 62.84 | 0.711× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5548 | 3933 | 0.709× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.352e+04 | 1.664e+04 | 0.708× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5669 | 4008 | 0.707× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 590.7 | 417.6 | 0.707× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 47.19 | 33.33 | 0.706× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2961 | 2087 | 0.705× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.03e+04 | 7230 | 0.702× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2913 | 2041 | 0.701× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 392.2 | 274.5 | 0.700× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 89.82 | 62.43 | 0.695× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 224.4 | 155.5 | 0.693× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.321e+04 | 9121 | 0.690× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.892e+04 | 1.304e+04 | 0.689× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7514 | 5170 | 0.688× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 142 | 97.2 | 0.685× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c32 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 3145 | 2138 | 0.680× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 437.4 | 296.7 | 0.678× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5548 | 3743 | 0.675× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 47.14 | 31.76 | 0.674× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2427 | 1634 | 0.673× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9697 | 6460 | 0.666× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4200 | 2794 | 0.665× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6639 | 4404 | 0.663× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.311e+04 | 8661 | 0.661× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 328 | 216.1 | 0.659× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 257.6 | 169.1 | 0.657× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9131 | 5949 | 0.652× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.26e+04 | 8206 | 0.651× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.547e+04 | 1.658e+04 | 0.651× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9697 | 6303 | 0.650× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4625 | 3001 | 0.649× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.26e+04 | 8155 | 0.647× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.321e+04 | 8439 | 0.639× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 257.6 | 163.2 | 0.633× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7060 | 4452 | 0.631× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.186e+04 | 7475 | 0.630× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 377.1 | 237.1 | 0.629× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.547e+04 | 1.593e+04 | 0.625× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2570 | 1606 | 0.625× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2570 | 1593 | 0.620× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1915 | 1187 | 0.620× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 395 | 244.7 | 0.619× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3582 | 2214 | 0.618× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 337.3 | 206.9 | 0.613× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.78e+04 | 1.079e+04 | 0.606× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2787 | 1689 | 0.606× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.688e+04 | 1.023e+04 | 0.606× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6796 | 4108 | 0.605× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.364e+04 | 1.423e+04 | 0.602× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4711 | 2828 | 0.600× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.326e+04 | 7927 | 0.598× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3302 | 1970 | 0.597× | **NO** | competitive |
| pro6000-x2 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 395 | 235.3 | 0.596× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.041e+04 | 6179 | 0.594× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.326e+04 | 7863 | 0.593× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5758 | 3404 | 0.591× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.03e+04 | 6064 | 0.589× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.364e+04 | 1.383e+04 | 0.585× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.041e+04 | 6085 | 0.585× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.695e+04 | 9874 | 0.583× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3549 | 2052 | 0.578× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 337.3 | 194.8 | 0.578× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.318e+04 | 7609 | 0.577× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8351 | 4818 | 0.577× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 180.7 | 104.2 | 0.577× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7514 | 4321 | 0.575× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3394 | 1950 | 0.575× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3549 | 2027 | 0.571× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 328 | 185.3 | 0.565× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6586 | 3715 | 0.564× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4457 | 2508 | 0.563× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3582 | 1999 | 0.558× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9939 | 5524 | 0.556× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.007e+04 | 5590 | 0.555× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5669 | 3145 | 0.555× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.562e+04 | 8663 | 0.554× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 189.5 | 105 | 0.554× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 244.8 | 134.1 | 0.548× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.918e+04 | 1.589e+04 | 0.544× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2176 | 1183 | 0.544× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4206 | 2273 | 0.540× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1610 | 868 | 0.539× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6502 | 3490 | 0.537× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4400 | 2358 | 0.536× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2224 | 1187 | 0.534× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.562e+04 | 8341 | 0.534× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8800 | 4651 | 0.528× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2270 | 1198 | 0.528× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 459.6 | 241.4 | 0.525× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.695e+04 | 8888 | 0.524× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.809e+04 | 9470 | 0.524× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7890 | 4049 | 0.513× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2200 | 1127 | 0.512× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | vllm 0.30.0 | output_tok_s | 2063 | 1045 | 0.506× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1203 | 606.6 | 0.504× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 303 | 152.5 | 0.503× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.547e+04 | 7783 | 0.503× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.101e+04 | 1.052e+04 | 0.501× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8214 | 4107 | 0.500× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3896 | 1948 | 0.500× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 390.1 | 194.9 | 0.500× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.311e+04 | 6523 | 0.498× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6785 | 3372 | 0.497× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6826 | 3382 | 0.495× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2913 | 1438 | 0.494× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.327e+04 | 1.146e+04 | 0.493× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 390.1 | 192.1 | 0.492× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.928e+04 | 1.419e+04 | 0.485× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 459.6 | 222.6 | 0.484× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2694 | 1300 | 0.482× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2014 | 968.4 | 0.481× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 518.4 | 248.9 | 0.480× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8214 | 3929 | 0.478× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.295e+04 | 1.095e+04 | 0.477× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 244.8 | 116.7 | 0.477× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4959 | 2333 | 0.470× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.284e+04 | 1.065e+04 | 0.466× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.236e+04 | 5754 | 0.466× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.458e+04 | 6756 | 0.463× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.749e+04 | 1.272e+04 | 0.463× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1580 | 731.3 | 0.463× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2833 | 1303 | 0.460× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.688e+04 | 7737 | 0.458× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2427 | 1110 | 0.458× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.236e+04 | 5631 | 0.456× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9939 | 4526 | 0.455× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3889 | 1768 | 0.455× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.284e+04 | 1.036e+04 | 0.453× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1374 | 622.8 | 0.453× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.295e+04 | 1.038e+04 | 0.452× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.928e+04 | 1.317e+04 | 0.450× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 518.4 | 233 | 0.449× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 303 | 136 | 0.449× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.458e+04 | 1.103e+04 | 0.449× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.212e+04 | 5408 | 0.446× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 164.6 | 72.81 | 0.442× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.892e+04 | 8364 | 0.442× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2.749e+04 | 1.215e+04 | 0.442× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8351 | 3630 | 0.435× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 164.6 | 71.46 | 0.434× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1915 | 828.1 | 0.432× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.212e+04 | 5241 | 0.432× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.558e+04 | 6732 | 0.432× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 300.3 | 129.7 | 0.432× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 192.4 | 83.09 | 0.432× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8860 | 3812 | 0.430× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 4629 | 1983 | 0.428× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3771 | 1612 | 0.427× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2957 | 1246 | 0.421× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.142e+04 | 4796 | 0.420× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7050 | 2939 | 0.417× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2957 | 1232 | 0.417× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.599e+04 | 6643 | 0.415× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.112e+04 | 4617 | 0.415× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3394 | 1408 | 0.415× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 116.3 | 48.14 | 0.414× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3604 | 1483 | 0.411× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.119e+04 | 8698 | 0.410× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2996 | 1226 | 0.409× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5526 | 2258 | 0.409× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 174.7 | 71.4 | 0.409× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4224 | 1705 | 0.404× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2961 | 1183 | 0.400× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8729 | 3488 | 0.400× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 300.3 | 119.3 | 0.397× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2.101e+04 | 8334 | 0.397× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6970 | 2749 | 0.394× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8729 | 3443 | 0.394× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | mixed-256 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7060 | 2783 | 0.394× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6657 | 2585 | 0.388× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.143e+04 | 4415 | 0.386× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 5869 | 2264 | 0.386× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.143e+04 | 4364 | 0.382× | **NO** | competitive |
| h100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 442.5 | 168.2 | 0.380× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 9475 | 3573 | 0.377× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1337 | 503.2 | 0.376× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1610 | 604 | 0.375× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1236 | 460.8 | 0.373× | **NO** | competitive |
| rtx5090-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1862 | 693 | 0.372× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 174.7 | 63.7 | 0.365× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.085e+04 | 3931 | 0.362× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c32 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.558e+04 | 5602 | 0.360× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8095 | 2905 | 0.359× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6785 | 2420 | 0.357× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6414 | 2280 | 0.355× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 905.2 | 320.4 | 0.354× | **NO** | competitive |
| pro6000-x2 | kimi-k3-mini8 | c8 | text-completion-bench | tp2 | sglang 0.5.20 | output_tok_s | 2063 | 723.5 | 0.351× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.121e+04 | 3912 | 0.349× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1793 | 622.5 | 0.347× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 360.6 | 124.2 | 0.344× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | kv-oversub | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.599e+04 | 5499 | 0.344× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.085e+04 | 3708 | 0.342× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.11e+04 | 3794 | 0.342× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 7842 | 2669 | 0.340× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3864 | 1293 | 0.335× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2270 | 754.4 | 0.332× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3864 | 1282 | 0.332× | **NO** | competitive |
| a100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2080 | 688.4 | 0.331× | **NO** | competitive |
| h100-pcie-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2846 | 940.5 | 0.330× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3896 | 1282 | 0.329× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.547e+04 | 5044 | 0.326× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2833 | 923.6 | 0.326× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 197.6 | 63.95 | 0.324× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 244.4 | 78.44 | 0.321× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3552 | 1139 | 0.321× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 3552 | 1139 | 0.321× | **NO** | competitive |
| rtx4090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1661 | 532.3 | 0.320× | **NO** | competitive |
| rtx5090-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2546 | 815.2 | 0.320× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1815 | 570.5 | 0.314× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1580 | 493.5 | 0.312× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.458e+04 | 4539 | 0.311× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 974 | 302.2 | 0.310× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4-mini5 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 379.9 | 116.9 | 0.308× | **NO** | competitive |
| a100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7050 | 2169 | 0.308× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1374 | 422.5 | 0.308× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.11e+04 | 3390 | 0.305× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | kv-oversub | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4206 | 1283 | 0.305× | **NO** | competitive |
| pro6000-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 9475 | 2878 | 0.304× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 197.6 | 59.59 | 0.302× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1.121e+04 | 3360 | 0.300× | **NO** | competitive |
| pro6000-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2625 | 782.1 | 0.298× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6970 | 2076 | 0.298× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1098 | 325.3 | 0.296× | **NO** | competitive |
| l40s-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 6414 | 1859 | 0.290× | **NO** | competitive |
| l40s-x1 | gemma-4-e4b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 1618 | 466.8 | 0.288× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 2428 | 698.3 | 0.288× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 3072 | 858.4 | 0.279× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 109.4 | 30.52 | 0.279× | **NO** | competitive |
| h100-pcie-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 8049 | 2233 | 0.277× | **NO** | competitive |
| pro6000-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4629 | 1282 | 0.277× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2460 | 680.5 | 0.277× | **NO** | competitive |
| rtx5090-x1 | qwen3.5-0.8b-bf16 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.142e+04 | 3109 | 0.272× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 327.9 | 87.35 | 0.266× | **NO** | competitive |
| rtx5090-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4959 | 1281 | 0.258× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 353.4 | 90.01 | 0.255× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 347.5 | 88.46 | 0.255× | **NO** | competitive |
| h100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1337 | 337.3 | 0.252× | **NO** | competitive |
| rtx4090-x1 | qwen3.5-0.8b-bf16 | c8 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 7842 | 1974 | 0.252× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 363.8 | 90.46 | 0.249× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1793 | 414 | 0.231× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 141.6 | 31.68 | 0.224× | **NO** | competitive |
| l40s-x1 | kimi-k3-mini8 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 905.2 | 201.6 | 0.223× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 467.7 | 102 | 0.218× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 475.5 | 101.6 | 0.214× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 470.6 | 99.66 | 0.212× | **NO** | competitive |
| a100-pcie-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1098 | 231.6 | 0.211× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 463.6 | 96.35 | 0.208× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6796 | 1411 | 0.208× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 4940 | 995.3 | 0.201× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | vllm 0.30.0 | output_tok_s | 141.5 | 24.65 | 0.174× | **NO** | competitive |
| pro6000-x1 | kimi-k3-mini8 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1815 | 313.6 | 0.173× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 156.2 | 21.71 | 0.139× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 155.5 | 21.29 | 0.137× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 142 | 18.17 | 0.128× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | lc-32k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 109.4 | 11.64 | 0.106× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.007e+04 | 987.6 | 0.098× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5869 | 524.3 | 0.089× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4-mini5 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.936e+04 | 1575 | 0.081× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | mixed-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2176 | 159 | 0.073× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 8095 | 539 | 0.067× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 6502 | 369.2 | 0.057× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-512-256 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 217.3 | 12.24 | 0.056× | **NO** | competitive |
| rtx4090-x1 | gpt-oss-20b-mxfp4-mini5 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 1.112e+04 | 624.2 | 0.056× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | ss-128-64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 214 | 11.72 | 0.055× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c32 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 5526 | 288 | 0.052× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-1k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 214.5 | 10.28 | 0.048× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-2k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 208.2 | 9.099 | 0.044× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2996 | 120.1 | 0.040× | **NO** | competitive |
| l40s-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2428 | 95.16 | 0.039× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | lc-8k-128 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 189.5 | 5.338 | 0.028× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | c8 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2200 | 47.11 | 0.021× | **NO** | competitive |
| a100-pcie-x1 | gpt-oss-20b-mxfp4 | prefix-1k-x64 | text-completion-bench | tp1 | sglang 0.5.20 | output_tok_s | 2555 | 23.39 | 0.009× | **NO** | competitive |
