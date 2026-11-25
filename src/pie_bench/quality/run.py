from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from pie_bench.installers.pie import python_dir
from pie_bench.paths import MATRIX

from .engines import ENGINES, engine_for, llamacpp_generate, mlxlm_generate, splash_generate
from .tasks import TASKS, wilson

LABELS = {"pie": "pie", "llamacpp": "llama.cpp", "mlxlm": "mlx-lm", "splash": "Splash"}

SYSTEM = "You are a helpful assistant."
PIE_RUN_TIMEOUT_S = 6 * 3600


class TasksSkipped(Exception):
    pass


def _tokenizer(snapshot: Path):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(snapshot), trust_remote_code=True)


def _chat_prompt(tok, prompt: str) -> str:
    if not getattr(tok, "chat_template", None):
        return f"{SYSTEM}\n\n{prompt}"
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    try:
        return tok.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
            reasoning_strength="low",
        )
    except Exception:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def _render(snapshot: Path, prompts: list[str]) -> list[str]:
    tok = _tokenizer(snapshot)
    return [_chat_prompt(tok, p) for p in prompts]


def _git_head(pie_root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(pie_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _quality_pie_env(pie_root: Path) -> dict[str, str]:
    from pie_bench.installers.bench_env import bench_dir

    path = [
        str(bench_dir()),
        str(python_dir(pie_root) / "client/src"),
        str(python_dir(pie_root) / "server/python"),
    ]
    return {**os.environ, "PIE_ROOT": str(pie_root), "PYTHONPATH": os.pathsep.join(path)}


def _quality_pie_argv(model, pie_root: Path, items: Path, out: Path, max_tokens: int) -> list[str]:
    from pie_bench.installers.bench_env import bench_python

    script = Path(__file__).resolve().parent / "scripts" / "quality_pie.py"
    engine = "metal" if sys.platform == "darwin" else "cuda"
    return [
        *(str(bench_python()), str(script), "--items", str(items), "--out", str(out)),
        *("--system", SYSTEM, "--max-tokens", str(max_tokens), "--"),
        *("latency", "--model", str(model), "--engine", engine),
        *("--inferlet-dir", str(pie_root / "examples/text-completion-bench")),
        *("--max-model-len", "4096", "--requests", "1"),
    ]


def _pie_generate(
    art, snapshot: Path, pie_root: Path, prompts: list[str], max_tokens: int, log
) -> tuple[list[str], str]:
    from pie_bench.checkpoints.pie_import import ensure_artifact, needs_import
    from pie_bench.installers.bench_env import bench_dir

    commit = _git_head(pie_root)
    model = (
        ensure_artifact(art, snapshot, pie_root / "target/release/pie", commit, log=log)
        if needs_import(art)
        else snapshot
    )
    env = _quality_pie_env(pie_root)
    tok = _tokenizer(snapshot)
    token_ids = [tok.encode(r, add_special_tokens=False) for r in _render(snapshot, prompts)]
    with tempfile.TemporaryDirectory() as tmp:
        items, out = Path(tmp) / "items.json", Path(tmp) / "out.json"
        rows = [
            {"prompt": p, "prompt_tokens": ids} for p, ids in zip(prompts, token_ids, strict=True)
        ]
        items.write_text(json.dumps(rows))
        argv = _quality_pie_argv(model, pie_root, items, out, max_tokens)
        subprocess.run(argv, cwd=str(bench_dir()), env=env, check=True, timeout=PIE_RUN_TIMEOUT_S)
        return json.loads(out.read_text()), commit[:12]


def tokenizer_dir(art, hf_cache: Path, log=print) -> Path:
    from huggingface_hub import snapshot_download

    from pie_bench.checkpoints.snapshots import TOKENIZER_PATTERNS

    repo = art.tokenizer_from or art.gguf_config_from
    if not repo:
        raise RuntimeError(f"{art.id}: no tokenizer repo (tokenizer_from) for a GGUF arm")
    log(f"tokenizer: {repo}")
    token = os.environ.get("HF_TOKEN") or None
    return Path(
        snapshot_download(
            repo, cache_dir=str(hf_cache), allow_patterns=TOKENIZER_PATTERNS, token=token
        )
    )


def generate(
    engine: str,
    art,
    snapshot: Path | None,
    tok_dir: Path | None,
    pie_root: Path,
    prompts: list[str],
    max_tokens: int,
    log,
) -> tuple[list[str], str]:
    if engine == "pie":
        return _pie_generate(art, snapshot, pie_root, prompts, max_tokens, log)
    if engine == "splash":
        return splash_generate(art, prompts, SYSTEM, max_tokens, log)
    rendered = _render(tok_dir, prompts)
    bos = _tokenizer(tok_dir).bos_token
    if engine == "mlxlm":
        return mlxlm_generate(snapshot, rendered, max_tokens, bos, log, family=art.family)
    if engine == "llamacpp":
        return llamacpp_generate(art, rendered, max_tokens, bos, log)
    raise ValueError(f"no engine {engine!r} (one of {', '.join(ENGINES)})")


def load_items(task: str, n: int, log=print):
    try:
        load, _score, _max_tokens = TASKS[task]
        return load(n)
    except Exception as e:
        gated = type(e).__name__ == "GatedRepoError" or "401" in str(e)
        hint = (
            " (gated dataset: accept its terms on huggingface.co and give the runner's HF_TOKEN access)"
            if gated
            else ""
        )
        first_line = str(e).splitlines()[0][:160] if str(e) else ""
        log(
            f"quality {task}: skipped, could not load the questions: {type(e).__name__}: {first_line}{hint}"
        )
        return None


def _summary(
    art,
    engine: str,
    task: str,
    items,
    texts: list[str],
    scores: list[float],
    version: str,
    t0: float,
) -> dict:
    correct = sum(scores)
    lo, hi = wilson(correct, len(scores))
    return {
        "artifact": art.id,
        "model": art.baseline_of or art.id,
        "engine": engine,
        "label": art.baseline_label or LABELS[engine],
        "checkpoint": art.base_model,
        "scheme": str(art.scheme),
        "task": task,
        "n": len(scores),
        "correct": correct,
        "score": correct / len(scores) if scores else None,
        "ci95": [lo, hi],
        "version": version,
        "empty": sum(1 for t in texts if not t),
        "minutes": round((time.monotonic() - t0) / 60, 1),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "samples": [
            {"id": i.id, "score": s, "text": t}
            for i, s, t in zip(items, scores, texts, strict=True)
        ],
    }


def _inputs_for(art, engine: str, log) -> tuple[Path | None, Path | None]:
    from pie_bench.checkpoints.hf_cache import hf_cache_dir
    from pie_bench.checkpoints.snapshots import ensure_snapshot

    if engine == "llamacpp":
        return None, tokenizer_dir(art, hf_cache_dir(), log)
    if engine == "splash":
        return None, None
    snapshot = ensure_snapshot(art, hf_cache_dir(), download=True, log=log)
    return snapshot, snapshot


def run_quality(
    artifact_id: str,
    tasks: list[str],
    n: int,
    *,
    matrix_dir: str = str(MATRIX),
    store_dir: str | None = None,
    pie_root: Path,
    tag: str | None = None,
    tag_kind: str | None = None,
    platform: str | None = None,
    log=print,
) -> list[str]:
    from pie_bench.plan.matrix import Matrix
    from pie_bench.plan.selectors import cannot_load
    from pie_bench.results.store import open_store

    store = open_store(store_dir)
    m = Matrix.load(matrix_dir)
    art = m.artifacts[artifact_id]
    engine = engine_for(art)
    why = cannot_load(m, engine, art)
    if why:
        log(f"quality {art.id}: not scored, {why}")
        return []
    snapshot, tok_dir = _inputs_for(art, engine, log)
    written: list[str] = []
    skipped: list[str] = []
    for task in tasks:
        _load, score, max_tokens = TASKS[task]
        items = load_items(task, n, log)
        if items is None:
            skipped.append(task)
            continue
        t0 = time.monotonic()
        texts, version = generate(
            engine, art, snapshot, tok_dir, pie_root, [i.prompt for i in items], max_tokens, log
        )
        scores = [score(i, t) for i, t in zip(items, texts, strict=True)]
        summary = _summary(art, engine, task, items, texts, scores, version, t0)
        if platform:
            summary["platform"] = platform
        path = store.write_quality(summary, tag=tag, tag_kind=tag_kind)
        lo, hi = summary["ci95"]
        log(
            f"quality {art.id} {task}: {summary['correct']:.0f}/{len(scores)} = {summary['score']:.1%} "
            f"(95% {lo:.1%}..{hi:.1%}) in {summary['minutes']} min"
        )
        written.append(path)
    if skipped:
        raise TasksSkipped(f"{art.id}: skipped {', '.join(skipped)}")
    return written
