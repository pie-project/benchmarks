# Automations

Every workflow in this repo, when it runs, and what it needs. Update this file when you add or change a workflow.

## Runs on its own

| Workflow | When | What it does | Secrets |
| --- | --- | --- | --- |
| `ci` | every push and pull request | lint, tests, matrix check | none |
| `pie eval` | a pie release (sent by the pie repo with its tag), or by hand with a tag | measures pie and the competitors' latest releases on the Macs and saves the results to the database under that tag | `PIE_EVALS_DB`, `GH_RUNNER_PAT`, `HF_TOKEN` |
| `pages` | every push to main and after each eval | builds the site from the database on liszt | `PIE_EVALS_DB` |
| `reap-pods` | hourly, at minute 17 | stops RunPod pods that were left running | `RUNPOD_API_KEY`, `GH_RUNNER_PAT` |

A commit without a tag is not measured. Each run is stored with its tag (a release like `0.5.2`, or `manual-<time>`) and its date and time.

## Started by hand

| Workflow | What it does | Secrets |
| --- | --- | --- |
| `smoke` | pie against its own history on small models | `RUNPOD_API_KEY`, `GH_RUNNER_PAT`, `HF_TOKEN` |
| `nightly` | pie against the other engines on rented GPUs | same as smoke |
| `weekly` | the largest set of models and machines | same as smoke |
| `quality` | scores models on gsm8k, ifeval, mmlu, arc and math500 on a Mac | `HF_TOKEN` |
| `collect` | imports the results of an earlier run into the database | `PIE_EVALS_DB` |
| `runpod-check` | rents one pod for a few minutes to check the RunPod setup | `RUNPOD_API_KEY`, `GH_RUNNER_PAT` |

`smoke` can also be started by the pie repo with a `pie-commit` dispatch. The `nightly` and `weekly` schedules are switched off until their cost is known.

## Shared pieces

- `tier.yml` is the body of every eval: plan the jobs, rent pods if needed, run on the machines, save the results. `pie eval`, `smoke`, `nightly` and `weekly` all call it.
- Results are committed to `main` by `pie-evals-bot`. These commits do not start `ci`.
- Repo variables: `PIE_REPO`, `RUNPOD_IMAGE`, `RUNPOD_NETWORK_VOLUME_ID`.

## Machines

- Macs are resident GitHub runners. `config.json` lists the only Macs that may be used: a Mac not listed there gets no job from any workflow or from the site's Bench button, and is not shown on the site. Add one with `infra/mac/setup-runner.sh`.
- RunPod pods are rented per run and end themselves when idle. `reap-pods` is the last safety net.
