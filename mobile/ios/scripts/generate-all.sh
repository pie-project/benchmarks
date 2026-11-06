#!/usr/bin/env bash
# Regenerates PieBench.xcodeproj with every engine this Mac has built: llama.cpp + MLX always,
# MLC when Vendor/mlc exists (scripts/vendor-mlc.sh), pie when Vendor/pie exists (scripts/build-pie.sh).
#   scripts/generate-all.sh [/path/to/pie-checkout]
# Plain `xcodegen generate` goes back to the llama.cpp + MLX project that is committed.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
[ -d Vendor/mlc/lib ] && export MLC_ENABLED=YES
if [ -n "${1:-}" ] && [ -f Vendor/pie/text-completion-bench.wasm ]; then
  export PIE_ENABLED=YES PIE_SWIFT_PACKAGE="$(cd "$1" && pwd)/packages/swift"
fi
xcodegen generate
echo "== MLC ${MLC_ENABLED:-NO}, pie ${PIE_ENABLED:-NO}"
