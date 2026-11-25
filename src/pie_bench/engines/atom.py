from __future__ import annotations

import os
import subprocess
from pathlib import Path

from pie_bench.engines import register
from pie_bench.engines.engine import EngineLaunchError
from pie_bench.schema import EngineName, ErrorClass, WorkloadSpec

from .served import ServedEngine, free_port

ATOM_CAPTURE_SIZES = [1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 48, 64, 128, 256, 512]
_KV_DTYPES = {"bf16": "bf16", "fp16": "bf16", "auto": "bf16", "fp8": "fp8", "fp8_e4m3": "fp8"}


def image_python() -> str:
    for c in ("/opt/venv/bin/python3", "/usr/bin/python3", "/usr/local/bin/python3"):
        if Path(c).exists() and subprocess.run([c, "-c", "import atom"], capture_output=True, timeout=300).returncode == 0:
            return c
    return "python3"


@register
class AtomEngine(ServedEngine):
    """AMD's ATOM (ROCm/ATOM) serving its OpenAI server from AMD's image, the way ATOM ships."""

    name = EngineName.ATOM
    health_path = "/v1/models"
    exact_length = "ignore_eos"
    token_ids = True

    def server_python(self) -> str:
        return os.environ.get("ATOM_PY") or image_python()

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        kv = r.get("kv_cache_dtype") or _KV_DTYPES.get(str(self.artifact.kv_dtype), "bf16")
        cmd = [
            self.server_python(), "-m", "atom.entrypoints.openai_server", "--model", self.model_arg(),
            "--host", "127.0.0.1", "--server-port", str(port), "--port", str(free_port()),
            "--tensor-parallel-size", str(max(1, int(self.mode.tp))), "--max-model-len", str(context),
            "--max-num-seqs", str(slots), "--kv_cache_dtype", str(kv), "--trust-remote-code",
            "--disable-uvicorn-access-log",
        ]
        if r.get("gpu_mem_util") is not None:
            cmd += ["--gpu-memory-utilization", str(r["gpu_mem_util"])]
        if not r.get("prefix_caching"):
            cmd.append("--no-enable_prefix_caching")
        if slots > ATOM_CAPTURE_SIZES[-1] and not r.get("enforce_eager"):
            cmd += ["--cudagraph-capture-sizes", str(ATOM_CAPTURE_SIZES + [slots]).replace(" ", "")]
        if r.get("enforce_eager"):
            cmd.append("--enforce-eager")
        if r.get("max_num_batched_tokens"):
            cmd += ["--max-num-batched-tokens", str(int(r["max_num_batched_tokens"]))]
        if r.get("index_cache_dtype"):
            cmd += ["--index-cache-dtype", str(r["index_cache_dtype"])]
        return cmd

    def server_env(self) -> dict[str, str]:
        """ATOM 0.1.9 keys its torch.compile cache (~/.cache/atom) without the model's widths, so gpt-oss-20b loads
        the graphs gpt-oss-120b left there and asserts (expected size 32==128): each checkpoint gets its own home."""
        from pie_bench.installers.baselines import cache_root

        return {"HOME": str(cache_root() / "atom-home" / self.artifact.id)}

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        pin, have = str(self.recipe.get("pin") or ""), self.version()
        if self._server_proc is None and pin and have.split("+")[0] != pin:
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"the image carries atom {have}, the run pins {pin}: install atom=={pin} into AMD's rocm/atom-dev image")
        super().serve(workload, log_path, timeout_s)

    def version(self) -> str:
        try:
            out = subprocess.run([self.server_python(), "-c", "from importlib.metadata import version; print(version('atom'))"],
                                 capture_output=True, text=True, timeout=120, check=False)
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["ATOM::EngineCore", "ATOM::EngineCor", "ATOM::TP0"]
