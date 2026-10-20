"""Reference implementations of the same weights, behind lazy imports.

* :class:`HFReference` — ``transformers`` on CUDA/CPU. The reference for
  HF-safetensors checkpoints (bf16, fp8, mxfp4 via transformers' dequant).
* :class:`MlxReference` — ``mlx_lm`` on Apple silicon. The reference for
  ``mlx-community`` conversions, mirroring how pie's own
  ``scripts/gemma4_parity_ref.py`` reads them (``mlx_lm.load`` +
  ``make_prompt_cache``, greedy argmax step by step, float32 logits).
* :class:`LlamaCppReference` — ``llama-server`` on one GGUF file. The
  reference for GGUF checkpoints: transformers cannot read every GGUF family
  (qwen3_5 and qwen3_6 among them), and llama.cpp is the implementation the
  conversion was made for.

Nothing here is imported at package import time; ``torch``/``mlx`` are
resolved inside the constructors, so a node without them can still run the
perf side and the pure parity arithmetic.

Reference outputs are expensive and deterministic, so :class:`ReferenceCache`
stores them as ``.npz`` keyed by ``(checkpoint revision, prompt hash,
max_new_tokens)`` — computed once per checkpoint, reused across engines and
runs.
"""

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
    """Which reference implementation to read a checkpoint against.

    ``"llamacpp"`` for GGUF checkpoints on any platform, ``"mlx"`` for MLX
    checkpoints on macOS (each is the implementation its conversion was made
    for); ``"hf"`` everywhere else.
    """
    if str(source_format) == "gguf":
        return "llamacpp"
    if str(platform_os).lower() in ("macos", "darwin", "mac") and str(source_format) == "mlx":
        return "mlx"
    return "hf"


# ---- HF transformers -----------------------------------------------------------


class HFReference:
    name = "hf"

    def __init__(self, snapshot_dir: str | Path, dtype: str = "bfloat16", device: str = "cuda"):
        import torch  # lazy
        from transformers import AutoModelForCausalLM  # lazy

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
        """Greedy continuation (new tokens only): the argmax at every step and
        no stop, as the mlx reference reads it. The engine runs ignore_eos,
        and the end of turn the model writes is where the gate cuts both
        answers; `generate(min_new_tokens=...)`, which this once used for a
        fixed length, masks the checkpoint's eos ids instead, so a model whose
        turn ends on an eos id (gemma-4's `<turn|>`) could never end one."""
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
        """``[len(ids), vocab]`` float32 logits; row ``i`` is the distribution
        over the token *after* ``ids[i]``."""
        torch = self.torch
        x = torch.tensor([list(ids)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            logits = self.model(input_ids=x, use_cache=False).logits[0]
        return logits.float().cpu().numpy().astype(np.float32)

    def close(self) -> None:
        """Hands the device back: the engine under test shares it and sized
        itself to what was free before this reference loaded."""
        import gc

        del self.model
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


# ---- mlx_lm ---------------------------------------------------------------------


class MlxReference:
    name = "mlxlm"

    def __init__(self, snapshot_dir: str | Path, dtype: str = "bfloat16", device: str = "gpu"):
        import mlx.core as mx  # lazy
        from mlx_lm import load  # lazy
        from mlx_lm.models.cache import make_prompt_cache  # lazy

        self.mx = mx
        self._make_prompt_cache = make_prompt_cache
        self.snapshot_dir = Path(snapshot_dir)
        mx.set_default_device(mx.gpu if device == "gpu" else mx.cpu)
        self.model, self.tokenizer = load(str(self.snapshot_dir))
        self.dtype = dtype  # the checkpoint decides; kept for the record

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


# ---- llama.cpp ------------------------------------------------------------------


class LlamaCppReference:
    """``llama-server`` (``$LLAMA_SERVER_BIN``) on the GGUF in ``snapshot_dir``,
    booted the way the llama.cpp adapter and the quality runs boot it.

    ``greedy`` asks ``/completion`` for the continuation of the prompt's token
    ids at ``top_k 1``, no stop. ``teacher_forced_logits`` asks for one token
    with the top ``n_probs`` log-probabilities: the gate reads only the last
    row, at two token ids, and a log-probability difference is a logit
    difference, so that row (every other id ``-inf``) adjudicates the same way;
    a token outside the top ``n_probs`` is not benign."""

    name = "llamacpp"

    def __init__(self, snapshot_dir: str | Path, gguf_file: str | None = None, device: str = "gpu", n_probs: int = 256):
        from pie_evals.node.snapshots import gguf_shards
        from pie_evals.quality.engines import _free_port, _get, _post, _serve

        self._post = _post
        self.snapshot_dir = Path(snapshot_dir)
        self.n_probs = n_probs
        if gguf_file:
            gguf = self.snapshot_dir / gguf_shards(gguf_file)[0]
        else:  # the snapshot holds one GGUF (or its shards): llama.cpp is handed the first
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
        """``[len(ids), vocab]`` float32; only the last row is filled (the top
        ``n_probs`` log-probabilities of the token after ``ids``), the rest and
        every id outside the top ``n_probs`` is ``-inf``."""
        out = self._complete(ids, 1, n_probs=self.n_probs, post_sampling_probs=False)
        first = out["completion_probabilities"][0]
        rows = np.full((len(ids), self.vocab_size), -np.inf, dtype=np.float32)
        if "top_logprobs" in first:
            for p in first["top_logprobs"]:
                rows[-1, int(p["id"])] = float(p["logprob"])
        else:  # builds before the logprob fields report probabilities
            for p in first["probs"]:
                rows[-1, int(p["id"])] = float(np.log(p["prob"])) if p["prob"] > 0 else -np.inf
        return rows

    def close(self) -> None:
        """Stops the server, handing the device back to the next engine."""
        from pie_evals.quality.engines import _stop

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
    """A reference built on its first use, so a run whose outputs the cache
    already holds never loads the weights beside the engine; ``close`` frees
    whatever it loaded."""

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


# ---- cache ----------------------------------------------------------------------


def prompt_hash(ids: list[int]) -> str:
    return hashlib.sha256(json.dumps([int(i) for i in ids]).encode()).hexdigest()[:16]


class ReferenceCache:
    """``<cache_dir>/<revision>/<kind>-<prompt_hash>-n<max_new_tokens>.npz``.

    ``revision`` is the checkpoint commit (or miniature recipe tag), which is
    what makes a cached reference valid: same weights, same prompt, same
    length -> same greedy tokens / teacher-forced logits, whichever reference
    process produced them.
    """

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
                return None  # hash collision or hand-edited file
            return z["value"]

    def put(self, revision: str, kind: str, ids: list[int], n: int, value: np.ndarray) -> Path:
        p = self._path(revision, kind, ids, n)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp.npz")
        np.savez(tmp, ids=np.asarray(ids, dtype=np.int64), value=np.asarray(value))
        tmp.replace(p)
        return p

    def greedy(self, ref: Reference, revision: str, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        # "argmax", not "greedy": a reply the eos-masking generate wrote is not reused
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
