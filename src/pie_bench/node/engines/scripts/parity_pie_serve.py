#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from pie_bench import EMBEDDED_CLI_ENGINES, build_config, build_parser, find_free_port


def main() -> None:
    args = build_parser().parse_args(sys.argv[1:])
    cfg, _ = build_config(args)
    cfg.server.port = find_free_port()
    if args.engine in EMBEDDED_CLI_ENGINES:
        path = Path(os.environ.get("TMPDIR", "/tmp")) / f"parity-pie-{cfg.server.port}.toml"
        path.write_text(cfg.to_toml())
        proc = subprocess.Popen([str(args.pie_bin), "--config", str(path), "serve"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            sys.stdout.write(line)
            if "Server ready at " in line:
                print(f"PARITY_URL=http://127.0.0.1:{line.strip().rsplit(':', 1)[-1]}", flush=True)
        sys.exit(proc.wait())

    from pie.server import Server

    async def run() -> None:
        async with Server(cfg) as server:
            port = str(server.url).rsplit(":", 1)[-1].strip("/")
            print(f"PARITY_URL=http://127.0.0.1:{port}", flush=True)
            await asyncio.Event().wait()

    asyncio.run(run())


if __name__ == "__main__":
    main()
