#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co")

DTYPE_BYTES = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "F8_E4M3": 1,
    "F8_E5M2": 1,
    "F8_E8M0": 1,
    "F8_E4M3FN": 1,
    "I16": 2,
    "U16": 2,
    "F16": 2,
    "BF16": 2,
    "I32": 4,
    "U32": 4,
    "F32": 4,
    "I64": 8,
    "U64": 8,
    "F64": 8,
}

MAX_SHARD_BYTES = 4 * 1024**3
COALESCE_GAP = 8 * 1024**2
CHUNK = 8 * 1024**2


def _token() -> str | None:
    for env in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        if os.environ.get(env):
            return os.environ[env]
    p = Path.home() / ".cache/huggingface/token"
    if p.is_file():
        t = p.read_text().strip()
        if t:
            return t
    return None


def _request(url: str, headers: dict[str, str] | None = None) -> urllib.request.Request:
    h = dict(headers or {})
    tok = _token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    h.setdefault("User-Agent", "pie-shrink-checkpoint/1.0")
    return urllib.request.Request(url, headers=h)


def _urlopen(url: str, headers: dict[str, str] | None = None, retries: int = 6):
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(_request(url, headers), timeout=120)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404):
                raise
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last}")


def file_url(repo: str, revision: str, name: str) -> str:
    return f"{HF_ENDPOINT}/{repo}/resolve/{revision}/{name}"


def fetch_bytes(
    repo: str, revision: str, name: str, start: int | None = None, end: int | None = None
) -> bytes:
    headers = {}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end - 1}"
    with _urlopen(file_url(repo, revision, name), headers) as resp:
        return resp.read()


def fetch_to_file(repo: str, revision: str, name: str, dest: Path, start: int, end: int) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    piece = 64 << 20
    with tmp.open("wb") as out:
        out.truncate(end - start)

    def part(lo: int) -> int:
        hi = min(lo + piece, end)
        headers = {"Range": f"bytes={lo}-{hi - 1}"}
        n = 0
        with _urlopen(file_url(repo, revision, name), headers) as resp, tmp.open("r+b") as out:
            out.seek(lo - start)
            while True:
                buf = resp.read(CHUNK)
                if not buf:
                    break
                out.write(buf)
                n += len(buf)
        return n

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(8) as pool:
        got = sum(pool.map(part, range(start, end, piece)))
    want = end - start
    if got != want:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{name}[{start}:{end}] short read: {got} != {want}")
    tmp.rename(dest)


def list_repo_files(repo: str, revision: str) -> list[dict[str, Any]]:
    url = f"{HF_ENDPOINT}/api/models/{repo}/revision/{revision}"
    with _urlopen(url) as resp:
        info = json.load(resp)
    return info.get("siblings", [])


@dataclass
class SrcTensor:
    name: str
    shard: str
    dtype: str
    shape: list[int]
    start: int
    end: int
    keep_from: int = 0
    keep_rows: int | None = None

    @property
    def nbytes(self) -> int:
        return self.end - self.start

    @property
    def row_bytes(self) -> int:
        return self.nbytes // self.shape[0] if self.shape and self.shape[0] else self.nbytes

    @property
    def fetch_start(self) -> int:
        return self.start + self.keep_from * self.row_bytes

    @property
    def keep_bytes(self) -> int:
        if self.keep_rows is None or not self.shape:
            return self.nbytes
        if self.keep_from == 0 and self.shape[0] <= self.keep_rows:
            return self.nbytes
        return self.row_bytes * self.keep_rows

    @property
    def keep_end(self) -> int:
        return self.fetch_start + self.keep_bytes


def read_shard_header(repo: str, revision: str, shard: str) -> dict[str, SrcTensor]:
    raw = fetch_bytes(repo, revision, shard, 0, 8)
    hdr_len = int.from_bytes(raw, "little")
    hdr = json.loads(fetch_bytes(repo, revision, shard, 8, 8 + hdr_len))
    data_start = 8 + hdr_len
    out: dict[str, SrcTensor] = {}
    for name, meta in hdr.items():
        if name == "__metadata__":
            continue
        s, e = meta["data_offsets"]
        out[name] = SrcTensor(
            name, shard, meta["dtype"], list(meta["shape"]), data_start + s, data_start + e
        )
    return out


def write_safetensors(
    path: Path, entries: list[tuple[str, str, list[int], Callable[[], Iterable[bytes]]]]
) -> None:
    header: dict[str, Any] = {}
    offset = 0
    for name, dtype, shape, _ in entries:
        n = DTYPE_BYTES[dtype]
        for d in shape:
            n *= d
        header[name] = {"dtype": dtype, "shape": shape, "data_offsets": [offset, offset + n]}
        offset += n
    blob = json.dumps(header, separators=(",", ":")).encode()
    pad = (-len(blob)) % 8
    blob += b" " * pad
    with path.open("wb") as f:
        f.write(len(blob).to_bytes(8, "little"))
        f.write(blob)
        for name, _dtype, _shape, gen in entries:
            want = header[name]["data_offsets"][1] - header[name]["data_offsets"][0]
            got = 0
            for chunk in gen():
                f.write(chunk)
                got += len(chunk)
            if got != want:
                raise RuntimeError(f"{name}: wrote {got} bytes, header says {want}")


@dataclass
class Plan:
    family: str
    layer_prefix: str
    src_layers: list[int]
    experts: int | None
    expert_re: re.Pattern | None
    router_suffixes: tuple[str, ...] = ()
    part_re: re.Pattern | None = None
    parts: int | None = None
    ple_carve: PleCarve | None = None
    globals_keep: tuple[str, ...] = ()
    drop_res: tuple[re.Pattern, ...] = ()
    config_rewrite: Callable[[dict, Plan], None] | None = None
    text_cfg_key: str | None = None
    attn_res_block_size: int | None = None
    text_only: bool = False
    dspark: bool = False
    sink_suffixes: tuple[str, ...] = ()
    sink_rows: int = 0
    engram_vocab: int | None = None
    engram_carve: EngramCarve | None = None


def _text_cfg(cfg: dict, plan: Plan) -> dict:
    return cfg[plan.text_cfg_key] if plan.text_cfg_key else cfg


def _rewrite_common(cfg: dict, plan: Plan) -> None:
    tc = _text_cfg(cfg, plan)
    tc["num_hidden_layers"] = len(plan.src_layers)
    if plan.experts is not None:
        for key in ("n_routed_experts", "num_experts", "num_local_experts"):
            if key in tc:
                tc[key] = plan.experts
        for key in ("num_experts_per_tok", "num_experts_per_token", "moe_topk"):
            if key in tc and isinstance(tc[key], int):
                tc[key] = min(tc[key], plan.experts)
        if tc.get("n_group"):
            tc["n_group"] = min(tc["n_group"], plan.experts)
            tc["topk_group"] = min(tc.get("topk_group", 1), tc["n_group"])
    if "num_nextn_predict_layers" in tc:
        tc["num_nextn_predict_layers"] = 0


def _slice_list(cfg_list: list, src_layers: list[int]) -> list:
    return [cfg_list[i] for i in src_layers]


def _rewrite_glm(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    for key in ("mlp_layer_types", "indexer_types", "layer_types"):
        if isinstance(tc.get(key), list):
            tc[key] = _slice_list(tc[key], plan.src_layers)
    if isinstance(tc.get("mlp_layer_types"), list):
        dense = sum(1 for t in tc["mlp_layer_types"] if t == "dense")
        tc["first_k_dense_replace"] = dense
    it = tc.get("indexer_types")
    if isinstance(it, list) and it and it[0] != "full":
        raise SystemExit("glm: selected layer block must start on a 'full' indexer layer")
    lac = tc.get("linear_attn_config")
    if isinstance(lac, dict):
        remap = {src: i for i, src in enumerate(plan.src_layers)}
        for key in ("kda_layers", "full_attn_layers"):
            if isinstance(lac.get(key), list):
                lac[key] = [remap[s] for s in lac[key] if s in remap]


def _rewrite_dsv4(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    if isinstance(cfg.get("compress_ratios"), list):
        cfg["compress_ratios"] = _slice_list(cfg["compress_ratios"], plan.src_layers)
    if "num_hash_layers" in cfg:
        cfg["num_hash_layers"] = _prefix_count(plan, "num_hash_layers", cfg["num_hash_layers"])


def _rewrite_dsv41(cfg: dict, plan: Plan) -> None:
    stages = _text_cfg(cfg, plan).get("num_nextn_predict_layers") or 0
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    remap = {src: i for i, src in enumerate(plan.src_layers)}
    if isinstance(tc.get("compress_ratios"), list):
        full = tc["compress_ratios"]
        tail = full[len(full) - stages :] if plan.dspark and stages else []
        tc["compress_ratios"] = _slice_list(full, plan.src_layers) + tail
    ratios = tc.get("compress_ratios") or []

    def kept(key: str) -> list[int]:
        return [remap[s] for s in tc.get(key, []) if s in remap]

    kv_sources = kept("kv_source_layer_ids")
    index_sources = kept("index_source_layer_ids")
    for i, ratio in enumerate(ratios):
        if ratio and not any(s <= i for s in kv_sources):
            raise SystemExit(
                f"deepseek_v41: kept layer {i} (source {plan.src_layers[i]}) compresses "
                f"at ratio {ratio} but no kept KV source layer precedes it; keep one of "
                f"{tc.get('kv_source_layer_ids')} before it"
            )
        if ratio and not any(s <= i for s in index_sources):
            raise SystemExit(
                f"deepseek_v41: kept layer {i} (source {plan.src_layers[i]}) attends "
                f"over a selection but no kept index source precedes it; keep one of "
                f"{tc.get('index_source_layer_ids')} before it"
            )
    tc["kv_source_layer_ids"] = kv_sources
    tc["index_source_layer_ids"] = index_sources
    cand = tc.get("candidate_source_layer_id")
    if isinstance(cand, int):
        tc["candidate_source_layer_id"] = remap.get(cand, -1)
    targets = tc.get("dspark_target_layer_ids") or []
    if plan.dspark and targets:
        n = len(targets)
        if n > len(plan.src_layers):
            raise SystemExit(
                f"deepseek_v41: DSpark taps {n} layers and {len(plan.src_layers)} are kept"
            )
        tc["dspark_target_layer_ids"] = list(range(len(plan.src_layers) - n, len(plan.src_layers)))
        tc["num_nextn_predict_layers"] = stages
        if plan.experts is not None and isinstance(tc.get("dspark_n_routed_experts"), int):
            tc["dspark_n_routed_experts"] = min(tc["dspark_n_routed_experts"], plan.experts)
            if isinstance(tc.get("dspark_num_experts_per_tok"), int):
                tc["dspark_num_experts_per_tok"] = min(
                    tc["dspark_num_experts_per_tok"], tc["dspark_n_routed_experts"]
                )
    else:
        tc["num_nextn_predict_layers"] = 0
        if "dspark_block_size" in tc:
            tc["dspark_block_size"] = 0
        if "dspark_target_layer_ids" in tc:
            tc["dspark_target_layer_ids"] = []
    carve = plan.engram_carve
    if carve is not None:
        tc["engram_layer_ids"] = [remap[s] for s in carve.kept_src_layers]
        tc["engram_num_embeddings"] = [sum(p) for p, _ in carve.dst]
        tc["engram_vocab_size"] = carve.dst_base
    else:
        source_ids = tc.get("engram_layer_ids", [])
        if isinstance(tc.get("engram_num_embeddings"), list):
            tc["engram_num_embeddings"] = [
                size
                for source_id, size in zip(source_ids, tc["engram_num_embeddings"])
                if source_id in remap
            ]
        tc["engram_layer_ids"] = kept("engram_layer_ids")


_LAYER_REF = re.compile(r"layers\.(\d+)\.")


def _remap_quant_lists(cfg: dict, plan: Plan) -> None:
    for table in (cfg.get("quantization_config"), _text_cfg(cfg, plan).get("quantization_config")):
        if not isinstance(table, dict):
            continue
        for key in ("ignored_layers", "modules_to_not_convert", "exclude_modules"):
            names = table.get(key)
            if not isinstance(names, list):
                continue
            out: list = []
            for name in names:
                m = _LAYER_REF.search(name) if isinstance(name, str) and "mtp" not in name else None
                if m is None:
                    out.append(name)
                    continue
                src = int(m.group(1))
                out.extend(
                    name[: m.start(1)] + str(dst) + name[m.end(1) :]
                    for dst, kept in enumerate(plan.src_layers)
                    if kept == src
                )
            table[key] = out


def _rewrite_mimo(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    for key in ("hybrid_layer_pattern", "moe_layer_freq"):
        if isinstance(cfg.get(key), list):
            cfg[key] = _slice_list(cfg[key], plan.src_layers)
    _remap_quant_lists(cfg, plan)


def _rewrite_hy4(cfg: dict, plan: Plan) -> None:
    _rewrite_glm(cfg, plan)
    cfg["index_topk"] = 16


def _rewrite_muse_spark(cfg: dict, plan: Plan) -> None:
    _rewrite_muse_glimmer(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("mlp_layer_types"), list):
        tc["mlp_layer_types"] = _slice_list(tc["mlp_layer_types"], plan.src_layers)
    _remap_quant_lists(cfg, plan)


def _rewrite_glm5_next(cfg: dict, plan: Plan) -> None:
    _rewrite_glm(cfg, plan)
    _remap_quant_lists(cfg, plan)


def _rewrite_kimi(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if "first_k_dense_replace" in tc:
        tc["first_k_dense_replace"] = sum(
            1 for i in plan.src_layers if i < tc["first_k_dense_replace"]
        )


def _prefix_count(plan: Plan, key: str, bound: int) -> int:
    marked = [i < bound for i in plan.src_layers]
    n = 0
    while n < len(marked) and marked[n]:
        n += 1
    if any(marked[n:]):
        raise SystemExit(
            f"{plan.family}: the first {bound} source layers are the ones "
            f"`{key}` names, and it can only name a *prefix* of the output "
            f"layers -- so they must be selected once and up front; got "
            f"--layers {plan.src_layers}"
        )
    return n


def _dense_prefix_len(plan: Plan, first_k_dense_replace: int) -> int:
    return _prefix_count(plan, "first_k_dense_replace", first_k_dense_replace)


TEXT_TOWER_PREFIX = "language_model."


def _strip_text_tower(name: str) -> str:
    return name[len(TEXT_TOWER_PREFIX) :] if name.startswith(TEXT_TOWER_PREFIX) else name


def _flatten_text_only(cfg: dict, plan: Plan) -> None:
    tc = cfg.pop(plan.text_cfg_key)
    for key in ("architectures", "auto_map", "_name_or_path", "model_type", "torch_dtype", "dtype"):
        tc.pop(key, None)
    for key in (
        "vision_config",
        "auto_map",
        "image_placeholder",
        "media_placeholder_token_id",
        "ignore_index",
    ):
        cfg.pop(key, None)
    cfg.update(tc)
    cfg["model_type"] = "kimi_k3"
    cfg["architectures"] = ["KimiK3ForCausalLM"]


def _rewrite_kimi_k3(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if "first_k_dense_replace" in tc:
        tc["first_k_dense_replace"] = _dense_prefix_len(plan, tc["first_k_dense_replace"])

    lac = tc.get("linear_attn_config")
    if isinstance(lac, dict):
        src_kda = set(lac.get("kda_layers") or ())
        kda: list[int] = []
        full: list[int] = []
        for out_idx, src_idx in enumerate(plan.src_layers):
            (kda if (src_idx + 1) in src_kda else full).append(out_idx + 1)
        if not kda or not full:
            raise SystemExit(
                "kimi_k3: the selection must keep at least one KDA layer and one "
                "full-attention (MLA) layer; source MLA layers are "
                f"{sorted(i - 1 for i in (lac.get('full_attn_layers') or ()))[:8]}..."
            )
        lac["kda_layers"] = kda
        lac["full_attn_layers"] = full

    if "attn_res_block_size" in tc:
        want = plan.attn_res_block_size
        if want is None:
            want = max(2, len(plan.src_layers) // 3)
        tc["attn_res_block_size"] = min(int(want), tc["attn_res_block_size"])

    if plan.text_only:
        _flatten_text_only(cfg, plan)


def _rewrite_muse_glimmer(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    for key in ("layer_types", "layer_rope_theta"):
        if isinstance(tc.get(key), list):
            tc[key] = _slice_list(tc[key], plan.src_layers)


def _rewrite_gemma4(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("layer_types"), list):
        tc["layer_types"] = _slice_list(tc["layer_types"], plan.src_layers)
    if plan.experts is not None and isinstance(tc.get("top_k_experts"), int):
        tc["top_k_experts"] = min(tc["top_k_experts"], plan.experts)


def _rewrite_inkling(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("local_layer_ids"), list):
        local = set(tc["local_layer_ids"])
        tc["local_layer_ids"] = [i for i, src in enumerate(plan.src_layers) if src in local]
    if isinstance(tc.get("dense_mlp_idx"), int):
        tc["dense_mlp_idx"] = _prefix_count(plan, "dense_mlp_idx", tc["dense_mlp_idx"])
    if isinstance(cfg.get("mtp_config"), dict):
        cfg["mtp_config"]["num_nextn_predict_layers"] = 0
        cfg["mtp_config"]["local_layer_ids"] = []


def _rewrite_minimax_m3(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("moe_layer_freq"), list):
        tc["moe_layer_freq"] = _slice_list(tc["moe_layer_freq"], plan.src_layers)
    sparse = tc.get("sparse_attention_config")
    if isinstance(sparse, dict):
        for key in ("sparse_attention_freq", "sparse_disable_index_value"):
            if isinstance(sparse.get(key), list):
                sparse[key] = _slice_list(sparse[key], plan.src_layers)
    if "num_mtp_modules" in tc:
        tc["num_mtp_modules"] = 0
    tc["num_nextn_predict_layers"] = 0


def _rewrite_nemotron_h(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    pat = cfg.get("hybrid_override_pattern")
    if isinstance(pat, str):
        cfg["hybrid_override_pattern"] = "".join(pat[i] for i in plan.src_layers)
    if isinstance(cfg.get("layers_block_type"), list):
        cfg["layers_block_type"] = _slice_list(cfg["layers_block_type"], plan.src_layers)
    cfg.pop("mtp_hybrid_override_pattern", None)
    cfg.pop("mtp_layers_block_type", None)


def _rewrite_gpt_oss(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    if isinstance(cfg.get("layer_types"), list):
        cfg["layer_types"] = _slice_list(cfg["layer_types"], plan.src_layers)
    if plan.experts is not None and isinstance(cfg.get("experts_per_token"), int):
        cfg["experts_per_token"] = min(cfg["experts_per_token"], plan.experts)


def _rewrite_qwen3_5_moe(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("layer_types"), list):
        tc["layer_types"] = _slice_list(tc["layer_types"], plan.src_layers)
        _check_attn_period(tc, plan)


def _check_attn_period(tc: dict, plan: Plan) -> None:
    interval = tc.get("full_attention_interval")
    if not isinstance(interval, int) or interval <= 0:
        return
    types = tc["layer_types"]
    derived = [
        "full_attention" if (i + 1) % interval == 0 else "linear_attention"
        for i in range(len(types))
    ]
    if types != derived:
        raise SystemExit(
            f"{plan.family}: --layers {plan.src_layers} truncates layer_types to "
            f"{types}, but full_attention_interval {interval} derives {derived}. "
            f"The artifact would say two different things about which layers are "
            f"full-attention; select a block that keeps the two in step (one "
            f"starting at 0 does)."
        )


def _rewrite_qwen4_exp(cfg: dict, plan: Plan) -> None:
    _rewrite_common(cfg, plan)
    tc = _text_cfg(cfg, plan)
    if isinstance(tc.get("layer_types"), list):
        tc["layer_types"] = _slice_list(tc["layer_types"], plan.src_layers)

    src_parts = tc.get("split_ngram_parts")
    if plan.parts is not None and isinstance(src_parts, int):
        if plan.parts > src_parts:
            raise SystemExit(
                f"qwen4_exp: --parts {plan.parts} exceeds the "
                f"checkpoint's {src_parts} n-gram shards"
            )
        tc["split_ngram_parts"] = plan.parts
        base = tc.get("ngram_vocab_size_base")
        if isinstance(base, int):
            tc["ngram_vocab_size_base"] = ple_base_for(base, src_parts, plan.parts)
        carve = plan.ple_carve
        if carve is not None and carve.dst_base != tc.get("ngram_vocab_size_base"):
            raise SystemExit(
                f"qwen4_exp: the carve cut the table for "
                f"ngram_vocab_size_base {carve.dst_base} and the config rewrite "
                f"declares {tc.get('ngram_vocab_size_base')}"
            )

    ids = tc.get("ple_layer_ids")
    if isinstance(ids, list) and ids:
        out_of = {src: out for out, src in enumerate(plan.src_layers)}
        kept = [out_of[i - 1] + 1 for i in ids if (i - 1) in out_of]
        if not kept:
            raise SystemExit(
                f"qwen4_exp: the selection drops every PLE layer (the config's "
                f"one-indexed ple_layer_ids {ids} name layer(s) "
                f"{[i - 1 for i in ids]}), and a Flash-Next without its n-gram "
                f"memory is a different model; got --layers {plan.src_layers}"
            )
        tc["ple_layer_ids"] = kept

    if "mtp_num_hidden_layers" in tc:
        tc["mtp_num_hidden_layers"] = 0
    tc.pop("mtp", None)

    if "language_model_only" in cfg:
        cfg["language_model_only"] = True


def ple_base_for(src_base: int, src_parts: int, dst_parts: int) -> int:
    return src_base * dst_parts // src_parts


def _is_prime(v: int) -> bool:
    if v < 2:
        return False
    if v % 2 == 0:
        return v == 2
    d = 3
    while d * d <= v:
        if v % d == 0:
            return False
        d += 2
    return True


def ngram_hash_geometry(
    base: int, heads: int, divisible_by: int
) -> tuple[list[int], list[int], int]:
    primes: list[int] = []
    offsets: list[int] = []
    total = 0
    prime = base - 1
    for _ in range(heads):
        prime += 1
        while not _is_prime(prime):
            prime += 1
        primes.append(prime)
        offsets.append(total)
        total += prime
    return primes, offsets, -(-total // divisible_by) * divisible_by


@dataclass
class Piece:
    src: SrcTensor
    row0: int
    rows: int


@dataclass
class PleCarve:
    heads: int
    divisible_by: int
    src_base: int
    dst_base: int
    src_parts: int
    dst_parts: int
    src_primes: list[int]
    src_offsets: list[int]
    src_padded: int
    dst_primes: list[int]
    dst_offsets: list[int]
    dst_padded: int
    layout: list[list[tuple[int, int, int]]]
    windows: dict[int, tuple[int, int]]

    @property
    def src_rows(self) -> int:
        return self.src_padded // self.src_parts

    @property
    def dst_rows(self) -> int:
        return self.dst_padded // self.dst_parts


def plan_ple_carve(cfg: dict, plan: Plan) -> PleCarve | None:
    if plan.parts is None or plan.part_re is None:
        return None
    tc = _text_cfg(cfg, plan)
    keys = (
        "ngram_vocab_size_base",
        "split_ngram_parts",
        "ngram_size",
        "heads_per_ngram",
        "make_ngram_vocab_size_divisible_by",
    )
    if any(not isinstance(tc.get(k), int) for k in keys):
        return None
    src_base, src_parts, ngram, per_ngram, divisible_by = (tc[k] for k in keys)
    if plan.parts == src_parts:
        return None
    heads = (ngram - 1) * per_ngram
    dst_base = ple_base_for(src_base, src_parts, plan.parts)

    src_primes, src_offsets, src_padded = ngram_hash_geometry(src_base, heads, divisible_by)
    dst_primes, dst_offsets, dst_padded = ngram_hash_geometry(dst_base, heads, divisible_by)
    if src_padded % src_parts:
        raise SystemExit(
            f"qwen4_exp: the source's {src_padded} padded n-gram rows do not "
            f"divide into its {src_parts} stored shards"
        )
    if dst_padded % plan.parts:
        raise SystemExit(
            f"qwen4_exp: `ngram_vocab_size_base {dst_base}` derives {dst_padded} "
            f"padded n-gram rows, which do not divide into --parts {plan.parts} "
            f"equal shards. Pick a --parts that divides it, or the table cannot "
            f"be stored the way this family stores tables."
        )

    spans = [(src_offsets[h], dst_primes[h]) for h in range(heads)]
    spans[-1] = (spans[-1][0], spans[-1][1] + dst_padded - sum(dst_primes))
    for h, (_, rows) in enumerate(spans):
        if rows > src_primes[h]:
            raise SystemExit(
                f"qwen4_exp: miniature head {h} wants {rows} rows and the "
                f"source's head {h} has {src_primes[h]}: this is a shrink, and "
                f"that would be a growth"
            )

    src_rows = src_padded // src_parts
    dst_rows = dst_padded // plan.parts
    flat: list[tuple[int, int, int]] = []
    for row0, rows in spans:
        at, left = row0, rows
        while left:
            part, local = divmod(at, src_rows)
            take = min(left, src_rows - local)
            flat.append((part, local, take))
            at += take
            left -= take

    layout: list[list[tuple[int, int, int]]] = [[] for _ in range(plan.parts)]
    windows: dict[int, tuple[int, int]] = {}
    at = 0
    for part, local, rows in flat:
        lo, hi = windows.get(part, (local, local + rows))
        windows[part] = (min(lo, local), max(hi, local + rows))
        while rows:
            shard, off = divmod(at, dst_rows)
            take = min(rows, dst_rows - off)
            layout[shard].append((part, local, take))
            local += take
            at += take
            rows -= take
    if at != dst_padded:
        raise SystemExit(f"qwen4_exp: the carve laid {at} rows, not {dst_padded}")

    return PleCarve(
        heads=heads,
        divisible_by=divisible_by,
        src_base=src_base,
        dst_base=dst_base,
        src_parts=src_parts,
        dst_parts=plan.parts,
        src_primes=src_primes,
        src_offsets=src_offsets,
        src_padded=src_padded,
        dst_primes=dst_primes,
        dst_offsets=dst_offsets,
        dst_padded=dst_padded,
        layout=layout,
        windows=windows,
    )


def carve_source_names(pairs: list[tuple[str, str]], plan: Plan) -> list[str]:
    carve = plan.ple_carve
    if carve is None:
        return []
    extra: set[str] = set()
    for _, src_name in pairs:
        if plan.part_re.search(src_name) is None:
            continue
        for part in carve.windows:
            extra.add(_part_name(src_name, plan, part))
    return sorted(extra)


def _part_name(src_name: str, plan: Plan, part: int) -> str:
    m = plan.part_re.search(src_name)
    lo, hi = m.span(1)
    return f"{src_name[:lo]}{part}{src_name[hi:]}"


def apply_ple_carve(
    outs: list[OutTensor], src: dict[str, SrcTensor], plan: Plan
) -> list[tuple[str, SrcTensor, bytes]]:
    carve = plan.ple_carve
    if carve is None:
        return []
    i64 = lambda v: b"".join(int(x).to_bytes(8, "little", signed=True) for x in v)

    seen = 0
    checks: list[tuple[str, SrcTensor, bytes]] = []
    for ot in outs:
        if plan.part_re.search(ot.src.name) is not None:
            out_part = int(plan.part_re.search(ot.name).group(1))
            rows_each = ot.src.shape[0]
            if rows_each != carve.src_rows:
                raise SystemExit(
                    f"{ot.src.name} stores {rows_each} rows and the config's "
                    f"hashing derives {carve.src_rows} per shard: the table in "
                    f"the file is not the table the config describes, and this "
                    f"tool will not guess which is right"
                )
            ot.pieces = [
                Piece(src[_part_name(ot.src.name, plan, part)], row0, rows)
                for part, row0, rows in carve.layout[out_part]
            ]
            ot.rows = carve.dst_rows
            seen += 1
            for part, (lo, hi) in carve.windows.items():
                piece = src[_part_name(ot.src.name, plan, part)]
                piece.keep_from, piece.keep_rows = lo, hi - lo
            continue
        tail = ot.src.name.rsplit(".", 1)[-1]
        if tail == "ngram_heads_vocab_sizes":
            ot.literal = i64(carve.dst_primes)
            checks.append((ot.src.name, ot.src, i64(carve.src_primes)))
        elif tail == "ngram_heads_offsets":
            ot.literal = i64(carve.dst_offsets)
            checks.append((ot.src.name, ot.src, i64(carve.src_offsets)))
    print(
        f"      the n-gram table is re-carved by head: {carve.src_padded} rows "
        f"in {carve.src_parts} shards -> {carve.dst_padded} in {carve.dst_parts}, "
        f"{seen} planes from {len(carve.windows)} source shards"
    )
    print(
        f"      heads past {carve.dst_base}: primes {carve.dst_primes[0]}"
        f"..{carve.dst_primes[-1]}, offsets to {carve.dst_offsets[-1]}, "
        f"padded to {carve.dst_padded} = {carve.dst_parts} x {carve.dst_rows}"
    )
    return checks


def carry_quant_overrides(cfg: dict, pairs: list[tuple[str, str]]) -> dict[str, int]:
    kept: dict[str, int] = {}
    for key in ("quantization", "quantization_config"):
        table = cfg.get(key)
        if not isinstance(table, dict):
            continue
        modules = {k: v for k, v in table.items() if isinstance(v, dict) and k != "quantization"}
        rebuilt = {k: v for k, v in table.items() if k not in modules}
        for module, spec in modules.items():
            head = module + "."
            for out_name, src_name in pairs:
                if not src_name.startswith(head):
                    continue
                tail = len(src_name) - len(module)
                rebuilt[out_name[:-tail]] = spec
        cfg[key] = rebuilt
        kept[key] = len(rebuilt) - (len(table) - len(modules))
    return kept


FAMILIES: dict[str, dict[str, Any]] = {
    "qwen3_5_moe": dict(
        layer_prefix="model.language_model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.weight",
            "mlp.experts.gate_up_proj",
            "mlp.experts.down_proj",
        ),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
            "lm_head.weight",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_qwen3_5_moe,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.visual\."),),
    ),
    "qwen3_5_moe_mlx": dict(
        model_type="qwen3_5_moe",
        layer_prefix="language_model.model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.weight",
            "mlp.gate.scales",
            "mlp.gate.biases",
            "mlp.switch_mlp.gate_proj.weight",
            "mlp.switch_mlp.gate_proj.scales",
            "mlp.switch_mlp.gate_proj.biases",
            "mlp.switch_mlp.up_proj.weight",
            "mlp.switch_mlp.up_proj.scales",
            "mlp.switch_mlp.up_proj.biases",
            "mlp.switch_mlp.down_proj.weight",
            "mlp.switch_mlp.down_proj.scales",
            "mlp.switch_mlp.down_proj.biases",
        ),
        globals_keep=(
            "language_model.model.embed_tokens.weight",
            "language_model.model.embed_tokens.scales",
            "language_model.model.embed_tokens.biases",
            "language_model.model.norm.weight",
            "language_model.lm_head.weight",
            "language_model.lm_head.scales",
            "language_model.lm_head.biases",
        ),
        default_layers="0-4",
        config_rewrite=_rewrite_qwen3_5_moe,
        text_cfg_key="text_config",
    ),
    "glm_moe_dsa": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-6",
        config_rewrite=_rewrite_glm,
    ),
    "glm5_next_mlx": dict(
        model_type="glm5_next",
        layer_prefix="model.language_model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.embed_tokens.scales",
            "model.language_model.embed_tokens.biases",
            "model.language_model.norm.weight",
            "lm_head.weight",
            "lm_head.scales",
            "lm_head.biases",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_glm,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.visual\."),),
    ),
    "deepseek_v4": dict(
        layer_prefix="layers.",
        expert_re=re.compile(r"\.ffn\.experts\.(\d+)\."),
        router_suffixes=("ffn.gate.weight", "ffn.gate.bias"),
        globals_keep=(
            "embed.weight",
            "norm.weight",
            "head.weight",
            "hc_head_fn",
            "hc_head_scale",
            "hc_head_base",
        ),
        default_layers="0-5",
        config_rewrite=_rewrite_dsv4,
    ),
    "deepseek_v4_mlx": dict(
        model_type="deepseek_v4",
        layer_prefix="model.layers.",
        expert_re=None,
        router_suffixes=(
            "ffn.gate.weight",
            "ffn.gate.e_score_correction_bias",
            "ffn.switch_mlp.gate_proj.weight",
            "ffn.switch_mlp.gate_proj.scales",
            "ffn.switch_mlp.gate_proj.biases",
            "ffn.switch_mlp.up_proj.weight",
            "ffn.switch_mlp.up_proj.scales",
            "ffn.switch_mlp.up_proj.biases",
            "ffn.switch_mlp.down_proj.weight",
            "ffn.switch_mlp.down_proj.scales",
            "ffn.switch_mlp.down_proj.biases",
        ),
        globals_keep=(
            "model.embed_tokens.weight",
            "model.embed_tokens.scales",
            "model.embed_tokens.biases",
            "model.norm.weight",
            "lm_head.weight",
            "lm_head.scales",
            "lm_head.biases",
            "model.hc_head.base",
            "model.hc_head.fn",
            "model.hc_head.scale",
        ),
        default_layers="0-3,42",
        config_rewrite=_rewrite_dsv4,
    ),
    "deepseek_v41": dict(
        layer_prefix="layers.",
        expert_re=re.compile(r"\.ffn\.experts\.(\d+)\."),
        router_suffixes=("ffn.gate.weight", "ffn.gate.bias", "ffn.gate.bias_vl"),
        globals_keep=("embed.weight", "head.weight", "norm.weight"),
        default_layers="0-3,20,21,24,25",
        config_rewrite=_rewrite_dsv41,
        text_cfg_key="text_config",
    ),
    "qwen4_exp": dict(
        layer_prefix="language_model.model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.weight",
            "mlp.switch_mlp.gate_proj.weight",
            "mlp.switch_mlp.gate_proj.scales",
            "mlp.switch_mlp.gate_proj.biases",
            "mlp.switch_mlp.up_proj.weight",
            "mlp.switch_mlp.up_proj.scales",
            "mlp.switch_mlp.up_proj.biases",
            "mlp.switch_mlp.down_proj.weight",
            "mlp.switch_mlp.down_proj.scales",
            "mlp.switch_mlp.down_proj.biases",
        ),
        part_re=re.compile(r"\.ngram_embedding\.shard_(\d+)\."),
        default_parts=8,
        globals_keep=(
            "language_model.model.embed_tokens.weight",
            "language_model.lm_head.weight",
            "language_model.model.hyper_connection_mixer.hc_norm.weight",
            "language_model.model.hyper_connection_mixer.input_mix_weight_down.weight",
            "language_model.model.hyper_connection_mixer.input_mix_weight_down.scales",
            "language_model.model.hyper_connection_mixer.input_mix_weight_down.biases",
            "language_model.model.hyper_connection_mixer.input_mix_weight_up.weight",
            "language_model.model.hyper_connection_mixer.input_mix_weight_up.scales",
            "language_model.model.hyper_connection_mixer.input_mix_weight_up.biases",
        ),
        default_layers="0-3",
        config_rewrite=_rewrite_qwen4_exp,
        text_cfg_key="text_config",
    ),
    "qwen4_exp_hf": dict(
        model_type="qwen4_exp",
        layer_prefix="model.language_model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.weight",
            "mlp.experts.gate_up_proj",
            "mlp.experts.down_proj",
        ),
        part_re=re.compile(r"\.ngram_embedding\.shard_(\d+)\."),
        default_parts=8,
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "lm_head.weight",
            "model.language_model.hyper_connection_mixer.hc_norm.weight",
            "model.language_model.hyper_connection_mixer.input_mix_weight_down.weight",
            "model.language_model.hyper_connection_mixer.input_mix_weight_up.weight",
        ),
        default_layers="0-3",
        config_rewrite=_rewrite_qwen4_exp,
        text_cfg_key="text_config",
    ),
    "kimi_k25": dict(
        layer_prefix="language_model.model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=(
            "language_model.model.embed_tokens.weight",
            "language_model.model.norm.weight",
            "language_model.lm_head.weight",
        ),
        default_layers="0-3",
        config_rewrite=_rewrite_kimi,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^vision_tower\."), re.compile(r"^mm_projector\.")),
    ),
    "kimi_k3": dict(
        layer_prefix="language_model.model.layers.",
        expert_re=re.compile(r"\.block_sparse_moe\.experts\.(\d+)\."),
        router_suffixes=(
            "block_sparse_moe.gate.weight",
            "block_sparse_moe.gate.e_score_correction_bias",
        ),
        globals_keep=(
            "language_model.model.embed_tokens.weight",
            "language_model.model.norm.weight",
            "language_model.lm_head.weight",
            "language_model.model.output_attn_res_norm.weight",
            "language_model.model.output_attn_res_proj.weight",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_kimi_k3,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^vision_tower\."), re.compile(r"^mm_projector\.")),
    ),
    "gemma4": dict(
        layer_prefix="model.language_model.layers.",
        expert_re=None,
        router_suffixes=(
            "router.proj.weight",
            "router.per_expert_scale",
            "experts.gate_up_proj",
            "experts.down_proj",
        ),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
        ),
        default_layers="0-5",
        config_rewrite=_rewrite_gemma4,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.(vision_tower|embed_vision)\."),),
    ),
    "muse_glimmer": dict(
        layer_prefix="model.language_model.layers.",
        expert_re=None,
        router_suffixes=(),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
            "lm_head.weight",
        ),
        default_layers="0-3,48-51",
        config_rewrite=_rewrite_muse_glimmer,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.vision_"),),
    ),
    "inkling_mm_model": dict(
        layer_prefix="model.llm.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.bias",
            "mlp.experts.w13_weight",
            "mlp.experts.w2_weight",
        ),
        sink_suffixes=("mlp.gate.weight",),
        sink_rows=2,
        globals_keep=(
            "model.llm.embed.weight",
            "model.llm.embed_norm.weight",
            "model.llm.norm.weight",
            "model.llm.unembed.weight",
        ),
        default_layers="0-6",
        config_rewrite=_rewrite_inkling,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.visual\."), re.compile(r"^model\.audio\.")),
    ),
    "llama": dict(
        layer_prefix="model.layers.",
        expert_re=None,
        router_suffixes=(),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-3",
        config_rewrite=_rewrite_common,
    ),
    "qwen3_moe": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight",),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-3",
        config_rewrite=_rewrite_common,
    ),
    "glm4_moe": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-4",
        config_rewrite=_rewrite_common,
    ),
    "qwen3_5_moe_modelopt": dict(
        model_type="qwen3_5_moe",
        layer_prefix="model.language_model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight",),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
            "lm_head.weight",
            "lm_head.weight_scale",
            "lm_head.weight_scale_2",
            "lm_head.input_scale",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_qwen3_5_moe,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.visual\."),),
    ),
    "qwen3_next": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight",),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-7",
        config_rewrite=_rewrite_common,
    ),
    "minimax_m2": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.block_sparse_moe\.experts\.(\d+)\."),
        router_suffixes=(
            "block_sparse_moe.gate.weight",
            "block_sparse_moe.e_score_correction_bias",
        ),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-3",
        config_rewrite=_rewrite_common,
    ),
    "minimax_m3_vl": dict(
        layer_prefix="language_model.model.layers.",
        expert_re=re.compile(r"\.block_sparse_moe\.experts\.(\d+)\."),
        router_suffixes=(
            "block_sparse_moe.gate.weight",
            "block_sparse_moe.e_score_correction_bias",
        ),
        globals_keep=(
            "language_model.model.embed_tokens.weight",
            "language_model.model.norm.weight",
            "language_model.lm_head.weight",
        ),
        default_layers="0-5",
        config_rewrite=_rewrite_minimax_m3,
        text_cfg_key="text_config",
        keep_res=(
            re.compile(r"^vision_tower\."),
            re.compile(r"^multi_modal_projector\."),
            re.compile(r"^patch_merge_mlp\."),
        ),
    ),
    "nemotron_h": dict(
        layer_prefix="backbone.layers.",
        expert_re=re.compile(r"\.mixer\.experts\.(\d+)\."),
        router_suffixes=("mixer.gate.weight", "mixer.gate.e_score_correction_bias"),
        globals_keep=("backbone.embeddings.weight", "backbone.norm_f.weight", "lm_head.weight"),
        default_layers="0-8",
        config_rewrite=_rewrite_nemotron_h,
    ),
    "gpt_oss": dict(
        layer_prefix="model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.router.weight",
            "mlp.router.bias",
            "mlp.experts.gate_up_proj_blocks",
            "mlp.experts.gate_up_proj_scales",
            "mlp.experts.gate_up_proj_bias",
            "mlp.experts.down_proj_blocks",
            "mlp.experts.down_proj_scales",
            "mlp.experts.down_proj_bias",
        ),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-3",
        config_rewrite=_rewrite_gpt_oss,
    ),
    "mimo_v2": dict(
        layer_prefix="model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=("model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"),
        default_layers="0-5",
        config_rewrite=_rewrite_mimo,
        keep_res=(
            re.compile(r"^visual\."),
            re.compile(r"^audio_encoder\."),
            re.compile(r"^speech_embeddings\."),
        ),
        aux_dirs=("audio_tokenizer/",),
    ),
    "hy_v4": dict(
        layer_prefix="model.layers.",
        expert_re=None,
        router_suffixes=(
            "mlp.gate.weight",
            "mlp.gate.e_score_correction_bias",
            "mlp.experts.gate_up_proj",
            "mlp.experts.down_proj",
        ),
        globals_keep=(
            "model.embed_tokens.weight",
            "model.norm.weight",
            "lm_head.weight",
            "model.hc_head.hc_head_base",
            "model.hc_head.hc_head_fn",
            "model.hc_head.hc_head_scale",
        ),
        default_layers="0-5",
        config_rewrite=_rewrite_hy4,
    ),
    "muse_spark": dict(
        layer_prefix="model.language_model.layers.",
        expert_re=None,
        router_suffixes=tuple(
            ["mlp.gate.weight", "mlp.gate.e_score_correction_bias"]
            + [
                f"mlp.experts.{p}{s}"
                for p in ("gate_up_proj", "down_proj")
                for s in ("", "_input_scale", "_weight_scale", "_weight_scale_2")
            ]
        ),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
            "lm_head.weight",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_muse_spark,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.vision_"), re.compile(r"^model\.audio_tower\.")),
    ),
    "glm5_next": dict(
        layer_prefix="model.language_model.layers.",
        expert_re=re.compile(r"\.mlp\.experts\.(\d+)\."),
        router_suffixes=("mlp.gate.weight", "mlp.gate.e_score_correction_bias"),
        globals_keep=(
            "model.language_model.embed_tokens.weight",
            "model.language_model.norm.weight",
            "lm_head.weight",
        ),
        default_layers="0-7",
        config_rewrite=_rewrite_glm5_next,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^model\.visual\."),),
    ),
    "qwen3_5_mlx": dict(
        model_type="qwen3_5",
        layer_prefix="language_model.model.layers.",
        expert_re=None,
        router_suffixes=(),
        globals_keep=tuple(
            f"language_model.{m}.{p}"
            for m in ("model.embed_tokens", "lm_head")
            for p in ("weight", "scales", "biases")
        )
        + ("language_model.model.norm.weight",),
        default_layers="0-7",
        config_rewrite=_rewrite_qwen3_5_moe,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^vision_tower\."),),
    ),
    "gemma4_mlx": dict(
        model_type="gemma4",
        layer_prefix="language_model.model.layers.",
        expert_re=None,
        router_suffixes=tuple(
            f"{m}.{p}"
            for m in (
                "router.proj",
                "experts.switch_glu.gate_proj",
                "experts.switch_glu.up_proj",
                "experts.switch_glu.down_proj",
            )
            for p in ("weight", "scales", "biases")
        )
        + ("router.per_expert_scale",),
        globals_keep=tuple(
            f"language_model.model.embed_tokens.{p}" for p in ("weight", "scales", "biases")
        )
        + ("language_model.model.norm.weight",),
        default_layers="0-5",
        config_rewrite=_rewrite_gemma4,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^(vision_tower|embed_vision)\."),),
    ),
    "muse_glimmer_mlx": dict(
        model_type="muse_glimmer",
        layer_prefix="language_model.model.layers.",
        expert_re=None,
        router_suffixes=(),
        globals_keep=tuple(
            f"language_model.{m}.{p}"
            for m in ("model.embed_tokens", "lm_head")
            for p in ("weight", "scales", "biases")
        )
        + ("language_model.model.norm.weight",),
        default_layers="0-7",
        config_rewrite=_rewrite_muse_glimmer,
        text_cfg_key="text_config",
        keep_res=(re.compile(r"^vision_"),),
    ),
    "gpt_oss_mlx": dict(
        model_type="gpt_oss",
        layer_prefix="model.layers.",
        expert_re=None,
        router_suffixes=tuple(
            f"mlp.{m}.{p}"
            for m in ("router", "experts.gate_proj", "experts.up_proj", "experts.down_proj")
            for p in ("weight", "scales", "biases", "bias")
        ),
        globals_keep=tuple(
            f"{m}.{p}"
            for m in ("model.embed_tokens", "lm_head")
            for p in ("weight", "scales", "biases")
        )
        + ("model.norm.weight",),
        default_layers="0-3",
        config_rewrite=_rewrite_gpt_oss,
    ),
}


def resolve_family(cfg: dict, weight_map: dict[str, str], forced: str | None) -> str:
    if forced is not None:
        if forced not in FAMILIES:
            raise SystemExit(f"unknown --family {forced!r}; known: {sorted(FAMILIES)}")
        return forced
    model_type = cfg.get("model_type", "")
    named = [k for k, v in FAMILIES.items() if v.get("model_type", k) == model_type]
    if not named:
        raise SystemExit(
            f"unsupported model_type {model_type!r}; known: "
            f"{sorted({v.get('model_type', k) for k, v in FAMILIES.items()})}"
        )
    if len(named) == 1:
        return named[0]
    fits = [k for k in named if any(n.startswith(FAMILIES[k]["layer_prefix"]) for n in weight_map)]
    if len(fits) != 1:
        raise SystemExit(
            f"model_type {model_type!r} is described by {named}, and the index "
            f"{'matches all of' if fits else 'matches none of'} their layer "
            f"prefixes {[FAMILIES[k]['layer_prefix'] for k in named]}; "
            f"pass --family"
        )
    return fits[0]


def parse_layer_spec(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part.lstrip("-"):
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


@dataclass
class OutTensor:
    name: str
    src: SrcTensor
    rows: int | None = None
    mod: int | None = None
    pieces: list[Piece] | None = None
    literal: bytes | None = None
    dequant_scale: OutTensor | None = None

    @property
    def out_bytes(self) -> int:
        if self.literal is not None:
            return len(self.literal)
        if self.rows is None or not self.src.shape:
            n = self.src.nbytes
        else:
            n = self.src.row_bytes * self.rows
        return 2 * n if self.dequant_scale is not None else n


def layer_index(name: str, prefix: str) -> int | None:
    if not name.startswith(prefix):
        return None
    rest = name[len(prefix) :]
    head = rest.split(".", 1)[0]
    return int(head) if head.isdigit() else None


def build_out_tensors(
    index: dict[str, str], plan: Plan, keep_res: tuple[re.Pattern, ...]
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for g in plan.globals_keep:
        if g in index:
            pairs.append((g, g))
    for kr in keep_res:
        for name in index:
            if kr.match(name):
                pairs.append((name, name))

    by_layer: dict[int, list[str]] = {}
    for name in index:
        li = layer_index(name, plan.layer_prefix)
        if li is not None:
            by_layer.setdefault(li, []).append(name)

    for out_idx, src_idx in enumerate(plan.src_layers):
        if src_idx not in by_layer:
            raise SystemExit(f"source layer {src_idx} not present in the checkpoint")
        src_pfx = f"{plan.layer_prefix}{src_idx}."
        out_pfx = f"{plan.layer_prefix}{out_idx}."
        for name in sorted(by_layer[src_idx]):
            suffix = name[len(src_pfx) :]
            if plan.experts is not None and plan.expert_re is not None:
                m = plan.expert_re.search(name)
                if m and int(m.group(1)) >= plan.experts:
                    continue
            if plan.parts is not None and plan.part_re is not None:
                m = plan.part_re.search(name)
                if m and int(m.group(1)) >= plan.parts:
                    continue
            pairs.append((out_pfx + suffix, name))
    if plan.dspark:
        for name in sorted(index):
            if not name.startswith("mtp."):
                continue
            if plan.experts is not None and plan.expert_re is not None:
                m = plan.expert_re.search(name)
                if m and int(m.group(1)) >= plan.experts:
                    continue
            pairs.append((name, name))
    return pairs


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="HF repo id, e.g. zai-org/GLM-5.2")
    ap.add_argument("--revision", default="main")
    ap.add_argument("--out", required=True, help="output snapshot directory")
    ap.add_argument(
        "--layers",
        default=None,
        help="source layer indices, e.g. '0-6' or '0,1,2,60' "
        "(default: per-family block covering every layer type)",
    )
    ap.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="repeat the selected layer block N times (weights are "
        "reused, so this costs no extra download)",
    )
    ap.add_argument(
        "--experts", type=int, default=8, help="routed experts to keep per MoE layer (0 = all)"
    )
    ap.add_argument(
        "--parts",
        type=int,
        default=None,
        help="pieces to keep of a weight the checkpoint splits "
        "into a fixed number of them -- Qwen4's PLE n-gram "
        "table (default: the family's, 0 = all)",
    )
    ap.add_argument(
        "--family",
        default=None,
        help="force a FAMILIES entry instead of picking one from "
        "config.json's model_type (two entries can describe "
        "one model_type: upstream naming vs an mlx_lm "
        f"conversion of it). Known: {sorted(FAMILIES)}",
    )
    ap.add_argument(
        "--attn-res-block-size",
        type=int,
        default=None,
        help="Kimi-K3 AttnRes residual-block stride (default: "
        "scaled down with the kept depth so the blend sees "
        "more than one block)",
    )
    ap.add_argument(
        "--text-only",
        action="store_true",
        help="drop the vision tower and flatten the text sub-config "
        "to the top level, producing a text-only checkpoint of "
        "the same decoder (Kimi-K3)",
    )
    ap.add_argument(
        "--engram-vocab",
        type=int,
        default=None,
        help="DeepSeek-V4.1: re-carve each Engram hash table to this "
        "bucket base (the release hashes at 16,000,000; a "
        "miniature at 20,000 keeps ~480k of 384M rows per table)",
    )
    ap.add_argument(
        "--dspark",
        action="store_true",
        help="DeepSeek-V4.1: keep the DSpark draft head (mtp.*), tapping the last kept layers",
    )
    ap.add_argument(
        "--keep-fp8",
        action="store_true",
        help="DeepSeek-V4/V4.1: keep the fp8 planes as released, beside "
        "their `.scale` e8m0 exponents (the release format), rather "
        "than reading them out to bf16",
    )
    ap.add_argument("--cache", default=None, help="raw tensor cache dir (default: <out>/.srccache)")
    ap.add_argument("--keep-cache", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the download plan and exit")
    return ap


def _weight_map(repo: str, revision: str) -> dict[str, str]:
    try:
        index_json = json.loads(fetch_bytes(repo, revision, "model.safetensors.index.json"))
        return index_json["weight_map"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        return {
            name: "model.safetensors"
            for name in read_shard_header(repo, revision, "model.safetensors")
        }


def _plan(args: argparse.Namespace, cfg: dict, family: str, fam: dict[str, Any]) -> Plan:
    src_layers = parse_layer_spec(args.layers or fam["default_layers"])
    if args.repeat > 1:
        src_layers = src_layers * args.repeat
    parts = fam.get("default_parts") if args.parts is None else args.parts
    plan = Plan(
        family=family,
        layer_prefix=fam["layer_prefix"],
        src_layers=src_layers,
        experts=args.experts or None,
        expert_re=fam["expert_re"],
        router_suffixes=fam["router_suffixes"],
        globals_keep=fam["globals_keep"],
        config_rewrite=fam["config_rewrite"],
        text_cfg_key=fam.get("text_cfg_key"),
        attn_res_block_size=args.attn_res_block_size,
        text_only=args.text_only,
        dspark=args.dspark,
        part_re=fam.get("part_re"),
        parts=parts or None,
        sink_suffixes=fam.get("sink_suffixes", ()),
        sink_rows=fam.get("sink_rows", 0),
        engram_vocab=args.engram_vocab,
    )
    plan.engram_carve = plan_engram_carve(cfg, plan)
    plan.ple_carve = plan_ple_carve(cfg, plan)
    return plan


def _output_pairs(args, plan: Plan, fam: dict[str, Any], weight_map: dict[str, str]):
    pairs = build_out_tensors(weight_map, plan, () if args.text_only else fam.get("keep_res", ()))
    if args.text_only and plan.layer_prefix.startswith(TEXT_TOWER_PREFIX):
        pairs = [(_strip_text_tower(out), src) for out, src in pairs]
    src_names = sorted(set(carve_source_names(pairs, plan)) | {s for _, s in pairs})
    missing = [n for n in src_names if n not in weight_map]
    if missing:
        raise SystemExit(
            f"the n-gram carve reads {len(missing)} tensor(s) the "
            f"index does not have, first {missing[0]}"
        )
    print(
        f"      {len(weight_map)} source tensors -> {len(pairs)} output tensors "
        f"({len(src_names)} distinct downloads)"
    )
    return pairs, src_names


def _source_tensors(
    args, weight_map: dict[str, str], src_names: list[str]
) -> tuple[dict[str, SrcTensor], list[str]]:
    shards = sorted({weight_map[s] for s in src_names})
    headers: dict[str, dict[str, SrcTensor]] = {}
    for i, shard in enumerate(shards, 1):
        headers[shard] = read_shard_header(args.repo, args.revision, shard)
        print(f"      [{i}/{len(shards)}] {shard}", end="\r", flush=True)
    print(" " * 78, end="\r")
    src: dict[str, SrcTensor] = {}
    for name in src_names:
        shard = weight_map[name]
        t = headers[shard].get(name)
        if t is None:
            raise SystemExit(f"{name} missing from {shard} header")
        src[name] = t
    return src, shards


def _coalesced(tensors: list[SrcTensor]) -> list[list[SrcTensor]]:
    tensors.sort(key=lambda t: t.fetch_start)
    groups: list[list[SrcTensor]] = []
    for t in tensors:
        if groups and t.fetch_start - groups[-1][-1].keep_end <= COALESCE_GAP:
            groups[-1].append(t)
        else:
            groups.append([t])
    return groups


def _fetch_group(args, cache: Path, shard: str, grp: list[SrcTensor]) -> None:
    lo = grp[0].fetch_start
    hi = max(t.keep_end for t in grp)
    blob_path = cache / f"span-{shard.replace('/', '_')}-{lo}-{hi}.bin"
    fetch_to_file(args.repo, args.revision, shard, blob_path, lo, hi)
    with blob_path.open("rb") as bf:
        for t in grp:
            dest = cache / cache_key(t)
            if dest.exists():
                continue
            bf.seek(t.fetch_start - lo)
            data = bf.read(t.keep_bytes)
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(data)
            tmp.rename(dest)
    blob_path.unlink(missing_ok=True)


def _download(
    args, cache: Path, src: dict[str, SrcTensor], src_names: list[str], total: int
) -> None:
    by_shard: dict[str, list[SrcTensor]] = {}
    for n in src_names:
        by_shard.setdefault(src[n].shard, []).append(src[n])
    done_bytes = 0
    t0 = time.time()
    for shard, tensors in by_shard.items():
        for grp in _coalesced(tensors):
            if all((cache / cache_key(t)).exists() for t in grp):
                done_bytes += sum(t.keep_bytes for t in grp)
                continue
            _fetch_group(args, cache, shard, grp)
            done_bytes += sum(t.keep_bytes for t in grp)
            el = time.time() - t0
            print(
                f"      {done_bytes / 1024**3:7.2f}/{total / 1024**3:.2f} GiB "
                f"({done_bytes / 1024**2 / max(el, 1e-3):.0f} MiB/s)",
                end="\r",
                flush=True,
            )
    print(" " * 78, end="\r")


def _int64s(b: bytes) -> list[int]:
    return [int.from_bytes(b[i : i + 8], "little", signed=True) for i in range(0, len(b), 8)]


def _verify_derived_heads(checks, cache: Path) -> None:
    for name, tensor, want in checks:
        got = (cache / cache_key(tensor)).read_bytes()
        if got != want:
            raise SystemExit(
                f"{name}: this tool derives {_int64s(want)} and the checkpoint "
                f"publishes {_int64s(got)}. The n-gram carve reads the head "
                f"segments the derivation names, so it must not run against a "
                f"hashing it cannot reproduce."
            )
    if checks:
        print(
            f"      the source's own n-gram head buffers are the derivation's "
            f"({len(checks)} of them)"
        )


def _write_config_and_tokenizer(
    args, out_dir: Path, cfg: dict, plan: Plan, pairs, fam: dict[str, Any], shard_files
) -> None:
    plan.config_rewrite(cfg, plan)
    for key, n in carry_quant_overrides(cfg, pairs).items():
        print(f"      {key}: {n} per-tensor overrides carried onto the renumbered names")
    (out_dir / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    copy_aux_files(args.repo, args.revision, out_dir, fam.get("aux_dirs", ()))
    write_index(out_dir, shard_files)
    if plan.family == "deepseek_v41":
        write_engram_token_map(out_dir)


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(os.path.expanduser(args.out))
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Path(os.path.expanduser(args.cache)) if args.cache else out_dir / ".srccache"
    cache.mkdir(parents=True, exist_ok=True)

    print(f"[1/6] reading {args.repo} config + index")
    cfg = json.loads(fetch_bytes(args.repo, args.revision, "config.json"))
    weight_map = _weight_map(args.repo, args.revision)
    family = resolve_family(cfg, weight_map, args.family)
    fam = FAMILIES[family]
    plan = _plan(args, cfg, family, fam)
    pairs, src_names = _output_pairs(args, plan, fam, weight_map)

    print("[2/6] reading safetensors headers")
    src, shards = _source_tensors(args, weight_map, src_names)

    print("[3/6] applying expert-bank slicing")
    outs = assign_rows(pairs, src, plan)
    checks = apply_ple_carve(outs, src, plan)
    src_names = apply_engram_carve(outs, src, plan, weight_map, src_names)
    if not args.keep_fp8:
        outs = mark_fp8_readout(outs, plan)
    raw_total = sum(src[n].nbytes for n in src_names)
    total = sum(src[n].keep_bytes for n in src_names)
    if total < raw_total:
        print(
            f"      expert banks stacked on dim 0 keep only their prefix: "
            f"{total / 1024**3:.2f} GiB instead of {raw_total / 1024**3:.2f}"
        )
    print(f"      download size: {total / 1024**3:.2f} GiB from {len(shards)} shards")
    if args.dry_run:
        for n in src_names[:20]:
            t = src[n]
            print(f"      {n}  {t.dtype}{t.shape}  {t.keep_bytes / 1024**2:.1f} MiB")
        return 0

    print("[4/6] downloading tensors")
    _download(args, cache, src, src_names, total)
    _verify_derived_heads(checks, cache)

    print("[5/6] writing shards")
    shard_files = write_output(out_dir, cache, outs)

    print("[6/6] writing config + tokenizer")
    _write_config_and_tokenizer(args, out_dir, cfg, plan, pairs, fam, shard_files)
    if not args.keep_cache:
        shutil.rmtree(cache, ignore_errors=True)

    size = sum(f.stat().st_size for f in out_dir.glob("*.safetensors"))
    print(
        f"done: {out_dir}  ({size / 1024**3:.2f} GiB, "
        f"{len(outs)} tensors, {len(plan.src_layers)} layers, "
        f"{plan.experts or 'all'} experts)"
    )
    return 0


def _next_prime_after(start: int, seen: set[int]) -> int:
    candidate = start + 1
    while not _is_prime(candidate) or candidate in seen:
        candidate += 1
    return candidate


def engram_geometry(
    base: int, orders: int, heads: int, modules: int
) -> list[tuple[list[int], list[int]]]:
    seen: set[int] = set()
    out: list[tuple[list[int], list[int]]] = []
    for _ in range(modules):
        primes: list[int] = []
        offsets: list[int] = []
        total = 0
        for _ in range(orders):
            current = base - 1
            for _ in range(heads):
                current = _next_prime_after(current, seen)
                seen.add(current)
                primes.append(current)
                offsets.append(total)
                total += current
        out.append((primes, offsets))
    return out


@dataclass
class EngramCarve:
    src_base: int
    dst_base: int
    src: list[tuple[list[int], list[int]]]
    dst: list[tuple[list[int], list[int]]]
    kept_src_layers: list[int]
    kept_src_modules: list[int]


ENGRAM_RE = re.compile(r"^layers\.(\d+)\.engram\.embed\.(weight|scale)$")


def plan_engram_carve(cfg: dict, plan: Plan) -> EngramCarve | None:
    if plan.family != "deepseek_v41" or plan.engram_vocab is None:
        return None
    tc = _text_cfg(cfg, plan)
    layer_ids = list(tc.get("engram_layer_ids") or [])
    if not layer_ids:
        return None
    orders = int(tc["engram_max_ngram_size"]) - 1
    heads = int(tc["engram_n_heads"])
    src_base = int(tc["engram_vocab_size"])
    src = engram_geometry(src_base, orders, heads, len(layer_ids))
    stated = list(tc.get("engram_num_embeddings") or [])
    for i, (primes, _) in enumerate(src):
        if i < len(stated) and sum(primes) != stated[i]:
            raise SystemExit(
                f"deepseek_v41: this tool derives {sum(primes)} rows for Engram module "
                f"{i} and config.json states {stated[i]}; the carve reads the head "
                f"segments the derivation names, so it must not run against a hashing "
                f"it cannot reproduce"
            )
    kept = [(s, m) for m, s in enumerate(layer_ids) if s in plan.src_layers]
    kept.sort(key=lambda sm: plan.src_layers.index(sm[0]))
    dst = engram_geometry(plan.engram_vocab, orders, heads, len(kept))
    return EngramCarve(
        src_base=src_base,
        dst_base=plan.engram_vocab,
        src=src,
        dst=dst,
        kept_src_layers=[s for s, _ in kept],
        kept_src_modules=[m for _, m in kept],
    )


def apply_engram_carve(
    outs: list[OutTensor],
    src: dict[str, SrcTensor],
    plan: Plan,
    weight_map: dict[str, str],
    src_names: list[str],
) -> list[str]:
    carve = plan.engram_carve
    if carve is None:
        return src_names
    drop: set[str] = set()
    extra: list[str] = []
    for ot in outs:
        m = ENGRAM_RE.match(ot.name)
        if m is None:
            continue
        out_layer = int(m.group(1))
        src_layer = plan.src_layers[out_layer]
        k = carve.kept_src_layers.index(src_layer)
        s_primes, s_offsets = carve.src[carve.kept_src_modules[k]]
        d_primes, _ = carve.dst[k]
        if not ot.src.shape or ot.src.shape[0] != sum(s_primes):
            raise SystemExit(
                f"{ot.src.name}: expected {sum(s_primes)} Engram table rows, "
                f"got {ot.src.shape[0] if ot.src.shape else 'no first dimension'}"
            )
        pieces: list[Piece] = []
        for j, (row0, rows) in enumerate(zip(s_offsets, d_primes)):
            if rows > s_primes[j]:
                raise SystemExit(f"{ot.name}: head {j} wants {rows} rows of {s_primes[j]}")
            clone = SrcTensor(
                ot.src.name,
                ot.src.shard,
                ot.src.dtype,
                list(ot.src.shape),
                ot.src.start,
                ot.src.end,
                keep_from=row0,
                keep_rows=rows,
            )
            key = f"{ot.src.name}#engram{j}"
            src[key] = clone
            weight_map[key] = ot.src.shard
            extra.append(key)
            pieces.append(Piece(clone, row0, rows))
        ot.pieces = pieces
        ot.rows = sum(d_primes)
        drop.add(ot.src.name)
    if not drop:
        return src_names
    print(
        f"      the Engram tables are re-carved by head: {carve.src_base} -> "
        f"{carve.dst_base} buckets, {[sum(p) for p, _ in carve.dst]} rows kept of "
        f"{[sum(p) for p, _ in carve.src]}"
    )
    return sorted((set(src_names) - drop) | set(extra))


def mark_fp8_readout(outs: list[OutTensor], plan: Plan) -> list[OutTensor]:
    if plan.family != "deepseek_v41":
        return outs
    by_name = {ot.name: ot for ot in outs}
    kept: list[OutTensor] = []
    consumed: set[str] = set()
    for ot in outs:
        if ot.src.dtype == "F8_E4M3" and ot.name.endswith(".weight"):
            scale = by_name.get(ot.name[: -len(".weight")] + ".scale")
            if scale is not None:
                ot.dequant_scale = scale
                consumed.add(scale.name)
    for ot in outs:
        if ot.name not in consumed:
            kept.append(ot)
    n = sum(1 for ot in kept if ot.dequant_scale is not None)
    if n:
        print(f"      {n} fp8 planes are read out to bf16 with their e8m0 exponents")
    return kept


_E4M3_LUT = None


def _e4m3_lut():
    global _E4M3_LUT
    if _E4M3_LUT is None:
        import numpy as np

        vals = np.zeros(256, dtype=np.float32)
        for b in range(256):
            sign = -1.0 if b & 0x80 else 1.0
            e = (b >> 3) & 0xF
            m = b & 7
            if e == 0:
                v = m / 8.0 * 2.0**-6
            elif e == 15 and m == 7:
                v = float("nan")
            else:
                v = (1.0 + m / 8.0) * 2.0 ** (e - 7)
            vals[b] = sign * v
        _E4M3_LUT = vals
    return _E4M3_LUT


def dequant_fp8_bf16(
    weight: bytes, wshape: list[int], scale: bytes, sshape: list[int]
) -> Iterable[bytes]:
    import numpy as np

    rows, cols = int(wshape[0]), int(wshape[1])
    srows, scols = int(sshape[0]), int(sshape[1])
    if rows % srows or cols % scols:
        raise SystemExit(f"a [{rows}, {cols}] plane does not block by [{srows}, {scols}] exponents")
    br, bc = rows // srows, cols // scols
    lut = _e4m3_lut()
    w = np.frombuffer(weight, dtype=np.uint8).reshape(rows, cols)
    s = np.frombuffer(scale, dtype=np.uint8).reshape(srows, scols)
    step = max(br, (8192 // br) * br)
    for r0 in range(0, rows, step):
        r1 = min(rows, r0 + step)
        f = lut[w[r0:r1]].reshape((r1 - r0) // br, br, scols, bc)
        e = np.ldexp(np.float32(1.0), s[r0 // br : r1 // br].astype(np.int32) - 127)
        f = (f * e[:, None, :, None]).reshape(r1 - r0, cols).astype(np.float32)
        u = f.view(np.uint32)
        rounded = ((u + np.uint32(0x7FFF) + ((u >> 16) & 1)) >> 16).astype(np.uint16)
        yield rounded.tobytes()


def write_engram_token_map(out_dir: Path) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from engram_token_map import FILE, build_compressed_token_map, write_plane
    except ImportError as exc:
        print(f"      engram token map skipped ({exc}); run engram_token_map.py on the snapshot")
        return
    tok = out_dir / "tokenizer.json"
    if not tok.exists():
        print("      engram token map skipped: no tokenizer.json in the snapshot")
        return
    try:
        lookup, compressed = build_compressed_token_map(tok)
    except ImportError as exc:
        print(f"      engram token map skipped ({exc}); run engram_token_map.py on the snapshot")
        return
    write_plane(out_dir / FILE, lookup)
    print(f"      engram token map: {len(lookup)} ids -> {compressed} compressed")


def cache_key(t: SrcTensor) -> str:
    safe = t.name.replace("/", "_")
    rows = "" if t.keep_rows is None else f".rows{t.keep_from}+{t.keep_rows}"
    return f"{safe}{rows}.bin"


def assign_rows(
    pairs: list[tuple[str, str]], src: dict[str, SrcTensor], plan: Plan
) -> list[OutTensor]:
    outs: list[OutTensor] = []
    router_rows = plan.experts
    full: set[str] = set()
    for out_name, src_name in pairs:
        t = src[src_name]
        ot = OutTensor(out_name, t)
        if router_rows is not None:
            tail = src_name.split(plan.layer_prefix, 1)[-1]
            tail = tail.split(".", 1)[-1] if "." in tail else tail
            if src_name.startswith("mtp."):
                tail = src_name.split(".", 2)[-1]
            if tail in plan.router_suffixes and t.shape and t.shape[0] > router_rows:
                ot.rows = router_rows
            if tail in plan.sink_suffixes and t.shape and t.shape[0] > router_rows + plan.sink_rows:
                ot.pieces = [
                    Piece(t, 0, router_rows),
                    Piece(t, t.shape[0] - plan.sink_rows, plan.sink_rows),
                ]
                ot.rows = router_rows + plan.sink_rows
                full.add(src_name)
            if tail.endswith("gate.tid2eid"):
                ot.mod = router_rows
        if ot.rows is None:
            full.add(src_name)
        outs.append(ot)
    for ot in outs:
        if ot.rows is not None and ot.pieces is None and ot.src.name not in full:
            ot.src.keep_rows = ot.rows
    return outs


def transform_bytes(ot: OutTensor, raw: bytes) -> tuple[bytes, list[int]]:
    shape = list(ot.src.shape)
    if ot.rows is not None and shape and shape[0] > ot.rows:
        row = ot.src.nbytes // shape[0]
        raw = raw[: ot.rows * row]
        shape[0] = ot.rows
    if ot.mod:
        import numpy as np

        a = np.frombuffer(raw, dtype=np.int64).copy()
        a %= ot.mod
        raw = a.tobytes()
    return raw, shape


def _rows_from(path: Path, row_bytes: int, skip: int, rows: int) -> Iterable[bytes]:
    left = rows * row_bytes
    with path.open("rb") as f:
        f.seek(skip * row_bytes)
        while left:
            buf = f.read(min(CHUNK, left))
            if not buf:
                raise RuntimeError(f"{path}: ran out {left} bytes early")
            left -= len(buf)
            yield buf


def output_entry(
    cache: Path, ot: OutTensor
) -> tuple[str, str, list[int], Callable[[], Iterable[bytes]]]:
    shape = list(ot.src.shape)
    if ot.literal is not None:
        data = ot.literal
        return ot.name, ot.src.dtype, shape, (lambda: iter((data,)))
    if ot.dequant_scale is not None:
        weight = OutTensor(ot.name, ot.src, rows=ot.rows, pieces=ot.pieces)
        _, wdtype, wshape, wgen = output_entry(cache, weight)
        _, sdtype, sshape, sgen = output_entry(cache, ot.dequant_scale)
        if wdtype != "F8_E4M3" or sdtype != "F8_E8M0":
            raise SystemExit(
                f"{ot.name}: read-out expects F8_E4M3 beside F8_E8M0, got {wdtype}/{sdtype}"
            )

        def readout(wgen=wgen, sgen=sgen, wshape=wshape, sshape=sshape) -> Iterable[bytes]:
            return dequant_fp8_bf16(b"".join(wgen()), wshape, b"".join(sgen()), sshape)

        return ot.name, "BF16", wshape, readout
    if ot.pieces is not None:
        shape[0] = ot.rows

        def joined() -> Iterable[bytes]:
            for piece in ot.pieces:
                yield from _rows_from(
                    cache / cache_key(piece.src),
                    piece.src.row_bytes,
                    piece.row0 - piece.src.keep_from,
                    piece.rows,
                )

        return ot.name, ot.src.dtype, shape, joined
    if ot.mod:
        raw, shape = transform_bytes(ot, (cache / cache_key(ot.src)).read_bytes())
        return ot.name, ot.src.dtype, shape, (lambda r=raw: iter((r,)))
    rows = ot.src.shape[0] if shape else 1
    if ot.rows is not None and shape and shape[0] > ot.rows:
        rows, shape[0] = ot.rows, ot.rows
    path = cache / cache_key(ot.src)
    if not shape:
        return ot.name, ot.src.dtype, shape, (lambda: iter((path.read_bytes(),)))
    return ot.name, ot.src.dtype, shape, (lambda: _rows_from(path, ot.src.row_bytes, 0, rows))


def write_output(out_dir: Path, cache: Path, outs: list[OutTensor]) -> list[tuple[str, list[str]]]:
    for f in out_dir.glob("*.safetensors"):
        f.unlink()
    shards: list[tuple[str, list[str]]] = []
    batch: list[OutTensor] = []
    acc = 0

    def flush(idx: int) -> None:
        nonlocal batch, acc
        if not batch:
            return
        name = f"model-{idx:05d}.safetensors"
        write_safetensors(out_dir / name, [output_entry(cache, ot) for ot in batch])
        shards.append((name, [ot.name for ot in batch]))
        batch, acc = [], 0

    idx = 1
    for ot in outs:
        n = ot.out_bytes
        if acc + n > MAX_SHARD_BYTES and batch:
            flush(idx)
            idx += 1
        batch.append(ot)
        acc += n
    flush(idx)
    return shards


def write_index(out_dir: Path, shards: list[tuple[str, list[str]]]) -> None:
    total = sum((out_dir / n).stat().st_size for n, _ in shards)
    renamed = []
    for i, (name, names) in enumerate(shards, 1):
        new = f"model-{i:05d}-of-{len(shards):05d}.safetensors"
        (out_dir / name).rename(out_dir / new)
        renamed.append((new, names))
    weight_map = {t: n for n, names in renamed for t in names}
    (out_dir / "model.safetensors.index.json").write_text(
        json.dumps({"metadata": {"total_size": total}, "weight_map": weight_map}, indent=2) + "\n"
    )


AUX_MAX = 64 * 1024**2
AUX_SKIP_SUFFIX = (".safetensors", ".bin", ".pt", ".pth", ".gguf", ".h5", ".msgpack")


def copy_aux_files(repo: str, revision: str, out_dir: Path, dirs: tuple[str, ...] = ()) -> None:
    for sib in list_repo_files(repo, revision):
        name = sib.get("rfilename", "")
        if name and name.startswith(dirs):
            (out_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (out_dir / name).write_bytes(fetch_bytes(repo, revision, name))
            continue
        if not name or "/" in name:
            continue
        if name.endswith(AUX_SKIP_SUFFIX) or name == "model.safetensors.index.json":
            continue
        if name == "config.json":
            continue
        try:
            data = fetch_bytes(repo, revision, name)
        except Exception as exc:
            print(f"      skip {name}: {exc}")
            continue
        if len(data) > AUX_MAX:
            continue
        (out_dir / name).write_bytes(data)


if __name__ == "__main__":
    sys.exit(main())
