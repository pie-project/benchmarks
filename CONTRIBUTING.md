# Contributing to Pie Bench

Engine authors, model authors and anyone who spots a number that looks wrong are
welcome here. Small, focused pull requests are the easiest to review.

## Report a number

Open an [issue](https://github.com/pie-project/pie-evals/issues), or use
**Report an Issue** on [the site](https://benchmarks.pie-project.org/), which fills
in the machine, model, workload and engine for you. Say what you expected and
why: a run log, a profile, or your own measurement.

## Add or update an engine

1. Pin it in `src/pie_bench/matrix/engines.yaml`: its id, operating systems and
   backends, weight formats, version (`pin`) and where releases come from
   (`release_source`).
2. Add its driver in `src/pie_bench/node/engines/<engine>.py`, following an
   existing one such as `vllm.py` or `llamacpp.py`.
3. Add a benchmark client in `src/pie_bench/clients/` if the engine has no
   OpenAI-compatible server.
4. Put its serving settings in `src/pie_bench/node/engines/recipes/<engine>.yaml`.
   You know your engine's best flags: tuned settings are welcome, as long as they
   are the same for every model on a platform.
5. Check it with `pie-bench plan --engines <engine>`, then a run on a machine
   you have.

## Add a model

Add it to `src/pie_bench/matrix/models.yaml` with its Hugging Face repo
(`base_model`), weight scheme and expected size, then check it with
`pie-bench plan --models <model>`.

## Develop

```bash
uv venv && uv pip install -e ".[dev,server]"
.venv/bin/ruff check src server tests
.venv/bin/pytest -q
```

To run the API and the site locally, see the [README](README.md#results-and-the-api).

## Pull requests

One change per pull request, with a short title and the commands you ran. A
change that moves numbers should show before and after results from at least one
machine.
