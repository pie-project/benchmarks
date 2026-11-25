import Foundation

#if canImport(MLXLLM)
import MLX
import MLXLLM
import MLXLMCommon
import Tokenizers

private struct HFTokenizer: MLXLMCommon.Tokenizer {
    let upstream: any Tokenizers.Tokenizer
    func encode(text: String, addSpecialTokens: Bool) -> [Int] { upstream.encode(text: text, addSpecialTokens: addSpecialTokens) }
    func decode(tokenIds: [Int], skipSpecialTokens: Bool) -> String { upstream.decode(tokens: tokenIds, skipSpecialTokens: skipSpecialTokens) }
    func convertTokenToId(_ token: String) -> Int? { upstream.convertTokenToId(token) }
    func convertIdToToken(_ id: Int) -> String? { upstream.convertIdToToken(id) }
    var bosToken: String? { upstream.bosToken }
    var eosToken: String? { upstream.eosToken }
    var unknownToken: String? { upstream.unknownToken }
    func applyChatTemplate(messages: [[String: any Sendable]], tools: [[String: any Sendable]]?, additionalContext: [String: any Sendable]?) throws -> [Int] {
        try upstream.applyChatTemplate(messages: messages, tools: tools, additionalContext: additionalContext)
    }
}

private struct HFTokenizerLoader: TokenizerLoader {
    func load(from directory: URL) async throws -> any MLXLMCommon.Tokenizer {
        HFTokenizer(upstream: try await AutoTokenizer.from(modelFolder: directory))
    }
}

struct MLXAdapter: EngineAdapter {
    let id = EngineID.mlxSwift
    static let version = "mlx-swift-lm 3.32.3 / mlx-swift 0.32.3"

    func unsupportedReason(_ m: ModelEntry) -> String? {
        #if targetEnvironment(simulator)
        return "MLX does not run on the iOS Simulator (needs the device GPU)"
        #else
        return nil
        #endif
    }

    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        let context = try await LLMModelFactory.shared.load(from: m.directory, using: HFTokenizerLoader())
        return MLXModel(context: context)
    }
}

final class MLXModel: LoadedModel, @unchecked Sendable {
    let engineVersion = MLXAdapter.version
    let backend = "metal"
    let concurrencyUnsupportedReason: String? = "serves one request at a time"
    private let context: ModelContext
    private let prefillStep = 2048

    init(context: consuming sending ModelContext) { self.context = context }

    var config: [(String, J)] {
        [("prefill_step_size", .int(prefillStep)), ("sampler", .str("argmax")), ("kv_cache", .str("default (unquantized)")),
         ("prompt", .str("tokenizer.encode(prefix+text+suffix, addSpecialTokens: false)"))]
    }

    func prepare(slots: Int, contextPerSlot: Int) throws {}

    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming] {
        try await Task.detached(priority: .userInitiated) {
            var out: [RequestTiming] = []
            for p in prompts { out.append(try self.one(p, decode: decode)) }
            return out
        }.value
    }

    private func one(_ prompt: String, decode: Int) throws -> RequestTiming {
        let sent = monotonic()
        let ids = context.tokenizer.encode(text: prompt, addSpecialTokens: false)
        let input = LMInput(tokens: MLXArray(ids.map(Int32.init)))
        var params = GenerateParameters(maxTokens: decode, temperature: 0)
        params.prefill.stepSize = prefillStep
        var it = try TokenIterator(input: input, model: context.model, parameters: params)
        var first = 0.0
        var n = 0
        while let _ = it.next() {
            if n == 0 { first = monotonic() }
            n += 1
        }
        let end = monotonic()
        MLX.Memory.clearCache()
        return RequestTiming(promptTokens: ids.count, outputTokens: n, ttft: first - sent, latency: end - sent)
    }

    func unload() { MLX.Memory.clearCache() }
}
#else
struct MLXAdapter: EngineAdapter {
    let id = EngineID.mlxSwift
    func unsupportedReason(_ m: ModelEntry) -> String? { "this build has no MLX Swift" }
    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        throw BenchError.message("this build has no MLX Swift")
    }
}
#endif
