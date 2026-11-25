from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from pie_bench.checkpoints.hf_cache import hf_snapshot_dir
from pie_bench.engines import register
from pie_bench.engines.engine import EngineLaunchError
from pie_bench.engines.llamacpp import LlamacppEngine
from pie_bench.engines.served import ServedEngine
from pie_bench.installers.bench_env import cache_root
from pie_bench.paths import CLIENTS
from pie_bench.schema import EngineName, ErrorClass

BROWSER = Path(__file__).resolve().parent / "harness"
LLAMACPP_WASM = Path(__file__).resolve().parent / "llamacpp_wasm"
SCRIPT = CLIENTS / "browser_bench.py"


def ensure_harness(log=print) -> str:
    node = shutil.which("node")
    if not node:
        raise EngineLaunchError(
            ErrorClass.LOAD_FAIL,
            "node is not installed: the browser engines need Node.js for the bridge",
        )
    lock = BROWSER / "node_modules" / ".package-lock.json"
    if not lock.exists():
        log("browser: npm install (playwright, web-llm)")
        subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund"], cwd=BROWSER, check=True, timeout=1800
        )
    stamp = BROWSER / "node_modules" / ".chromium-installed"
    if not stamp.exists():
        log("browser: installing Playwright's Chromium and its system libraries")
        subprocess.run(
            ["npx", "playwright", "install", "--with-deps", "chromium"],
            cwd=BROWSER,
            check=True,
            timeout=3600,
        )
        stamp.write_text("ok\n")
    _ensure_vulkan(log)
    return node


NVIDIA_ICD = {
    "file_format_version": "1.0.0",
    "ICD": {"library_path": "libGLX_nvidia.so.0", "api_version": "1.3"},
}


def _ensure_vulkan(log=print) -> None:
    if platform.system() != "Linux" or not shutil.which("nvidia-smi"):
        return
    libs = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True).stdout
    has = {
        name: name in libs
        for name in (
            "libvulkan.so.1",
            "libGLX_nvidia.so.0",
            "libnvidia-glvkspirv.so",
            "libnvidia-gpucomp.so",
        )
    }
    dirs = [Path(d) for d in ("/usr/share/vulkan/icd.d", "/etc/vulkan/icd.d")]
    icds = [str(f) for d in dirs if d.is_dir() for f in d.glob("*.json")]
    log(
        f"browser: vulkan: NVIDIA_DRIVER_CAPABILITIES={os.environ.get('NVIDIA_DRIVER_CAPABILITIES', '')!r}, libraries {has}, icd manifests {icds}"
    )
    if not has["libvulkan.so.1"] and shutil.which("apt-get"):
        log("browser: vulkan: installing the loader (libvulkan1)")
        subprocess.run(["apt-get", "install", "-y", "-q", "libvulkan1"], check=False, timeout=900)
    if has["libGLX_nvidia.so.0"] and not any("nvidia" in i for i in icds):
        d = dirs[0]
        d.mkdir(parents=True, exist_ok=True)
        (d / "nvidia_icd.json").write_text(json.dumps(NVIDIA_ICD))
        log(f"browser: vulkan: wrote {d / 'nvidia_icd.json'}")
    if not has["libGLX_nvidia.so.0"]:
        log(
            "browser: vulkan: the driver's graphics libraries are not in this container; WebGPU will be SwiftShader"
        )


def _link(dst: Path, src: Path) -> None:
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src)


class BrowserEngine(ServedEngine):
    page_engine: str = ""
    health_path = "/health"
    exact_length = "ignore_eos"
    reports_timing = False

    def script_path(self) -> Path:
        return SCRIPT

    def files_dir(self) -> Path:
        d = (
            cache_root()
            / "browser-files"
            / f"{self.page_engine}-{re.sub(r'[^A-Za-z0-9._-]', '_', self.artifact.id)}-{os.getpid()}"
        )
        d.mkdir(parents=True, exist_ok=True)
        return d

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        raise NotImplementedError

    def default_env(self) -> dict[str, str]:
        root = cache_root() / "browser-profiles"
        root.mkdir(parents=True, exist_ok=True)
        return {"BROWSER_PROFILE_ROOT": str(root)}

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        node = ensure_harness()
        files = self.files_dir()
        options = self.stage(files, max(1, slots), context)
        return [
            node,
            str(BROWSER / "bridge.mjs"),
            "--engine",
            self.page_engine,
            "--port",
            str(port),
            "--files",
            str(files),
            "--options",
            json.dumps(options),
        ]

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
        except Exception:
            pass
        return out

    def leftover_process_names(self) -> list[str]:
        return ["bridge.mjs", "chrome", "headless_shell"]

    def stall_s(self) -> int:
        return int(self.recipe.get("stall_s") or 3600)


@register
class WebllmEngine(BrowserEngine):
    name = EngineName.WEBLLM
    page_engine = "webllm"

    def model_arg(self) -> str:
        return self.artifact.tokenizer_from or self.artifact.base_model

    def model_lib(self) -> Path:
        url = str(self.recipe.get("model_lib") or "")
        if not url:
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"webllm: no model_lib for {self.artifact.id} in recipes/webllm.yaml",
            )
        if "://" not in url:
            return Path(self.recipe.get("snapshot_dir") or "") / url
        d = cache_root() / "webllm-libs"
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
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"webllm: {snap} is not an MLC build (no mlc-chat-config.json)",
            )
        _link(files / "model" / "resolve" / "main", snap)
        _link(files / "lib.wasm", self.model_lib())
        overrides = {
            "context_window_size": max(int(self.recipe.get("context_window_size") or 0), context)
        }
        if self.recipe.get("prefill_chunk_size"):
            overrides["prefill_chunk_size"] = int(self.recipe["prefill_chunk_size"])
        out = {
            "model_id": self.artifact.id,
            "model_url": "/files/model/",
            "model_lib": "/files/lib.wasm",
            "overrides": overrides,
        }
        for k in ("model_manifest", "buffer_size_required_bytes", "required_features"):
            if self.recipe.get(k) is not None:
                out[k] = self.recipe[k]
        return out

    def version(self) -> str:
        pkg = BROWSER / "node_modules" / "@mlc-ai" / "web-llm" / "package.json"
        try:
            return json.loads(pkg.read_text())["version"]
        except (OSError, ValueError, KeyError):
            return str(self.recipe.get("pin") or "unknown")


@register
class LlamacppWebgpuEngine(BrowserEngine):
    name = EngineName.LLAMACPP_WEBGPU
    page_engine = "llamacpp"

    def model_arg(self) -> str:
        return LlamacppEngine.model_arg(self)

    def build_dir(self) -> Path:
        tag = str(self.recipe.get("pin") or "b11312")
        src = hashlib.sha256(
            b"".join((LLAMACPP_WASM / f).read_bytes() for f in ("llama_webgpu.cpp", "build.sh"))
        ).hexdigest()[:8]
        out = cache_root() / "llamacpp-webgpu" / f"{tag}-{src}"
        if not (out / "lw.wasm").exists():
            subprocess.run(
                ["bash", str(LLAMACPP_WASM / "build.sh"), str(out), tag], check=True, timeout=7200
            )
        return out

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        _link(files / "model.gguf", LlamacppEngine.gguf_path(self))
        _link(files / "lw", self.build_dir())
        r = self.recipe
        per_slot = min(context, int(r.get("slot_context") or 1024))
        return {
            "module_url": "/files/lw/lw.mjs",
            "model_url": "/files/model.gguf",
            "n_ctx": per_slot * slots,
            "n_slots": slots,
            "n_batch": int(r.get("n_batch") or 2048),
            "n_ubatch": int(r.get("n_ubatch") or 512),
            "flash_attn": {"on": 1, "off": 0}.get(str(r.get("flash_attn", "auto")), -1),
        }

    def version(self) -> str:
        try:
            return (self.build_dir() / "VERSION").read_text().split()[0]
        except OSError:
            return str(self.recipe.get("pin") or "unknown")


@register
class PieWebEngine(BrowserEngine):
    name = EngineName.PIE
    only_backend = "webgpu"
    page_engine = "pie"

    def model_arg(self) -> str:
        zt = Path(self.recipe.get("snapshot_dir") or "")
        beside = zt.parent if zt.suffix == ".zt" else zt
        if (beside / "tokenizer_config.json").exists() or (beside / "tokenizer.json").exists():
            return str(beside)
        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        return str(snap) if snap else self.artifact.tokenizer_from or self.artifact.base_model

    def web_dist(self) -> Path:
        from pie_bench.installers import pie as pb

        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.pie_root, capture_output=True, text=True
        ).stdout.strip()
        cached = pb.cache_dir(commit, ["wgpu"]) / "web" if commit else None
        if cached and (cached / "pie.mjs").exists():
            return cached
        dist = self.pie_root / "packages/javascript/server-web/dist"
        if not (dist / "pie.mjs").exists():
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"pie: no server-web build at {dist} (build.py builds it with the wgpu feature)",
            )
        return dist

    def inferlet(self) -> Path:
        from pie_bench.installers.pie import wasm_target

        w = (
            self.pie_root
            / f"examples/target/{wasm_target(self.pie_root)}/release/text_completion_bench.wasm"
        )
        if not w.exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"pie: {w} is not built")
        return w

    def stage(self, files: Path, slots: int, context: int) -> dict[str, Any]:
        zt = Path(self.recipe.get("snapshot_dir") or "")
        if zt.suffix != ".zt" or not zt.exists():
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL, f"pie on WebGPU serves an imported .wgpu.zt; got {zt}"
            )
        _link(files / "model.wgpu.zt", zt)
        _link(files / "pie", self.web_dist())
        _link(files / "text_completion_bench.wasm", self.inferlet())
        r = self.recipe
        weights_gib = zt.stat().st_size / 2**30
        room = max(
            0.5,
            float(self.platform.memory_gib or 16) * float(r.get("web_memory_share") or 0.85)
            - weights_gib
            - 1.5,
        )
        cap = float(r.get("web_kv_budget_gib") or room)
        kv = f"{max(256, int(min(room, cap) * 1024))}MiB"
        config = (
            f"max_forward_tokens = {int(r.get('web_max_forward_tokens') or 512)}\n"
            f"max_forward_requests = {slots}\n"
            f"max_state_slots = {slots}\n"
            f"max_model_len = {context}\n"
            f'device_kv_budget = "{kv}"\n'
            f"device_memory_mb = {int(float(self.platform.memory_gib or 8) * 1024)}\n"
        )
        out = {
            "pie_module": "/files/pie/pie.mjs",
            "model_url": "/files/model.wgpu.zt",
            "inferlet_url": "/files/text_completion_bench.wasm",
            "config": config,
            "worker": bool(r.get("web_worker", True)),
        }
        return out

    def version(self) -> str:
        out = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=self.pie_root,
            capture_output=True,
            text=True,
        )
        return out.stdout.strip() or "unknown"
