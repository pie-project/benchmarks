from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

TOPK = 20
EPS = 1e-12
DECISIVE = 0.5


def _post(url: str, body: dict, timeout: float = 900.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from {url}: {e.read()[:1000].decode(errors='replace')}") from e


def wait_ready(base: str, timeout_s: float = 1800.0) -> str:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            with urllib.request.urlopen(f"{base}/v1/models", timeout=10) as r:
                data = json.loads(r.read()).get("data") or [{}]
                return data[0].get("id") or "default"
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(3)


def greedy(base: str, model: str, prompts: list[str], max_tokens: int, parallel: int = 4, timeout: float = 900.0, retries: int = 0, extra: dict | None = None) -> list[str]:
    def one(p: str) -> str:
        for attempt in range(retries + 1):
            try:
                r = _post(f"{base}/v1/completions", {"model": model, "prompt": p, "max_tokens": max_tokens, "temperature": 0.0, "top_p": 1.0, **(extra or {})}, timeout=timeout)
                return r["choices"][0]["text"]
            except (RuntimeError, TimeoutError, OSError):
                if attempt == retries:
                    raise
        raise AssertionError

    with ThreadPoolExecutor(parallel) as ex:
        return list(ex.map(one, prompts))


def _dist(entry) -> dict[int, float]:
    if not entry:
        return {}
    return {int(k): float(v["logprob"] if isinstance(v, dict) else v) for k, v in entry.items()}


def scored(base: str, model: str, texts: list[str], parallel: int = 4, extra: dict | None = None) -> list[list[dict[int, float]]]:
    def one(t: str) -> list[dict[int, float]]:
        r = _post(f"{base}/v1/completions", {"model": model, "prompt": t, "max_tokens": 1, "temperature": 0.0, "prompt_logprobs": TOPK, **(extra or {})})
        return [_dist(e) for e in r["choices"][0].get("prompt_logprobs") or r.get("prompt_logprobs") or []]

    with ThreadPoolExecutor(parallel) as ex:
        return list(ex.map(one, texts))


def partition_kl(p: dict[int, float], q: dict[int, float]) -> float:
    ranked = sorted(q.values(), reverse=True)
    q_min = math.exp(ranked[min(len(ranked), TOPK) - 1]) if ranked else 0.0
    missing = [t for t in p if t not in q]
    q_unlisted = max(1.0 - sum(math.exp(v) for v in q.values()), 0.0)
    q_missing = min(q_min, q_unlisted / len(missing)) if missing else 0.0
    kl = 0.0
    pr = qr = 1.0
    for t, lp in p.items():
        pp = math.exp(lp)
        lq = q[t] if t in q else math.log(max(q_missing, EPS))
        pr -= pp
        qr -= math.exp(lq)
        kl += pp * (lp - lq)
    pr, qr = max(pr, 0.0), max(qr, EPS)
    if pr > EPS:
        kl += pr * math.log(pr / qr)
    return max(kl, 0.0)


def _argmax(d: dict[int, float]) -> int | None:
    return max(d, key=d.get) if d else None


def compare(ref: list[list[dict[int, float]]], pie: list[list[dict[int, float]]], answer_from: list[int]) -> dict:
    kls: list[float] = []
    agree = total = misaligned = 0
    dec_agree = dec_total = 0
    ref_p1 = ref_mass = 0.0
    for r, p, start in zip(ref, pie, answer_from, strict=True):
        if len(r) != len(p):
            misaligned += 1
        for i in range(start, min(len(r), len(p))):
            if not r[i] or not p[i]:
                continue
            kls.append(partition_kl(r[i], p[i]))
            total += 1
            agree += _argmax(r[i]) == _argmax(p[i])
            top = sorted(r[i].values(), reverse=True)
            ref_p1 += math.exp(top[0])
            ref_mass += sum(math.exp(v) for v in top)
            if len(top) < 2 or top[0] - top[1] >= DECISIVE:
                dec_total += 1
                dec_agree += _argmax(r[i]) == _argmax(p[i])
    kls.sort()
    pct = lambda q: kls[min(len(kls) - 1, int(q * len(kls)))] if kls else None
    return {
        "positions": total, "kl_mean": sum(kls) / len(kls) if kls else None, "kl_p50": pct(0.5), "kl_p99": pct(0.99),
        "kl_max": kls[-1] if kls else None, "top1_agree": agree / total if total else None, "misaligned_texts": misaligned,
        "top1_agree_decisive": dec_agree / dec_total if dec_total else None, "decisive_positions": dec_total,
        "ref_top1_p": ref_p1 / total if total else None, "ref_topk_mass": ref_mass / total if total else None,
    }


def gibberish(tok, n: int = 64, length: int = 48, seed: int = 0) -> list[str]:
    import random

    rng = random.Random(seed)
    special = set(getattr(tok, "all_special_ids", []) or [])
    vocab = [i for i in range(min(len(tok), getattr(tok, "vocab_size", len(tok)))) if i not in special]
    bos = getattr(tok, "bos_token", None) or ""
    if bos == "]~b]" and "]~!b[" in tok.get_vocab():
        bos = "]~!b[" + bos
    out: list[str] = []
    while len(out) < n:
        ids = tok.encode(tok.decode([rng.choice(vocab) for _ in range(length + 1)]), add_special_tokens=False)
        text = tok.decode(ids)
        if ids and tok.encode(text, add_special_tokens=False) == ids and text.isprintable():
            out.append(bos + text)
    return out


def last_position(ref: list[list[dict[int, float]]], pie: list[list[dict[int, float]]], expect: list[int]) -> dict:
    keep = [i for i, (r, p) in enumerate(zip(ref, pie, strict=True)) if len(r) == len(p)]
    out = compare([ref[i] for i in keep], [pie[i] for i in keep], [len(ref[i]) - 1 for i in keep])
    out["prompt_tokens_mismatch"] = len(ref) - len(keep)
    out["prompt_tokens_off_harness"] = sum(1 for i in keep if len(ref[i]) != expect[i])
    kls = [(partition_kl(ref[i][-1], pie[i][-1]), i) for i in keep if ref[i][-1] and pie[i][-1]]
    if kls:
        med = sorted(k for k, _ in kls)[len(kls) // 2]
        k, i = min(kls, key=lambda x: abs(x[0] - med))
        top = sorted(ref[i][-1], key=ref[i][-1].get, reverse=True)[:10]
        out["first_token_kl"] = k
        out["first_token_topk"] = {"prompt": i, "ids": top, "ref": [math.exp(ref[i][-1][t]) for t in top],
                                   "pie": [math.exp(pie[i][-1][t]) if t in pie[i][-1] else None for t in top]}
    return out


def texts_hash(texts: list[str]) -> str:
    return hashlib.sha256(json.dumps(texts).encode()).hexdigest()[:16]


def exact_match(a: list[str], b: list[str]) -> float:
    return sum(x == y for x, y in zip(a, b, strict=True)) / len(a) if a else 0.0
