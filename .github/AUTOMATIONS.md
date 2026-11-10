# Automations

Every workflow in this repo, when it runs, and what it needs. Update this file when you add or change a workflow.

## Runs on its own

| Workflow | When | What it does | Secrets |
| --- | --- | --- | --- |
| `ci` | every push and pull request | lint, tests, matrix check | none |
| `pie eval` | a pie release (sent by the pie repo with its tag), or by hand with a tag | measures pie and the competitors' latest releases on the Macs and saves the results to the database under that tag | `PIE_EVALS_DB`, `GH_RUNNER_PAT`, `HF_TOKEN` |
| `pages` | every push to main and after each eval | builds the site from the database on liszt | `PIE_EVALS_DB` |
| `reap-pods` | hourly, at minute 17 | stops RunPod pods that were left running | `RUNPOD_API_KEY`, `GH_RUNNER_PAT` |
| `tpu` | daily at 09:00 UTC, or by hand with a pie commit | measures pie main on one Google Cloud TPU v6e chip (`tpu-v6e-1`: pie only, Qwen3.5-0.8B, `ss-512-256` and `c32`). The schedule runs only when a pie commit since the last TPU run changed `crates/engine-xla` or `crates/kernels-xla`; a manual run always runs. It creates a TPU VM, builds pie there, runs the job, deletes the VM even when the run fails, and saves the results to the database as nightly rows tagged `main-<first 9 characters of the commit>`. By hand, `platform` picks another TPU (`tpu-v5e-1`, `tpu-v5p-8`, `tpu-v4-8`, `tpu7x-4`: the smallest single-host slice, reported per chip) for a release's Raw rows (`tier=weekly`), trying the platform's `tpu.zones` (or `zone`) on demand, then spot | `GCP_TPU_SA_KEY`, `PIE_EVALS_DB`, `HF_TOKEN` |

A commit without a tag is not measured. Each run is stored with its tag (a release like `0.5.2`, or `manual-<time>`) and its date and time.

## Started by hand

| Workflow | What it does | Secrets |
| --- | --- | --- |
| `smoke` | pie against its own history on small models | `RUNPOD_API_KEY`, `GH_RUNNER_PAT`, `HF_TOKEN` |
| `nightly` | pie against the other engines on rented GPUs | same as smoke |
| `weekly` | the largest set of models and machines | same as smoke |
| `quality` | scores models on gsm8k, ifeval, mmlu, arc and math500 on a Mac | `HF_TOKEN` |
| `collect` | imports the results of an earlier run into the database, or deletes tags, engines or workloads from it | `PIE_EVALS_DB` |
| `runpod-check` | rents one pod for a few minutes to check the RunPod setup | `RUNPOD_API_KEY`, `GH_RUNNER_PAT` |

The `nightly` and `weekly` schedules are switched off until their cost is known.

## Google Cloud TPU

`tpu` needs the secret `GCP_TPU_SA_KEY`: the JSON key of a service account in the GCP project `pie-project-510103` that may create, ssh to and delete TPU VMs. The roles that cover it: `roles/tpu.admin` (create, describe, delete), `roles/iam.serviceAccountUser` (the VM runs as the project's default compute service account), and `roles/compute.osAdminLogin` with OS Login on, or `roles/compute.instanceAdmin.v1` without it (`gcloud ... tpu-vm ssh` pushes its key into the project metadata). TPU7x is not served by the TPU API: it is a Compute Engine instance (`roles/compute.instanceAdmin.v1`). Each scheduled run uses one on-demand v6e-1 in `us-east5-b` at $2.70 an hour, about 1 to 1.5 hours a run. The last measured commit is kept in `~/.pie-evals/tpu-last-commit` on the site laptop that runs collect (the `handoff` runners); with none, the next scheduled run measures.

## Shared pieces

- `tier.yml` is the body of every eval: plan the jobs, rent pods if needed, run on the machines, save the results. `pie eval`, `smoke`, `nightly` and `weekly` all call it.
- Results are committed to `main` by `pie-evals-bot`. These commits do not start `ci`.
- Repo variables: `PIE_REPO`, `RUNPOD_IMAGE`, `RUNPOD_NETWORK_VOLUME_ID`.

## Machines

- Macs are resident GitHub runners. `config.json` lists the only Macs that may be used: a Mac not listed there gets no job from any workflow or from the site's Bench button, and is not shown on the site. Add one with `infra/mac/setup-runner.sh`.
- RunPod pods are rented per run and end themselves when idle. `reap-pods` is the last safety net.
- The TPU VM is created by `tpu` for one run (`pie-evals-tpu-<run id>-<attempt>`) and deleted by its `teardown` job.
