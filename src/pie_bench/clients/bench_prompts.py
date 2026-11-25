from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

BENCH_SYSTEM = "You are a helpful benchmarking assistant."
BENCH_PROMPT = "Write a short story about a robot."

FILLER = (
    "the quick brown fox jumps over the lazy dog and then walks "
    "back home again to rest before the next long day begins"
).split()

OUTPUT_SPREAD_PERIOD = 16


def _filler_words(count: int) -> str:
    return " ".join(FILLER[i % len(FILLER)] for i in range(count))


def request_max_tokens(args: argparse.Namespace, i: int) -> int:
    if args.mixed_phase and i % 2 == 0:
        return args.mixed_short_output
    spread = args.output_spread or 0.0
    if spread > 0.0:
        frac = (i % OUTPUT_SPREAD_PERIOD) / (OUTPUT_SPREAD_PERIOD - 1)
        return max(1, round(args.max_tokens * (1.0 + spread * (2.0 * frac - 1.0))))
    return args.max_tokens


def request_max_tokens_varies(args: argparse.Namespace) -> bool:
    if args.mixed_phase:
        return True
    return (args.output_spread or 0.0) > 0.0


def _prompts_from_file(path: str, n: int) -> list[str]:
    with open(path, encoding="utf-8") as f:
        prompts = json.load(f)
    if not isinstance(prompts, list) or not all(isinstance(x, str) for x in prompts):
        raise SystemExit(f"--prompts-file {path}: expected a JSON list of strings")
    if len(prompts) < n:
        raise SystemExit(f"--prompts-file {path}: {len(prompts)} prompts, {n} needed")
    return prompts[:n]


def _mixed_phase_prompts(args: argparse.Namespace, n: int) -> list[str]:
    long_body = _filler_words(args.mixed_long_prompt_words)
    return [
        f"{long_body}. {args.prompt} (Request #{i})"
        if i % 2 == 0
        else f"{args.prompt} (Request #{i})"
        for i in range(n)
    ]


def _shared_prefix_prompts(args: argparse.Namespace, n: int, words: int) -> list[str]:
    shared = (
        "You will answer questions about the following policy. "
        + _filler_words(words)
        + ". Policy ends. "
    )
    return [f"{shared}{args.prompt} (Request #{i})" for i in range(n)]


def make_prompts(args: argparse.Namespace, n: int) -> list[str]:
    if args.prompts_file:
        return _prompts_from_file(args.prompts_file, n)
    if args.mixed_phase:
        return _mixed_phase_prompts(args, n)
    shared_words = args.shared_prefix_words or 0
    if shared_words > 0:
        return _shared_prefix_prompts(args, n, shared_words)
    if args.unique_prompts:
        return [f"{args.prompt} (Request #{i})" for i in range(n)]
    return [args.prompt for _ in range(n)]


def _shuffled(prompt: str, seed: int) -> str:
    words = prompt.split()
    random.Random(seed).shuffle(words)
    return " ".join(words)


def shuffled_against_prefix_cache(args: argparse.Namespace, prompts: list[str]) -> list[str]:
    if not args.flush_cache or args.prompts_file:
        return prompts
    salt = random.SystemRandom().getrandbits(32)
    return [_shuffled(p, salt + i) for i, p in enumerate(prompts)]


def load_tokenizer(model: str):
    from transformers import AutoTokenizer

    source = str(Path(model).parent) if Path(model).is_file() else model
    return AutoTokenizer.from_pretrained(source, trust_remote_code=True)


def render_chat(
    tok, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> list[str]:
    if not getattr(tok, "chat_template", None):
        return [f"{system}\n\n{p}" if system else p for p in prompts]
    extra = {} if enable_thinking is None else {"enable_thinking": enable_thinking}
    return [
        tok.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": p}],
            tokenize=False,
            add_generation_prompt=True,
            **extra,
        )
        for p in prompts
    ]


def hf_chat_prompts_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[str], list[int]]:
    tok = load_tokenizer(model)
    rendered = render_chat(tok, system, prompts, enable_thinking)
    counts = [len(tok.encode(p, add_special_tokens=False)) for p in rendered]
    return rendered, counts


def hf_chat_token_ids_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[list[int]], list[int]]:
    tok = load_tokenizer(model)
    rendered = render_chat(tok, system, prompts, enable_thinking)
    token_ids = [tok.encode(p, add_special_tokens=False) for p in rendered]
    return token_ids, [len(ids) for ids in token_ids]
