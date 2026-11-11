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

from pie_bench.node.build import bench_dir
from pie_bench.paths import MATRIX

from . import kl
from .run import _render, _tokenizer
from .tasks import TASKS

PER_TASK = 8
ANSWER_TOKENS = 256
PARITY_TASKS = ("gsm8k", "mmlu", "arc", "math500", "ifeval")
WORKLOAD = "lc-2k-128"
TEXTS_DIR = "parity-texts"
KL_PASS = 0.15
SELF_TIMES = 2


def first_token_inconclusive(kl_mean: float | None, self_kl: float | None) -> bool:
    return kl_mean is not None and self_kl is not None and kl_mean < SELF_TIMES * self_kl


def saved_texts(matrix_dir: str, artifact_id: str, rendered: list[str]) -> list[str] | None:
    p = Path(matrix_dir) / TEXTS_DIR / f"{artifact_id}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    ok = d.get("prompts") == kl.texts_hash(rendered) and d.get("answer_tokens") == ANSWER_TOKENS and len(d.get("texts") or []) == len(rendered)
    return d["texts"] if ok else None


FIRST_REF_DIR = "first-token-ref"


def saved_first_ref(matrix_dir: str, artifact_id: str, rendered: list[str]) -> dict | None:
    for aid in dict.fromkeys([artifact_id, artifact_id.removesuffix("-tpu"), artifact_id.removesuffix("-bf16")]):
        p = Path(matrix_dir) / FIRST_REF_DIR / f"{aid}.json"
        if p.exists():
            d = json.loads(p.read_text())
            if d.get("prompts") == kl.texts_hash(rendered) and len(d.get("last") or []) == len(rendered):
                return {**d, "artifact": aid}
    return None


def prompts(log=print) -> list[str]:
    out = []
    for t in PARITY_TASKS:
        try:
            out += [i.prompt for i in TASKS[t][0](PER_TASK)]
        except Exception as e:
            log(f"parity: {t} questions unavailable ({type(e).__name__}); skipped")
    return out


def device_idle(backend: str, grace_s: float = 60.0) -> str | None:
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
    except Exception:
        return None
    return None


class Server:

    def __init__(self, argv: list[str], env: dict, cwd: str | None, log_path: Path, url: str | None = None):
        self.log_path = log_path
        self.fh = log_path.open("w")
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
            except Exception:
                if time.monotonic() > deadline:
                    raise RuntimeError(f"server never answered /v1/models: {self.tail()}") from None

    def tail(self, n: int = 40) -> str:
        try:
            return "".join(self.log_path.read_text().splitlines(True)[-n:])
        except OSError:
            return ""

    def stop(self) -> None:
        def group(sig) -> bool:
            try:
                os.killpg(self.proc.pid, sig)
                return True
            except (ProcessLookupError, PermissionError):
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
    from pie_bench.node.engines.served import free_port

    return free_port()


def vllm_server(engine, snapshot: Path, tp: int, log_path: Path, max_seqs: int = 1, extra: list[str] | None = None) -> Server:
    port = _free_port()
    gmu = engine.recipe.get("gpu_mem_util", 0.90) or 0.90
    argv = [engine.python, "-m", "vllm.entrypoints.openai.api_server", "--model", str(snapshot), "--port", str(port), "--host", "127.0.0.1",
            "--tensor-parallel-size", str(tp), "--max-model-len", "4096", "--max-logprobs", str(kl.TOPK), "--gpu-memory-utilization", str(gmu),
            "--no-enable-prefix-caching", "--trust-remote-code", "--max-num-seqs", str(max_seqs), *(extra or [])]
    if engine.artifact.kv_dtype and str(engine.artifact.kv_dtype) not in ("bf16", "auto", "fp16"):
        argv += ["--kv-cache-dtype", str(engine.artifact.kv_dtype)]
    if engine.recipe.get("attention_backend"):
        argv += ["--attention-backend", str(engine.recipe["attention_backend"])]
    engine.recipe.setdefault("snapshot_dir", str(snapshot))
    env = engine.process_env(*([engine._tpu_env()] if str(engine.platform.backend) == "xla" else []))
    if str(engine.platform.backend) == "cuda":
        env.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    cfg = json.loads((snapshot / "config.json").read_text()) if (snapshot / "config.json").exists() else {}
    if "vision_config" in cfg and "hf_overrides" not in env.get("PIE_BENCH_VLLM_ENGINE_ARGS", ""):
        argv += ["--limit-mm-per-prompt", json.dumps({"image": 0, "video": 0})]
    keys = {**cfg, **(cfg.get("text_config") or {})}
    if str(engine.platform.backend) == "xla" and str(engine.artifact.scheme) == "mxfp4":
        env.setdefault("MOE_REQUANTIZE_BLOCK_SIZE", "32")
        env.setdefault("MOE_REQUANTIZE_WEIGHT_DTYPE", "int8")
    if str(engine.platform.backend) == "xla" and str(engine.artifact.family).startswith("gemma4"):
        env.setdefault("RPA_V3_PREFILL_BLOCK_SIZES", "128,512,128,256")
        env.setdefault("RPA_V3_MIXED_BLOCK_SIZES", "128,512,128,256")
    if str(engine.platform.backend) == "xla" and ("kv_lora_rank" in keys or str(keys.get("model_type", "")).startswith("deepseek")):
        env["NEW_MODEL_DESIGN"] = "1"
        argv += ["--additional-config", json.dumps({"sharding": {"sharding_strategy": {"enable_dp_attention": True}}})]
    return Server(argv, env, None, log_path, url=f"http://127.0.0.1:{port}")


def pie_server(engine, workload, log_path: Path, prewarm: bool = True) -> Server:
    from pie_bench.node.workloads import common_args_for

    argv = engine.build_argv(workload, common_args_for(workload), log_path.with_suffix(".json"))
    script = Path(__file__).resolve().parents[1] / "node" / "engines" / "scripts" / "parity_pie_serve.py"
    i = next(k for k, a in enumerate(argv) if a.endswith("pie_client.py"))
    argv = [argv[0], str(script), *argv[i + 1:]]
    env = engine.process_env()
    env["PYTHONPATH"] = ":".join([str(bench_dir()), env.get("PYTHONPATH", "")])
    if str(engine.platform.backend) == "xla":
        env["PIE_XLA_PREWARM"] = "1" if prewarm and os.environ.get("PARITY_PIE_PREWARM", "1") == "1" else "0"
        env.setdefault("PIE_SILENCE_TIMEOUT", "7200s")
    return Server(argv, env, str(bench_dir()), log_path)


def mlx_python(vlm: bool) -> str:
    return os.environ.get("MLX_VLM_PY" if vlm else "MLX_PY", sys.executable)


def mlx_side(snapshot: Path, rendered: list[str], greedy: bool, log_path: Path, vlm: bool = False, unfused: bool = False) -> tuple[list[str], list[list[dict[int, float]]]]:
    script = Path(__file__).resolve().parents[1] / "node" / "engines" / "scripts" / ("parity_mlxvlm.py" if vlm else "parity_mlx.py")
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = Path(tmp) / "in.json", Path(tmp) / "out.json"
        inp.write_text(json.dumps({"prompts": rendered, "max_tokens": ANSWER_TOKENS, "topk": kl.TOPK, "greedy": greedy, "unfused": unfused}))
        with log_path.open("w") as fh:
            subprocess.run([mlx_python(vlm), str(script), str(snapshot), str(inp), str(out)], stdout=fh, stderr=subprocess.STDOUT, check=True, timeout=6 * 3600)
        d = json.loads(out.read_text())
    return d["texts"], [[{int(k): v for k, v in pos.items()} for pos in t] for t in d["scored"]]


def _reason(e: Exception, out_dir: Path, art_id: str, ref_name: str) -> str:
    for log_path in sorted(out_dir.glob(f"{art_id}-{'vllm' if ref_name == 'vllm' else 'mlx'}*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        lines = [ln.strip() for ln in log_path.read_text(errors="replace").splitlines() if re.search(r"(Error|not supported|unsupported)", ln)
                 and not re.search(r"(Engine core initialization failed|Error raised in subprocess|ValidationError: 1 validation error|Pin memory is not supported|\braise \w|File \x22)", ln)]
        if lines:
            return lines[-1][:400]
    return f"{type(e).__name__}: {str(e).strip().splitlines()[-1][:400] if str(e).strip() else ''}"


def _reference(ref_name, art, plat, workload, mode, snapshot, rendered, tp, backend, pie_root, m, vllm_pin, summary, out_dir, log, texts=None,
               again: bool = False):
    from pie_bench.node.engines import get_engine
    from pie_bench.node.engines.recipes import load_recipe

    if ref_name == "vllm":
        from pie_bench.node.baselines import ensure_baseline

        recipe = load_recipe("vllm", "competitive", plat, workload, family=art.family)
        pin = vllm_pin or os.environ.get("PARITY_VLLM_PIN") or m.engines["vllm"].pin
        if pin:
            recipe["pin"] = pin
            if not os.environ.get("VLLM_PY"):
                ensure_baseline("vllm", pin, backend=backend, log=log)
        ref_engine = get_engine("vllm")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=recipe)
        summary["ref_version"] = ref_engine.version()
        srv = vllm_server(ref_engine, snapshot, tp, out_dir / f"{art.id}-vllm{'-eager' if again else ''}.log", extra=["--enforce-eager"] if again else None)
        try:
            model = srv.wait(3600)
            bos = getattr(_tokenizer(snapshot), "bos_token", None)
            extra = {"add_special_tokens": False} if bos and rendered and all(r.startswith(bos) for r in rendered) else None
            ref_texts = texts if texts is not None else kl.greedy(srv.url, model, rendered, ANSWER_TOKENS, parallel=1, extra=extra)
            ref_scored = kl.scored(srv.url, model, [r + t for r, t in zip(rendered, ref_texts, strict=True)], parallel=1, extra=extra)
        finally:
            srv.stop()
        return ref_texts, ref_scored
    vlm = art.family == "qwen4_exp"
    pkg = "mlx_vlm" if vlm else "mlx_lm"
    version = subprocess.run([mlx_python(vlm), "-c", f"import {pkg}; print({pkg}.__version__)"], capture_output=True, text=True).stdout.strip()
    summary["ref_version"] = f"mlx-vlm {version}" if vlm else version
    ref_texts = texts if texts is not None else mlx_side(snapshot, rendered, True, out_dir / f"{art.id}-mlx-greedy.log", vlm)[0]
    _, ref_scored = mlx_side(snapshot, [r + t for r, t in zip(rendered, ref_texts, strict=True)], False,
                             out_dir / f"{art.id}-mlx-score{'-unfused' if again else ''}.log", vlm, unfused=again)
    return ref_texts, ref_scored


def reference_spread(ref_scored, again_scored, expect: list[int], how: str) -> dict:
    s = kl.last_position(ref_scored, again_scored, expect)
    return {"ref_self_kl": s["kl_mean"], "ref_self_top1": s["top1_agree"], "ref_self": how}


def run_parity(artifact_id: str, platform_id: str, *, pie_root: Path, matrix_dir: str = str(MATRIX), store_dir: str | None = None,
               tag: str | None = None, tag_kind: str | None = None, out_dir: Path = Path("parity-out"), vllm_pin: str | None = None, log=print,
               first_token: bool | None = None, carry: dict | None = None) -> dict:
    from pie_bench.node.engines import get_engine
    from pie_bench.node.engines.recipes import load_recipe
    from pie_bench.node.importer import ensure_artifact, needs_import
    from pie_bench.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_bench.plan.matrix import Matrix
    from pie_bench.results.store import Store

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
    first = os.environ.get("PARITY_FIRST_TOKEN") == "1" if first_token is None else first_token
    rendered = kl.gibberish(tok) if first else _render(snapshot, prompts(log))
    t0 = time.monotonic()
    ref_name = "mlxlm" if backend == "metal" else "vllm"
    summary: dict = {"artifact": art.id, "model": art.id, "engine": "pie", "ref_engine": ref_name, "platform": platform_id,
                     "task": f"parity@{platform_id}", "checkpoint": art.base_model, "scheme": str(art.scheme), "tp": tp,
                     "miniature": str(art.kind) == "miniature", "layers": getattr(art.miniature, "layers", None) if art.miniature else None,
                     "prompts": len(rendered), "answer_tokens": 1 if first else ANSWER_TOKENS}
    if first:
        summary["mode"] = "first_token"
    summary.update(carry or {})

    ref_texts = ref_scored = None
    texts = [""] * len(rendered) if first else saved_texts(matrix_dir, art.id, rendered)
    summary["ref_texts"] = "saved" if texts is not None else "greedy"
    try:
        if first and os.environ.get("PARITY_SAVED_REF") == "1" and saved_first_ref(matrix_dir, art.id, rendered):
            raise RuntimeError("PARITY_SAVED_REF=1: this device's reference is not trusted for this model, the saved one scores it")
        ref_texts, ref_scored = _reference(ref_name, art, plat, workload, mode, snapshot, rendered, tp, backend, pie_root, m, vllm_pin, summary, out_dir, log, texts)
        if texts is None and not first:
            (out_dir / f"{art.id}.json").write_text(json.dumps({"prompts": kl.texts_hash(rendered), "answer_tokens": ANSWER_TOKENS,
                                                                 "ref_engine": ref_name, "ref_version": summary.get("ref_version"),
                                                                 "platform": platform_id, "texts": ref_texts}, indent=1))
        if first:
            (out_dir / FIRST_REF_DIR).mkdir(parents=True, exist_ok=True)
            (out_dir / FIRST_REF_DIR / f"{art.id}.json").write_text(json.dumps({
                "prompts": kl.texts_hash(rendered), "ref_engine": ref_name, "ref_version": summary.get("ref_version"), "platform": platform_id,
                "tokens": [len(x) for x in ref_scored], "last": [{str(k): v for k, v in (x[-1] if x else {}).items()} for x in ref_scored]}))
            if os.environ.get("PARITY_REF_ONLY") == "1":
                log(f"first-token {art.id}@{platform_id}: reference saved, pie not run")
                return summary
    except Exception as e:
        summary["ref_unsupported"] = str(e) if str(e).startswith("PARITY_SAVED_REF=1") else _reason(e, out_dir, art.id, ref_name)
        log(f"parity {art.id}@{platform_id}: {ref_name} cannot run it: {summary['ref_unsupported']}")
        saved = saved_first_ref(matrix_dir, art.id, rendered) if first else None
        if saved:
            ref_scored = [[{}] * (n - 1) + [{int(k): v for k, v in last.items()}] for n, last in zip(saved["tokens"], saved["last"], strict=True)]
            ref_texts = texts
            summary.update(ref_local_unsupported=summary.pop("ref_unsupported"), ref_engine=saved["ref_engine"], ref_version=saved.get("ref_version"),
                           ref_platform=saved["platform"], ref_artifact=saved["artifact"])
            log(f"parity {art.id}@{platform_id}: the saved {saved['ref_engine']} reference from {saved['platform']} ({saved['artifact']}) instead")
    log(f"parity {art.id}@{platform_id}: reference {ref_name} done in {(time.monotonic() - t0) / 60:.1f} min")

    busy = device_idle(backend)
    if busy:
        raise RuntimeError(f"device not idle between engines: {busy}")

    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    model_path = snapshot
    if needs_import(art) or tp > 1 or backend == "xla":
        imported = art
        if backend == "xla" and art.pie_sku and re.search(r"[0-9]a[48](g[0-9]+)?-", art.pie_sku):
            imported = art.model_copy(update={"pie_sku": None})
        model_path = ensure_artifact(imported, snapshot, pie_root / "target/release/pie", commit, log=log)
    precipe = load_recipe("pie", "default", plat, workload, family=art.family, artifact=art.id)
    precipe["snapshot_dir"] = str(model_path)
    if backend == "xla":
        precipe["gpu_mem_util"] = precipe.pop("parity_gpu_mem_util", None) or min(float(precipe.get("gpu_mem_util") or 0.90), 0.75)
        precipe["max_forward_tokens"] = int(precipe.pop("parity_max_forward_tokens", None) or 512)
        precipe["engine_option"] = {**(precipe.get("engine_option") or {}), "max_state_slots": 4}
    pie_engine = get_engine("pie")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=precipe)
    srv = pie_server(pie_engine, workload.model_copy(update={"params": {**workload.params, "concurrency": 64}}), out_dir / f"{art.id}-pie.log")
    try:
        model = srv.wait(3600)
        pie_texts = [""] * len(rendered) if first else kl.greedy(srv.url, model, rendered, ANSWER_TOKENS, parallel=1)
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

    if first:
        expect = [len(tok.encode(r, add_special_tokens=False)) for r in rendered]
        summary.update(kl.last_position(ref_scored, pie_scored, expect))
        local = "ref_platform" not in summary and (ref_name == "mlxlm" or backend in ("cuda", "rocm"))
        if local and (summary.get("kl_mean") or 0) >= KL_PASS and os.environ.get("PARITY_REF_SPREAD", "1") == "1":
            busy = device_idle(backend)
            if busy:
                raise RuntimeError(f"device not idle before the reference's second pass: {busy}")
            _, again = _reference(ref_name, art, plat, workload, mode, snapshot, rendered, tp, backend, pie_root, m, vllm_pin, {}, out_dir, log,
                                  ref_texts, again=True)
            summary.update(reference_spread(ref_scored, again, expect, "vLLM --enforce-eager" if ref_name == "vllm" else "mlx-lm, fused kernels off"))
            log(f"first-token {art.id}@{platform_id}: {ref_name} against itself ({summary['ref_self']}): KL {summary['ref_self_kl']}")
            if first_token_inconclusive(summary["kl_mean"], summary["ref_self_kl"]):
                (out_dir / f"{art.id}-{platform_id}-first-token.json").write_text(json.dumps(summary, indent=1))
                log(f"first-token {art.id}@{platform_id}: pie within {SELF_TIMES}x the reference's own spread; checked on the answers instead")
                carry = {"first_kl_mean": summary["kl_mean"], "first_top1": summary["top1_agree"], "first_self_kl": summary["ref_self_kl"],
                         "first_self_top1": summary["ref_self_top1"], "first_self": summary["ref_self"]}
                return run_parity(artifact_id, platform_id, pie_root=pie_root, matrix_dir=matrix_dir, store_dir=store_dir, tag=tag, tag_kind=tag_kind,
                                  out_dir=out_dir, vllm_pin=vllm_pin, log=log, first_token=False, carry=carry)
        if summary.get("first_token_topk"):
            summary["first_token_topk"]["tokens"] = [tok.decode([t]) for t in summary["first_token_topk"]["ids"]]
        summary["score"], summary["n"] = summary["top1_agree"], summary["positions"]
        summary["correct"] = round((summary["top1_agree"] or 0) * summary["positions"])
        summary["ci95"] = [summary["score"] or 0, summary["score"] or 0]
        summary["exact_match"] = summary["top1_agree"]
        summary["samples"] = [{"id": i, "prompt": r} for i, r in enumerate(rendered)]
        (out_dir / f"{art.id}-{platform_id}.json").write_text(json.dumps(summary, indent=1))
        where = Store(store_dir).write_quality(summary, tag=tag, tag_kind=tag_kind)
        log(f"first-token {art.id}@{platform_id}: KL mean {summary['kl_mean']}, top-1 {summary['top1_agree']} over {summary['positions']} prompts, "
            f"{summary['prompt_tokens_mismatch']} tokenized apart -> {where}")
        return summary
    starts = [max(0, len(s) - len(tok.encode(t, add_special_tokens=False))) for s, t in zip(ref_scored, ref_texts, strict=True)]
    summary.update(kl.compare(ref_scored, pie_scored, starts))
    summary["exact_match"] = kl.exact_match(ref_texts, pie_texts)
    summary["score"], summary["n"] = summary["top1_agree"], summary["positions"]
    summary["correct"] = round((summary["top1_agree"] or 0) * summary["positions"])
    summary["ci95"] = [summary["score"] or 0, summary["score"] or 0]
    summary["samples"] = [{"id": i, "ref": a, "pie": b} for i, (a, b) in enumerate(zip(ref_texts, pie_texts, strict=True))]
    (out_dir / f"{art.id}-{platform_id}.json").write_text(json.dumps(summary, indent=1))
    where = Store(store_dir).write_quality(summary, tag=tag, tag_kind=tag_kind)
    log(f"parity {art.id}@{platform_id}: KL mean {summary['kl_mean']}, top-1 {summary['top1_agree']} (decisive {summary.get('top1_agree_decisive')}, ref top-1 p {summary.get('ref_top1_p')}), exact {summary['exact_match']:.2f} -> {where}")
    return summary


ACCURACY_CONCURRENCY = int(os.environ.get("PARITY_ACCURACY_CONCURRENCY") or 16)


def run_accuracy(artifact_id: str, platform_id: str, tasks: list[str], n: int, *, pie_root: Path, matrix_dir: str = str(MATRIX), store_dir: str | None = None,
                 tag: str | None = None, tag_kind: str | None = None, out_dir: Path = Path("parity-out"), vllm_pin: str | None = None, log=print) -> list[dict]:
    from pie_bench.node.baselines import ensure_baseline
    from pie_bench.node.engines import get_engine
    from pie_bench.node.engines.recipes import load_recipe
    from pie_bench.node.importer import ensure_artifact
    from pie_bench.node.snapshots import ensure_snapshot, hf_cache_dir
    from pie_bench.plan.matrix import Matrix
    from pie_bench.results.store import Store

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

    engines = [e for e in os.environ.get("PARITY_ENGINES", "vllm,pie").split(",") if e]
    done = {d for d in os.environ.get("PARITY_DONE", "").split(",") if d}
    todo = {e: [t for t in tasks if f"{art.id if e == 'pie' else art.id + '@vllm'}/{t}" not in done] for e in ("vllm", "pie")}
    engines = [e for e in engines if todo[e]]
    rows = []
    store = Store(store_dir)

    def emit(engine: str, t: str, texts: list[str]) -> None:
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
    req = {"timeout": 7200.0, "retries": 2} if backend == "xla" else {}
    if "vllm" in engines:
        recipe = load_recipe("vllm", "competitive", plat, workload, family=art.family)
        recipe["pin"] = vllm_pin or os.environ.get("PARITY_VLLM_PIN") or m.engines["vllm"].pin
        if not os.environ.get("VLLM_PY"):
            ensure_baseline("vllm", recipe["pin"], backend=backend, log=log)
        ref = get_engine("vllm")(pie_root=pie_root, artifact=art, platform=plat, mode=mode, recipe=recipe)
        versions["vllm"] = ref.version()
        srv = vllm_server(ref, snapshot, int(os.environ.get("PARITY_VLLM_TP") or tp), out_dir / f"{art.id}-acc-vllm.log", max_seqs=ACCURACY_CONCURRENCY)
        try:
            model = srv.wait(5400)
            for t, (_items, rendered) in sets.items():
                if t not in todo["vllm"]:
                    continue
                answers["vllm"][t] = kl.greedy(srv.url, model, rendered, TASKS[t][2], parallel=ACCURACY_CONCURRENCY)
                log(f"accuracy {art.id}@{platform_id}: vllm {t} done")
                emit("vllm", t, answers["vllm"][t])
        except Exception as e:
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
    pie_error = None
    if "pie" in engines:
        srv = pie_server(pie, workload, out_dir / f"{art.id}-acc-pie.log")
        try:
            try:
                model = srv.wait(5400)
            except RuntimeError:
                if backend != "xla":
                    raise
                log(f"accuracy {art.id}@{platform_id}: pie did not come up with prewarm, again without: {srv.tail(5)}")
                srv.stop()
                srv = pie_server(pie, workload, out_dir / f"{art.id}-acc-pie-noprewarm.log", prewarm=False)
                model = srv.wait(5400)
            fresh = False
            for t, (_items, rendered) in sets.items():
                if t not in todo["pie"]:
                    continue
                if fresh and os.environ.get("PARITY_PIE_RESTART") == "1":
                    srv.stop()
                    srv = pie_server(pie, workload, out_dir / f"{art.id}-acc-pie-{t}.log")
                    model = srv.wait(5400)
                fresh = True
                answers["pie"][t] = kl.greedy(srv.url, model, rendered, TASKS[t][2], parallel=ACCURACY_CONCURRENCY, **req)
                log(f"accuracy {art.id}@{platform_id}: pie {t} done")
                emit("pie", t, answers["pie"][t])
        except Exception as e:
            pie_error = e
        finally:
            srv.stop()

    if "vllm_unsupported" in versions:
        for t in tasks:
            store.write_quality({"artifact": f"{art.id}@vllm", "model": art.id, "engine": "vllm", "label": "vLLM", "task": t, "platform": platform_id,
                                 "score": None, "n": 0, "correct": 0, "ci95": [0, 0], "ref_unsupported": versions["vllm_unsupported"],
                                 "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "samples": []}, tag=tag, tag_kind=tag_kind)
    if pie_error is not None:
        raise pie_error
    return rows
