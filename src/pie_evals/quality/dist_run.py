"""Run distribution parity (``kl.py``) for one model on one device: the reference
engine (vLLM, or mlx-lm on a Mac) and pie, one after the other, each alone on the
device, on the same checkpoint, cut, dtype and tp. One quality row per (model,
platform), task ``parity@<platform>``."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import kl
from .run import _render, _tokenizer
from .tasks import TASKS

#: prompts per task, from the catalog's question sets (gsm8k, mmlu, arc, math500, ifeval)
PER_TASK = 8
ANSWER_TOKENS = 256
PARITY_TASKS = ("gsm8k", "mmlu", "arc", "math500", "ifeval")
#: the shape whose engine config pie_bench boots with: concurrency 1, a 4k context
WORKLOAD = "lc-2k-128"


def prompts(log=print) -> list[str]:
    out = []
    for t in PARITY_TASKS:
        try:
            out += [i.prompt for i in TASKS[t][0](PER_TASK)]
        except Exception as e:  # noqa: BLE001 — a gated set is skipped, the rest still score
            log(f"parity: {t} questions unavailable ({type(e).__name__}); skipped")
    return out


def device_idle(backend: str, grace_s: float = 60.0) -> str | None:
    """Why the device is not idle, or None. One test per device: nothing else may hold it. nvidia-smi's utilization
    is averaged over its last sample period and reads 100% for a while after a process exits, so a busy reading must
    hold for ``grace_s`` with memory in use before it counts."""
    deadline = time.monotonic() + grace_s
    while True:
        why = _busy(backend)
        if why is None or time.monotonic() > deadline:
            return why
        time.sleep(5)


def _busy(backend: str) -> str | None:
    try:
        if backend == "cuda":
            q = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=30).stdout
            for ln in q.strip().splitlines():
                util, mem = (int(x.strip()) for x in ln.split(","))
                if mem > 1500 or (util > 5 and mem > 100):
                    return f"GPU busy: {util}% util, {mem} MiB used"
        elif backend == "rocm":
            q = subprocess.run(["rocm-smi", "--showuse", "--json"], capture_output=True, text=True, timeout=30).stdout
            for card in (json.loads(q or "{}") or {}).values():
                if isinstance(card, dict) and int(str(card.get("GPU use (%)", "0")).strip() or 0) > 5:
                    return f"GPU busy: {card.get('GPU use (%)')}%"
    except Exception:  # noqa: BLE001 — no tool to ask: assume idle, the clean-check of the pod already ran
        return None
    return None


class Server:
    """A server process that announces its base URL on stdout (``PARITY_URL=``) or listens on a known port."""

    def __init__(self, argv: list[str], env: dict, cwd: str | None, log_path: Path, url: str | None = None):
        self.log_path = log_path
        self.fh = log_path.open("w")
        # its own process group: stop() reaches the server's children too (pie under the serve script, vLLM's engine core)
        self.proc = subprocess.Popen(argv, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
        self.url = url
        self.ready = threading.Event()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        for line in self.proc.stdout:
            self.fh.write(line)
            self.fh.flush()
            m = re.search(r"PARITY_URL=(\S+)", line)
            if m:
                self.url = m.group(1)
                self.ready.set()

    def wait(self, timeout_s: float) -> str:
        deadline = time.monotonic() + timeout_s
        while self.url is None:
            if self.proc.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(f"server did not come up: {self.tail()}")
            time.sleep(2)
        while True:
            if self.proc.poll() is not None:
                raise RuntimeError(f"server exited: {self.tail()}")
            try:
                return kl.wait_ready(self.url, timeout_s=10)
            except Exception:  # noqa: BLE001
                if time.monotonic() > deadline:
                    raise RuntimeError(f"server never answered /v1/models: {self.tail()}") from None

    def tail(self, n: int = 40) -> str:
        try:
            return "".join(self.log_path.read_text().splitlines(True)[-n:])
        except OSError:
            return ""

    def stop(self) -> None:
        # the whole group, until none of it is left: a child that outlives the server holds the device (TPU: /dev/vfio busy)
        def group(sig) -> bool:
            try:
                os.killpg(self.proc.pid, sig)
                return True
            except ProcessLookupError:
                return False

        group(signal.SIGTERM)
        deadline = time.monotonic() + 60
        while self.proc.poll() is None or group(0):
            if time.monotonic() > deadline:
                group(signal.SIGKILL)
                self.proc.wait()
                break
            time.sleep(1)
        self.fh.close()


def _free_port() -> int:
    from pie_evals.node.engines.served import free_port

    return free_port()


def vllm_server(engine, snapshot: Path, tp: int, log_path: Path, max_seqs: int = 1) -> Server:
    port = _free_port()
    gmu = engine.recipe.get("gpu_mem_util", 0.90) or 0.90
    argv = [engine.python, "-m", "vllm.entrypoints.openai.api_server", "--model", str(snapshot), "--port", str(port), "--host", "127.0.0.1",
            "--tensor-parallel-size", str(tp), "--max-model-len", "4096", "--max-logprobs", str(kl.TOPK), "--gpu-memory-utilization", str(gmu),
            "--no-enable-prefix-caching", "--trust-remote-code", "--max-num-seqs", str(max_seqs)]
    if engine.artifact.kv_dtype and str(engine.artifact.kv_dtype) not in ("bf16", "auto", "fp16"):
        argv += ["--kv-cache-dtype", str(engine.artifact.kv_dtype)]
    if engine.recipe.get("attention_backend"):
        argv += ["--attention-backend", str(engine.recipe["attention_backend"])]
    env = engine.process_env()
    cfg = json.loads((snapshot / "config.json").read_text()) if (snapshot / "config.json").exists() else {}
    if str(engine.platform.backend) == "xla" and "kv_lora_rank" in {**cfg, **(cfg.get("text_config") or {})}:
        # vllm-tpu serves an MLA model only on its new model design with DP attention ("MLA models require both ...")
        env["NEW_MODEL_DESIGN"] = "1"
        argv += ["--additional-config", json.dumps({"sharding": {"sharding_strategy": {"enable_dp_attention": True}}})]
    return Server(argv, env, None, log_path, url=f"http://127.0.0.1:{port}")


def pie_server(engine, workload, log_path: Path) -> Server:
    from pie_evals.node.workloads import common_args_for

    argv = engine.build_argv(workload, common_args_for(workload), log_path.with_suffix(".json"))
    script = Path(__file__).resolve().parents[1] / "node" / "engines" / "scripts" / "parity_pie_serve.py"
    i = next(k for k, a in enumerate(argv) if a.endswith("pie_bench.py"))
    argv = [argv[0], str(script), *argv[i + 1:]]
    env = engine.process_env()
    env["PYTHONPATH"] = ":".join([str(engine.pie_root / "scripts/bench"), env.get("PYTHONPATH", "")])
    return Server(argv, env, str(engine.pie_root / "scripts/bench"), log_path)


def mlx_side(snapshot: Path, rendered: list[str], greedy: bool, log_path: Path) -> tuple[list[str], list[list[dict[int, float]]]]:
    """mlx-lm in its own interpreter: greedy answers and teacher-forced top-20 over prompt+answer."""
    script = Path(__file__).resolve().parents[1] / "node" / "engines" / "scripts" / "parity_mlx.py"
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = Path(tmp) / "in.json", Path(tmp) / "out.json"
        inp.write_text(json.dumps({"prompts": rendered, "max_tokens": ANSWER_TOKENS, "topk": kl.TOPK, "greedy": greedy}))
        with log_path.open("w") as fh:
            subprocess.run([os.environ.get("MLX_PY", sys.executable), str(script), str(snapshot), str(inp), str(out)], stdout=fh, stderr=subprocess.STDOUT, check=True, timeout=6 * 3600)
        d = json.loads(out.read_text())
    return d["texts"], [[{int(k): v for k, v in pos.items()} for pos in t] for t in d["scored"]]



def _reason(e: Exception, out_dir: Path, art_id: str, ref_name: str) -> str:
    """The line that says why the reference engine could not run the model: its log's last error line, else the exception."""
    for log_path in sorted(out_dir.glob(f"{art_id}-{'vllm' if ref_name == 'vllm' else 'mlx'}*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        lines = [ln.strip() for ln in log_path.read_text(errors="replace").splitlines() if re.search(r"(Error|not supported|unsupported)", ln)]
        if lines:
            return lines[-1][:400]
    return f"{type(e).__name__}: {str(e).strip().splitlines()[-1][:400] if str(e).strip() else ''}"


def _reference(ref_name, art, plat, workload, mode, snapshot, rendered, tp, backend, pie_root, m, vllm_pin, summary, out_dir, log):
    from pie_evals.node.engines import get_engine
    from pie_evals.node.engines.recipes import load_recipe

    if ref_name == "vllm":
        from pie_evals.node.baselines import ensure_baseline

        recipe = load_recipe("vllm", "competitive", plat, workload, family=art.family)
        pin = vllm_pin or os.environ.get("PARITY_VLLM_PIN") or m.engines["vllm"].pin
        if pin:
            recipe["pin"] = pin
            if not os.environ.get("VLLM_PY"):
                ensure_baseline("vllm", pin, backend=backend, log=log)
        ref_engine = get_engine("vllm")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=recipe)
        summary["ref_version"] = ref_engine.version()
        srv = vllm_server(ref_engine, snapshot, tp, out_dir / f"{art.id}-vllm.log")
        try:
            model = srv.wait(3600)
            ref_texts = kl.greedy(srv.url, model, rendered, ANSWER_TOKENS, parallel=1)
            ref_scored = kl.scored(srv.url, model, [r + t for r, t in zip(rendered, ref_texts, strict=True)], parallel=1)
        finally:
            srv.stop()
        return ref_texts, ref_scored
    summary["ref_version"] = subprocess.run([os.environ.get("MLX_PY", sys.executable), "-c", "import mlx_lm; print(mlx_lm.__version__)"], capture_output=True, text=True).stdout.strip()
    ref_texts, _ = mlx_side(snapshot, rendered, True, out_dir / f"{art.id}-mlx-greedy.log")
    _, ref_scored = mlx_side(snapshot, [r + t for r, t in zip(rendered, ref_texts, strict=True)], False, out_dir / f"{art.id}-mlx-score.log")
    return ref_texts, ref_scored

def run_parity(artifact_id: str, platform_id: str, *, pie_root: Path, matrix_dir: str = "matrix", store_dir: str | None = None,
               tag: str | None = None, tag_kind: str | None = None, out_dir: Path = Path("parity-out"), vllm_pin: str | None = None, log=print) -> dict:
    from pie_evals.node.engines import get_engine
    from pie_evals.node.engines.recipes import load_recipe
    from pie_evals.node.importer import ensure_artifact, needs_import
    from pie_evals.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_evals.plan.matrix import Matrix
    from pie_evals.results.store import Store

    m = Matrix.load(matrix_dir)
    art, plat = m.artifacts[artifact_id], m.platforms[platform_id]
    backend = str(plat.backend)
    tp = max(1, int(plat.count))
    mode = next((md for md in m.modes.values() if int(md.tp) == tp and not md.spec_dec and not md.extra), None)
    workload = m.workloads[WORKLOAD]
    out_dir.mkdir(parents=True, exist_ok=True)
    busy = device_idle(backend)
    if busy:
        raise RuntimeError(f"device not idle before the run: {busy}")
    snapshot = ensure_snapshot(art, hf_cache_dir(), pie_root=pie_root, python=os.environ.get("PIE_PY", "python3"), download=True, log=log)
    tok = _tokenizer(snapshot)
    qs = prompts(log)
    rendered = _render(snapshot, qs)
    t0 = time.monotonic()
    ref_name = "mlxlm" if backend == "metal" else "vllm"
    summary: dict = {"artifact": art.id, "model": art.id, "engine": "pie", "ref_engine": ref_name, "platform": platform_id,
                     "task": f"parity@{platform_id}", "checkpoint": art.base_model, "scheme": str(art.scheme), "tp": tp,
                     "miniature": str(art.kind) == "miniature", "layers": getattr(art.miniature, "layers", None) if art.miniature else None,
                     "prompts": len(rendered), "answer_tokens": ANSWER_TOKENS}

    # 1. the reference: greedy answers, then the teacher-forced distributions over prompt + answer.
    # A reference that cannot run the model is a cell of its own (the site's crossed-out circle); pie still runs.
    ref_texts = ref_scored = None
    try:
        ref_texts, ref_scored = _reference(ref_name, art, plat, workload, mode, snapshot, rendered, tp, backend, pie_root, m, vllm_pin, summary, out_dir, log)
    except Exception as e:  # noqa: BLE001
        summary["ref_unsupported"] = _reason(e, out_dir, art.id, ref_name)
        log(f"parity {art.id}@{platform_id}: {ref_name} cannot run it: {summary['ref_unsupported']}")
    log(f"parity {art.id}@{platform_id}: reference {ref_name} done in {(time.monotonic() - t0) / 60:.1f} min")

    busy = device_idle(backend)
    if busy:
        raise RuntimeError(f"device not idle between engines: {busy}")

    # 2. pie on the same device, same weights, same text: pie must run every model, a failure here is a pie bug
    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    model_path = snapshot
    if needs_import(art) or tp > 1 or backend == "xla":
        model_path = ensure_artifact(art, snapshot, pie_root / "target/release/pie", commit, log=log)
    precipe = load_recipe("pie", "default", plat, workload, family=art.family)
    precipe["snapshot_dir"] = str(model_path)
    pie_engine = get_engine("pie")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=precipe)
    srv = pie_server(pie_engine, workload, out_dir / f"{art.id}-pie.log")
    try:
        model = srv.wait(3600)
        pie_texts = kl.greedy(srv.url, model, rendered, ANSWER_TOKENS, parallel=1)
        pie_scored = kl.scored(srv.url, model, [r + t for r, t in zip(rendered, ref_texts, strict=True)], parallel=1) if ref_texts is not None else None
    finally:
        srv.stop()
    summary["version"] = commit[:12]
    summary["minutes"] = round((time.monotonic() - t0) / 60, 1)
    summary["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if ref_texts is None:
        summary.update(score=None, n=0, correct=0, ci95=[0, 0], pie_ok=sum(1 for t in pie_texts if t) == len(pie_texts))
        summary["samples"] = [{"id": i, "pie": b} for i, b in enumerate(pie_texts)]
        (out_dir / f"{art.id}-{platform_id}.json").write_text(json.dumps(summary, indent=1))
        where = Store(store_dir).write_quality(summary, tag=tag, tag_kind=tag_kind)
        log(f"parity {art.id}@{platform_id}: {ref_name} unsupported, pie answered {sum(1 for t in pie_texts if t)}/{len(pie_texts)} -> {where}")
        return summary

    # 3. compare over the answer positions
    starts = [max(0, len(s) - len(tok.encode(t, add_special_tokens=False))) for s, t in zip(ref_scored, ref_texts, strict=True)]
    summary.update(kl.compare(ref_scored, pie_scored, starts))
    summary["exact_match"] = kl.exact_match(ref_texts, pie_texts)
    # the site's quality table reads score/n/ci95: score is top-1 agreement over every answer position
    summary["score"], summary["n"] = summary["top1_agree"], summary["positions"]
    summary["correct"] = round((summary["top1_agree"] or 0) * summary["positions"])
    summary["ci95"] = [summary["score"] or 0, summary["score"] or 0]
    summary["samples"] = [{"id": i, "ref": a, "pie": b} for i, (a, b) in enumerate(zip(ref_texts, pie_texts, strict=True))]
    (out_dir / f"{art.id}-{platform_id}.json").write_text(json.dumps(summary, indent=1))
    where = Store(store_dir).write_quality(summary, tag=tag, tag_kind=tag_kind)
    log(f"parity {art.id}@{platform_id}: KL mean {summary['kl_mean']}, top-1 {summary['top1_agree']}, exact {summary['exact_match']:.2f} -> {where}")
    return summary


#: requests in flight on both engines in an accuracy run: the same for pie and vLLM
ACCURACY_CONCURRENCY = 16


def run_accuracy(artifact_id: str, platform_id: str, tasks: list[str], n: int, *, pie_root: Path, matrix_dir: str = "matrix", store_dir: str | None = None,
                 tag: str | None = None, tag_kind: str | None = None, out_dir: Path = Path("parity-out"), vllm_pin: str | None = None, log=print) -> list[dict]:
    """The catalog's question sets on the full model, vLLM then pie on the same node: same rendered prompts (the checkpoint's
    chat template, thinking off), greedy, same answer parser, same concurrency. Rows: ``<id>@vllm`` (engine vllm) and ``<id>`` (pie)."""
    from pie_evals.node.baselines import ensure_baseline
    from pie_evals.node.engines import get_engine
    from pie_evals.node.engines.recipes import load_recipe
    from pie_evals.node.importer import ensure_artifact
    from pie_evals.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_evals.plan.matrix import Matrix
    from pie_evals.results.store import Store

    from .tasks import wilson

    m = Matrix.load(matrix_dir)
    art, plat = m.artifacts[artifact_id], m.platforms[platform_id]
    backend, tp = str(plat.backend), max(1, int(plat.count))
    mode = next((md for md in m.modes.values() if int(md.tp) == tp and not md.spec_dec and not md.extra), None)
    base = m.workloads["c32"]
    workload = base.model_copy(update={"params": {**base.params, "concurrency": ACCURACY_CONCURRENCY, "prefill": 3072, "decode": 1024}})
    out_dir.mkdir(parents=True, exist_ok=True)
    busy = device_idle(backend)
    if busy:
        raise RuntimeError(f"device not idle before the run: {busy}")
    snapshot = ensure_snapshot(art, hf_cache_dir(), pie_root=pie_root, python=os.environ.get("PIE_PY", "python3"), download=True, log=log)
    sets = {}
    for t in tasks:
        items = TASKS[t][0](n)
        sets[t] = (items, _render(snapshot, [i.prompt for i in items]))
    answers: dict[str, dict[str, list[str]]] = {"vllm": {}, "pie": {}}
    versions = {}

    recipe = load_recipe("vllm", "competitive", plat, workload, family=art.family)
    recipe["pin"] = vllm_pin or os.environ.get("PARITY_VLLM_PIN") or m.engines["vllm"].pin
    if not os.environ.get("VLLM_PY"):
        ensure_baseline("vllm", recipe["pin"], backend=backend, log=log)
    ref = get_engine("vllm")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=recipe)
    versions["vllm"] = ref.version()
    srv = vllm_server(ref, snapshot, tp, out_dir / f"{art.id}-acc-vllm.log", max_seqs=ACCURACY_CONCURRENCY)
    try:
        model = srv.wait(5400)
        for t, (_items, rendered) in sets.items():
            answers["vllm"][t] = kl.greedy(srv.url, model, rendered, TASKS[t][2], parallel=ACCURACY_CONCURRENCY)
            log(f"accuracy {art.id}@{platform_id}: vllm {t} done")
    except Exception as e:  # noqa: BLE001 — vLLM that cannot serve the model is a crossed-out cell; pie still runs
        versions["vllm_unsupported"] = _reason(e, out_dir, f"{art.id}-acc", "vllm")
        log(f"accuracy {art.id}@{platform_id}: vllm cannot run it: {versions['vllm_unsupported']}")
    finally:
        srv.stop()

    busy = device_idle(backend)
    if busy:
        raise RuntimeError(f"device not idle between engines: {busy}")
    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    model_path = ensure_artifact(art, snapshot, pie_root / "target/release/pie", commit, log=log)
    precipe = load_recipe("pie", "default", plat, workload, family=art.family)
    precipe["snapshot_dir"] = str(model_path)
    pie = get_engine("pie")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=precipe)
    versions["pie"] = commit[:12]
    srv = pie_server(pie, workload, out_dir / f"{art.id}-acc-pie.log")
    try:
        model = srv.wait(5400)
        for t, (_items, rendered) in sets.items():
            answers["pie"][t] = kl.greedy(srv.url, model, rendered, TASKS[t][2], parallel=ACCURACY_CONCURRENCY)
            log(f"accuracy {art.id}@{platform_id}: pie {t} done")
    finally:
        srv.stop()

    rows = []
    store = Store(store_dir)
    for engine, by_task in answers.items():
        for t, texts in by_task.items():
            items = sets[t][0]
            scores = [TASKS[t][1](i, x) for i, x in zip(items, texts, strict=True)]
            correct = sum(scores)
            lo, hi = wilson(correct, len(scores))
            row = {"artifact": art.id if engine == "pie" else f"{art.id}@vllm", "model": art.id, "engine": engine, "label": "pie" if engine == "pie" else "vLLM",
                   "checkpoint": art.base_model, "scheme": str(art.scheme), "platform": platform_id, "tp": tp, "task": t, "n": len(scores), "correct": correct,
                   "score": correct / len(scores) if scores else None, "ci95": [lo, hi], "version": versions[engine], "empty": sum(1 for x in texts if not x),
                   "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "samples": [{"id": i.id, "score": sc, "text": x} for i, sc, x in zip(items, scores, texts, strict=True)]}
            store.write_quality(row, tag=tag, tag_kind=tag_kind)
            log(f"accuracy {row['artifact']} {t}: {correct:.0f}/{len(scores)} = {row['score']:.1%}")
            rows.append(row)
    if "vllm_unsupported" in versions:
        for t in tasks:
            store.write_quality({"artifact": f"{art.id}@vllm", "model": art.id, "engine": "vllm", "label": "vLLM", "task": t, "platform": platform_id,
                                 "score": None, "n": 0, "correct": 0, "ci95": [0, 0], "ref_unsupported": versions["vllm_unsupported"],
                                 "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "samples": []}, tag=tag, tag_kind=tag_kind)
    return rows
