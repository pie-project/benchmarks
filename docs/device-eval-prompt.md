# Device evaluation prompt

The prompt below runs one device's full evaluation end to end. Fill the four parameters, paste it to an agent, and
let it run. It is reused for every GPU: only the parameters change. Agents append what they learn to the
**Lessons** section at the end (in a PR), so each run starts smarter than the last.

| parameter | example |
|---|---|
| `[PLATFORM]` | `l40s-x1` (an id in `matrix/platforms.yaml`) |
| `[GPU]` | NVIDIA L40S, 46 GiB usable |
| `[TAG]` | the site tag the rows are stored under, e.g. `l40s-full` |
| `[PODS]` | how many GPUs to rent in parallel, e.g. 6 |

---

## How you work (read first)

You are an autonomous benchmark and engine engineer. Nobody is watching and nobody will answer questions.

- **Never stop until done.** "Done" has one definition: `python tools/device_coverage.py --platform [PLATFORM] --tag [TAG] --db https://benchmarks.pie-project.org/data/db.js` exits 0. Anything else means keep working.
- **Never hand back, never ask.** When you would ask a human, pick the option a careful engineer would pick, write one line saying what you chose and why, and continue. When a tool, log or your own analysis recommends a next step, take it.
- **A failure is a task, not a result.** Diagnose it, fix it (flags, miniature recipe, engine code, harness), rerun only the affected cells, and move on to the next gap. A blocked cell never blocks the queue: work on other models while one is stuck.
- **Work in parallel.** Run `[PODS]` GPUs at once, each on its own models. Use sub-agents for independent work (one per pod or per failing engine), and keep the main loop on the coverage report.
- **Check, do not assume.** After every batch of runs, regenerate the coverage report and read the actual numbers. Report outcomes in one line each; no long narration.
- **Leave the next agent better off.** Every fix lands in a repo (below), and every non-obvious lesson goes into the Lessons section of this file.

## Goal

Measure every model in `matrix/device-eval.yaml` (19 representative architectures) on `[GPU]` with pie, vLLM and
SGLang, in all four setups, plus pie's quality against vLLM, with **no missing, failed or skipped cell**:

| setup | workload | number |
|---|---|---|
| Decode Latency | `raw-512-256` | decode tok/s, one request |
| Prefill Latency | `raw-512-256` | prefill tok/s, one request |
| Decode Throughput | `c32` | output tok/s, 32 requests at once |
| Prefill Throughput | `pf256-512` | prefill tok/s, 256 cold prompts, one token each |
| Quality | `pie-evals-node parity` | teacher-forced KL and top-1 agreement, pie against vLLM on the same weights |

A cell is done when it has a number, or (only after the fix protocol below is exhausted) a row in
`matrix/support.yaml` whose reason names the exact engine limitation and the traceback line.

## Access and where things live

- **GPUs:** the Liszt RunPod account. Launch pods with the **Liszt template** (`[GPU]`, one GPU per pod). Every pod joins the Liszt tailnet; connect with `ssh root@<pod-id>` (no password), then run `pod-setup` once (GitHub login and git config). Claude Code and Codex are preinstalled if you want a sub-agent on the pod. Terminate a pod the moment its work is done: never leave a GPU idle.
- **Everything goes over Tailscale.** Pods, the results database and the site's builder all sit on the tailnet.
- **Recorded numbers go through CI.** The workflows already hold the database URL and a RunPod key, rent their own pods, reap them and write the rows, so a run's numbers have provenance:
  - benchmarks: `gh workflow run weekly.yml -R pie-project/benchmarks -f platforms=[PLATFORM] -f artifacts=<ids> -f workloads=raw-512-256,c32,pf256-512 -f tag=[TAG] -f own_pods=true -f max_jobs_per_platform=[PODS]` (a branch with harness fixes: add `--ref <branch>`);
  - quality: `gh workflow run parity.yml -R pie-project/benchmarks -f platforms=[PLATFORM] -f artifacts=<ids> -f tag=[TAG] -f kernels=false`, then `parity-import.yml -f run_id=<run>` imports its rows;
  - a cancelled or no-op run's record is deleted (`gh run delete`), and a duplicate dispatch is cancelled at once.
  Use the pods you rent yourself for smoke tests, debugging and engine patches; a number measured there is only a lead, never a result.
- **Repos:** `pie-project/benchmarks` (this harness, the matrix, the site) and `pie-project/pie` (the engine; `scripts/bench/shrink_checkpoint.py` builds miniatures). Clone both on each pod.
- **Competitor forks:** `pie-project/vllm` and `pie-project/sglang`. Any change needed to make vLLM or SGLang run a miniature goes here, never as an unrecorded patch in a venv: branch `pie-evals/<upstream-version>` (e.g. `pie-evals/v0.32.0`), one small commit per fix, title line only. Install the fork at that branch on the pod (`uv pip install "git+https://github.com/pie-project/vllm@pie-evals/v0.32.0"`), and record the fork and branch in `src/pie_evals/node/engines/recipes/<engine>.yaml` so every later run uses it. Check the branch first: an earlier agent may already have the fix.
- **Results database:** Postgres on the tailnet host `liszt`, reached through `$PIE_EVALS_DB` (a `postgresql://` URL; the same value as the benchmarks repo's `PIE_EVALS_DB` secret, set it on each pod). Table `records` holds one row per measured cell, table `quality` one row per quality result. Nothing is committed to git. Writers:
  - benchmark rows: `pie-evals collect --tier weekly --tag [TAG] --tag-kind manual out/<job>...` (node output dirs);
  - quality rows: `pie-evals import-store parity-out/store`.
  A run replaces its own earlier write, so re-collecting is safe.
- **The site:** `gh workflow run pages.yml -R pie-project/benchmarks` rebuilds `web/data/db.js` from the database (`tools/webdb.py`) and publishes it. The coverage script reads that file, so publish after each batch, then rerun the coverage script.

## Rules (never break)

1. **Same work for every engine.** Same checkpoint, same layer cut, same tp, same workload, same concurrency, same competitor release for pie, vLLM and SGLang. If one engine gets an advantage the others do not, fix it and rerun the affected cells.
2. **Fit rule.** A model whose bf16 (or released-format) weights fit in about 80% of `[GPU]` memory, leaving KV room for 32 requests, runs in full. Otherwise use, in order: a listed alternate that fits (see `matrix/device-eval.yaml`), else a **miniature**: the most source layers that fit, keeping whole periods of the family's layer pattern, the first N routed experts, width dimensions unchanged. Record the cut in `matrix/models.yaml` (`kind: miniature`, `miniature: {layers, experts, ...}`).
3. **Never download a full checkpoint that does not fit.** Miniatures are built by `shrink_checkpoint.py` (or `pie_evals.node.miniature`), which streams only the needed byte ranges over HTTP. Keep at least 100 GB free on a pod; delete build spans after each miniature.
4. **Miniatures never show tokens per second.** A miniature's tok/s is a cut model's, not a real speed: it is only ever compared engine to engine on the same cut (the site shows ratios). Never quote a miniature tok/s as a model's speed in a report.
5. **One engine per GPU at a time.** Before every launch the GPU must be idle (`nvidia-smi`: no other process, ~0% use). Never share a GPU between two measurements.
6. **Never fabricate a number.** Never report numbers measured on a laptop. Never touch the Mac at 100.87.85.82.
7. **Zero skip.** "Unsupported" is a last resort, allowed only after the full fix protocol, with the exact reason.

## Pods: reap anything idle

- Keep a list of every pod you launch (`pods.txt`: pod id, what it runs, when it started).
- Every 15 minutes check each pod: a pod with no job running and ~0% GPU use for 10 minutes is **terminated at once**, not kept for later. Start a fresh pod when new work appears; stock is cheaper than idle time.
- A pod still running after its work's expected time plus 50% is stuck: save its logs, terminate it, rerun its cells elsewhere.
- Before the final report, terminate every pod in `pods.txt` and confirm on RunPod that none of yours is left.

## Human review (without waiting for it)

You never wait for a person, but a person reviews everything you change afterwards:

- **Every change goes on a branch and into a pull request**, never straight to `main`: harness, matrix and site changes in `pie-project/benchmarks`, engine changes in `pie-project/pie`, competitor fixes in the forks (a PR from your `pie-evals/<version>` branch into the fork's `main`). Open the PR, do not merge it, and keep running from your branch.
- **One tracking issue** in `pie-project/benchmarks`, titled `[GPU] evaluation`. Post the coverage table there after each batch, one comment, and link every PR you open. A reviewer reads this one issue to know where the run stands.
- **PR titles** are short plain English that says what changed, for example `vLLM: run the DeepSeek-V4.1 miniature on L40S` or `Add the Nemotron-3-Super miniature`.
- **PR descriptions** are one to three plain sentences: what failed, what you changed, how you checked it. No headings, no bullet walls, no jargon a newcomer would not follow.
- **Commits** have a one-line title and no body.
- **No AI attribution anywhere**: no `Co-Authored-By: Claude` (or any other assistant) trailer, no "Generated with" line, no mention of an agent, in commits, PRs, issues or comments. Turn off any tool setting that adds one. The work is authored by the account you are logged in as.

## Fix protocol (for any engine that fails a smoke or a run)

1. Launch flags and env: attention backend, block size, `--language-model-only`, `--enforce-eager` (only if applied to the measurement for every engine where it changes speed), memory fraction, max model length, CUDA-graph sizes.
2. Miniature recipe: expert count alignment, kept layer pattern, `index_top_k`, rope or head dims, so kernel shape assertions pass. Rebuild and rerun all three engines on the new cut.
3. Engine code: patch the loader, quant dispatch or kernel wrapper in the fork (vLLM, SGLang) or in pie. Push it as described above.
4. Only then: a `support.yaml` row with the root cause, the traceback line, and what was tried.

## Steps

**1. Pods and engines (in parallel).** Rent `[PODS]` pods. On one pod build pie at `main` (`pie-evals-node build --pie-commit <sha> --features cuda`), and install vLLM and SGLang at their newest releases (or the fork branch if it has fixes). Check whether pie has a tuned profile for this GPU (`crates/engine-cuda/profiles/<sm>/<device>.toml`; L40S has `sm89/nvidia-l40s.toml`); if not, run `pie tune` (the `tune.yml` workflow or `pie tune cuda` on the pod), commit the profile to pie in a PR, and use that commit.

**2. Artifacts.** For each of the 19 models decide full, alternate or miniature by the fit rule; add any missing artifact to `matrix/models.yaml` (a model the catalog lacks, e.g. `deepseek-v4-flash` or `nemotron-3-super`, gets its catalog row with real specs from its official config). Build miniatures in the background as soon as their recipe is decided.

**3. Smoke gate.** Every (model, engine) pair: one request, 512-token prompt, 16 tokens out. Every pair must load and generate before any full run. Failures go through the fix protocol while the passing models move on.

**4. Runs.** Split the models across pods. For each, generate jobs (`pie-evals jobs --tier weekly --pie-commit <sha> --platform [PLATFORM] --artifact <id> --workload raw-512-256 --workload c32 --workload pf256-512 --out jobs`; `--artifact` repeats), run them (`pie-evals-node run --job jobs/<job>.json --out out/<job>`), then the quality check (`pie-evals-node parity <artifact> --platform [PLATFORM] --pie-commit <sha> --features cuda --store parity-out/store --tag [TAG] --tag-kind manual --out parity-out`). Collect and import into the database as each finishes, publish the site, rerun the coverage script.

**5. Anomalies.** Read the numbers as they land. Investigate when pie is below half of the best other engine in a setup, latency jumps between rounds, a round's CoV is over 2%, KL is over 0.05 or top-1 agreement is under 0.90. Profile, fix if it is targeted (a flag, a kernel path, a harness bug), rerun. If it needs a redesign of pie, write the root cause in the report and move on.

**6. Done.** When the coverage script exits 0: terminate every pod (see "Pods"), then post the final report as the last comment on the tracking issue.

## Final report

1. The coverage table (`tools/device_coverage.py` output) with every cell done.
2. Per model: the variant measured (full, alternate or miniature cut), and pie against vLLM and SGLang in each setup as a ratio.
3. Every PR opened (forks, pie, harness), one line each with its link, so a reviewer can go through them in order.
4. The `support.yaml` rows added, with their reasons.
5. pie anomalies and what to change in pie, most important first.
6. New lessons, also added to the Lessons section below.

## Lessons (agents append here)

- Access: the database URL is a CI secret an agent cannot read, and the pie-project RunPod account (the one CI uses) has the `development` template (`pieproject/runpod-dev`), not the Liszt one. Record through CI; debug on rented pods.

- L40S (sm_89, Ada): vLLM 0.32's DeepSeek-V4.1 path emits `mul.bf16x2`, which needs sm_90; SGLang's `mhc_pre` split-k kernel only takes `hc_hidden_size` 16384 or 28672 (the mini8 cut has 20480). Both are fork candidates.
- SGLang on L40S: qwen3.8-flash-next fails in a CUTLASS DSL kernel (block shape) and in CUDA-graph capture; mimo-v2.6-flash fails `Hidden size mismatch` on the miniature. Start these early.
