import Foundation

/// One request's raw timings, as the row sends them.
struct RequestTiming {
    var promptTokens: Int
    var outputTokens: Int
    /// From the request's send time (the batch start for concurrent shapes).
    var ttft: Double
    var latency: Double

    var json: J {
        .obj([("prompt_tokens", .int(promptTokens)), ("output_tokens", .int(outputTokens)),
              ("ttft_s", .num(ttft)), ("latency_s", .num(latency)), ("cached_prompt_tokens", .int(0))])
    }
}

/// A model loaded into an engine; load happens once per (engine, model).
protocol LoadedModel: AnyObject {
    var engineVersion: String { get }
    var backend: String { get }
    var config: [(String, J)] { get }
    /// Runs `concurrency` requests at once as real parallel sequences; nil when the engine cannot.
    var concurrencyUnsupportedReason: String? { get }
    /// True when the engine applies the chat template itself (pie's bench inferlet): it gets the user text only.
    var rendersTemplate: Bool { get }
    /// Size the engine for a workload (context, sequence slots). Not timed.
    func prepare(slots: Int, contextPerSlot: Int) throws
    /// Runs all `prompts` (full rendered text) with up to `concurrency` in flight, greedy, ignoring EOS,
    /// `decode` output tokens each, prompts cold. Results in prompt order.
    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming]
    func unload()
}

extension LoadedModel {
    var rendersTemplate: Bool { false }
}

protocol EngineAdapter {
    var id: EngineID { get }
    /// Non-nil when this build/engine cannot serve the model at all (becomes declared_unsupported).
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
