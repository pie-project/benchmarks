"""Whether a cell's rounds measured what the workload asked for. A round that finished fewer requests,
or rounds that did not read the same prompts, give a number that describes different work: the cell
fails instead of passing on its median (vLLM's perf scripts refuse such runs the same way)."""

from __future__ import annotations

from typing import Any


def expected_requests(mode_args: list[str]) -> int | None:
    """The request count the bench client was told to finish, from its ``--requests`` / ``--num-requests``."""
    for flag in ("--requests", "--num-requests"):
        if flag in mode_args:
            try:
                return int(mode_args[mode_args.index(flag) + 1])
            except (IndexError, ValueError):
                return None
    return None


def round_problem(expected: int | None, rounds: list[Any], *, prompt_tolerance: float = 0.03) -> str | None:
    """The first reason the rounds cannot be read, or None. ``rounds`` are the rounds' PerfMetrics."""
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
