#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
pie="$(cd "${1:?usage: build-pie.sh /path/to/pie}" && pwd)"
(cd "$pie/packages/swift" && ./build-xcframework.sh release)
(cd "$pie/examples" && cargo build -p text-completion-bench --target wasm32-wasip3 --release)
mkdir -p "$here/Vendor/pie"
cp "$pie/examples/target/wasm32-wasip3/release/text_completion_bench.wasm" "$here/Vendor/pie/text-completion-bench.wasm"
commit="$(git -C "$pie" rev-parse HEAD)"
cat > "$here/Vendor/pie/PieVendored.swift" <<SWIFT
enum PieBuild {
    static let commit: String? = "$commit"
    static let unavailable = ""
}
SWIFT
cd "$here" && PIE_ENABLED=YES PIE_SWIFT_PACKAGE="$pie/packages/swift" xcodegen generate
echo "== pie $commit built in; open PieBench.xcodeproj (run plain 'xcodegen generate' to drop pie again)"
