#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import time

from common import (
    ArrivalPacer,
    RequestResult,
    add_mode_subcommands,
    add_output_dump_args,
    arrival_schedule,
    finish,
    hf_chat_token_ids_and_counts,
    make_prompts,
    maybe_set_cpu_affinity,
    print_first_output,
    request_max_tokens,
    request_max_tokens_varies,
    summarize,
    visible_cuda_devices,
)


def server_arg_names(server_args_cls) -> set[str]:
    fields = getattr(server_args_cls, "__dataclass_fields__", None)
    if fields:
        return set(fields)
    fields = getattr(server_args_cls, "model_fields", None)
    if fields:
        return set(fields)
    import inspect

    return set(inspect.signature(server_args_cls).parameters)


def build_engine(args: argparse.Namespace, max_running_requests: int):
    import sglang as sgl
    from sglang.srt.server_args import ServerArgs

    supported = server_arg_names(ServerArgs)
    engine_kwargs = {
        "model_path": args.model,
        "trust_remote_code": True,
        "mem_fraction_static": args.gpu_mem_util,
        "disable_cuda_graph": args.sglang_disable_cuda_graph,
        "disable_radix_cache": True,
        "max_running_requests": max_running_requests,
        "tp_size": args.tp_size,
        "context_length": args.max_model_len,
    }
    if "disable_piecewise_cuda_graph" in supported:
        engine_kwargs["disable_piecewise_cuda_graph"] = (
            args.sglang_disable_piecewise_cuda_graph
        )
    elif args.sglang_disable_piecewise_cuda_graph and "cuda_graph_backend_prefill" in supported:
        engine_kwargs["cuda_graph_backend_prefill"] = "disabled"
    elif args.sglang_disable_piecewise_cuda_graph:
        raise SystemExit(
            "--sglang-disable-piecewise-cuda-graph: installed SGLang has no "
            "such server arg"
        )
    if "disable_hybrid_swa_memory" in supported:
        engine_kwargs["disable_hybrid_swa_memory"] = (
            args.sglang_disable_hybrid_swa_memory
        )
    elif args.sglang_disable_hybrid_swa_memory:
        raise SystemExit(
            "--sglang-disable-hybrid-swa-memory: installed SGLang has no "
            "such server arg"
        )
    if args.sglang_attention_backend:
        engine_kwargs["attention_backend"] = args.sglang_attention_backend
    if args.sglang_sampling_backend:
        engine_kwargs["sampling_backend"] = args.sglang_sampling_backend
    if args.sglang_moe_runner_backend:
        engine_kwargs["moe_runner_backend"] = args.sglang_moe_runner_backend
    if args.sglang_flashinfer_mxfp4_moe_precision:
        engine_kwargs["flashinfer_mxfp4_moe_precision"] = args.sglang_flashinfer_mxfp4_moe_precision
    if args.sglang_kv_cache_dtype:
        engine_kwargs["kv_cache_dtype"] = args.sglang_kv_cache_dtype
    if args.sglang_dsa_backend:
        engine_kwargs["dsa_prefill_backend"] = args.sglang_dsa_backend
        engine_kwargs["dsa_decode_backend"] = args.sglang_dsa_backend
    if args.sglang_max_total_tokens is not None:
        engine_kwargs["max_total_tokens"] = args.sglang_max_total_tokens
    if args.sglang_page_size is not None:
        engine_kwargs["page_size"] = args.sglang_page_size
    if args.sglang_cuda_graph_max_bs is not None:
        key = (
            "cuda_graph_max_bs_decode"
            if "cuda_graph_max_bs_decode" in supported
            else "cuda_graph_max_bs"
        )
        engine_kwargs[key] = args.sglang_cuda_graph_max_bs
    missing = [k for k in engine_kwargs if k not in supported]
    if missing:
        raise SystemExit(f"installed SGLang lacks server args: {missing}")
    engine = sgl.Engine(**engine_kwargs)
    if args.sglang_max_total_tokens is not None:
        got = engine.get_server_info().get("max_total_num_tokens")
        if got != args.sglang_max_total_tokens:
            engine.shutdown()
            raise SystemExit(
                f"SGLang KV pool is {got} tokens, not the requested "
                f"{args.sglang_max_total_tokens}: raise --gpu-mem-util "
                f"(currently {args.gpu_mem_util}) until the memory-derived "
                f"pool exceeds the request."
            )
    return engine


def run(args: argparse.Namespace):
    cpu_affinity = maybe_set_cpu_affinity(args, visible_cuda_devices(args.tp_size))
    n = args.requests if args.mode == "latency" else args.num_requests
    prompts, prompt_counts = hf_chat_token_ids_and_counts(
        args.model, args.system, make_prompts(args, n + args.warmup), getattr(args, "think", None)
    )
    if args.mode == "latency":
        max_running_requests = 1
    elif args.concurrency == 0:
        max_running_requests = max(1, args.num_requests)
    else:
        max_running_requests = args.concurrency

    base_sampling = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_tokens,
        "ignore_eos": args.ignore_eos,
    }

    all_sampling = [
        base_sampling
        if request_max_tokens(args, i) == args.max_tokens
        else {**base_sampling, "max_new_tokens": request_max_tokens(args, i)}
        for i in range(len(prompts))
    ]

    engine = build_engine(args, max_running_requests)
    want_timing = getattr(args, "report_timing", False)
    want_text = getattr(args, "dump_all_texts", False) or getattr(
        args, "dump_first_text", False
    )

    async def stream_one(
        prompt,
        prompt_count: int,
        params: dict,
        measured_epoch_monotonic_ns: int | None = None,
    ) -> RequestResult:
        start = time.perf_counter()
        send_monotonic_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        client_send_s = (
            (send_monotonic_ns - measured_epoch_monotonic_ns) / 1_000_000_000.0
            if measured_epoch_monotonic_ns is not None
            else None
        )
        if not want_timing:
            try:
                out = await engine.async_generate(
                    input_ids=prompt, sampling_params=params, stream=False
                )
                meta = out.get("meta_info") or {}
                return RequestResult(
                    True,
                    time.perf_counter() - start,
                    int(meta.get("completion_tokens", 0)),
                    prompt_count,
                    client_send_s=client_send_s,
                    output_text=out.get("text") if want_text else None,
                )
            except Exception as e:
                return RequestResult(
                    False,
                    time.perf_counter() - start,
                    0,
                    prompt_count,
                    error=f"{type(e).__name__}: {e}",
                )
        ttft_s = None
        last_tick = None
        gaps_us: list[int] = []
        token_arrival_s: list[float] = []
        token_arrival_monotonic_ns: list[int] = []
        n_tokens = 0
        text: str | None = None
        try:
            generator = await engine.async_generate(
                input_ids=prompt, sampling_params=params, stream=True
            )
            async for out in generator:
                now = time.perf_counter()
                now_monotonic_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
                if want_text:
                    text = out.get("text")
                meta = out.get("meta_info") or {}
                new_total = int(meta.get("completion_tokens", n_tokens))
                if new_total > n_tokens:
                    if measured_epoch_monotonic_ns is not None:
                        delta = new_total - n_tokens
                        token_arrival_s.extend(
                            [
                                (now_monotonic_ns - measured_epoch_monotonic_ns)
                                / 1_000_000_000.0
                            ]
                            * delta
                        )
                        token_arrival_monotonic_ns.extend(
                            [now_monotonic_ns] * delta
                        )
                    if ttft_s is None:
                        ttft_s = now - start
                    else:
                        gaps_us.append(int((now - last_tick) * 1e6))
                    last_tick = now
                    n_tokens = new_total
            returned = time.perf_counter()
            returned_monotonic_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            return RequestResult(
                True,
                returned - start,
                n_tokens,
                prompt_count,
                ttft_s=ttft_s,
                intertoken_us=gaps_us or None,
                client_send_s=client_send_s,
                token_arrival_s=token_arrival_s or None,
                token_arrival_monotonic_ns=token_arrival_monotonic_ns or None,
                client_return_s=(
                    (returned_monotonic_ns - measured_epoch_monotonic_ns)
                    / 1_000_000_000.0
                    if measured_epoch_monotonic_ns is not None
                    else None
                ),
                output_text=text,
            )
        except Exception as e:
            return RequestResult(
                False,
                time.perf_counter() - start,
                n_tokens,
                prompt_count,
                error=f"{type(e).__name__}: {e}",
            )

    pacer = ArrivalPacer(
        arrival_schedule(
            n, args.arrival_rate, args.arrival_process, args.arrival_seed
        )
    )

    async def drive() -> tuple[list[RequestResult], float]:
        if args.warmup:
            warmup_budget = args.warmup_max_tokens
            for j, p in enumerate(prompts[: args.warmup]):
                params = all_sampling[j]
                if warmup_budget is not None:
                    params = {**params, "max_new_tokens": warmup_budget}
                await stream_one(p, prompt_counts[j], params)
            if args.mode != "latency" and max_running_requests > 1:
                short = {**base_sampling, "max_new_tokens": 8}
                await asyncio.gather(*(stream_one(prompts[k % args.warmup], prompt_counts[k % args.warmup], short)
                                       for k in range(max_running_requests)))

        if args.mode == "latency":
            out: list[RequestResult] = []
            begin = time.perf_counter()
            for i in range(n):
                idx = args.warmup + i
                out.append(
                    await stream_one(
                        prompts[idx], prompt_counts[idx], all_sampling[idx]
                    )
                )
            return out, time.perf_counter() - begin

        epoch_monotonic_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        begin = time.perf_counter()
        pacer.start()

        async def offer(i: int) -> RequestResult:
            await pacer.wait(i)
            idx = args.warmup + i
            return await stream_one(
                prompts[idx],
                prompt_counts[idx],
                all_sampling[idx],
                epoch_monotonic_ns,
            )

        gathered = list(await asyncio.gather(*(offer(i) for i in range(n))))
        return gathered, time.perf_counter() - begin

    try:
        results, wall = engine.loop.run_until_complete(drive())
    finally:
        engine.shutdown()

    summary = summarize(
        mode=args.mode,
        engine="sglang",
        model=args.model,
        results=results,
        wall_s=wall,
        config={
            "disable_cuda_graph": args.sglang_disable_cuda_graph,
            "disable_piecewise_cuda_graph": args.sglang_disable_piecewise_cuda_graph,
            "disable_hybrid_swa_memory": args.sglang_disable_hybrid_swa_memory,
            "disable_radix_cache": True,
            "attention_backend": args.sglang_attention_backend,
            "sampling_backend": args.sglang_sampling_backend,
            "max_running_requests": max_running_requests,
            "max_total_tokens": args.sglang_max_total_tokens,
            "page_size": args.sglang_page_size,
            "cuda_graph_max_bs": args.sglang_cuda_graph_max_bs,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "ignore_eos": args.ignore_eos,
            "unique_prompts": args.unique_prompts,
            "cpu affinity": cpu_affinity,
            "warmup max tokens": args.warmup_max_tokens,
            "per-request max tokens": request_max_tokens_varies(args),
            "arrival": {
                "rate": args.arrival_rate,
                "process": args.arrival_process,
                "seed": args.arrival_seed,
                **pacer.stats(),
            },
            "report timing": want_timing,
        },
    )
    return summary, results


def main() -> None:
    parser = argparse.ArgumentParser(description="SGLang canonical latency/throughput benchmark")
    add_mode_subcommands(parser)
    for sp in parser._subparsers._group_actions[0].choices.values():
        add_output_dump_args(sp)
        sp.add_argument(
            "--report-timing",
            action="store_true",
            help="Collect per-request TTFT and inter-token gap distributions. "
                 "Streams every request so the client vantage matches pie's "
                 "and vLLM's (stamps on token delivery, all requests "
                 "submitted at t=0 with the engine enforcing the cap).",
        )
    args = parser.parse_args()
    summary, results = run(args)
    first = next((r.output_text for r in results if r.ok and r.output_text), None)
    print_first_output(args, first)
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
