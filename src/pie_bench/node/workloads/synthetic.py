from __future__ import annotations

import random

from pie_bench.schema import WorkloadSpec

WORDS_PER_TOKEN = 1.0
SEED = 20260730

_WORDS = (
    "the of and to in a is that for it as was with be by on not he this are or his from at which but have an "
    "had they you were their one all we can her has there been if more when will would who so no she what "
    "about up out many then them these some him time into only its two could other new than first any my "
    "now such like our over man me even most made after also did much before here through years where "
    "must way well down should because each just those people how too little state good very make world "
    "still own see men work long get life never day another know while last might great old year off "
    "come since against go came right used take three states himself few house use during without again "
    "place american around however home small found mrs thought went say part once general high upon "
    "school every don does got united left number course war until always away something fact though "
    "water less public put think almost hand enough far took head yet government system better set told "
    "nothing night end why called didn eyes find going look asked later knew point next program city"
).split()


def prompt_words_for_tokens(n_tokens: int, seed: int = SEED, salt: str = "") -> str:
    n_words = max(1, int(round(n_tokens * WORDS_PER_TOKEN)))
    rng = random.Random(f"{seed}:{salt}:{n_tokens}")
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def common_args_for(workload: WorkloadSpec, warmup: int = 2) -> list[str]:
    p = workload.params
    kind = str(workload.kind)
    args: list[str] = ["--temperature", str(p.get("temperature", 0)), "--top-p", str(p.get("top_p", 1)), "--ignore-eos", "--warmup", str(warmup), "--no-think"]
    if kind == "long_context":
        prefill = int(p.get("prefill", 2048))
        tail = 64
        args += ["--prompt", prompt_words_for_tokens(tail, salt=workload.id)]
        args += ["--shared-prefix-words", str(int(round((prefill - tail) * WORDS_PER_TOKEN)))]
        args += ["--max-tokens", str(int(p.get("decode", 64)))]
    elif kind in ("single_stream", "control_aa", "concurrency"):
        prompt = str(p["prompt"]) if p.get("prompt") else prompt_words_for_tokens(int(p.get("prefill", 128)), salt=workload.id)
        args += ["--prompt", prompt]
        args += ["--max-tokens", str(int(p.get("decode", 64)))]
        if kind == "concurrency":
            args += ["--unique-prompts"]
    elif kind == "prefix_shared":
        args += ["--prompt", prompt_words_for_tokens(int(p.get("unique_suffix", 64)), salt=workload.id)]
        args += ["--shared-prefix-words", str(int(round(int(p.get("shared_prefix", 1024)) * WORDS_PER_TOKEN)))]
        args += ["--max-tokens", str(int(p.get("decode", 64))), "--unique-prompts"]
    elif kind == "mixed_length":
        mu_p, _ = p.get("prompt_lognormal", [6.0, 0.8])
        mu_o, _ = p.get("output_lognormal", [5.0, 0.7])
        import math

        long_words = int(min(int(p.get("max_prompt", 4096)), math.exp(mu_p) * 4) * WORDS_PER_TOKEN)
        args += ["--prompt", prompt_words_for_tokens(int(math.exp(mu_p)), salt=workload.id)]
        args += ["--mixed-phase", "--mixed-long-prompt-words", str(long_words)]
        args += ["--mixed-short-output", str(max(8, int(math.exp(mu_o) / 4)))]
        args += ["--max-tokens", str(int(min(int(p.get("max_output", 1024)), math.exp(mu_o) * 2)))]
        args += ["--output-spread", "4", "--unique-prompts"]
    elif kind == "replay":
        args += ["--prompt", prompt_words_for_tokens(512, salt=workload.id), "--max-tokens", "256"]
        args += ["--arrival-rate", str(p.get("arrival_rate", 4.0)), "--arrival-process", "poisson", "--arrival-seed", str(SEED)]
        args += ["--unique-prompts"]
    else:
        raise ValueError(kind)
    if p.get("request_timeout_s"):
        args += ["--request-timeout", str(int(p["request_timeout_s"]))]
    return args
