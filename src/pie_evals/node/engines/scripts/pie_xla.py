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


def rewrite(text: str) -> str:
    out, section = [], None
    for line in text.splitlines():
        header = re.match(r"^\[([^\]]+)\]\s*$", line)
        if header:
            section = header.group(1)
        elif section == "engine":
            if re.match(r"^type\s*=", line):
                line = 'type = "xla"'
            line = re.sub(r"^total_pages(\s*=)", r"max_total_pages\1", line)
        out.append(line)
    return "\n".join(out) + "\n"


def main() -> None:
    argv = sys.argv[1:]
    real = os.environ.get("PIE_XLA_REAL_PIE")
    if not real:
        sys.exit("pie_xla.py: PIE_XLA_REAL_PIE is not set")
    if "--config" in argv:
        path = argv[argv.index("--config") + 1]
        with open(path) as f:
            text = rewrite(f.read())
        with open(path, "w") as f:
            f.write(text)
    debug = os.environ.get("PIE_XLA_DEBUG_DIR")
    if debug and "serve" in argv:
        import subprocess, time
        run = os.path.join(debug, time.strftime("%H%M%S") + "-" + str(os.getpid()))
        os.makedirs(run, exist_ok=True)
        os.makedirs(debug, exist_ok=True)
        env = dict(os.environ, PIE_XLA_DUMP=os.path.join(run, "dump"), PIE_XLA_CAPTURE=os.path.join(run, "steps"),
                   LIBTPU_INIT_ARGS="--xla_dump_to=" + os.path.join(run, "hlo") + " --xla_dump_hlo_as_text")
        os.makedirs(env["PIE_XLA_CAPTURE"], exist_ok=True)
        if "--config" in argv:
            with open(argv[argv.index("--config") + 1]) as f, open(os.path.join(run, "config.toml"), "w") as g:
                g.write(f.read())
        log = open(os.path.join(run, "server.log"), "w")
        proc = subprocess.Popen([real, *argv], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        import signal
        signal.signal(signal.SIGTERM, lambda *_: proc.terminate())
        signal.signal(signal.SIGINT, lambda *_: proc.terminate())
        t0 = time.monotonic()
        for line in proc.stdout:
            sys.stdout.buffer.write(line)
            sys.stdout.flush()
            log.write("[%9.3f] " % (time.monotonic() - t0) + line.decode("utf-8", "replace"))
            log.flush()
        sys.exit(proc.wait())
    os.execv(real, [real, *argv])


if __name__ == "__main__":
    main()
