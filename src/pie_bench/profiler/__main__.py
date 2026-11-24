"""Profile one grid cell on this machine: python -m pie_bench.profiler --model gemma-4-e2b --setup decode [--upload]

Under a tracer that must launch the run (nsys, rocprofv3), the command runs itself again inside it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pie_bench import local

from . import cell, tracer_for, unit

TRACED = "PIE_BENCH_PROFILER_TRACED"


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m pie_bench.profiler", description="Profile a cell's two fastest engines end to end.")
    ap.add_argument("--model", required=True, help="model id as the site names it, e.g. gemma-4-e2b")
    ap.add_argument("--setup", required=True, choices=unit.SETUPS)
    ap.add_argument("--machine", default=None, help="this machine's id when it is not detected")
    ap.add_argument("--engines", default=None, help="two engines to compare instead of the cell's two fastest, comma-separated")
    ap.add_argument("--pie-root", type=Path, default=None, help="pie checkout to build and use (default ~/.pie-bench/pie)")
    ap.add_argument("--out", type=Path, default=None, help="folder for the run (default ~/.pie-bench/profiles/<time>)")
    ap.add_argument("--upload", action="store_true", help="post the cell to /v1/profiles")
    a = ap.parse_args()
    a.out = (a.out or local.HOME / "profiles" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")).resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    from pie_bench.paths import MATRIX
    from pie_bench.plan.matrix import Matrix

    backend = str(local.detect(Matrix.load(MATRIX), a.machine).platform.backend)
    prefix = tracer_for(backend, a.out).prefix
    if prefix and not os.environ.get(TRACED):
        os.environ[TRACED] = "1"
        argv = [*sys.argv[1:], "--out", str(a.out)] if "--out" not in sys.argv else sys.argv[1:]
        os.execvp(prefix[0], [*prefix, sys.executable, "-m", "pie_bench.profiler", *argv])
    doc = cell.profile(a.machine, a.model, a.setup, a.out, a.engines.split(",") if a.engines else None, a.pie_root)
    print(json.dumps(doc, indent=1))
    failed = [f"{s['engine']}: {s['why']}" for s in (doc["fastest"], doc["second"]) if "why" in s]
    if failed:
        sys.exit("not profiled, nothing uploaded: " + "; ".join(failed))
    if a.upload:
        print(cell.upload(doc))


if __name__ == "__main__":
    main()
