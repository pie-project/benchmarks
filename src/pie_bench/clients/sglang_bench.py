#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import inspect
import time
from typing import Any

from bench_args import add_mode_subcommands, add_output_dump_args
from bench_devices import maybe_set_cpu_affinity, visible_cuda_devices
from bench_pacing import ArrivalPacer, arrival_schedule
from bench_prompts import (
    hf_chat_token_ids_and_counts,
    make_prompts,
    request_max_tokens,
    request_max_tokens_varies,
)
from bench_results import RequestResult, finish, print_first_output, summarize
from bench_streaming import StreamTimer
from bench_tracing import end_trace, monotonic_ns

PASSED_WHEN_SET = (
    ("sglang_attention_backend", "attention_backend"),
    ("sglang_sampling_backend", "sampling_backend"),
    ("sglang_moe_runner_backend", "moe_runner_backend"),
    ("sglang_flashinfer_mxfp4_moe_precision", "flashinfer_mxfp4_moe_precision"),
    ("sglang_kv_cache_dtype", "kv_cache_dtype"),
)


def server_arg_names(server_args_cls) -> set[str]:
    fields = getattr(server_args_cls, "__dataclass_fields__", None)
    if fields:
        return set(fields)
    fields = getattr(server_args_cls, "model_fields", None)
    if fields:
        return set(fields)
    return set(inspect.signature(server_args_cls).parameters)


def _graph_kwargs(args: argparse.Namespace, supported: set[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if "disable_piecewise_cuda_graph" in supported:
        kwargs["disable_piecewise_cuda_graph"] = args.sglang_disable_piecewise_cuda_graph
    elif args.sglang_disable_piecewise_cuda_graph and "cuda_graph_backend_prefill" in supported:
        kwargs["cuda_graph_backend_prefill"] = "disabled"
    elif args.sglang_disable_piecewise_cuda_graph:
        raise SystemExit(
            "--sglang-disable-piecewise-cuda-graph: installed SGLang has no such server arg"
        )
    if "disable_hybrid_swa_memory" in supported:
        kwargs["disable_hybrid_swa_memory"] = args.sglang_disable_hybrid_swa_memory
    elif args.sglang_disable_hybrid_swa_memory:
        raise SystemExit(
            "--sglang-disable-hybrid-swa-memory: installed SGLang has no such server arg"
        )
    return kwargs


def _chosen_kwargs(args: argparse.Namespace, supported: set[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        key: getattr(args, flag) for flag, key in PASSED_WHEN_SET if getattr(args, flag)
    }
    if args.sglang_dsa_backend:
        kwargs["dsa_prefill_backend"] = args.sglang_dsa_backend
        kwargs["dsa_decode_backend"] = args.sglang_dsa_backend
    if args.sglang_max_total_tokens is not None:
        kwargs["max_total_tokens"] = args.sglang_max_total_tokens
    if args.sglang_page_size is not None:
        kwargs["page_size"] = args.sglang_page_size
    if args.sglang_cuda_graph_max_bs is not None:
        key = (
            "cuda_graph_max_bs_decode"
            if "cuda_graph_max_bs_decode" in supported
            else "cuda_graph_max_bs"
        )
        kwargs[key] = args.sglang_cuda_graph_max_bs
    return kwargs


def engine_kwargs(
    args: argparse.Namespace, max_running_requests: int, supported: set[str]
) -> dict[str, Any]:
    return {
        "model_path": args.model,
        "trust_remote_code": True,
        "mem_fraction_static": args.gpu_mem_util,
        "disable_cuda_graph": args.sglang_disable_cuda_graph,
        "disable_radix_cache": True,
        "max_running_requests": max_running_requests,
        "tp_size": args.tp_size,
        "context_length": args.max_model_len,
        **_graph_kwargs(args, supported),
        **_chosen_kwargs(args, supported),
    }


def _check_kv_pool(engine, args: argparse.Namespace) -> None:
    got = engine.get_server_info().get("max_total_num_tokens")
    if got != args.sglang_max_total_tokens:
        engine.shutdown()
        raise SystemExit(
            f"SGLang KV pool is {got} tokens, not the requested "
            f"{args.sglang_max_total_tokens}: raise --gpu-mem-util "
            f"(currently {args.gpu_mem_util}) until the memory-derived "
            f"pool exceeds the request."
        )


def build_engine(args: argparse.Namespace, max_running_requests: int):
    import sglang as sgl
    from sglang.srt.server_args import ServerArgs

    supported = server_arg_names(ServerArgs)
    kwargs = engine_kwargs(args, max_running_requests, supported)
    missing = [k for k in kwargs if k not in supported]
    if missing:
        raise SystemExit(f"installed SGLang lacks server args: {missing}")
    engine = sgl.Engine(**kwargs)
    if args.sglang_max_total_tokens is not None:
        _check_kv_pool(engine, args)
    return engine


def max_running_requests_for(args: argparse.Namespace) -> int:
    if args.mode == "latency":
        return 1
    if args.concurrency == 0:
        return max(1, args.num_requests)
    return args.concurrency


def base_sampling(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_tokens,
        "ignore_eos": args.ignore_eos,
    }


def sampling_per_request(args: argparse.Namespace, count: int) -> list[dict[str, Any]]:
    base = base_sampling(args)
    return [
        base
        if request_max_tokens(args, i) == args.max_tokens
        else {**base, "max_new_tokens": request_max_tokens(args, i)}
        for i in range(count)
    ]


async def _generate_whole(
    engine, timer: StreamTimer, prompt, prompt_count: int, params: dict, want_text: bool
) -> RequestResult:
    try:
        out = await engine.async_generate(input_ids=prompt, sampling_params=params, stream=False)
        meta = out.get("meta_info") or {}
        return RequestResult(
            True,
            time.perf_counter() - timer.start,
            int(meta.get("completion_tokens", 0)),
            prompt_count,
            client_send_s=timer.client_send_s,
            output_text=out.get("text") if want_text else None,
        )
    except Exception as e:
        return timer.failure(prompt_count, e, tokens=0)


async def stream_request(
    engine,
    prompt,
    prompt_count: int,
    params: dict,
    epoch_ns: int | None = None,
    *,
    timed: bool,
    want_text: bool,
) -> RequestResult:
    timer = StreamTimer(epoch_ns)
    if not timed:
        return await _generate_whole(engine, timer, prompt, prompt_count, params, want_text)
    text: str | None = None
    try:
        generator = await engine.async_generate(
            input_ids=prompt, sampling_params=params, stream=True
        )
        async for out in generator:
            stamp = timer.stamp()
            if want_text:
                text = out.get("text")
            meta = out.get("meta_info") or {}
            timer.saw(int(meta.get("completion_tokens", timer.tokens)), stamp)
        return timer.result(prompt_count, output_text=text)
    except Exception as e:
        return timer.failure(prompt_count, e)


class Driver:
    def __init__(
        self, engine, args: argparse.Namespace, prompts: list, counts: list[int], max_running: int
    ) -> None:
        self.engine = engine
        self.args = args
        self.prompts = prompts
        self.counts = counts
        self.max_running = max_running
        self.sampling = sampling_per_request(args, len(prompts))
        self.timed = args.report_timing
        self.want_text = args.dump_all_texts or args.dump_first_text

    def request(self, idx: int, params: dict, epoch_ns: int | None = None):
        return stream_request(
            self.engine,
            self.prompts[idx],
            self.counts[idx],
            params,
            epoch_ns,
            timed=self.timed,
            want_text=self.want_text,
        )

    async def warm_up(self) -> None:
        args = self.args
        for j in range(args.warmup):
            params = self.sampling[j]
            if args.warmup_max_tokens is not None:
                params = {**params, "max_new_tokens": args.warmup_max_tokens}
            await self.request(j, params)
        if args.mode != "latency" and self.max_running > 1:
            short = {**base_sampling(args), "max_new_tokens": 8}
            await asyncio.gather(
                *(self.request(k % args.warmup, short) for k in range(self.max_running))
            )

    async def measured(
        self, n: int, pacer: ArrivalPacer, epoch_ns: int
    ) -> tuple[list[RequestResult], float]:
        args = self.args
        if args.mode == "latency":
            out: list[RequestResult] = []
            begin = time.perf_counter()
            for i in range(n):
                idx = args.warmup + i
                out.append(await self.request(idx, self.sampling[idx], epoch_ns))
            return out, time.perf_counter() - begin

        begin = time.perf_counter()
        pacer.start()

        async def offer(i: int) -> RequestResult:
            await pacer.wait(i)
            idx = args.warmup + i
            return await self.request(idx, self.sampling[idx], epoch_ns)

        gathered = list(await asyncio.gather(*(offer(i) for i in range(n))))
        return gathered, time.perf_counter() - begin

    async def drive(
        self, n: int, pacer: ArrivalPacer
    ) -> tuple[list[RequestResult], float, dict[str, Any]]:
        if self.args.warmup:
            await self.warm_up()
        epoch_ns = monotonic_ns()
        epoch = {
            "client timing epoch unix s": time.time(),
            "client timing epoch monotonic ns": epoch_ns,
        }
        results, wall = await self.measured(n, pacer, epoch_ns)
        return results, wall, epoch


def run(args: argparse.Namespace):
    cpu_affinity = maybe_set_cpu_affinity(args, visible_cuda_devices(args.tp_size))
    n = args.requests if args.mode == "latency" else args.num_requests
    prompts, prompt_counts = hf_chat_token_ids_and_counts(
        args.model, args.system, make_prompts(args, n + args.warmup), args.think
    )
    max_running_requests = max_running_requests_for(args)
    engine = build_engine(args, max_running_requests)
    driver = Driver(engine, args, prompts, prompt_counts, max_running_requests)
    pacer = ArrivalPacer(
        arrival_schedule(n, args.arrival_rate, args.arrival_process, args.arrival_seed)
    )
    try:
        results, wall, epoch = engine.loop.run_until_complete(driver.drive(n, pacer))
    finally:
        end_trace()
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
            "report timing": driver.timed,
            **(epoch if driver.timed else {}),
        },
    )
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SGLang canonical latency/throughput benchmark")
    for sp in add_mode_subcommands(parser):
        add_output_dump_args(sp)
        sp.add_argument(
            "--report-timing",
            action="store_true",
            help="Collect per-request TTFT and inter-token gap distributions. "
            "Streams every request so the client vantage matches pie's "
            "and vLLM's (stamps on token delivery, all requests "
            "submitted at t=0 with the engine enforcing the cap).",
        )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary, results = run(args)
    first = next((r.output_text for r in results if r.ok and r.output_text), None)
    print_first_output(args, first)
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
