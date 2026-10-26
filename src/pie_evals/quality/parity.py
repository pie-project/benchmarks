"""Parity of quality scores across engines.

For one model and one task, every engine that ran it is compared with pie. Two
checks, both per engine arm:

- score: the difference from pie is larger than the two 95% intervals combined
  (the half-widths added in quadrature). Flag ``mismatch``.
- answers: share of identical prompts where the greedy answer is exactly pie's.
  Only meaningful on the same weights (same scheme and checkpoint), and not for
  Splash, which renders its own chat template. Flag ``mismatch`` below 95%.

Hardware does not change accuracy, so a pie mismatch on the same model is a
pie bug until shown otherwise; the site says so.
"""

from __future__ import annotations

import math

AGREE_FLOOR = 0.95
ENGINE_RANK = {"pie": 0, "vllm": 1, "mlxlm": 1, "splash": 2, "llamacpp": 3}
#: an arm's name when its summary carries none: a vLLM arm (artifact ``<id>@vllm``) is compared with pie as mlx-lm is
LABELS = {"pie": "pie", "vllm": "vLLM", "mlxlm": "mlx-lm", "splash": "Splash", "llamacpp": "llama.cpp"}
#: engines whose answers come from their own chat template: not comparable exactly
OWN_TEMPLATE = {"splash"}


def _half(row: dict) -> float:
    return (row["ci95"][1] - row["ci95"][0]) / 2


def _answers(a: dict, b: dict) -> float | None:
    """Share of the prompts both runs answered with the same text (None when not both sampled)."""
    got_a = {s["id"]: (s.get("text") or "").strip() for s in a.get("samples") or []}
    got_b = {s["id"]: (s.get("text") or "").strip() for s in b.get("samples") or []}
    common = sorted(set(got_a) & set(got_b))
    if not common:
        return None
    return sum(got_a[i] == got_b[i] for i in common) / len(common)


def _cell(row: dict) -> dict:
    return {
        "artifact": row["artifact"], "engine": row["engine"], "label": row.get("label") or LABELS.get(row["engine"], row["engine"]),
        "scheme": row.get("scheme"), "checkpoint": row.get("checkpoint"), "score": round(row["score"], 3),
        "ci_low": round(row["ci95"][0], 3), "ci_high": round(row["ci95"][1], 3), "n": row["n"],
        "version": row.get("version"), "diff": None, "tolerance": None, "score_flag": None,
        "agree": None, "agree_flag": None,
    }


def compare(pie: dict, arm: dict, cell: dict) -> dict:
    """Fill the cell of ``arm`` against the pie row ``pie``."""
    diff = arm["score"] - pie["score"]
    tolerance = math.sqrt(_half(pie) ** 2 + _half(arm) ** 2)
    cell["diff"] = round(diff, 3)
    cell["tolerance"] = round(tolerance, 3)
    cell["score_flag"] = "mismatch" if abs(diff) > tolerance else "ok"
    known = all(r.get(k) for r in (arm, pie) for k in ("scheme", "checkpoint"))
    same_weights = known and arm["scheme"] == pie["scheme"] and arm["checkpoint"] == pie["checkpoint"]
    if arm["engine"] in OWN_TEMPLATE:
        cell["agree_flag"] = "n/a"  # its own template: the prompts are not the same text
    elif not same_weights:
        cell["agree_flag"] = "n/a"  # different weights: the answers are expected to differ
    else:
        share = _answers(pie, arm)
        cell["agree"] = None if share is None else round(share, 3)
        cell["agree_flag"] = "n/a" if share is None else ("ok" if share >= AGREE_FLOOR else "mismatch")
    return cell


def rows(summaries: list[dict]) -> list[dict]:
    """One row per (model, task) with every engine's cell: ``summaries`` are the quality rows of one tag, samples included."""
    grouped: dict[tuple[str, str], dict[str, dict]] = {}
    for s in summaries:
        grouped.setdefault((s["model"].removesuffix("@vllm"), s["task"]), {})[s["artifact"]] = s
    out = []
    for (model, task), arms in sorted(grouped.items()):
        pies = [r for r in arms.values() if r["engine"] == "pie"]
        pie = pies[0] if pies else None
        cells = []
        for art, r in sorted(arms.items(), key=lambda kv: (ENGINE_RANK.get(kv[1]["engine"], 9), kv[0])):
            cell = _cell(r)
            if pie is None:
                cell["score_flag"] = cell["agree_flag"] = "n/a"
            elif r["engine"] == "pie":
                cell["score_flag"] = cell["agree_flag"] = "reference"
            else:
                # the pie arm on the same weights when there is one (a GPU's vLLM arm against the GPU's pie arm)
                same = next((p for p in pies if (p.get("scheme"), p.get("checkpoint")) == (r.get("scheme"), r.get("checkpoint"))), pie)
                compare(same, r, cell)
                cell["vs"] = same["artifact"]
            cells.append(cell)
        flags = [c[k] for c in cells for k in ("score_flag", "agree_flag")]
        if pie is None:
            flag = "no_pie"
        else:
            flag = "mismatch" if "mismatch" in flags else "ok"
        out.append({"model": model, "task": task, "flag": flag, "pie": pie["artifact"] if pie else None, "arms": cells})
    return out
