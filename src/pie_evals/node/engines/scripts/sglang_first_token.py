"""SGLang's next-token top-k after each prompt, as a second reference for a first-token parity check (diag).

usage: <sglang python> sglang_first_token.py <pie_root> <prompts.json: token id lists> <out.json> <topk> -- <sglang_bench args>
The engine is built by pie's scripts/bench/sglang_bench.py from the same flags the harness's SglangEngine passes it.
SGLang starts its scheduler with the spawn method, which imports this file again: all work sits under the main guard."""
import argparse
import json
import sys


def main() -> None:
    pie_root, prompts_path, out_path, topk = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    bench_argv = sys.argv[sys.argv.index("--") + 1:]
    sys.path.insert(0, f"{pie_root}/scripts/bench")
    import sglang_bench

    parser = argparse.ArgumentParser()
    sglang_bench.add_mode_subcommands(parser)
    args, unknown = parser.parse_known_args(["latency", *bench_argv])
    if unknown:
        print(f"sglang_first_token: ignored {unknown}", file=sys.stderr, flush=True)
    engine = sglang_bench.build_engine(args, max_running_requests=1)
    out = []
    try:
        for ids in json.load(open(prompts_path)):
            r = engine.generate(input_ids=ids, sampling_params={"max_new_tokens": 1, "temperature": 0.0}, return_logprob=True, top_logprobs_num=topk)
            top = r["meta_info"]["output_top_logprobs"][0]
            out.append({str(int(t[1])): float(t[0]) for t in top})
    finally:
        engine.shutdown()
    json.dump({"version": __import__("sglang").__version__, "last": out}, open(out_path, "w"))
    print(f"sglang_first_token: {len(out)} prompts", flush=True)


if __name__ == "__main__":
    main()
