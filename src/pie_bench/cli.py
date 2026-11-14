from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from pie_bench import __version__, local, submit
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.plan.suites import SUITES

PATHS = [Path.home() / ".local/bin", Path.home() / ".cargo/bin", Path("/opt/homebrew/bin")]


def _split(values: tuple[str, ...]) -> list[str] | None:
    out = [v.strip() for s in values for v in s.split(",") if v.strip()]
    return out or None


def _say(msg: str) -> None:
    click.echo(msg, err=True)


def _env() -> None:
    os.environ["PATH"] = os.pathsep.join([*(str(p) for p in PATHS if p.is_dir()), os.environ.get("PATH", "")])


def _mask_gpus(count: int) -> None:
    if os.environ.get("CUDA_VISIBLE_DEVICES") or not shutil.which("nvidia-smi"):
        return
    visible = sum(1 for ln in subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.splitlines() if ln.startswith("GPU "))
    if visible > count:
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(str(i) for i in range(count))


def _upload(out: Path) -> None:
    path = out / submit.SUBMISSION
    _say(f"uploading {path} to {submit.API}")
    try:
        res = submit.upload(path)
    except submit.ApiError as e:
        _say(f"upload failed: {e}\nyour results are safe in {out}; retry with: pie-bench upload {out}")
        sys.exit(1)
    _say(f"uploaded: run {res.get('run_id')}, {res.get('results', 0)} results")


@click.group()
@click.version_option(__version__, prog_name="pie-bench")
def main():
    _env()


@main.command(help="Measure pie against the other engines on this machine, then upload the results.")
@click.option("--models", multiple=True, help="model names to measure, comma-separated (default: the release suite)")
@click.option("--engines", multiple=True, help="engines to measure, comma-separated (default: every engine on this machine)")
@click.option("--workloads", multiple=True, help="workload ids, comma-separated (default: the release workloads)")
@click.option("--suite", type=click.Choice(SUITES), default="targeted", show_default=True)
@click.option("--machine", "machine_id", default=None, help="this machine's id when it is not detected")
@click.option("--pie", "pie_ref", default="latest", show_default=True, help="pie release tag, branch or commit")
@click.option("--pie-root", type=click.Path(path_type=Path), default=None, help="an existing pie checkout to build and use")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="folder for the results (default: ~/.pie-bench/runs/<time>)")
@click.option("--upload/--no-upload", default=True, show_default=True)
@click.option("-y", "--yes", is_flag=True, help="start without asking")
def run(models, engines, workloads, suite, machine_id, pie_ref, pie_root, out, upload, yes):
    m = Matrix.load(MATRIX)
    machine = local.detect(m, machine_id)
    missing = local.prerequisites(machine)
    if missing:
        _say("install these first:\n  " + "\n  ".join(missing))
        sys.exit(1)
    commit, tag = local.resolve_pie(pie_ref)
    job = local.plan(m, machine, pie_commit=commit, models=_split(models), engines=_split(engines), workloads=_split(workloads), suite=suite)
    if job is None:
        _say(f"nothing to measure on {machine.platform.id}; try `pie-bench plan` with other --models")
        sys.exit(1)
    groups = job.cells_by_process()
    _say(f"machine   {machine.platform.id} ({machine.platform.accelerator}, {machine.platform.memory_gib:g} GiB){'' if machine.known else ', new to the catalog'}")
    _say(f"pie       {tag} ({commit[:9]})")
    _say(f"measure   {len(job.cells)} cells, {len({c.artifact.id for c in job.cells})} models, engines {', '.join(sorted({str(c.engine) for c in job.cells}))}")
    _say(f"estimate  about {max(1, round(job.est_minutes + 3 * len(groups)))} minutes, plus model downloads on a first run")
    if not yes and not click.confirm("start?", default=True, err=True):
        return
    out = (out or local.HOME / "runs" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "job.json").write_text(job.model_dump_json(indent=1))
    os.environ.update(local.setup_engines(m, job, log=_say))
    _mask_gpus(machine.platform.count)
    from pie_bench.node.machine import MachineBusy, machine_lock
    from pie_bench.node.runner import NodeRunner

    try:
        with machine_lock(job.job_id, max_wait_s=3600, log=_say):
            runner = NodeRunner(job, pie_root=(pie_root or local.HOME / "pie").resolve(), out_dir=out, download=True)
            recs = runner.run()
    except MachineBusy as e:
        _say(str(e))
        sys.exit(3)
    by: dict[str, int] = {}
    for r in recs:
        by[str(r.status)] = by.get(str(r.status), 0) + 1
    submit.pack(out, {"run_id": runner.run_id, "tier": str(job.tier), "tag": tag, "tag_kind": "release" if not tag.startswith("manual-") else "manual",
                      "platform": machine.platform.model_dump(mode="json"), "pie_commit": commit})
    _say(f"done: {len(recs)} results ({', '.join(f'{v} {k}' for k, v in sorted(by.items()))}) in {out}")
    if upload:
        _upload(out)


@main.command(help="Show what `pie-bench run` would measure here, without running anything.")
@click.option("--models", multiple=True)
@click.option("--engines", multiple=True)
@click.option("--workloads", multiple=True)
@click.option("--suite", type=click.Choice(SUITES), default="targeted", show_default=True)
@click.option("--machine", "machine_id", default=None)
@click.option("--json", "as_json", is_flag=True)
def plan(models, engines, workloads, suite, machine_id, as_json):
    m = Matrix.load(MATRIX)
    machine = local.detect(m, machine_id)
    job = local.plan(m, machine, pie_commit="0" * 40, models=_split(models), engines=_split(engines), workloads=_split(workloads), suite=suite)
    cells = job.cells if job else []
    if as_json:
        click.echo(json.dumps([c.cell_key for c in cells], indent=1))
        return
    click.echo(f"{machine.platform.id}: {len(cells)} cells")
    for (engine, artifact, _), group in (job.cells_by_process().items() if job else []):
        click.echo(f"  {engine:<10} {artifact:<60} {', '.join(sorted({c.workload.id for c in group}))}")


@main.command(help="Every machine id the catalog knows.")
def machines():
    m = Matrix.load(MATRIX)
    for p in sorted(m.platforms.values(), key=lambda p: (p.os, p.id)):
        click.echo(f"{p.id:<22} {p.os:<6} {p.accelerator} x{p.count}, {p.memory_gib:g} GiB")


@main.command(help="Get an upload token for this machine (once).")
@click.option("--name", default=None, help="a name for this machine's token (default: its host name)")
def login(name):
    try:
        res = submit.login(name)
    except submit.ApiError as e:
        _say(f"login failed: {e}")
        sys.exit(1)
    _say(f"token saved to {submit.TOKEN_FILE} (quota {res.get('quota')} uploads)")


@main.command(help="Upload a finished run's folder.")
@click.argument("out", type=click.Path(exists=True, file_okay=False, path_type=Path))
def upload(out):
    if not (out / submit.SUBMISSION).exists():
        job = json.loads((out / "job.json").read_text())
        run_id = (out / "run_id.txt").read_text().strip() if (out / "run_id.txt").exists() else job["job_id"]
        submit.pack(out, {"run_id": run_id, "tier": job["tier"], "tag": None, "tag_kind": "manual",
                          "platform": job["cells"][0]["platform"] if job["cells"] else None, "pie_commit": job.get("pie_commit")})
    _upload(out.resolve())


@main.command("import-phone", help="Turn the phone app's shared records.jsonl into submissions for `pie-bench upload`.")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--tag", required=True, help="the release tag the rows join, e.g. main-f03640150 (a test-* tag for a test)")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="folder for the submissions (default: ~/.pie-bench/phone)")
@click.option("--dry-run", is_flag=True, help="check the rows and print a summary, write nothing")
def import_phone(file, tag, out, dry_run):
    import re

    from pie_bench import phone

    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", tag):
        _say(f"bad tag {tag!r}")
        sys.exit(2)
    m = Matrix.load(MATRIX)
    good, bad, warnings = phone.validate(phone.read_file(file), m, phone.model_ids(m), tag=tag)
    for w in warnings:
        _say(f"warning: {w}")
    for b in bad:
        _say(f"line {b['line']} refused: {b['error']}")
    for row, rec in good:
        p = rec.perf
        what = f"decode {p.decode_tok_s or 0:.1f} tok/s, prefill {p.prefill_tok_s or 0:.0f} tok/s" if p else (rec.error_message or rec.invalid_reason or "")
        _say(f"  {rec.cell.platform.id:<14} {row.engine:<9} {row.artifact:<26} {row.workload:<12} {rec.status!s:<20} {what}")
    _say(f"{len(good)} rows ok, {len(bad)} refused")
    if dry_run or not good:
        sys.exit(1 if bad or not good else 0)
    for d in phone.pack(good, (out or local.HOME / "phone").resolve(), tag=tag):
        _say(f"wrote {d / submit.SUBMISSION}; send it with: pie-bench upload {d}")


@main.command(help="Score model accuracy on question sets, then upload the scores.")
@click.option("--models", multiple=True, required=True, help="model artifact ids, comma-separated")
@click.option("--task", "tasks", multiple=True, default=("gsm8k", "ifeval", "mmlu", "arc", "math500"), show_default=True)
@click.option("--n", type=int, default=100, show_default=True)
@click.option("--pie-root", type=click.Path(path_type=Path), default=None)
@click.option("--out", type=click.Path(path_type=Path), default=None)
@click.option("--upload/--no-upload", default=True, show_default=True)
def quality(models, tasks, n, pie_root, out, upload):
    from pie_bench.quality.run import run_quality

    m = Matrix.load(MATRIX)
    machine = local.detect(m)
    out = (out or local.HOME / "runs" / f"quality-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    failed = []
    for a in _split(models) or []:
        try:
            run_quality(a, _split(tasks), n, store_dir=str(out), pie_root=(pie_root or local.HOME / "pie").resolve(),
                        platform=machine.platform.id, log=_say)
        except Exception as e:
            failed.append(a)
            _say(f"{a}: {type(e).__name__}: {e}")
    submit.pack(out, {"run_id": out.name, "tier": "quality", "tag": None, "tag_kind": "manual", "platform": machine.platform.model_dump(mode="json"), "pie_commit": None})
    if upload:
        _upload(out)
    sys.exit(1 if failed else 0)


@main.command(help="Check this machine is ready to run pie-bench.")
def doctor():
    m = Matrix.load(MATRIX)
    machine = local.detect(m)
    click.echo(f"machine  {machine.platform.id} ({machine.platform.accelerator}){'' if machine.known else ', new to the catalog'}")
    missing = local.prerequisites(machine)
    click.echo("tools    " + ("ready" if not missing else "missing: " + "; ".join(missing)))
    click.echo(f"token    {'saved' if submit.saved_token() else 'not yet (made on the first upload)'}")
    click.echo(f"api      {submit.API}")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
