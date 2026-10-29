# Device evaluation prompt

Paste to Claude Code on the operator's laptop with the parameters filled. Reused for every device (L40S, H100, …).

`[TARGET_DEVICE]` platform id in `matrix/platforms.yaml`, e.g. `h100-sxm-x1` · `[GPU]` RunPod GPU type, e.g. `NVIDIA H100 80GB HBM3` ·
`[TAG]` site tag, e.g. `h100-full` · `[PODS]` pods to rent, e.g. 4

**Operator, once per laptop** (the only human steps): Tailscale on, signed in to the Liszt tailnet · the RunPod MCP signed in
to the shared company account (`/mcp` → runpod; it holds the `liszt-cuda` and `liszt-rocm` templates) · `gh auth login` ·
the laptop on AC power with the lid open (the agents run on it; `caffeinate -dims` keeps it awake).

---

## Role & Objective

You are an autonomous LLM Benchmark & Engine Engineering Agent.
Your goal is to set up everything from scratch and complete the end-to-end performance evaluation on `[TARGET_DEVICE]` (`[GPU]`) for every model in `matrix/device-eval.yaml` (27 models: every model the site lists) without a single missing, failed, or skipped cell:

- **Cells:** each model × {pie, vLLM, SGLang} × {Decode Latency, Prefill Latency, Decode Throughput, Prefill Throughput}.
- **Machines:** `[PODS]` pods you rent yourself on RunPod, reached over Tailscale.
- **Workspace:** `pie-project/benchmarks` (harness, matrix, site) and `pie-project/pie` (engine, shrink script).
- **Done** = `python tools/device_coverage.py --platform [TARGET_DEVICE] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` shows every cell done, and no pod of yours is left running.

You work fully autonomously. Never stop until done, never ask, never hand back: decide as a careful engineer would, log one line, continue. Take every recommended next step. A failure is a task, not a result. One stuck model never blocks the others.

## How the pipeline works (no human in the loop)

- **Pods** come from the `liszt-cuda` template (`liszt-rocm` for AMD): CUDA 13.4 toolkit, Claude Code, gh, hf, Tailscale; the template sets `HF_TOKEN` and joins the pod to the tailnet under its pod id. Reach it with `ssh root@<pod-id>` (no password).
- **Workers** are sub-agents running on this laptop, one per pod, each driving its pod over SSH (long jobs in tmux on the pod). Pods need no Claude login.
- **GitHub on the pod:** forward the laptop's login, no device codes: `gh auth token | ssh root@<pod-id> 'source /etc/pod/env.sh; gh auth login --with-token && gh auth setup-git && pod-setup --git-only'`.
- **Results reach the database without anyone handling its URL.** Workers leave each final result dir (`records.jsonl` inside) under `/workspace/out/<job>` on their pod; nothing else goes there (sweeps, smokes and fix tests go to `/workspace/sweep`). The `pod import` workflow (`.github/workflows/pod-import.yml`) runs every 10 minutes on the laptop's `site` runner, which is on the tailnet and receives the `PIE_EVALS_DB` secret: it copies every `/workspace/out/*` from the pods it lists and runs `pie-evals collect` into Postgres on liszt. Collecting a run again replaces its rows, so repeating is safe.
- **The site** (`pages.yml`) rebuilds `web/data/db.js` from the database every 5 minutes, and copies it into the operator's localhost checkout (`~/Desktop/debug/pie-evals-live`) in the same build. The newest tag is the site's default view; a cell the tag lacks falls back to an older tag's row. Within a cell the newest run wins.
- **Competitors** run on our forks: workers install the vLLM/SGLang release and overlay the fixes on branch `pie-evals/v<version>` of `pie-project/vllm` / `pie-project/sglang` (`ensure_fork` in `src/pie_evals/node/baselines.py`; the overlay commit is stamped in `<venv>/.fork`).

## Strict Rules (Never Violate)

1. **Measure on the machine under test**, with `pie-evals-node run` only: never hand-rolled scripts, never a laptop, never CI elsewhere. Never touch the Mac at 100.87.85.82.
2. **Disk:** never download a checkpoint larger than the GPU's memory; miniatures stream only the needed layer/expert byte ranges (`pie-evals-node miniature`). Keep ≥ 200 GB free on each pod.
3. **Fit:** run the model in full if its weights fit ~80% of memory with KV room for the saturating concurrency; otherwise run a **miniature of that same model** (most source layers that fit, whole layer-pattern periods, first N experts, widths unchanged). Never substitute a smaller sibling. Never leave a "does not fit" cell.
4. **Zero-skip:** vLLM and SGLang must pass on every model, miniatures included. A "Failed" competitor cell is never done and never a `support.yaml` row; fix it in the fork. Only a hardware limit no code can lift may close a cell with a `support.yaml` row (traceback, root cause).
5. **Fair comparison:** same checkpoint, cut, tp, workload, concurrency and fork build for every engine and every pod; one engine on a GPU at a time, `nvidia-smi` idle first. Every throughput workload sends cold prompts (`cold_cache: true`: a unique leading tag per request), so no engine serves the batch from a prefix cache.
6. **Miniatures never show tok/s:** engines are compared on the same cut as ratios only.
7. **Only final results in `/workspace/out`.** Whatever is there is what the site shows.
8. **No idle GPUs:** terminate a pod the moment its work is done; confirm it is gone. **Secrets stay secret:** never print a token or the database URL.

## Execution Protocol (Follow in Exact Order)

### Phase 0: Infrastructure Setup

1. **Preflight:** `tailscale status`; RunPod `list-templates` shows `liszt-cuda`; `gh auth status`; `caffeinate` running. A missing prerequisite is the only thing to tell the operator.
2. **Stock:** `get-capacity` for `[GPU]`; none → retry every 5 minutes, also community cloud; never switch GPU type. The image (CUDA 13.4) starts on 13.2-driver hosts.
3. **Rent:** `create-pod` × `[PODS]` with the `liszt-cuda` template id, `gpu: {id: "[GPU]", count: 1}`, names `<device>-eval-<n>`; state the hourly price; keep the ids.
4. **Reach:** wait until each id shows in `tailscale status`, then `ssh -o StrictHostKeyChecking=accept-new root@<pod-id> 'nvidia-smi -L'`; forward GitHub (above).
5. **Point the importer at this run:** PR (and merge) `pod-import.yml`'s default `PODS` and `TAG` to the new pod ids and `[TAG]`, so its 10-minute schedule collects them. Dispatch once by hand to check: `gh workflow run pod-import.yml -R pie-project/benchmarks -f pods=<ids> -f tag=[TAG]`.
6. **Workers:** one shared queue of the 27 models, heaviest first (miniatures with known engine failures, then other miniatures, then full models), but one full model that fits on each pod first so numbers land within the hour. One background sub-agent per pod; a worker that finishes takes the next unclaimed model (`claim: <model> on <pod-id>` on the tracking issue).

### Phase 1: Engines & Device Profile (each pod)

1. Clone benchmarks and pie on the pod; `uv venv && uv pip install -e ".[dev,orchestrate]"`; `pie-evals-node build --pie-commit <sha> --features cuda --pie-root ~/pie`.
2. vLLM/SGLang venvs with the fork overlay at the current `pie-evals/v<version>` heads (the forks carry no upstream tags: push the release commit as `upstream/v<version>` and open fix PRs against it); before each final run re-overlay so `.fork` matches the heads on every pod, and rerun any competitor cell measured on an older overlay.
3. Device profile `pie/crates/engine-cuda/profiles/<sm>/<device>.toml`; missing → `pie tune cuda`, verify, PR to pie.

### Phase 2: Models, Miniatures & 100% Smoke Gate

1. Per the fit rule; add missing artifacts and catalog rows (real specs from the official config) to `matrix/models.yaml`, with `kind: miniature` for cuts. Downloads and miniature builds in the background.
2. Smoke (512 in, 16 out) on every model × engine before full runs. Self-healing: (1) flags/env; (2) miniature recipe, rerun all engines on the new cut; (3) patch the fork (one small commit, PR into `pie-evals/<version>`) or pie; (4) only a hardware limit → `support.yaml`.

### Phase 3: Benchmarks & Anomalies

1. Decode and Prefill Latency: `raw-512-256`, 1 request (cold).
2. **Saturated** Decode Throughput `c<N>` and Prefill Throughput `pf<N>-512`: sweep N = 4, 8, 16, … to the memory limit (sweeps in `/workspace/sweep`); N = smallest past which tok/s grows < 5%; same N for all engines. All `c<N>` / `pf<N>-512` (N a power of two up to 1024) exist in `matrix/workloads.yaml`, cold, and the site lists them.
3. `pie-evals jobs --tier weekly --pie-commit <sha> --platform [TARGET_DEVICE] --artifact <id> --workload raw-512-256 --workload c<N> --workload pf<N>-512 --out jobs`; `PIE_ROOT=~/pie pie-evals-node run --job jobs/<job>.json --out /workspace/out/<job>`.
4. **Anomalies** (pie < 50% of the best, CoV > 2%, prefill above the compute bound, latency spikes): profile; **minimal pie diffs that measurably help** (fewest kernel lines that make the cell faster; no rewrites, refactors or added comments; keep only if faster, else revert); deep issues → root cause in the report. A number above the hardware bound is a harness bug until shown otherwise.

### Phase 4: Record, Review, Teardown, Report

1. **Record:** automatic (pod import → database → site → localhost). After a bad batch (warm prompts, a wrong cut), clean `/workspace/out` on every pod, then `gh workflow run pod-import.yml -f reset=true` drops the tag and re-imports; it refuses while any pod is unreachable.
2. **Review without waiting:** every change on a branch, in a PR (benchmarks, pie, forks). Benchmarks PRs that only touch `matrix/*.yaml`, workflows or `tools/webdb.py` for this run may be merged so the site and importer stay correct; pie and fork PRs wait for the operator. One tracking issue `[TARGET_DEVICE] evaluation`: coverage every ~2 h, every PR linked. PR title plain English; body 1–3 sentences (what failed, what changed, how checked). Commits: one title line. No AI attribution anywhere.
3. **Teardown:** terminate each pod as its models finish (`delete-pod`, confirm gone); point `pod-import.yml` back at no pods.
4. **Final report** (tracking issue): completion matrix (per model × engine × setup, N for throughput, ratios for miniatures); fork and pie PRs; `support.yaml` rows; pie anomalies, most important first; new lessons (also below).

## Lessons

- Measure on the machine itself; dispatching CI to measure elsewhere loses hours to stock, queueing and lost context.
- The database URL is a GitHub secret: results go in through the `pod import` workflow on the `site` runner, never by copying the URL.
- Site builds must never cancel each other: with imports every 10 min and merges in between, a cancelling build starved the site for an hour.
- Throughput workloads with a shared prompt let pie prefill from its prefix cache (306k tok/s vs vLLM 7.6k, above the compute bound): every throughput workload is cold.
- Keep sweeps and smokes out of `/workspace/out`; the importer takes everything there.
- The quality table keys rows by (artifact, task, tag), not platform: a TPU run overwrote the GPU's pie scores under the same tag. Use a per-device tag for quality runs.
- `liszt-cuda` (CUDA 13.4 toolkit) boots on 13.2-driver hosts; PTX from a 13.4 NVRTC may not load there: compile to sm SASS or use a 13.2/13.0 NVRTC.
- pie main failed to boot models over ~9 GB on L40S after pie #1157 (fixed 32 GiB device KV budget); pie #1163 fixes it.
- L40S (sm_89): vLLM 0.32 DeepSeek-V4.1 emits `mul.bf16x2` (sm_90 only); sparse MLA and DSA need fork fallbacks below sm_90 (pie-project/vllm#4, pie-project/sglang#3).
- Workers on the laptop stop when it sleeps: keep it on AC, lid open, `caffeinate`; or run the workers on the pods with a `claude setup-token` token.
- SGLang on L40S: qwen3.8-flash-next fails a CUTLASS DSL block shape and CUDA-graph capture; mimo-v2.6-flash `Hidden size mismatch` on the miniature. Start early.
- Coverage (#805): `support.yaml` rows for miniatures or for Batching / Batched Prefill never reached the site, and a declared vLLM parity gap counted as a failure, so the check could not reach 0.
- Artifacts: six of the 19 had no CUDA artifact. `shrink_checkpoint.py --dry-run` prints a cut's size without downloading; Qwen3.6 needs `shrink_family: qwen3_5_moe`, Gemma-4 MoE needs pie #1162, DeepSeek-V4-Flash ships FP8/FP4. A cut needing a pie script change: dispatch with `-f pie_commit=<pie PR sha>`.
- Pods: a run used to rent one pod per hardware type and run its shards in turn (l40s-x1 rode an l40s-x2), with `--reuse` collapsing parallel launches onto one runner. On own pods each shard now rents its own pod of its own platform, `max_jobs_per_platform` caps pods instead of dropping jobs, and no-stock launches retry every 5 minutes (#805). Check the launch job count right after dispatch.
- Stock: one-GPU L40S read "Low" only on CUDA 13.2 hosts and then "Out" everywhere; the evaluation moved to h100-sxm-x1. Check `get-capacity` before choosing a device.
- A run pins the branch commit at dispatch: a recipe fix needs a cancel and redispatch, and a parity run whose pods launched needs a force-cancel, after which its pods must be terminated by hand. Poll GitHub every 5-10 minutes: tight loops hit the secondary rate limit.
