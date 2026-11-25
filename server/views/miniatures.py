from __future__ import annotations

from server.views.matrix_files import load
from server.views.models import artifact_to_model
from server.views.workloads import WL_PRIORITY


def _cut(a: dict) -> tuple:
    m = a.get("miniature") if a.get("kind") == "miniature" else None
    return (str(m["layers"]), m.get("experts")) if m else ("full",)


CUT = {a["id"]: _cut(a) for a in load("models")["artifacts"]}


def _miniature_labels() -> dict[str, str]:
    arts = load("models")["artifacts"]
    a2m = artifact_to_model()[0]
    full = {a2m[a["id"]]: a["layers"] for a in arts if a.get("layers") and a.get("kind", "full") == "full"}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    experts = {(a2m[a["id"]], CUT[a["id"]]) for a in arts if a.get("kind") == "miniature" and a.get("miniature")
               and a.get("platforms") and set(a["platforms"]) <= macs and a["miniature"].get("experts")}
    out = {}
    for a in arts:
        if a.get("kind") != "miniature" or not a.get("miniature"):
            continue
        model = a2m[a["id"]]
        kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(a["miniature"]["layers"]).split(","))
        out[a["id"]] = f"{kept} of {full[model]} layers" if model in full else f"{kept} layers"
        if (model, CUT[a["id"]]) in experts:
            out[a["id"]] += f", {a['miniature']['experts']} experts"
    return out


MINIATURE = _miniature_labels()


def _miniature_shapes() -> dict[str, dict]:
    arts = load("models")["artifacts"]
    full = {a["base_model"]: a for a in arts if a.get("kind", "full") == "full" and a.get("layers") and a.get("vocab")}
    out = {}
    for a in arts:
        f = full.get(a.get("base_model"))
        if a.get("kind") != "miniature" or not a.get("miniature") or not f or not f.get("params_b"):
            continue
        r = a["miniature"]
        kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(r["layers"]).split(","))
        share = kept / f["layers"]
        emb = 2 * f["vocab"] * f["hidden_size"] / 1e9
        body, active_body = f["params_b"] - emb, (f.get("active_b") or f["params_b"]) - emb
        n, top = f.get("experts"), f.get("top_k") or 0
        idle = min(1.0, max(0, (r.get("experts") or n) - top) / (n - top)) if n and n > top else 1.0
        out[a["id"]] = {"mini_active_b": round(emb + active_body * share, 3),
                        "mini_params_b": round(emb + (active_body + (body - active_body) * idle) * share, 3),
                        "mini_emb_b": round(emb, 3), "mini_layers": kept,
                        "mini_k": round(min(1.0, f["top_k"] / (r.get("experts") or f["experts"])), 3) if f.get("top_k") and f.get("experts") else 1.0}
    return out


MINI_SHAPE = _miniature_shapes()


def miniature_fields(artifact: str) -> dict:
    return {"miniature": MINIATURE.get(artifact, ""), **MINI_SHAPE.get(artifact, {})}


_FULL_BASES = {a["base_model"] for a in load("models")["artifacts"] if a.get("kind", "full") == "full" and (a.get("expected_gib") or 0) > 100}
SHOWN_MINIATURES = {a["id"] for a in load("models")["artifacts"] if a["id"] in MINIATURE and (a["base_model"] in _FULL_BASES or "smoke" not in a.get("tiers", []))}


def _cut_size(c: tuple) -> tuple:
    if c == ("full",):
        return (1, 0, 0)
    kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in c[0].split(","))
    return (0, kept, c[1] or 0)


def share_cut(rows: list[dict], a2m: dict[str, str]) -> list[dict]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}

    def counted(r):
        art = arts.get(r["artifact"], {})
        if art.get("kind") == "miniature" and r["artifact"] not in SHOWN_MINIATURES:
            return False
        return not (r["platform"] in macs and r["engine"] == "pie" and art and art.get("source_format") != "mlx")

    groups: dict[tuple, dict[str, list[dict]]] = {}
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        if cp and counted(r):
            groups.setdefault((r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0]), {}).setdefault(r["engine"], []).append(r)
    target = {}
    for g, by in groups.items():
        cuts = {CUT.get(r["artifact"], ("full",)) for rs in by.values() for r in rs}
        if len(cuts) < 2:
            continue
        newest = [CUT.get(max(rs, key=lambda r: r["started_at"])["artifact"], ("full",)) for rs in by.values()]
        ran = [{CUT.get(r["artifact"], ("full",)) for r in rs} for rs in by.values()]
        target[g] = max(cuts, key=lambda c: (newest.count(c), sum(c in s for s in ran), _cut_size(c)))
    out = []
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        t = target.get((r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])) if cp and counted(r) else None
        if t and CUT.get(r["artifact"], ("full",)) != t:
            continue
        out.append(r)
    return out
