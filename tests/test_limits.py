"""The site's hardware limits (web/assets/js/ui/methodology.js) against the results CI Reports once flagged above them.

The limits run in node, as the browser runs them, on what tools/webdb.py exports for them: the machines
(matrix/hardware.yaml), the models (matrix/models.yaml), the workloads with each benchmark's own shape
(matrix/workloads.yaml), and each model's architecture (web/assets/js/config/architectures.js). HELD is every result
the site flagged above its limit on 2026-11-07 whose limit was wrong: each must now sit under its limit. BOUNDS keep
the fixed limits from drifting loose: each is an inequality worked out by hand from the model's config and the chip's
datasheet.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "web/assets/js/config/architectures.js", ROOT / "web/assets/js/ui/methodology.js"]

# methodology.js in a bare context: a window, no page, the store's tables from the export. Each case is a row
# (setup, engine, hardware, model, scheme, benchmark, prompt per request), and comes back as its limit's tok/s and parts
HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
const ctx = vm.createContext({ console });
ctx.window = ctx;
ctx.document = { getElementById: () => null };
ctx.localStorage = { getItem: () => null, setItem: () => {} };
const byId = (rows) => Object.fromEntries(rows.map((r) => [r.id, r]));
ctx.Pie = { store: { rows: (t) => data[t], index: { hardware: byId(data.hardware), models: byId(data.models), workloads: byId(data.workloads) } } };
for (const f of data.files) vm.runInContext(fs.readFileSync(f, "utf8"), ctx, { filename: f });
const WORKLOAD = { decode: "raw", prefill: "raw", batching: "throughput", pbatch: "prefill_batch" };
process.stdout.write(JSON.stringify(data.cases.map(([setup, engine, hardware, model, scheme, benchmark, prompt]) => {
  const row = { engine, hardware, model, scheme, benchmark, workload: WORKLOAD[setup], prompt_per_request: prompt };
  const limit = setup === "batching" ? ctx.Pie.batchedCeiling(hardware, model, scheme, benchmark) : ctx.Pie.ceiling(row, setup);
  return limit && { tps: limit.tps, parts: limit.parts };
})));
"""


@pytest.fixture(scope="module")
def webdb():
    sys.path.insert(0, str(ROOT / "tools"))
    import webdb

    return webdb


def limits(webdb, cases):
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    _, models = webdb.artifact_to_model()
    data = {"files": [str(f) for f in FILES], "hardware": webdb.hardware(), "models": models, "workloads": webdb.workloads(),
            "cases": [list(c[:7]) for c in cases]}
    out = subprocess.run(["node", "-e", HARNESS], input=json.dumps(data, default=str), capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_every_batched_benchmark_exports_its_own_shape(webdb):
    params = {w["id"]: w["params"] for w in webdb.load("workloads")["workloads"]}
    shapes = {w["id"]: w["shapes"] for w in webdb.workloads()}
    for cat, ids in (("throughput", webdb.THROUGHPUT), ("prefill_batch", webdb.PREFILL_BATCH)):
        for i in ids:
            assert shapes[cat][i] == {"concurrency": params[i]["concurrency"], "prompt_tokens": params[i]["prefill"],
                                      "output_tokens": params[i]["decode"]}, i


# (setup, engine, hardware, model, scheme, benchmark, prompt tokens per request, measured tok/s): the fastest such
# result on each set of the limit's inputs, from the 265 the site flagged on 2026-11-07. The one left out, TensorRT-LLM's
# c256 on pro6000-x1 with Qwen3.6-35B-A3B (5,308 tok/s), was not a limit error: c256 sends every request the same body,
# so a mixture of experts' batch routes alike and reads fewer experts than independent requests would
HELD = [
    ("batching", "vllm", "a100-pcie-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 8773.46),
    ("batching", "vllm", "a100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 4553.61),
    ("batching", "trtllm", "a100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c128", None, 3345.52),
    ("batching", "vllm", "a100-sxm-x1", "gemma-4-e4b", "bf16", "c1024", None, 10412.7),
    ("batching", "trtllm", "a100-sxm-x1", "gemma-4-e4b", "bf16", "c512", None, 8997.59),
    ("batching", "vllm", "a100-sxm-x1", "gpt-oss-120b", "mxfp4", "c128", None, 2644.01),
    ("batching", "vllm", "a100-sxm-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 9440.99),
    ("batching", "vllm", "a100-sxm-x1", "muse-glimmer-30b", "bf16", "c1024", None, 1999.97),
    ("batching", "trtllm", "a100-sxm-x1", "qwen3.6-27b", "bf16", "c128", None, 1569.67),
    ("batching", "trtllm", "a100-sxm-x1", "qwen3.8-27b", "bf16", "c128", None, 1572.87),
    ("batching", "vllm", "a100-sxm-x1", "qwen3.8-27b", "bf16", "c256", None, 1165.61),
    ("batching", "vllm", "a40-x1", "gemma-4-e4b", "bf16", "c1024", None, 4727.77),
    ("batching", "trtllm", "a40-x1", "gemma-4-e4b", "bf16", "c256", None, 3940.98),
    ("batching", "vllm", "a40-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 5152.88),
    ("batching", "vllm", "a40-x1", "qwen3-0.6b", "bf16", "c512", None, 11525.44),
    ("batching", "vllm", "a40-x1", "qwen3.5-0.8b", "bf16", "c256", None, 8556.95),
    ("batching", "sglang", "b200-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 28448.64),
    ("batching", "trtllm", "b200-x1", "gemma-4-26b-a4b", "bf16", "c256", None, 8172),
    ("batching", "trtllm", "b200-x1", "gemma-4-31b", "bf16", "c128", None, 4929.91),
    ("batching", "vllm", "b200-x1", "gemma-4-31b", "bf16", "c256", None, 6392.95),
    ("batching", "sglang", "b200-x1", "gemma-4-e4b", "bf16", "c512", None, 40382.86),
    ("batching", "sglang", "b200-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 25515.09),
    ("batching", "trtllm", "b200-x1", "gpt-oss-120b", "mxfp4", "c256", None, 8641.71),
    ("batching", "sglang", "b200-x1", "gpt-oss-20b", "mxfp4", "c512", None, 38840.49),
    ("batching", "vllm", "b200-x1", "muse-glimmer-30b", "bf16", "c1024", None, 12288.37),
    ("batching", "trtllm", "b200-x1", "qwen3.6-27b", "bf16", "c128", None, 5797.37),
    ("batching", "vllm", "b200-x1", "qwen3.6-27b", "bf16", "c512", None, 7366.78),
    ("batching", "sglang", "b200-x1", "qwen3.6-35b-a3b", "bf16", "c1024", None, 18527.88),
    ("batching", "trtllm", "b200-x1", "qwen3.6-35b-a3b", "bf16", "c512", None, 7685.62),
    ("batching", "trtllm", "b200-x1", "qwen3.8-27b", "bf16", "c128", None, 5548.58),
    ("batching", "vllm", "b200-x1", "qwen3.8-27b", "bf16", "c512", None, 7238.6),
    ("batching", "sglang", "h100-pcie-x1", "gemma-4-e4b", "bf16", "c512", None, 14080.54),
    ("batching", "sglang", "h100-pcie-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 14694.12),
    ("batching", "vllm", "h100-pcie-x1", "muse-glimmer-30b", "bf16", "c512", None, 3753.98),
    ("batching", "sglang", "h100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 8171.69),
    ("batching", "trtllm", "h100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c128", None, 5351.9),
    ("batching", "vllm", "h100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c512", None, 9438.95),
    ("batching", "vllm", "h100-sxm-x1", "gemma-4-e4b", "bf16", "c512", None, 22284.15),
    ("batching", "trtllm", "h100-sxm-x1", "gpt-oss-120b", "mxfp4", "c256", None, 7568.24),
    ("batching", "sglang", "h100-sxm-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 21987.12),
    ("batching", "trtllm", "h100-sxm-x1", "gpt-oss-20b", "mxfp4", "c512", None, 10500.43),
    ("batching", "vllm", "h100-sxm-x1", "muse-glimmer-30b", "bf16", "c1024", None, 5454.56),
    ("batching", "trtllm", "h100-sxm-x1", "qwen3.6-27b", "bf16", "c128", None, 3366.33),
    ("batching", "trtllm", "h100-sxm-x1", "qwen3.8-27b", "bf16", "c128", None, 3356.51),
    ("batching", "vllm", "h100-sxm-x1", "qwen3.8-27b", "bf16", "c256", None, 2350.63),
    ("batching", "vllm", "h200-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 13787.24),
    ("batching", "trtllm", "h200-x1", "gemma-4-26b-a4b", "bf16", "c256", None, 10666.46),
    ("batching", "sglang", "h200-x1", "gemma-4-31b", "bf16", "c128", None, 3271.58),
    ("batching", "sglang", "h200-x1", "gemma-4-e4b", "bf16", "c512", None, 24228.91),
    ("batching", "sglang", "h200-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 12883.37),
    ("batching", "trtllm", "h200-x1", "gpt-oss-120b", "mxfp4", "c512", None, 10084.74),
    ("batching", "sglang", "h200-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 22765.52),
    ("batching", "trtllm", "h200-x1", "gpt-oss-20b", "mxfp4", "c512", None, 18620.65),
    ("batching", "sglang", "h200-x1", "muse-glimmer-30b", "bf16", "c1024", None, 6810.34),
    ("batching", "trtllm", "h200-x1", "qwen3.6-27b", "bf16", "c128", None, 3995.09),
    ("batching", "vllm", "h200-x1", "qwen3.6-27b", "bf16", "c256", None, 4279.3),
    ("batching", "trtllm", "h200-x1", "qwen3.6-35b-a3b", "bf16", "c512", None, 14513.5),
    ("batching", "trtllm", "h200-x1", "qwen3.8-27b", "bf16", "c256", None, 4881.78),
    ("batching", "vllm", "l4-x1", "gpt-oss-20b", "mxfp4", "c256", None, 2192.91),
    ("batching", "vllm", "l40s-x1", "gemma-4-e4b", "bf16", "c256", None, 6378.7),
    ("batching", "vllm", "l40s-x1", "gpt-oss-20b", "mxfp4", "c256", None, 7690.53),
    ("batching", "vllm", "l40s-x1", "qwen3-0.6b", "bf16", "c512", None, 15784.75),
    ("batching", "trtllm", "l40s-x1", "qwen3.5-0.8b", "bf16", "c256", None, 11314.09),
    ("batching", "vllm", "l40s-x1", "qwen3.5-0.8b", "bf16", "c512", None, 11241.67),
    ("batching", "vllm", "mi300x-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 10824.9),
    ("batching", "vllm", "mi300x-x1", "qwen3.6-27b", "bf16", "c1024", None, 3080.1),
    ("batching", "sglang", "mi300x-x1", "qwen3.6-35b-a3b", "bf16", "c1024", None, 9503.38),
    ("batching", "vllm", "mi300x-x1", "qwen3.6-35b-a3b", "bf16", "c256", None, 6308.47),
    ("batching", "sglang", "mi300x-x1", "qwen3.8-27b", "bf16", "c1024", None, 2958),
    ("batching", "vllm", "mi300x-x1", "qwen3.8-27b", "bf16", "c512", None, 3087.32),
    ("batching", "trtllm", "pro4500-x1", "gemma-4-e4b", "bf16", "c128", None, 2948.35),
    ("batching", "vllm", "pro4500-x1", "gemma-4-e4b", "bf16", "c256", None, 6099.71),
    ("batching", "trtllm", "pro4500-x1", "gpt-oss-20b", "mxfp4", "c512", None, 9213.31),
    ("batching", "trtllm", "pro4500-x1", "qwen3-0.6b", "bf16", "c256", None, 15826.12),
    ("batching", "trtllm", "pro4500-x1", "qwen3.5-0.8b", "bf16", "c256", None, 17227.3),
    ("batching", "vllm", "pro6000-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 6784.88),
    ("batching", "trtllm", "pro6000-x1", "gemma-4-26b-a4b", "bf16", "c256", None, 5280.92),
    ("batching", "vllm", "pro6000-x1", "gemma-4-31b", "bf16", "c128", None, 1070.01),
    ("batching", "vllm", "pro6000-x1", "gemma-4-e4b", "bf16", "c1024", None, 14303.91),
    ("batching", "trtllm", "pro6000-x1", "gemma-4-e4b", "bf16", "c512", None, 11876.13),
    ("batching", "vllm", "pro6000-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 8536.53),
    ("batching", "trtllm", "pro6000-x1", "gpt-oss-120b", "mxfp4", "c512", None, 8877.38),
    ("batching", "vllm", "pro6000-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 16848.49),
    ("batching", "trtllm", "pro6000-x1", "gpt-oss-20b", "mxfp4", "c512", None, 19577.98),
    ("batching", "sglang", "pro6000-x1", "muse-glimmer-30b", "bf16", "c1024", None, 3787.01),
    ("batching", "vllm", "pro6000-x1", "qwen3-0.6b", "bf16", "c512", None, 29322.69),
    ("batching", "trtllm", "pro6000-x1", "qwen3.5-0.8b", "bf16", "c256", None, 21984.33),
    ("batching", "vllm", "pro6000-x1", "qwen3.5-0.8b", "bf16", "c512", None, 24367.89),
    ("batching", "trtllm", "pro6000-x1", "qwen3.6-27b", "bf16", "c128", None, 1813.79),
    ("batching", "vllm", "pro6000-x1", "qwen3.6-35b-a3b", "bf16", "c256", None, 3889.28),
    ("batching", "trtllm", "pro6000-x1", "qwen3.8-27b", "bf16", "c128", None, 1811.25),
    ("batching", "vllm", "rtx4090-x1", "gemma-4-e4b", "bf16", "c256", None, 5840.61),
    ("batching", "vllm", "rtx4090-x1", "gpt-oss-20b", "mxfp4", "c256", None, 7213.07),
    ("batching", "vllm", "rtx4090-x1", "qwen3-0.6b", "bf16", "c256", None, 18108.05),
    ("batching", "trtllm", "rtx4090-x1", "qwen3.5-0.8b", "bf16", "c128", None, 13358.57),
    ("batching", "sglang", "rtx4090-x1", "qwen3.5-0.8b", "bf16", "c256", None, 12825.78),
    ("batching", "vllm", "rtx5090-x1", "gemma-4-e4b", "bf16", "c256", None, 9748.01),
    ("batching", "trtllm", "rtx5090-x1", "gpt-oss-20b", "mxfp4", "c512", None, 17362.01),
    ("batching", "trtllm", "rtx5090-x1", "qwen3.5-0.8b", "bf16", "c512", None, 25679.31),
    ("batching", "vllm", "tpu-v5e-1", "gemma-4-e2b", "bf16", "c256", None, 8810.87),
    ("batching", "vllm", "tpu-v6e-1", "gemma-4-e2b", "bf16", "c256", None, 15112.61),
    ("batching", "vllm", "tpu-v6e-1", "gemma-4-e4b", "bf16", "c256", None, 8604.92),
    ("batching", "vllm", "tpu-v6e-1", "gpt-oss-20b", "mxfp4", "c256", None, 6109.23),
    ("batching", "pie", "a100-pcie-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 9289.05),
    ("batching", "pie", "a100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 4477.82),
    ("batching", "pie", "a100-sxm-x1", "gemma-4-e4b", "bf16", "c1024", None, 10081.79),
    ("batching", "pie", "a100-sxm-x1", "gpt-oss-120b", "mxfp4", "c128", None, 2167.88),
    ("batching", "pie", "a100-sxm-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 10314.21),
    ("batching", "pie", "a100-sxm-x1", "muse-glimmer-30b", "bf16", "c1024", None, 2252.48),
    ("batching", "pie", "a100-sxm-x1", "qwen3.5-0.8b", "bf16", "c512", None, 28010.92),
    ("batching", "pie", "a100-sxm-x1", "qwen3.6-27b", "bf16", "c64", None, 1143.3),
    ("batching", "pie", "a100-sxm-x1", "qwen3.8-27b", "bf16", "c128", None, 1134.02),
    ("batching", "pie", "a40-x1", "gemma-4-e4b", "bf16", "c1024", None, 3312.83),
    ("batching", "pie", "a40-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 4805.41),
    ("batching", "pie", "a40-x1", "qwen3.5-0.8b", "bf16", "c256", None, 11294.84),
    ("batching", "pie", "b200-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 27474.18),
    ("batching", "pie", "b200-x1", "gemma-4-31b", "bf16", "c256", None, 6127.73),
    ("batching", "pie", "b200-x1", "gemma-4-e4b", "bf16", "c512", None, 35448.38),
    ("batching", "pie", "b200-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 20971.85),
    ("batching", "pie", "b200-x1", "gpt-oss-20b", "mxfp4", "c512", None, 36024.78),
    ("batching", "pie", "b200-x1", "muse-glimmer-30b", "bf16", "c1024", None, 12978.55),
    ("batching", "pie", "b200-x1", "qwen3.6-27b", "bf16", "c512", None, 6770.54),
    ("batching", "pie", "b200-x1", "qwen3.6-35b-a3b", "bf16", "c1024", None, 22093.21),
    ("batching", "pie", "b200-x1", "qwen3.8-27b", "bf16", "c512", None, 6921.59),
    ("batching", "pie", "h100-pcie-x1", "gemma-4-e4b", "bf16", "c512", None, 11531.78),
    ("batching", "pie", "h100-pcie-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 12023.77),
    ("batching", "pie", "h100-pcie-x1", "qwen3-0.6b", "bf16", "c512", None, 33515.71),
    ("batching", "pie", "h100-sxm-x1", "gemma-4-26b-a4b", "bf16", "c512", None, 8354.89),
    ("batching", "pie", "h100-sxm-x1", "gemma-4-e4b", "bf16", "c512", None, 20932.09),
    ("batching", "pie", "h100-sxm-x1", "gpt-oss-120b", "mxfp4", "c256", None, 4560.73),
    ("batching", "pie", "h100-sxm-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 21639.75),
    ("batching", "pie", "h100-sxm-x1", "muse-glimmer-30b", "bf16", "c1024", None, 5975.02),
    ("batching", "pie", "h100-sxm-x1", "qwen3.5-0.8b", "bf16", "c1024", None, 51807.33),
    ("batching", "pie", "h100-sxm-x1", "qwen3.6-27b", "bf16", "c128", None, 2489.15),
    ("batching", "pie", "h100-sxm-x1", "qwen3.8-27b", "bf16", "c256", None, 2311.3),
    ("batching", "pie", "h200-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 14308.29),
    ("batching", "pie", "h200-x1", "gemma-4-31b", "bf16", "c128", None, 3322.52),
    ("batching", "pie", "h200-x1", "gemma-4-e4b", "bf16", "c512", None, 23721.21),
    ("batching", "pie", "h200-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 9971.08),
    ("batching", "pie", "h200-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 24880.66),
    ("batching", "pie", "h200-x1", "muse-glimmer-30b", "bf16", "c1024", None, 6419.93),
    ("batching", "pie", "h200-x1", "qwen3.5-0.8b", "bf16", "c1024", None, 60127.29),
    ("batching", "pie", "h200-x1", "qwen3.6-27b", "bf16", "c256", None, 4275.19),
    ("batching", "pie", "h200-x1", "qwen3.6-35b-a3b", "bf16", "c512", None, 13159.46),
    ("batching", "pie", "h200-x1", "qwen3.8-27b", "bf16", "c256", None, 4380.46),
    ("batching", "pie", "l4-x1", "gpt-oss-20b", "mxfp4", "c256", None, 1576.34),
    ("batching", "pie", "l40s-x1", "gemma-4-e4b", "bf16", "c256", None, 6337.43),
    ("batching", "pie", "l40s-x1", "gpt-oss-20b", "mxfp4", "c256", None, 7472.39),
    ("batching", "pie", "l40s-x1", "qwen3-0.6b", "bf16", "c512", None, 15940.46),
    ("batching", "pie", "l40s-x1", "qwen3.5-0.8b", "bf16", "c512", None, 15070.47),
    ("batching", "pie", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "c32", None, 269.36),
    ("batching", "pie", "mi300x-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 11916.86),
    ("batching", "pie", "mi300x-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 16680.3),
    ("batching", "pie", "mi300x-x1", "qwen3.6-35b-a3b", "bf16", "c1024", None, 11402.5),
    ("batching", "pie", "mi300x-x1", "qwen3.8-27b", "bf16", "c1024", None, 3145.31),
    ("batching", "pie", "pro4500-x1", "gemma-4-e4b", "bf16", "c256", None, 6423.99),
    ("batching", "pie", "pro4500-x1", "gpt-oss-20b", "mxfp4", "c512", None, 7368.73),
    ("batching", "pie", "pro4500-x1", "qwen3-0.6b", "bf16", "c256", None, 16794.99),
    ("batching", "pie", "pro4500-x1", "qwen3.5-0.8b", "bf16", "c256", None, 17703.35),
    ("batching", "pie", "pro6000-x1", "gemma-4-26b-a4b", "bf16", "c1024", None, 6438.29),
    ("batching", "pie", "pro6000-x1", "gemma-4-31b", "bf16", "c128", None, 960.21),
    ("batching", "pie", "pro6000-x1", "gemma-4-e4b", "bf16", "c1024", None, 14827.34),
    ("batching", "pie", "pro6000-x1", "gpt-oss-120b", "mxfp4", "c1024", None, 6214.56),
    ("batching", "pie", "pro6000-x1", "gpt-oss-20b", "mxfp4", "c1024", None, 19177.47),
    ("batching", "pie", "pro6000-x1", "muse-glimmer-30b", "bf16", "c1024", None, 4176.44),
    ("batching", "pie", "pro6000-x1", "qwen3-0.6b", "bf16", "c512", None, 31349.31),
    ("batching", "pie", "pro6000-x1", "qwen3.5-0.8b", "bf16", "c512", None, 35037.01),
    ("batching", "pie", "pro6000-x1", "qwen3.6-27b", "bf16", "c128", None, 1817.38),
    ("batching", "pie", "pro6000-x1", "qwen3.6-35b-a3b", "bf16", "c256", None, 4643.28),
    ("batching", "pie", "pro6000-x1", "qwen3.8-27b", "bf16", "c128", None, 1815.3),
    ("batching", "pie", "rtx4090-x1", "gemma-4-e4b", "bf16", "c256", None, 6142.58),
    ("batching", "pie", "rtx4090-x1", "gpt-oss-20b", "mxfp4", "c256", None, 7697.07),
    ("batching", "pie", "rtx4090-x1", "qwen3-0.6b", "bf16", "c256", None, 18654.52),
    ("batching", "pie", "rtx4090-x1", "qwen3.5-0.8b", "bf16", "c256", None, 19681.67),
    ("batching", "pie", "rtx5090-x1", "gemma-4-e4b", "bf16", "c256", None, 9428.68),
    ("batching", "pie", "rtx5090-x1", "gpt-oss-20b", "mxfp4", "c512", None, 11035.21),
    ("batching", "pie", "rtx5090-x1", "qwen3-0.6b", "bf16", "c256", None, 29583.07),
    ("batching", "pie", "rtx5090-x1", "qwen3.5-0.8b", "bf16", "c512", None, 30629.78),
    ("batching", "pie", "tpu-v5e-1", "gemma-4-e2b", "bf16", "c256", None, 6721.23),
    ("batching", "pie", "tpu-v6e-1", "gemma-4-e4b", "bf16", "c256", None, 6629.81),
    ("decode", "vllm", "h200-x4", "qwen3.8-flash-next", "bf16", "raw-512-256", 589.5, 197.26),
    ("decode", "sglang", "h200-x4", "qwen3.8-flash-next", "bf16", "raw-512-256", 590.6, 182.84),
    ("decode", "llamacpp", "m5-max-128g", "qwen3.8-flash-next", "gguf_q2_k", "raw-512-256", 554.5, 62.95),
    ("decode", "mlxlm", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "raw-512-256", 554.5, 60.69),
    ("decode", "pie", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "raw-512-256", 554.3, 74.96),
    ("pbatch", "mlxlm", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "pf256-512", None, 1100.85),
    ("pbatch", "trtllm", "rtx5090-x1", "gpt-oss-20b", "mxfp4", "pf64-512", None, 57987.15),
    ("pbatch", "trtllm", "rtx5090-x1", "qwen3-0.6b", "bf16", "pf64-512", None, 181100.06),
    ("pbatch", "pie", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "pf256-512", None, 1294.46),
    ("pbatch", "pie", "rtx5090-x1", "qwen3-0.6b", "bf16", "pf16-512", None, 179830.76),
    ("prefill", "llamacpp", "m5-max-128g", "qwen3.8-flash-next", "gguf_q2_k", "raw-512-256", 554.5, 966.27),
    ("prefill", "mlxlm", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "raw-512-256", 554.5, 1221.13),
    ("prefill", "sglang", "pro6000-x1", "qwen3.6-35b-a3b", "bf16", "raw-512-256", 553.1, 12685.51),
    ("prefill", "pie", "m4-pro-48g", "qwen3.5-4b", "affine_u4_g64", "raw-512-256", 554.9, 1211.5),
    ("prefill", "pie", "m4-pro-48g", "qwen3.5-9b", "affine_u4_g64", "raw-512-256", 554.4, 723.4),
    ("prefill", "pie", "m4-pro-48g", "qwen3.6-27b", "affine_u4_g64", "raw-512-256", 553.7, 214.09),
    ("prefill", "pie", "m4-pro-48g", "qwen3.8-27b", "affine_u4_g64", "raw-512-256", 554.4, 214.3),
    ("prefill", "pie", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "raw-512-256", 554.3, 1053.73),
    ("prefill", "pie", "pro6000-x1", "qwen3.6-35b-a3b", "bf16", "raw-512-256", 554.0, 12823.68),
]


def test_the_limit_holds_every_result_it_once_flagged(webdb):
    got = limits(webdb, HELD)
    over = [(*c, round(g["tps"], 1) if g else None) for c, g in zip(HELD, got) if not g or c[7] > g["tps"]]
    assert not over, over


# (case, lowest, highest): limits the fixes must keep, from first principles
BOUNDS = [
    # c1024 is held to 1,024 requests (the c32 shape it was held to gave 1,107 tok/s, under pie's 6,438)
    (("batching", "pie", "pro6000-x1", "gemma-4-26b-a4b", "bf16", "c1024", None), 6438.29, None),
    (("batching", "pie", "pro6000-x1", "gemma-4-26b-a4b", "bf16", "c32", None), None, 6438.29),
    # Qwen3.8-Flash-Next reads its 6.0 B active body and head each token, not its 51.2 B n-gram table or its MTP layer;
    # its 2-bit MLX build keeps the experts at 2.25 bits: ~3.1 GB of weights a token at 614 GB/s
    (("decode", "pie", "m5-max-128g", "qwen3.8-flash-next", "mlx_2bit", "raw-512-256", 554.0), 150, 250),
    (("decode", "vllm", "h200-x4", "qwen3.8-flash-next", "bf16", "raw-512-256", 554.0), 197.26, None),
    # Qwen3-0.6B's own 0.440 B body at the RTX 5090's 209.5 TFLOPS of dense BF16: at most 238,068 tok/s
    (("pbatch", "trtllm", "rtx5090-x1", "qwen3-0.6b", "bf16", "pf64-512", None), 181100.06, 238068),
    # gpt-oss-20b's MXFP4 experts on FP8 tensor cores (838 TFLOPS), attention and head at BF16 (209.5): between the
    # all-BF16 roof (34,493) and the all-FP8 one (138,022)
    (("pbatch", "trtllm", "rtx5090-x1", "gpt-oss-20b", "mxfp4", "pf64-512", None), 57987.15, 138022),
    # Hopper has no MX block scales: its MXFP4 experts are widened to BF16, so its limit is the BF16 one
    (("pbatch", "trtllm", "h100-sxm-x1", "gpt-oss-20b", "mxfp4", "pf64-512", None), None, 989.5e12 / (2 * 3.03575e9) * 1.001),
    # pie splits a dense SwiGLU MLP with the M4 Pro's Neural Engine; MLX runs on the GPU alone, under pie's 214 tok/s
    (("prefill", "pie", "m4-pro-48g", "qwen3.6-27b", "affine_u4_g64", "raw-512-256", 555.0), 214.09, None),
    (("prefill", "mlxlm", "m4-pro-48g", "qwen3.6-27b", "affine_u4_g64", "raw-512-256", 555.0), 126.47, 214.09),
    # Qwen3.6-35B-A3B's bf16 weights read once for the 554 tokens pie prefilled: 34.15 B (its 34.66 B without the MTP
    # layer, less the input embedding it only looks up) at the RTX PRO 6000 Server's 1,597 GB/s
    (("prefill", "pie", "pro6000-x1", "qwen3.6-35b-a3b", "bf16", "raw-512-256", 554.0), 12823.68, 554 / ((34.661 - 0.509) * 2 / 1597)),
]


@pytest.mark.parametrize("case,lowest,highest", BOUNDS, ids=[" ".join(map(str, b[0][:6])) for b in BOUNDS])
def test_a_fixed_limit_stays_within_its_bounds(webdb, case, lowest, highest):
    got = limits(webdb, [case])[0]
    assert got, case
    assert lowest is None or got["tps"] >= lowest, (got["tps"], lowest)
    assert highest is None or got["tps"] <= highest, (got["tps"], highest)
