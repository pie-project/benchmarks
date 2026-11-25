from __future__ import annotations

import json
import sys
from datetime import datetime

from server.views.matrix_files import load
from server.views.miniatures import miniature_fields, share_cut, shown_miniatures
from server.views.releases import local
from server.views.timing_fixes import withhold_seat_ttft
from server.views.workloads import METRICS, WL_PRIORITY


def share_workload(rows: list[dict], a2m: dict[str, str]) -> list[dict]:
    have: dict[tuple, dict[str, set]] = {}
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        if cp:
            g = (r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])
            have.setdefault(g, {}).setdefault(r["workload"], set()).add(r["engine"])
    target = {
        g: max(ws, key=lambda w: (len(ws[w]), -WL_PRIORITY[w][1]))
        for g, ws in have.items()
        if len(ws) > 1
    }
    out = []
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        g = cp and (r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])
        t = target.get(g) if g else None
        if t and r["workload"] != t and r["engine"] in have[g][t]:
            continue
        out.append(r)
    return out


def pick(rows: list[dict], a2m: dict[str, str], skipped: dict | None = None) -> dict[tuple, tuple]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    shown = shown_miniatures()
    best: dict[tuple, tuple] = {}
    cands: dict[tuple, list[tuple]] = {}
    for r in rows:
        cat_pri = WL_PRIORITY.get(r["workload"])
        if not cat_pri:
            continue
        art = arts.get(r["artifact"], {})
        mini = art.get("kind") == "miniature"
        if mini and r["artifact"] not in shown:
            if skipped is not None:
                skipped[(r.get("tag"), r["platform"], r["engine"], r["artifact"])] = (
                    "a CI fixture, never a model's number"
                )
            continue
        if r["engine"] == "splash" and WL_PRIORITY[r["workload"]][0] in ("raw", "throughput"):
            continue
        if (
            r["platform"] in macs
            and r["engine"] == "pie"
            and art
            and art.get("source_format") != "mlx"
        ):
            continue
        cat, pri = cat_pri
        model = a2m.get(r["artifact"], r["artifact"])
        key = (r["platform"], r["engine"], model, cat)
        shared = r["platform"] in macs and art.get("source_format") == "mlx"
        released = r["platform"] in macs or art.get("source_format") != "mlx"
        rank = (released, r["started_at"], not mini, -pri, shared)
        cands.setdefault(key, []).append((rank, r))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    groups: dict[tuple, list[tuple]] = {}
    for key in best:
        groups.setdefault((key[0], key[2], key[3]), []).append(key)
    for keys in groups.values():
        if len({best[k][1]["workload"] for k in keys}) < 2:
            continue
        have: dict[str, int] = {}
        for k in keys:
            for w in {r["workload"] for _, r in cands[k]}:
                have[w] = have.get(w, 0) + 1
        target = max(have, key=lambda w: (have[w], -WL_PRIORITY[w][1]))
        for k in keys:
            same = [c for c in cands[k] if c[1]["workload"] == target]
            if same:
                best[k] = max(same, key=lambda c: c[0])
    return best


def as_row(r: dict, key: tuple, tag: str) -> dict:
    hw, engine, model, cat = key
    version = (r["pie_commit"] or "")[:9] if engine == "pie" else r["engine_version"]
    row = {
        "hardware": hw,
        "engine": engine,
        "release": tag,
        "group": tag,
        "version": version or "",
        "model": model,
        "scheme": r["scheme"],
        "workload": cat,
        **{
            m: (
                round(r[m], 2)
                if isinstance(r[m], (int, float))
                and not (m == "prefill_tok_s" and cat == "throughput")
                else None
            )
            for m in METRICS
        },
        "accuracy": None,
        "commit": (r["pie_commit"] or "")[:9] if engine == "pie" else "",
        "measured": local(r["started_at"]),
        "benchmark": r["workload"],
        "prompt_per_request": prompt_per_request(r),
        "status": r["status"],
        "note": draft_note(r, engine),
        **miniature_fields(r["artifact"]),
    }
    return withhold_seat_ttft(row, r, hw, engine, cat)


def prompt_per_request(r: dict) -> float | None:
    done = int(r.get("requests") or 0) - int(r.get("failed") or 0)
    return round(r["prompt_tokens"] / done, 1) if r.get("prompt_tokens") and done > 0 else None


def draft_note(r: dict, engine: str) -> str:
    try:
        counters = json.loads(r.get("counters_json") or "{}")
    except ValueError:
        return ""
    return (
        "Speculative: drafts with a small same-family model"
        if engine != "pie" and counters.get("speculative")
        else ""
    )


def measured(r: dict) -> bool:
    return r["status"] in ("pass", "noisy") and any(
        r.get(m) is not None for m in ("decode_tok_s", "prefill_tok_s", "output_tok_s")
    )


PREFILL = ("prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99", "prompt_tokens", "requests", "failed")


def keep_decode(
    tag_rows: list[dict],
    picked: dict[tuple, tuple],
    a2m: dict[str, str],
    engine: str,
    since: datetime,
) -> None:
    earlier = pick([r for r in tag_rows if r["engine"] == engine and r["started_at"] < since], a2m)
    for key, (rank, r) in picked.items():
        if key[1] == engine and key[3] == "raw" and r["started_at"] >= since and key in earlier:
            old = earlier[key][1]
            picked[key] = (rank, {**old, **{m: r[m] for m in PREFILL}})


def results_by_tag(store, a2m, hardware_ids, engine_ids, prefill_only=None):
    cols = [
        "platform",
        "engine",
        "engine_version",
        "artifact",
        "scheme",
        "workload",
        "status",
        "pie_commit",
        "started_at",
        "tag",
        "tag_kind",
        "counters_json",
        "prompt_tokens",
        "requests",
        "failed",
        "harness_commit",
    ] + METRICS
    rows = [
        r
        for r in store.table().select(cols).to_pylist()
        if measured(r) and r["platform"] in hardware_ids and r["engine"] in engine_ids
    ]
    rows = share_workload(share_cut(rows, a2m), a2m)
    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        if r["tag"] and not r["tag"].startswith("test-"):
            by_tag.setdefault(r["tag"], []).append(r)
    skipped: dict[tuple, str] = {}
    tagged = {t: pick(rs, a2m, skipped) for t, rs in by_tag.items()}
    for (t, hw, engine, art), why in sorted(skipped.items()):
        print(f"{t}: {engine} {art} on {hw} not shown: {why}", file=sys.stderr)
    for t, p in (prefill_only or {}).items():
        if t in tagged:
            keep_decode(by_tag[t], tagged[t], a2m, p["engine"], datetime.fromisoformat(p["since"]))
    meta = {
        t: {
            "kind": rs[0]["tag_kind"] or "manual",
            "at": max(r["started_at"] for r in rs),
            "commit": next(
                (r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), ""
            ),
        }
        for t, rs in by_tag.items()
    }
    return tagged, meta
