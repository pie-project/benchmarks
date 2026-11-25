from __future__ import annotations

import base64
import gzip
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from pie_bench import submission
from pie_bench.metrics.perf import perf_from_common_json
from pie_bench.metrics.stats import cov
from pie_bench.schema import (
    Backend,
    CellStatus,
    ErrorClass,
    PerfMetrics,
    PlatformSpec,
    Provenance,
    Record,
    Tier,
)
from pie_bench.schema.cell import Cell, EngineName, Mode

SCHEMA = "pie-evals-phone/1"
PHONE_WORKLOADS = ("raw-512-256", "c4", "pf4-512")
TEST_TAG_PREFIX = "test-"
PROMPT_TOLERANCE = 0.05
PROGRAM = "text-completion-bench"
WORKLOADS_JSON = Path(__file__).resolve().parents[2] / "mobile" / "shared" / "workloads.json"


class PhoneRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool = True
    prompt_tokens: int | None = Field(default=None, ge=0, le=1_000_000)
    output_tokens: int = Field(ge=0, le=1_000_000)
    ttft_s: float | None = Field(default=None, ge=0)
    latency_s: float | None = Field(default=None, ge=0)
    cached_prompt_tokens: int | None = Field(default=0, ge=0)
    error: str | None = None


class PhoneRound(BaseModel):
    model_config = ConfigDict(extra="ignore")
    wall_s: float | None = Field(default=None, ge=0)
    peak_mem_gib: float | None = Field(default=None, ge=0)
    requests: list[PhoneRequest] = Field(default_factory=list, max_length=4096)


class PhoneDevice(BaseModel):
    model_config = ConfigDict(extra="allow")
    os: Literal["android", "ios"]
    os_version: str | None = None
    manufacturer: str | None = None
    model: str = Field(min_length=1, max_length=120)
    device: str | None = None
    soc: str | None = None
    soc_vendor: str | None = None
    gpu: str | None = None
    ram_gib: float | None = Field(default=None, ge=0, le=4096)
    cpu_cores: int | None = None
    abi: str | None = None
    emulator: bool = False


class PhoneApp(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: str = Field(min_length=1, max_length=40)
    harness_commit: str = Field(min_length=7, max_length=64)
    platform: Literal["android", "ios"]


class PhoneCheckpoint(BaseModel):
    model_config = ConfigDict(extra="allow")
    repo: str | None = None
    file: str | None = None
    revision: str | None = None
    sha256: str | None = None
    bytes: int | None = None


class PhoneRow(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    schema_: Literal[SCHEMA] = Field(alias="schema")
    run_id: str = Field(pattern=r"^phone-[A-Za-z0-9._-]{1,120}$")
    tag: str | None = Field(default=None, pattern=r"^[A-Za-z0-9._-]{1,64}$")
    started_at: datetime
    duration_s: float | None = Field(default=None, ge=0)
    app: PhoneApp
    device: PhoneDevice
    engine: Literal["llamacpp", "litert", "mlc", "mlx-swift", "pie"]
    engine_version: str = Field(min_length=1, max_length=80)
    engine_backend: str | None = Field(default=None, max_length=40)
    engine_config: dict[str, Any] = Field(default_factory=dict)
    artifact: str
    checkpoint: PhoneCheckpoint = Field(default_factory=PhoneCheckpoint)
    workload: str
    status: Literal["pass", "fail", "declared_unsupported"]
    error_class: str | None = None
    error: str | None = Field(default=None, max_length=4000)
    load_s: float | None = Field(default=None, ge=0)
    rounds: list[PhoneRound] = Field(default_factory=list, max_length=12)


class PhoneRowError(ValueError):
    pass


def parse_text(text: str) -> list[dict]:
    text = text.strip()
    if text and text[0] not in "[{":
        try:
            text = gzip.decompress(base64.b64decode("".join(text.split()), validate=True)).decode()
        except (ValueError, OSError) as e:
            raise PhoneRowError(f"neither JSON lines nor gzip+base64: {e}") from None
        text = text.strip()
    if text.startswith("["):
        return list(json.loads(text))
    if text.startswith("{") and "\n" not in text:
        one = json.loads(text)
        return list(one["rows"]) if isinstance(one, dict) and "rows" in one else [one]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read_file(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return parse_text(raw.decode())


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "unknown"


def load_phones(matrix_root: Path | str) -> dict[str, PlatformSpec]:
    import yaml

    path = Path(matrix_root) / "phones.yaml"
    phones = (yaml.safe_load(path.read_text()) or {}).get("phones", []) if path.exists() else []
    return {p["id"]: PlatformSpec(**{**p, "tiers": []}) for p in phones}


def _matches(code: str, pattern: str) -> bool:
    code, pattern = code.strip().lower(), pattern.strip().lower()
    return code.startswith(pattern[:-1]) if pattern.endswith("*") else code == pattern


def platform_for(
    device: PhoneDevice, phones: dict[str, PlatformSpec]
) -> tuple[PlatformSpec, str | None]:
    if device.emulator:
        pid = "android-emulator" if device.os == "android" else "ios-simulator"
        if pid in phones:
            return phones[pid], None
    for p in phones.values():
        if p.os == device.os and any(_matches(device.model or "", m) for m in p.device_models):
            return p, None
    pid = f"{device.os}-{_slug(device.model)}"
    spec = PlatformSpec(
        id=pid,
        os=device.os,
        backend=Backend.VULKAN if device.os == "android" else Backend.METAL,
        accelerator=device.soc or device.gpu or "unknown",
        arch=_slug(device.soc or "unknown"),
        memory_gib=round(device.ram_gib or 0, 1),
        interconnect="uma",
        tiers=[],
    )
    return (
        spec,
        f"{device.manufacturer or ''} {device.model} is not in matrix/phones.yaml: stored as {pid}",
    )


def expected_prompt_tokens(
    model: str | None, workload: str, path: Path = WORKLOADS_JSON
) -> list[int]:
    if not model or not path.exists():
        return []
    t = json.loads(path.read_text()).get("templates", {}).get(model, {})
    return [n for rnd in t.get("prompt_tokens", {}).get(workload, []) for n in rnd]


_ERROR_CLASSES = {e.value for e in ErrorClass}


def _round_perf(rnd: PhoneRound, concurrency: int, cold: bool):
    reqs = [r.model_dump() for r in rnd.requests]
    ok = [r for r in reqs if r["ok"]]
    out_tok = sum(r["output_tokens"] for r in ok)
    prompt = [r["prompt_tokens"] for r in ok]
    summary = {
        "output_tokens": out_tok,
        "prompt_tokens": sum(prompt) if all(p is not None for p in prompt) else None,
        "wall_s": rnd.wall_s or 0.0,
        "requests": len(reqs),
        "failed": len(reqs) - len(ok),
        "config": {},
    }
    if rnd.wall_s:
        summary["output_tok_per_s"] = out_tok / rnd.wall_s
    return perf_from_common_json(summary, reqs, None, concurrency=concurrency, cold_tags=cold)


@dataclass
class Outcome:
    status: CellStatus
    perf: PerfMetrics | None = None
    error_class: ErrorClass | None = None
    error: str | None = None
    invalid: str | None = None


def to_record(
    row: PhoneRow, matrix, model_of: dict[str, str] | None = None
) -> tuple[Record, list[str]]:
    art, wl = _catalog_entries(row, matrix)
    plat, warning = platform_for(row.device, load_phones(matrix.root))
    cell = Cell(
        engine=EngineName(row.engine),
        engine_version=row.engine_version,
        platform=plat,
        artifact=art,
        workload=wl,
        program=matrix.programs[PROGRAM],
        mode=Mode(),
    )
    outcome = _outcome(row, wl, (model_of or {}).get(row.artifact))
    rec = Record(
        run_id=row.run_id,
        job_id=f"{row.run_id}:{row.engine}:{row.artifact}",
        tier=Tier.TARGETED,
        cell_id=cell.cell_id,
        cell_key=cell.cell_key,
        cell=cell,
        status=outcome.status,
        error_class=outcome.error_class,
        error_message=outcome.error if outcome.status == CellStatus.FAIL else None,
        invalid_reason=outcome.invalid,
        perf=outcome.perf,
        provenance=_provenance(row),
        started_at=row.started_at,
        duration_s=row.duration_s,
    )
    missing = rec.validate_for_store()
    if missing:
        raise PhoneRowError(f"missing provenance: {', '.join(missing)}")
    return rec, [warning] if warning else []


def _catalog_entries(row: PhoneRow, matrix):
    if row.workload not in PHONE_WORKLOADS:
        raise PhoneRowError(
            f"workload {row.workload!r} is not a phone workload ({', '.join(PHONE_WORKLOADS)})"
        )
    art = matrix.artifacts.get(row.artifact)
    if art is None:
        raise PhoneRowError(f"artifact {row.artifact!r} is not in matrix/models.yaml")
    eng = matrix.engines.get(row.engine)
    if eng is None:
        raise PhoneRowError(f"engine {row.engine!r} is not in matrix/engines.yaml")
    if str(art.source_format) not in eng.formats:
        raise PhoneRowError(
            f"{row.engine} does not load {art.source_format} weights ({row.artifact})"
        )
    if row.engine == "pie" and not re.fullmatch(r"[0-9a-f]{7,40}", row.engine_version):
        raise PhoneRowError("a pie row's engine_version must be the pie commit it ran")
    return art, matrix.workloads[row.workload]


def _outcome(row: PhoneRow, wl, model: str | None) -> Outcome:
    if row.status == "fail":
        cls = ErrorClass(row.error_class) if row.error_class in _ERROR_CLASSES else ErrorClass.CRASH
        return Outcome(CellStatus.FAIL, error_class=cls, error=row.error)
    if row.status != "pass":
        return Outcome(CellStatus(row.status), invalid=row.error)
    problem = _incomplete_round(row, wl)
    if problem:
        return Outcome(CellStatus.FAIL, error_class=ErrorClass.HARNESS_INVALID, error=problem)
    perf = _median_perf(row, wl)
    mismatch = _prompt_mismatch(row, perf, model)
    if mismatch:
        return Outcome(CellStatus.FAIL, error_class=ErrorClass.INPUT_MISMATCH, error=mismatch)
    return Outcome(CellStatus.PASS, perf=perf)


def _incomplete_round(row: PhoneRow, wl) -> str | None:
    if not row.rounds:
        return "no rounds"
    want = int(wl.params.get("num_requests") or wl.params.get("requests") or 1)
    for i, rnd in enumerate(row.rounds):
        ok = sum(1 for r in rnd.requests if r.ok)
        if ok != want:
            return f"round {i}: {ok} of {want} requests completed"
    return None


def _median_perf(row: PhoneRow, wl) -> PerfMetrics:
    conc = int(wl.params.get("concurrency", 1))
    cold = bool(wl.params.get("cold_cache"))
    perfs = [_round_perf(r, conc, cold) for r in row.rounds]
    values = [getattr(p, p.primary) or 0.0 for p in perfs]
    perf = perfs[sorted(range(len(values)), key=lambda i: values[i])[len(values) // 2]]
    perf.rounds = values
    perf.cov = cov(values)
    perf.load_s = row.load_s
    peaks = [r.peak_mem_gib for r in row.rounds if r.peak_mem_gib is not None]
    perf.resident_gib = max(peaks) if peaks else None
    outs = [r.output_tokens for rnd in row.rounds for r in rnd.requests if r.ok]
    if outs and min(outs) < int(wl.params.get("decode", 1)):
        perf.counters["short_output"] = 1.0
        perf.counters["output_tokens_min"] = float(min(outs))
    return perf


def _prompt_mismatch(row: PhoneRow, perf: PerfMetrics, model: str | None) -> str | None:
    expected = expected_prompt_tokens(model, row.workload)
    got = [
        r.prompt_tokens
        for rnd in row.rounds
        for r in rnd.requests
        if r.ok and r.prompt_tokens is not None
    ]
    if not (expected and got):
        return None
    exp_mid, got_mid = median(expected), median(got)
    perf.counters["prompt_tokens_expected_p50"] = float(exp_mid)
    if abs(got_mid - exp_mid) > PROMPT_TOLERANCE * exp_mid:
        return f"prompt tokens: the engine read {got_mid:g} per request, the harness tokenizer counts {exp_mid:g}"
    return None


def _provenance(row: PhoneRow) -> Provenance:
    hw = {k: v for k, v in row.device.model_dump().items() if v is not None}
    ck = row.checkpoint
    revision = f"{ck.repo or row.artifact}@{ck.revision or ck.sha256 or 'unknown'}"
    if ck.file:
        revision += f"/{ck.file}"
    config = {
        **row.engine_config,
        **({"backend": row.engine_backend} if row.engine_backend else {}),
    }
    return Provenance(
        harness_commit=row.app.harness_commit,
        pie_commit=row.engine_version if row.engine == "pie" else None,
        engine_version=row.engine_version,
        engine_config=config,
        engine_config_recipe="phone-app",
        checkpoint_revision=revision,
        hardware_fingerprint={**hw, "app_version": row.app.version},
        os_version=f"{row.device.os} {row.device.os_version or ''}".strip(),
        runner=f"phone app {row.app.version}",
        machine_state={
            k: v
            for k, v in (row.device.model_extra or {}).items()
            if k in ("thermal_start", "thermal_end", "battery_pct", "charging")
        },
    )


def validate(
    raw: list[dict], matrix, model_of: dict[str, str] | None = None, tag: str | None = None
) -> tuple[list[tuple[PhoneRow, Record]], list[dict], list[str]]:
    good, bad, warnings = [], [], []
    for i, obj in enumerate(raw, 1):
        try:
            row = PhoneRow.model_validate(obj)
            if row.device.emulator and not (tag or row.tag or "").startswith(TEST_TAG_PREFIX):
                raise PhoneRowError(
                    f"an emulator or simulator row is stored only under a {TEST_TAG_PREFIX}* tag"
                )
            rec, warn = to_record(row, matrix, model_of)
            good.append((row, rec))
            warnings += [w for w in warn if w not in warnings]
        except (ValidationError, PhoneRowError, ValueError, KeyError) as e:
            bad.append(
                {
                    "line": i,
                    "error": str(e).splitlines()[0][:500]
                    if not isinstance(e, ValidationError)
                    else "; ".join(
                        f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()[:5]
                    ),
                }
            )
    return good, bad, warnings


def model_ids(matrix) -> dict[str, str]:
    drop = {
        "4bit",
        "bf16",
        "gguf",
        "mlx",
        "mxfp4",
        "q4",
        "q4km",
        "mtp",
        "instruct",
        "it",
        "base",
        "8k",
        "mini5",
        "mini8",
        "litert",
        "lm",
        "mlc",
        "q4f16_1",
        "q4f32_1",
    }
    out = {}
    for a in matrix.artifacts.values():
        tail = (a.base_model or a.id).split("/")[-1]
        out[a.id] = "-".join(p for p in tail.split("-") if p.lower() not in drop).lower()
    return out


def pack(good: list[tuple[PhoneRow, Record]], out: Path, *, tag: str) -> list[Path]:
    by_run: dict[str, list[tuple[PhoneRow, Record]]] = {}
    for row, rec in good:
        by_run.setdefault(row.run_id, []).append((row, rec))
    folders = []
    for run_id, pairs in by_run.items():
        d = out / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "records.jsonl").write_text("".join(rec.model_dump_json() + "\n" for _, rec in pairs))
        pie = {rec.provenance.pie_commit for _, rec in pairs if rec.provenance.pie_commit}
        commit = pie.pop() if len(pie) == 1 else None
        submission.pack(
            d,
            {
                "run_id": run_id,
                "tier": str(Tier.TARGETED),
                "tag": tag,
                "tag_kind": "manual" if tag.startswith((TEST_TAG_PREFIX, "manual-")) else "release",
                "platform": pairs[0][1].cell.platform.model_dump(mode="json"),
                "pie_commit": commit if commit and re.fullmatch(r"[0-9a-f]{40}", commit) else None,
            },
        )
        folders.append(d)
    return folders
