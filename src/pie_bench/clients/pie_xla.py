#!/usr/bin/env python3

import os
import re
import sys


def _engine_line(line: str) -> str:
    if re.match(r"^type\s*=", line):
        line = 'type = "xla"'
    return re.sub(r"^total_pages(\s*=)", r"max_total_pages\1", line)


def rewrite(text: str, port: str | None = None) -> str:
    out, section = [], None
    for line in text.splitlines():
        header = re.match(r"^\[([^\]]+)\]\s*$", line)
        if header:
            section = header.group(1)
            out.append(line)
            if section == "engine":
                out.append("prewarm = true")
            continue
        if section == "engine" and re.match(r"^prewarm\s*=", line):
            continue
        if section == "server" and port and re.match(r"^listen\s*=", line):
            line = f'listen = "127.0.0.1:{port}"'
        elif section == "engine":
            line = _engine_line(line)
        out.append(line)
    return "\n".join(out) + "\n"


def _rewrite_config_in_place(argv: list[str]) -> None:
    path = argv[argv.index("--config") + 1]
    port = re.search(r"-(\d+)\.toml$", path)
    with open(path) as f:
        text = rewrite(f.read(), port and port.group(1))
    with open(path, "w") as f:
        f.write(text)


def _add_profiler_preload() -> None:
    preload = os.environ.get("PIE_BENCH_PIE_PRELOAD")
    if preload:
        os.environ["LD_PRELOAD"] = " ".join(filter(None, [preload, os.environ.get("LD_PRELOAD")]))


def main() -> None:
    argv = sys.argv[1:]
    real = os.environ.get("PIE_XLA_REAL_PIE")
    if not real:
        sys.exit("pie_xla.py: PIE_XLA_REAL_PIE is not set")
    if "--config" in argv:
        _rewrite_config_in_place(argv)
    _add_profiler_preload()
    os.execv(real, [real, *argv])


if __name__ == "__main__":
    main()
