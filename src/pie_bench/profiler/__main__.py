from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pie_bench import api_client, submission
from pie_bench.machine import detect
from pie_bench.paths import HOME
from pie_bench.profiler import breakdown, rerun
from pie_bench.profiler.tracers import tracer_for

TRACED = "PIE_BENCH_PROFILER_TRACED"


def judged(docs: list[dict]) -> list[dict]:
    try:
        from server import profiles
    except ImportError:
        return [
            {
                "cell": f"{d['hardware']}|{d['model']}|{d['setup']}",
                "verdict": "not judged here: run from a checkout with fastapi",
            }
            for d in docs
        ]
    out = []
    for d in docs:
        key = f"{d['hardware']}|{d['model']}|{d['setup']}"
        if d["gap_pct"] is None or any("why" in d[s] for s in ("fastest", "second")):
            out.append(
                {
                    "cell": key,
                    "verdict": "not profiled",
                    "why": "; ".join(
                        f"{d[s]['engine']}: {d[s]['why']}"
                        for s in ("fastest", "second")
                        if "why" in d[s]
                    ),
                }
            )
        else:
            out.append({"cell": key, **profiles.judge(profiles.check({"profiles": [d]})[0])})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m pie_bench.profiler",
        description="Rerun cells' two fastest engines: the benchmark, then its profile, in one job.",
    )
    ap.add_argument(
        "cells",
        nargs="+",
        help="model:setup, the model as the site names it, e.g. gemma-4-e2b:prefill (setups: "
        + ", ".join(breakdown.SETUPS)
        + ")",
    )
    ap.add_argument("--machine", default=None, help="this machine's id when it is not detected")
    ap.add_argument(
        "--engines",
        default=None,
        help="the engines to compare instead of each cell's two fastest, comma-separated",
    )
    ap.add_argument(
        "--pie-root",
        type=Path,
        default=None,
        help="pie checkout to build and use (default ~/.pie-bench/pie)",
    )
    ap.add_argument(
        "--pie-commit",
        default=None,
        help="pie commit to build instead of the cells' pie rows' (a row's commit that today's bench client cannot start)",
    )
    ap.add_argument(
        "--tag",
        default=None,
        help="the release the records join (default: the live one, so they replace its rows)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="folder for the run (default ~/.pie-bench/profiles/<time>)",
    )
    ap.add_argument(
        "--upload",
        action="store_true",
        help="post the records to /v1/submissions (one of the token's quota) and the cells to /v1/profiles",
    )
    a = ap.parse_args()
    cells = [tuple(c.split(":", 1)) for c in a.cells]
    if any(len(c) != 2 or c[1] not in breakdown.SETUPS for c in cells):
        ap.error("each cell is model:setup")
    a.out = (
        a.out or HOME / "profiles" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    ).resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    from pie_bench.paths import MATRIX
    from pie_bench.plan.matrix import Matrix

    backend = str(detect(Matrix.load(MATRIX), a.machine).platform.backend)
    tracer = tracer_for(backend, a.out)
    if tracer.prefix and not getattr(tracer, "whole_run", False) and not os.environ.get(TRACED):
        os.environ[TRACED] = "1"
        argv = [*sys.argv[1:], "--out", str(a.out)] if "--out" not in sys.argv else sys.argv[1:]
        os.execvp(
            tracer.prefix[0], [*tracer.prefix, sys.executable, "-m", "pie_bench.profiler", *argv]
        )
    docs = rerun.profile(
        a.machine,
        cells,
        a.out,
        a.engines.split(",") if a.engines else None,
        a.pie_root,
        a.tag,
        a.pie_commit,
    )
    verdicts = judged(docs)
    (a.out / "verdicts.json").write_text(json.dumps(verdicts, indent=1))
    print(json.dumps(verdicts, indent=1))
    print(f"records: {a.out / submission.SUBMISSION}\nprofiles: {a.out / 'profiles.json'}")
    if a.upload:
        print(api_client.upload(a.out / submission.SUBMISSION))
        print(api_client.upload_profiles(docs))


if __name__ == "__main__":
    main()
