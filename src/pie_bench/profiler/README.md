# Profiler

```
python -m pie_bench.profiler gemma-4-e2b:prefill qwen3.5-4b:pbatch [--upload]
```

Reruns a results cell's two fastest engines on this machine in one job: the standard benchmark rounds, untraced, then
one short round under the platform's device tracer in the same engine session. Each engine reruns its results row's
matrix cell through the harness: the row's pie commit or engine version, the same boot, recipe and bench client.

The run writes the benchmark records as `pie-bench run` uploads them (`records.jsonl`, `submission.json.gz`) and the
cells for `POST /v1/profiles` (`profiles.json`). Per benchmark unit a profile gives the wall time, the forward time
(the union of the device's work intervals inside the measured windows) and the rest, idle. It names no kernels.

The verdicts printed at the end come from `server/profiles.py`, so they need a checkout of this repo with the
`server` extra. From a pip install the profiler prints "not judged here".

## Modules

| Module | Job |
|---|---|
| `__main__.py` | the command; under a tracer that must launch the run (nsys) it runs itself again inside it |
| `rerun.py` | picks each cell's two fastest engines from `/v1/results`, plans their matrix cells, runs the job, writes the profiles |
| `breakdown.py` | the measured windows from the bench client's JSON (`--report-timing`) and the split into wall, forward and idle |
| `profiled_round.py` | the workload of the profiled round |
| `tracers/` | one tracer per backend; `tracer_for` picks it |

## Units

| Setup | Unit |
|---|---|
| decode, spec | ms per output token |
| prefill | ms per prompt of the cell's prefill length |
| batching | ms per batched decode step of the cell's concurrency |
| pbatch | ms per wave of the cell's concurrency of prompts |

Units count tokens, so two engines that ran different shapes still share one unit. Where the benchmark number is the
median of its requests' own rates (decode, spec, prefill), the profiled step is taken the same way, so one slow request
moves neither. Times are Unix nanoseconds: the windows come from the bench client's own clock, the device intervals
from the tracer, and every window must hold device work.

## The profiled round

The round keeps the benchmark's shape and its requests, at most 8, or 3 waves of its concurrency. A single-stream
step is the median request's, and 4 requests let two lucky ones set it (pie's A40 Qwen3.5-0.8B prefill: 15.1 and
15.2 ms against 17.2 to 17.4 for the rest).

`PIE_BENCH_PROFILE_ROUND=full` keeps a whole benchmark round, for a Mac that throttles within one: on the fanless
m3-16g mlx-lm's 4th pf8-512 wave runs 25 to 55% slower than its first, so a 3-wave round leaves the slow wave out and
profiles 12 to 14% under the benchmark's own step.

A cold-cache cell's profiled round sends prompts of its own: round 0's would hit the engine's prefix cache.

## Matching the site

`rerun.py` finds the one matrix cell a results row measured the way the site picks rows:

- the machine's own tier first, then any tier that holds the cell (NVIDIA's full runs are weekly cells);
- a Mac's model slices are in no suite, so a row no arm plans is looked for in every artifact;
- off a Mac the grid takes the safetensors checkpoint's row over the MLX one;
- the grid's rows are the plain, unspeculated runs;
- slices with the same label are told apart by their parameter count;
- for one label with several cuts the site shows the biggest cut an engine ran last, so the rerun takes that one.

Rivals rerun at the version their rows measured; pie runs at its commit. One job builds one pie commit and runs one
version of each engine, so cells measured at different ones are run apart.

## Tracers

| Backend | Tracer | Choice |
|---|---|---|
| cuda | `cupti` (default), `nsys` | `PIE_BENCH_CUDA_TRACER` |
| rocm | `hsa` | |
| metal | `metal-cb` (default), `xctrace` | `PIE_BENCH_METAL_TRACER` |
| xla | `xla` | |

### cupti

A CUDA injection library (`cupti_trace.c`, built against the CUPTI 13 of the toolkit or of an engine's
`nvidia-cuda-cupti` wheel) that every engine process loads at CUDA init (`CUDA_INJECTION64_PATH`). It traces no API
calls and records nothing until the profiled round, then only the device's kernel, copy and memset activity. nsys also
traces every CUDA API call, and on engines that launch kernels one by one from Python (SGLang's and vLLM's eager
prefill) that cost 10 to 38% of the profiled round (an RTX 4090's SGLang Qwen3.5-0.8B prefill took 29 to 34% longer).

The handshake lives in `PIE_CUPTI_DIR`:

- the profiler writes `on` with the round's number N, whole, through a rename;
- each process writes `<pid>.alive` at CUDA init and `<pid>-<N>.armed` once it records;
- when `on` goes, each process writes `<pid>-<N>.bin` (uint64 start and end pairs in CUPTI ns), `<pid>-<N>.clock` (a
  CUPTI timestamp and the CLOCK_REALTIME ns taken together) and `<pid>-<N>.done`.

The profiler waits up to 120 s for every live process to arm: CUPTI's first enable in a process with many modules
loaded (vLLM's EngineCore) takes seconds, and a round started before it lost its first windows. Completed records leave
every 100 ms, so a process that exits inside the round (SGLang's scheduler at its client's shutdown) loses at most
that, not a part-filled 8 MB buffer. A forced flush hands over records whose work has not finished; they carry no
timestamps and are skipped. The bench clients' `end_trace` ends the round while an in-process engine still runs.

`PIE_CUPTI_MODE` sets what a process records: `graph` traces each CUDA graph launch whole, `hw` takes kernel times
from the GPU's hardware events (Blackwell), `off` records nothing (for an A/B of the tracer's cost).
`PIE_CUPTI_MODES="<word>=<mode>;..."` sets the mode of a process whose command line holds the word.

### nsys

The profiler runs under `nsys launch`; each measured round is one `nsys start` and `nsys stop` collection, exported to
SQLite. Its timestamps count from the session start, which the export gives in Unix ns. A CUDA graph launch is one
interval of its own.

| Setting | Why |
|---|---|
| `--trace-fork-before-exec=true` | engines that fork their model worker without exec (vLLM's EngineCore) are traced too |
| `--cuda-flush-interval=500` | with the default, a server idle after the round lost its last part-filled buffer at stop (SGLang on an A40: the last 620 ms) |
| `--cuda-graph-trace=graph` | node by node tracing slowed graph-replaying decode (TRT-LLM on an H200: +19% node by node, +1.4% whole) |
| `--cuda-event-trace=false` | on by default since driver 12.8, it can add false dependencies across streams |
| `--sample=none --cpuctxsw=none` | only device work is read |
| `VLLM_WORKER_MULTIPROC_METHOD=spawn` | a forked EngineCore kept losing the round's last kernels at stop (1.3 s of a Raw 512 round on an A40) |

The profiler waits three flush intervals before the round, so every traced process collects before its first request
(SGLang's scheduler on an RTX 5090 showed no work in its first window without it), and three after, so the last
buffers are saved.

### hsa

rocprofv3 traced every dispatch from launch through intercept queues and made each dispatch create and wait on a
signal of its own: that cost launch-bound engines 4% to 246% of their step, and SGLang's HIP graph replay crashed under
it on ROCm 7.2.0. Instead every engine process loads `hsa_trace.cpp` (`HSA_TOOLS_LIB`), which leaves the engine's
queues as they are and, outside a round, only checks one flag on each signal store.

While `$PIE_BENCH_HSA_TRACE_DIR/recording` exists, a store to a queue's doorbell gives each kernel packet it publishes
a completion signal from the queue's pool (4096 per queue, made when a round starts). The queues write start and end
timestamps into it, and a thread of the tool's own writes them as Unix ns to `kernels-<pid>-<n>.csv`, then
`kernels-<pid>-<n>.done` once the round's dispatches have all completed, or 5 s after the round, counting the rest in
`.unfinished`. A kernel that carries a completion signal of its own is left as it is and counted in `.skipped`. More
than 1% skipped or unfinished kernels fails the profile. Copies (SDMA, and ROCr's own blit queues) are not traced; a
prefill's are a few microseconds.

ROCr skips `HSA_TOOLS_LIB` in processes where rocprofiler-register took the API table (any torch process) unless v1
tools are allowed, so the tracer sets `HSA_TOOLS_ROCPROFILER_V1_TOOLS=1`. HIP on ROCm 10 makes its queues with
`hsa_amd_queue_create`, which the tool wraps too. The ROCm tree with HSA's headers is `ROCM_PATH`, `/opt/rocm`, or the
one `hipcc` sits in (AMD's vLLM image ships ROCm as pip packages).

### metal-cb

`metal_command_buffers.m`, preloaded into the job's processes (`DYLD_INSERT_LIBRARIES`), wraps `-commit` of the
device's command buffer classes once the process creates its device. While `<dir>/recording` exists, each committed
buffer gets a completed handler that appends its `GPUStartTime` and `GPUEndTime` in Unix ns to `<dir>/<pid>.txt`;
outside that window `-commit` costs one atomic load more. A buffer's interval spans its encoders back to back, and a
forked child records nothing.

There is no kernel tracing, so a host-bound engine runs at its own speed. On an M5 Max (gemma-4-e2b, 512-token
prefill) the profiled walls came within 0.8% of the same session's benchmark for pie and mlx-lm (xctrace: +2% and
+13%), and the forward passes within 0.6% of xctrace's GPU intervals (22.42 against 22.49 ms, 24.65 against 24.50 ms).
`PIE_BENCH_METAL_TRACER=xctrace` records with Instruments instead, for an engine started through a system shell, which
drops `DYLD_INSERT_LIBRARIES`.

### xctrace

Records the GPU instrument alone (`xctrace record --instrument GPU --all-processes`): the same metal-gpu-intervals as
the Metal System Trace template (an M5 Max mlx-lm server's GPU busy time 8.65 s either way), in a trace 30 times
smaller that saves in seconds, not minutes. Its kernel tracing still costs a host-bound engine time: mlx-lm's
512-token prefill 8 to 15%, pie's 0 to 3%. The intervals kept are those of the processes under the profiler, on the
trace's own clock moved to Unix time by its start date. Instruments' temporary recording files, GBs a minute, are
deleted after each save.

### xla

Processes that import jax arm a trace through `jax_site/sitecustomize.py`, first on `PYTHONPATH` (a sitecustomize
further down the path still runs). Once jax loads, a thread of its own watches the trace folder's `command` file
(`<seq> start` or `<seq> stop`) and starts or stops `jax.profiler`, host and device, with no Python tracer (it slows a
Python-bound engine loop). Markers `<pid>.started` and `<pid>.done` (`<seq> ok|skip|error ...`) say when each is
over; a process with no TPU backend of its own (a server's front end) skips both.

pie's XLA server is armed by `xla_trace.c`, preloaded by the `pie_xla.py` launcher: SIGUSR1 starts the PJRT plugin's
profiler (the PLUGIN_Profiler API that pie's own `PIE_XLA_PROFILE` drives), SIGUSR2 stops it and writes the trace as a
serialized XSpace to `<dir>/pie-<pid>/trace.xplane.pb`. pie runs as benchmarked: no run waits for the device.

The bench clients' `xla_trace` starts and stops these traces around the measured requests of an engine that runs
inside its bench client (pie's server, vLLM's engine core); a server already up when the round starts (SGLang-JAX) is
traced from the round's start to its end. The intervals are the ops on the TPU devices' "XLA Ops", "Async XLA Ops"
and "Sparse Core Ops" lines. A device line with no timestamp counts from the device tracer's own start, which the trace
does not state (it is not the session's profile_start_time: 1.3 ms later in a vLLM-TPU trace), so the host launches
and completions of its program runs, matched by run_id, pin it.

## Environment

| Variable | Effect |
|---|---|
| `PIE_BENCH_CUDA_TRACER` | `cupti` (default) or `nsys` |
| `PIE_BENCH_METAL_TRACER` | `cb` (default) or `xctrace` |
| `PIE_BENCH_PROFILE_ROUND=full` | profile a whole benchmark round |
| `PIE_BENCH_PROFILER_KEEP_TRACES` | keep the raw trace files |
| `PIE_CUPTI_DIR`, `PIE_CUPTI_MODE`, `PIE_CUPTI_MODES` | the CUPTI tracer's folder and modes |
