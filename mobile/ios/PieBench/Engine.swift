import Foundation

struct RequestTiming {
    var promptTokens: Int
    var outputTokens: Int
    var ttft: Double
    var latency: Double

    var json: J {
        .obj([("prompt_tokens", .int(promptTokens)), ("output_tokens", .int(outputTokens)),
              ("ttft_s", .num(ttft)), ("latency_s", .num(latency)), ("cached_prompt_tokens", .int(0))])
    }
}

protocol LoadedModel: AnyObject {
    var engineVersion: String { get }
    var backend: String { get }
    var config: [(String, J)] { get }
    var concurrencyUnsupportedReason: String? { get }
    var rendersTemplate: Bool { get }
    func prepare(slots: Int, contextPerSlot: Int) throws
    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming]
    func unload()
}

extension LoadedModel {
    var rendersTemplate: Bool { false }
}

protocol EngineAdapter {
    var id: EngineID { get }
    func unsupportedReason(_ m: ModelEntry) -> String?
    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel
}

enum Engines {
    static func adapter(_ id: EngineID) -> EngineAdapter {
        switch id {
        case .llamacpp: return LlamaAdapter()
        case .mlxSwift: return MLXAdapter()
        case .mlc: return MLCAdapter()
        case .pie: return PieAdapter()
        case .litert: return LiteRtAdapter()
        }
    }
}

let monotonic: () -> Double = {
    var t = timespec()
    clock_gettime(CLOCK_MONOTONIC_RAW, &t)
    return Double(t.tv_sec) + Double(t.tv_nsec) / 1e9
}
