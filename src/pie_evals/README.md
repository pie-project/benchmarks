# pie_evals

The Python code. Each folder does one thing.

- `plan/` decides what to run. It reads `matrix/` and writes job files.
- `node/` runs the jobs on the machine being measured and writes records.
- `results/` saves the records in `store/` and builds the reports.
- `site/` builds the web page from the store.
- `pods/` rents RunPod GPUs and turns them into GitHub runners.
- `quality/` scores models on question sets like gsm8k and mmlu.
- `schema/` holds the shared data shapes: Cell, JobSpec, Record.
- `cli.py` is the `pie-evals` command. `node/cli.py` is the `pie-evals-node` command.
