from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

IMAGES = [("sglang", "SGLang", "lmsysorg/sglang", "latest"), ("vllm", "vLLM", "vllm/vllm-openai", "latest")]
PIE = "pie-project/pie"
PIE_ASSET = re.compile(r"pie-x86_64-linux-cuda[\d.]*\.tar\.gz")


def _get(url: str) -> dict:
    headers = {"User-Agent": "pie-bench-api", "Accept": "application/json"}
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as res:
        return json.load(res)


def sizes(get=None) -> dict:
    get, engines = get or _get, []
    for id, name, repo, tag in IMAGES:
        images = get(f"https://hub.docker.com/v2/repositories/{repo}/tags/{tag}")["images"]
        size = next(i["size"] for i in images if i.get("os") == "linux" and i.get("architecture") == "amd64")
        engines.append({"id": id, "name": name, "what": "Docker image", "source": f"{repo}:{tag}", "mb": round(size / 1e6)})
    release = get(f"https://api.github.com/repos/{PIE}/releases/latest")
    asset = next(a for a in release["assets"] if PIE_ASSET.fullmatch(a["name"]))
    engines.append({"id": "pie", "name": "Pie", "what": "Single binary", "source": f"{PIE} {release['tag_name']} {asset['name']}", "mb": round(asset["size"] / 1e6)})
    return {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "download": "compressed, linux/amd64", "engines": engines}
