from __future__ import annotations

import argparse
import json
from pathlib import Path

BENCH_SYSTEM = "You are a helpful benchmarking assistant."
BENCH_PROMPT = "Write a short story about a robot."


def _filler_words(count: int) -> str:
    base = (
        "the quick brown fox jumps over the lazy dog and then walks "
        "back home again to rest before the next long day begins"
    ).split()
    return " ".join(base[i % len(base)] for i in range(count))


OUTPUT_SPREAD_PERIOD = 16


def request_max_tokens(args: argparse.Namespace, i: int) -> int:
    if getattr(args, "mixed_phase", False) and i % 2 == 0:
        return args.mixed_short_output
    spread = getattr(args, "output_spread", 0.0) or 0.0
    if spread > 0.0:
        frac = (i % OUTPUT_SPREAD_PERIOD) / (OUTPUT_SPREAD_PERIOD - 1)
        return max(1, round(args.max_tokens * (1.0 + spread * (2.0 * frac - 1.0))))
    return args.max_tokens


def request_max_tokens_varies(args: argparse.Namespace) -> bool:
    if getattr(args, "mixed_phase", False):
        return True
    return (getattr(args, "output_spread", 0.0) or 0.0) > 0.0


def make_prompts(args: argparse.Namespace, n: int) -> list[str]:
    prompts_file = getattr(args, "prompts_file", None)
    if prompts_file:
        with open(prompts_file, encoding="utf-8") as f:
            prompts = json.load(f)
        if not isinstance(prompts, list) or not all(isinstance(x, str) for x in prompts):
            raise SystemExit(f"--prompts-file {prompts_file}: expected a JSON list of strings")
        if len(prompts) < n:
            raise SystemExit(f"--prompts-file {prompts_file}: {len(prompts)} prompts, {n} needed")
        return prompts[:n]
    if getattr(args, "mixed_phase", False):
        long_body = _filler_words(getattr(args, "mixed_long_prompt_words", 400))
        return [
            f"{long_body}. {args.prompt} (Request #{i})"
            if i % 2 == 0
            else f"{args.prompt} (Request #{i})"
            for i in range(n)
        ]
    shared_words = getattr(args, "shared_prefix_words", 0) or 0
    if shared_words > 0:
        base = (
            "the quick brown fox jumps over the lazy dog and then walks "
            "back home again to rest before the next long day begins"
        ).split()
        filler = " ".join(base[i % len(base)] for i in range(shared_words))
        shared = (
            "You will answer questions about the following policy. "
            + filler
            + ". Policy ends. "
        )
        return [f"{shared}{args.prompt} (Request #{i})" for i in range(n)]
    if args.unique_prompts:
        return [f"{args.prompt} (Request #{i})" for i in range(n)]
    return [args.prompt for _ in range(n)]


def _render_chat(tok, system: str, prompts: list[str], enable_thinking: bool | None = None) -> list[str]:
    if getattr(tok, "chat_template", None):
        extra = {} if enable_thinking is None else {"enable_thinking": enable_thinking}
        return [
            tok.apply_chat_template(
                [{"role": "system", "content": system},
                 {"role": "user", "content": p}],
                tokenize=False,
                add_generation_prompt=True,
                **extra,
            )
            for p in prompts
        ]
    return [f"{system}\n\n{p}" if system else p for p in prompts]


def hf_chat_prompts_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[str], list[int]]:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(Path(model).parent) if Path(model).is_file() else model, trust_remote_code=True)
    rendered = _render_chat(tok, system, prompts, enable_thinking)
    counts = [len(tok.encode(p, add_special_tokens=False)) for p in rendered]
    return rendered, counts


def hf_chat_token_ids_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[list[int]], list[int]]:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(Path(model).parent) if Path(model).is_file() else model, trust_remote_code=True)
    rendered = _render_chat(tok, system, prompts, enable_thinking)
    token_ids = [tok.encode(p, add_special_tokens=False) for p in rendered]
    return token_ids, [len(ids) for ids in token_ids]
