# Device evaluation prompt

Reusable for any GPU. Fill the parameters, hand it to an agent. Agents add what they learn to **Lessons** (by PR).

`[PLATFORM]` l40s-x1 · `[GPU]` NVIDIA L40S, 46 GiB · `[TAG]` l40s-full · `[PODS]` 6

---

## Operating mode

Autonomous. No human answers questions.

- Done = `python tools/device_coverage.py --platform [PLATFORM] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` exits 0. Until then, keep working.
- Never ask, never hand back. Decide as a careful engineer would, log one line, continue. Take every recommended next step.
- A failure is a task: diagnose, fix, rerun only the affected cells. Never let one stuck cell block the queue.
- Parallelize: `[PODS]` GPUs, sub-agents per pod or per failing engine.
- Verify: rerun the coverage check after every batch. One-line status updates.

## Goal

All 19 models in `matrix/device-eval.yaml` × {pie, vLLM, SGLang} × 4 setups, plus quality. Zero gaps.

| setup | workload | metric |
|---|---|---|
| Decode Latency | `raw-512-256` | decode tok/s, 1 request |
| Prefill Latency | `raw-512-256` | prefill tok/s, 1 request |
| Decode Throughput | `c32` | output tok/s, 32 requests |
| Prefill Throughput | `pf256-512` | prefill tok/s, 256 prompts × 1 token |
| Quality | `parity` | KL and top-1 agreement, pie vs vLLM, same weights |

A cell is done with a number, or a `matrix/support.yaml` row (exact limitation + traceback line) after the fix protocol is exhausted.

## Infrastructure

- **Recorded runs: CI only.** CI holds the DB URL and RunPod key, rents, reaps, and writes rows.
  - Bench: `gh workflow run weekly.yml -R pie-project/benchmarks -f platforms=[PLATFORM] -f artifacts=<ids> -f workloads=raw-512-256,c32,pf256-512 -f tag=[TAG] -f own_pods=true -f max_jobs_per_platform=[PODS]` (`--ref <branch>` for harness fixes).
  - Quality: `gh workflow run parity.yml ... -f platforms=[PLATFORM] -f artifacts=<ids> -f tag=[TAG] -f kernels=false`, then `parity-import.yml -f run_id=<run>`.
  - Publish: `gh workflow run pages.yml` (rebuilds `web/data/db.js`), then rerun the coverage check.
  - Cancel duplicate dispatches; `gh run delete` cancelled or no-op runs.
- **Debug pods:** RunPod (Liszt template if available, else `development`), over Tailscale (`ssh root@<pod-id>`, `pod-setup`). Smoke, debug, patch only; numbers there are leads, never results.
- **DB:** Postgres on `liszt` (`$PIE_EVALS_DB`; tables `records`, `quality`). Written by `pie-evals collect` / `pie-evals import-store` inside CI.
- **Repos:** `pie-project/benchmarks` (harness, matrix, site), `pie-project/pie` (engine; `scripts/bench/shrink_checkpoint.py`).

## vLLM and SGLang forks (keep miniatures working)

`pie-project/vllm` and `pie-project/sglang` hold every competitor fix, so a miniature that runs once keeps running.

- Branch per upstream release: `pie-evals/<version>` (e.g. `pie-evals/v0.32.0`). Rebase onto each new release.
- One small commit per fix. Check the branch first: the fix may exist.
- CI installs the fork branch, not PyPI: set it in `src/pie_evals/node/engines/recipes/<engine>.yaml`.
- One fork build serves every comparison on every GPU. Never patch a venv in place.
- Fixes must not change speed for full models: shape guards, missing-arch fallbacks, loader fixes only.

## Rules

1. Same checkpoint, cut, tp, workload, concurrency and competitor release for all engines. Fix any advantage, rerun.
2. Fit: full model if weights fit ~80% of `[GPU]` with KV for 32 requests; else a listed alternate that fits; else a miniature (most source layers that fit, whole layer-pattern periods, first N experts, widths unchanged), recorded in `matrix/models.yaml`.
3. Never download a full checkpoint that does not fit. Miniatures stream byte ranges. Keep ≥100 GB free; delete spans.
4. Miniatures never show tok/s: engine-to-engine ratios only.
5. One measurement per GPU at a time, GPU idle first (`nvidia-smi`).
6. No fabricated numbers, no laptop numbers. Never touch 100.87.85.82.
7. "Unsupported" only after the fix protocol.

## Fix protocol

1. Flags/env: attention backend, block size, `--language-model-only`, memory fraction, max length, CUDA-graph sizes (`--enforce-eager` only if applied equally).
2. Miniature recipe: expert alignment, layer pattern, `index_top_k`, rope/head dims. Rerun all engines on the new cut.
3. Code: fork (vLLM, SGLang) or pie. Push as above.
4. Then a `support.yaml` row: root cause, traceback line, what was tried.

## Steps

1. **Engines.** pie `main` (`pie-evals-node build --features cuda`), vLLM/SGLang fork branches. Device profile: `pie/crates/engine-cuda/profiles/<sm>/<device>.toml`; if missing, `tune.yml`, PR to pie.
2. **Artifacts.** Full / alternate / miniature per the fit rule. Add missing catalog rows with real specs from the official config. Build miniatures in the background.
3. **Smoke.** Every model × engine: 512-token prompt, 16 tokens out. Failures → fix protocol; passing models proceed.
4. **Runs.** Dispatch bench + quality per model batch. Publish. Recheck coverage.
5. **Anomalies.** pie < 50% of best engine, latency jumps, CoV > 2%, KL > 0.05, top-1 < 0.90: profile, fix if targeted, rerun; else root-cause in the report.
6. **Done.** Coverage exits 0 → terminate all pods → final report on the tracking issue.

## Pods

- Track every pod in `pods.txt`. Check every 15 min. Idle 10 min (no job, ~0% GPU) → terminate now. Over expected time +50% → save logs, terminate, rerun elsewhere.
- At the end: terminate all, confirm none left.

## Review

- Every change on a branch, in a PR. Never merge; keep running from the branch.
- One tracking issue, `[GPU] evaluation`: coverage table after each batch, link every PR.
- PR title: plain English, what changed (`vLLM: run the DeepSeek-V4.1 miniature on L40S`). Description: 1–3 sentences: what failed, what changed, how checked.
- Commits: one title line. No AI attribution anywhere (no co-author trailer, no "Generated with", no mention of an agent).

## Final report

1. Coverage table.
2. Per model: variant (full / alternate / cut), pie vs vLLM vs SGLang per setup as ratios.
3. Every PR, one line + link.
4. `support.yaml` rows added.
5. pie anomalies, most important first.
6. New lessons (also below).

## Lessons

- Access: the DB URL is a CI secret; the pie-project RunPod account (CI's) has `development`, not the Liszt template. Record via CI; debug on rented pods.
- L40S (sm_89): vLLM 0.32 DeepSeek-V4.1 emits `mul.bf16x2` (needs sm_90); SGLang `mhc_pre` split-k only takes `hc_hidden_size` 16384/28672 (mini8: 20480). Fork fixes.
- SGLang on L40S: qwen3.8-flash-next fails a CUTLASS DSL block shape and CUDA-graph capture; mimo-v2.6-flash `Hidden size mismatch` on the miniature. Start early.
