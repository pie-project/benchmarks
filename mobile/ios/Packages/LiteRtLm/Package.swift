// swift-tools-version:5.9

import PackageDescription

let package = Package(
    name: "LiteRtLm",
    platforms: [.iOS(.v16)],
    products: [.library(name: "LiteRtLm", targets: ["LiteRtLm"])],
    targets: [
        .binaryTarget(
            name: "CLiteRTLM",
            url: "https://github.com/google-ai-edge/LiteRT-LM/releases/download/v0.19.1/CLiteRTLM.xcframework.zip",
            checksum: "21cf294b3dfdd9c8166b0f7934ed392d5c69c8bfa57cd1a20e341a7d16874017"
        ),
        .target(
            name: "LiteRtLm",
            dependencies: ["CLiteRTLM"]
        ),
    ]
)
