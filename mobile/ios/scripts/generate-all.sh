#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
[ -d Vendor/mlc/lib ] && export MLC_ENABLED=YES
if [ -n "${1:-}" ] && [ -f Vendor/pie/text-completion-bench.wasm ]; then
  export PIE_ENABLED=YES PIE_SWIFT_PACKAGE="$(cd "$1" && pwd)/packages/swift"
fi
xcodegen generate
echo "== MLC ${MLC_ENABLED:-NO}, pie ${PIE_ENABLED:-NO}"
