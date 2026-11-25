// swift-tools-version:5.9

import PackageDescription

let package = Package(
    name: "LiteRtLm",
    platforms: [.iOS(.v16), .macOS(.v13)],
    products: [.library(name: "LiteRtLm", targets: ["LiteRtLm"])],
    targets: [
        .binaryTarget(
            name: "CLiteRTLM",
            url: "https://github.com/google-ai-edge/LiteRT-LM/releases/download/v0.19.1/CLiteRTLM.xcframework.zip",
            checksum: "21cf294b3dfdd9c8166b0f7934ed392d5c69c8bfa57cd1a20e341a7d16874017"
        ),
        .binaryTarget(
            name: "CLiteRTLM_mac",
            url: "https://github.com/google-ai-edge/LiteRT-LM/releases/download/v0.19.1/CLiteRTLM_mac.xcframework.zip",
            checksum: "cedd331e78e94bf98ca8f2f28aeb3d543e20277fcd51570c12deed6d49524fb6"
        ),
        .target(
            name: "LiteRtLm",
            dependencies: [
                .target(name: "CLiteRTLM", condition: .when(platforms: [.iOS])),
                .target(name: "CLiteRTLM_mac", condition: .when(platforms: [.macOS])),
            ]
        ),
    ]
)
