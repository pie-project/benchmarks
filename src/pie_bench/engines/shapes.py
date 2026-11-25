from __future__ import annotations

from pie_bench.schema import WorkloadSpec

MAX_MODEL_LEN_QUANTUM = 2048


CHAT_TEMPLATE_MARGIN_TOKENS = 64


def workload_concurrency(workload: WorkloadSpec) -> int:
    p = workload.params
    kind = str(workload.kind)
    if kind in ("single_stream", "control_aa"):
        return 1
    if kind == "long_context":
        return max(1, int(p.get("concurrency", 1)))
    return max(1, int(p.get("concurrency", 8)))


def workload_num_requests(workload: WorkloadSpec) -> int:
    p = workload.params
    kind = str(workload.kind)
    if kind in ("single_stream", "control_aa"):
        return int(p.get("requests", 8))
    if kind == "long_context":
        conc = workload_concurrency(workload)
        if conc <= 1:
            return int(p.get("requests", 4))
        return int(p.get("num_requests", conc * 2))
    conc = workload_concurrency(workload)
    return int(p.get("num_requests", p.get("variants", conc * 4)))


def context_tokens_for(workload: WorkloadSpec) -> int:
    p = workload.params
    kind = str(workload.kind)
    if kind in ("single_stream", "control_aa", "long_context", "concurrency"):
        return int(p.get("prefill", 128)) + int(p.get("decode", 64))
    if kind == "prefix_shared":
        return int(p.get("shared_prefix", 1024)) + int(p.get("unique_suffix", 64)) + int(p.get("decode", 64))
    if kind == "mixed_length":
        return int(p.get("max_prompt", 4096)) + int(p.get("max_output", 1024))
    if kind == "replay":
        return 512 + 256
    raise ValueError(f"unknown workload kind {kind}")


def max_model_len_for(workload: WorkloadSpec) -> int:
    need = context_tokens_for(workload) + CHAT_TEMPLATE_MARGIN_TOKENS
    q = MAX_MODEL_LEN_QUANTUM
    return ((need + q - 1) // q) * q


def is_prefix_workload(workload: WorkloadSpec) -> bool:
    return str(workload.kind) == "prefix_shared"


def serve_envelope(workloads: list[WorkloadSpec]) -> WorkloadSpec:
    by_ctx = max(workloads, key=context_tokens_for)
    conc = max(workload_concurrency(w) for w in workloads)
    reqs = max(workload_num_requests(w) for w in workloads)
    if workload_concurrency(by_ctx) >= conc:
        return by_ctx
    kind = "concurrency" if str(by_ctx.kind) in ("single_stream", "control_aa") else by_ctx.kind
    return by_ctx.model_copy(update={"kind": kind, "params": {**by_ctx.params, "concurrency": conc, "num_requests": max(reqs, conc * 2)}})


def workload_mode_args(workload: WorkloadSpec) -> tuple[str, list[str]]:
    p = workload.params
    kind = str(workload.kind)
    if kind in ("single_stream", "control_aa"):
        return "latency", ["--requests", str(p.get("requests", 8))]
    if kind == "long_context":
        conc = int(p.get("concurrency", 1))
        if conc <= 1:
            return "latency", ["--requests", str(p.get("requests", 4))]
        return "tput", ["--num-requests", str(p.get("num_requests", conc * 2)), "--concurrency", str(conc)]
    if kind in ("concurrency", "prefix_shared", "mixed_length", "replay"):
        conc = int(p.get("concurrency", 8))
        n = int(p.get("num_requests", p.get("variants", conc * 4)))
        return "tput", ["--num-requests", str(n), "--concurrency", str(conc)]
    raise ValueError(f"unknown workload kind {kind}")
