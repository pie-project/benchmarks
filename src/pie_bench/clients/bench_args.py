from __future__ import annotations

import argparse

from bench_prompts import BENCH_PROMPT, BENCH_SYSTEM


def add_mode_subcommands(parser: argparse.ArgumentParser) -> list[argparse.ArgumentParser]:
    sub = parser.add_subparsers(dest="mode", required=True)
    latency = sub.add_parser("latency", help="single-request latency")
    add_common_args(latency)
    latency.add_argument("--requests", type=int, default=16)
    latency.set_defaults(num_requests=0, concurrency=1)

    tput = sub.add_parser("tput", help="many-request throughput")
    add_common_args(tput)
    tput.add_argument("--num-requests", type=int, default=512)
    tput.add_argument(
        "--concurrency",
        type=int,
        default=0,
        help="Throughput concurrency cap. 0 means unlimited.",
    )
    tput.set_defaults(requests=0)
    return [latency, tput]


def add_common_args(p: argparse.ArgumentParser) -> None:
    _add_request_args(p)
    _add_workload_shape_args(p)
    _add_arrival_args(p)
    _add_warmup_args(p)
    _add_capture_args(p)
    _add_deployment_args(p)
    _add_sglang_args(p)
    _add_pie_guest_args(p)


def _add_request_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", default="Qwen/Qwen3-0.6B")
    p.add_argument("--prompt", default=BENCH_PROMPT)
    p.add_argument("--system", default=BENCH_SYSTEM)
    p.add_argument(
        "--think",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Pass enable_thinking to the chat template (Qwen3 family): --think / --no-think; "
        "absent, the template's own default applies.",
    )
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--ignore-eos", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--unique-prompts", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument(
        "--prompts-file",
        default=None,
        help="JSON list of exact prompt strings, one per request (warmup first). "
        "Replaces --prompt and every shared-prefix rule, so the caller "
        "controls each prompt byte for byte (cold-cache runs).",
    )


def _add_workload_shape_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--shared-prefix-words",
        type=int,
        default=0,
        help="Prefix-heavy shape: prepend a deterministic shared block of "
        "roughly this many tokens to every prompt (unique tails kept). "
        "Pair with prefix caching on engines that support it.",
    )
    p.add_argument(
        "--output-spread",
        type=float,
        default=0.0,
        help="Fan per-request output budgets out over "
        "[max_tokens*(1-F), max_tokens*(1+F)] on a deterministic "
        "sawtooth with mean exactly max_tokens. Breaks the lockstep a "
        "uniform shape imposes on a closed-loop client without changing "
        "the total work.",
    )
    p.add_argument(
        "--mixed-phase",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Mixed-phase shape: even-indexed requests are prefill-heavy "
        "(long prompt, --mixed-short-output tokens out), odd-indexed "
        "are decode-heavy (short prompt, --max-tokens out). Run with "
        "prefix caching OFF on both engines.",
    )
    p.add_argument(
        "--mixed-long-prompt-words",
        type=int,
        default=400,
        help="Word count of the long prompt body in --mixed-phase.",
    )
    p.add_argument(
        "--mixed-short-output",
        type=int,
        default=16,
        help="max_tokens for the prefill-heavy half in --mixed-phase.",
    )


def _add_arrival_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--arrival-rate",
        type=float,
        default=0.0,
        help="Open-loop offered load in requests/second. 0 (the default) "
        "offers every request at t=0, which measures saturation only. "
        "A finite rate makes the load exogenous so queueing delay shows "
        "up in TTFT instead of being absorbed by the arrival process.",
    )
    p.add_argument(
        "--arrival-process",
        choices=["poisson", "uniform"],
        default="poisson",
        help="Inter-arrival distribution for --arrival-rate.",
    )
    p.add_argument(
        "--arrival-seed",
        type=int,
        default=20260730,
        help="Seeds the arrival schedule. Engines compared against each "
        "other must share this so they see the identical pattern.",
    )


def _add_warmup_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument(
        "--warmup-seconds",
        type=float,
        default=0.0,
        help="Keep repeating the warmup set until this much wall time has "
        "elapsed, on top of --warmup. Off by default: on this hardware "
        "the run-to-run spread came from CPU pinning, not from a short "
        "warmup, and a longer warmup did not reduce it.",
    )
    p.add_argument(
        "--warmup-max-tokens",
        type=int,
        default=None,
        help="Override max_tokens only for warmup requests.",
    )


def _add_capture_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json-out", default=None)
    p.add_argument(
        "--cuda-profiler-capture",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Call cudaProfilerStart/Stop around the measured section. Use with "
        "`nsys profile --capture-range=cudaProfilerApi` to exclude setup "
        "and warmup from the trace.",
    )
    p.add_argument(
        "--cuda-profiler-delay-s",
        type=float,
        default=0.0,
        help="Delay cudaProfilerStart after measured work begins.",
    )
    p.add_argument(
        "--cuda-profiler-duration-s",
        type=float,
        default=0.0,
        help="Stop a delayed profiler capture after this duration. Zero keeps "
        "the legacy whole-measured-window capture.",
    )


def _add_deployment_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--request-timeout",
        type=float,
        default=300.0,
        help="Seconds a request may wait; pie_bench counts them from the last event any request of the run heard.",
    )
    p.add_argument("--tp-size", type=int, default=1)
    p.add_argument(
        "--dp-size",
        type=int,
        default=1,
        help="Data-parallel replicas. Each replica is its own tp-size-wide "
        "shard group, so the run occupies tp_size * dp_size devices. "
        "PIE derives this from the device list (world_size / tp_size); "
        "vLLM takes it as data_parallel_size.",
    )
    p.add_argument(
        "--cpu-affinity",
        default="auto",
        help="CPU affinity for the benchmark process. Use 'auto' to pin to "
        "the GPU-local CPUs from `nvidia-smi topo -m`, 'none' to disable, "
        "or an explicit list like '80-87,208-215'.",
    )
    p.add_argument("--gpu-mem-util", type=float, default=0.90)
    p.add_argument(
        "--engine-option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra [model.engine.options] entries, handed straight to the "
        "engine's own options struct (deny_unknown_fields still rules). "
        "Values parse as TOML scalars: true/false, ints, floats, else "
        "strings. Repeatable. pie cuda only; other engines "
        "ignore it.",
    )
    p.add_argument("--max-model-len", type=int, default=2048)


def _add_sglang_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--sglang-attention-backend", default=None)
    p.add_argument("--sglang-sampling-backend", default=None)
    p.add_argument(
        "--sglang-moe-runner-backend",
        default=None,
        help="SGLang's MoE runner. Its auto pick for DeepSeek-V4.1's MXFP4 experts "
        "(flashinfer_mxfp4) wants 128-multiple widths a tp4 share is not.",
    )
    p.add_argument(
        "--sglang-flashinfer-mxfp4-moe-precision",
        default=None,
        help="SGLang's flashinfer_mxfp4 MoE activations. Its default on SM100 quantizes them "
        "to MXFP8; bf16 keeps gpt-oss at pie's and vLLM's W4A16.",
    )
    p.add_argument(
        "--sglang-kv-cache-dtype",
        default=None,
        help="SGLang's KV cache dtype. Its auto pick for DSA models on SM100 and newer "
        "(SM120 too) is fp8_e4m3; bfloat16 keeps the cache at pie's and vLLM's precision.",
    )
    p.add_argument(
        "--sglang-dsa-backend",
        default=None,
        help="SGLang's DSA prefill and decode kernels. Its auto pick on an "
        "SM120 card at a bf16 KV cache is trtllm-gen, which runs on SM100 only.",
    )
    p.add_argument(
        "--sglang-max-total-tokens",
        type=int,
        default=None,
        help="Pin SGLang's KV pool to this many tokens. The cross-engine "
        "analogue of pie's `--device-kv-budget` and vLLM's "
        "`--num-gpu-blocks-override P --block-size B`: without it the "
        "pool is sized from --gpu-mem-util and the three engines are "
        "not given the same KV budget.",
    )
    p.add_argument(
        "--sglang-page-size",
        type=int,
        default=None,
        help="SGLang KV page size in tokens. Defaults to SGLang's own "
        "default (1). Set to 16 to match vLLM's --block-size and pie's "
        "page granularity so internal fragmentation is comparable too.",
    )
    p.add_argument(
        "--sglang-cuda-graph-max-bs",
        type=int,
        default=None,
        help="Largest decode batch SGLang captures a CUDA graph for. "
        "SGLang's default is a hardware-tier heuristic keyed on total "
        "GPU memory (32 on an L40S at tp<4), so a decode batch of 128 "
        "runs eager and a small model loses most of its throughput to "
        "launch overhead. vLLM captures up to max_num_seqs, so leaving "
        "this at SGLang's default measures the heuristic, not the "
        "engine. Set it to the concurrency.",
    )
    p.add_argument(
        "--sglang-disable-cuda-graph", action=argparse.BooleanOptionalAction, default=False
    )
    p.add_argument(
        "--sglang-disable-piecewise-cuda-graph",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    p.add_argument(
        "--sglang-disable-hybrid-swa-memory",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Size one uniform KV pool instead of SGLang's split "
        "sliding-window/full-attention pools. On a sliding-window model "
        "(Gemma) the hybrid sizer derives a token budget from the cheap "
        "SWA layers and then refuses to start because the full-attention "
        "layers cannot hold that many tokens — SGLang aborts where vLLM "
        "just sizes the pool from free memory and schedules within it. "
        "Set this to get a run at all, and to put both engines on the "
        "same pool policy.",
    )


def _add_pie_guest_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--wasm-delay-us",
        type=int,
        default=0,
        help="Busy-spin in the bench inferlet's WASM between every "
        "execute() call (microseconds). Simulates per-token "
        "WASM work — useful for measuring the wall-clock benefit "
        "of async chain firing on W>0 workloads. Default 0.",
    )
    p.add_argument(
        "--run-ahead-frames",
        type=int,
        default=None,
        help="Decode frames each pie lane keeps queued in the engine. "
        "The wave quorum waits for every lane, so deeper queues hide "
        "guest turnaround. pie only; unset means the engine sizes the "
        "window itself via model.channel-capacity().",
    )


def add_output_dump_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dump-first-text", action="store_true")
    p.add_argument("--dump-all-token-ids", action="store_true")
    p.add_argument("--dump-all-texts", action="store_true")
