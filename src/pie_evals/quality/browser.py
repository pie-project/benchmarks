"""Quality of pie in a browser tab (the webgpu platforms), the way the Macs are scored: MATH-500 on a full model
(the Mac's prompts, greedy, 1024 tokens, run.py) and, on a model slice, the KL of pie's first-token distribution
from the Mac's mlx-lm one (dist_run.py's first-token mode, against its saved reference in matrix/first-token-ref).
pie runs as the browser speed rows run it: the same .wgpu.zt, server-web and bridge (node/engines/browser.py)."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from . import kl
from .dist_run import FIRST_REF_DIR, saved_first_ref
from .run import _render, _tokenizer
from .tasks import TASKS, wilson

#: requests in flight in the tab: the first-token prompts four at once, as the Mac's pie quality run sends them
#: (quality_pie.py); answers one at a time, since pie's tab stops making progress once 4 lanes end at different
#: lengths (MATH-500 on Qwen3.5-4B, web-rtx5090: GPU idle, no request returns), while one at a time answers
CONCURRENCY = 4
INFERLET = Path(__file__).resolve().parents[3] / "inferlets" / "first-token-topk"


def topk_wasm(pie_root: Path, log=print) -> Path:
    """inferlets/first-token-topk built in pie's examples/ (its pinned toolchain and inferlet crate)."""
    from pie_evals.node.build import wasm_target

    import shutil

    dst = pie_root / "examples" / INFERLET.name
    shutil.copytree(INFERLET, dst, dirs_exist_ok=True)
    target = wasm_target(pie_root)
    log(f"browser quality: building {INFERLET.name} ({target})")
    subprocess.run(["cargo", "build", "--release", "--target", target, "--manifest-path", f"{INFERLET.name}/Cargo.toml"], cwd=pie_root / "examples", check=True, timeout=3600)
    return dst / "target" / target / "release" / "first_token_topk.wasm"


def run_browser(artifact_id: str, platform_id: str, *, first: bool, tasks: list[str], n: int, pie_root: Path, matrix_dir: str = "matrix",
                store_dir: str | None = None, tag: str | None = None, tag_kind: str | None = None, out_dir: Path = Path("parity-out"), log=print) -> list[dict]:
    from pie_evals.node.engines import get_engine
    from pie_evals.node.engines.recipes import load_recipe
    from pie_evals.node.importer import ensure_artifact
    from pie_evals.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_evals.plan.matrix import Matrix
    from pie_evals.results.store import Store

    m = Matrix.load(matrix_dir)
    art, plat = m.artifacts[artifact_id], m.platforms[platform_id]
    mode = next(md for md in m.modes.values() if int(md.tp) == 1 and not md.spec_dec and not md.extra)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = ensure_snapshot(art, hf_cache_dir(), pie_root=pie_root, python=os.environ.get("PIE_PY", "python3"), download=True, log=log)
    tok = _tokenizer(snapshot)
    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    zt = ensure_artifact(art, snapshot, pie_root / "target/release/pie", commit, log=log)
    store = Store(store_dir)
    now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731

    if first:
        rendered = kl.gibberish(tok)
        saved = saved_first_ref(matrix_dir, art.id, rendered)
        if not saved:
            raise RuntimeError(f"{art.id}: no saved first-token reference for these prompts in {matrix_dir}/{FIRST_REF_DIR}")
        sets = {"first": [{"prompt": r, "ids": tok.encode(r, add_special_tokens=False)} for r in rendered]}
        # the distribution after all but the last token, as prompt_logprobs scores the last position
        reqs = {"first": [{"prompt": "", "ids": x["ids"][:-1], "max_tokens": 1, "topk": kl.TOPK} for x in sets["first"]]}
        prefill, decode = 64, 1
    else:
        sets, reqs = {}, {}
        for t in tasks:
            items = TASKS[t][0](n)
            rendered = _render(snapshot, [i.prompt for i in items])
            sets[t] = items
            reqs[t] = [{"prompt": r, "ids": tok.encode(r, add_special_tokens=False), "max_tokens": TASKS[t][2]} for r in rendered]
        prefill, decode = max(len(q["ids"]) for rs in reqs.values() for q in rs), max(TASKS[t][2] for t in tasks)
    conc = CONCURRENCY if first else 1
    base = m.workloads["c32"]
    workload = base.model_copy(update={"params": {**base.params, "concurrency": conc, "prefill": prefill, "decode": decode}})
    recipe = load_recipe("pie", "default", plat, workload, family=art.family, artifact=art.id)
    recipe["snapshot_dir"] = str(zt)
    if first:
        recipe["topk_wasm"] = str(topk_wasm(pie_root, log))
    # pie reports no token until a request returns (no per-token timing at 4 in flight): a 1024-token answer outlasts the
    # bridge's 300 s stall watch
    os.environ.setdefault("BROWSER_STALL_S", "3600")
    engine = get_engine("pie", "webgpu")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=recipe)
    t0 = time.monotonic()
    engine.serve(workload, out_dir / f"{art.id}-{platform_id}-bridge.log", 3600)
    answers: dict[str, list[dict]] = {}
    try:
        for t, rs in reqs.items():
            job = {"requests": rs, "concurrency": conc, "sampling": {"temperature": 0.0, "top_p": 1.0, "ignore_eos": False, "return_text": True}}
            out = kl._post(engine.server_url + "/run", job, timeout=12 * 3600)
            if out.get("error"):
                raise RuntimeError(f"browser: {out['error']}")
            bad = [r.get("error") for r in out["results"] if not r.get("ok")]
            if bad:
                raise RuntimeError(f"browser: {len(bad)} of {len(rs)} requests failed: {bad[0]}")
            answers[t] = out["results"]
            log(f"browser quality {art.id}@{platform_id} {t}: {len(rs)} answered in {(time.monotonic() - t0) / 60:.1f} min")
    finally:
        engine.stop()
    version = commit[:12]
    rows = []
    if first:
        ref = [[{}] * (k - 1) + [{int(a): v for a, v in last.items()}] for k, last in zip(saved["tokens"], saved["last"], strict=True)]
        pie = [[{}] * (len(x["ids"]) - 1) + [dict(zip(r["topk"]["ids"], r["topk"]["logprobs"], strict=True))] for x, r in zip(sets["first"], answers["first"], strict=True)]
        summary = {"artifact": art.id, "model": art.id, "engine": "pie", "ref_engine": saved["ref_engine"], "ref_version": saved.get("ref_version"),
                   "ref_platform": saved["platform"], "ref_artifact": saved["artifact"], "platform": platform_id, "task": f"parity@{platform_id}",
                   "checkpoint": art.base_model, "scheme": str(art.scheme), "tp": 1, "miniature": str(art.kind) == "miniature",
                   "layers": getattr(art.miniature, "layers", None) if art.miniature else None, "prompts": len(rendered), "answer_tokens": 1,
                   "mode": "first_token", "ref_texts": "saved", "version": version}
        summary.update(kl.last_position(ref, pie, [len(x["ids"]) for x in sets["first"]]))
        if summary.get("first_token_topk"):
            summary["first_token_topk"]["tokens"] = [tok.decode([i]) for i in summary["first_token_topk"]["ids"]]
        summary["score"], summary["n"] = summary["top1_agree"], summary["positions"]
        summary["correct"] = round((summary["top1_agree"] or 0) * summary["positions"])
        summary["ci95"] = [summary["score"] or 0, summary["score"] or 0]
        summary["exact_match"] = summary["top1_agree"]
        summary.update(minutes=round((time.monotonic() - t0) / 60, 1), date=now(), samples=[{"id": i, "prompt": r} for i, r in enumerate(rendered)])
        (out_dir / f"{art.id}-{platform_id}.json").write_text(json.dumps(summary, indent=1))
        where = store.write_quality(summary, tag=tag, tag_kind=tag_kind)
        log(f"first-token {art.id}@{platform_id}: KL mean {summary['kl_mean']}, top-1 {summary['top1_agree']} over {summary['positions']} prompts -> {where}")
        return [summary]
    for t, items in sets.items():
        texts = [r.get("text") or "" for r in answers[t]]
        scores = [TASKS[t][1](i, x) for i, x in zip(items, texts, strict=True)]
        correct = sum(scores)
        lo, hi = wilson(correct, len(scores))
        row = {"artifact": art.id, "model": art.baseline_of or art.id, "engine": "pie", "label": "pie", "checkpoint": art.base_model, "scheme": str(art.scheme),
               "platform": platform_id, "task": t, "n": len(scores), "correct": correct, "score": correct / len(scores) if scores else None, "ci95": [lo, hi],
               "version": version, "empty": sum(1 for x in texts if not x), "minutes": round((time.monotonic() - t0) / 60, 1), "date": now(),
               "samples": [{"id": i.id, "score": s, "text": x} for i, s, x in zip(items, scores, texts, strict=True)]}
        store.write_quality(row, tag=tag, tag_kind=tag_kind)
        log(f"browser quality {art.id}@{platform_id} {t}: {correct:.0f}/{len(scores)} = {row['score']:.1%} (95% {lo:.1%}..{hi:.1%})")
        rows.append(row)
    return rows
