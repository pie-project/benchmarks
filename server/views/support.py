from __future__ import annotations

import functools

from pie_bench.paths import MATRIX
from pie_bench.plan.suites import all_models
from server.views.engines import ENGINE_META
from server.views.matrix_files import load
from server.views.workloads import RAW, WL_PRIORITY


@functools.cache
def catalog_matrix():
    from pie_bench.plan.matrix import Matrix

    return Matrix.load(MATRIX)


def cells_on(platform_ids):
    m = catalog_matrix()
    wanted = set(platform_ids)
    for pid in [pid for pid in m.platforms if pid in wanted]:
        yield from m.expand(platforms=[pid])


@functools.cache
def reasoned_gpu_cells() -> list[tuple]:
    from pie_bench.plan.selectors import selector_matches

    m = catalog_matrix()
    out = []
    for c in cells_on(p.id for p in m.platforms.values() if p.os != "macos"):
        reason = c.declared_unsupported_reason
        if not reason or reason.startswith("does not fit"):
            continue
        excluded = any(selector_matches(sel, c) for sel in m.global_exclude)
        plain = (
            c.artifact.source_format.value == "hf_safetensors" and c.artifact.kind.value == "full"
        )
        out.append(
            (
                c.platform.id,
                str(c.engine),
                c.workload.id,
                c.artifact.id,
                c.program.id,
                reason,
                excluded,
                plain,
            )
        )
    return out


def unsupported_reasons(
    a2m: dict[str, str],
    config: dict,
    hardware_ids: list[str],
    engine_ids: list[str],
    model_ids: list[str],
) -> dict[tuple, str]:
    from pie_bench.plan.selectors import selector_matches
    from pie_bench.schema import Tier

    m = catalog_matrix()
    wanted = set(all_models(config))
    pie_arts = {a.baseline_of for a in m.artifacts.values() if a.id in wanted and a.baseline_of}
    arms = {
        a.id
        for a in m.artifacts.values()
        if a.id in wanted or a.id in pie_arts or a.baseline_of in pie_arts
    }
    benches = set(config.get("benchmarks", []))
    seen: dict[tuple, list[str | None]] = {}
    for c in m.cells_for(Tier.TARGETED, list(cells_on(hardware_ids))):
        if (
            c.platform.id not in hardware_ids
            or str(c.engine) not in engine_ids
            or c.artifact.id not in arms
        ):
            continue
        if (str(c.engine) == "pie") != (c.artifact.baseline_of is None):
            continue
        if benches and c.workload.id not in benches:
            continue
        model = a2m.get(c.artifact.id)
        if model not in model_ids:
            continue
        reason = next(
            (rule.reason for rule in m.unsupported if selector_matches(rule.when, c)), None
        )
        if (
            reason is None
            and c.declared_unsupported_reason
            and not c.declared_unsupported_reason.startswith("does not fit")
        ):
            reason = c.declared_unsupported_reason
        seen.setdefault((c.platform.id, str(c.engine), model), []).append(reason)
        if c.workload.id in WL_PRIORITY:
            seen.setdefault(
                (c.platform.id, str(c.engine), model, WL_PRIORITY[c.workload.id][0]), []
            ).append(reason)
    out = {k: next(r for r in rs if r) for k, rs in seen.items() if rs and all(rs)}
    names = {e: ENGINE_META.get(e, (e,))[0] for e in engine_ids}
    for hw in hardware_ids:
        for e in engine_ids:
            for model in model_ids:
                if (hw, e, model) not in seen:
                    out[(hw, e, model)] = f"{names[e]} has no build of this model"
    return out


def stack(
    order: list[str], tagged: dict[str, dict], keys: list[tuple], row, when
) -> dict[str, list[dict]]:
    snaps: dict[str, list[dict]] = {}
    newest: dict = {}
    for t in reversed(order):
        own = tagged.get(t, {})
        for key, item in own.items():
            if key not in newest or (when(item) or "") >= (when(tagged[newest[key]][key]) or ""):
                newest[key] = t
        out = []
        for key in keys:
            src = newest.get(key)
            if src is None:
                continue
            item = tagged[src][key]
            out.append(
                {
                    **row(item, key, src),
                    "stale": None if src == t else {"tag": src, "measured": when(item)},
                }
            )
        snaps[t] = out
    return snaps


def stack_sources(
    order: list[str], tagged: dict[str, dict], keys: list[tuple], when
) -> dict[str, list[tuple]]:
    sources: dict[str, list[tuple]] = {}
    newest: dict = {}
    for t in reversed(order):
        for key, item in tagged.get(t, {}).items():
            if key not in newest or (when(item) or "") >= (when(tagged[newest[key]][key]) or ""):
                newest[key] = t
        sources[t] = [(key, newest[key]) for key in keys if key in newest]
    return sources


def gpu_note(memory) -> str:
    from pie_bench.plan.matrix import gpu_gib

    return f"{round(gpu_gib(memory))}" if memory else "?"


def no_fit(
    a2m: dict[str, str],
    config: dict,
    hw_rows: list[dict],
    engine_ids: list[str],
    model_ids: list[str],
) -> dict:
    factor = float(load("support").get("fit_factor", 1.25))
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    need: dict[tuple[str, str], float] = {}
    for model in model_ids:
        for engine in engine_ids:
            if engine == "pie":
                ids = [
                    i
                    for i, a in arts.items()
                    if a2m.get(i) == model
                    and a.get("source_format") == "mlx"
                    and a.get("kind") != "miniature"
                ]
            else:
                ids = [
                    i
                    for i in all_models(config)
                    if i.endswith(f"-{engine}") and a2m.get(i) == model
                ]
            sizes = [arts[i]["expected_gib"] for i in ids if arts.get(i, {}).get("expected_gib")]
            if sizes:
                need[(model, engine)] = min(sizes) * factor
        if (model, "pie") not in need and "pie" in engine_ids:
            others = [gib for (m, _), gib in need.items() if m == model]
            if others:
                need[(model, "pie")] = min(others)
    from pie_bench.plan.matrix import gpu_gib

    out: dict[str, dict] = {}
    for hw in hw_rows:
        memory = hw.get("memory_gib")
        if not memory:
            continue
        for (model, engine), gib in need.items():
            if gib > gpu_gib(memory):
                out.setdefault(hw["id"], {}).setdefault(model, {})[engine] = round(gib, 1)
    return out


def gpu_unsupported(
    a2m: dict[str, str], gpu_ids: list[str], engine_ids: list[str], benches: list[str]
) -> dict[tuple, str]:
    gpus, engines = set(gpu_ids), set(engine_ids)
    out: dict[tuple, str] = {}
    for plat, engine, workload, art, program, reason, excluded, plain in reasoned_gpu_cells():
        if (
            plat not in gpus
            or engine not in engines
            or (benches and workload not in benches)
            or workload not in RAW
        ):
            continue
        if excluded or not plain or program != "text-completion-bench" or art not in a2m:
            continue
        out.setdefault((plat, engine, a2m[art]), reason)
    return out


def gpu_unsupported_setups(
    a2m: dict[str, str], gpu_ids: list[str], engine_ids: list[str]
) -> dict[tuple, str]:
    gpus, engines = set(gpu_ids), set(engine_ids)
    out: dict[tuple, str] = {}
    for plat, engine, workload, art, program, reason, _, _ in reasoned_gpu_cells():
        if (
            plat not in gpus
            or engine not in engines
            or workload not in WL_PRIORITY
            or program != "text-completion-bench"
            or art not in a2m
        ):
            continue
        out.setdefault((plat, engine, a2m[art], WL_PRIORITY[workload][0]), reason)
    return out


def gpu_no_fit(store, a2m: dict[str, str], hw_rows: list[dict], gpu_ids: list[str]) -> dict:
    from pie_bench.plan.matrix import gpu_gib

    factor = float(load("support").get("fit_factor", 1.25))
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    used: dict[str, set[str]] = {}
    engines: set[str] = set()
    for r in store.table().select(["platform", "engine", "artifact"]).to_pylist():
        a = arts.get(r["artifact"])
        if (
            r["platform"] in gpu_ids
            and a
            and a.get("source_format", "hf_safetensors") == "hf_safetensors"
            and a.get("kind", "full") == "full"
            and r["artifact"] in a2m
        ):
            used.setdefault(a2m[r["artifact"]], set()).add(r["artifact"])
            engines.add(r["engine"])
    weights = {
        m: min(arts[i]["expected_gib"] for i in ids if arts[i].get("expected_gib"))
        for m, ids in used.items()
        if any(arts[i].get("expected_gib") for i in ids)
    }
    factors = {p["id"]: p.get("fit_factor") or factor for p in load("platforms")["platforms"]}
    web = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "webgpu"}
    out: dict[str, dict] = {}
    for hw in hw_rows:
        if hw["id"] not in gpu_ids or hw["id"] in web or not hw.get("memory_gib"):
            continue
        cap = gpu_gib(hw["memory_gib"], hw.get("interconnect") or "pcie")
        for model, w in weights.items():
            gib = w * factors.get(hw["id"], factor)
            if gib > cap:
                out.setdefault(hw["id"], {})[model] = {e: round(gib, 1) for e in engines}
    return out
