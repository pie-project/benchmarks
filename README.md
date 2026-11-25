<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/bench-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/assets/bench-light.svg">
    <img alt="Pie Bench: an open benchmark for LLM inference engines"
         src=".github/assets/bench-light.svg"
         width="30%">
    <p></p>
  </picture>

[Benchmarks] | [Bench Book] | [PyPI] | [API] | [Pie]
</div>

[Benchmarks]: https://benchmarks.pie-project.org/
[Bench Book]: https://benchmarks.pie-project.org/#approach
[PyPI]: https://pypi.org/project/pie-bench/
[API]: https://bench-api.pie-project.org/v1/catalog
[Pie]: https://github.com/pie-project/pie

Pie Bench is an open, apples-to-apples benchmark for LLM inference. vLLM,
SGLang, TensorRT-LLM, llama.cpp, MLX, Ollama, MLC, pie and friends: same weights,
same prompts, same silicon, pinned versions. Datacenter GPUs, TPUs, Apple
Silicon, browsers and phones. Ship a kernel, watch it land. Spot a gap, go close it.

[Reproducible][PyPI] by default. One command sizes up the box, picks the models
that fit in memory, installs every engine at its pinned version, runs the sweep,
and uploads a signed submission to [benchmarks.pie-project.org][Benchmarks].

Every gap over 25% is re-measured under an end-to-end
GPU profiler on fresh prompts. It's marked verified only if the profile agrees
with the benchmark within 10%; otherwise it's rerun. Details in the [Bench Book].

## Install

```bash
pip install pie-bench
pie-bench doctor
```

Needs Python 3.11+, git, [Rust](https://rustup.rs) and [uv](https://docs.astral.sh/uv/):
Apple Silicon on a Mac, NVIDIA or AMD GPUs on Linux, or a Cloud TPU. Or run it in
the Docker image for your cloud (listed above); see [docker/](docker/README.md).

## Run a benchmark

```bash
pie-bench plan                                   # what would run here
pie-bench run                                    # measure and upload
pie-bench run --models qwen3.6-35b               # only some models
pie-bench run --engines pie,llamacpp             # only some engines
pie-bench run --pie 0.6.0                        # a pie release, branch or commit
pie-bench run --no-upload                        # keep the results local
pie-bench upload ~/.pie-bench/runs/<time>        # upload later
pie-bench quality                                # model accuracy on question sets
```

Nothing is sent while a run measures. Each run writes one folder under
`~/.pie-bench/runs/`:

- `records.jsonl`: one line per measured cell
- `run.log`: the full log, for audit and debugging
- `submission.json.gz`: both, with machine specs and versions; this is what gets uploaded

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
| GET | `/v1/head-to-head` | pie against each engine, per platform |
| GET | `/v1/footprint` | download size of pie, vLLM and SGLang |
| POST | `/v1/tokens` | a signed upload token |
| POST | `/v1/submissions` | upload a `submission.json.gz` |

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
submission, shown on the site's Mobile page.

## Develop

```bash
uv venv && uv pip install -e ".[dev,server]"
.venv/bin/ruff check src server tests
.venv/bin/pytest -q
```

[`src/pie_bench/matrix`](src/pie_bench/matrix) declares what exists: engines
and their pins, machines, models and workloads. To add an engine, add its
driver under `src/pie_bench/node/engines`, its client under
`src/pie_bench/clients`, and its entry in `matrix/engines.yaml`. A tag
(`git tag v0.1.4 && git push --tags`) publishes a release to PyPI.

## Community & License

[Discord](https://discord.gg/R62Udyzum) ·
[Issues](https://github.com/pie-project/pie-evals/issues) ·
[Discussions](https://github.com/pie-project/pie/discussions) ·
[Contributing](CONTRIBUTING.md)

[Apache License 2.0](LICENSE) ([NOTICE](NOTICE)).
