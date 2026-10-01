# pie-evals

Benchmark & evaluation framework for [pie](https://github.com/pie-project/pie):
performance against vLLM / SGLang / llama.cpp / mlx-lm on every supported
platform, accuracy preservation against a same-weights reference, and a
coverage matrix in which nothing goes missing silently.

Read `docs/design.md` first.

## Layout

- `matrix/` what exists: engines, platforms, models, workloads, inferlets, modes, support declarations, tier suites.
- `src/pie_evals/` the code, one folder per job: `plan/`, `node/`, `results/`, `site/`, `pods/`, `quality/`, `schema/`.
- `store/` the measured results, committed. `reports/` the tables built from them.
- `infra/` RunPod and Mac runner setup. `.github/workflows/` the tiers and bookkeeping.

Each folder has a short README.

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

## Macs: pie against Ollama

The `targeted` tier measures pie against [Ollama](https://github.com/ollama/ollama) on self-hosted Apple Silicon Macs. Every pie commit on main (or a manual `pie eval` run) is measured on the Macs listed in `config.json`. Each model runs twice: pie on its own checkpoint, Ollama on the tag it ships for the same model. Both engines get the same prompts through pie's `scripts/bench/common.py` client, and the `pages` workflow publishes prefill and decode side by side. The `quality` workflow scores the same models on gsm8k, ifeval, mmlu, arc and math500.

```sh
.venv/bin/pie-evals jobs --tier targeted --pie-commit <sha> --platform m5-max-48g --out jobs
.venv/bin/pie-evals-node run --job jobs/<job>.json --out out/<job> --download
.venv/bin/pie-evals collect --tier targeted out/<job> && .venv/bin/pie-evals dashboard --out site
```

A Mac runner is registered with `infra/mac/setup-runner.sh` and removed with `infra/mac/remove-runner.sh`. It needs AC power, Low Power Mode off, Rust with `wasm32-wasip2`, uv and Ollama.
