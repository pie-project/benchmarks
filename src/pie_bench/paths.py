import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
MATRIX = PACKAGE / "matrix"
CLIENTS = PACKAGE / "clients"
CONFIG = PACKAGE / "config.json"


HOME = Path(os.environ.get("PIE_BENCH_HOME") or Path.home() / ".pie-bench")
