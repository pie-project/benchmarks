"""Engines in a browser tab on WebGPU (the ``webgpu`` platforms: headless Chrome on the pod's GPU).

``browser/bridge.mjs`` boots Chromium (Playwright's build) with WebGPU on Dawn's Vulkan backend, loads one engine
in a tab and answers ``/health`` and ``/run``; ``scripts/browser_bench.py`` is the client, with openai_bench.py's
prompts and summary, and every request is timed in the tab. Three engines run there:

- ``webllm``: mlc-ai/web-llm (pinned in browser/package.json) on an -MLC build and its WebGPU model library;
- ``llamacpp-webgpu``: llama.cpp at the native rows' release, built by emscripten with ggml-webgpu
  (browser/llamacpp/build.sh), on the GGUF the native llama.cpp rows load;
- ``pie`` on a webgpu platform: @pie-project/server-web built at the job's pie commit, on the .wgpu.zt the
  wgpu build of ``pie model import`` writes, each request one process of text-completion-bench.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from pie_evals.schema import EngineName, ErrorClass

from .base import EngineLaunchError, register
from .llamacpp import LlamacppEngine
from .served import ServedEngine
from .shape import hf_snapshot_dir

BROWSER = Path(__file__).resolve().parent / "browser"
SCRIPT = Path(__file__).resolve().parent / "scripts" / "browser_bench.py"


def _cache() -> Path:
    from pie_evals.node.baselines import cache_root

    return cache_root()


def ensure_harness(log=print) -> str:
    """node, the bridge's node_modules (Playwright and WebLLM at the pins in package.json) and Playwright's Chromium."""
    node = shutil.which("node")
    if not node:
        raise EngineLaunchError(ErrorClass.LOAD_FAIL, "node is not installed: the browser engines need Node.js for the bridge")
    lock = BROWSER / "node_modules" / ".package-lock.json"
    if not lock.exists():
        log("browser: npm install (playwright, web-llm)")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=BROWSER, check=True, timeout=1800)
    stamp = BROWSER / "node_modules" / ".chromium-installed"
    if not stamp.exists():
        log("browser: installing Playwright's Chromium and its system libraries")
        subprocess.run(["npx", "playwright", "install", "--with-deps", "chromium"], cwd=BROWSER, check=True, timeout=3600)
        stamp.write_text("ok\n")
    return node


def _link(dst: Path, src: Path) -> None:
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src)


class BrowserEngine(ServedEngine):
    """One engine in a tab: subclasses name the page engine and stage its files."""

    #: page/engines/<page_engine>.mjs
    page_engine: str = ""
    health_path = "/health"
    # every engine here pins the output length itself (WebLLM's ignore_eos, llama.cpp's slots, pie's inferlet)
    exact_length = "ignore_eos"

    def script_path(self) -> Path:
        return SCRIPT

    def engine_args(self, workload) -> list[str]:
        args = super().engine_args(workload)
        # the bench client sends every request in one job: a request may wait behind the whole batch
        return args

    def files_dir(self) -> Path:
        d = _cache() / "browser-files" / f"{self.page_engine}-{re.sub(r'[^A-Za-z0-9._-]', '_', self.artifact.id)}-{os.getpid()}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        """Link the engine's files under ``files`` (served at /files/) and return the page's options."""
        raise NotImplementedError

    def default_env(self) -> dict[str, str]:
        root = _cache() / "browser-profiles"
        root.mkdir(parents=True, exist_ok=True)
        return {"BROWSER_PROFILE_ROOT": str(root)}

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        node = ensure_harness()
        files = self.files_dir()
        options = self.stage(files, max(1, slots), context)
        return [node, str(BROWSER / "bridge.mjs"), "--engine", self.page_engine, "--port", str(port), "--files", str(files), "--options", json.dumps(options)]

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        out = super().counters_from_summary(summary)
        try:
            with urllib.request.urlopen((self.server_url or "") + "/info", timeout=5) as r:
                info = json.loads(r.read())
            lim = (info.get("adapter") or {}).get("limits") or {}
            for k in ("maxBufferSize", "maxStorageBufferBindingSize"):
                if lim.get(k):
                    out[f"webgpu_{k}"] = float(lim[k])
            if info.get("load_s") is not None:
                out["tab_load_s"] = float(info["load_s"])
        except Exception:  # noqa: BLE001 — the counters are a footnote
            pass
        return out

    def leftover_process_names(self) -> list[str]:
        return ["bridge.mjs", "chrome", "headless_shell"]

    def stall_s(self) -> int:
        # the work runs in Chrome's renderer and GPU processes, not in the watched bridge (node idles while a tab
        # computes): the bridge itself abandons a batch that stops making progress (BROWSER_STALL_S, 300 s)
        return int(self.recipe.get("stall_s") or 3600)


@register
class WebllmEngine(BrowserEngine):
    """WebLLM: the -MLC weights (the artifact's snapshot) and the model library the recipe names, both from local disk."""

    name = EngineName.WEBLLM
    page_engine = "webllm"

    def model_arg(self) -> str:
        # the bench client renders the chat template with the original checkpoint's tokenizer
        # (the -MLC repo ships the same tokenizer.json, but no Hugging Face chat template)
        return self.artifact.tokenizer_from or self.artifact.base_model

    def model_lib(self) -> Path:
        url = str(self.recipe.get("model_lib") or "")
        if not url:
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"webllm: no model_lib for {self.artifact.id} in recipes/webllm.yaml")
        d = _cache() / "webllm-libs"
        d.mkdir(parents=True, exist_ok=True)
        path = d / url.rsplit("/", 1)[-1]
        if not path.exists():
            tmp = path.with_suffix(".part")
            urllib.request.urlretrieve(url, tmp)
            tmp.replace(path)
        return path

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        snap = Path(self.recipe.get("snapshot_dir") or "")
        if not (snap / "mlc-chat-config.json").exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"webllm: {snap} is not an MLC build (no mlc-chat-config.json)")
        _link(files / "model" / "resolve" / "main", snap)
        _link(files / "lib.wasm", self.model_lib())
        overrides = {"context_window_size": max(int(self.recipe.get("context_window_size") or 0), context)}
        if self.recipe.get("prefill_chunk_size"):
            overrides["prefill_chunk_size"] = int(self.recipe["prefill_chunk_size"])
        return {"model_id": self.artifact.id, "model_url": "/files/model/", "model_lib": "/files/lib.wasm", "overrides": overrides}

    def version(self) -> str:
        pkg = BROWSER / "node_modules" / "@mlc-ai" / "web-llm" / "package.json"
        try:
            return json.loads(pkg.read_text())["version"]
        except (OSError, ValueError, KeyError):
            return str(self.recipe.get("pin") or "unknown")


@register
class LlamacppWebgpuEngine(BrowserEngine):
    """llama.cpp's WebGPU backend in the tab, at the native llama.cpp rows' release, on the same GGUF."""

    name = EngineName.LLAMACPP_WEBGPU
    page_engine = "llamacpp"

    def model_arg(self) -> str:
        return LlamacppEngine.model_arg(self)  # the tokenizer the native llama.cpp rows render with

    def build_dir(self) -> Path:
        tag = str(self.recipe.get("pin") or "b11312")
        import hashlib

        src = hashlib.sha256(b"".join((BROWSER / "llamacpp" / f).read_bytes() for f in ("lw.cpp", "build.sh"))).hexdigest()[:8]
        out = _cache() / "llamacpp-webgpu" / f"{tag}-{src}"  # a change to the driver or its build is a new build
        if not (out / "lw.wasm").exists():
            subprocess.run(["bash", str(BROWSER / "llamacpp" / "build.sh"), str(out), tag], check=True, timeout=7200)
        return out

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        _link(files / "model.gguf", LlamacppEngine.gguf_path(self))
        _link(files / "lw", self.build_dir())
        r = self.recipe
        return {
            "module_url": "/files/lw/lw.mjs", "model_url": "/files/model.gguf",
            # llama-server's shape: one slot per request in flight, each with the whole context
            "n_ctx": context * slots, "n_slots": slots,
            "n_batch": int(r.get("n_batch") or 2048), "n_ubatch": int(r.get("n_ubatch") or 512),
            "flash_attn": {"on": 1, "off": 0}.get(str(r.get("flash_attn", "auto")), -1),
        }

    def version(self) -> str:
        try:
            return (self.build_dir() / "VERSION").read_text().split()[0]
        except OSError:
            return str(self.recipe.get("pin") or "unknown")


@register
class PieWebEngine(BrowserEngine):
    """pie in the tab: server-web and the bench inferlet from the job's pie build, on the imported .wgpu.zt."""

    name = EngineName.PIE
    only_backend = "webgpu"  # registered as pie@webgpu: get_engine("pie", "webgpu")
    page_engine = "pie"

    def model_arg(self) -> str:
        # the .zt carries the tokenizer; the bench client renders with the checkpoint's own (copied beside the .zt)
        zt = Path(self.recipe.get("snapshot_dir") or "")
        beside = zt.parent if zt.suffix == ".zt" else zt
        if (beside / "tokenizer_config.json").exists() or (beside / "tokenizer.json").exists():
            return str(beside)
        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        return str(snap) if snap else self.artifact.tokenizer_from or self.artifact.base_model

    def web_dist(self) -> Path:
        from pie_evals.node import build as pb

        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.pie_root, capture_output=True, text=True).stdout.strip()
        cached = pb.cache_dir(commit, ["wgpu"]) / "web" if commit else None
        if cached and (cached / "pie.mjs").exists():
            return cached
        dist = self.pie_root / "packages/javascript/server-web/dist"
        if not (dist / "pie.mjs").exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"pie: no server-web build at {dist} (build.py builds it with the wgpu feature)")
        return dist

    def inferlet(self) -> Path:
        from pie_evals.node.build import wasm_target

        w = self.pie_root / f"examples/target/{wasm_target(self.pie_root)}/release/text_completion_bench.wasm"
        if not w.exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"pie: {w} is not built")
        return w

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        zt = Path(self.recipe.get("snapshot_dir") or "")
        if zt.suffix != ".zt" or not zt.exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"pie on WebGPU serves an imported .wgpu.zt; got {zt}")
        _link(files / "model.wgpu.zt", zt)
        _link(files / "pie", self.web_dist())
        _link(files / "text_completion_bench.wasm", self.inferlet())
        # web_* knobs only (pie.yaml backend: webgpu): the native rows' max_forward_tokens and slot counts are tuned for CUDA
        r = self.recipe
        weights_gib = zt.stat().st_size / 2**30
        # the KV pool: what the GPU leaves beside the weights
        room = max(0.5, float(self.platform.memory_gib or 16) * float(r.get("web_memory_share") or 0.85) - weights_gib - 1.5)
        cap = float(r.get("web_kv_budget_gib") or room)
        kv = f"{max(256, int(min(room, cap) * 1024))}MiB"
        config = (
            f"max_forward_tokens = {int(r.get('web_max_forward_tokens') or 2048)}\n"
            f"max_forward_requests = {slots}\n"
            f"max_state_slots = {slots}\n"
            f"max_model_len = {context}\n"
            f'device_kv_budget = "{kv}"\n'
            # a tab is not told the GPU's memory (WebGPU exposes no heap size) and pie then assumes 8 GiB: it is told,
            # as the other engines here allocate up to what the card holds
            f"device_memory_mb = {int(float(self.platform.memory_gib or 8) * 1024)}\n"
        )
        return {"pie_module": "/files/pie/pie.mjs", "model_url": "/files/model.wgpu.zt", "inferlet_url": "/files/text_completion_bench.wasm",
                "config": config, "worker": bool(r.get("web_worker", True))}

    def version(self) -> str:
        out = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=self.pie_root, capture_output=True, text=True)
        return out.stdout.strip() or "unknown"
