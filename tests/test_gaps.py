"""Engine Gaps (web/assets/js/ui/board.js pieGaps) holds pie only against an engine that ran the same workload: the
m3-16g Qwen3.6-35B-A3B cell once set pie's c32 (94 tok/s) against llama.cpp's c8 (45 tok/s)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# board.js in a bare context: whatever the page has that pieGaps does not read is a stand-in that takes any key or call
HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const { file, rows } = JSON.parse(fs.readFileSync(0, "utf8"));
const auto = (own = {}) => new Proxy(Object.assign(function () {}, own), {
  get: (t, k) => (k in t ? t[k] : k === Symbol.toPrimitive ? () => "" : (t[k] = auto())),
  apply: () => auto(),
});
const ctx = vm.createContext({ console });
Object.assign(ctx, { window: ctx, addEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }),
  document: auto(), localStorage: { getItem: () => null, setItem: () => {} } });
ctx.Pie = auto({ hiddenPlatforms: new Set(), ceiling: undefined, batchedCeiling: undefined, state: { release: "t" },
  store: { snapshot: () => rows, isMeasured: () => true, tables: { engines: [{ id: "pie" }, { id: "llamacpp" }] }, index: { hardware: {} } } });
vm.runInContext(fs.readFileSync(file, "utf8"), ctx, { filename: file });
process.stdout.write(JSON.stringify(ctx.Pie.board.pieGaps(0).map((g) => [g.hardware, g.setup, g.pieValue, g.rival, g.rivalValue])));
"""


def test_pie_is_held_only_against_the_same_workload():
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    row = lambda hw, engine, benchmark, tps: {"hardware": hw, "model": "qwen3.6-35b-a3b", "miniature": "40 layers", "engine": engine,
                                              "workload": "throughput", "benchmark": benchmark, "output_tok_s": tps, "status": "pass"}
    rows = [row("m3-16g", "pie", "c32", 94.25), row("m3-16g", "llamacpp", "c8", 45.2),
            row("m2-16g", "pie", "c8", 40.0), row("m2-16g", "llamacpp", "c8", 20.0)]
    data = {"file": str(ROOT / "web/assets/js/ui/board.js"), "rows": rows}
    out = subprocess.run(["node", "-e", HARNESS], input=json.dumps(data), capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [["m2-16g", "batching", 40.0, "llamacpp", 20.0]]
