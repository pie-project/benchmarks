import Accelerate
import Foundation
import llama

struct LlamaAdapter: EngineAdapter {
    let id = EngineID.llamacpp

    func unsupportedReason(_ m: ModelEntry) -> String? { nil }

    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        let path = m.directory.appending(path: m.file ?? "").path
        return try await Task.detached(priority: .userInitiated) { try LlamaModel(path: path) }.value
    }
}

final class LlamaModel: LoadedModel, @unchecked Sendable {
    static let tag = "b11312"
    private static let initOnce: Void = { llama_backend_init() }()

    let engineVersion = LlamaModel.tag
    let backend: String
    let concurrencyUnsupportedReason: String? = nil

    private let model: OpaquePointer
    private let vocab: OpaquePointer
    private var ctx: OpaquePointer?
    private var batch: llama_batch?
    private let nVocab: Int
    private let eog: [Int]
    private let gpuLayers: Int32
    private var slots = 1
    private var ctxPerSlot = 0
    private let nBatch: Int32 = 2048
    private let nUbatch: Int32 = 512

    var config: [(String, J)] {
        [("n_gpu_layers", .str(gpuLayers < 0 ? "all" : String(gpuLayers))), ("flash_attn", .str("on")),
         ("n_ctx", .int(slots * ctxPerSlot)), ("ctx_per_seq", .int(ctxPerSlot)), ("n_seq_max", .int(slots)),
         ("n_batch", .int(Int(nBatch))), ("n_ubatch", .int(Int(nUbatch))), ("sampler", .str("greedy argmax, EOG masked")),
         ("xcframework", .str("llama-\(LlamaModel.tag)-xcframework.zip"))]
    }

    init(path: String) throws {
        _ = LlamaModel.initOnce
        let cpu = ProcessInfo.processInfo.environment["PIEBENCH_LLAMA_CPU"] == "1"
        var mp = llama_model_default_params()
        mp.n_gpu_layers = cpu ? 0 : -1
        gpuLayers = mp.n_gpu_layers
        backend = cpu ? "cpu" : "metal"
        guard let m = llama_model_load_from_file(path, mp) else {
            throw BenchError.message("llama_model_load_from_file failed for \(URL(fileURLWithPath: path).lastPathComponent)")
        }
        model = m
        let v = llama_model_get_vocab(m)!
        vocab = v
        let n = Int(llama_vocab_n_tokens(v))
        nVocab = n
        eog = (0..<Int32(n)).filter { llama_vocab_is_eog(v, $0) }.map(Int.init)
    }

    func prepare(slots: Int, contextPerSlot: Int) throws {
        if ctx != nil && slots == self.slots && contextPerSlot == ctxPerSlot { return }
        if let c = ctx { llama_free(c); ctx = nil }
        if let b = batch { llama_batch_free(b); batch = nil }
        var cp = llama_context_default_params()
        cp.n_ctx = UInt32(slots * contextPerSlot)
        cp.n_batch = UInt32(nBatch)
        cp.n_ubatch = UInt32(nUbatch)
        cp.n_seq_max = UInt32(slots)
        cp.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED
        cp.no_perf = true
        guard let c = llama_init_from_model(model, cp) else {
            throw BenchError.message("llama_init_from_model failed (n_ctx \(slots * contextPerSlot), \(slots) seqs)")
        }
        ctx = c
        batch = llama_batch_init(nBatch + Int32(slots), 0, 1)
        self.slots = slots
        ctxPerSlot = contextPerSlot
    }

    func tokenize(_ text: String) -> [llama_token] {
        let utf8 = Array(text.utf8CString)
        var n = Int32(utf8.count + 8)
        var out = [llama_token](repeating: 0, count: Int(n))
        var got = llama_tokenize(vocab, utf8, Int32(utf8.count - 1), &out, n, false, true)
        if got < 0 {
            n = -got
            out = [llama_token](repeating: 0, count: Int(n))
            got = llama_tokenize(vocab, utf8, Int32(utf8.count - 1), &out, n, false, true)
        }
        return Array(out.prefix(Int(max(0, got))))
    }

    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming] {
        try await Task.detached(priority: .userInitiated) { try self.runSync(prompts: prompts, concurrency: concurrency, decode: decode) }.value
    }

    private struct Slot {
        let request: Int
        let tokens: [llama_token]
        var consumed = 0
        var generated = 0
        var last: llama_token = 0
        var logitIndex: Int32 = -1
        let sent: Double
        var first: Double = 0
    }

    private func runSync(prompts: [String], concurrency: Int, decode: Int) throws -> [RequestTiming] {
        guard let ctx, var batch else { throw BenchError.message("llama.cpp context not prepared") }
        let lanes = min(concurrency, slots)
        let mem = llama_get_memory(ctx)
        var queue = Array(prompts.indices)
        var active = [Slot?](repeating: nil, count: lanes)
        var results = [RequestTiming?](repeating: nil, count: prompts.count)

        while !queue.isEmpty || active.contains(where: { $0 != nil }) {
            for s in 0..<lanes where active[s] == nil && !queue.isEmpty {
                let r = queue.removeFirst()
                llama_memory_seq_rm(mem, llama_seq_id(s), -1, -1)
                let sent = monotonic()
                let toks = tokenize(prompts[r])
                if toks.count + decode > ctxPerSlot {
                    throw BenchError.message("prompt of \(toks.count) tokens + \(decode) does not fit a \(ctxPerSlot)-token sequence")
                }
                active[s] = Slot(request: r, tokens: toks, sent: sent)
            }

            batch.n_tokens = 0
            var budget = Int(nBatch)
            func add(_ tok: llama_token, _ pos: Int, _ seq: Int, _ logits: Bool) {
                let i = Int(batch.n_tokens)
                batch.token[i] = tok
                batch.pos[i] = llama_pos(pos)
                batch.n_seq_id[i] = 1
                batch.seq_id[i]![0] = llama_seq_id(seq)
                batch.logits[i] = logits ? 1 : 0
                batch.n_tokens += 1
            }
            for s in 0..<lanes {
                guard var slot = active[s] else { continue }
                slot.logitIndex = -1
                if slot.consumed == slot.tokens.count && slot.generated > 0 {
                    slot.logitIndex = batch.n_tokens
                    add(slot.last, slot.tokens.count + slot.generated - 1, s, true)
                    budget -= 1
                }
                active[s] = slot
            }
            for s in 0..<lanes {
                guard var slot = active[s], slot.consumed < slot.tokens.count, budget > 0 else { continue }
                let k = min(slot.tokens.count - slot.consumed, budget)
                for j in 0..<k {
                    let p = slot.consumed + j
                    let lastOfPrompt = p == slot.tokens.count - 1
                    if lastOfPrompt { slot.logitIndex = batch.n_tokens }
                    add(slot.tokens[p], p, s, lastOfPrompt)
                }
                slot.consumed += k
                budget -= k
                active[s] = slot
            }

            let rc = llama_decode(ctx, batch)
            if rc != 0 { throw BenchError.message("llama_decode returned \(rc)") }

            for s in 0..<lanes {
                guard var slot = active[s], slot.logitIndex >= 0 else { continue }
                let tok = argmax(llama_get_logits_ith(ctx, slot.logitIndex))
                let t = monotonic()
                if slot.generated == 0 { slot.first = t }
                slot.generated += 1
                slot.last = tok
                if slot.generated >= decode {
                    results[slot.request] = RequestTiming(promptTokens: slot.tokens.count, outputTokens: slot.generated,
                                                          ttft: slot.first - slot.sent, latency: t - slot.sent)
                    active[s] = nil
                } else {
                    active[s] = slot
                }
            }
        }
        self.batch = batch
        return results.map { $0! }
    }

    private func argmax(_ logits: UnsafeMutablePointer<Float>) -> llama_token {
        for e in eog { logits[e] = -.infinity }
        var maxV: Float = 0
        var idx: vDSP_Length = 0
        vDSP_maxvi(logits, 1, &maxV, &idx, vDSP_Length(nVocab))
        return llama_token(idx)
    }

    func unload() {
        if let b = batch { llama_batch_free(b); batch = nil }
        if let c = ctx { llama_free(c); ctx = nil }
        llama_model_free(model)
    }
}
