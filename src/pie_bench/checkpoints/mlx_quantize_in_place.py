#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import sys

import mlx.core as mx

SHARD_BYTES = 4 << 30


def main() -> None:
    src, dst, rules_path = sys.argv[1:4]
    rules = json.loads(open(rules_path).read())
    bits, group = int(rules["bits"]), int(rules["group_size"])
    quantize = [re.compile(r) for r in rules["quantize"]]
    drop = [re.compile(r) for r in rules.get("drop", [])]
    split = {re.compile(k): v for k, v in rules.get("split", {}).items()}
    rename = [(re.compile(k), v) for k, v in rules.get("rename", {}).items()]
    os.makedirs(dst)
    out: dict[str, mx.array] = {}
    index: dict[str, str] = {}
    shard = [0, 0]

    def flush() -> None:
        if not out:
            return
        name = f"model-{shard[0]:05d}.safetensors"
        mx.save_safetensors(os.path.join(dst, name), out, metadata={"format": "mlx"})
        index.update({k: name for k in out})
        out.clear()
        shard[0] += 1
        shard[1] = 0

    def put(key: str, value: mx.array) -> None:
        mx.eval(value)
        out[key] = value
        shard[1] += value.nbytes
        if shard[1] >= SHARD_BYTES:
            flush()

    def emit(key: str, value: mx.array) -> None:
        for pat, new in rename:
            if pat.search(key):
                key = pat.sub(new, key)
        if any(p.search(key) for p in quantize) and key.endswith(".weight") and value.shape[-1] % group == 0:
            w, scales, biases = mx.quantize(value, group_size=group, bits=bits)
            stem = key[: -len(".weight")]
            put(stem + ".weight", w)
            put(stem + ".scales", scales)
            put(stem + ".biases", biases)
        else:
            put(key, value)

    for path in sorted(glob.glob(os.path.join(src, "*.safetensors"))):
        for key, value in mx.load(path).items():
            if any(p.search(key) for p in drop):
                continue
            for pat, how in split.items():
                if pat.search(key):
                    for i, leg in enumerate(mx.split(value, len(how["legs"]), axis=how["axis"])):
                        emit(pat.sub(how["legs"][i], key), leg)
                    break
            else:
                emit(key, value)
    flush()
    total = sum(os.path.getsize(os.path.join(dst, f)) for f in set(index.values()))
    with open(os.path.join(dst, "model.safetensors.index.json"), "w") as f:
        json.dump({"metadata": {"total_size": total}, "weight_map": dict(sorted(index.items()))}, f, indent=1)
    config = json.loads(open(os.path.join(src, "config.json")).read())
    for key in rules.get("config_drop", []):
        config.pop(key, None)
    config["quantization"] = {"group_size": group, "bits": bits, "mode": "affine"}
    with open(os.path.join(dst, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    for name in os.listdir(src):
        if not name.endswith(".safetensors") and name not in ("config.json", "model.safetensors.index.json") and os.path.isfile(os.path.join(src, name)):
            shutil.copy2(os.path.join(src, name), os.path.join(dst, name))
    print(f"quantized {len(index)} tensors into {shard[0]} shards, {total / 2**30:.2f} GiB")


if __name__ == "__main__":
    main()
