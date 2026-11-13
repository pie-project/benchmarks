from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from pie_bench.node.build import python_dir
from pie_bench.paths import MATRIX

from .engines import ENGINES, engine_for, llamacpp_generate, mlxlm_generate, splash_generate
from .tasks import TASKS, wilson

LABELS = {"pie": "pie", "llamacpp": "llama.cpp", "mlxlm": "mlx-lm", "splash": "Splash"}

SYSTEM = "You are a helpful assistant."


def _tokenizer(snapshot: Path):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(snapshot), trust_remote_code=True)


def _render(snapshot: Path, prompts: list[str]) -> list[str]:
    tok = _tokenizer(snapshot)
    out = []
    for p in prompts:
        if not getattr(tok, "chat_template", None):
            out.append(f"{SYSTEM}\n\n{p}")
            continue
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": p}]
        try:
            out.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False, reasoning_strength="low"))
        except Exception:
            out.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    return out


def _pie_generate(art, snapshot: Path, pie_root: Path, prompts: list[str], max_tokens: int, log) -> tuple[list[str], str]:
    from pie_bench.node.build import bench_dir, bench_python
    from pie_bench.node.importer import ensure_artifact, needs_import

    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    model = ensure_artifact(art, snapshot, pie_root / "target/release/pie", commit, log=log) if needs_import(art) else snapshot
    script = Path(__file__).resolve().parents[1] / "node" / "engines" / "scripts" / "quality_pie.py"
    env = {**os.environ, "PIE_ROOT": str(pie_root), "PYTHONPATH": os.pathsep.join([str(bench_dir()), str(python_dir(pie_root) / "client/src"), str(python_dir(pie_root) / "server/python")])}
    tok = _tokenizer(snapshot)
    token_ids = [tok.encode(r, add_special_tokens=False) for r in _render(snapshot, prompts)]
    with tempfile.TemporaryDirectory() as tmp:
        items, out = Path(tmp) / "items.json", Path(tmp) / "out.json"
        items.write_text(json.dumps([{"prompt": p, "prompt_tokens": ids} for p, ids in zip(prompts, token_ids, strict=True)]))
        argv = [str(bench_python()), str(script), "--items", str(items), "--out", str(out), "--system", SYSTEM, "--max-tokens", str(max_tokens), "--",
                "latency", "--model", str(model), "--engine", "metal" if sys.platform == "darwin" else "cuda", "--inferlet-dir", str(pie_root / "examples/text-completion-bench"),
                "--max-model-len", "4096", "--requests", "1"]
        subprocess.run(argv, cwd=str(bench_dir()), env=env, check=True, timeout=6 * 3600)
        return json.loads(out.read_text()), commit[:12]


def tokenizer_dir(art, hf_cache: Path, log=print) -> Path:
    from huggingface_hub import snapshot_download

    from pie_bench.node.snapshots import TOKENIZER_PATTERNS

    repo = art.tokenizer_from or art.gguf_config_from
    if not repo:
        raise RuntimeError(f"{art.id}: no tokenizer repo (tokenizer_from) for a GGUF arm")
    log(f"tokenizer: {repo}")
    return Path(snapshot_download(repo, cache_dir=str(hf_cache), allow_patterns=TOKENIZER_PATTERNS, token=os.environ.get("HF_TOKEN") or None))


def generate(engine: str, art, snapshot: Path | None, tok_dir: Path | None, pie_root: Path, prompts: list[str], max_tokens: int, log) -> tuple[list[str], str]:
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


class TasksSkipped(Exception):
    def __init__(self, artifact: str, tasks: list[str], written: list[Path]):
        super().__init__(f"{artifact}: skipped {', '.join(tasks)}")
        self.artifact, self.tasks, self.written = artifact, tasks, written


def load_items(task: str, n: int, log=print):
    try:
        return TASKS[task][0](n)
    except Exception as e:
        gated = type(e).__name__ == "GatedRepoError" or "401" in str(e)
        hint = " (gated dataset: accept its terms on huggingface.co and give the runner's HF_TOKEN access)" if gated else ""
        log(f"quality {task}: skipped, could not load the questions: {type(e).__name__}: {str(e).splitlines()[0][:160] if str(e) else ''}{hint}")
        return None


def run_quality(artifact_id: str, tasks: list[str], n: int, *, matrix_dir: str = str(MATRIX), store_dir: str | None = None, pie_root: Path, tag: str | None = None, tag_kind: str | None = None, platform: str | None = None, log=print) -> list[str]:
    from pie_bench.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_bench.plan.matrix import Matrix
    from pie_bench.results.store import Store

    store = Store(store_dir)
    m = Matrix.load(matrix_dir)
    art = m.artifacts[artifact_id]
    engine = engine_for(art)
    from pie_bench.plan.matrix import cannot_load

    why = cannot_load(m, engine, art)
    if why:
        log(f"quality {art.id}: not scored, {why}")
        return []
    snapshot = tok_dir = None
    if engine == "llamacpp":
        tok_dir = tokenizer_dir(art, hf_cache_dir(), log)
    elif engine != "splash":
        snapshot = tok_dir = ensure_snapshot(art, hf_cache_dir(), download=True, log=log)
    written: list[str] = []
    skipped: list[str] = []
    for task in tasks:
        load, score, max_tokens = TASKS[task]
        items = load_items(task, n, log)
        if items is None:
            skipped.append(task)
            continue
        t0 = time.monotonic()
        texts, version = generate(engine, art, snapshot, tok_dir, pie_root, [i.prompt for i in items], max_tokens, log)
        scores = [score(i, t) for i, t in zip(items, texts, strict=True)]
        correct = sum(scores)
        lo, hi = wilson(correct, len(scores))
        summary = {
            "artifact": art.id, "model": art.baseline_of or art.id, "engine": engine, "label": art.baseline_label or LABELS[engine],
            "checkpoint": art.base_model, "scheme": str(art.scheme),
            "task": task, "n": len(scores), "correct": correct, "score": correct / len(scores) if scores else None, "ci95": [lo, hi],
            "version": version, "empty": sum(1 for t in texts if not t), "minutes": round((time.monotonic() - t0) / 60, 1),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "samples": [{"id": i.id, "score": s, "text": t} for i, s, t in zip(items, scores, texts, strict=True)],
        }
        if platform:
            summary["platform"] = platform
        path = store.write_quality(summary, tag=tag, tag_kind=tag_kind)
        log(f"quality {art.id} {task}: {correct:.0f}/{len(scores)} = {summary['score']:.1%} (95% {lo:.1%}..{hi:.1%}) in {summary['minutes']} min")
        written.append(path)
    if skipped:
        raise TasksSkipped(art.id, skipped, written)
    return written
