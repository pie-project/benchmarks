from __future__ import annotations

from pie_bench.plan.suites import all_models
from pie_bench.quality.parity_table import rows as parity_rows
from server.views.matrix_files import load
from server.views.releases import is_diag_tag, local

QUALITY_TASKS = [
    ("gsm8k", "Grade-school math word problems, worked step by step", "openai/gsm8k (test)", "final number matches"),
    ("ifeval", "Following explicit instructions (length, format, keywords)", "google/IFEval", "every instruction met"),
    ("mmlu", "Multiple-choice knowledge across 57 subjects", "cais/mmlu (test)", "chosen letter matches"),
    ("arc", "Grade-school science reasoning, multiple choice", "allenai/ai2_arc (ARC-Challenge test)", "chosen letter matches"),
    ("math500", "Competition math, final answer in boxed form", "HuggingFaceH4/MATH-500", "final answer equivalent"),
]


def quality_arms(config: dict) -> list[tuple[str, str]]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out: list[tuple[str, str]] = []
    for aid in all_models(config):
        eng = next((e for e in ("llamacpp", "mlxlm", "splash") if aid.endswith(f"-{e}") or f"-{e}-" in aid), None)
        if eng:
            out.append((eng, aid))
        pie = arts.get(aid, {}).get("baseline_of")
        if pie and ("pie", pie) not in out:
            out.append(("pie", pie))
    return out


def mismatched_arms() -> dict[str, str]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for a in arts.values():
        pie = arts.get(a.get("baseline_of") or "")
        if pie and a.get("scheme") != pie.get("scheme"):
            out[a["id"]] = f"Runs {a.get('scheme')} weights where pie runs {pie.get('scheme')}: not compared"
    return out


def quality_tasks() -> list[dict]:
    from pie_bench.quality.tasks import ANSWER_TOKENS, PARITY_TASKS, TASKS

    scored = [{"id": t, "task": t, "description": d, "source": src, "scoring": sc, "max_tokens": TASKS[t][2]}
              for t, d, src, sc in QUALITY_TASKS if t in TASKS]
    parity = {"id": "parity", "task": "parity",
              "description": "Pie matches vLLM on the same weights",
              "source": ", ".join(PARITY_TASKS),
              "scoring": "mean KL, top-1 agreement",
              "max_tokens": ANSWER_TOKENS}
    return scored + [parity]


CHECKS = ("parity@", "kernels@")


def is_check(q: dict) -> bool:
    return str(q.get("task") or "").startswith(CHECKS)


def model_of(a2m: dict[str, str], model: str) -> str:
    return a2m.get(model, a2m.get(model.removesuffix("@vllm"), model.removesuffix("@vllm")))


def quality_checks(store, a2m) -> dict[str, list[dict]]:
    newest: dict[tuple, dict] = {}
    for q in store.quality():
        if not is_check(q) or is_diag_tag(q.get("tag") or ""):
            continue
        key = (q["artifact"], q["task"])
        if key not in newest or (q.get("date") or "") > (newest[key].get("date") or ""):
            newest[key] = q
    out: dict[str, list[dict]] = {"parity": [], "kernels": []}
    for (art, task), q in sorted(newest.items()):
        kind, platform = task.split("@", 1)
        row = {k: v for k, v in q.items() if k not in ("samples", "ci95", "tag_kind")}
        row.update(platform=q.get("platform") or platform, release=q.get("tag"))
        if kind == "parity":
            row["model"] = model_of(a2m, q.get("model") or art)
        else:
            errors = q.get("errors") or {}
            worst = q.get("worst") or q.get("worst_error")
            if not isinstance(worst, dict) and errors:
                name = max(errors, key=lambda n: (errors[n] or {}).get("max_abs") or 0)
                worst = {"name": name, **(errors[name] or {})}
            row["worst"] = worst if isinstance(worst, dict) else ({"max_abs": worst} if worst is not None else None)
            row.pop("errors", None)
            row["failing"] = q.get("failing") or q.get("failures") or []
        out[kind].append(row)
    return out


def quality_by_tag(store, a2m):
    from datetime import datetime

    tagged: dict[str, dict[tuple, dict]] = {}
    meta: dict[str, dict] = {}
    for q in store.quality():
        t = q.get("tag")
        if not t or is_check(q) or q.get("score") is None or not q.get("ci95") or None in q["ci95"]:
            continue
        at = datetime.fromisoformat(q["date"].replace("Z", "+00:00"))
        row = {"model": model_of(a2m, q["model"]), "engine": q["engine"], "artifact": q["artifact"],
               "task": q["task"], "score": round(q["score"], 3), "ci_low": round(q["ci95"][0], 3),
               "ci_high": round(q["ci95"][1], 3), "n": q["n"], "version": q.get("version"),
               "minutes": q.get("minutes"), "date": local(at)[:10], "release": t, "_at": at}
        key = (row["engine"], row["model"], row["artifact"], row["task"])
        if key not in tagged.setdefault(t, {}) or at > tagged[t][key]["_at"]:
            tagged[t][key] = row
        m = meta.setdefault(t, {"kind": q.get("tag_kind") or "manual", "at": at, "commit": ""})
        m["at"] = max(m["at"], at)
    return tagged, meta


def parity_by_tag(store, a2m) -> dict[str, list[dict]]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    by_tag: dict[str, list[dict]] = {}
    for q in store.quality_answers():
        t = q.get("tag")
        if not t or is_check(q):
            continue
        art = arts.get(q["artifact"], {})
        row = {**q, "model": model_of(a2m, q["model"]), "tag": t,
               "scheme": q.get("scheme") or art.get("scheme"), "checkpoint": q.get("checkpoint") or art.get("base_model")}
        by_tag.setdefault(t, []).append(row)
    web = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "webgpu"}
    refs = sorted((r for rs in by_tag.values() for r in rs if r["engine"] != "pie" and r.get("score") is not None and r.get("platform") not in web), key=lambda r: r.get("date") or "")
    for rs in by_tag.values():
        for r in [r for r in rs if r["engine"] == "pie" and r.get("platform") in web]:
            ref = next((x for x in reversed(refs) if (x["scheme"], x["checkpoint"], x["task"], x.get("n")) == (r["scheme"], r["checkpoint"], r["task"], r.get("n"))), None)
            if ref and not any(x["engine"] != "pie" and x.get("platform") == r["platform"] and x["model"] == r["model"] and x["task"] == r["task"] for x in rs):
                rs.append({**ref, "platform": r["platform"], "ref_platform": ref.get("platform") or "m5-max-128g"})
    return {t: parity_rows(rs) for t, rs in by_tag.items()}
