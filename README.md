<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/bench-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/assets/bench-light.svg">
    <img alt="Pie Bench: pie against other inference engines, on your own machine"
         src=".github/assets/bench-light.svg"
         width="30%">
    <p></p>
  </picture>

[Benchmarks] | [API] | [Pie] | [Docs] | [Paper (SOSP'25)]
</div>

[Benchmarks]: https://benchmarks.pie-project.org/
[API]: https://bench-api.pie-project.org/v1/catalog
[Pie]: https://github.com/pie-project/pie
[Docs]: https://pie-project.org/docs
[Paper (SOSP'25)]: https://ingim.org/papers/gim2025pie.pdf

Pie Bench measures [pie](https://github.com/pie-project/pie) against other
inference engines on your own machine: the same models, the same prompts, each
engine at a pinned version. One command detects the machine, picks the models
that fit, installs every engine, builds pie, measures them all, and uploads one
signed submission to [benchmarks.pie-project.org][Benchmarks].

This repository holds the `pie-bench` command line tool, the results API the
site reads, the site itself, the phone app that runs the same workloads on
iPhone and Android, and Docker images for cloud GPUs and TPUs.

## Install

```bash
pip install pie-bench
pie-bench doctor
```

Needs Python 3.11+, git, [Rust](https://rustup.rs) and [uv](https://docs.astral.sh/uv/):
Apple Silicon on a Mac, NVIDIA or AMD GPUs on Linux, or a Cloud TPU. Or skip the
setup with a ready image, one per cloud (`pieproject/benchmark-runpod-cuda`,
`-runpod-rocm`, `-digitalocean-cuda`, `-digitalocean-rocm`, `-gcloud-tpu`); see
[docker/](docker/README.md).

## Run a benchmark

```bash
pie-bench plan                                   # what would run here
pie-bench run                                    # measure and upload
pie-bench run --models qwen3.6-35b               # only some models
pie-bench run --engines pie,llamacpp             # only some engines
pie-bench run --pie 0.6.0                        # a pie release, branch or commit
pie-bench run --no-upload                        # keep the results local
pie-bench upload ~/.pie-bench/runs/<time>        # upload later
pie-bench quality --models <artifact id>         # model accuracy on question sets
```

Nothing is sent while a run measures. Each run writes one folder under
`~/.pie-bench/runs/`:

| File | What |
|---|---|
| `records.jsonl` | one line per measured cell |
| `run.log` | the full log, for audit and debugging |
| `submission.json.gz` | both, with machine specs and versions: what gets uploaded |

Uploads need a token, made the first time (`pie-bench login`) and kept in
`~/.config/pie-bench/token`.

## Results and the API

The site is a static page that reads the API. Reads are public JSON, rebuilt
after each upload; writes need a token with an upload quota.

| Method | Path | What |
|---|---|---|
| GET | `/healthz` | service health |
| GET | `/v1/catalog` | machines, models, engines, workloads and the newest release |
| GET | `/v1/results` | the newest release: its results and quality scores |
| GET | `/v1/releases/latest` | the same as `/v1/results` |
| GET | `/v1/head-to-head` | pie against each engine, per platform |
| GET | `/v1/footprint` | download size of pie, vLLM and SGLang |
| GET | `/v1/profiles` | each grid cell's forward-pass profile of its two fastest engines |
| POST | `/v1/tokens` | a signed upload token |
| POST | `/v1/submissions` | upload a `submission.json.gz` |
| POST | `/v1/profiles` | upload the profiles a `pie-bench` run made |

Run the API locally against Postgres:

```bash
uv venv && uv pip install -e ".[dev,server]"
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pie postgres:16-alpine
DATABASE_URL=postgresql://postgres:pie@localhost/postgres JWT_SECRET=$(openssl rand -hex 32) \
  .venv/bin/uvicorn server.app:app --port 8790
PIE_BENCH_API=http://localhost:8790 pie-bench run
```

`render.yaml` deploys the API and its database on Render.

## Phones

The [phone app](mobile) runs the phone workloads on iPhone and Android with
pie, llama.cpp, LiteRT-LM, MLC LLM and MLX Swift, on the same prompts as the
Macs. `pie-bench import-phone` turns its shared `records.jsonl` into a
submission, shown on the site's Mobile page. The import computes every number
with the harness's own code, as for a Mac run, and keeps the median round; it
trusts nothing the phone derived. A phone not listed in
`src/pie_bench/matrix/phones.yaml` is stored as `<os>-<model>`.

## Develop

```bash
uv venv && uv pip install -e ".[dev,server]"
.venv/bin/ruff check src server
.venv/bin/ruff format --check src server
```

[`src/pie_bench/matrix`](src/pie_bench/matrix) declares what exists: engines
and their pins, machines, models and workloads. To add an engine, add its
driver under `src/pie_bench/engines`, its client under
`src/pie_bench/clients`, and its entry in `matrix/engines.yaml`. A version tag
(`git tag v0.1.4 && git push --tags`) runs the release workflow, which builds
the wheel and sdist for PyPI and a GitHub release.

## Community & License

[Discord](https://discord.gg/R62Udyzum) ·
[Issues](https://github.com/pie-project/benchmarks/issues) ·
[Pie](https://github.com/pie-project/pie)

[Apache License 2.0](LICENSE).
