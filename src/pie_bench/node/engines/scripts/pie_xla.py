#!/usr/bin/env python3

import os
import re
import sys


def rewrite(text: str, port: str | None = None) -> str:
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
