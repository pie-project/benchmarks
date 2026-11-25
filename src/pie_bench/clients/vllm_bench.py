#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from typing import Any

from bench_args import add_mode_subcommands, add_output_dump_args
from bench_devices import gpu_clock_state, maybe_set_cpu_affinity, visible_cuda_devices
from bench_pacing import ArrivalPacer, arrival_schedule, run_timed_warmup_sync
from bench_prompts import (
    hf_chat_token_ids_and_counts,
    make_prompts,
    request_max_tokens,
    request_max_tokens_varies,
)
from bench_replicas import run_replicas
from bench_results import RequestResult, finish, hash_output_tokens, print_first_output, summarize
from bench_streaming import StreamTimer
from bench_tracing import (
    cuda_profiler_start,
    cuda_profiler_stop,
    end_trace,
    monotonic_ns,
    start_measured_profiler,
    stop_measured_profiler,
    xla_trace,
)

REPLICA_FLAGS = {"--dp-size", "--json-out", "--requests", "--num-requests"}


def _vllm_metric_value(llm: Any, name: str) -> int:
    try:
        metrics = llm.get_metrics()
    except Exception:
        return 0
    total = 0
    for metric in metrics:
        if getattr(metric, "name", None) != name:
            continue
        value = getattr(metric, "value", None)
        if value is not None:
            total += int(value)
    return total


def _vllm_metric_vector(llm: Any, name: str) -> list[int]:
    try:
        metrics = llm.get_metrics()
    except Exception:
        return []
    values: list[int] = []
    for metric in metrics:
        if getattr(metric, "name", None) != name:
            continue
        metric_values = getattr(metric, "values", None)
        if metric_values is None:
            continue
        if not values:
            values = [0] * len(metric_values)
        for i, value in enumerate(metric_values):
            values[i] += int(value)
    return values


def _vllm_spec_metrics(llm: Any) -> dict[str, Any]:
    return {
        "drafts": _vllm_metric_value(llm, "vllm:spec_decode_num_drafts"),
        "draft_tokens": _vllm_metric_value(llm, "vllm:spec_decode_num_draft_tokens"),
        "accepted_tokens": _vllm_metric_value(llm, "vllm:spec_decode_num_accepted_tokens"),
        "accepted_per_position": _vllm_metric_vector(
            llm, "vllm:spec_decode_num_accepted_tokens_per_pos"
        ),
    }


def _vllm_spec_delta(after: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    pos_after = after.get("accepted_per_position") or []
    pos_before = before.get("accepted_per_position") or []
    pos_len = max(len(pos_after), len(pos_before))
    accepted_per_position = [
        (pos_after[i] if i < len(pos_after) else 0) - (pos_before[i] if i < len(pos_before) else 0)
        for i in range(pos_len)
    ]
    drafts = int(after.get("drafts", 0)) - int(before.get("drafts", 0))
    draft_tokens = int(after.get("draft_tokens", 0)) - int(before.get("draft_tokens", 0))
    accepted_tokens = int(after.get("accepted_tokens", 0)) - int(before.get("accepted_tokens", 0))
    out: dict[str, Any] = {
        "vllm spec drafts": drafts,
        "vllm spec draft tokens": draft_tokens,
        "vllm spec accepted tokens": accepted_tokens,
    }
    if accepted_per_position:
        out["vllm spec accepted per position"] = accepted_per_position
    if draft_tokens > 0:
        out["vllm spec acceptance rate"] = accepted_tokens / draft_tokens
    if drafts > 0:
        out["vllm spec mean acceptance length"] = 1.0 + (accepted_tokens / drafts)
    return out


def max_num_seqs_for(args: argparse.Namespace) -> int:
    if args.mode == "latency":
        seqs = 1
    elif args.concurrency == 0:
        seqs = max(1, args.num_requests)
    else:
        seqs = args.concurrency
    if args.max_num_seqs:
        seqs = min(seqs, args.max_num_seqs)
    return seqs


def engine_kwargs(args: argparse.Namespace, *, offline: bool) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if args.attention_backend:
        kwargs["attention_config"] = {"backend": args.attention_backend}
    if args.moe_backend:
        kwargs["kernel_config"] = {"moe_backend": args.moe_backend}
    if args.enforce_eager:
        kwargs["enforce_eager"] = True
    if args.compilation_config:
        kwargs["compilation_config"] = json.loads(args.compilation_config)
    if args.language_model_only:
        kwargs["language_model_only"] = True
    if offline and os.environ.get("VLLM_DISABLE_CUSTOM_AR"):
        kwargs["disable_custom_all_reduce"] = True
    if args.num_gpu_blocks_override:
        kwargs["num_gpu_blocks_override"] = args.num_gpu_blocks_override
    if args.block_size:
        kwargs["block_size"] = args.block_size
    if offline and args.kv_cache_dtype != "auto":
        kwargs["kv_cache_dtype"] = args.kv_cache_dtype
    if offline and args.no_chunked_prefill:
        kwargs["enable_chunked_prefill"] = False
    return kwargs


def _claim(config: dict[str, Any], key: str, value: Any, flag: str) -> None:
    if key in config:
        raise ValueError(f"{flag} conflicts with speculative_config.{key}")
    config[key] = value


def speculative_config_for(args: argparse.Namespace) -> dict[str, Any] | None:
    config = json.loads(args.speculative_config) if args.speculative_config is not None else None
    if args.spec_method is not None or args.spec_tokens is not None:
        config = dict(config or {})
        if args.spec_method is not None:
            _claim(config, "method", args.spec_method, "--spec-method")
        if args.spec_tokens is not None:
            _claim(config, "num_speculative_tokens", args.spec_tokens, "--spec-tokens")
    if args.mtp_assistant_model is not None:
        config = dict(config or {})
        _claim(config, "model", args.mtp_assistant_model, "--mtp-assistant-model")
        _claim(config, "method", args.mtp_method, "--mtp-method")
        _claim(config, "num_speculative_tokens", args.mtp_num_drafts, "--mtp-num-drafts")
        if args.mtp_draft_tp_size is not None:
            _claim(
                config, "draft_tensor_parallel_size", args.mtp_draft_tp_size, "--mtp-draft-tp-size"
            )
    return config


class Sampling:
    def __init__(self, args: argparse.Namespace) -> None:
        from vllm import SamplingParams

        self.args = args
        self.make = SamplingParams
        self.base = self.with_max_tokens(args.max_tokens)

    def with_max_tokens(self, max_tokens: int):
        args = self.args
        return self.make(
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=max_tokens,
            ignore_eos=args.ignore_eos,
        )

    def for_request(self, i: int):
        max_tokens = request_max_tokens(self.args, i)
        return self.base if max_tokens == self.args.max_tokens else self.with_max_tokens(max_tokens)


def chat_token_prompts(
    args: argparse.Namespace, n: int
) -> tuple[list[dict[str, list[int]]], list[int]]:
    token_ids, prompt_counts = hf_chat_token_ids_and_counts(
        args.model, args.system, make_prompts(args, n + args.warmup), args.think
    )
    return [{"prompt_token_ids": ids} for ids in token_ids], prompt_counts


def _warm_up_offline(
    llm, args: argparse.Namespace, prompts: list, sampling: Sampling, max_num_seqs: int
) -> None:
    warmup_sampling = sampling.base
    if args.warmup_max_tokens is not None:
        warmup_sampling = sampling.with_max_tokens(args.warmup_max_tokens)

    def warmup_pass() -> None:
        llm.generate(prompts[: args.warmup], warmup_sampling)

    warmup_pass()
    if args.mode == "tput" and max_num_seqs > 1:
        llm.generate(
            [prompts[k % args.warmup] for k in range(max_num_seqs)], sampling.with_max_tokens(8)
        )
    run_timed_warmup_sync(warmup_pass, args.warmup_seconds, label="vllm")


def _offline_result(
    args: argparse.Namespace, out: Any, req_wall: float, prompt_count: int
) -> RequestResult:
    token_ids = [int(t) for t in out.outputs[0].token_ids]
    result = RequestResult(True, float(req_wall), len(token_ids), prompt_count)
    result.output_token_sha256 = hash_output_tokens(token_ids)
    if args.dump_all_token_ids:
        result.output_token_ids = token_ids
    if args.dump_all_texts:
        result.output_text = out.outputs[0].text
    return result


def _generate_measured(
    llm, args, prompts: list, counts: list[int], sampling: Sampling, results: list, texts: list
) -> None:
    def record(out: Any, req_wall: float, prompt_count: int) -> None:
        results.append(_offline_result(args, out, req_wall, prompt_count))
        texts.append(out.outputs[0].text)

    if args.mode == "latency":
        for i, (p, prompt_count) in enumerate(zip(prompts, counts), start=args.warmup):
            req_start = time.perf_counter()
            outputs = llm.generate([p], sampling.for_request(i))
            req_wall = time.perf_counter() - req_start
            for out in outputs:
                record(out, req_wall, prompt_count)
        return
    measured_sampling = (
        [sampling.for_request(args.warmup + i) for i in range(len(prompts))]
        if request_max_tokens_varies(args)
        else sampling.base
    )
    for out, prompt_count in zip(llm.generate(prompts, measured_sampling), counts):
        record(out, 0.0, prompt_count)


def run(args: argparse.Namespace):
    from vllm import LLM

    cpu_affinity = maybe_set_cpu_affinity(args, visible_cuda_devices(args.tp_size))
    n = args.requests if args.mode == "latency" else args.num_requests
    prompts, prompt_counts = chat_token_prompts(args, n)
    max_num_seqs = max_num_seqs_for(args)
    llm_kwargs = engine_kwargs(args, offline=True)
    speculative_config = speculative_config_for(args)
    if speculative_config is not None:
        llm_kwargs["speculative_config"] = dict(speculative_config)
    shared = {
        "model": args.model,
        "gpu_memory_utilization": args.gpu_mem_util,
        "max_num_seqs": max_num_seqs,
        "max_num_batched_tokens": args.max_num_batched_tokens,
        "tensor_parallel_size": args.tp_size,
        "max_model_len": args.max_model_len,
        "enable_prefix_caching": args.prefix_caching,
        "disable_log_stats": False,
    }
    if args.print_llm_kwargs:
        print(json.dumps({**shared, **llm_kwargs}, indent=2))
    llm = LLM(trust_remote_code=True, **shared, **llm_kwargs)
    sampling = Sampling(args)
    if args.warmup:
        _warm_up_offline(llm, args, prompts, sampling, max_num_seqs)

    spec_metrics_before = _vllm_spec_metrics(llm)
    clocks_at_start = gpu_clock_state()
    results: list[RequestResult] = []
    texts: list[str] = []
    cuda_profiler_start(args.cuda_profiler_capture)
    start = time.perf_counter()
    try:
        _generate_measured(
            llm,
            args,
            prompts[args.warmup :],
            prompt_counts[args.warmup :],
            sampling,
            results,
            texts,
        )
    finally:
        wall = time.perf_counter() - start
        cuda_profiler_stop(args.cuda_profiler_capture)
        clocks_at_end = gpu_clock_state()
    spec_metrics_after = _vllm_spec_metrics(llm)
    print_first_output(args, texts[0] if texts else None)

    summary = summarize(
        mode=args.mode,
        engine="vllm",
        model=args.model,
        results=results,
        wall_s=wall,
        config={
            "enable_prefix_caching": args.prefix_caching,
            "max_num_seqs": max_num_seqs,
            "max_num_batched_tokens": args.max_num_batched_tokens,
            "attention_backend": args.attention_backend,
            "enforce_eager": args.enforce_eager,
            "speculative_config": dict(speculative_config) if speculative_config else None,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "ignore_eos": args.ignore_eos,
            "unique_prompts": args.unique_prompts,
            "cuda profiler capture": args.cuda_profiler_capture,
            "cpu affinity": cpu_affinity,
            "warmup seconds": args.warmup_seconds,
            "gpu clocks at start": clocks_at_start,
            "gpu clocks at end": clocks_at_end,
            "warmup max tokens": args.warmup_max_tokens,
            **_vllm_spec_delta(spec_metrics_after, spec_metrics_before),
        },
    )
    return summary, results


async def stream_request(
    engine,
    request_id: str,
    prompt,
    prompt_count: int,
    params,
    epoch_ns: int | None,
    want_text: bool,
) -> RequestResult:
    timer = StreamTimer(epoch_ns)
    text: str | None = None
    try:
        async for out in engine.generate(prompt, params, request_id):
            stamp = timer.stamp()
            if want_text:
                text = out.outputs[0].text
            timer.saw(len(out.outputs[0].token_ids), stamp)
        return timer.result(prompt_count, process_id=request_id, output_text=text)
    except Exception as e:
        return timer.failure(prompt_count, e)


def _streaming_batched_tokens(args: argparse.Namespace, engine_args_cls) -> int | None:
    if args.max_num_batched_tokens is not None or not hasattr(
        engine_args_cls, "get_batch_defaults"
    ):
        return args.max_num_batched_tokens
    from vllm.usage.usage_lib import UsageContext

    serve = engine_args_cls.get_batch_defaults(args.tp_size)[0].get(UsageContext.OPENAI_API_SERVER)
    return max(serve or 0, 2048)


async def _warm_up_streaming(
    engine,
    args,
    prompts: list,
    counts: list[int],
    sampling: Sampling,
    max_num_seqs: int,
    want_text: bool,
) -> None:
    for j, p in enumerate(prompts[: args.warmup]):
        await stream_request(engine, f"warmup-{j}", p, counts[j], sampling.base, None, want_text)
    if max_num_seqs > 1:
        short = sampling.with_max_tokens(8)
        await asyncio.gather(
            *(
                stream_request(
                    engine,
                    f"warmup-batch-{k}",
                    prompts[k % args.warmup],
                    counts[k % args.warmup],
                    short,
                    None,
                    want_text,
                )
                for k in range(max_num_seqs)
            )
        )


async def _drive_streaming(
    engine,
    args,
    prompts: list,
    counts: list[int],
    sampling: Sampling,
    max_num_seqs: int,
    pacer: ArrivalPacer,
):
    n = args.num_requests
    want_text = args.dump_all_texts or args.dump_first_text
    if args.warmup:
        await _warm_up_streaming(engine, args, prompts, counts, sampling, max_num_seqs, want_text)
    await asyncio.to_thread(xla_trace, "start")
    epoch_unix_s = time.time()
    epoch_ns = monotonic_ns()
    profiler_window = start_measured_profiler(args)
    start = time.perf_counter()
    pacer.start()

    async def offer(i: int, paced: bool = True) -> RequestResult:
        if paced:
            await pacer.wait(i)
        k = args.warmup + i
        return await stream_request(
            engine, f"req-{i}", prompts[k], counts[k], sampling.for_request(k), epoch_ns, want_text
        )

    try:
        if args.concurrency == 1 and not args.arrival_rate:
            results = [await offer(i, paced=False) for i in range(n)]
        else:
            results = list(await asyncio.gather(*(offer(i) for i in range(n))))
    finally:
        await stop_measured_profiler(args, profiler_window)
    wall = time.perf_counter() - start
    await asyncio.to_thread(xla_trace, "stop")
    return results, wall, epoch_unix_s, epoch_ns


def run_streaming(args: argparse.Namespace):
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.v1.engine.async_llm import AsyncLLM

    cpu_affinity = maybe_set_cpu_affinity(args, visible_cuda_devices(args.tp_size))
    prompts, prompt_counts = chat_token_prompts(args, args.num_requests)
    max_num_seqs = max_num_seqs_for(args)
    max_num_batched_tokens = _streaming_batched_tokens(args, AsyncEngineArgs)
    engine = AsyncLLM.from_engine_args(
        AsyncEngineArgs(
            model=args.model,
            trust_remote_code=True,
            gpu_memory_utilization=args.gpu_mem_util,
            max_num_seqs=max_num_seqs,
            max_num_batched_tokens=max_num_batched_tokens,
            tensor_parallel_size=args.tp_size,
            max_model_len=args.max_model_len,
            enable_prefix_caching=args.prefix_caching,
            disable_log_stats=False,
            **engine_kwargs(args, offline=False),
        )
    )
    sampling = Sampling(args)
    pacer = ArrivalPacer(
        arrival_schedule(
            args.num_requests, args.arrival_rate, args.arrival_process, args.arrival_seed
        )
    )
    try:
        results, wall, epoch_unix_s, epoch_ns = asyncio.run(
            _drive_streaming(engine, args, prompts, prompt_counts, sampling, max_num_seqs, pacer)
        )
    finally:
        end_trace()
        engine.shutdown()

    summary = summarize(
        mode=args.mode,
        engine="vllm",
        model=args.model,
        results=results,
        wall_s=wall,
        config={
            "streaming_client": True,
            "client timing epoch unix s": epoch_unix_s,
            "client timing epoch monotonic ns": epoch_ns,
            "enable_prefix_caching": args.prefix_caching,
            "max_num_seqs": max_num_seqs,
            "max_num_batched_tokens": max_num_batched_tokens,
            "enforce_eager": args.enforce_eager,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "ignore_eos": args.ignore_eos,
            "unique_prompts": args.unique_prompts,
            "cpu affinity": cpu_affinity,
            "arrival_rate": args.arrival_rate,
            "arrival_process": args.arrival_process,
            **pacer.stats(),
        },
    )
    return summary, results


def _add_engine_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--attention-backend", default=None)
    sp.add_argument(
        "--moe-backend",
        default=None,
        help="Override vLLM's MoE kernel choice (kernel_config.moe_backend): "
        "auto, triton, flashinfer_trtllm, flashinfer_cutlass, marlin, "
        "... Default None leaves vLLM's own 'auto' selection alone, "
        "which is what a deployment gets and therefore what the "
        "headline baseline should report.",
    )
    sp.add_argument("--enforce-eager", action="store_true")
    sp.add_argument(
        "--compilation-config",
        default=None,
        help="JSON object passed through to vLLM's compilation_config, e.g. "
        '\'{"cudagraph_mode": "PIECEWISE"}\' where vLLM drops to eager because '
        "its attention backend has no full-graph support.",
    )
    sp.add_argument(
        "--language-model-only",
        action="store_true",
        help="Build the text tower alone: a miniature carved without its "
        "vision tower loads, and a multimodal row skips its encoder "
        "budget.",
    )
    sp.add_argument(
        "--no-chunked-prefill",
        action="store_true",
        help="disable vLLM's chunked prefill. Prefill then does not share "
        "a step with decode, which is the mechanism a fanned "
        "--output-spread is thought to tax.",
    )


def _add_kv_cache_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--num-gpu-blocks-override",
        type=int,
        default=0,
        help="Exact KV block count, the counterpart of pie's `[model] "
        "device_kv_budget` in blocks, so both engines can be sized "
        "by the same budget instead of by a calibrated memory "
        "fraction.",
    )
    sp.add_argument(
        "--block-size",
        type=int,
        default=0,
        help="KV block size in tokens. 0 leaves vLLM's default; set 16 to "
        "match pie's page size when using --num-gpu-blocks-override.",
    )
    sp.add_argument(
        "--prefix-caching",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    sp.add_argument("--max-num-batched-tokens", type=int, default=None)
    sp.add_argument(
        "--max-num-seqs",
        type=int,
        default=0,
        help="Cap on vLLM's max_num_seqs (0: the concurrency). For a hybrid "
        "model whose per-sequence state pool cannot hold every offered "
        "request at once; the rest queue in vLLM's scheduler.",
    )
    sp.add_argument(
        "--kv-cache-dtype",
        default="auto",
        help="vLLM KV cache dtype. DeepSeek-V4 needs 'fp8' because its "
        "fp8_ds_mla cache layout refuses anything else.",
    )


def _add_speculation_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--speculative-config",
        default=None,
        help="JSON object passed through to vLLM's speculative_config.",
    )
    sp.add_argument("--spec-method", default=None)
    sp.add_argument("--spec-tokens", type=int, default=None)
    sp.add_argument(
        "--mtp-assistant-model",
        default=None,
        help="Assistant checkpoint/model for vLLM Gemma4 MTP speculative decoding.",
    )
    sp.add_argument(
        "--mtp-method",
        default="gemma4_mtp",
        help="vLLM speculative method for the assistant. Default: gemma4_mtp.",
    )
    sp.add_argument(
        "--mtp-num-drafts",
        type=int,
        default=3,
        help="Number of vLLM speculative tokens. Match Pie --mtp-num-drafts.",
    )
    sp.add_argument(
        "--mtp-draft-tp-size",
        type=int,
        default=None,
        help="Optional draft_tensor_parallel_size for vLLM speculative_config.",
    )


def _add_reporting_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--print-llm-kwargs",
        action="store_true",
        help="Print the vLLM LLM kwargs used by the benchmark before loading.",
    )
    sp.add_argument(
        "--report-timing",
        action="store_true",
        help="Collect per-request TTFT and inter-token gap distributions. "
        "Switches tput mode to the AsyncLLM streaming engine with a "
        "closed-loop client (mirrors pie's client vantage: stamps on "
        "token delivery, all requests submitted at t=0 when "
        "num_requests == concurrency).",
    )
    sp.add_argument(
        "--report-arrivals",
        action="store_true",
        help="Collect absolute per-token client arrivals without enabling "
        "additional latency reporting.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="vLLM canonical latency/throughput benchmark")
    for sp in add_mode_subcommands(parser):
        add_output_dump_args(sp)
        _add_engine_args(sp)
        _add_kv_cache_args(sp)
        _add_speculation_args(sp)
        _add_reporting_args(sp)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.dp_size > 1:
        summary, results = run_replicas(args, "vllm", os.path.abspath(__file__), REPLICA_FLAGS)
    elif (args.report_timing or args.report_arrivals) and args.mode == "tput":
        summary, results = run_streaming(args)
    else:
        summary, results = run(args)
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
