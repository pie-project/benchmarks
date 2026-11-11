# pie-bench

Measure [pie](https://github.com/pie-project/pie) against other inference engines on your own machine, and publish the results to [pie-project.org/benchmarks](https://pie-project.org/benchmarks).

This repository holds two things:

| | What | Where | Runs on |
|---|---|---|---|
| 1 | `pie-bench`, the command line tool anyone installs | `src/pie_bench/` | your machine |
| 2 | the results API the website reads | `server/` | Render |

The website itself lives in [pie-project/website](https://github.com/pie-project/website).

## Run it

```sh
pip install pie-bench
pie-bench doctor
pie-bench run
```

`pie-bench run` detects the machine, picks the models that fit, installs each engine at its pinned version, builds pie, measures every engine on the same prompts, and uploads one signed submission when it is done. Nothing is sent while it runs.

```sh
pie-bench plan                                   # what would run here
pie-bench run --models qwen3.6-35b               # only some models
pie-bench run --engines pie,llamacpp             # only some engines
pie-bench run --pie 0.6.0                        # a pie release, branch or commit
pie-bench run --no-upload                        # keep the results local
pie-bench upload ~/.pie-bench/runs/<time>        # upload later
```

Each run writes a folder under `~/.pie-bench/runs/`:

| File | What |
|---|---|
| `records.jsonl` | one line per measured cell |
| `run.log` | the full log, for audit and debugging |
| `submission.json.gz` | both, plus machine specs and versions: what gets uploaded |

Uploading needs a token, made automatically the first time and kept in `~/.config/pie-bench/token`.

Requirements: Python 3.11+, git, [Rust](https://rustup.rs) and [uv](https://docs.astral.sh/uv/). On a Mac, Apple Silicon. On Linux, NVIDIA GPUs.

## The API

| Method | Path | What |
|---|---|---|
| GET | `/healthz` | service health |
| GET | `/v1/catalog` | machines, models, engines, workloads and the list of releases |
| GET | `/v1/releases/latest` | the newest release: its results and quality scores |
| GET | `/v1/releases/{id}` | one release: its results and quality scores |
| GET | `/v1/head-to-head` | pie against each engine, per platform |
| POST | `/v1/tokens` | a signed upload token |
| POST | `/v1/submissions` | upload a `submission.json.gz` |
| PATCH | `/v1/tokens/{id}` | admin: set a token's quota, body `{"quota": n}` |

Reads are public JSON, built once after each upload, gzip-compressed and carry an ETag. Writes need a token; each token has an upload quota, every upload is checked and stored in one transaction.

Run it locally:

```sh
uv venv && uv pip install -e ".[dev,server]"
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pie postgres:16-alpine
DATABASE_URL=postgresql://postgres:pie@localhost/postgres JWT_SECRET=$(openssl rand -hex 32) ADMIN_TOKEN=dev \
  .venv/bin/uvicorn server.app:app --port 8790
PIE_BENCH_API=http://localhost:8790 pie-bench run
```

Deploy: `render.yaml` is a Render Blueprint (the API, its Postgres 16 and generated secrets); `bench-api.pie-project.org` is a CNAME to the service.

## Develop

```sh
uv venv && uv pip install -e ".[dev,server]"
.venv/bin/ruff check src server tests
.venv/bin/pytest -q
```

`src/pie_bench/matrix/` declares what exists: engines and their pins, machines, models, workloads. To add an engine, add its driver under `src/pie_bench/node/engines/`, its client under `src/pie_bench/clients/` and its entry in `matrix/engines.yaml`.

A release is a tag: `git tag v0.1.1 && git push --tags` publishes to PyPI.
