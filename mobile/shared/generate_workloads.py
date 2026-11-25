from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pie_bench.metrics.fairness import COLD_SEED, cold_prompts, cold_request_count
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.workloads import prompt_words_for_tokens

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mobile" / "shared" / "workloads.json"
SYSTEM = "You are a helpful benchmarking assistant."
ROUNDS = 3
PHONE_WORKLOADS = ["raw-512-256", "c4", "pf4-512"]
TOKENIZERS = {
    "qwen3.5-0.8b": "mlx-community/Qwen3.5-0.8B-4bit",
    "qwen3.5-4b": "mlx-community/Qwen3.5-4B-4bit",
    "gemma-4-e2b": "mlx-community/gemma-4-e2b-it-4bit",
    "gemma-4-e4b": "mlx-community/gemma-4-e4b-it-4bit",
    "gemma-4-12b": "mlx-community/gemma-4-12B-it-4bit",
}
SPLIT = "\x00USER\x00"


def round_prompts(wl, r: int) -> tuple[list[str], list[str]]:
    p = wl.params
    conc = int(p.get("concurrency", 1))
    n = int(p.get("num_requests") or p.get("requests") or 1)
    warm = conc if conc > 1 else int(p.get("warmup", 1))
    body = (
        str(p["prompt"])
        if p.get("prompt")
        else prompt_words_for_tokens(int(p.get("prefill", 128)), salt=wl.id)
    )
    if p.get("cold_cache"):
        seed = COLD_SEED if r == 0 else f"{COLD_SEED}|round{r}"
        prompts = cold_prompts(body, workload_id=wl.id, seed=seed, count=cold_request_count(p))
    else:
        prompts = [f"{body} (Request #{i})" for i in range(warm + n)]
    return prompts[:warm], prompts[warm : warm + n]


def phone_workload(m: Matrix, wid: str) -> dict:
    wl = m.workloads[wid]
    p = wl.params
    rounds = [dict(zip(("warmup", "measured"), round_prompts(wl, r))) for r in range(ROUNDS)]
    return {
        "id": wid,
        "kind": str(wl.kind),
        "concurrency": int(p.get("concurrency", 1)),
        "prefill": int(p.get("prefill", 128)),
        "decode": int(p.get("decode", 64)),
        "requests": len(rounds[0]["measured"]),
        "warmup": len(rounds[0]["warmup"]),
        "cold_cache": bool(p.get("cold_cache")),
        "temperature": 0.0,
        "ignore_eos": True,
        "rounds": rounds,
    }


def messages(user: str) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def render(tok, user: str) -> str:
    return tok.apply_chat_template(
        messages(user), tokenize=False, add_generation_prompt=True, enable_thinking=False
    )


def prompt_token_counts(tok, model: str, workloads: list[dict], prefix: str, suffix: str) -> dict:
    counts = {}
    for w in workloads:
        per_round = []
        for rnd in w["rounds"]:
            ids = []
            for text in rnd["measured"]:
                rendered = render(tok, text)
                assert rendered == prefix + text + suffix, (model, w["id"])
                ids.append(len(tok.encode(rendered, add_special_tokens=False)))
            per_round.append(ids)
        counts[w["id"]] = per_round
    return counts


def chat_template(model: str, repo: str, workloads: list[dict]) -> dict:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(repo)
    prefix, suffix = render(tok, SPLIT).split(SPLIT)
    counts = prompt_token_counts(tok, model, workloads, prefix, suffix)
    print(model, {k: v[0][:2] for k, v in counts.items()}, file=sys.stderr)
    return {"tokenizer": repo, "prefix": prefix, "suffix": suffix, "prompt_tokens": counts}


def main() -> None:
    m = Matrix.load(MATRIX)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    workloads = [phone_workload(m, wid) for wid in PHONE_WORKLOADS]
    templates = {model: chat_template(model, repo, workloads) for model, repo in TOKENIZERS.items()}
    contract = {
        "schema": "pie-evals-phone-workloads/1",
        "harness_commit": commit,
        "system": SYSTEM,
        "rounds": ROUNDS,
        "workloads": workloads,
        "templates": templates,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, ensure_ascii=False, indent=1) + "\n")
    print(OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
