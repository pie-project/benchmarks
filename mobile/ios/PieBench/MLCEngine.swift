import Foundation

#if PIEBENCH_MLC && canImport(MLCEngineObjC)
import MLCEngineObjC

struct MLCAdapter: EngineAdapter {
    let id = EngineID.mlc
    static var version: String { "mlc-llm \(MLCVendored.commit.prefix(12)) / tvm \(MLCVendored.tvm.prefix(12))" }

    static func modelLib(_ m: ModelEntry) -> String? {
        guard let url = Bundle.main.url(forResource: "mlc-app-config", withExtension: "json"),
              let d = try? Data(contentsOf: url),
              let o = try? JSONSerialization.jsonObject(with: d) as? [String: Any],
              let list = o["model_list"] as? [[String: Any]] else { return nil }
        let id = m.repo.split(separator: "/").last.map(String.init) ?? ""
        return list.first { ($0["model_id"] as? String) == id }?["model_lib"] as? String
    }

    func unsupportedReason(_ m: ModelEntry) -> String? {
        MLCAdapter.modelLib(m) == nil ? "no compiled MLC model lib for \(m.repo) in this build" : nil
    }

    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        try MLCAdapter.passThroughTemplate(m.directory)
        let lib = MLCAdapter.modelLib(m)!
        let engine = MLCModel(lib: lib)
        try await engine.reload(path: m.directory.path)
        return engine
    }

    static func passThroughTemplate(_ dir: URL) throws {
        let url = dir.appending(path: "mlc-chat-config.json")
        let data = try Data(contentsOf: url)
        guard var cfg = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw BenchError.message("mlc-chat-config.json is not an object")
        }
        let old = cfg["conv_template"] as? [String: Any] ?? [:]
        if old["name"] as? String == "pie-bench-raw" { return }
        try data.write(to: dir.appending(path: "mlc-chat-config.original.json"))
        cfg["conv_template"] = [
            "name": "pie-bench-raw", "system_template": "{system_message}", "system_message": "",
            "system_prefix_token_ids": NSNull(), "add_role_after_system_message": false,
            "roles": ["user": "", "assistant": ""],
            "role_templates": ["user": "{user_message}", "assistant": "{assistant_message}", "tool": "{tool_message}"],
            "messages": [], "seps": [""], "role_content_sep": "", "role_empty_sep": "", "stop_str": [],
            "stop_token_ids": old["stop_token_ids"] ?? [], "function_string": "", "use_function_calling": false,
        ] as [String: Any]
        try JSONSerialization.data(withJSONObject: cfg, options: [.prettyPrinted]).write(to: url)
    }
}

final class MLCModel: LoadedModel, @unchecked Sendable {
    let engineVersion = MLCAdapter.version
    let backend = "metal"
    let concurrencyUnsupportedReason: String? = nil
    private let lib: String
    private let ffi = JSONFFIEngine()
    private var threads: [Thread] = []
    private let lock = NSLock()
    private var waiting: [String: (String) -> Void] = [:]
    private let maxSeq = 4

    var config: [(String, J)] {
        [("model_lib", .str(lib)), ("mode", .str("local")), ("max_num_sequence", .int(maxSeq)),
         ("max_total_seq_length", .int(4096)), ("prefill_chunk_size", .int(512)),
         ("conv_template", .str("pass-through (prompt pre-rendered)")), ("ignore_eos", .bool(true))]
    }

    init(lib: String) {
        self.lib = lib
        ffi.initBackgroundEngine { [weak self] s in self?.deliver(s) }
        let ffi = self.ffi
        let loop = Thread { ffi.runBackgroundLoop() }
        loop.qualityOfService = .userInteractive
        let back = Thread { ffi.runBackgroundStreamBackLoop() }
        threads = [loop, back]
        loop.start(); back.start()
    }

    func reload(path: String) async throws {
        let cfg: [String: Any] = ["model": path, "model_lib": "system://\(lib)", "mode": "local",
                                  "max_num_sequence": maxSeq, "max_total_seq_length": 4096, "prefill_chunk_size": 512]
        let s = String(decoding: try JSONSerialization.data(withJSONObject: cfg), as: UTF8.self)
        try await Task.detached { self.ffi.reload(s) }.value
    }

    private func deliver(_ s: String?) {
        guard let s, let d = s.data(using: .utf8), let arr = try? JSONSerialization.jsonObject(with: d) as? [[String: Any]] else { return }
        for chunk in arr {
            guard let id = chunk["id"] as? String else { continue }
            lock.lock(); let h = waiting[id]; lock.unlock()
            if let h, let one = try? JSONSerialization.data(withJSONObject: chunk) { h(String(decoding: one, as: UTF8.self)) }
        }
    }

    func prepare(slots: Int, contextPerSlot: Int) throws {}

    private func request(_ prompt: String, decode: Int) async throws -> RequestTiming {
        let id = UUID().uuidString
        let body: [String: Any] = [
            "messages": [["role": "user", "content": prompt]], "max_tokens": decode, "temperature": 0, "top_p": 1,
            "stream": true, "stream_options": ["include_usage": true], "debug_config": ["ignore_eos": true],
        ]
        let json = String(decoding: try JSONSerialization.data(withJSONObject: body), as: UTF8.self)
        return try await withCheckedThrowingContinuation { (c: CheckedContinuation<RequestTiming, Error>) in
            var first = 0.0
            var finished = false
            let sent = monotonic()
            lock.lock()
            waiting[id] = { [weak self] text in
                guard !finished, let o = J.parse(text) else { return }
                if first == 0, let ch = o["choices"] as? [[String: Any]], !ch.isEmpty { first = monotonic() }
                if let u = o["usage"] as? [String: Any] {
                    finished = true
                    let end = monotonic()
                    self?.lock.lock(); self?.waiting[id] = nil; self?.lock.unlock()
                    c.resume(returning: RequestTiming(promptTokens: (u["prompt_tokens"] as? Int) ?? 0,
                                                      outputTokens: (u["completion_tokens"] as? Int) ?? 0,
                                                      ttft: (first > 0 ? first : end) - sent, latency: end - sent))
                }
            }
            lock.unlock()
            ffi.chatCompletion(json, requestID: id)
        }
    }

    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming] {
        var results = [RequestTiming?](repeating: nil, count: prompts.count)
        var offset = 0
        while offset < prompts.count {
            let wave = Array(offset..<min(offset + concurrency, prompts.count))
            try await withThrowingTaskGroup(of: (Int, RequestTiming).self) { g in
                for i in wave { g.addTask { (i, try await self.request(prompts[i], decode: decode)) } }
                for try await (i, r) in g { results[i] = r }
            }
            offset += wave.count
        }
        return results.map { $0! }
    }

    func unload() {
        ffi.unload()
        ffi.exitBackgroundLoop()
    }
}
#else
enum MLCBuild {
    #if targetEnvironment(simulator)
    static let reason = "MLC LLM's iOS runtime and model libs are built for devices only (no simulator build)"
    #else
    static let reason = "MLC LLM is not built into this app (scripts/vendor-mlc.sh + MLC_ENABLED=YES xcodegen generate)"
    #endif
}

struct MLCAdapter: EngineAdapter {
    let id = EngineID.mlc
    func unsupportedReason(_ m: ModelEntry) -> String? { MLCBuild.reason }
    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        throw BenchError.message(MLCBuild.reason)
    }
}
#endif
