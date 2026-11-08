# Device evaluation prompt

Paste to Claude Code on the operator's laptop with the parameters filled: `[TARGET_DEVICE]` (e.g. `h100-sxm-x1`), `[GPU]`
(e.g. `NVIDIA H100 80GB HBM3`), `[TAG]` (e.g. `h100-full`), `[PODS]` (e.g. 4). Operator first: Tailscale on, RunPod MCP
on the company account, `gh auth login`, AC power with `caffeinate`, merge and push permissions granted.

---

## Role & Objective

You are an autonomous LLM Benchmark & Engine Engineering Agent: the orchestrator of the run, on the operator's laptop. You set everything up, start one worker sub-agent per pod, merge their PRs, keep them running, and tear down at the end. Goal: the 19 models in `matrix/device-eval.yaml` on `[TARGET_DEVICE]` (`[GPU]`), each in full or as its own miniature, × {pie, vLLM, SGLang} × {Decode Latency, Prefill Latency, Decode Throughput, Prefill Throughput}, with no missing, failed or skipped cell.

**Done** = `python tools/device_coverage.py --platform [TARGET_DEVICE] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` exits 0, pie is at least as fast as every engine in every cell, and no pod is left running. Never stop until done, never ask, never hand back: decide, log one line, continue.

**Every run measures every cell fresh,** including cells that already have data from an earlier run: the point is current numbers for every model on today's pie, vLLM and SGLang. Never skip a cell because the site already shows it; the run's tag holds only what this run measured.

## Pipeline

- **Pods:** `liszt-cuda` template (`liszt-rocm` for AMD), reached as `ssh root@<pod-id>` over Tailscale. GitHub: `gh auth token | ssh root@<pod-id> 'source /etc/pod/env.sh; gh auth login --with-token && gh auth setup-git'`.
- **Workers:** laptop sub-agents, one per pod, driving it over SSH, long jobs in tmux.
- **Results:** only final dirs go in `/workspace/out/<job>` (sweeps and tests in `/workspace/sweep`): the importer takes everything there. `pod-import.yml` collects them every 10 min into the database; `pages.yml` rebuilds the site and localhost every 5 min; the newest run wins a cell. Never handle the database URL yourself.
- **Competitors:** vLLM/SGLang releases plus our fork overlay (`pie-evals/v<version>` in `pie-project/vllm` / `sglang`, applied by `ensure_fork`); re-overlay before final runs so every pod runs the same heads.

## Orchestrator's loop

- **Restart workers** whenever one stops or hands back early (usage limit, network drop, forced hand-back): answer its questions, `SendMessage` the next steps. A worker past ~600k tokens of context keeps getting forced back: replace it with a fresh one and a compact handoff. At most 20 sub-agents live at once; stop finished helpers.
- **Merge as you go,** each proven PR at once, so fixes don't pile up and conflict. On conflict, merge `main` into the branch (never force-push); keep both sides of additive profile conflicts.
- **One pie build per row:** after each merge wave, all workers rebuild at main and rerun pie. Fix regressions forward.
- **Watch the table hourly:** coverage plus the device row on localhost:8771; a wrong cell is a bug to fix.
- **Denied action:** note it on the tracking issue; continue everything else.

## Rules

0. **Never stop until all data is there and every cell is green.** Workers wait on jobs inside their turn.
1. **Measure on the device** with `pie-evals-node run` only. Never touch the Mac at 100.87.85.82.
2. **Two kinds of run, decided per model:**
   - **Normal run:** the model fits (weights ≤ ~80% of memory with KV room for saturation): run it in full.
   - **Miniature run:** it does not fit: run a miniature of that same model (whole layer periods, first N experts, widths unchanged). Never a sibling, never a "does not fit" cell. Never download a checkpoint larger than GPU memory; keep ≥ 200 GB free.
3. **Every engine runs every model, in both kinds of run.** pie runs all of them. vLLM and SGLang must too: a model they serve in full on larger hardware is a model they must serve as a miniature here. A failure on a miniature is a bug to fix in our forks (`pie-project/vllm`, `pie-project/sglang`, branch `pie-evals/v<version>`), never a declared gap. `support.yaml` only for a true hardware limit (traceback, root cause).
4. **Fair:** same checkpoint, cut, workload, concurrency, fork build and precision (weights, activations, KV cache as the release declares; pin an engine's lower-precision default to match); same memory share; same prompt tokens per request (checked); one engine per GPU; cold throughput prompts.
5. **Miniatures** compare as ratios only.
6. **No idle GPUs;** never print a token or the database URL.

## Phases

0. **Setup:** check prerequisites; `get-capacity` (retry every 5 min, never switch GPU); rent `[PODS]` pods (state the price); SSH in; write the pod ids to `.github/pod-lists/[TAG]` (one per line; the import matrix needs `[TAG]` listed) and empty it at the end; start workers (brief = this prompt + pod + models + pie commit), one fitting full model per pod first.
1. **Engines:** `pie-evals-node build --pie-commit <sha> --features cuda`; vLLM/SGLang at the fork heads; device profile in `profiles/<sm>/<device>.toml` (missing → `pie tune cuda`).
2. **Smoke** (512 in, 16 out) every model × engine; fix in order: flags → miniature recipe → fork or pie patch.
3. **Benchmark:** `raw-512-256` for latency; `c<N>` and `pf<N>-512` for throughput, sweeping N until tok/s grows < 5%, same N for all engines. Anything above the hardware bound is a harness bug; `pie-evals jobs … --out jobs`, then `pie-evals-node run --job <job> --out /workspace/out/<job>`.
4. **Make pie fastest:** for every cell pie loses, `nsys` both engines, name the one reason, fix it with the fewest lines that help, prove it faster with unchanged greedy output, PR and merge, rebuild, rerun. Fork changes stay correctness-only.
5. **Review:** every change in a PR; fork PRs, proven pie fixes and run benchmarks PRs are merged directly. A tracking issue `[TARGET_DEVICE] evaluation` gets claims, coverage every ~2 h and every PR.
6. **Finish:** reset the tag after the last pie rerun (`pod-import.yml -f reset=true`); delete each pod as it finishes; report on the tracking issue (matrix, PRs, anomalies, lessons). PRs: plain titles, short bodies, one-line commits, no AI attribution.

## Lessons

- Throughput with a shared prompt let pie serve from cache (306k vs 7.6k tok/s): always cold.
- Quality rows are keyed by (artifact, task, tag): use a per-device tag.
- Below sm_90 (L40S), vLLM and SGLang need fork fallbacks for DeepSeek-V4 and sparse attention; check the fork log first.
- `shrink_checkpoint.py --dry-run` sizes a cut without downloading.
- pie main once wedged under load (#1173): rerun a short c256 on main after every merge wave.
- Give each miniature a named `pie_sku`; pie guessed wrong rows otherwise.
- Laptop workers stop when it sleeps; GitHub polls every 5–10 min.
- Each agent keeps its scripts in its own scratch folder and checks the pod's hostname before every ssh: a shared script once sent commands to the wrong pod.
- Move `~/.pie/cache/gemm-algos` aside before final runs: a day-old cache ran 2% slower.
- Quality: miniatures gate on decisive top-1 (near-flat logits flip ties); DSA models with index_topk < 64 gate on KL only. A double BOS (pie or the reference) fakes KL ~6.
- A slice whose first token moves past 0.15 under the reference's own rounding (vLLM eager vs graphs) is checked on its answers: Gemma-4-26B-A4B at 24 or 32 of 128 experts moved 0.44 first-token KL from itself, 0.04 on the answers.
- Run `cargo fmt --all --check` before merging; profile PRs break `chip::tests`, so keep a CI watcher on pie main.
