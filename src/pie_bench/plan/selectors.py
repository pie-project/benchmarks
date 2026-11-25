from __future__ import annotations

import operator
import re
from typing import TYPE_CHECKING, Any

from pie_bench.schema import ArtifactSpec, Cell

if TYPE_CHECKING:
    from pie_bench.plan.matrix import Matrix

_CMP = re.compile(r"^(>=|<=|>|<|!=|==)?\s*(-?\d+)$")
_OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "!=": operator.ne,
    "==": operator.eq,
    None: operator.eq,
}


_FIELD_SOURCES: dict[str, tuple[str, Any]] = {
    "engine": ("engine", str),
    "backend": ("platform", lambda p: str(p.backend)),
    "os": ("platform", lambda p: p.os),
    "arch": ("platform", lambda p: p.arch),
    "platform": ("platform", lambda p: p.id),
    "interconnect": ("platform", lambda p: p.interconnect),
    "family": ("artifact", lambda a: a.family),
    "artifact": ("artifact", lambda a: a.id),
    "scheme": ("artifact", lambda a: str(a.scheme)),
    "source_format": ("artifact", lambda a: str(a.source_format)),
    "artifact_kind": ("artifact", lambda a: str(a.kind)),
    "baseline": ("artifact", lambda a: a.baseline_of is not None),
    "program": ("program", lambda p: p.id),
    "program_category": ("program", lambda p: p.category),
    "workload": ("workload", lambda w: w.id),
    "workload_kind": ("workload", lambda w: str(w.kind)),
    "tp": ("mode", lambda m: m.tp),
    "spec_dec": ("cell", lambda c: c.mode.spec_dec),
}


def _on_cell(attr: str, get: Any) -> Any:
    return get if attr == "cell" else lambda c: get(getattr(c, attr))


_CELL_FIELDS = {k: _on_cell(attr, get) for k, (attr, get) in _FIELD_SOURCES.items()}


def _narrow(
    sels: list[tuple[Any, dict[str, Any]]], attr: str, obj: Any
) -> list[tuple[Any, dict[str, Any]]]:
    out = []
    for payload, sel in sels:
        rest: dict[str, Any] = {}
        for key, want in sel.items():
            negate = key.startswith("not_")
            src = _FIELD_SOURCES.get(key[4:] if negate else key)
            if src is None or src[0] != attr:
                rest[key] = want
            elif _field_matches(src[1](obj), want) == negate:
                break
        else:
            out.append((payload, rest))
    return out


def narrow_all(
    groups: list[list[tuple[Any, dict[str, Any]]]], attr: str, obj: Any
) -> list[list[tuple[Any, dict[str, Any]]]]:
    return [_narrow(g, attr, obj) for g in groups]


def selector_matches(sel: dict[str, Any], cell: Cell) -> bool:
    for key, want in sel.items():
        negate = key.startswith("not_")
        have = _CELL_FIELDS[key[4:] if negate else key](cell)
        if negate:
            if _field_matches(have, want):
                return False
            continue
        if not _field_matches(have, want):
            return False
    return True


def _field_matches(have: Any, want: Any) -> bool:
    if isinstance(want, list):
        return have in want
    compare = _CMP.match(want.strip()) if isinstance(want, str) and isinstance(have, int) else None
    if compare:
        op, num = compare.groups()
        return bool(_OPS[op](have, int(num)))
    return have == want


_ARTIFACT_KEYS = {"engine", "artifact", "family", "scheme", "source_format"}


def cannot_load(m: Matrix, engine: str, artifact: ArtifactSpec) -> str | None:
    have = {
        "engine": engine,
        "artifact": artifact.id,
        "family": artifact.family,
        "scheme": str(artifact.scheme),
        "source_format": str(artifact.source_format),
    }
    for rule in m.unsupported:
        if (
            rule.when
            and set(rule.when) <= _ARTIFACT_KEYS
            and all(_field_matches(have[k], v) for k, v in rule.when.items())
        ):
            return rule.reason
    return None
