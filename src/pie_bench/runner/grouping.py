from __future__ import annotations

from pie_bench.engines import get_engine
from pie_bench.engines.shapes import context_tokens_for, max_model_len_for, workload_concurrency
from pie_bench.schema import Backend

SHORT_CONTEXT_TOKENS = 8192
MEMORY_BOUND_MARKS = (
    "device memory exhausted",
    "weight residency",
    "does not hold this deployment",
    "bytes of elastic device memory",
)


HEAVY_FRACTION = 0.35


def split_heavy_processes(groups: dict[tuple, list]) -> dict[tuple, list]:
    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        first = cells[0]
        per_gpu = float(first.platform.memory_gib or 0) * max(1, int(first.mode.tp))
        heavy = per_gpu > 0 and float(first.artifact.expected_gib or 0) / per_gpu > HEAVY_FRACTION
        short = [c for c in cells if context_tokens_for(c.workload) <= SHORT_CONTEXT_TOKENS]
        if not heavy or not short or len(short) == len(cells):
            out[key] = cells
            continue
        engine, artifact, mode = key
        out[(engine, artifact, f"{mode}-short")] = short
        out[(engine, artifact, f"{mode}-long")] = [c for c in cells if c not in short]
    return out


def split_draft_processes(groups: dict[tuple, list]) -> dict[tuple, list]:
    from pie_bench.engines.served import ServedEngine

    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        engine, artifact, mode = key
        cls = get_engine(cells[0].engine, str(cells[0].platform.backend))
        drafts = (
            cells[0].artifact.draft_model
            and issubclass(cls, ServedEngine)
            and cls.draft_args is not ServedEngine.draft_args
        )
        spec = [c for c in cells if c.workload.kind.value == "single_stream"] if drafts else []
        if not spec or len(spec) == len(cells):
            out[key] = cells
            continue
        out[key] = [c for c in cells if c not in spec]
        out[(engine, artifact, f"{mode}-draft")] = spec
    return out


def split_startups(groups: dict[tuple, list]) -> dict[tuple, list]:
    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        engine, artifact, mode = key
        one = [c for c in cells if workload_concurrency(c.workload) == 1]
        if getattr(
            get_engine(cells[0].engine, str(cells[0].platform.backend)), "one_request_server", False
        ) and 0 < len(one) < len(cells):
            out[(engine, artifact, f"{mode}@c1")] = one
            out[key] = [c for c in cells if c not in one]
            continue
        if str(engine) != "pie" or cells[0].platform.backend not in (Backend.CUDA, Backend.ROCM):
            out[key] = cells
            continue
        shapes: dict[tuple[int, int], list] = {}
        for c in cells:
            shapes.setdefault(
                (workload_concurrency(c.workload), max_model_len_for(c.workload)), []
            ).append(c)
        if len(shapes) == 1:
            out[key] = cells
            continue
        for (conc, ctx), sub in sorted(shapes.items()):
            out[(engine, artifact, f"{mode}@c{conc}x{ctx}")] = sub
    return out


def cell_priority(cell) -> tuple[int, float]:
    return (0 if cell.workload.kind.value == "control_aa" else 1, float(cell.workload.est_minutes))
