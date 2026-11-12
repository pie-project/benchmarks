window.Pie = window.Pie || {};
// GPU stage profiles of the cells where the second fastest engine trails the fastest by 25% or more: both engines
// profiled on the same machine with the platform's own tracer, each step split into the same stages. A cell's verdict
// is "confirmed" when both profiles agree with the benchmark, "bad run" when one does not (the cell needs a rerun).
Pie.profiles = {
 "m4-pro-48g|qwen3.5-4b|prefill": {
  "verdict": "confirmed",
  "stage": "dense matmul",
  "stageKey": "dense_matmul",
  "stageMs": 266.578,
  "gapPct": 47,
  "profiledGapPct": 56.0,
  "unit": "ms per prompt (one request)",
  "why": "",
  "fastest": {
   "engine": "pie",
   "stepMs": 458.8361,
   "benchMs": 457.532,
   "ane": 155.9247,
   "stages": {
    "attention": 30.361,
    "dense_matmul": 352.962,
    "moe": 0,
    "norm_rope_elementwise": 7.598,
    "sampling": 0.049,
    "other_gpu": 0.805,
    "gpu_idle": 67.061
   }
  },
  "second": {
   "engine": "mlxlm",
   "stepMs": 715.646,
   "benchMs": 671.675,
   "ane": null,
   "stages": {
    "attention": 32.321,
    "dense_matmul": 619.54,
    "moe": 0,
    "norm_rope_elementwise": 14.56,
    "sampling": 0.13,
    "other_gpu": 0.362,
    "gpu_idle": 48.733
   }
  }
 },
 "m4-pro-48g|qwen3.8-flash-next|decode": {
  "verdict": "confirmed",
  "stage": "GPU idle within the step",
  "stageKey": "gpu_idle",
  "stageMs": 1.034,
  "gapPct": 30,
  "profiledGapPct": 33.4,
  "unit": "ms per output token",
  "why": "",
  "fastest": {
   "engine": "pie",
   "stepMs": 5.0355,
   "benchMs": 5.012,
   "ane": 0.0,
   "stages": {
    "attention": 0.172,
    "dense_matmul": 3.198,
    "moe": 0.621,
    "norm_rope_elementwise": 0.158,
    "sampling": 0.049,
    "other_gpu": 0.108,
    "gpu_idle": 0.73
   }
  },
  "second": {
   "engine": "mlxlm",
   "stepMs": 6.7159,
   "benchMs": 6.498,
   "ane": null,
   "stages": {
    "attention": 0.348,
    "dense_matmul": 3.259,
    "moe": 0.91,
    "norm_rope_elementwise": 0.37,
    "sampling": 0.059,
    "other_gpu": 0.007,
    "gpu_idle": 1.764
   }
  }
 },
 "m5-max-64g|gemma-4-e2b|prefill": {
  "verdict": "bad run",
  "stage": null,
  "stageKey": null,
  "stageMs": null,
  "gapPct": 33,
  "profiledGapPct": 44.9,
  "unit": "ms per prompt (one request)",
  "why": "mlxlm profiled 38.06 ms vs benchmark 34.02 ms (+12%); its unprofiled run (33.75 ms) agrees with the benchmark, so the profiler slowed it",
  "fastest": {
   "engine": "pie",
   "stepMs": 26.2599,
   "benchMs": 25.623,
   "ane": null,
   "stages": {
    "attention": 2.487,
    "dense_matmul": 15.422,
    "moe": 0,
    "norm_rope_elementwise": 1.627,
    "sampling": 0.034,
    "other_gpu": 0.932,
    "gpu_idle": 5.758
   }
  },
  "second": {
   "engine": "mlxlm",
   "stepMs": 38.0559,
   "benchMs": 34.019,
   "ane": null,
   "stages": {
    "attention": 0.742,
    "dense_matmul": 18.597,
    "moe": 0,
    "norm_rope_elementwise": 1.858,
    "sampling": 0.099,
    "other_gpu": 0.246,
    "gpu_idle": 16.508
   }
  }
 }
};
