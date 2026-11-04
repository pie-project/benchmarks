"""``pie-evals-node`` — what runs on the machine under test."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from pie_evals.quality.tasks import TASKS
from pie_evals.schema import JobSpec

from .build import DEFAULT_PIE_ROOT


@click.group()
def main():
    pass


def mask_gpus(job: JobSpec, env: dict | None = None) -> str | None:
    """A pod hosts every platform of its GPU type, so an x1 job on an x2 pod sees
    both cards: mask CUDA to the platform's count (the first devices). Set once,
    before any engine starts, so every subprocess inherits it; an explicit
    CUDA_VISIBLE_DEVICES from the runner is left alone."""
    import shutil
    import subprocess

    env = os.environ if env is None else env
    if env.get("CUDA_VISIBLE_DEVICES") or not job.cells or not shutil.which("nvidia-smi"):
        return None
    count = job.cells[0].platform.count
    try:
        visible = len([ln for ln in subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=20).stdout.splitlines() if ln.startswith("GPU ")])
    except (OSError, subprocess.SubprocessError):
        return None
    if visible <= count:
        return None
    env["CUDA_VISIBLE_DEVICES"] = ",".join(str(i) for i in range(count))
    click.echo(f"{visible} GPUs visible, platform {job.platform_id} uses {count}: CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']}", err=True)
    return env["CUDA_VISIBLE_DEVICES"]


@main.command("run")
@click.option("--job", "job_path", type=click.Path(exists=True), required=True)
@click.option("--pie-root", type=click.Path(exists=True), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--out", type=click.Path(), default="out")
@click.option("--hf-cache", type=click.Path(), default=None)
@click.option("--no-build", is_flag=True, help="use the pie binary already in target/release")
@click.option("--only", multiple=True, help="restrict to cells whose key contains this substring")
@click.option("--download", is_flag=True, help="fetch missing full checkpoints here (default: no — `prepare` does that once before the fan-out)")
def run(job_path, pie_root, out, hf_cache, no_build, only, download):
    """Execute a JobSpec and write records.jsonl under --out."""
    from .runner import NodeRunner

    job = JobSpec.model_validate_json(Path(job_path).read_text())
    mask_gpus(job)
    if only:
        job = job.model_copy(update={"cells": [c for c in job.cells if any(s in c.cell_key for s in only)]})
    from .machine import MachineBusy, machine_lock

    try:
        # the runner's clock starts once the machine is ours, so the wait is not taken out of the job's budget
        # a Mac with two runners gets two shards at once: the second waits for the first however long it takes
        # (the workflow's timeout is the bound), instead of giving up and dropping its cells
        wait_s = float(os.environ.get("PIE_MACHINE_LOCK_WAIT_S") or 24 * 3600)
        with machine_lock(job.job_id, max_wait_s=wait_s, log=lambda m: click.echo(m, err=True)):
            runner = NodeRunner(job, pie_root=Path(pie_root), out_dir=Path(out), hf_cache=Path(hf_cache) if hf_cache else None, build=not no_build, download=download)
            recs = runner.run()
    except MachineBusy as e:
        # nothing is recorded, so the next run measures these cells
        click.echo(f"{e}; nothing measured this time", err=True)
        sys.exit(3)  # a job that measured nothing must not look like a success
    by = {}
    for r in recs:
        by[str(r.status)] = by.get(str(r.status), 0) + 1
    click.echo(json.dumps({"run_id": runner.run_id, "records": len(recs), "by_status": by}))


@main.command("build")
@click.option("--pie-commit", required=True)
@click.option("--features", default="cuda", show_default=True, help="comma-separated pie cargo features")
@click.option("--pie-root", type=click.Path(), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--mirror", type=click.Path(), default=os.environ.get("PIE_MIRROR"), help="bare mirror on the shared volume; updated, then used as clone source")
@click.option("--target-dir", type=click.Path(), default=os.environ.get("CARGO_TARGET_DIR"))
@click.option("--force", is_flag=True)
def build_cmd(pie_commit, features, pie_root, mirror, target_dir, force):
    """Build pie at a commit and cache the artifacts (binary, engine wheel, bench wasm) under $PIE_EVALS_CACHE/builds.
    The tier workflow runs this once before the bench fan-out."""
    from . import build as pb

    feats = [f for f in features.split(",") if f]
    if mirror:
        pb.update_mirror(Path(mirror))
    pb.ensure_checkout(Path(pie_root), pie_commit, mirror=Path(mirror) if mirror else None)
    if pb.is_cached(pie_commit, feats) and not force:
        click.echo(f"cache hit: {pb.cache_dir(pie_commit, feats)}")
        return
    out = pb.build(Path(pie_root), pie_commit, feats, target_dir=Path(target_dir) if target_dir else None, python=os.environ.get("PIE_PY", "python3"))
    click.echo(str(out))


@main.command("prepare")
@click.option("--tier", type=click.Choice(["smoke", "nightly", "weekly", "targeted"]), required=True)
@click.option("--matrix", "matrix_dir", default="matrix")
@click.option("--platform", "platforms", multiple=True, help="restrict to artifacts these platforms run (default: all of the tier)")
@click.option("--engine", "engines_f", multiple=True)
@click.option("--program", "programs_f", multiple=True)
@click.option("--pie-root", type=click.Path(), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--pie-commit", default=None, help="import quantized checkpoints as .zt artifacts for this commit (needs the built pie binary)")
@click.option("--hf-cache", type=click.Path(), default=None)
def prepare_cmd(tier, matrix_dir, platforms, engines_f, programs_f, pie_root, pie_commit, hf_cache):
    """Fetch every checkpoint a tier needs (downloads + miniatures) so bench pods find them on the volume.
    Failures are reported per artifact and never abort the rest; exit 1 if any failed."""
    from pie_evals.plan.matrix import Matrix
    from pie_evals.schema import Tier

    from .snapshots import ensure_snapshot, hf_cache_dir

    m = Matrix.load(matrix_dir)
    cells = m.runnable(Tier(tier))
    if platforms:
        cells = [c for c in cells if c.platform.id in platforms]
    if engines_f:
        cells = [c for c in cells if str(c.engine) in engines_f]
    if programs_f:
        cells = [c for c in cells if c.program.id in programs_f]
    arts = {c.artifact.id: c.artifact for c in cells}
    cache = Path(hf_cache) if hf_cache else hf_cache_dir()
    failed = {}
    from .build import bench_python
    from .importer import ensure_artifact, needs_import

    pie_bin = Path(pie_root) / "target/release/pie"
    say = lambda m_: click.echo(m_, err=True)  # noqa: E731
    shrink_py = os.environ.get("PIE_PY") or str(bench_python(log=say))  # shrink_checkpoint needs numpy
    for aid, art in sorted(arts.items()):
        try:
            p = ensure_snapshot(art, cache, pie_root=Path(pie_root), python=shrink_py, log=say)
            if pie_commit and needs_import(art) and pie_bin.exists():
                p = ensure_artifact(art, p, pie_bin, pie_commit, log=say)
            click.echo(f"ok    {aid}: {p}")
        except Exception as e:
            failed[aid] = str(e).strip().splitlines()[-1][:200] if str(e).strip() else repr(e)
            click.echo(f"FAIL  {aid}: {failed[aid]}", err=True)
    from .baselines import SPECS, ensure_baseline

    engines = {(str(c.engine), str(c.platform.backend)) for c in cells}
    for e, backend in sorted(x for x in engines if x[0] in SPECS):
        pin = m.engines[e].pin_for(backend)
        try:
            ensure_baseline(e, pin, backend=backend, log=lambda m_: click.echo(m_, err=True))
            click.echo(f"ok    baseline {e}=={pin}")
        except Exception as ex:
            failed[f"baseline:{e}"] = str(ex)[:200]
            click.echo(f"FAIL  baseline {e}=={pin}: {failed[f'baseline:{e}']}", err=True)
    click.echo(json.dumps({"prepared": len(arts) - len(failed), "failed": failed}))
    sys.exit(1 if failed else 0)


@main.command("quality", help="Score model quality (GSM8K, IFEval, MMLU, ARC, MATH-500) on sampled questions, on each model's arms.")
@click.option("--artifact", "artifacts", multiple=True, required=True, help="artifact id from matrix/models.yaml (a pie checkpoint or a baseline arm)")
@click.option("--task", "tasks", multiple=True, type=click.Choice(sorted(TASKS)), default=("gsm8k", "ifeval", "mmlu", "arc", "math500"), show_default=True)
@click.option("--n", type=int, default=100, show_default=True)
@click.option("--matrix", "matrix_dir", default="matrix")
@click.option("--store", "store_dir", default=None, help="postgresql://... or a directory (default: $PIE_EVALS_DB, else ./store)")
@click.option("--pie-root", type=click.Path(), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--tag", default=None, help="the release or manual tag these scores belong to")
@click.option("--tag-kind", type=click.Choice(["release", "manual"]), default=None)
@click.option("--platform", "platform_id", default=None, help="the Mac's platform id, stored on each row (empty: the quality Mac)")
def quality_cmd(artifacts, tasks, n, matrix_dir, store_dir, pie_root, tag, tag_kind, platform_id):
    from pie_evals.quality.run import TasksSkipped, run_quality

    from .machine import machine_lock

    skipped, failed = [], []
    with machine_lock("quality", max_wait_s=6 * 3600, log=lambda m_: click.echo(m_, err=True)):
        for a in artifacts:
            # one engine that fails to load must not drop the other arms of the run: say so, go on, and fail at the end
            try:
                run_quality(a, list(tasks), n, matrix_dir=matrix_dir, store_dir=store_dir, pie_root=Path(pie_root), tag=tag, tag_kind=tag_kind,
                            platform=platform_id, log=lambda m_: click.echo(m_, err=True))
            except TasksSkipped as e:
                skipped.append(str(e))
            except Exception as e:  # noqa: BLE001
                failed.append(f"{a}: {type(e).__name__}: {str(e).strip().splitlines()[-1][:200] if str(e).strip() else ''}")
                click.echo(f"FAIL  {failed[-1]}", err=True)
    if skipped:
        click.echo("skipped tasks: " + "; ".join(skipped), err=True)
    if failed:
        click.echo("failed arms: " + "; ".join(failed), err=True)
    if skipped or failed:
        sys.exit(1)


@main.command("parity", help="pie against the reference engine (vLLM, mlx-lm on a Mac) on the same weights and device: teacher-forced KL, top-1 agreement, greedy exact match.")
@click.option("--artifact", "artifacts", multiple=True, required=True)
@click.option("--platform", "platform_id", required=True)
@click.option("--matrix", "matrix_dir", default="matrix")
@click.option("--store", "store_dir", default=None, help="postgresql://... or a directory (default: $PIE_EVALS_DB, else ./store)")
@click.option("--pie-root", type=click.Path(), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--tag", default=None)
@click.option("--tag-kind", type=click.Choice(["release", "manual"]), default=None)
@click.option("--out", "out_dir", type=click.Path(), default="parity-out")
@click.option("--pie-commit", default=None, help="check pie out at this commit and put its cached build in place (a pod: `build` ran first)")
@click.option("--features", default="cuda", show_default=True, help="the build's features, with --pie-commit")
@click.option("--accuracy", "accuracy_tasks", default="", help="comma-separated question sets: score the full model on them (pie and vLLM) instead of parity")
@click.option("--n", type=int, default=100, show_default=True, help="questions per set in an accuracy run")
@click.option("--first-token", is_flag=True, help="word-salad prompts, one token out: KL of the first-token distribution (PARITY_FIRST_TOKEN=1)")
def parity_cmd(artifacts, platform_id, matrix_dir, store_dir, pie_root, tag, tag_kind, out_dir, pie_commit, features, accuracy_tasks, n, first_token):
    from pie_evals.quality.dist_run import run_accuracy, run_parity

    if first_token:
        os.environ["PARITY_FIRST_TOKEN"] = "1"

    if pie_commit:
        _restore_pie(Path(pie_root), pie_commit, features)
    failed = []
    for a in artifacts:
        try:
            if accuracy_tasks:
                run_accuracy(a, platform_id, [t for t in accuracy_tasks.split(",") if t], n, pie_root=Path(pie_root), matrix_dir=matrix_dir, store_dir=store_dir,
                             tag=tag, tag_kind=tag_kind, out_dir=Path(out_dir), log=lambda m_: click.echo(m_, err=True))
            else:
                run_parity(a, platform_id, pie_root=Path(pie_root), matrix_dir=matrix_dir, store_dir=store_dir, tag=tag, tag_kind=tag_kind,
                           out_dir=Path(out_dir), log=lambda m_: click.echo(m_, err=True))
        except Exception as e:  # noqa: BLE001 — one model that fails must not drop the others
            failed.append(f"{a}: {type(e).__name__}: {str(e).strip()[-600:]}")
            click.echo(f"FAIL  {failed[-1]}", err=True)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "failed.json").write_text(json.dumps(failed, indent=1))
    sys.exit(1 if failed else 0)


def _restore_pie(pie_root: Path, pie_commit: str, features: str) -> None:
    from . import build as pb

    mirror = Path(os.environ["PIE_MIRROR"]) if os.environ.get("PIE_MIRROR") else None
    pb.ensure_checkout(pie_root, pie_commit, mirror=mirror)
    pb.ensure(pie_root, pie_commit, [f for f in features.split(",") if f],
              target_dir=Path(os.environ["CARGO_TARGET_DIR"]) if os.environ.get("CARGO_TARGET_DIR") else None,
              python=os.environ.get("PIE_PY", "python3"), log=lambda m_: click.echo(m_, err=True))


@main.command("kernels", help="pie's kernel test suite for the platform's backend (kernels-cuda / kernels-rocm) as one quality row: passed / (passed + failed).")
@click.option("--platform", "platform_id", required=True)
@click.option("--matrix", "matrix_dir", default="matrix")
@click.option("--store", "store_dir", default=None, help="postgresql://... or a directory (default: $PIE_EVALS_DB, else ./store)")
@click.option("--pie-root", type=click.Path(), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--pie-commit", default=None, help="check pie out at this commit first")
@click.option("--tag", default=None)
@click.option("--tag-kind", type=click.Choice(["release", "manual"]), default=None)
@click.option("--out", "out_dir", type=click.Path(), default="kernels-out")
@click.option("--log", "log_file", type=click.Path(exists=True), default=None, help="parse this saved `cargo test` output instead of running the tests")
def kernels_cmd(platform_id, matrix_dir, store_dir, pie_root, pie_commit, tag, tag_kind, out_dir, log_file):
    from pie_evals.quality.kernels import run_kernels

    if pie_commit:
        from . import build as pb

        pb.ensure_checkout(Path(pie_root), pie_commit, mirror=Path(os.environ["PIE_MIRROR"]) if os.environ.get("PIE_MIRROR") else None)
    s = run_kernels(platform_id, pie_root=Path(pie_root), matrix_dir=matrix_dir, store_dir=store_dir, tag=tag, tag_kind=tag_kind,
                    out_dir=Path(out_dir), log_file=Path(log_file) if log_file else None, log=lambda m_: click.echo(m_, err=True))
    sys.exit(1 if s.get("failed") or s.get("error") else 0)


@main.command("rescore", help="Grade saved quality answers again with the current scorers.")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def rescore_cmd(files):
    from pie_evals.quality.run import rescore

    for f in files:
        rescore(Path(f), log=lambda m_: click.echo(m_, err=True))


@main.command("preflight")
def preflight_cmd():
    """Print the hardware fingerprint and machine state checks."""
    from . import preflight as pf
    from . import provenance as prov

    click.echo(json.dumps({"fingerprint": prov.hardware_fingerprint(), "versions": prov.versions(), "state": pf.Preflight().before_job(None)}, indent=1, default=str))


@main.command("miniature")
@click.option("--artifact", required=True, help="artifact id from matrix/models.yaml")
@click.option("--matrix", "matrix_dir", default="matrix")
@click.option("--pie-root", type=click.Path(exists=True), default=os.environ.get("PIE_ROOT", str(DEFAULT_PIE_ROOT)))
@click.option("--hf-cache", type=click.Path(), default=None)
def miniature_cmd(artifact, matrix_dir, pie_root, hf_cache):
    """Build (or find) a miniature checkpoint in the HF cache."""
    from pie_evals.plan.matrix import Matrix

    from .miniature import ensure_miniature

    m = Matrix.load(matrix_dir)
    art = m.artifacts[artifact]
    cache = Path(hf_cache or os.environ.get("HF_HUB_CACHE") or Path.home() / ".cache/huggingface/hub")
    click.echo(str(ensure_miniature(art, Path(pie_root), cache, python=os.environ.get("PIE_PY", "python3"))))


if __name__ == "__main__":
    main()
