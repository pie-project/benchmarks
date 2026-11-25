#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
xcf="$(cd "${1:?llama.xcframework}" && pwd)"; home="${2:?home dir}"
fw="$xcf/macos-arm64_x86_64"
mkdir -p "$home"
files=()
for f in JSON Contract Catalog DeviceInfo Downloader Engine LlamaEngine MLXEngine MLCEngine PieEngine PieBuild Runner; do
  files+=("$here/PieBench/$f.swift")
done
xcrun swiftc -O -swift-version 5 -target arm64-apple-macos14 -o "$home/piebench-e2e" "${files[@]}" "$here/e2e/main.swift" \
  -F "$fw" -framework llama -Xlinker -rpath -Xlinker "$fw"
PIEBENCH_HOME="$home" PIEBENCH_WORKLOADS_JSON="$here/../shared/workloads.json" "$home/piebench-e2e"
