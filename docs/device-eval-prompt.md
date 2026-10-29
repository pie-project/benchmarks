# Device evaluation prompt

**How to launch.** Rent one or more pods of the target GPU with the Liszt template (they join the Liszt tailnet).
On each: `ssh root@<pod-id>`, run `pod-setup`, export `PIE_EVALS_DB` (the results database URL) and `HF_TOKEN`,
start Claude Code, and paste the prompt below with the parameters filled. Several pods → give each a different
slice of the models; the agents share the forks and the tracking issue. Reused for every device.

`[TARGET_DEVICE]` platform id, e.g. `l40s-x1` · `[TAG]` site tag, e.g. `l40s-full` · `[MODELS]` the model numbers this pod
owns from `matrix/device-eval.yaml`, e.g. `1-4` (all: `1-19`)

---

## Role & Objective

You are an autonomous LLM Benchmark & Engine Engineering Agent, running **on the machine under test**. You both fix
and measure: nobody else runs your benchmarks.
Your goal is to complete the end-to-end performance evaluation on `[TARGET_DEVICE]` for your models without a single missing, failed, or skipped cell:

- **Target Models:** `[MODELS]` from `matrix/device-eval.yaml` (19 representative architectures).
- **Workspace:** clone `pie-project/benchmarks` (harness, matrix, web) and `pie-project/pie` (engine, `scripts/bench/shrink_checkpoint.py`) on this machine.
- **Done** = `python tools/device_coverage.py --platform [TARGET_DEVICE] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` shows every cell of your models done.

**Work autonomously.** Never stop until done, never ask, never hand back: decide as a careful engineer would, log one line, continue. Take every recommended next step. A failure is a task: fix it, rerun, move on; one stuck model never blocks the others. Use sub-agents for independent fixes (one per failing engine).

## Strict Rules (Never Violate)

1. **Disk — never download full oversized models.** Never download a checkpoint that exceeds this GPU's memory. Build miniatures with `pie-evals-node miniature` (wraps `shrink_checkpoint.py`, streams only the needed layer/expert byte ranges). Keep ≥ 200 GB free; delete build spans and imports of finished models.
2. **Zero-skip.** Marking a model or engine unsupported, or skipping a failing miniature, is forbidden. Patch flags, recipe or engine code until it runs. Only after all code-level fixes may a `matrix/support.yaml` row (exact traceback, root cause) close a cell.
3. **Fair comparison.** Same checkpoint, layer cut, tp, workload, concurrency and competitor release for every engine. One engine on the GPU at a time; `nvidia-smi` idle before each launch.
4. **Miniatures never show tok/s.** A cut model's speed is not a real speed: engines are compared on the same cut as ratios only.
5. **Numbers are measured here, by `pie-evals-node run`,** never by hand-rolled scripts, never on a laptop. Never touch the Mac at 100.87.85.82.
6. **No idle GPU.** When your models are done, post the report and terminate this pod (or tell the operator its id in the report).

## Execution Protocol (Follow in Exact Order)

### Phase 1: Engines & pie Device Profile

1. `uv venv && uv pip install -e ".[dev,orchestrate]"` in benchmarks. Build pie: `pie-evals-node build --pie-commit <main sha> --features cuda --pie-root ~/pie`.
2. **vLLM and SGLang from our forks,** `pie-project/vllm` and `pie-project/sglang`, branch `pie-evals/<upstream-version>` (pull first: another agent may have pushed fixes). Install into the venvs the recipes name (`src/pie_evals/node/engines/recipes/`); set `VLLM_PY` / `SGLANG_PY`.
3. pie device profile: `pie/crates/engine-cuda/profiles/<sm>/<device>.toml` (L40S: `sm89/nvidia-l40s.toml`). If missing: `pie tune cuda`, verify it matches or beats the default, PR it to pie.

### Phase 2: Models, Miniatures & 100% Smoke Gate

1. **Fit rule:** full model if weights fit ~80% of memory with KV room for the saturating concurrency; else a listed alternate that fits; else a miniature (most source layers that fit, whole layer-pattern periods, first N experts, widths unchanged). Missing artifacts and catalog rows go in `matrix/models.yaml` (real specs from the official config). Start downloads and miniature builds in the background.
2. **Smoke test** every (model × engine): one request, 512-token prompt, 16 tokens out. 100% must load and generate before any full run. Self-healing:
   - Attempt 1: flags/env (attention backend, block size, `--language-model-only`, memory fraction, graph sizes).
   - Attempt 2: miniature recipe (expert alignment, `index_top_k`, rope/head dims); rerun all engines on the new cut.
   - Attempt 3: patch the loader, quant dispatcher or kernel wrapper **in the fork** (one small commit per fix on `pie-evals/<version>`, push it, reinstall; never leave an unrecorded venv patch; fixes are shape guards, loader fixes or arch fallbacks that never change a full model's speed), or pie's source.
   - Escalation: only then a `support.yaml` row.

### Phase 3: Benchmarks & Anomalies

For each model that passes the smoke test, on every engine:

1. Decode latency — `raw-512-256`, 1 request.
2. Prefill latency — `raw-512-256`, 1 request.
3. **Saturated decode throughput** — `c<N>`.
4. **Saturated prefill throughput** — `pf<N>-512`.

**Saturation:** sweep concurrency in powers of two (4, 8, 16, … to the memory limit); N = smallest past which tok/s grows < 5%. Same N for all engines. Add a missing `c<N>` / `pf<N>-512` to `matrix/workloads.yaml` and `tools/webdb.py`.

Run: `pie-evals jobs --tier weekly --pie-commit <sha> --platform [TARGET_DEVICE] --artifact <id> --workload raw-512-256 --workload c<N> --workload pf<N>-512 --out jobs`, then `PIE_ROOT=~/pie pie-evals-node run --job jobs/<job>.json --out out/<job>`.

Anomalies (inspect as each model finishes): pie < 50% of vLLM/SGLang, latency spikes, CoV > 2%:
1. Profile to find the bottleneck.
2. Targeted fix, re-measure. **pie speedups are minimal diffs that measurably help:** the fewest kernel lines that make the measured cell faster; no rewrites, no refactors, no added comments; keep only if the rerun is faster, else revert.
3. Deep architectural issue: root-cause in the report, move on.

### Phase 4: Record, Publish & Report

1. **Record** each model as it finishes: `pie-evals collect --tier weekly --tag [TAG] --tag-kind manual out/<job>` (writes Postgres on `liszt` over Tailscale via `$PIE_EVALS_DB`; re-collecting replaces, so it is safe).
2. **Publish:** `gh workflow run pages.yml -R pie-project/benchmarks` rebuilds the site data; rerun the coverage check.
3. **Review, without waiting for it:** every change on a branch, in a PR (benchmarks, pie, forks); never merge your own; run from your branch. One tracking issue `[TARGET_DEVICE] evaluation` shared by all pods: coverage after each model, every PR linked. PR title plain English (`vLLM: run the DeepSeek-V4.1 miniature on L40S`); body 1–3 sentences: what failed, what changed, how checked. Commits: one title line. No AI attribution anywhere.
4. **Final report** (comment on the tracking issue): completion matrix for your models (4 setups × 3 engines, N for throughput, ratios for miniatures); fork and pie PRs with links; `support.yaml` rows added; pie anomalies, most important first; new lessons (also added below).

## Lessons

- Run the benchmarks on the machine itself: an agent that fixes on a pod and dispatches CI to measure elsewhere loses hours to stock, queueing and lost context.
- pie main fails to boot models over ~9 GB on L40S since pie #1157 (a fixed 32 GiB device KV budget); use a commit with pie #1163.
- L40S (sm_89): vLLM 0.32 DeepSeek-V4.1 emits `mul.bf16x2` (sm_90 only); SGLang `mhc_pre` split-k takes `hc_hidden_size` 16384/28672 only (mini8: 20480; pie-project/sglang#1).
- SGLang on L40S: qwen3.8-flash-next fails a CUTLASS DSL block shape and CUDA-graph capture; mimo-v2.6-flash `Hidden size mismatch` on the miniature. Start early.
- Throughput workloads must send cold prompts: a shared prompt plus a "(Request #i)" suffix let pie prefill from its prefix cache (pf256-512 306k tok/s, 40x vLLM, on the Muse Glimmer mini). Prefill throughput above the compute bound is a bug, not a result.
- Check the prompt token counts per engine: pie's Muse Spark template rendered 560 tokens where the release chat template renders 677 (pie#1201). Check pie's deployment row: a 24-layer cut was served by an 8-layer row that reads only the first layers (pie#1167), and block-FP8 checkpoints were identified as their bf16 row and dequantized (set pie_sku).
- A `pie tune` user profile (~/.pie/profiles/cuda/user/) pins every knob and masks checked-in profile fixes; `pie tune --no-check` searches nothing. Move it aside before measuring.
- The gateway admitted on a stale inflight count after cold rounds and wedged (no healthy worker, GPU idle): pie#1175.
- nsys sees no vLLM kernels unless the engine core runs in-process or `--trace-fork-before-exec=true` is set.
- Pushing to the forks' pie-evals/<version> branches and `gh pr merge` may be blocked for the agent: run a fork branch under review with PIE_EVALS_FORK_REF_<ENGINE>.
