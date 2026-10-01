from __future__ import annotations

import base64
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import yaml

from pie_evals.plan.matrix import Matrix
from pie_evals.results import flops
from pie_evals.results.store import Store
from pie_evals.schema import CellStatus, Tier

DEFAULT_MODEL = "gemma-4-26b-a4b-ollama"
DEFAULT_BASELINE = "Ollama"
#: the engine that serves an arm, by the format of its copy of the weights
ARM_ENGINE = {"ollama": "ollama", "gguf": "llamacpp", "mlx": "mlxlm", "splash": "splash"}
#: the order the "compare against" choices are listed in
BASELINE_ORDER = ["Ollama", "Ollama MLX", "llama.cpp", "mlx-lm", "Splash"]
HERE = Path(__file__).resolve().parent
#: the maker's logo shown beside a model's name, by the start of its family
FAMILY_ICON = {"qwen": "qwen.png", "gemma": "gemma.svg", "llama": "meta.svg", "muse": "meta.svg"}
MIME = {".png": "image/png", ".svg": "image/svg+xml"}


def icon_for(family: str) -> str | None:
    return next((name for prefix, name in FAMILY_ICON.items() if family.startswith(prefix)), None)


def icons() -> dict[str, str]:
    """Each logo file as a data URI, so the page stays one file."""
    out = {}
    for name in sorted(set(FAMILY_ICON.values())):
        path = HERE / "icons" / name
        out[name] = f"data:{MIME[path.suffix]};base64," + base64.b64encode(path.read_bytes()).decode()
    return out

PAGE = (HERE / "page.html").read_text()


def _gh(path: str) -> dict | list | None:
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def history(pie_repo: str) -> list[dict]:
    try:
        out = subprocess.run(["gh", "api", "--paginate", "--slurp", f"repos/{pie_repo}/commits?sha=main&per_page=100"],
                             capture_output=True, text=True, check=True).stdout
        pages = json.loads(out)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return []
    return [{"sha": c["sha"], "message": (c["commit"]["message"] or "").splitlines()[0][:120] if c["commit"]["message"] else "",
             "author": (c.get("author") or {}).get("login") or c["commit"]["author"]["name"],
             "date": c["commit"]["committer"]["date"]} for page in pages for c in page]


def runners(repo: str) -> list[dict] | None:
    got = _gh(f"repos/{repo}/actions/runners?per_page=100")
    return got.get("runners", []) if isinstance(got, dict) else None


def _pool(live: list[dict] | None, matrix: Matrix, last: dict[str, dict]) -> list[dict]:
    pool = []
    for r in live or []:
        labels = [lab["name"] for lab in r.get("labels", [])]
        pid = next((lab for lab in labels if lab in matrix.platforms), None)
        if not pid:
            continue
        spec = matrix.platforms[pid]
        if spec.os != "macos":
            continue
        pool.append({
            "name": spec.accelerator,
            "id": pid,
            "kind": "RunPod" if spec.runpod_gpu_type else "self-hosted",
            "os": spec.os,
            "memory_gib": int(spec.memory_gib),
            "status": "busy" if r["status"] == "online" and r.get("busy") else "idle" if r["status"] == "online" else "offline",
            "last": last.get(pid, {}),
        })
    return sorted(pool, key=lambda m: (m["kind"] != "self-hosted", m["name"]))


def _tokens(n: int) -> str:
    return f"{n // 1024}k" if n >= 1024 and n % 1024 == 0 else str(n)


def benchmarks(matrix: Matrix) -> list[dict]:
    workloads = {c.workload.id: c.workload for c in matrix.cells_for(Tier.TARGETED)
                 if str(c.engine) == "ollama" and str(c.workload.kind) in ("single_stream", "long_context", "concurrency", "prefix_shared")}
    order = sorted(workloads.values(), key=lambda w: (int(w.params.get("concurrency") or 1), int(w.params.get("prefill") or 0)))
    tests = []
    for w in order:
        n, prompt, out = int(w.params.get("concurrency") or 1), int(w.params.get("prefill") or 0), int(w.params.get("decode") or 0)
        head = "story prompt" if w.params.get("prompt") else f"{_tokens(prompt)}-token prompt"
        label = w.params.get("label") or f"{head}, {out} tokens out" + (f", {n} requests at once" if n > 1 else "")
        metric = "prefill" if w.params.get("primary") == "prefill_tok_s" else "decode"
        tests.append({"id": w.id, "name": label, "description": w.params.get("description", ""), "concurrency": n, "metric": metric})
    return tests


def verdicts(results: dict, commits: list[dict]) -> dict[str, list[dict]]:
    order = [c["sha"] for c in sorted(commits, key=lambda c: c["date"] or "")]
    out: dict[str, list[dict]] = {}
    for mac, r in results.items():
        for model, by_test in r["models"].items():
            for wl, by_commit in by_test.items():
                for phase in ("prefill", "decode"):
                    prev = None
                    for sha in order:
                        v = (by_commit.get(sha) or {}).get(phase)
                        if v is None:
                            continue
                        if prev:
                            out.setdefault(sha, []).append(
                                {"mac": mac, "model": model, "test": wl, "phase": phase, "pct": round(100 * (v / prev - 1), 1)})
                        prev = v
    return out


def quant_label(scheme: str) -> str:
    low = scheme.lower()
    if "u4" in low or "q4" in low:
        return "4-bit"
    if "mxfp4" in low:
        return "mxfp4"
    if "bf16" in low:
        return "bf16"
    if "nvfp4" in low:
        return "nvfp4"
    return scheme


def mac_models(matrix: Matrix) -> list[dict]:
    macs = [p for p in matrix.platforms.values() if p.os == "macos"]
    why = {}
    broken = (yaml.safe_load((matrix.root / "support.yaml").read_text()) or {}).get("first_token_broken") or {}
    for c in matrix.expand():
        if str(c.engine) == "pie" and c.platform.os == "macos":
            why.setdefault(c.artifact.id, set()).add(c.declared_unsupported_reason)
    out = []
    for a in matrix.artifacts.values():
        pie = matrix.artifacts.get(a.baseline_of or "")
        if not a.baseline_label or pie is None or not macs:
            continue
        out.append({"id": a.id, "name": a.ollama_tag or pie.display_name or pie.id, "pie": pie.id, "label": a.baseline_label, "family": a.family, "icon": icon_for(a.family),
                    "engine": ARM_ENGINE.get(a.source_format.value, a.source_format.value),
                    "scheme": str(a.scheme), "format": str(a.source_format), "gib": a.expected_gib, "context": pie.max_context,
                    "quant": quant_label(str(a.scheme)), "first_token_broken": broken.get(pie.id),
                    "unsupported": next(iter(why[pie.id])) if pie.id in why and None not in why[pie.id] else None})
    return sorted(out, key=lambda m: (m["name"], m["label"]))


def _paginate(path: str) -> list:
    try:
        out = subprocess.run(["gh", "api", "--paginate", "--slurp", path], capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return []


def in_flight(repo: str) -> list[str]:
    runs = _gh(f"repos/{repo}/actions/workflows/pie-eval.yml/runs?per_page=50&status=in_progress") or {}
    queued = _gh(f"repos/{repo}/actions/workflows/pie-eval.yml/runs?per_page=50&status=queued") or {}
    out = []
    for run in [*(runs.get("workflow_runs") or []), *(queued.get("workflow_runs") or [])]:
        title = run.get("display_title") or ""
        for word in title.replace(",", " ").split():
            if len(word) >= 7 and all(ch in "0123456789abcdef" for ch in word):
                out.append(word)
    return sorted(set(out))


def usage(repo: str, authors: dict[str, str]) -> dict[str, dict]:
    pages = _paginate(f"repos/{repo}/actions/workflows/pie-eval.yml/runs?per_page=100")
    out: dict[str, dict] = {}
    for run in (r for page in pages for r in page.get("workflow_runs", [])):
        sha = (run.get("display_title") or "").split()[-1] if run.get("display_title") else ""
        who = (run.get("triggering_actor") or {}).get("login") if run.get("event") == "workflow_dispatch" else authors.get(sha)
        if not who:
            continue
        u = out.setdefault(who, {"last": ""})
        u["last"] = max(u["last"], run.get("created_at") or "")
    return out


def people(repo: str, authors: dict[str, str]) -> list[dict]:
    roles = {c["login"]: c.get("role_name", "") for page in _paginate(f"repos/{repo}/collaborators?affiliation=all&per_page=100") for c in page}
    used = usage(repo, authors)
    none = {"last": ""}
    rows = [{"login": who, "role": roles.get(who, ""), **used.get(who, none)} for who in set(roles) | set(used)]
    rows.sort(key=lambda p: p["login"].lower())
    return sorted(rows, key=lambda p: p["last"], reverse=True)


def quality(store: Store) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted((store.root / "quality").glob("*.json")) if (store.root / "quality").exists() else []:
        q = json.loads(f.read_text())
        out.setdefault(q["artifact"], {})[q["task"]] = {k: q.get(k) for k in ("score", "ci95", "n", "version", "date", "engine", "empty")}
    return out


def build(store: Store, matrix: Matrix, live: list[dict] | None, *, repo: str, pie_repo: str,
          lookup_commits: bool = True) -> dict:
    tests = benchmarks(matrix)
    concurrency = {b["id"]: b["concurrency"] for b in tests}
    t = store.table(Tier.TARGETED)
    every = [r for r in t.to_pylist() if r["pie_commit"]] if t.num_rows else []
    latest = {}
    for r in every:
        latest[(r["run_id"], r["cell_id"] or r["cell_key"])] = r
    every = list(latest.values())
    measured_ok = (str(CellStatus.PASS), str(CellStatus.NOISY))
    rows = [r for r in every if r["status"] in measured_ok and (r["decode_tok_s"] is not None or r["output_tok_s"] is not None or r["prefill_tok_s"] is not None)]
    rows.sort(key=lambda r: r["started_at"])
    baseline_of = {a.id: a.baseline_of for a in matrix.artifacts.values() if a.baseline_of}
    label_of = {a.id: a.baseline_label for a in matrix.artifacts.values() if a.baseline_of and a.baseline_label}
    shown = {m["pie"] for m in mac_models(matrix)}
    baselines: dict[str, dict] = {}
    for r in rows:
        if r["engine"] != "pie" and r["artifact"] in label_of and r["workload"] in concurrency:
            single = concurrency[r["workload"]] == 1
            baselines.setdefault(r["platform"], {}).setdefault(baseline_of.get(r["artifact"], r["artifact"]), {}).setdefault(r["workload"], {}).setdefault(label_of[r["artifact"]], []).append({
                "at": r["started_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "prefill": r["prefill_tok_s"],
                "decode": r["decode_tok_s"] if single else r["output_tok_s"],
                "version": r["engine_version"] or "", "ttft": r["ttft_ms_p50"],
                "noisy": r["invalid_reason"] if r["status"] == str(CellStatus.NOISY) else None})
    rows = [r for r in rows if r["engine"] == "pie" and r["artifact"] in shown]
    failed = sorted({(r["pie_commit"], r["platform"], r["artifact"]) for r in every
                     if r["status"] == str(CellStatus.FAIL)
                     and r["workload"] in concurrency and r["artifact"] in shown})

    results: dict[str, dict] = {}
    order: list[str] = []
    last: dict[str, dict] = {}
    have: set[str] = set()
    for r in rows:
        if r["pie_commit"] not in order:
            order.append(r["pie_commit"])
        last[r["platform"]] = {"at": r["started_at"].strftime("%Y-%m-%dT%H:%M:%SZ"), "commit": r["pie_commit"]}
        if r["workload"] not in concurrency:
            continue
        mac = results.setdefault(r["platform"], {"name": r["accelerator"], "models": defaultdict(lambda: defaultdict(dict))})
        cell = json.loads(r["record_json"])["cell"]
        tf = flops.tflops(r, cell["workload"]["params"], flops.model_config(cell["artifact"]["base_model"]))
        single = concurrency[r["workload"]] == 1
        mac["models"][r["artifact"]][r["workload"]][r["pie_commit"]] = {
            "prefill": r["prefill_tok_s"], "prefill_tflops": tf["prefill_tflops"],
            "decode": r["decode_tok_s"] if single else r["output_tok_s"], "decode_tflops": tf["decode_tflops"], "output": r["output_tok_s"],
            "at": r["started_at"].strftime("%Y-%m-%dT%H:%M:%SZ"), "ttft": r["ttft_ms_p50"],
            "noisy": r["invalid_reason"] if r["status"] == str(CellStatus.NOISY) else None}
        have.add(r["artifact"])

    known = {c["sha"]: c for c in (history(pie_repo) if lookup_commits else [])}
    commits = []
    for sha in order:
        if sha in known:
            commits.append(dict(known[sha]))
            continue
        info = _gh(f"repos/{pie_repo}/commits/{sha}") if lookup_commits else None
        commit = (info or {}).get("commit", {})
        commits.append({
            "sha": sha,
            "message": (commit.get("message") or "").splitlines()[0][:90] if commit else "",
            "author": ((info or {}).get("author") or {}).get("login") or (commit.get("author") or {}).get("name", ""),
            "date": (commit.get("committer") or {}).get("date", ""),
        })
    commits.sort(key=lambda c: c["date"] or "~")
    measured = {c["sha"] for c in commits}
    all_commits = [c for c in known.values() if c["sha"] not in measured]

    models = mac_models(matrix)
    for m in models:
        m["has_results"] = m["pie"] in have
    return {
        "repo": repo, "pie_repo": pie_repo, "default_model": DEFAULT_MODEL,
        "benchmarks": tests,
        "verdicts": verdicts(results, commits), "baselines": baselines,
        "baseline_labels": sorted(set(label_of.values()), key=lambda label: (BASELINE_ORDER.index(label) if label in BASELINE_ORDER else len(BASELINE_ORDER), label)),
        "default_baseline": DEFAULT_BASELINE,
        "quality": quality(store),
        "icons": icons(),
        "commits": commits, "history": all_commits, "results": results, "models": models,
        "failed": [{"sha": sha, "mac": mac, "model": model} for sha, mac, model in failed],
        "running": in_flight(repo) if lookup_commits else [],
        "pool": _pool(live, matrix, last),
        "platforms": sorted(p.id for p in matrix.platforms.values() if p.os == "macos"),
        "specs": {p.id: {"accelerator": p.accelerator, "os": p.os, "memory_gib": int(p.memory_gib)} for p in matrix.platforms.values() if p.os == "macos"},
        "last": last,
        "people": people(repo, {c["sha"]: c["author"] for c in [*known.values(), *commits]}) if lookup_commits else [],
    }


def render(store: Store, matrix: Matrix, out: Path, live: list[dict] | None = None, *, repo: str = "pie-project/pie-evals",
           pie_repo: str = "pie-project/pie", lookup_commits: bool = True) -> int:
    data = build(store, matrix, live, repo=repo, pie_repo=pie_repo, lookup_commits=lookup_commits)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(PAGE.replace("__DATA__", json.dumps(data)))
    return len(data["commits"])
