import Foundation

/// Pie commit this build's PieServerCore came from (scripts/build-pie.sh writes PieBuild.swift).
enum PieInfo {
    static var commit: String? { PieBuild.commit }
    /// The pie main commit this app's pie path was built and checked against; reported by rows of a build without pie.
    static let evaluated = "a6547509432d48c76e258bfefbb85bd58984f8e4"
}

#if canImport(PieServer)
import PieServer

/// Pie in-process (PieServer, Metal), driven through the harness's bench inferlet
/// (examples/text-completion-bench) as the Mac rows are. Each request is its own inferlet process;
/// concurrent shapes run `concurrency` processes at once, which pie batches into shared forwards.
struct PieAdapter: EngineAdapter {
    let id = EngineID.pie
    /// The runtime boots once per process (PieServer.shutdown is final).
    @MainActor static var booted: String?
    /// The model `booted` serves, kept for a second run of it in the same launch.
    @MainActor static var served: PieModel?

    /// The bundled bench inferlet (PIEBENCH_PIE_WASM overrides it for the Mac test harness).
    static var wasm: URL? {
        ProcessInfo.processInfo.environment["PIEBENCH_PIE_WASM"].map { URL(fileURLWithPath: $0) }
            ?? Bundle.main.url(forResource: "text-completion-bench", withExtension: "wasm")
    }

    func unsupportedReason(_ m: ModelEntry) -> String? {
        if PieAdapter.wasm == nil {
            return "the bench inferlet (text-completion-bench.wasm) is not in this build"
        }
        return nil
    }

    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        if let other = await PieAdapter.booted {
            // the same model again in this launch: the server it booted is still up
            if other == m.artifact, let served = await PieAdapter.served { return served }
            throw BenchError.message("pie boots once per app process and already served \(other); relaunch the app to run \(m.artifact)")
        }
        guard let file = Downloader.pieFile(m) else { throw BenchError.message("no .metal.zt for \(m.artifact)") }
        await MainActor.run { PieAdapter.booted = m.artifact }
        var cfg = PieServer.Configuration()
        // A window-ring model (Gemma 4) runs a prompt in one fire: room for the longest prompt this contract sends, its chat
        // template included (512 refused raw's ~550 tokens), as the next power of two.
        let longest = (contract.workloads.map(\.prefill).max() ?? 0) + 128
        cfg.maxForwardTokens = max(512, 1 << Int(ceil(log2(Double(longest)))))
        cfg.maxForwardRequests = 4
        cfg.maxConcurrentProcesses = 8
        // PieServer's default of 16 state slots starves Qwen3.5's recurrent layers ("state pool starved"); 256 is pie's own default
        // (64 starved Qwen3.5-4B: 32 slots a request).
        cfg.maxStateSlots = 256
        // Test knob (the Mac harness shares its GPU with other work): PIEBENCH_PIE_MEMORY_SHARE overrides the 0.6 share.
        if let v = ProcessInfo.processInfo.environment["PIEBENCH_PIE_MEMORY_SHARE"].flatMap(Double.init) { cfg.deviceMemoryShare = v }
        let server = try await PieServer.start(model: file, configuration: cfg)
        let client = try await server.connect()
        let wasm = PieAdapter.wasm!
        let name = try await server.install(contentsOf: wasm)
        let model = PieModel(server: server, client: client, inferlet: name, system: contract.system, cfg: cfg)
        await MainActor.run { PieAdapter.served = model }
        return model
    }
}

final class PieModel: LoadedModel, @unchecked Sendable {
    let server: PieServer
    let client: PieClient
    let inferlet: String
    let system: String
    let cfg: PieServer.Configuration
    let backend = "metal"
    let concurrencyUnsupportedReason: String? = nil
    /// The inferlet renders system + user + the no-think cue with pie's own template.
    let rendersTemplate = true
    var engineVersion: String { PieInfo.commit ?? PieInfo.evaluated }

    init(server: PieServer, client: PieClient, inferlet: String, system: String, cfg: PieServer.Configuration) {
        self.server = server; self.client = client; self.inferlet = inferlet; self.system = system; self.cfg = cfg
    }

    var config: [(String, J)] {
        [("pie_commit", .opt(PieInfo.commit)), ("deployment", .str(server.summary.deployment)),
         ("inferlet", .str(inferlet)), ("device_memory_share", .num(cfg.deviceMemoryShare)),
         ("max_forward_tokens", .int(cfg.maxForwardTokens)), ("max_forward_requests", .int(cfg.maxForwardRequests)),
         ("max_state_slots", .int(cfg.maxStateSlots)),
         ("kv_pages", .int(server.summary.kvPages)), ("kv_page_size", .int(server.summary.kvPageSize)),
         ("prompt", .str("inferlet chat::system_user(system, text) + cue (no_think)")),
         ("ttft_origin", .str("start signal to the ready inferlet"))]
    }

    func prepare(slots: Int, contextPerSlot: Int) throws {}

    struct Input: Encodable {
        let prompt: String
        let system: String
        let max_tokens: Int
        let temperature: Double = 0
        let ignore_eos = true
        let no_think = true
        let return_text = false
        let report_timing = true
        let wait_for_start = true
    }

    struct Output: Decodable {
        let num_prompt_tokens: Int
        let num_output_tokens: Int
    }

    /// One request: launch, wait for "ready", stamp the send, "start", first token at "t0".
    private func request(_ text: String, decode: Int, startGate: @escaping () async -> Void) async throws -> RequestTiming {
        let p = try await client.launch(inferlet, json: JSONEncoder().encode(Input(prompt: text, system: system, max_tokens: decode)))
        var sent = 0.0, first = 0.0
        for try await ev in p.events {
            switch ev {
            case .message("ready"):
                await startGate()
                sent = monotonic()
                try await p.send("start")
            case .message("t0"):
                first = monotonic()
            case .returned(let json):
                let end = monotonic()
                let o = try JSONDecoder().decode(Output.self, from: Data(json.utf8))
                return RequestTiming(promptTokens: o.num_prompt_tokens, outputTokens: o.num_output_tokens,
                                     ttft: (first > 0 ? first : end) - sent, latency: end - sent)
            default: break
            }
        }
        throw BenchError.message("inferlet ended without a result")
    }

    func run(prompts: [String], concurrency: Int, decode: Int) async throws -> [RequestTiming] {
        // A concurrent wave starts together: every process of the wave is ready before any is released.
        var results = [RequestTiming?](repeating: nil, count: prompts.count)
        var offset = 0
        while offset < prompts.count {
            let wave = Array(offset..<min(offset + concurrency, prompts.count))
            let gate = Gate(count: wave.count)
            try await withThrowingTaskGroup(of: (Int, RequestTiming).self) { g in
                for i in wave {
                    g.addTask { (i, try await self.request(prompts[i], decode: decode) { await gate.arrive() }) }
                }
                for try await (i, r) in g { results[i] = r }
            }
            offset += wave.count
        }
        return results.map { $0! }
    }

    func unload() {}
}

actor Gate {
    private var waiting: [CheckedContinuation<Void, Never>] = []
    private let count: Int
    init(count: Int) { self.count = count }
    func arrive() async {
        await withCheckedContinuation { c in
            waiting.append(c)
            if waiting.count >= count { waiting.forEach { $0.resume() }; waiting.removeAll() }
        }
    }
}
#else
struct PieAdapter: EngineAdapter {
    @MainActor static var booted: String?
    let id = EngineID.pie
    func unsupportedReason(_ m: ModelEntry) -> String? { PieBuild.unavailable }
    func load(_ m: ModelEntry, checkpoint: Checkpoint, contract: Contract) async throws -> LoadedModel {
        throw BenchError.message(PieBuild.unavailable)
    }
}
#endif
