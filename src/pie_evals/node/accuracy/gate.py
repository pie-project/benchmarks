"""T0 gate wiring: engine tokens vs reference tokens, adjudicated by the
reference's teacher-forced logits at the first divergence."""

from __future__ import annotations

import math
from collections.abc import Callable, Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from pie_evals.schema import AccuracyMetrics, AccuracyStatus, ArtifactKind, Cell, QuantScheme

from .parity import BF16_ULP, adjudicate_divergence, first_divergence, t0_verdict

TeacherForcedFn = Callable[[list[int]], np.ndarray]

#: schemes whose checkpoint can be read by a reference implementation *of the
#: same weights*. Anything else needs a ``degradation_budget`` against bf16
#: (T1/T2) or is skipped.
SAME_WEIGHTS_REFERENCE: dict[QuantScheme, str] = {
    QuantScheme.BF16: "hf",
    QuantScheme.FP8: "hf",
    QuantScheme.MXFP4: "hf",
    QuantScheme.AWQ: "hf",
    QuantScheme.GPTQ: "hf",
    QuantScheme.AFFINE_U4_G64: "mlxlm",
    QuantScheme.MLX_2BIT: "mlxlm",
    QuantScheme.GGUF_Q4_K_M: "llamacpp",
    QuantScheme.GGUF_Q2_K: "llamacpp",
    QuantScheme.GGUF_Q2_0: "llamacpp",
    QuantScheme.GGUF_Q8_0: "llamacpp",
}


def skip_reason(cell: Cell) -> AccuracyStatus | None:
    """Why the accuracy gate does not apply to this cell (``None`` = it does).

    * miniatures are real shapes but not real models — never gated;
    * a scheme with no same-weights reference and no degradation budget has
      nothing to be compared against.
    """
    art = cell.artifact
    if art.kind == ArtifactKind.MINIATURE:
        return AccuracyStatus.SKIPPED_MINIATURE
    if art.scheme not in SAME_WEIGHTS_REFERENCE and not art.degradation_budget:
        return AccuracyStatus.SKIPPED_NO_REFERENCE
    return None


def run_t0(
    engine_output_ids: list[list[int]],
    reference_ids: list[list[int]],
    teacher_forced_logits_fn: TeacherForcedFn,
    prompt_ids: list[list[int]],
    ulp: float = BF16_ULP,
    reference: str | None = None,
    stops: Collection[int] = (),
) -> AccuracyMetrics:
    """Per prompt: find the first divergent token; if any, teacher-force the
    reference on ``prompt + shared prefix`` and adjudicate the two candidates
    at that position with the logit-gap rule.

    Each side is read as its answer: its tokens up to the first stop token in
    ``stops``. What an ``ignore_eos`` run writes past the end of the answer is
    the model reading a turn it was never trained to continue, where a
    near-tie decides every token; an engine that stops at EOS leaves the stop
    token out of its output, so an answer that ends before the other ended on
    a stop. Where one answer ends and the other goes on, the stop (the
    reference's own, or the likeliest of ``stops`` for the engine) is judged
    against the other's token by the same logit-gap rule.

    ``teacher_forced_logits_fn(ids)`` returns ``[len(ids), vocab]`` where row
    ``i`` predicts the token after ``ids[i]`` — so the row for the divergent
    position is the last one of ``prompt + reference[:d]``.
    """
    if not (len(engine_output_ids) == len(reference_ids) == len(prompt_ids)):
        raise ValueError(
            f"prompt count mismatch: engine={len(engine_output_ids)} "
            f"reference={len(reference_ids)} prompts={len(prompt_ids)}"
        )
    divergences: list[int | None] = []
    gaps: list[float] = []
    benign: list[bool] = []
    detail: list[dict] = []
    for i, (eng, ref, prompt) in enumerate(zip(engine_output_ids, reference_ids, prompt_ids)):
        ref_stop = next((t for t in ref if t in stops), None)
        eng, ref = _answer(eng, stops), _answer(ref, stops)
        d = first_divergence(eng, ref)
        divergences.append(d)
        if d is None:
            continue
        if (d >= len(eng) or d >= len(ref)) and not stops:
            # one side stopped early and no stop token says how: nothing to adjudicate, and not benign
            gaps.append(float("nan"))
            benign.append(False)
            detail.append({"prompt": i, "pos": d, "kind": "length_mismatch",
                           "engine_len": len(eng), "reference_len": len(ref)})
            continue
        prefix = list(prompt) + list(ref[:d])
        logits = np.asarray(teacher_forced_logits_fn(prefix))
        if logits.ndim != 2 or logits.shape[0] != len(prefix):
            raise ValueError(f"teacher-forced logits shape {logits.shape} for {len(prefix)} ids")
        stop = max(stops, key=lambda t: logits[-1][t]) if stops else None
        eng_tok = int(eng[d]) if d < len(eng) else int(stop)
        ref_tok = int(ref[d]) if d < len(ref) else int(ref_stop if ref_stop is not None else stop)
        gap, ok = adjudicate_divergence(logits[-1], eng_tok, ref_tok, ulp=ulp)
        gaps.append(gap)
        benign.append(ok)
        detail.append({"prompt": i, "pos": d, "engine_tok": eng_tok,
                       "reference_tok": ref_tok, "gap": gap, "benign": ok})
    status = t0_verdict(divergences, gaps, benign)
    finite = [g for g in gaps if not math.isnan(g)]
    return AccuracyMetrics(
        status=status,
        reference=reference,
        t0_first_divergence=divergences,
        t0_max_logit_gap=max(finite) if finite else None,
        t0_benign=(all(benign) if benign else None) if any(d is not None for d in divergences) else True,
        detail={"t0": detail, "ulp": ulp},
    )


def _answer(ids: list[int], stops: Collection[int]) -> list[int]:
    """The tokens before the first stop token in ``stops``."""
    end = next((at for at, t in enumerate(ids) if t in stops), len(ids))
    return list(ids)[:end]


# ---------------------------------------------------------------------------
# T0 through a live engine adapter
# ---------------------------------------------------------------------------

BENCH_SYSTEM_DEFAULT = "You are a helpful benchmarking assistant."


def bench_system_prompt(pie_root: str | Path) -> str:
    """The system prompt scripts/bench/common.py renders; read from the pinned tree
    so the reference tokenizes exactly what the engine saw."""
    import re

    try:
        src = (Path(pie_root) / "scripts/bench" / "common.py").read_text()
        m = re.search(r'^BENCH_SYSTEM\s*=\s*"([^"]*)"', src, re.M)
        return m.group(1) if m else BENCH_SYSTEM_DEFAULT
    except OSError:
        return BENCH_SYSTEM_DEFAULT


def stop_ids(snapshot_dir: str | Path) -> set[int]:
    """The checkpoint's end-of-turn tokens: ``eos_token_id`` of its
    generation_config.json, else of its config.json (or text_config), and the
    tokenizer's ``eos_token``. A chat checkpoint may state only its
    end-of-text there (Qwen3.5 has no generation_config.json and its config
    says ``<|endoftext|>``) while its turns end on the tokenizer's
    ``<|im_end|>``, past which a reply is ignore_eos filler."""
    import json

    snap = Path(snapshot_dir)
    stops: set[int] = set()
    for name in ("generation_config.json", "config.json"):
        try:
            cfg = json.loads((snap / name).read_text())
        except (OSError, ValueError):
            continue
        eos = cfg.get("eos_token_id", cfg.get("text_config", {}).get("eos_token_id"))
        if eos is not None:
            stops = {int(t) for t in (eos if isinstance(eos, list) else [eos])}
            break
    stops.update(_tokenizer_eos(snap))
    return stops


def _tokenizer_eos(snap: Path) -> set[int]:
    """The id of tokenizer_config.json's ``eos_token``, found among
    tokenizer.json's added tokens; empty where either does not say."""
    import json

    try:
        eos = json.loads((snap / "tokenizer_config.json").read_text()).get("eos_token")
        added = json.loads((snap / "tokenizer.json").read_text()).get("added_tokens", [])
    except (OSError, ValueError):
        return set()
    if isinstance(eos, dict):
        eos = eos.get("content")
    return {int(t["id"]) for t in added if eos is not None and t.get("content") == eos}


def render_like_bench(snapshot_dir: str | Path, system: str, prompt: str, enable_thinking: bool | None = False) -> list[int]:
    """Mirror ``scripts/bench/common.py::_render_chat`` + tokenize: chat template
    when the tokenizer has one (Qwen3-family ``enable_thinking`` switch
    honoured), plain ``system\\n\\nprompt`` otherwise."""
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(snapshot_dir))
    if getattr(tok, "chat_template", None):
        extra = {} if enable_thinking is None else {"enable_thinking": enable_thinking}
        text = tok.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True, **extra,
        )
        return tok(text, add_special_tokens=False)["input_ids"]
    return tok(f"{system}\n\n{prompt}" if system else prompt)["input_ids"]


@dataclass
class T0Outputs:
    """What the engine answered for the T0 prompt set, held until the engine
    is down: the reference then loads on a device the engine no longer holds
    (a 24 GB card has no room for a 16 GB reference beside the engine that
    serves those weights, nightly rtx4090 gemma-4-E4B)."""

    engine_ids: list[list[int]]
    prompt_ids: list[list[int]]


def t0_engine_outputs(
    engine: Any,
    snapshot_dir: str | Path,
    *,
    pie_root: str | Path,
    out_dir: str | Path,
    max_new_tokens: int = 64,
    timeout_s: int = 900,
) -> T0Outputs | AccuracyMetrics:
    """Run the fixed T0 prompt set through the engine adapter (greedy,
    ``ignore_eos``, one request per prompt).

    The engine renders prompts through scripts/bench/common.py's chat template;
    the reference tokenizes the same rendering and the prompt-token count the
    engine reported is checked against it. A count mismatch, or no count at
    all, means the two may have seen different inputs: the gate then returns
    SKIPPED_NO_REFERENCE with the detail, never a FAIL that is really a
    template difference.
    """
    from pie_evals.schema import WorkloadKind, WorkloadSpec

    from .prompts import t0_prompts

    out_dir = Path(out_dir)
    system = bench_system_prompt(pie_root)
    prompts = t0_prompts()
    engine_ids: list[list[int]] = []
    prompt_ids: list[list[int]] = []
    reported_prompt_tokens: list[int] = []
    wl = WorkloadSpec(id="t0", kind=WorkloadKind.SINGLE_STREAM, params={"requests": 1, "decode": max_new_tokens})
    for pid, text in prompts:
        common = ["--prompt", text, "--max-tokens", str(max_new_tokens), "--temperature", "0", "--top-p", "1",
                  "--ignore-eos", "--warmup", "0", "--no-think", "--no-unique-prompts"]
        res = engine.run(wl, common, out_dir / pid, timeout_s)
        if not res.output_token_ids or not res.output_token_ids[0]:
            return AccuracyMetrics(status=AccuracyStatus.SKIPPED_NO_REFERENCE, detail={"error": f"engine returned no token ids for {pid} (needs --dump-all-token-ids)"})
        engine_ids.append(list(res.output_token_ids[0]))
        reported_prompt_tokens.append(int(res.requests[0].get("prompt_tokens") or 0))
        prompt_ids.append(render_like_bench(snapshot_dir, system, text, enable_thinking=False))
    # A run that states no count (a program that is not the bench, e.g.
    # classifier-free-guidance, renders its own prompt) cannot be shown to
    # have read the reference's input either.
    mismatch = [(pid, len(p), n) for (pid, _), p, n in zip(prompts, prompt_ids, reported_prompt_tokens) if n != len(p)]
    if mismatch:
        return AccuracyMetrics(
            status=AccuracyStatus.SKIPPED_NO_REFERENCE,
            detail={"error": "prompt token count differs between engine and reference rendering", "mismatch": mismatch},
        )
    return T0Outputs(engine_ids, prompt_ids)


def t0_judge(
    outputs: T0Outputs,
    cell: Cell,
    snapshot_dir: str | Path,
    platform_os: str,
    *,
    cache_dir: str | Path,
    max_new_tokens: int = 64,
    reference_device: str | None = None,
) -> AccuracyMetrics:
    """Compare the engine's T0 answers with the reference. The reference is
    built only when the cache misses, and handed back when this returns."""
    from .reference import LazyReference, ReferenceCache, reference_for

    kind = reference_for(platform_os, str(cell.artifact.source_format))
    kw = {"device": reference_device} if reference_device else {}
    if kind == "llamacpp":
        kw["gguf_file"] = cell.artifact.gguf_file  # the arm the engine loaded, not whichever GGUF sorts first
    ref = LazyReference(kind, snapshot_dir, **kw)
    cache = ReferenceCache(cache_dir)
    revision = Path(snapshot_dir).name

    def tf(ids: list[int]):
        return cache.teacher_forced_logits(ref, revision, ids)

    try:
        reference_ids = [cache.greedy(ref, revision, p, max_new_tokens) for p in outputs.prompt_ids]
        return run_t0(outputs.engine_ids, reference_ids, tf, outputs.prompt_ids, reference=kind, stops=stop_ids(snapshot_dir))
    finally:
        ref.close()
