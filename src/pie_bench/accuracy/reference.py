from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Protocol

import numpy as np


class Reference(Protocol):
    name: str

    def greedy(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]: ...

    def teacher_forced_logits(self, ids: list[int]) -> np.ndarray: ...


def reference_for(platform_os: str, source_format: str) -> str:
    if str(source_format) == "gguf":
        return "llamacpp"
    if str(platform_os).lower() in ("macos", "darwin", "mac") and str(source_format) == "mlx":
        return "mlx"
    return "hf"


class HFReference:
    name = "hf"

    def __init__(self, snapshot_dir: str | Path, dtype: str = "bfloat16", device: str = "cuda"):
        import torch
        from transformers import AutoModelForCausalLM

        self.torch = torch
        self.snapshot_dir = Path(snapshot_dir)
        self.device = device
        self.dtype = getattr(torch, dtype) if isinstance(dtype, str) else dtype
        self.model = AutoModelForCausalLM.from_pretrained(
            str(self.snapshot_dir), torch_dtype=self.dtype, device_map=None, trust_remote_code=True
        )
        self.model.to(device)
        self.model.eval()

    @property
    def vocab_size(self) -> int:
        return int(self.model.get_output_embeddings().weight.shape[0])

    def greedy(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        torch = self.torch
        gen: list[int] = []
        step = torch.tensor([list(prompt_ids)], dtype=torch.long, device=self.device)
        past = None
        with torch.no_grad():
            for _ in range(max_new_tokens):
                out = self.model(input_ids=step, past_key_values=past, use_cache=True)
                past = out.past_key_values
                nxt = int(out.logits[0, -1].argmax())
                gen.append(nxt)
                step = torch.tensor([[nxt]], dtype=torch.long, device=self.device)
        return gen

    def teacher_forced_logits(self, ids: list[int]) -> np.ndarray:
        torch = self.torch
        x = torch.tensor([list(ids)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            logits = self.model(input_ids=x, use_cache=False).logits[0]
        return logits.float().cpu().numpy().astype(np.float32)

    def close(self) -> None:
        import gc

        del self.model
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


class MlxReference:
    name = "mlxlm"

    def __init__(self, snapshot_dir: str | Path, dtype: str = "bfloat16", device: str = "gpu"):
        import mlx.core as mx
        from mlx_lm import load
        from mlx_lm.models.cache import make_prompt_cache

        self.mx = mx
        self._make_prompt_cache = make_prompt_cache
        self.snapshot_dir = Path(snapshot_dir)
        mx.set_default_device(mx.gpu if device == "gpu" else mx.cpu)
        self.model, self.tokenizer = load(str(self.snapshot_dir))
        self.dtype = dtype

    def greedy(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        mx = self.mx
        cache = self._make_prompt_cache(self.model)
        out = self.model(mx.array([list(prompt_ids)]), cache=cache)[0, -1].astype(mx.float32)
        mx.eval(out)
        gen: list[int] = []
        for _ in range(max_new_tokens):
            nxt = int(mx.argmax(out).item())
            gen.append(nxt)
            out = self.model(mx.array([[nxt]]), cache=cache)[0, -1].astype(mx.float32)
            mx.eval(out)
        return gen

    def teacher_forced_logits(self, ids: list[int]) -> np.ndarray:
        mx = self.mx
        tf = self.model(mx.array([list(ids)]))[0].astype(mx.float32)
        mx.eval(tf)
        return np.asarray(tf).astype(np.float32)


class LlamaCppReference:

    name = "llamacpp"

    def __init__(self, snapshot_dir: str | Path, gguf_file: str | None = None, device: str = "gpu", n_probs: int = 256):
        from pie_bench.checkpoints.snapshots import gguf_shards
        from pie_bench.quality.engines import _free_port, _get, _post, _serve

        self._post = _post
        self.snapshot_dir = Path(snapshot_dir)
        self.n_probs = n_probs
        if gguf_file:
            gguf = self.snapshot_dir / gguf_shards(gguf_file)[0]
        else:
            found = sorted(self.snapshot_dir.glob("*.gguf"))
            if not found:
                raise FileNotFoundError(f"no .gguf file in {self.snapshot_dir}")
            gguf = found[0]
        server = os.environ.get("LLAMA_SERVER_BIN") or "llama-server"
        port = _free_port()
        cmd = [server, "--model", str(gguf), "--host", "127.0.0.1", "--port", str(port), "--ctx-size", "8192",
               "--parallel", "1", "--n-gpu-layers", "0" if device == "cpu" else "all", "--no-warmup"]
        self._proc, self.url = _serve(cmd, {}, port, "/health", 1800)
        meta = json.loads(_get(self.url + "/v1/models"))["data"][0].get("meta", {})
        self.vocab_size = int(meta["n_vocab"])

    def _complete(self, ids: list[int], n_predict: int, **extra: Any) -> dict:
        body = {"prompt": [int(i) for i in ids], "n_predict": n_predict, "temperature": 0.0, "top_k": 1, "top_p": 1.0,
                "ignore_eos": True, "cache_prompt": False, "seed": 0, **extra}
        return self._post(f"{self.url}/completion", body)

    def greedy(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        out = self._complete(prompt_ids, max_new_tokens, return_tokens=True)
        return [int(t) for t in out["tokens"]][:max_new_tokens]

    def teacher_forced_logits(self, ids: list[int]) -> np.ndarray:
        out = self._complete(ids, 1, n_probs=self.n_probs, post_sampling_probs=False)
        first = out["completion_probabilities"][0]
        rows = np.full((len(ids), self.vocab_size), -np.inf, dtype=np.float32)
        if "top_logprobs" in first:
            for p in first["top_logprobs"]:
                rows[-1, int(p["id"])] = float(p["logprob"])
        else:
            for p in first["probs"]:
                rows[-1, int(p["id"])] = float(np.log(p["prob"])) if p["prob"] > 0 else -np.inf
        return rows

    def close(self) -> None:
        from pie_bench.quality.engines import _stop

        proc, self._proc = self._proc, None
        if proc is not None:
            _stop(proc)


def load_reference(kind: str, snapshot_dir: str | Path, **kw: Any) -> HFReference | MlxReference | LlamaCppReference:
    if kind == "mlx":
        return MlxReference(snapshot_dir, **kw)
    if kind == "hf":
        return HFReference(snapshot_dir, **kw)
    if kind == "llamacpp":
        return LlamaCppReference(snapshot_dir, **kw)
    raise ValueError(f"unknown reference kind {kind!r}")


class LazyReference:

    def __init__(self, kind: str, snapshot_dir: str | Path, **kw: Any):
        self.name = kind
        self._make = lambda: load_reference(kind, snapshot_dir, **kw)
        self._ref: HFReference | MlxReference | None = None

    def _loaded(self) -> HFReference | MlxReference:
        if self._ref is None:
            self._ref = self._make()
        return self._ref

    def greedy(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        return self._loaded().greedy(prompt_ids, max_new_tokens)

    def teacher_forced_logits(self, ids: list[int]) -> np.ndarray:
        return self._loaded().teacher_forced_logits(ids)

    def close(self) -> None:
        ref, self._ref = self._ref, None
        if ref is not None and hasattr(ref, "close"):
            ref.close()


def prompt_hash(ids: list[int]) -> str:
    return hashlib.sha256(json.dumps([int(i) for i in ids]).encode()).hexdigest()[:16]


class ReferenceCache:

    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)

    def _path(self, revision: str, kind: str, ids: list[int], n: int) -> Path:
        rev = str(revision).replace("/", "_")
        return self.cache_dir / rev / f"{kind}-{prompt_hash(ids)}-n{n}.npz"

    def get(self, revision: str, kind: str, ids: list[int], n: int) -> np.ndarray | None:
        p = self._path(revision, kind, ids, n)
        if not p.exists():
            return None
        with np.load(p) as z:
            if "ids" in z and z["ids"].tolist() != [int(i) for i in ids]:
                return None
            return z["value"]

    def put(self, revision: str, kind: str, ids: list[int], n: int, value: np.ndarray) -> Path:
        p = self._path(revision, kind, ids, n)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp.npz")
        np.savez(tmp, ids=np.asarray(ids, dtype=np.int64), value=np.asarray(value))
        tmp.replace(p)
        return p

    def greedy(self, ref: Reference, revision: str, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        hit = self.get(revision, "argmax", prompt_ids, max_new_tokens)
        if hit is not None:
            return [int(t) for t in hit.tolist()]
        out = ref.greedy(prompt_ids, max_new_tokens)
        self.put(revision, "argmax", prompt_ids, max_new_tokens, np.asarray(out, dtype=np.int64))
        return out

    def teacher_forced_logits(self, ref: Reference, revision: str, ids: list[int]) -> np.ndarray:
        hit = self.get(revision, "tf", ids, len(ids))
        if hit is not None:
            return hit
        out = ref.teacher_forced_logits(ids)
        self.put(revision, "tf", ids, len(ids), out.astype(np.float32))
        return out
