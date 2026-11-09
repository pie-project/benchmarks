# pie-evals

Benchmark & evaluation framework for [pie](https://github.com/pie-project/pie):
performance against vLLM / SGLang / llama.cpp / mlx-lm on every supported
platform, accuracy preservation against a same-weights reference, and a
coverage matrix in which nothing goes missing silently.

Read `docs/design.md` first.

## Layout

- `matrix/` what exists: engines, platforms, models, workloads, inferlets, modes, support declarations, tier suites.
- `src/pie_evals/` the code, one folder per job: `plan/`, `node/`, `results/`, `site/`, `pods/`, `quality/`, `schema/`.
- Results live in the Postgres database on liszt (`PIE_EVALS_DB`); nothing is committed back to git.
- `infra/` RunPod and Mac runner setup. `.github/workflows/` the tiers and bookkeeping.

Each folder has a short README. The workflows are listed in [.github/AUTOMATIONS.md](.github/AUTOMATIONS.md).

## Quick start

```sh
uv venv && uv pip install -e ".[dev,orchestrate]"
.venv/bin/pytest -q
.venv/bin/pie-evals expand                      # matrix summary + budgets
.venv/bin/pie-evals jobs --tier smoke --pie-commit <sha> --platform l40s-x1 --out jobs
PIE_ROOT=/root/pie .venv/bin/pie-evals-node run --job jobs/<job>.json --out out/<job>
.venv/bin/pie-evals collect --tier smoke out/<job> && .venv/bin/pie-evals report --tier smoke
```

Node prerequisites: the pie checkout (built at the pinned commit by the node), the checkpoints in the HF cache (`resolve_local_model` refuses to download), baseline venvs at the pins in `matrix/engines.yaml` (`VLLM_PY`, `SGLANG_PY`, `LLAMA_SERVER_BIN`, `MLX_PY`).

## Macs: pie against other engines

The `targeted` tier measures pie against [llama.cpp](https://github.com/ggml-org/llama.cpp), [mlx-lm](https://github.com/ml-explore/mlx-lm) and [Splash](https://github.com/incoai/splash) on self-hosted Apple Silicon Macs. Every pie commit on main (or a manual `pie eval` run) is measured on the Macs listed in `config.json`, on the models of one of its two suites: `targeted` (Tier 1, what a release runs) or `full` (every model the site lists); a manual run picks one with its `suite` input. pie runs on its own checkpoint; each other engine runs on its own copy of the same model: llama.cpp on a Q4_K_M GGUF, mlx-lm on the MLX checkpoint pie reads, Splash on the two Qwen models it ships for. An engine is measured once per version, not on every pie commit. All engines get the same prompts through the `bench/common.py` client, and the site shows prefill and decode side by side, with a select for the engine to compare against. The `quality` workflow scores the models on gsm8k, ifeval, mmlu, arc and math500.

```sh
.venv/bin/pie-evals jobs --tier targeted --pie-commit <sha> --platform m5-max-64g --out jobs
.venv/bin/pie-evals-node run --job jobs/<job>.json --out out/<job> --download
.venv/bin/pie-evals collect --tier targeted out/<job>
```

A Mac runner is registered with `infra/mac/setup-runner.sh` and removed with `infra/mac/remove-runner.sh`. It needs AC power, Low Power Mode off, Rust with `wasm32-wasip2`, and uv. Splash, llama.cpp and mlx-lm are fetched at their pinned versions; Splash needs macOS 26.4 or newer.

## Trying a change to the harness

Push your change to a branch and start the eval from that branch:

```sh
gh workflow run pie-eval.yml --ref my-branch -f macs=m5-max-64g -f benchmarks=ob-short-100 -f rerun=true
```

The run uses the branch's code and saves nothing to the database, so the site stays untouched.
