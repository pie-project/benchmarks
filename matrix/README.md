# matrix

Lists of everything we can measure. The plan is built by combining them.

- `engines.yaml` the engines and their pinned versions.
- `platforms.yaml` the machines. `runpod.yaml` says where rented GPUs live.
- `models.yaml` the models.
- `workloads.yaml` the prompt shapes.
- `programs.yaml` the pie inferlets.
- `modes.yaml` the run modes, like tensor parallel.
- `support.yaml` the combinations we know do not work.
- `suites.yaml` which combinations go in which tier.
- `install.yaml` each engine's install size per platform, with how it was measured (the site's Install Size cards).

Run `pie-evals check` after editing.
