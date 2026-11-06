#!/usr/bin/env bash
# Puts a built MLC LLM iOS runtime into Vendor/mlc and generates the project with it (MLC_ENABLED).
#   scripts/vendor-mlc.sh <mlc-llm checkout> <dist dir of `mlc_llm package`>
#
# How the dist was made (2026-11-05, Mac, Xcode 27.2): mlc-llm main 44fd06d0 with its TVM submodule built
# from source (LLVM 20 static, Metal on; the nightly wheels lack gemma4 and crash on `compile --device iphone`),
# TVM patched with scripts/mlc-tvm-ios.patch (AttachGlobalSymbol returns the call as an Expr: without it every
# system-lib (iOS/Android) compile fails in compact_kv_copy), `rustup target add aarch64-apple-ios`, then
#   python -m mlc_llm package --package-config mlc-package-config.json --mlc-llm-source-dir <mlc-llm> --output dist
# with device "iphone" and the three models (Qwen3.5-0.8B-q4f32_1, Qwen3.5-4B-q4f16_1, gemma-4-E2B-it-q4f16_1),
# context_window_size 4096, prefill_chunk_size 512, bundle_weight false.
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
// Written by scripts/vendor-mlc.sh.
enum MLCVendored {
    static let commit = "$commit"
    static let tvm = "$tvm"
}
SWIFT
echo "== $out; now: MLC_ENABLED=YES xcodegen generate (add PIE_ENABLED=YES PIE_SWIFT_PACKAGE=... for pie too)"
