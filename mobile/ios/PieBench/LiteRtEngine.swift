import Foundation

#if canImport(LiteRtLm)
struct LiteRtAdapter: EngineAdapter {
    let id = EngineID.litert

    func unsupportedReason(_ m: ModelEntry) -> String? {
        #if targetEnvironment(simulator)
        return "LiteRT-LM's GPU backend needs the device"
        #else
        return nil
        #endif
    }

    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        let path = m.directory.appending(path: m.file ?? "").path(percentEncoded: false)
        let cache = URL.cachesDirectory.appending(path: "litert", directoryHint: .isDirectory).path(percentEncoded: false)
        return try await Task.detached(priority: .userInitiated) {
            LiteRtModel(core: try LiteRtCore(path: path, backend: "gpu", maxNumTokens: LiteRtModel.maxTokens, cacheDir: cache),
                        stripBos: m.model.hasPrefix("gemma"))
        }.value
    }
}

final class LiteRtModel: LoadedModel, @unchecked Sendable {
    static let maxTokens = 2048
    let engineVersion = LiteRtCore.version
    let backend = "metal"
    let concurrencyUnsupportedReason: String? = "serves one request at a time"
    private var core: LiteRtCore?
    private let stripBos: Bool

    init(core: LiteRtCore, stripBos: Bool) { self.core = core; self.stripBos = stripBos }

    var config: [(String, J)] {
        [("api", .str("LiteRT-LM C API: a Session per request, litert_lm_session_generate_content_stream (raw prompt text)")),
         ("backend", .str("GPU")), ("max_num_tokens", .int(LiteRtModel.maxTokens)),
         ("sampler", .str("top_k=1 top_p=1 temperature=0 (greedy)")), ("ignore_eos", .bool(false)),
         ("ignore_eos_note", .str("LiteRT-LM has no ignore_eos: decode is cancelled after `decode` stream chunks, a model that stops early records its real count")),
         ("output_tokens_source", .str("stream chunks (one per decode step)")),
         ("prompt_tokens_source", .str("harness tokenizer count from workloads.json (a LiteRT-LM Session does not report it)")),
         ("bos", .str(stripBos ? "leading '<bos>' text removed, the session adds the model's start token itself" : "none in template")),
         ("session", .str("fresh session per request, created before the send timestamp"))]
    }

    func prepare(slots: Int, contextPerSlot: Int) throws {}

    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming] {
        guard let core else { throw BenchError.message("LiteRT-LM model is unloaded") }
        return try await Task.detached(priority: .userInitiated) {
            try prompts.map { p0 in
                let p = self.stripBos && p0.hasPrefix("<bos>") ? String(p0.dropFirst(5)) : p0
                let s = try core.generate(p, want: decode, clock: monotonic)
                return RequestTiming(promptTokens: -1, outputTokens: s.tokens, ttft: s.first - s.sent, latency: s.last - s.sent)
            }
        }.value
    }

    func unload() { core = nil }
}
#else
struct LiteRtAdapter: EngineAdapter {
    let id = EngineID.litert
    func unsupportedReason(_ m: ModelEntry) -> String? { "this build has no LiteRT-LM" }
    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        throw BenchError.message("this build has no LiteRT-LM")
    }
}
#endif
