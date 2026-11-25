from __future__ import annotations

import functools

from server.views.matrix_files import catalog, load
from server.views.models import artifact_to_model
from server.views.workloads import WL_PRIORITY

FULL = ("full",)


def kept_layers(layers: str) -> int:
    return sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(layers).split(","))


def _cut(a: dict) -> tuple:
    m = a.get("miniature") if a.get("kind") == "miniature" else None
    return (str(m["layers"]), m.get("experts")) if m else FULL


@functools.cache
def cuts() -> dict[str, tuple]:
    return {a["id"]: _cut(a) for a in load("models")["artifacts"]}


def cut_of(artifact: str) -> tuple:
    return cuts().get(artifact, FULL)


@functools.cache
def miniature_labels() -> dict[str, str]:
    arts = load("models")["artifacts"]
    a2m = artifact_to_model()[0]
    full = {
        a2m[a["id"]]: a["layers"]
        for a in arts
        if a.get("layers") and a.get("kind", "full") == "full"
    }
    macs = {p["id"] for p in catalog("platforms")["platforms"] if p.get("os") == "macos"}
    experts = {
        (a2m[a["id"]], cuts()[a["id"]])
        for a in arts
        if a.get("kind") == "miniature"
        and a.get("miniature")
        and a.get("platforms")
        and set(a["platforms"]) <= macs
        and a["miniature"].get("experts")
    }
    out = {}
    for a in arts:
        if a.get("kind") != "miniature" or not a.get("miniature"):
            continue
        model = a2m[a["id"]]
        kept = kept_layers(a["miniature"]["layers"])
        out[a["id"]] = f"{kept} of {full[model]} layers" if model in full else f"{kept} layers"
        if (model, cuts()[a["id"]]) in experts:
            out[a["id"]] += f", {a['miniature']['experts']} experts"
    return out


def _shape(a: dict, f: dict) -> dict:
    r = a["miniature"]
    kept = kept_layers(r["layers"])
    share = kept / f["layers"]
    emb = 2 * f["vocab"] * f["hidden_size"] / 1e9
    body, active_body = f["params_b"] - emb, (f.get("active_b") or f["params_b"]) - emb
    n, top = f.get("experts"), f.get("top_k") or 0
    idle = min(1.0, max(0, (r.get("experts") or n) - top) / (n - top)) if n and n > top else 1.0
    k = (
        round(min(1.0, f["top_k"] / (r.get("experts") or f["experts"])), 3)
        if f.get("top_k") and f.get("experts")
        else 1.0
    )
    return {
        "mini_active_b": round(emb + active_body * share, 3),
        "mini_params_b": round(emb + (active_body + (body - active_body) * idle) * share, 3),
        "mini_emb_b": round(emb, 3),
        "mini_layers": kept,
        "mini_k": k,
    }


@functools.cache
def miniature_shapes() -> dict[str, dict]:
    arts = load("models")["artifacts"]
    full = {
        a["base_model"]: a
        for a in arts
        if a.get("kind", "full") == "full" and a.get("layers") and a.get("vocab")
    }
    out = {}
    for a in arts:
        f = full.get(a.get("base_model"))
        if a.get("kind") == "miniature" and a.get("miniature") and f and f.get("params_b"):
            out[a["id"]] = _shape(a, f)
    return out


def miniature_fields(artifact: str) -> dict:
    return {
        "miniature": miniature_labels().get(artifact, ""),
        **miniature_shapes().get(artifact, {}),
    }


@functools.cache
def shown_miniatures() -> set[str]:
    arts = load("models")["artifacts"]
    labels = miniature_labels()
    big = {
        a["base_model"]
        for a in arts
        if a.get("kind", "full") == "full" and (a.get("expected_gib") or 0) > 100
    }
    return {
        a["id"]
        for a in arts
        if a["id"] in labels and (a["base_model"] in big or "smoke" not in a.get("tiers", []))
    }


def _cut_size(c: tuple) -> tuple:
    if c == FULL:
        return (1, 0, 0)
    return (0, kept_layers(c[0]), c[1] or 0)


def share_cut(rows: list[dict], a2m: dict[str, str]) -> list[dict]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    shown = shown_miniatures()

    def counted(r):
        art = arts.get(r["artifact"], {})
        if art.get("kind") == "miniature" and r["artifact"] not in shown:
            return False
        return not (
            r["platform"] in macs
            and r["engine"] == "pie"
            and art
            and art.get("source_format") != "mlx"
        )

    def group(r):
        cp = WL_PRIORITY.get(r["workload"])
        return (
            (r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])
            if cp and counted(r)
            else None
        )

    groups: dict[tuple, dict[str, list[dict]]] = {}
    for r in rows:
        g = group(r)
        if g:
            groups.setdefault(g, {}).setdefault(r["engine"], []).append(r)
    target = {}
    for g, by in groups.items():
        seen = {cut_of(r["artifact"]) for rs in by.values() for r in rs}
        if len(seen) < 2:
            continue
        newest = [cut_of(max(rs, key=lambda r: r["started_at"])["artifact"]) for rs in by.values()]
        ran = [{cut_of(r["artifact"]) for r in rs} for rs in by.values()]
        target[g] = max(
            seen, key=lambda c: (newest.count(c), sum(c in s for s in ran), _cut_size(c))
        )
    out = []
    for r in rows:
        g = group(r)
        t = target.get(g) if g else None
        if t and cut_of(r["artifact"]) != t:
            continue
        out.append(r)
    return out
