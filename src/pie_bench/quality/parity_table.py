from __future__ import annotations

import math

ENGINE_RANK = {"pie": 0, "vllm": 1, "mlxlm": 1, "splash": 2, "llamacpp": 3}
LABELS = {"pie": "pie", "vllm": "vLLM", "mlxlm": "mlx-lm", "splash": "Splash", "llamacpp": "llama.cpp"}
OWN_TEMPLATE = {"splash"}


def _half(row: dict) -> float:
    return (row["ci95"][1] - row["ci95"][0]) / 2


def _answers(a: dict, b: dict) -> float | None:
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
    diff = arm["score"] - pie["score"]
    tolerance = math.sqrt(_half(pie) ** 2 + _half(arm) ** 2)
    cell["diff"] = round(diff, 3)
    cell["tolerance"] = round(tolerance, 3)
    cell["score_flag"] = "mismatch" if diff > tolerance else "ok"
    known = all(r.get(k) for r in (arm, pie) for k in ("scheme", "checkpoint"))
    same_weights = known and arm["scheme"] == pie["scheme"] and arm["checkpoint"] == pie["checkpoint"]
    if arm["engine"] in OWN_TEMPLATE:
        cell["agree_flag"] = "n/a"
    elif not same_weights:
        cell["agree_flag"] = "n/a"
    else:
        share = _answers(pie, arm)
        cell["agree"] = None if share is None else round(share, 3)
        cell["agree_flag"] = "n/a" if share is None else "measured"
    return cell


def rows(summaries: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str], dict[str, dict]] = {}
    for s in summaries:
        if s.get("score") is None or not s.get("ci95") or None in s["ci95"]:
            continue
        grouped.setdefault((s["model"].removesuffix("@vllm"), s["task"], s.get("platform") or ""), {})[s["artifact"]] = s
    out = []
    for (model, task, platform), arms in sorted(grouped.items()):
        pies = [r for r in arms.values() if r["engine"] == "pie"]
        pie = pies[0] if pies else None
        cells = []
        for _art, r in sorted(arms.items(), key=lambda kv: (ENGINE_RANK.get(kv[1]["engine"], 9), kv[0])):
            cell = _cell(r)
            if pie is None:
                cell["score_flag"] = cell["agree_flag"] = "n/a"
            elif r["engine"] == "pie":
                cell["score_flag"] = cell["agree_flag"] = "reference"
            else:
                weights = (r.get("scheme"), r.get("checkpoint"))
                same = next((p for p in pies if all(weights) and (p.get("scheme"), p.get("checkpoint")) == weights), None)
                if same is None:
                    continue
                compare(same, r, cell)
                cell["vs"] = same["artifact"]
            cells.append(cell)
        flags = [c["score_flag"] for c in cells]
        if pie is None:
            flag = "no_pie"
        else:
            flag = "mismatch" if "mismatch" in flags else "ok"
        out.append({"model": model, "task": task, "platform": platform or None, "flag": flag, "pie": pie["artifact"] if pie else None, "arms": cells})
    return out
