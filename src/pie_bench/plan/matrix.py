from __future__ import annotations

import operator
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pie_bench.paths import MATRIX
from pie_bench.schema import (
    ArtifactSpec,
    Cell,
    EngineName,
    Mode,
    PlatformSpec,
    ProgramSpec,
    Tier,
    WorkloadSpec,
)


def gpu_gib(memory_gib: float, interconnect: str | None = "uma") -> float:
    if interconnect != "uma":
        return memory_gib
    return memory_gib * (2 / 3 if memory_gib <= 36 else 0.75)


@dataclass
class EngineDecl:
    id: str
    os: list[str]
    formats: list[str]
    tiers: list[Tier]
    recipe: str = "default"
    pin: str | None = None
    backend_pins: dict[str, str] = field(default_factory=dict)
    release_source: str | None = None
    backends: list[str] | None = None

    def pin_for(self, backend: str | None) -> str | None:
        return self.backend_pins.get(str(backend or ""), self.pin)


@dataclass
class SupportRule:
    when: dict[str, Any]
    reason: str


@dataclass
class SuiteDecl:
    max_jobs_per_platform: int = 1
    enforce_budget: bool = True
    exclude: list[dict[str, Any]] = field(default_factory=list)
    include: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Matrix:
    engines: dict[str, EngineDecl]
    platforms: dict[str, PlatformSpec]
    artifacts: dict[str, ArtifactSpec]
    workloads: dict[str, WorkloadSpec]
    programs: dict[str, ProgramSpec]
    modes: dict[str, Mode]
    unsupported: list[SupportRule]
    fit_factor: float
    suites: dict[str, SuiteDecl]
    escalation: dict[str, Any]
    root: Path
    global_exclude: list[dict[str, Any]] = field(default_factory=list)
    job_budget_minutes: float = 60.0
    kill_factor: float = 1.5

    @property
    def kill_minutes(self) -> int:
        return int(round(self.job_budget_minutes * self.kill_factor))

    @classmethod
    def load(cls, root: Path | str = MATRIX) -> Matrix:
        root = Path(root)

        def read(name: str) -> dict:
            with open(root / name) as f:
                return yaml.safe_load(f) or {}

        eng = {e["id"]: EngineDecl(**e) for e in read("engines.yaml")["engines"]}
        plats = {p["id"]: PlatformSpec(**p) for p in read("platforms.yaml")["platforms"]}
        arts = {a["id"]: ArtifactSpec(**a) for a in read("models.yaml")["artifacts"]}
        wls = {w["id"]: WorkloadSpec(**w) for w in read("workloads.yaml")["workloads"]}
        progs = {p["id"]: ProgramSpec(**p) for p in read("programs.yaml")["programs"]}
        modes = {m["id"]: Mode(**m) for m in read("modes.yaml")["modes"]}
        sup = read("support.yaml")
        rules = [SupportRule(r["when"], r["reason"]) for r in sup.get("unsupported", [])]
        suites_raw = read("suites.yaml")
        suites = {k: SuiteDecl(**v) for k, v in suites_raw.get("suites", {}).items()}
        return cls(
            engines=eng, platforms=plats, artifacts=arts, workloads=wls, programs=progs, modes=modes,
            unsupported=rules, fit_factor=float(sup.get("fit_factor", 1.25)), suites=suites,
            escalation=suites_raw.get("escalation", {}), root=root,
            global_exclude=list(suites_raw.get("global_exclude", []) or []),
            job_budget_minutes=float(suites_raw.get("job_budget_minutes", 60)),
            kill_factor=float(suites_raw.get("kill_factor", 1.5)),
        )

    def expand(self, platforms=None, artifacts=None) -> list[Cell]:
        sels = self._selector_lists()
        suite_tiers = [Tier(name) for name in self.suites]
        cells: list[Cell] = []
        for eng in self.engines.values():
            s_eng = _narrow_all(sels, "engine", EngineName(eng.id))
            for plat in self.platforms.values():
                if plat.os not in eng.os or (platforms and plat.id not in platforms):
                    continue
                if eng.backends is not None and str(plat.backend) not in eng.backends:
                    continue
                s_plat = _narrow_all(s_eng, "platform", plat)
                for art in self.artifacts.values():
                    if artifacts and art.id not in artifacts:
                        continue
                    if str(art.source_format) not in eng.formats:
                        continue
                    if art.platforms is not None and plat.id not in art.platforms:
                        continue
                    s_art = _narrow_all(s_plat, "artifact", art)
                    for mode in self.modes.values():
                        if mode.tp > 1 and (plat.count < mode.tp or not plat.tp_capable):
                            continue
                        s_mode = _narrow_all(s_art, "mode", mode)
                        for prog in self.programs.values():
                            if prog.pie_only and eng.id != "pie":
                                continue
                            if prog.families is not None and art.family not in prog.families:
                                continue
                            s_prog = _narrow_all(s_mode, "program", prog)
                            for wl in self.workloads.values():
                                if prog.workloads is not None and wl.id not in prog.workloads:
                                    continue
                                if wl.kind.value == "control_aa" and eng.id != "pie":
                                    continue
                                cell_mode = mode.model_copy(update={"spec_dec": prog.spec_dec}) if prog.spec_dec else mode
                                cell = Cell(
                                    engine=EngineName(eng.id), engine_version=eng.pin_for(plat.backend.value), platform=plat,
                                    artifact=art, workload=wl, program=prog, mode=cell_mode,
                                )
                                cell.tiers = self._tiers_for(eng, plat, art, wl, prog, mode)
                                reason = self._physical_reason(cell) or next(
                                    (r.reason for r, sel in s_prog[0] if selector_matches(sel, cell)), None)
                                if reason:
                                    cell.declared_unsupported_reason = reason
                                self._apply_suites_one(cell, s_prog, suite_tiers)
                                cells.append(cell)
        return cells

    def _selector_lists(self) -> list[list[tuple[Any, dict[str, Any]]]]:
        out: list[list[tuple[Any, dict[str, Any]]]] = [[(r, r.when) for r in self.unsupported], [(None, s) for s in self.global_exclude]]
        for suite in self.suites.values():
            out += [[(None, s) for s in suite.exclude], [(None, s) for s in suite.include]]
        return out

    @staticmethod
    def _apply_suites_one(c: Cell, groups: list[list[tuple[Any, dict[str, Any]]]], suite_tiers: list[Tier]) -> None:
        if groups[1] and any(selector_matches(sel, c) for _, sel in groups[1]):
            c.tiers = []
        for k, tier in enumerate(suite_tiers):
            exclude, include = groups[2 + 2 * k], groups[3 + 2 * k]
            if exclude and tier in c.tiers and any(selector_matches(sel, c) for _, sel in exclude):
                c.tiers.remove(tier)
            if include and tier not in c.tiers and any(selector_matches(sel, c) for _, sel in include):
                c.tiers.append(tier)

    def _tiers_for(self, eng: EngineDecl, plat: PlatformSpec, art: ArtifactSpec, wl: WorkloadSpec, prog: ProgramSpec, mode: Mode) -> list[Tier]:
        s = set(eng.tiers) & set(plat.tiers) & set(art.tiers) & set(wl.tiers) & set(prog.tiers) & set(mode.tiers)
        return [t for t in Tier if t in s]

    def _physical_reason(self, cell: Cell) -> str | None:
        if cell.artifact.max_context:
            need = int(cell.workload.params.get("prefill", 0)) + int(cell.workload.params.get("decode", 0))
            if cell.workload.kind.value == "prefix_shared":
                need = int(cell.workload.params.get("shared_prefix", 0)) + int(cell.workload.params.get("unique_suffix", 0)) + int(cell.workload.params.get("decode", 0))
            if need > cell.artifact.max_context:
                return f"shape needs {need} tokens > the artifact's max_context {cell.artifact.max_context}"
        if str(cell.mode.spec_dec or "").startswith("dflash") and not cell.artifact.pie_drafter:
            return "the artifact ships no draft head for a dflash program to draft with"
        if cell.workload.params.get("speculation") is True and not drafts(cell):
            return f"{cell.engine} has no drafter for this model"
        if cell.artifact.expected_gib is not None:
            per_device = cell.artifact.expected_gib * (cell.platform.fit_factor or self.fit_factor) / max(1, cell.mode.tp)
            available = cell.platform.memory_gib / max(1, cell.platform.count) if cell.platform.interconnect != "uma" else gpu_gib(cell.platform.memory_gib)
            if per_device > available:
                return f"does not fit: {per_device:.1f} GiB per device > {available:.1f} GiB"
        return None

    def cells_for(self, tier: Tier, cells: list[Cell] | None = None) -> list[Cell]:
        cells = cells if cells is not None else self.expand()
        return [c for c in cells if tier in c.tiers]

    def runnable(self, tier: Tier, cells: list[Cell] | None = None) -> list[Cell]:
        return [c for c in self.cells_for(tier, cells) if c.declared_unsupported_reason is None]

    def budget_report(self, tier: Tier, cells: list[Cell] | None = None) -> dict[str, dict[str, float]]:
        from pie_bench.plan.jobs import shard_groups

        out: dict[str, dict[str, float]] = {}
        by_plat: dict[str, list[Cell]] = {}
        for c in self.runnable(tier, cells):
            by_plat.setdefault(c.platform.id, []).append(c)
        for plat, pc in by_plat.items():
            minutes = sum(c.workload.est_minutes for c in pc)
            shards = shard_groups(pc, self.job_budget_minutes)
            out[plat] = {"minutes": minutes, "shards": len(shards), "max_shard_minutes": max((sum(c.workload.est_minutes for c in sh) for sh in shards), default=0.0)}
        return out

    def check_budget(self, tier: Tier, cells: list[Cell] | None = None, *, enforced_only: bool = False) -> list[str]:
        suite = self.suites.get(tier.value)
        if not suite or (enforced_only and not suite.enforce_budget):
            return []
        problems = []
        for plat, r in self.budget_report(tier, cells).items():
            if r["shards"] > suite.max_jobs_per_platform:
                problems.append(f"{tier}: platform {plat} needs {int(r['shards'])} jobs of ~{self.job_budget_minutes:.0f} min ({r['minutes']:.0f} min total) > max_jobs_per_platform {suite.max_jobs_per_platform}")
            if r["max_shard_minutes"] > self.job_budget_minutes * self.kill_factor:
                problems.append(f"{tier}: platform {plat} has a single process group of {r['max_shard_minutes']:.0f} min that cannot fit a {self.job_budget_minutes:.0f}-min job")
        return problems


_CMP = re.compile(r"^(>=|<=|>|<|!=|==)?\s*(-?\d+)$")
_OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "!=": operator.ne, "==": operator.eq, None: operator.eq}


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


def _narrow(sels: list[tuple[Any, dict[str, Any]]], attr: str, obj: Any) -> list[tuple[Any, dict[str, Any]]]:
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


def _narrow_all(groups: list[list[tuple[Any, dict[str, Any]]]], attr: str, obj: Any) -> list[list[tuple[Any, dict[str, Any]]]]:
    return [_narrow(g, attr, obj) for g in groups]


def _cell_field(cell: Cell, key: str) -> Any:
    return _CELL_FIELDS[key](cell)


def selector_matches(sel: dict[str, Any], cell: Cell) -> bool:
    for key, want in sel.items():
        negate = key.startswith("not_")
        have = _cell_field(cell, key[4:] if negate else key)
        if negate:
            if _field_matches(have, want):
                return False
            continue
        if not _field_matches(have, want):
            return False
    return True


def _field_matches(have: Any, want: Any) -> bool:
    if True:
        if isinstance(want, list):
            return have in want
        if isinstance(want, str) and isinstance(have, int) and _CMP.match(want.strip()):
            op, num = _CMP.match(want.strip()).groups()
            return bool(_OPS[op](have, int(num)))
        return have == want


_ARTIFACT_KEYS = {"engine", "artifact", "family", "scheme", "source_format"}


def cannot_load(m: Matrix, engine: str, artifact: ArtifactSpec) -> str | None:
    have = {"engine": engine, "artifact": artifact.id, "family": artifact.family,
            "scheme": str(artifact.scheme), "source_format": str(artifact.source_format)}
    for rule in m.unsupported:
        if rule.when and set(rule.when) <= _ARTIFACT_KEYS and all(_field_matches(have[k], v) for k, v in rule.when.items()):
            return rule.reason
    return None


def summarize(cells: Iterable[Cell]) -> dict[str, int]:
    out: dict[str, int] = {"total": 0, "declared_unsupported": 0}
    for c in cells:
        out["total"] += 1
        if c.declared_unsupported_reason:
            out["declared_unsupported"] += 1
        for t in c.tiers:
            out[f"tier:{t}"] = out.get(f"tier:{t}", 0) + 1
    return out


def drafts(cell: Cell) -> bool:
    engine = str(cell.engine)
    if engine == "splash":
        return True
    if engine == "pie":
        return "dflash" in (cell.artifact.pie_sku or "")
    if engine in ("llamacpp", "mlxlm"):
        return bool(cell.artifact.draft_model)
    return False
