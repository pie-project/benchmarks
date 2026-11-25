from __future__ import annotations

from typing import Any


def expected_requests(mode_args: list[str]) -> int | None:
    for flag in ("--requests", "--num-requests"):
        if flag in mode_args:
            try:
                return int(mode_args[mode_args.index(flag) + 1])
            except (IndexError, ValueError):
                return None
    return None


def round_problem(expected: int | None, rounds: list[Any], *, prompt_tolerance: float = 0.03) -> str | None:
    for i, p in enumerate(rounds, 1):
        if p.failed:
            return f"round {i}: {p.failed} of {p.requests} requests failed"
        if expected is not None and p.requests != expected:
            return f"round {i} ran {p.requests} of {expected} requests"
    counts = {p.requests for p in rounds}
    if len(counts) > 1:
        return f"rounds ran different request counts: {sorted(counts)}"
    prompts = [p.prompt_tokens for p in rounds if p.prompt_tokens]
    if len(prompts) > 1 and (max(prompts) - min(prompts)) > prompt_tolerance * max(prompts):
        return f"rounds read different prompts: {min(prompts)}–{max(prompts)} prompt tokens"
    return None
