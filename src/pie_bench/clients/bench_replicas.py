from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

from bench_results import BenchSummary, RequestResult, summarize


def requests_per_replica(total: int, replicas: int) -> list[int]:
    per = [total // replicas] * replicas
    for i in range(total % replicas):
        per[i] += 1
    return per


def forwarded_argv(argv: list[str], dropped: set[str]) -> list[str]:
    forwarded, skip_next = [], False
    for token in argv:
        if skip_next:
            skip_next = False
            continue
        if token in dropped:
            skip_next = True
            continue
        if any(token.startswith(f"{flag}=") for flag in dropped):
            continue
        forwarded.append(token)
    return forwarded


def _merged_results(outs: list[str]) -> tuple[list[RequestResult], float]:
    merged: list[RequestResult] = []
    wall = 0.0
    for path in outs:
        with open(path) as fh:
            payload = json.load(fh)
        wall = max(wall, float(payload["summary"]["wall_s"]))
        merged.extend(RequestResult(**record) for record in payload["requests"])
    return merged, wall


def run_replicas(
    args: argparse.Namespace, engine: str, script: str, dropped: set[str]
) -> tuple[BenchSummary, list[RequestResult]]:
    total = args.requests if args.mode == "latency" else args.num_requests
    per = requests_per_replica(total, args.dp_size)
    forwarded = forwarded_argv(sys.argv[1:], dropped)
    count_flag = "--requests" if args.mode == "latency" else "--num-requests"
    procs, outs = [], []
    tmpdir = tempfile.mkdtemp(prefix=f"{engine}-dp-")
    for replica, count in enumerate(per):
        if count == 0:
            continue
        devices = ",".join(str(replica * args.tp_size + i) for i in range(args.tp_size))
        out = os.path.join(tmpdir, f"replica{replica}.json")
        outs.append(out)
        argv = [sys.executable, script, *forwarded, "--json-out", out, count_flag, str(count)]
        procs.append(subprocess.Popen(argv, env={**os.environ, "CUDA_VISIBLE_DEVICES": devices}))
    failures = [p.wait() for p in procs]
    if any(rc != 0 for rc in failures):
        raise RuntimeError(f"{engine} data-parallel replica failed: {failures}")
    merged, wall = _merged_results(outs)
    summary = summarize(
        mode=args.mode,
        engine=engine,
        model=args.model,
        results=merged,
        wall_s=wall,
        config={
            "data_parallel_size": args.dp_size,
            "tensor_parallel_size": args.tp_size,
            "dp_replica_requests": per,
            "max_tokens": args.max_tokens,
        },
    )
    return summary, merged
