from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import numpy as np

_DT = {
    "F32": np.float32,
    "F16": np.float16,
    "U8": np.uint8,
    "I8": np.int8,
    "F8_E4M3": np.uint8,
    "F8_E8M0": np.uint8,
    "BF16": np.uint16,
    "I32": np.int32,
    "I64": np.int64,
    "U16": np.uint16,
    "BOOL": np.uint8,
}
_FP4 = np.array(
    [0, 0.5, 1, 1.5, 2, 3, 4, 6, -0.0, -0.5, -1, -1.5, -2, -3, -4, -6], dtype=np.float32
)


def _e4m3() -> np.ndarray:
    b = np.arange(256)
    s, e, m = b >> 7, (b >> 3) & 0xF, b & 7
    v = np.where(e == 0, m / 8.0 * 2.0**-6, (1 + m / 8.0) * 2.0 ** (e - 7.0))
    v = np.where((e == 15) & (m == 7), np.nan, v)
    return np.where(s == 1, -v, v).astype(np.float32)


_E4M3 = _e4m3()


def _bf16(x: np.ndarray) -> np.ndarray:
    u = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    return ((u + 0x7FFF + ((u >> 16) & 1)) >> 16).astype(np.uint16)


def _read(path: Path) -> tuple[dict, int, np.memmap]:
    with path.open("rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(n))
    return header, 8 + n, np.memmap(path, dtype=np.uint8, mode="r")


def _tensor(header: dict, base: int, mm: np.memmap, name: str) -> np.ndarray:
    h = header[name]
    a, b = h["data_offsets"]
    return np.frombuffer(mm[base + a : base + b], dtype=_DT[h["dtype"]]).reshape(h["shape"])


def _mxfp8(w: np.ndarray, s: np.ndarray) -> np.ndarray:
    block = w.shape[-1] // s.shape[-1]
    scale = np.ldexp(np.float32(1), s.astype(np.int32) - 127).astype(np.float32)
    return _E4M3[w] * np.repeat(scale, block, axis=-1)


def _nvfp4(packed: np.ndarray, s: np.ndarray, g: np.ndarray) -> np.ndarray:
    codes = np.stack([packed & 0xF, packed >> 4], axis=-1).reshape(
        *packed.shape[:-1], packed.shape[-1] * 2
    )
    block = codes.shape[-1] // s.shape[-1]
    scale = _E4M3[s] / np.float32(g.reshape(-1)[0])
    return _FP4[codes] * np.repeat(scale, block, axis=-1)


def widen_shard(path: Path) -> dict[str, str] | None:
    header, base, mm = _read(path)
    meta = header.pop("__metadata__", None)
    names = set(header)
    out: list[tuple[str, str, list[int], int, object]] = []
    renamed: dict[str, str] = {}
    widened = 0
    for name in sorted(names):
        h = header[name]
        stem = name.rsplit(".", 1)[0]
        if (
            name.endswith(".weight")
            and h["dtype"] == "F8_E4M3"
            and f"{stem}.weight_scale_inv" in names
        ):
            widened += 1
            out.append(
                (
                    name,
                    "BF16",
                    h["shape"],
                    2 * int(np.prod(h["shape"])),
                    lambda n=name, st=stem: _bf16(
                        _mxfp8(
                            _tensor(header, base, mm, n),
                            _tensor(header, base, mm, f"{st}.weight_scale_inv"),
                        )
                    ),
                )
            )
        elif (
            name.endswith(".weight_packed")
            and f"{stem}.weight_scale" in names
            and f"{stem}.weight_global_scale" in names
        ):
            widened += 1
            shape = [*h["shape"][:-1], h["shape"][-1] * 2]
            renamed[name] = f"{stem}.weight"
            out.append(
                (
                    f"{stem}.weight",
                    "BF16",
                    shape,
                    2 * int(np.prod(shape)),
                    lambda n=name, st=stem: _bf16(
                        _nvfp4(
                            _tensor(header, base, mm, n),
                            _tensor(header, base, mm, f"{st}.weight_scale"),
                            _tensor(header, base, mm, f"{st}.weight_global_scale"),
                        )
                    ),
                )
            )
        elif (
            name.endswith(".weight_scale_inv")
            and header.get(f"{stem}.weight", {}).get("dtype") == "F8_E4M3"
        ) or (
            name.endswith((".weight_scale", ".weight_global_scale", ".input_global_scale"))
            and f"{stem}.weight_packed" in names
        ):
            renamed[name] = ""
        else:
            a, b = h["data_offsets"]
            out.append(
                (name, h["dtype"], h["shape"], b - a, lambda a=a, b=b: mm[base + a : base + b])
            )
    if not widened:
        return None
    new_header: dict = {"__metadata__": meta} if meta else {}
    off = 0
    for name, dtype, shape, size, _ in out:
        new_header[name] = {"dtype": dtype, "shape": shape, "data_offsets": [off, off + size]}
        off += size
    blob = json.dumps(new_header, separators=(",", ":")).encode()
    blob += b" " * (-len(blob) % 8)
    tmp = path.with_name(path.name + ".widen")
    with tmp.open("wb") as f:
        f.write(struct.pack("<Q", len(blob)))
        f.write(blob)
        for name, _dtype, _shape, size, data in out:
            arr = np.ascontiguousarray(data())
            assert arr.nbytes == size, (name, arr.nbytes, size)
            f.write(memoryview(arr).cast("B"))
    mm = None
    os.replace(tmp, path)
    return renamed


def widen_bf16(snapshot: Path, log=print) -> None:
    snapshot = Path(snapshot)
    renamed: dict[str, str] = {}
    for shard in sorted(snapshot.glob("*.safetensors")):
        renamed.update(widen_shard(shard) or {})
    index = snapshot / "model.safetensors.index.json"
    if index.exists():
        d = json.loads(index.read_text())
        wm = {}
        for k, v in d.get("weight_map", {}).items():
            k2 = renamed.get(k, k)
            if k2:
                wm[k2] = v
        d["weight_map"] = wm
        d.pop("metadata", None)
        index.write_text(json.dumps(d, indent=2))
    cfg_path = snapshot / "config.json"
    cfg = json.loads(cfg_path.read_text())
    cfg.pop("quantization_config", None)
    if isinstance(cfg.get("text_config"), dict):
        cfg["text_config"].pop("quantization_config", None)
    cfg_path.write_text(json.dumps(cfg, indent=2))
    log(
        f"widen: {snapshot.name}: {sum(1 for v in renamed.values() if not v)} scale planes dropped, quantized planes read out to bf16"
    )
