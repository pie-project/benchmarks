#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
work="${1:-$(mktemp -d)}"
tag=b11312
mkdir -p "$work" && cd "$work"
[ -d llama.cpp ] || git clone -q --depth 1 --branch "$tag" https://github.com/ggml-org/llama.cpp.git llama.cpp
(cd llama.cpp && ./build-xcframework.sh ios-sim)
[ -f release.zip ] || curl -sSL -o release.zip "https://github.com/ggml-org/llama.cpp/releases/download/$tag/llama-$tag-xcframework.zip"
rm -rf release && mkdir release && unzip -q release.zip -d release
out="$here/Packages/LlamaCpp/local/llama.xcframework"
rm -rf "$out" && mkdir -p "$(dirname "$out")"
xcodebuild -create-xcframework \
  -framework release/build-apple/llama.xcframework/ios-arm64/llama.framework \
  -framework llama.cpp/build-apple/llama.xcframework/ios-arm64_x86_64-simulator/llama.framework \
  -output "$out"
echo "== $out"
