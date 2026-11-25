from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pie_bench.paths import MATRIX
from pie_bench.plan.selectors import narrow_all, selector_matches
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
    root: Path
    global_exclude: list[dict[str, Any]] = field(default_factory=list)
    job_budget_minutes: float = 60.0
    kill_factor: float = 1.5

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
            engines=eng,
            platforms=plats,
            artifacts=arts,
            workloads=wls,
            programs=progs,
            modes=modes,
            unsupported=rules,
            fit_factor=float(sup.get("fit_factor", 1.25)),
            suites=suites,
            root=root,
            global_exclude=list(suites_raw.get("global_exclude", []) or []),
            job_budget_minutes=float(suites_raw.get("job_budget_minutes", 60)),
            kill_factor=float(suites_raw.get("kill_factor", 1.5)),
        )

    def expand(self, platforms=None, artifacts=None) -> list[Cell]:
        suite_tiers = [Tier(name) for name in self.suites]
        cells: list[Cell] = []
        for eng, plat, s_plat in self._engine_platforms(self._selector_lists(), platforms):
            for art, s_art in self._artifacts_for(eng, plat, s_plat, artifacts):
                for mode, s_mode in self._modes_for(plat, s_art):
                    for prog, s_prog in self._programs_for(eng, art, s_mode):
                        for wl in self._workloads_for(eng, prog):
                            cells.append(
                                self._cell(eng, plat, art, mode, prog, wl, s_prog, suite_tiers)
                            )
        return cells

    def _engine_platforms(
        self, sels: list, platforms
    ) -> Iterator[tuple[EngineDecl, PlatformSpec, list]]:
        for eng in self.engines.values():
            s_eng = narrow_all(sels, "engine", EngineName(eng.id))
            for plat in self.platforms.values():
                if plat.os not in eng.os or (platforms and plat.id not in platforms):
                    continue
                if eng.backends is None or str(plat.backend) in eng.backends:
                    yield eng, plat, narrow_all(s_eng, "platform", plat)

    def _artifacts_for(
        self, eng: EngineDecl, plat: PlatformSpec, sels: list, artifacts
    ) -> Iterator[tuple[ArtifactSpec, list]]:
        for art in self.artifacts.values():
            if artifacts and art.id not in artifacts:
                continue
            if str(art.source_format) not in eng.formats:
                continue
            if art.platforms is None or plat.id in art.platforms:
                yield art, narrow_all(sels, "artifact", art)

    def _modes_for(self, plat: PlatformSpec, sels: list) -> Iterator[tuple[Mode, list]]:
        for mode in self.modes.values():
            if mode.tp <= 1 or (plat.count >= mode.tp and plat.tp_capable):
                yield mode, narrow_all(sels, "mode", mode)

    def _programs_for(
        self, eng: EngineDecl, art: ArtifactSpec, sels: list
    ) -> Iterator[tuple[ProgramSpec, list]]:
        for prog in self.programs.values():
            if prog.pie_only and eng.id != "pie":
                continue
            if prog.families is None or art.family in prog.families:
                yield prog, narrow_all(sels, "program", prog)

    def _workloads_for(self, eng: EngineDecl, prog: ProgramSpec) -> Iterator[WorkloadSpec]:
        for wl in self.workloads.values():
            if prog.workloads is not None and wl.id not in prog.workloads:
                continue
            if wl.kind.value != "control_aa" or eng.id == "pie":
                yield wl

    def _cell(
        self,
        eng: EngineDecl,
        plat: PlatformSpec,
        art: ArtifactSpec,
        mode: Mode,
        prog: ProgramSpec,
        wl: WorkloadSpec,
        sels: list,
        suite_tiers: list[Tier],
    ) -> Cell:
        cell_mode = mode.model_copy(update={"spec_dec": prog.spec_dec}) if prog.spec_dec else mode
        cell = Cell(
            engine=EngineName(eng.id),
            engine_version=eng.pin_for(plat.backend.value),
            platform=plat,
            artifact=art,
            workload=wl,
            program=prog,
            mode=cell_mode,
        )
        cell.tiers = self._tiers_for(eng, plat, art, wl, prog, mode)
        reason = self._physical_reason(cell) or next(
            (r.reason for r, sel in sels[0] if selector_matches(sel, cell)), None
        )
        if reason:
            cell.declared_unsupported_reason = reason
        self._apply_suites_one(cell, sels, suite_tiers)
        return cell

    def _selector_lists(self) -> list[list[tuple[Any, dict[str, Any]]]]:
        out: list[list[tuple[Any, dict[str, Any]]]] = [
            [(r, r.when) for r in self.unsupported],
            [(None, s) for s in self.global_exclude],
        ]
        for suite in self.suites.values():
            out += [[(None, s) for s in suite.exclude], [(None, s) for s in suite.include]]
        return out

    @staticmethod
    def _apply_suites_one(
        c: Cell, groups: list[list[tuple[Any, dict[str, Any]]]], suite_tiers: list[Tier]
    ) -> None:
        if groups[1] and any(selector_matches(sel, c) for _, sel in groups[1]):
            c.tiers = []
        for k, tier in enumerate(suite_tiers):
            exclude, include = groups[2 + 2 * k], groups[3 + 2 * k]
            if exclude and tier in c.tiers and any(selector_matches(sel, c) for _, sel in exclude):
                c.tiers.remove(tier)
            if (
                include
                and tier not in c.tiers
                and any(selector_matches(sel, c) for _, sel in include)
            ):
                c.tiers.append(tier)

    def _tiers_for(
        self,
        eng: EngineDecl,
        plat: PlatformSpec,
        art: ArtifactSpec,
        wl: WorkloadSpec,
        prog: ProgramSpec,
        mode: Mode,
    ) -> list[Tier]:
        s = (
            set(eng.tiers)
            & set(plat.tiers)
            & set(art.tiers)
            & set(wl.tiers)
            & set(prog.tiers)
            & set(mode.tiers)
        )
        return [t for t in Tier if t in s]

    def _physical_reason(self, cell: Cell) -> str | None:
        if cell.artifact.max_context:
            need = int(cell.workload.params.get("prefill", 0)) + int(
                cell.workload.params.get("decode", 0)
            )
            if cell.workload.kind.value == "prefix_shared":
                need = (
                    int(cell.workload.params.get("shared_prefix", 0))
                    + int(cell.workload.params.get("unique_suffix", 0))
                    + int(cell.workload.params.get("decode", 0))
                )
            if need > cell.artifact.max_context:
                return f"shape needs {need} tokens > the artifact's max_context {cell.artifact.max_context}"
        if str(cell.mode.spec_dec or "").startswith("dflash") and not cell.artifact.pie_drafter:
            return "the artifact ships no draft head for a dflash program to draft with"
        if cell.workload.params.get("speculation") is True and not drafts(cell):
            return f"{cell.engine} has no drafter for this model"
        if cell.artifact.expected_gib is not None:
            per_device = (
                cell.artifact.expected_gib
                * (cell.platform.fit_factor or self.fit_factor)
                / max(1, cell.mode.tp)
            )
            available = (
                cell.platform.memory_gib / max(1, cell.platform.count)
                if cell.platform.interconnect != "uma"
                else gpu_gib(cell.platform.memory_gib)
            )
            if per_device > available:
                return f"does not fit: {per_device:.1f} GiB per device > {available:.1f} GiB"
        return None

    def cells_for(self, tier: Tier, cells: list[Cell] | None = None) -> list[Cell]:
        cells = cells if cells is not None else self.expand()
        return [c for c in cells if tier in c.tiers]

    def runnable(self, tier: Tier, cells: list[Cell] | None = None) -> list[Cell]:
        return [c for c in self.cells_for(tier, cells) if c.declared_unsupported_reason is None]


def drafts(cell: Cell) -> bool:
    engine = str(cell.engine)
    if engine == "splash":
        return True
    if engine == "pie":
        return "dflash" in (cell.artifact.pie_sku or "")
    if engine in ("llamacpp", "mlxlm"):
        return bool(cell.artifact.draft_model)
    return False
