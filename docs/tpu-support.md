# TPU support (pie engine-xla)

Measured on 2026-10-08 on a Cloud TPU v6e-1 (one Trillium chip, 32 GB HBM, us-east5-b) at pie `da839689b` with libtpu 0.0.48. Each model ran pie's own device test `crates/engine-xla/tests/a_model_speaks_on_the_device.rs` on an artifact made by `pie model import` (built with `--features xla`). The test prefills "The capital of France is", decodes 16 greedy tokens, replays the prompt one token at a time, and checks that a batch of three lanes answers what each lane answers alone. Every `kernels_*` device test and `pjrt_runs_a_built_module` passed.

Miniatures (a few layers and experts cut from a frontier checkpoint by `bench/shrink_checkpoint.py`) are expected to print nonsense, so for them "generates" means the test ran and the prefill and token walks agree. It does not mean the text reads well.

| family | variant tested | chips | builds | loads | generates | notes |
|---|---|---|---|---|---|---|
| Qwen3.5 (control) | qwen35-d0.8b, bf16 and u4g64 | 1 | yes | yes | yes, " Paris.\nThe capital of France is Paris." | test passes |
| Qwen3.6 dense (qwen_3) | qwen36-27b-u4g64 (mlx-community 4-bit) | 1 | yes | yes | yes, " Paris.\n\n<think>…" | test passes |
| Qwen3.6 MoE (qwen3_6_moe) | qwen36-35b-a3b-u4g64 (mlx-community 4-bit) | 1 | yes | yes | yes, " Paris, a city renowned for its iconic landmarks…" | test passes |
| Qwen3.8 Flash Next (qwen_4) | qwen38-flash-next-u4g64-u2g128 miniature (4 layers, 16 experts) | 1 | yes | yes | runs (miniature) | prefill and token walks agree; one batched lane diverges after 4 tokens |
| Muse (muse_glimmer) | muse-glimmer-30b-u4g64 (imported from bf16) | 1 | yes | yes | yes, " Paris. The capital of Spain is Madrid…" | test passes |
| GLM (glm_5_next) | glm53-flash-mini-u4g64-u4g64 miniature (8 layers, 32 experts) | 1 | yes | yes | runs (miniature) | test passes |
| Kimi (kimi_k3) | kimik3-mini-bf16-mxfp4 miniature (8 layers, 32 experts) | 1 | yes | yes | runs (miniature) | prefill and token walks agree (max logit gap 1.43); one batched lane diverges after 4 tokens |
| DeepSeek V4 (deepseek_v4) | dsv4-flash-mini-bf16-mxfp4 miniature | 1 | yes | yes, with pie #853 | runs (miniature) | without #853, no catalog row reads the MXFP4 experts in mlx-community/DeepSeek-V4-Flash-bf16; the max logit gap between walks is 9.8 |
| DeepSeek V4.1 (deepseek_v41) | dsv41-flash-mini-bf16-mxfp4 miniature | 1 | yes | yes, with pie #854 and `engram_token_map.py` | runs (miniature) | without #854, the import cannot find `engram_token_map.safetensors`; one batched lane diverges |
| Gemma 4 dense (gemma_4) | gemma4-e4b-bf16 | 1 | yes | yes | partly | the test passes; with no BOS it echoes the prompt, and with BOS it answers " Paris" and then "......" (no reference run yet) |
| Gemma 4 MoE (gemma4_moe) | gemma4-26b-a4b-u4g64 (mlx-community 4-bit) | 1 | yes | yes | **no** | the prefill and token walks disagree (max logit gap about 4), batched lanes disagree, and every `PIE_XLA_MOE_PATH` gives the same failure, so the fault is outside the MoE formulation |
| GLM 5 (glm_5) | not tested | 8 (v6e-8) | | | | glm5-a12b bf16 is 192 GiB; there is no single-chip row |

## Not tested: models that need several chips

engine-xla runs one replica on one device. Collectives answer only a world of one, and every weight plane stays resident on that device. No full DeepSeek V4 or V4.1 Flash row and no Kimi K3 row has tp > 1 in the catalog. Even on a larger slice, none of these models can run until engine-xla compiles for several replicas and lands banded weights. That is engine work, not a configuration change.

| model | weights | smallest slice | cost/hour |
|---|---|---|---|
| DeepSeek V4 Flash (dsv4-flash-full-u4g64-u2g64) | about 90 GiB | v6e-4 | $10.80 |
| DeepSeek V4.1 Flash (dsv41-flash-bf16-mxfp4) | about 650 GiB | v6e-32 | $86.40 |
| Kimi K3 (full; no catalog row) | about 1.45 TB | v6e-64 | $172.80 |
| GLM-5.3 Flash (glm53-flash-u8g64-u2g64) | about 97 GiB | v6e-4 | $10.80 |
| GLM-5 (glm5-a12b bf16) | about 192 GiB | v6e-8 | $21.60 |
| Qwen3.8 Flash Next (full, u4g64-u2g128) | about 66 GiB | v6e-4 | $10.80 |
| Gemma 4 31B / Muse 30B / Qwen3.6 27B, bf16 | 52-58 GiB | v6e-4 | $10.80 (their 4-bit rows fit on one chip) |

_Last reviewed: 2026-10-09._
