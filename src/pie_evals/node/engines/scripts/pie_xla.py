#!/usr/bin/env python3
"""Stands in for the ``pie`` binary when pie_bench.py drives the XLA (TPU) engine.

pie_bench.py has no ``--engine xla``: its choices stop at cuda_native and metal.
Its ``metal`` arm boots ``pie --config <toml> serve`` as a subprocess, so the TPU
cells run through that arm with ``--pie-bin`` pointing here. This rewrites the
``[engine]`` table it was handed into the XLA engine's and execs the real pie
(``$PIE_XLA_REAL_PIE``, built with ``--features xla``). The metal arm writes only
keys ``XlaEngineOptions`` also takes (max_forward_tokens, max_forward_requests,
max_state_slots, max_model_len); its ``total_pages`` is the XLA engine's
``max_total_pages``.

Runs under the TPU VM's system python (3.10), so no tomllib.
"""

import os
import re
import sys


def rewrite(text: str, port: str | None = None) -> str:
    # PIE_XLA_PREWARM (on unless "0"): compile the fire ladder at load, 8 at a time, not one by one under the
    # measured requests, as vLLM-TPU and SGLang-JAX compile their shapes at startup. Without it a batched cell's
    # rounds stall on each new (rows, lanes) shape its arrivals make: v6e qwen3-0.6b c256 (tpu.yml 42468180591)
    # spent 122 s compiling against 29.6 s on the device, and its rounds read 740 / 1730 / 1428 / 1658 tok/s.
    # The load still counts in load_s; the kv pool is sized before the ladder runs, so the memory share holds.
    # PIE_SILENCE_TIMEOUT (e.g. 7200s): how long a lane may wait (on a compile) before the runtime gives up on it
    prewarm = os.environ.get("PIE_XLA_PREWARM", "1") == "1"
    silence = os.environ.get("PIE_SILENCE_TIMEOUT")
    out, section = [], None
    for line in text.splitlines():
        header = re.match(r"^\[([^\]]+)\]\s*$", line)
        if header:
            section = header.group(1)
            out.append(line)
            if section == "engine" and prewarm:
                out.append("prewarm = true")
            if section == "runtime" and silence:
                out.append(f'silence_timeout = "{silence}"')
            continue
        if (section == "engine" and prewarm and re.match(r"^prewarm\s*=", line)) or (section == "runtime" and silence and re.match(r"^silence_timeout\s*=", line)):
            continue
        elif section == "server" and port and re.match(r"^listen\s*=", line):
            # the bench connects to the port in the file's name; its `listen = "127.0.0.1:0"` binds another
            line = f'listen = "127.0.0.1:{port}"'
        elif section == "engine":
            if re.match(r"^type\s*=", line):
                line = 'type = "xla"'
            line = re.sub(r"^total_pages(\s*=)", r"max_total_pages\1", line)
        out.append(line)
    if silence and not any(re.match(r"^\[runtime\]\s*$", ln) for ln in out):
        out += ["[runtime]", f'silence_timeout = "{silence}"']
    return "\n".join(out) + "\n"


def main() -> None:
    argv = sys.argv[1:]
    real = os.environ.get("PIE_XLA_REAL_PIE")
    if not real:
        sys.exit("pie_xla.py: PIE_XLA_REAL_PIE is not set")
    if "--config" in argv:
        path = argv[argv.index("--config") + 1]
        port = re.search(r"-(\d+)\.toml$", path)
        with open(path) as f:
            text = rewrite(f.read(), port and port.group(1))
        with open(path, "w") as f:
            f.write(text)
    os.execv(real, [real, *argv])


if __name__ == "__main__":
    main()
