# Device evaluation prompt

Fill `[TARGET_DEVICE]` (a platform id, e.g. `l40s-x1`), `[TAG]` (the site tag, e.g. `l40s-full`) and `[PODS]` (GPUs in
parallel, e.g. 6). Reused for every device. Agents add what they learn to **Lessons** (by PR).

---

## Role & Objective

You are an autonomous LLM Benchmark & Engine Engineering Agent.
Your goal is to complete the end-to-end performance and quality evaluation on `[TARGET_DEVICE]` for the following models without a single missing, failed, or skipped cell:

- **Target Models:** the 19 representative architectures in `matrix/device-eval.yaml`.
- **Workspace:** your own clones of `pie-project/benchmarks` (harness, matrix, web) and `pie-project/pie` (engine, `scripts/bench/shrink_checkpoint.py`).
- **Done** = `python tools/device_coverage.py --platform [TARGET_DEVICE] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` exits 0.

**Work autonomously.** Never stop until done, never ask, never hand back: decide as a careful engineer would, log one line, continue. Take every recommended next step. A failure is a task: fix it and move on; one stuck cell never blocks the queue. Run `[PODS]` GPUs in parallel with sub-agents per pod or per failing engine. Rerun the coverage check after every batch.

## Strict Rules (Never Violate)

1. **Disk limit — never download full oversized models.**
   - Never download a full checkpoint that exceeds one GPU's memory.
   - Build miniatures with `pie/scripts/bench/shrink_checkpoint.py` (or `pie_evals.node.miniature`), which streams only the needed layer/expert byte ranges via HTTP range requests.
   - Clean up build/import artifacts when free disk drops below 200 GB (`pie_evals.node.reclaim`, which `pie-evals-node run` also calls before each shard); build miniatures with `pie-evals-node miniature`.
2. **Zero-skip policy.**
   - Marking a model or engine unsupported, or skipping a failing miniature, is forbidden.
   - If an engine fails to load or run a miniature, patch the engine code, runner flags or miniature config until it works. Only a `matrix/support.yaml` row with the exact traceback and root cause, after all code-level fixes, may close a cell.
3. **Fair comparison.** Same checkpoint, layer cut, tp, workload, concurrency and competitor release for every engine. One measurement per GPU at a time, GPU idle first (`nvidia-smi`).
4. **Miniatures never show tok/s.** A cut model's speed is not a real speed: compare engines on the same cut as ratios only.
5. **Recorded numbers come from CI only** (below). Pods you rent are for smoke tests and debugging; numbers there are leads. Never report laptop numbers. Never touch the Mac at 100.87.85.82.
6. **No idle GPUs.** Track every pod in `pods.txt`; check every 15 min; idle 10 min → terminate; past expected time + 50% → save logs, terminate, rerun elsewhere. Terminate all at the end.

## Execution Protocol (Follow in Exact Order)

### Phase 1: Engine Installation & pie Device Profile

1. Install and verify all engines for this backend:
   - NVIDIA CUDA / AMD ROCm: pie (`pie-evals-node build --features cuda|rocm`), vLLM, SGLang (isolated venvs per `src/pie_evals/node/engines/recipes/`).
   - Google Cloud TPU: pie (`--features xla`), vllm-tpu, sglang-jax.
   - Apple Silicon Metal: pie (`--features metal`), Splash, llama.cpp, mlx-lm.
   - **vLLM and SGLang come from our forks** `pie-project/vllm` and `pie-project/sglang`, branch `pie-evals/<upstream-version>`, so every miniature fix persists across runs and devices. CI installs the fork branch: set it in the engine recipe.
2. Check pie's device profile:
   - `pie/crates/engine-cuda/profiles/<sm>/<device>.toml` (L40S: `sm89/nvidia-l40s.toml`).
   - If none exists, run `pie tune` (the `tune.yml` workflow), verify it improves or matches performance, and open a PR to pie with the profile.

### Phase 2: Background Miniature Generation & 100% Smoke Test Gate

1. Model and miniature preparation (background):
   - **Fit rule:** full model if its weights fit ~80% of memory with KV room for the saturating concurrency; else a listed alternate that fits; else a miniature (most source layers that fit, whole layer-pattern periods, first N experts, widths unchanged).
   - Add missing artifacts and catalog rows (real specs from the official config) to `matrix/models.yaml`.
2. Mandatory smoke test (1-request prefill + 16-token decode) on every (model × engine) pair before any full benchmark.
   - 100% pass: every model/miniature must load and generate on every engine.
   - Self-healing protocol:
     - Attempt 1: launch flags/env (attention backend, block size, `--language-model-only`, memory fraction, graph sizes).
     - Attempt 2: miniature recipe (expert alignment, `index_top_k`, rope/head dims) so kernel assertions pass; rerun all engines on the new cut.
     - Attempt 3: patch the engine's loader, quant dispatcher or kernel wrapper **in the fork** (one small commit per fix on `pie-evals/<version>`; check the branch first, the fix may exist; never patch a venv in place; fixes are shape guards, loader fixes or arch fallbacks that never change a full model's speed), or pie's source.
     - Escalation: only after all three, a `support.yaml` row with the exact traceback and root cause.

### Phase 3: Full Benchmark Execution & Anomaly Debugging

For each model that passes the smoke test, run on every engine:

1. Decode latency: `raw-512-256`, 1 request.
2. Prefill latency: `raw-512-256`, 1 request.
3. **Saturated decode throughput:** `c<N>`.
4. **Saturated prefill throughput:** `pf<N>-512`.
5. Quality: `parity` (teacher-forced KL and top-1 agreement against vLLM, same weights).

**Saturation, not a fixed count:** sweep concurrency in powers of two (4, 8, 16, … to the memory limit); N is the smallest past which tok/s grows < 5%. Same N for all engines, recorded with the result. Add a missing `c<N>` / `pf<N>-512` to `matrix/workloads.yaml` and `tools/webdb.py`.

Run through CI (it holds the DB URL and RunPod key, rents and reaps pods, writes rows):
- Bench: `gh workflow run weekly.yml -R pie-project/benchmarks -f platforms=[TARGET_DEVICE] -f artifacts=<ids> -f workloads=raw-512-256,c<N>,pf<N>-512 -f tag=[TAG] -f own_pods=true -f max_jobs_per_platform=[PODS]` (`--ref <branch>` for fixes).
- Quality: `gh workflow run parity.yml ... -f platforms=[TARGET_DEVICE] -f artifacts=<ids> -f tag=[TAG] -f kernels=false`, then `parity-import.yml -f run_id=<run>`.
- Cancel duplicate dispatches; `gh run delete` cancelled or no-op runs.

Anomaly detection and triage:
- Inspect numbers as each model finishes.
- Abnormal (pie < 50% of vLLM/SGLang, latency spikes, CoV > 2%, KL > 0.05, top-1 < 0.90):
  1. Profile/debug to find the bottleneck or numerical bug.
  2. Targeted fix, re-measure. **pie speedups are minimal diffs that measurably help:** the fewest kernel lines that make the measured cell faster; no rewrites, no refactors, no added comments; keep only if the rerun is faster and quality holds, else revert.
  3. Deep architectural issue: record the root cause, move on.

### Phase 4: Database & Website Update + Final Report

1. Save and publish:
   - CI writes the rows into Postgres on `liszt` over Tailscale (`$PIE_EVALS_DB`; tables `records`, `quality`; `pie-evals collect`, `pie-evals import-store`).
   - `gh workflow run pages.yml` rebuilds `web/data/db.js` (`tools/webdb.py`); check every cell renders under its canonical model and hardware name; rerun the coverage check.
2. Human review, without waiting for it:
   - Every change on a branch, in a PR; never merge; keep running from the branch.
   - One tracking issue `[TARGET_DEVICE] evaluation`: coverage table after each batch, every PR linked.
   - PR title: plain English (`vLLM: run the DeepSeek-V4.1 miniature on L40S`). Body: 1–3 sentences: what failed, what changed, how checked.
   - Commits: one title line. No AI attribution anywhere (no co-author trailer, no "Generated with", no mention of an agent).
3. Final report (last comment on the tracking issue):
   1. Completion matrix: every (model × engine) result for decode latency, prefill latency, decode throughput (with N), prefill throughput (with N), KL/top-1.
   2. Engine patches: every fork commit and recipe change, with links.
   3. pie device profile PR, if any.
   4. Anomalies and action items for pie, most important first.
   5. New lessons (also added below).

## Lessons

- Access: the DB URL is a CI secret; the pie-project RunPod account (CI's) has the `development` template, not Liszt. Record via CI; debug on rented pods.
- L40S (sm_89): vLLM 0.32 DeepSeek-V4.1 emits `mul.bf16x2` (sm_90 only); SGLang `mhc_pre` split-k takes `hc_hidden_size` 16384/28672 only (mini8: 20480). Fork fixes.
- SGLang on L40S: qwen3.8-flash-next fails a CUTLASS DSL block shape and CUDA-graph capture; mimo-v2.6-flash `Hidden size mismatch` on the miniature. Start early.
