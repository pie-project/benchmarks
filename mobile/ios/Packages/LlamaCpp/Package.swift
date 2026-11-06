// swift-tools-version:5.9
// llama.cpp b11312, the official release XCFramework (the same pin as the Mac rows).
// That release ships ios-arm64 and macOS slices only. For an iOS Simulator test build, point
// LLAMA_XCFRAMEWORK at a local xcframework with a simulator slice (scripts/build-llama-sim.sh).

import Foundation
import PackageDescription

let local = ProcessInfo.processInfo.environment["LLAMA_XCFRAMEWORK"].flatMap { $0.isEmpty ? nil : $0 }

let llama: Target = local.map { .binaryTarget(name: "llama", path: $0) } ?? .binaryTarget(
    name: "llama",
    url: "https://github.com/ggml-org/llama.cpp/releases/download/b11312/llama-b11312-xcframework.zip",
    checksum: "beeffb82df39be0fc31a5d366bab437b32d457d2031f6ba96f151c211b09b9d3"
)

let package = Package(
    name: "LlamaCpp",
    platforms: [.iOS(.v16), .macOS(.v13)],
    products: [.library(name: "LlamaCpp", targets: ["llama"])],
    targets: [llama]
)
