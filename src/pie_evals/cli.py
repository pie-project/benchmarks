"""``pie-evals`` — orchestration CLI. Thin, so that a workflow step and a
future coordinator service call the same functions."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import click

from pie_evals.plan.jobs import make_jobs
from pie_evals.plan.matrix import Matrix, summarize
from pie_evals.results import baselines as bl
from pie_evals.results import report as rp
from pie_evals.results.store import Store
from pie_evals.schema import Tier


@click.group()
@click.option("--matrix", "matrix_dir", default="matrix", show_default=True)
@click.option("--store", "store_dir", default=None, help="postgresql://... or a directory (default: $PIE_EVALS_DB, else ./store)")
@click.pass_context
def main(ctx, matrix_dir, store_dir):
    ctx.obj = {"matrix": Matrix.load(matrix_dir), "matrix_dir": matrix_dir, "store": Store(store_dir)}


@main.command("expand")
@click.option("--tier", type=click.Choice([t.value for t in Tier]), default=None)
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def expand(obj, tier, as_json):
    """Expand the matrix; print a summary (or the cells as JSON)."""
    m: Matrix = obj["matrix"]
    cells = m.expand()
    if tier:
        cells = m.cells_for(Tier(tier), cells)
    if as_json:
        click.echo(json.dumps([c.model_dump(mode="json") | {"cell_id": c.cell_id, "cell_key": c.cell_key} for c in cells]))
    else:
        click.echo(json.dumps(summarize(cells), indent=1))
        for t in Tier:
            click.echo(f"{t}: budget {json.dumps(m.budget_report(t, cells))}")
        for p in [p for t in Tier for p in m.check_budget(t, cells)]:
            click.echo(f"BUDGET: {p}", err=True)


@main.command("check")
@click.option("--tier", "only", type=click.Choice([t.value for t in Tier]), default=None, help="check this tier only (a run checks the tier it fans out)")
@click.pass_obj
def check(obj, only):
    """Validate the matrix: budgets per tier. Exit 1 on a violation in an enforced tier."""
    m: Matrix = obj["matrix"]
    cells = m.expand()
    tiers = [t for t in Tier if only in (None, t.value)]
    for t in tiers:
        for p in m.check_budget(t, cells):
            click.echo(("ERROR " if m.suites[t.value].enforce_budget else "warn  ") + p, err=True)
    problems = [p for t in tiers for p in m.check_budget(t, cells, enforced_only=True)]
    click.echo(json.dumps(summarize(cells)))
    sys.exit(1 if problems else 0)


@main.command("suite")
@click.argument("name", default="targeted")
@click.option("--config", "config_path", default="config.json", show_default=True)
def suite_cmd(name, config_path):
    """Print the comma-separated arm ids of a suite in config.json (targeted or full)."""
    from pie_evals.plan.suites import SUITES, load_config, suite_models

    if name not in SUITES:
        raise click.BadParameter(f"{name!r} is not one of {', '.join(SUITES)}", param_hint="NAME")
    click.echo(",".join(suite_models(load_config(config_path), name)))


@main.command("docs-only")
def docs_only_cmd():
    """Read changed file paths from stdin; print true when all of them are docs or CI files."""
    from pie_evals.plan.changes import docs_only

    click.echo("true" if docs_only(sys.stdin.read().splitlines()) else "false")


@main.command("jobs")
@click.option("--tier", type=click.Choice([t.value for t in Tier]), required=True)
@click.option("--pie-commit", default=None)
@click.option("--platform", "platforms", multiple=True)
@click.option("--engine", "engines", multiple=True)
@click.option("--program", "programs", multiple=True, help="restrict to these program ids")
@click.option("--artifact", "artifacts", multiple=True, help="restrict to these artifact ids")
@click.option("--workload", "workloads", multiple=True, help="restrict to these workload ids (the control A/A always stays)")
@click.option("--max-jobs", type=int, default=None, help="cap the number of jobs (shards) written, baseline-bearing first")
@click.option("--max-jobs-per-platform", type=int, default=None, help="cap per platform, so a capped dispatch spans every platform")
@click.option("--out", type=click.Path(), default="jobs")
@click.option("--label", default=None)
@click.option("--skip-unavailable", is_flag=True, help="drop platforms with no RunPod type and no online runner (needs gh + a token with actions:read)")
@click.option("--repo", default=None, help="owner/name for --skip-unavailable (default: $GITHUB_REPOSITORY)")
@click.option("--skip-recorded", is_flag=True, help="drop cells the store already holds at this pie commit / baseline pin (a re-dispatch after lost launches)")
@click.option("--run-label", default=None, help="extra runner label on every pod shard and its pod, so a run's pods take only its own jobs")
@click.pass_obj
def jobs(obj, tier, pie_commit, platforms, engines, programs, artifacts, workloads, max_jobs, max_jobs_per_platform, out, label, skip_unavailable, repo, skip_recorded, run_label):
    """Write one JobSpec JSON per platform shard, plus a GitHub Actions matrix file."""
    from pie_evals.plan.jobs import available_platforms, plan_pods, recorded_cell_keys

    m: Matrix = obj["matrix"]
    st: Store = obj["store"]
    outp = Path(out)
    outp.mkdir(parents=True, exist_ok=True)
    plats = list(platforms) or None
    if skip_unavailable:
        ok, skipped = available_platforms(m, repo or os.environ.get("GITHUB_REPOSITORY", "pie-project/benchmarks"))
        if ok is None:
            plats = plats or [p.id for p in m.platforms.values() if p.runpod_gpu_type]
            click.echo(f"{skipped['*']}; scheduling only RunPod platforms and those asked for: {', '.join(plats) or 'none'}", err=True)
        else:
            plats = [p for p in (plats or list(m.platforms)) if p in ok]
        (outp / "skipped-platforms.json").write_text(json.dumps(skipped, indent=1))
        for pid, why in skipped.items():
            click.echo(f"skip platform {pid}: {why}", err=True)
    from pie_evals.plan.machines import allowed_macs, is_allowed

    allowed = allowed_macs()
    barred = [p.id for p in m.platforms.values() if not is_allowed(p.id, p.os, allowed)]
    if barred:
        for pid in (p for p in (plats or []) if p in barred):
            click.echo(f"skip platform {pid}: not in config.json machines", err=True)
        plats = [p for p in (list(m.platforms) if plats is None else plats) if p not in barred]
    cells = [] if plats == [] else m.expand(platforms=plats, artifacts=artifacts)  # no platform left: expand nothing, not everything
    if programs:
        cells = [c for c in cells if c.program.id in programs]
    if artifacts:
        cells = [c for c in cells if c.artifact.id in artifacts]
    if workloads:
        cells = [c for c in cells if c.workload.id in workloads or str(c.workload.kind) == "control_aa"]
    if skip_recorded and pie_commit:
        done = recorded_cell_keys(st, Tier(tier), pie_commit, {e.id: e.pin for e in m.engines.values() if getattr(e, "pin", None)})
        before = len(cells)
        cells = [c for c in cells if c.cell_key not in done]
        click.echo(f"skip {before - len(cells)} cells already recorded at {pie_commit[:8]}", err=True)
    js = [] if plats == [] else make_jobs(m, Tier(tier), pie_commit=pie_commit, store=st, platforms=plats, engines=list(engines) or None, cells=cells, label=label)
    # a run on its own pods keeps every job: there the cap is how many pods run side by side
    if max_jobs_per_platform is not None and not run_label:
        seen: dict[str, int] = {}
        kept = []
        for j in js:
            if seen.get(j.platform_id, 0) < max_jobs_per_platform:
                kept.append(j)
                seen[j.platform_id] = seen.get(j.platform_id, 0) + 1
        js = kept
    if max_jobs is not None:
        js = js[:max_jobs]
    gh = []
    for j in js:
        (outp / f"{j.job_id}.json").write_text(j.model_dump_json(indent=1))
        plat = m.platforms[j.platform_id]
        # a pod's runner carries the run's label too, so two runs on one GPU type never trade shards
        extra = [run_label] if run_label and plat.runpod_gpu_type else []
        gh.append({"job_id": j.job_id, "platform": j.platform_id, "pod": plat.pod or plat.id, "shard": j.shard, "labels": plat.runner_labels + extra, "os": plat.os, "runpod": bool(plat.runpod_gpu_type), "cells": len(j.cells), "est_minutes": round(j.est_minutes, 1)})
    pods = plan_pods(m, js, pod_per_job=bool(run_label), max_pods=max_jobs_per_platform)
    if run_label:
        for p in pods:
            p["labels"] = sorted(set(p["labels"]) | {run_label})
    (outp / "gh-matrix.json").write_text(json.dumps({"include": gh}))
    (outp / "pods.json").write_text(json.dumps({"include": pods}))
    (outp / "policy.json").write_text(json.dumps({"job_budget_minutes": m.job_budget_minutes, "kill_minutes": m.kill_minutes}))
    click.echo(json.dumps(gh, indent=1))
    for p in pods:
        click.echo(f"pod {p['pod']}: {len(p['jobs'])} jobs, {p['est_minutes']} est min, kill {p['kill_minutes']} min, labels {','.join(p['labels'])}", err=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            # shards of one Mac run one after another (the machine lock), so a shard may first wait out the ones ahead of it
            per_mac = max([sum(1 for j in js if j.platform_id == p) for p in {j.platform_id for j in js}] or [1])
            kill_min = max([j.kill_s // 60 for j in js] or [int(m.kill_minutes)])
            f.write(f"kill_minutes={kill_min}\nbench_timeout_minutes={kill_min * per_mac + 15}\njobs={len(js)}\n")  # workflow expressions cannot add
            f.write(f"pods={json.dumps({'include': pods})}\n")


@main.command("collect")
@click.option("--tier", type=click.Choice([t.value for t in Tier]), required=True)
@click.option("--tag", default=None, help="the release or manual tag this run belongs to")
@click.option("--tag-kind", type=click.Choice(["release", "manual"]), default=None)
@click.argument("node_out", nargs=-1, type=click.Path(exists=True))
@click.pass_obj
def collect(obj, tier, tag, tag_kind, node_out):
    """Import node output directories (records.jsonl) into the store."""
    st: Store = obj["store"]
    problems = []
    for d in node_out:
        d = Path(d)
        run_id = (d / "run_id.txt").read_text().strip() if (d / "run_id.txt").exists() else d.name
        try:
            p = st.import_node_output(d, tier=Tier(tier), run_id=run_id, tag=tag or None, tag_kind=tag_kind or None)
        except Exception as e:
            problems.append(f"{d}: {e}")
            click.echo(f"{d}: IMPORT FAILED: {e}", err=True)
            continue
        click.echo(f"{d} -> {p if p else 'no records (node crashed before its first record)'}")
    if problems:
        sys.exit(1)


@main.command("store-status")
@click.pass_obj
def store_status(obj):
    """Count what the store holds: records, runs, quality summaries."""
    st = obj["store"]
    t = st.table()
    runs = len(set(t.column("run_id").to_pylist())) if t.num_rows else 0
    click.echo(json.dumps({"store": st.describe(), "records": t.num_rows, "runs": runs, "quality": len(st.quality())}))


@main.command("import-phone")
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--spool", type=click.Path(file_okay=False), default=None, help="also store every pending file of this phone inbox (the ingest's --spool)")
@click.option("--tag", default=None, help="tag for rows that name none (default: the newest release tag)")
@click.option("--dry-run", is_flag=True, help="check the rows, store nothing")
@click.pass_obj
def import_phone(obj, files, spool, tag, dry_run):
    """Store the benchmark app's records.jsonl (a shared file, or the "Copy for workflow" text) as phone rows."""
    from pie_evals.results import phone
    from pie_evals.results.phone_ingest import import_spool

    m: Matrix = obj["matrix"]
    failed = 0
    for f in files:
        good, bad, warnings = phone.validate(phone.read_file(Path(f)), m, phone.model_ids())
        for w in warnings:
            click.echo(f"{f}: {w}", err=True)
        for b in bad:
            click.echo(f"{f}: line {b['line']}: {b['error']}", err=True)
        failed += bool(bad)
        if not good:
            failed += 1
            continue
        if dry_run:
            click.echo(f"{f}: {len(good)} rows ok ({', '.join(sorted({f'{r.engine}/{r.artifact}/{r.workload}={rec.status}' for r, rec in good}))})")
            continue
        for msg in phone.store_rows(good, obj["store"], tag=tag):
            click.echo(f"{f}: {msg}")
        stored_tag = good[0][0].tag or tag or phone.latest_release_tag(obj["store"])
        click.echo(f"{f}: read back under {stored_tag}: {phone.count_rows(obj['store'], stored_tag, sorted({r.run_id for r, _ in good}))}")
    if spool and not dry_run:
        ok, bad_files = import_spool(Path(spool).expanduser(), obj["store"], m, tag=tag, log=click.echo)
        click.echo(f"inbox {spool}: {ok} stored, {bad_files} failed")
        failed += bad_files
    if failed:
        sys.exit(1)


@main.command("phone-ingest")
@click.option("--listen", required=True, help="HOST:PORT; only a loopback or Tailscale (100.64.0.0/10) address")
@click.option("--token-file", type=click.Path(dir_okay=False), required=True, help="file holding the bearer token (mode 600)")
@click.option("--init-token", is_flag=True, help="make the token file when it does not exist")
@click.option("--spool", type=click.Path(file_okay=False), default="~/.pie-evals/phone-inbox", show_default=True)
@click.option("--direct", is_flag=True, help="store into $PIE_EVALS_DB at once instead of leaving rows in the inbox")
@click.pass_obj
def phone_ingest(obj, listen, token_file, init_token, spool, direct):
    """Serve POST /v1/results for the phone benchmark app, on the tailnet only."""
    from pie_evals.results.phone_ingest import read_token, serve

    token = read_token(Path(token_file).expanduser(), create=init_token)
    serve(listen, token, Path(spool).expanduser(), Path(obj["matrix_dir"]).resolve(), obj["store"] if direct else None)


@main.command("drop-tag")
@click.argument("tag")
@click.pass_obj
def drop_tag(obj, tag):
    """Delete every record of a manual tag (a release tag is refused)."""
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise click.UsageError(f"{tag} is a release tag; releases are never dropped")
    click.echo(f"{tag}: {obj['store'].drop_tag(tag)} records deleted")


@main.command("move-tag")
@click.argument("src")
@click.argument("dst")
@click.pass_obj
def move_tag(obj, src, dst):
    """Move SRC's good rows into DST for the cells DST has no good row for."""
    click.echo(f"{src} -> {dst}: {obj['store'].move_tag(src, dst)} records moved")


@main.command("drop-engine")
@click.argument("engine")
@click.pass_obj
def drop_engine(obj, engine):
    """Delete every result and quality score of an engine (pie is refused)."""
    if engine == "pie":
        raise click.UsageError("pie's own results are never dropped")
    records, scores = obj["store"].drop_engine(engine)
    click.echo(f"{engine}: {records} records and {scores} quality scores deleted")


@main.command("drop-workload")
@click.argument("workload")
@click.pass_obj
def drop_workload(obj, workload):
    """Delete every record of a workload."""
    click.echo(f"{workload}: {obj['store'].drop_workload(workload)} records deleted")


@main.command("drop-quality")
@click.argument("artifact")
@click.argument("task")
@click.argument("tag")
@click.pass_obj
def drop_quality(obj, artifact, task, tag):
    """Delete the quality scores of one artifact, task and tag (a failed run's row)."""
    click.echo(f"{artifact} {task} {tag}: {obj['store'].drop_quality(artifact, task, tag)} quality scores deleted")


@main.command("import-store")
@click.argument("src", type=click.Path(exists=True))
@click.pass_obj
def import_store(obj, src):
    """Copy a store directory (records/**.parquet, quality/*.json) into the store. Safe to repeat."""
    import pyarrow.parquet as pq

    from pie_evals.results.store import DirStore
    from pie_evals.schema.record import ARROW_SCHEMA

    st, d = obj["store"], DirStore(src)
    files = d.files()
    for i, f in enumerate(files, 1):
        st._write_table(pq.read_table(f, schema=ARROW_SCHEMA), tier=Tier(f.parts[-3]), run_id=f.stem, when=None)
        if i % 100 == 0 or i == len(files):
            click.echo(f"{i}/{len(files)} runs", err=True)
    # dotfiles are not summaries: a Mac's rsync leaves an AppleDouble "._<name>.json" beside each file it copies
    summaries = [f for f in sorted((d.root / "quality").glob("*.json")) if not f.name.startswith(".")]
    for f in summaries:
        q = json.loads(f.read_text())
        st.write_quality(q, tag=q.get("tag"), tag_kind=q.get("tag_kind"))
    click.echo(f"{len(files)} runs, {len(summaries)} quality summaries")


@main.command("report")
@click.option("--tier", type=click.Choice([t.value for t in Tier]), required=True)
@click.option("--out", type=click.Path(), default="reports")
@click.pass_obj
def report(obj, tier, out):
    """Render coverage, regressions, baseline ratios."""
    m: Matrix = obj["matrix"]
    st: Store = obj["store"]
    t = Tier(tier)
    outp = Path(out) / t.value
    outp.mkdir(parents=True, exist_ok=True)
    views = rp.coverage(m, st, t)
    (outp / "coverage.md").write_text(rp.coverage_markdown(views, t))
    regs = rp.regressions(m, st, t)
    (outp / "regressions.md").write_text(rp.regressions_markdown(regs))
    (outp / "regressions.json").write_text(rp.to_json(regs))
    ratios = rp.baseline_ratios(m, st, t)
    (outp / "baselines.md").write_text(rp.baseline_markdown(ratios))
    (outp / "baselines.json").write_text(rp.to_json(ratios))
    n_reg = sum(1 for r in regs if r["kind"] == "regression")
    trails = sum(1 for r in ratios if not r["pie_leads"])
    click.echo(json.dumps({"cells": len(views), "regressions": n_reg, "pie_trails": trails, "escalate_families": rp.escalation_families(m, st)}))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"regressions={n_reg}\npie_trails={trails}\n")


@main.command("checks")
@click.option("--tier", type=click.Choice([t.value for t in Tier]), required=True)
@click.pass_obj
def checks(obj, tier):
    """After a collect: each cell against its last 7 days, and each engine's output length against pie's.
    Writes both tables to the job summary and a warning per finding; only a prompt-length mismatch fails (exit 3)."""
    m: Matrix = obj["matrix"]
    st: Store = obj["store"]
    t = Tier(tier)
    regs = rp.regressions(m, st, t)
    lengths = rp.output_length_mismatches(m, st, t)
    text = rp.regressions_markdown(regs) + "\n" + rp.output_length_markdown(lengths)
    click.echo(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(text)
    for r in regs:
        if r["kind"] == "regression":
            click.echo(f"::warning::regression {r['engine']} {r['platform']} {r['artifact']} {r['workload']}: {r['delta_rel']*100:+.1f}% against the last 7 days")
    for r in lengths:
        click.echo(f"::warning::output length {r['engine']} {r['platform']} {r['model']} {r['workload']}: {r['gap_rel']*100:+.0f}% tokens per request against pie")
    prompts = rp.prompt_length_mismatches(m, st, t)
    # only a pair measured in the last two days fails the collect: an old pair no run measures again (a retired
    # machine's rows) stays a warning, so it cannot turn every later collect red and hide a real failure
    from datetime import datetime, timedelta, timezone
    recent = datetime.now(timezone.utc) - timedelta(days=2)
    fresh = []
    for r in prompts:
        at = r["newest"] if r["newest"].tzinfo else r["newest"].replace(tzinfo=timezone.utc)
        level = "error" if at >= recent else "warning"
        click.echo(f"::{level}::prompt length {r['platform']} {r['model']} {r['workload']}: engines prefill different prompts, mean tokens per request {r['per_request']}")
        if level == "error":
            fresh.append(r)
    if fresh:
        raise SystemExit(3)


@main.command("pins")
@click.argument("action", type=click.Choice(["latest", "set"]))
@click.argument("assignments", required=False, default="")
@click.pass_obj
def pins(obj, action, assignments):
    """latest: print id=version for each engine's newest release. set id=version,...: write those pins into matrix/engines.yaml."""
    import re

    from pie_evals.results import baselines as bl

    m: Matrix = obj["matrix"]
    if action == "latest":
        out = []
        for e in m.engines.values():
            # an engine with no pin (the phone engines) has nothing to set: `pins set` would refuse its line
            if not e.release_source or not e.pin:
                continue
            kind, ident = e.release_source.split(":", 1)
            if kind == "pypi":
                v = bl._pypi_latest(ident)
            elif e.id == "llamacpp":
                v = bl._github_newest(ident)  # its builds are tagged bNNNN and published as pre-releases
            else:
                v = bl._github_latest(ident)
            if not v:
                # one engine whose source publishes no release (mlc-llm tags only) keeps its pinned version: it must
                # not stop every run's start (pie-eval 42172766118 failed on it)
                click.echo(f"no release found for {e.id} at {e.release_source}; keeping its pin", err=True)
                continue
            out.append(f"{e.id}={v.lstrip('v')}")
        click.echo(",".join(out))
        return
    path = Path(obj["matrix_dir"]) / "engines.yaml"
    text = path.read_text()
    for item in filter(None, assignments.split(",")):
        eid, version = item.split("=", 1)
        pat = re.compile(r'(  - id: ' + re.escape(eid) + r'\n(?:    [^\n]*\n)*?    pin: )"[^"]*"')
        text, n = pat.subn(lambda mm, v=version: f'{mm.group(1)}"{v}"', text, count=1)
        if n != 1:
            raise click.ClickException(f"no pin line for {eid}")
    path.write_text(text)
    click.echo(f"pinned {assignments}")


@main.command("watch-baselines")
@click.option("--lock", type=click.Path(), default="matrix/baselines.lock.json")
@click.pass_obj
def watch_baselines(obj, lock):
    """Check PyPI/GitHub for newer baseline releases than the pins."""
    checks = bl.check(obj["matrix"])
    bl.write_lock(checks, Path(lock))
    for c in checks:
        click.echo(f"{c.engine}: pinned {c.pinned} latest {c.latest}{'  <-- NEWER' if c.newer else ''}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("newer=" + ",".join(c.engine for c in checks if c.newer) + "\n")


@main.command("launch-pod")
@click.option("--platform", required=True, help="platform id, or a comma-separated fallback list tried in order (build pods: any GPU will do)")
@click.option("--repo", required=True, help="owner/name the runner registers with")
@click.option("--runner-pat", envvar="GH_RUNNER_PAT", default=None, help="PAT with Administration: read/write on --repo; minted into a registration token inside the pod")
@click.option("--runner-token", envvar="GH_RUNNER_TOKEN", default=None, help="pre-minted registration token (preferred: 1 h, registration-only); one of --runner-pat/--runner-token is required")
@click.option("--image", default=None, help="default: pieproject/runpod-ci-runner:latest")
@click.option("--image-version", default="latest")
@click.option("--network-volume-id", envvar="RUNPOD_NETWORK_VOLUME_ID", default=None)
@click.option("--kill-minutes", type=int, default=None, help="pod self-destruct; default = job budget × kill_factor")
@click.option("--cuda", "cuda_versions", multiple=True, default=[], show_default=True, help="allowed host CUDA versions; default: any host, and the pod drops itself below CUDA 13.0 (RunPod's v1 pod API takes nothing above 13.0 and the fleet moved to 13.2 hosts: a 13.0 pin found no instance anywhere, weekly 39399397655)")
@click.option("--debug", is_flag=True, help="serve the start log on the pod's :8080 proxy and hold a failed pod 10 min")
@click.option("--exec", "exec_script", default=None, help="run this bash script on the pod (same env as a job) instead of a runner, then terminate; volume maintenance")
@click.option("--wait-runner", type=int, default=0, help="seconds to wait for the pod's runner to register (needs GH_RUNNER_PAT); a pod that never registers is terminated and the next platform tried")
@click.option("--labels", default=None, help="comma-separated runner labels (default: the platform's); a pod hosting several platforms carries all of theirs")
@click.option("--idle-minutes", type=int, default=20, show_default=True, help="the pod terminates itself after this long without a job")
@click.option("--reuse", is_flag=True, help="if a live pod already carries every label, queue on it instead of renting another (needs GH_RUNNER_PAT)")
@click.option("--name-prefix", default="pie-evals", show_default=True, help="pod name prefix (reap only ends pie-evals-* pods)")
@click.pass_obj
def launch_pod(obj, platform, repo, runner_pat, runner_token, image, image_version, network_volume_id, kill_minutes, cuda_versions, debug, exec_script, wait_runner, labels, idle_minutes, reuse, name_prefix):
    from pie_evals.pods import runpod

    m: Matrix = obj["matrix"]
    rp = m.runpod
    if not (runner_pat or runner_token or exec_script):
        raise click.UsageError("set GH_RUNNER_PAT or GH_RUNNER_TOKEN (the workflow saw GH_RUNNER_PAT empty: check the org secret's name and its repository access list)")
    h = None
    plat = None
    errors = []
    want = [x.strip() for x in labels.split(",") if x.strip()] if labels else None
    lab = None
    runners: list = []
    running: set | None = None  # None: no reuse
    if reuse and runner_pat and not exec_script:
        try:
            runners = runpod.list_runners(repo, runner_pat)
        except Exception as e:
            runners = []
            click.echo(f"runner list unavailable ({str(e)[:80]}); launching", err=True)
        try:
            running = {p["id"] for p in runpod.list_pods() if p.get("desiredStatus") == "RUNNING"}
        except Exception as e:
            running = set()  # unknown: rent rather than queue on a pod that may be gone
            click.echo(f"pod list unavailable ({str(e)[:80]}); not reusing", err=True)
    def reused(pid: str) -> bool:
        if running is None:
            return False
        p = m.platforms[pid]
        lab = [x for x in want if x not in m.platforms or m.platforms[x].count <= p.count] if want else p.runner_labels
        found = runpod.reusable_pod(lab, runners, running)
        if not found:
            return False
        pod_id, have = found
        click.echo(f"reusing pod {pod_id} ({','.join(have)}): its runner carries every label {pid} needs", err=True)
        click.echo(pod_id)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"pod_id={pod_id}\nplatform={pid}\nlabels={','.join(lab)}\nreused=true\n")
        return True

    for pid in [x.strip() for x in platform.split(",") if x.strip()]:
        # the planned pod is rented before a fallback's live pod is reused: an x1 pod up
        # must not swallow a run whose x2 shards then never run (pro6000, nightly 36294204789)
        if reused(pid):
            return
        plat = m.platforms[pid]
        # a fallback pod seats only the hosted platforms that fit on it
        lab = [x for x in want if x not in m.platforms or m.platforms[x].count <= plat.count] if want else None
        gone = False
        # a platform with its own image (ROCm: the AMD SGLang image at the run's SGLang pin) takes it over
        # the runner image; a 15-25 GB image takes far longer to pull than the runner's 2.5 GB
        pod_image, wait = image or runpod.DEFAULT_IMAGE, wait_runner
        if plat.runpod_image:
            pins = {e.id: (e.pin_for(plat.backend) or "") for e in m.engines.values()}
            pod_image, wait = plat.runpod_image.format(**pins), max(wait_runner, 2700) if wait_runner else 0
            click.echo(f"{pid}: image {pod_image}", err=True)
        for _attempt in range(3):  # a pod that ends itself (host below CUDA 13.0) or never registers (pull stuck: pro6000-x4, weekly 39547027079): rent another
            try:
                h = runpod.create_pod(plat, repo=repo, runner_pat=runner_pat, runner_token=runner_token, kill_minutes=kill_minutes or m.kill_minutes,
                                      image=pod_image, image_version=image_version, network_volume_id=network_volume_id,
                                      volumes=rp.get("volumes") or None, preferred_data_centers=rp.get("preferred_data_centers"),
                                      container_disk_gb=max(int(rp.get("container_disk_gb", 40)), plat.container_disk_gb or 0), cloud_type=str(rp.get("cloud_type", "SECURE")),
                                      allowed_cuda_versions=list(cuda_versions) or None, debug=debug, exec_script=exec_script,
                                      community_fallback=bool(rp.get("community_fallback", True)), log=lambda m_: click.echo(m_, err=True),
                                      labels=lab, idle_minutes=idle_minutes, name_prefix=name_prefix)
            except RuntimeError as e:
                errors.append(f"{pid}: {str(e)[:120]}")
                click.echo(f"no pod for {pid}: {str(e)[:600]}", err=True)
                h = None
                break
            click.echo(f"launched on {pid}", err=True)
            if not (wait_runner and runner_pat and not exec_script):
                break
            status = runpod.wait_for_runner(h.id, repo, runner_pat, wait, log=lambda m_: click.echo(m_, err=True))
            if status is True:
                break
            gone = status == "gone"
            click.echo(f"pod {h.id} on {pid} {'ended before registering a runner' if gone else f'never registered a runner within {wait}s'}; terminating it", err=True)
            try:
                runpod.terminate_pod(h.id)
            except RuntimeError as e:
                click.echo(f"terminate {h.id}: {str(e)[:120]}", err=True)
            errors.append(f"{pid}: runner not registered ({'pod ended' if gone else f'{wait}s'})")
            h = None  # a pod whose image pull never finishes (runtime never up) is a host problem: rent another
        if h is not None:
            break
    if h is None or plat is None:
        raise click.ClickException("no instance on any platform: " + "; ".join(errors))
    click.echo(h.id)
    if debug:
        click.echo(f"start log: https://{h.id}-8080.proxy.runpod.net/start.log", err=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"pod_id={h.id}\nplatform={plat.id}\nlabels={','.join(lab or plat.runner_labels)}\n")


@main.command("release-pods")
@click.argument("pod_ids", nargs=-1)
@click.option("--repo", required=True)
@click.option("--runner-pat", envvar="GH_RUNNER_PAT", default=None)
def release_pods(pod_ids, repo, runner_pat):
    """Terminate the given pods at the end of a run unless their runner is busy
    (another run's job on a shared pod): a finished run leaves no pod billing
    until the 20-minute idle watchdog."""
    from pie_evals.pods import runpod

    busy: set[str] = set()
    if runner_pat:
        try:
            busy = runpod.busy_pods(runpod.list_runners(repo, runner_pat))
        except Exception as e:  # noqa: BLE001 — unknown: leave every pod to its idle watchdog
            click.echo(f"runner list unavailable ({str(e)[:80]}); leaving pods to their idle watchdog", err=True)
            return
    for pid in {p.strip() for p in pod_ids if p.strip()}:
        if pid in busy:
            click.echo(f"{pid}: runner busy with another job; left to its idle watchdog")
            continue
        try:
            runpod.terminate_pod(pid)
            click.echo(f"{pid}: terminated")
        except RuntimeError as e:
            click.echo(f"{pid}: {str(e)[:120]}")


@main.command("runpod-gpus")
def runpod_gpus():
    """List RunPod GPU type ids (what platforms.yaml runpod_gpu_type must use) with price/stock."""
    from pie_evals.pods import runpod

    for g in sorted(runpod.gpu_types(), key=lambda g: str(g.get("id"))):
        click.echo(f"{g.get('id', ''):55s} {g.get('memoryInGb') or '':>4} GB  {g.get('displayName', '')}")


@main.command("runpod-volume")
@click.argument("action", type=click.Choice(["list", "create"]))
@click.argument("data_center", required=False)
@click.argument("size_gb", type=int, required=False)
def runpod_volume(action, data_center, size_gb):
    """List network volumes, or create one: runpod-volume create EUR-IS-1 200 (then add it to matrix/runpod.yaml)."""
    from pie_evals.pods import runpod

    if action == "list":
        for v in runpod._req("GET", "/networkvolumes"):
            click.echo(f"{v['id']}  {v.get('dataCenterId')}  {v.get('size')} GB  {v.get('name')}")
    else:
        v = runpod.create_network_volume(f"pie-evals-{data_center.lower()}", size_gb, data_center)
        click.echo(f"{v['id']}  {v.get('dataCenterId')}  {v.get('size')} GB  — add to matrix/runpod.yaml volumes")


@main.command("validate-platforms")
@click.option("--platforms", default="", help="comma-separated platform ids to check (default: every platform)")
@click.pass_obj
def validate_platforms(obj, platforms):
    """Check runpod_gpu_type in platforms.yaml against the live GPU type list. Exit 1 on unknown ids.

    A run checks only its own platforms, so a type RunPod drops does not stop runs on the others."""
    from pie_evals.pods import runpod

    chosen = {p for p in platforms.split(",") if p}
    specs = {k: v for k, v in obj["matrix"].platforms.items() if not chosen or k in chosen}
    problems = runpod.validate_platforms(specs)
    for p in problems:
        click.echo(p, err=True)
    click.echo("ok" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


@main.command("terminate-pod")
@click.argument("pod_id")
def terminate_pod(pod_id):
    from pie_evals.pods import runpod

    runpod.terminate_pod(pod_id)
    click.echo(f"terminated {pod_id}")


@main.command("reap-pods")
@click.option("--max-age-hours", type=float, default=2.0, help="a pod this old whose runner is not busy is an orphan")
@click.option("--hard-max-age-hours", type=float, default=30.0, help="even a busy pod ends here: a configuration's whole queue fits well inside")
@click.option("--repo", default=None, help="owner/name whose runners say which pods are busy (needs GH_TOKEN); default: $GITHUB_REPOSITORY")
@click.option("--dry-run", is_flag=True)
def reap_pods(max_age_hours, hard_max_age_hours, repo, dry_run):
    from pie_evals.pods import runpod

    keep: set[str] = set()
    try:
        keep = runpod.busy_pods(runpod.list_runners(repo or os.environ.get("GITHUB_REPOSITORY", "pie-project/benchmarks")))
    except Exception as e:  # no token: age alone decides, as before
        click.echo(f"runner list unavailable ({str(e)[:80]}); busy pods are not spared", err=True)
    click.echo(json.dumps(runpod.reap(int(max_age_hours * 3600), dry_run=dry_run, keep=keep, hard_max_age_s=int(hard_max_age_hours * 3600))))


if __name__ == "__main__":
    main()
