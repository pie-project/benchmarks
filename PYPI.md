# pie-bench

Measure [Pie](https://github.com/pie-project/pie) against other inference engines on your own machine, and share the results on [benchmarks.pie-project.org](https://benchmarks.pie-project.org).

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

Requirements: Python 3.11+, git, [Rust](https://rustup.rs) and [uv](https://docs.astral.sh/uv/). On a Mac, Apple Silicon. On Linux, NVIDIA or AMD GPUs, or a Cloud TPU.
