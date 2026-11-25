// swift-tools-version:5.9

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
