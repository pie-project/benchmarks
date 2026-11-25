#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
src="$(cd "${1:?mlc-llm checkout}" && pwd)"; dist="$(cd "${2:?dist}" && pwd)"
out="$here/Vendor/mlc"
rm -rf "$out" && mkdir -p "$out/lib" "$out/MLCSwift/tvm_home/3rdparty/tvm-tirx/3rdparty/tvm-ffi/3rdparty/dlpack"
cp "$dist"/lib/*.a "$out/lib/"
cp "$dist/bundle/mlc-app-config.json" "$out/"
cp -R "$src/ios/MLCSwift/Sources" "$src/ios/MLCSwift/Package.swift" "$out/MLCSwift/"
t="$src/3rdparty/tvm"
cp -R "$t/include" "$out/MLCSwift/tvm_home/"
cp -R "$t/3rdparty/tvm-tirx/include" "$out/MLCSwift/tvm_home/3rdparty/tvm-tirx/"
cp -R "$t/3rdparty/tvm-tirx/3rdparty/tvm-ffi/include" "$out/MLCSwift/tvm_home/3rdparty/tvm-tirx/3rdparty/tvm-ffi/"
cp -R "$t/3rdparty/tvm-tirx/3rdparty/tvm-ffi/3rdparty/dlpack/include" "$out/MLCSwift/tvm_home/3rdparty/tvm-tirx/3rdparty/tvm-ffi/3rdparty/dlpack/"
commit="$(git -C "$src" rev-parse HEAD)"
tvm="$(git -C "$t" rev-parse HEAD)"
cat > "$out/MLCBuild.swift" <<SWIFT
enum MLCVendored {
    static let commit = "$commit"
    static let tvm = "$tvm"
}
SWIFT
echo "== $out; now: MLC_ENABLED=YES xcodegen generate (add PIE_ENABLED=YES PIE_SWIFT_PACKAGE=... for pie too)"
