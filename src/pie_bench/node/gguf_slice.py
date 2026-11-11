from __future__ import annotations

import argparse
import os
import re
import struct
import urllib.request
from pathlib import Path

GGML = {0: (1, 4), 1: (1, 2), 2: (32, 18), 3: (32, 20), 6: (32, 22), 7: (32, 24), 8: (32, 34), 9: (32, 36),
        10: (256, 84), 11: (256, 110), 12: (256, 144), 13: (256, 176), 14: (256, 210), 15: (256, 292),
        16: (256, 66), 17: (256, 74), 18: (256, 98), 19: (256, 50), 20: (32, 18), 21: (256, 110), 22: (256, 82),
        23: (256, 136), 24: (1, 1), 25: (1, 2), 26: (1, 4), 27: (1, 8), 28: (1, 8), 29: (256, 56), 30: (1, 2),
        34: (256, 54), 35: (256, 66), 39: (32, 17)}
SCALAR = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
EXPERT_BANK = re.compile(r"(_exps\.|ffn_gate_inp\.|exp_probs_b\.)")
CHUNK = 64 << 20


def _url(repo: str, revision: str, name: str) -> str:
    return f"{os.environ.get('HF_ENDPOINT', 'https://huggingface.co')}/{repo}/resolve/{revision}/{name}"


def _get(url: str, lo: int, hi: int) -> bytes:
    req = urllib.request.Request(url, headers={"Range": f"bytes={lo}-{hi - 1}"})
    if os.environ.get("HF_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['HF_TOKEN']}")
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except OSError:
            if attempt == 5:
                raise
    raise AssertionError


class _Reader:
    def __init__(self, url: str):
        self.url, self.buf, self.pos = url, b"", 0

    def read(self, n: int) -> bytes:
        while len(self.buf) < self.pos + n:
            self.buf += _get(self.url, len(self.buf), len(self.buf) + max(8 << 20, n))
        b = self.buf[self.pos:self.pos + n]
        self.pos += n
        return b

    def scalar(self, f: str):
        return struct.unpack("<" + f, self.read(struct.calcsize(f)))[0]

    def string(self) -> str:
        return self.read(self.scalar("Q")).decode("utf-8")

    def value(self, t: int):
        if t in SCALAR:
            return self.scalar(SCALAR[t])
        if t == 8:
            return self.string()
        if t == 9:
            et, n = self.scalar("I"), self.scalar("Q")
            return (et, [self.value(et) for _ in range(n)])
        raise ValueError(f"unknown GGUF value type {t}")


def read_header(url: str):
    r = _Reader(url)
    if r.read(4) != b"GGUF":
        raise ValueError(f"{url}: not a GGUF file")
    version, n_tensors, n_kv = r.scalar("I"), r.scalar("Q"), r.scalar("Q")
    kv = []
    for _ in range(n_kv):
        k = r.string()
        t = r.scalar("I")
        kv.append((k, t, r.value(t)))
    tensors = []
    for _ in range(n_tensors):
        name = r.string()
        dims = [r.scalar("Q") for _ in range(r.scalar("I"))]
        ty = r.scalar("I")
        tensors.append((name, dims, ty, r.scalar("Q")))
    return version, kv, tensors, r.pos


def nbytes(dims: list[int], ty: int) -> int:
    blk, size = GGML[ty]
    n = 1
    for d in dims:
        n *= d
    return n // blk * size


def _pack_value(t: int, v) -> bytes:
    if t in SCALAR:
        return struct.pack("<" + SCALAR[t], v)
    if t == 8:
        b = v.encode("utf-8")
        return struct.pack("<Q", len(b)) + b
    et, items = v
    return struct.pack("<IQ", et, len(items)) + b"".join(_pack_value(et, x) for x in items)


def parse_layers(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def plan(kv, tensors, layers: list[int], experts: int | None):
    arch = next(v for k, _, v in kv if k == "general.architecture")
    meta = {k: (t, v) for k, t, v in kv}
    blocks = meta[f"{arch}.block_count"][1]
    n_exp = meta.get(f"{arch}.expert_count", (None, 0))[1]
    nextn = meta.get(f"{arch}.nextn_predict_layers", (None, 0))[1]
    trunk = blocks - nextn
    if max(layers) >= trunk:
        raise SystemExit(f"layer {max(layers)} is past the trunk's {trunk} layers")
    if experts and n_exp and experts > n_exp:
        raise SystemExit(f"{experts} experts asked of {n_exp}")
    new_index = {src: i for i, src in enumerate(layers)}
    out_kv = []
    for k, t, v in kv:
        if k == f"{arch}.block_count":
            v = len(layers)
        elif k == f"{arch}.nextn_predict_layers":
            v = 0
        elif k == f"{arch}.expert_count" and experts:
            v = experts
        elif k == f"{arch}.expert_used_count" and experts:
            v = min(v, experts)
        elif t == 9 and len(v[1]) in (blocks, trunk) and k.startswith(f"{arch}."):
            v = (v[0], [v[1][i] for i in layers])
        out_kv.append((k, t, v))
    out_t = []
    for name, dims, ty, off in tensors:
        m = re.match(r"blk\.(\d+)\.(.*)$", name)
        size = nbytes(dims, ty)
        if m:
            src = int(m.group(1))
            if src not in new_index:
                continue
            name = f"blk.{new_index[src]}.{m.group(2)}"
            if experts and n_exp and dims[-1] == n_exp and EXPERT_BANK.search(name):
                size = size // n_exp * experts
                dims = dims[:-1] + [experts]
        out_t.append((name, dims, ty, off, size))
    return out_kv, out_t


def slice_gguf(repo: str, file: str, layers: str, experts: int | None, out_dir: Path, revision: str = "main", dry_run: bool = False, log=print) -> Path:
    from .snapshots import gguf_shards

    urls = [_url(repo, revision, f) for f in gguf_shards(file)]
    version, kv, tensors = None, None, []
    for si, url in enumerate(urls):
        v, skv, st, end = read_header(url)
        align = next((x for k, _, x in skv if k == "general.alignment"), 32)
        data0 = (end + align - 1) // align * align
        if kv is None:
            version, kv = v, [(k, t, x) for k, t, x in skv if not k.startswith("split.")]
        tensors += [(name, dims, ty, (si, data0 + off)) for name, dims, ty, off in st]
    align = next((x for k, _, x in kv if k == "general.alignment"), 32)
    out_kv, out_t = plan(kv, tensors, parse_layers(layers), experts)
    total = sum(t[4] for t in out_t)
    log(f"gguf slice: {len(out_t)} of {len(tensors)} tensors, {total / 2**30:.2f} GiB of {sum(nbytes(d, ty) for _, d, ty, _ in tensors) / 2**30:.2f}")
    if dry_run:
        return out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / Path(file).name
    head = bytearray(b"GGUF" + struct.pack("<IQQ", version, len(out_t), len(out_kv)))
    for k, t, v in out_kv:
        head += _pack_value(8, k) + struct.pack("<I", t) + _pack_value(t, v)
    offsets, pos = [], 0
    for name, dims, ty, _, size in out_t:
        offsets.append(pos)
        head += _pack_value(8, name) + struct.pack("<I", len(dims)) + b"".join(struct.pack("<Q", d) for d in dims)
        head += struct.pack("<IQ", ty, pos)
        pos = (pos + size + align - 1) // align * align
    head += b"\0" * ((-len(head)) % align)
    tmp = dest.with_suffix(".part")
    groups: list[list[int]] = []
    for i, (_, _, _, (si, off), size) in enumerate(out_t):
        first = out_t[groups[-1][0]] if groups else None
        prev = out_t[groups[-1][-1]] if groups else None
        if prev and prev[3][0] == si and 0 <= off - (prev[3][1] + prev[4]) <= (1 << 20) and off + size - first[3][1] <= CHUNK:
            groups[-1].append(i)
        else:
            groups.append([i])
    done, shown = 0, 0
    with tmp.open("wb") as f:
        f.write(head)
        for g in groups:
            url = urls[out_t[g[0]][3][0]]
            lo = out_t[g[0]][3][1]
            hi = max(out_t[i][3][1] + out_t[i][4] for i in g)
            if hi - lo <= CHUNK:
                span = _get(url, lo, hi)
                for i in g:
                    f.seek(len(head) + offsets[i])
                    f.write(span[out_t[i][3][1] - lo:out_t[i][3][1] - lo + out_t[i][4]])
            else:
                (i,) = g
                f.seek(len(head) + offsets[i])
                for s in range(0, out_t[i][4], CHUNK):
                    f.write(_get(url, lo + s, lo + min(out_t[i][4], s + CHUNK)))
            done += sum(out_t[i][4] for i in g)
            if done - shown >= 1 << 30:
                shown = done
                log(f"gguf slice: {done / 2**30:.2f}/{total / 2**30:.2f} GiB")
        f.truncate(len(head) + pos)
    os.replace(tmp, dest)
    return dest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--revision", default="main")
    ap.add_argument("--layers", required=True)
    ap.add_argument("--experts", type=int, default=0, help="routed experts kept (0 = all)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    slice_gguf(a.repo, a.file, a.layers, a.experts or None, Path(a.out), a.revision, a.dry_run)


if __name__ == "__main__":
    main()
