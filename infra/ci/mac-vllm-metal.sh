#!/usr/bin/env bash
# vllm-metal <pin> into <dir>, the way its install.sh installs a release: the release's wheel, the vLLM core wheel it
# names (.github/vllm-release-tag.commit at the tag, vLLM's prebuilt macOS arm64 build) and the wheel's torch pins.
# A no-op when <dir> already holds that release.
set -euo pipefail
pin="$1"; dir="$2"
py="$dir/bin/python"
if [ -x "$dir/bin/vllm" ] && [ "$("$py" -c "from importlib.metadata import version; print(version('vllm-metal'))" 2>/dev/null)" = "$pin" ]; then exit 0; fi
rm -rf "$dir"
uv venv --quiet --python 3.12 "$dir"
api() { curl -fsSL ${GH_TOKEN:+-H "Authorization: Bearer $GH_TOKEN"} "https://api.github.com/repos/$1"; }
whl=$(api "vllm-project/vllm-metal/releases/tags/v$pin" | "$py" -c 'import sys, json; print(next(a["browser_download_url"] for a in json.load(sys.stdin)["assets"] if a["name"].endswith(".whl")))')
vtag=$(curl -fsSL "https://raw.githubusercontent.com/vllm-project/vllm-metal/v$pin/.github/vllm-release-tag.commit" | tr -d '[:space:]')
# vLLM publishes a release's wheels on the tag or on its last rc (0.33.0 on v0.33.0rc3): find the asset by name
core=$(api "vllm-project/vllm/releases?per_page=60" | NAME="vllm-${vtag#v}+cpu-cp38-abi3-macosx_11_0_arm64.whl" "$py" -c 'import os, sys, json; n = os.environ["NAME"]; print(next(a["browser_download_url"] for r in json.load(sys.stdin) for a in r["assets"] if a["name"] == n))')
echo "vllm-metal $pin: $whl over vLLM $vtag ($core)"
uv pip install --quiet --python "$py" "$core"
uv pip install --quiet --python "$py" "$whl"
req=$("$py" -I -c 'from importlib.metadata import distribution; print(distribution("vllm-metal").locate_file("vllm_metal/requirements-torch.txt"))')
if [ -f "$req" ]; then uv pip install --quiet --python "$py" -r "$req"; fi
"$py" -c "from importlib.metadata import version; print('installed vllm-metal', version('vllm-metal'), 'vllm', version('vllm'))"
