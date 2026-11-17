import Foundation
#if canImport(UIKit)
import UIKit
#endif

extension EngineID {
    /// What a row reports when the engine never loaded.
    var staticVersion: String {
        switch self {
        case .llamacpp: return LlamaModel.tag
        case .mlxSwift: return "mlx-swift-lm 3.32.3 / mlx-swift 0.32.3"
        case .mlc: return "not built"
        case .pie: return PieInfo.commit ?? PieInfo.evaluated
        case .litert: return "0.19.1"
        }
    }
}

/// A row as the results table shows it (display only; the server computes the real metrics).
struct RowSummary: Identifiable {
    let id = UUID()
    let engine: String
    let artifact: String
    let workload: String
    let status: String
    let error: String?
    let decodeTokS: Double?
    let prefillTokS: Double?
    let ttftS: Double?
    let peakGiB: Double?

    init(_ o: [String: Any]) {
        engine = o["engine"] as? String ?? "?"
        artifact = o["artifact"] as? String ?? "?"
        workload = o["workload"] as? String ?? "?"
        status = o["status"] as? String ?? "?"
        error = o["error"] as? String
        let rounds = o["rounds"] as? [[String: Any]] ?? []
        let reqs = rounds.flatMap { $0["requests"] as? [[String: Any]] ?? [] }
        func d(_ r: [String: Any], _ k: String) -> Double { (r[k] as? NSNumber)?.doubleValue ?? 0 }
        let dec = reqs.compactMap { r -> Double? in
            let n = d(r, "output_tokens"), span = d(r, "latency_s") - d(r, "ttft_s")
            return n > 1 && span > 0 ? (n - 1) / span : nil
        }
        let pre = reqs.compactMap { r -> Double? in d(r, "ttft_s") > 0 ? d(r, "prompt_tokens") / d(r, "ttft_s") : nil }
        let ttft = reqs.map { d($0, "ttft_s") }.sorted()
        func median(_ a: [Double]) -> Double? { a.isEmpty ? nil : a.sorted()[a.count / 2] }
        decodeTokS = median(dec)
        prefillTokS = median(pre)
        ttftS = median(ttft)
        peakGiB = rounds.compactMap { ($0["peak_mem_gib"] as? NSNumber)?.doubleValue }.max()
    }
}

struct RunPlan {
    var models: [ModelEntry]
    var workloads: [String]
    var tag: String?
}

@MainActor
final class Runner: ObservableObject {
    @Published var log: [String] = []
    @Published var rows: [RowSummary] = []
    @Published var running = false
    @Published var status = "idle"
    @Published var downloadProgress: Double?

    let contract: Contract?
    let loadError: String?
    private var task: Task<Void, Never>?

    init() {
        do { contract = try Contract.load(); loadError = nil } catch { contract = nil; loadError = error.localizedDescription }
        try? FileManager.default.createDirectory(at: Storage.importFolder, withIntermediateDirectories: true)
        recoverCrashedCell()
        reloadRows()
    }

    func say(_ s: String) {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        let line = "\(f.string(from: Date())) \(s)"
        log.append(line)
        if log.count > 500 { log.removeFirst(log.count - 500) }
        print("[PieBench] \(s)")
    }

    func reloadRows() {
        guard let text = try? String(contentsOf: Storage.records, encoding: .utf8) else { rows = []; return }
        rows = text.split(separator: "\n").compactMap { J.parse(String($0)) }.map(RowSummary.init)
    }

    // MARK: - rows

    static let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    static func runID(for models: [ModelEntry]) -> String {
        let slugs = Set(models.map(\.model))
        let slug = slugs.count == 1 ? slugs.first! : "multi"
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone(identifier: "UTC")
        f.dateFormat = "yyyyMMdd'T'HHmmss"
        return "phone-\(slug)-\(f.string(from: Date()))-\(String(format: "%04x", UInt16.random(in: 0...UInt16.max)))"
    }

    struct Cell {
        let runID: String
        let tag: String?
        let model: ModelEntry
        let workload: String
        let started: Date
        let thermalStart: String
        var engineVersion: String
        var backend: String
        var config: [(String, J)]
        var checkpoint: Checkpoint?
        var loadS: Double
    }

    func row(_ c: Cell, status: String, errorClass: String? = nil, error: String? = nil, rounds: [J] = []) -> J {
        let checkpoint = c.checkpoint ?? Checkpoint(repo: c.model.repo, file: c.model.file, revision: nil, bytes: 0)
        return .obj([
            ("schema", .str("pie-evals-phone/1")), ("run_id", .str(c.runID)), ("tag", .opt(c.tag)),
            ("started_at", .str(Self.iso.string(from: c.started))), ("duration_s", .num(Date().timeIntervalSince(c.started))),
            ("app", .obj([("version", .str(AppInfo.version)), ("harness_commit", .opt(contract?.harness_commit)), ("platform", .str("ios"))])),
            ("device", DeviceInfo.json(thermalStart: c.thermalStart, thermalEnd: DeviceInfo.thermal)),
            ("engine", .str(c.model.engine.rawValue)), ("engine_version", .str(c.engineVersion)), ("engine_backend", .str(c.backend)),
            ("engine_config", .obj(c.config)), ("artifact", .str(c.model.artifact)), ("checkpoint", checkpoint.json),
            ("workload", .str(c.workload)), ("status", .str(status)), ("error_class", .opt(errorClass)), ("error", .opt(error)),
            ("load_s", .num(c.loadS)), ("rounds", .arr(rounds)),
        ])
    }

    func emit(_ row: J) {
        let line = row.text + "\n"
        if let h = try? FileHandle(forWritingTo: Storage.records) {
            h.seekToEndOfFile(); h.write(Data(line.utf8)); try? h.close()
        } else {
            try? Data(line.utf8).write(to: Storage.records)
        }
        if let o = J.parse(row.text) { rows.append(RowSummary(o)) }
    }

    // MARK: - crash recovery

    struct Marker: Codable {
        var runID: String; var tag: String?; var modelID: String; var workload: String
        var started: Date; var thermalStart: String; var loadS: Double; var engineVersion: String; var backend: String
    }

    func mark(_ c: Cell?) {
        guard let c else { try? FileManager.default.removeItem(at: Storage.inProgress); return }
        let m = Marker(runID: c.runID, tag: c.tag, modelID: c.model.id, workload: c.workload, started: c.started,
                       thermalStart: c.thermalStart, loadS: c.loadS, engineVersion: c.engineVersion, backend: c.backend)
        try? JSONEncoder().encode(m).write(to: Storage.inProgress)
    }

    /// The app died inside a cell (jetsam or a crash): that cell still gets its row.
    func recoverCrashedCell() {
        guard let d = try? Data(contentsOf: Storage.inProgress), let m = try? JSONDecoder().decode(Marker.self, from: d),
              let model = ModelEntry.all.first(where: { $0.id == m.modelID }) else { return }
        try? FileManager.default.removeItem(at: Storage.inProgress)
        let c = Cell(runID: m.runID, tag: m.tag, model: model, workload: m.workload, started: m.started, thermalStart: m.thermalStart,
                     engineVersion: m.engineVersion, backend: m.backend, config: [], checkpoint: Downloader.present(model), loadS: m.loadS)
        var r = row(c, status: "fail", errorClass: "crash", error: "the app was terminated during this cell (iOS memory limit or a crash)")
        if case .obj(var kv) = r, let i = kv.firstIndex(where: { $0.0 == "duration_s" }) { kv[i].1 = .null; r = .obj(kv) }
        emit(r)
        say("recovered a cell the app died in: \(model.artifact) \(m.workload)")
    }

    // MARK: - run

    func start(_ plan: RunPlan, then: (@MainActor () async -> Void)? = nil) {
        guard !running else { return }
        task = Task { [weak self] in
            await self?.execute(plan)
            await then?()
        }
    }

    func stop() { task?.cancel(); say("stopping after the current request") }

    private func execute(_ plan: RunPlan) async {
        guard let contract else { say("no workloads.json: \(loadError ?? "")"); return }
        running = true
        Self.keepAwake(true)
        defer { running = false; Self.keepAwake(false); status = "idle"; downloadProgress = nil }

        // records.jsonl keeps every run (each row carries its run id), so a run never loses the one before it.
        let fm = FileManager.default
        if !fm.fileExists(atPath: Storage.records.path) { fm.createFile(atPath: Storage.records.path, contents: nil) }
        rows = []
        let runID = Self.runID(for: plan.models)
        say("run \(runID): \(plan.models.count) model(s) x \(plan.workloads.count) workload(s)")
        let workloads = plan.workloads.compactMap { contract.workload($0) }

        for m in plan.models {
            if Task.isCancelled { break }
            await runModel(m, workloads: workloads, contract: contract, runID: runID, tag: plan.tag)
        }
        say("done: \(Storage.records.lastPathComponent) has \(rows.count) row(s)")
    }

    private func runModel(_ m: ModelEntry, workloads: [Contract.Workload], contract: Contract, runID: String, tag: String?) async {
        let adapter = Engines.adapter(m.engine)
        let started = Date()
        func cell(_ w: String, _ s: Date = started, thermal: String = DeviceInfo.thermal) -> Cell {
            Cell(runID: runID, tag: tag, model: m, workload: w, started: s, thermalStart: thermal, engineVersion: m.engine.staticVersion,
                 backend: m.engine == .llamacpp && ProcessInfo.processInfo.environment["PIEBENCH_LLAMA_CPU"] == "1" ? "cpu" : "metal", config: [], checkpoint: nil, loadS: 0)
        }
        status = "\(m.engine.label) \(m.artifact)"
        if let reason = adapter.unsupportedReason(m) {
            say("\(m.artifact) [\(m.engine.rawValue)]: declared_unsupported: \(reason)")
            for w in workloads { emit(row(cell(w.id), status: "declared_unsupported", error: reason)) }
            return
        }
        // a pie server the cell before unloaded gives its memory back before this cell measures what it has
        await PieAdapter.settle()
        // Too big for what iOS lets this app have: fail without loading (or downloading).
        let avail = DeviceInfo.availableBytes
        let need = Int64(Double(m.bytes) * 1.1) + 300 << 20
        if avail > 0 && need > avail {
            let msg = String(format: "needs ~%.2f GiB, iOS allows this app %.2f GiB now", Double(need) / 1_073_741_824, Double(avail) / 1_073_741_824)
            say("\(m.artifact): doesnt_fit: \(msg)")
            for w in workloads { emit(row(cell(w.id), status: "fail", errorClass: "doesnt_fit", error: msg)) }
            return
        }
        let checkpoint: Checkpoint
        do {
            checkpoint = try await Downloader.ensure(m, log: { [weak self] s in Task { @MainActor in self?.say(s) } },
                                                     progress: { [weak self] p in Task { @MainActor in self?.downloadProgress = p } })
            downloadProgress = nil
        } catch {
            downloadProgress = nil
            say("\(m.artifact): download failed: \(error.localizedDescription)")
            for w in workloads { emit(row(cell(w.id), status: "fail", errorClass: "load_fail", error: "download: \(error.localizedDescription)")) }
            return
        }

        say("load \(m.artifact) (\(m.engine.label))")
        let loadStart = monotonic()
        let loaded: LoadedModel
        var base = cell("")
        base.checkpoint = checkpoint
        do {
            // A load that kills the app is recorded on the next launch.
            mark(base)
            loaded = try await adapter.load(m, checkpoint: checkpoint, contract: contract)
            mark(nil)
        } catch {
            mark(nil)
            say("\(m.artifact): load failed: \(error.localizedDescription)")
            for w in workloads {
                var c = cell(w.id); c.checkpoint = checkpoint; c.loadS = monotonic() - loadStart
                emit(row(c, status: "fail", errorClass: "load_fail", error: error.localizedDescription))
            }
            return
        }
        let loadS = monotonic() - loadStart
        say(String(format: "loaded in %.2fs (%@, %@)", loadS, loaded.backend, loaded.engineVersion))
        defer { loaded.unload() }

        for w in workloads {
            if Task.isCancelled { break }
            var c = cell(w.id, Date(), thermal: DeviceInfo.thermal)
            c.checkpoint = checkpoint; c.loadS = loadS
            c.engineVersion = loaded.engineVersion; c.backend = loaded.backend; c.config = loaded.config
            if w.concurrency > 1, let reason = loaded.concurrencyUnsupportedReason {
                say("\(w.id): declared_unsupported: \(reason)")
                emit(row(c, status: "declared_unsupported", error: reason))
                continue
            }
            let template = contract.templates[m.model]
            // The rendered prompt (prefix + text + suffix), or just the text for an engine that templates itself.
            let prefix = loaded.rendersTemplate ? "" : template?.prefix ?? "", suffix = loaded.rendersTemplate ? "" : template?.suffix ?? ""
            let maxPrompt = template?.prompt_tokens[w.id]?.flatMap { $0 }.max() ?? Int(Double(w.prefill) * 1.2)
            let perSlot = ((maxPrompt + w.decode + 16 + 255) / 256) * 256
            var rounds: [J] = []
            mark(c)
            do {
                try loaded.prepare(slots: w.concurrency, contextPerSlot: perSlot)
                c.config = loaded.config
                for r in 0..<contract.rounds {
                    try Task.checkCancellation()
                    let spec = w.rounds[r]
                    status = "\(m.artifact) \(w.id) round \(r + 1)/\(contract.rounds)"
                    let sampler = MemorySampler()
                    sampler.start()
                    _ = try await loaded.run(prompts: spec.warmup.map { prefix + $0 + suffix }, concurrency: w.concurrency, decode: w.decode)
                    let t0 = monotonic()
                    var res = try await loaded.run(prompts: spec.measured.map { prefix + $0 + suffix }, concurrency: w.concurrency, decode: w.decode)
                    let wall = monotonic() - t0
                    let peak = sampler.stop()
                    let expect = template?.prompt_tokens[w.id]?[r]
                    // LiteRT-LM reports no prompt count (-1): the harness count stands in, as on Android
                    if let expect, expect.count == res.count { for i in res.indices where res[i].promptTokens < 0 { res[i].promptTokens = expect[i] } }
                    rounds.append(.obj([("wall_s", .num(wall)), ("peak_mem_gib", .num(peak)), ("requests", .arr(res.map(\.json)))]))
                    let got = res.map(\.promptTokens)
                    say(String(format: "%@ r%d: wall %.2fs peak %.2f GiB prompt %@%@", w.id, r + 1, wall, peak, "\(got.prefix(4))",
                               expect.map { $0 == got ? " (= harness)" : " (harness \($0.prefix(4)))" } ?? ""))
                }
                mark(nil)
                emit(row(c, status: "pass", rounds: rounds))
            } catch is CancellationError {
                mark(nil)  // stopped by the user: no row for a cell that did not finish
                break
            } catch {
                mark(nil)
                say("\(w.id): failed: \(error.localizedDescription)")
                emit(row(c, status: "fail", errorClass: "crash", error: error.localizedDescription, rounds: rounds))
            }
        }
    }
}

extension Runner {
    /// A run may take an hour: the screen stays on.
    static func keepAwake(_ on: Bool) {
        #if canImport(UIKit)
        UIApplication.shared.isIdleTimerDisabled = on
        #endif
    }
}

enum AppInfo {
    static var version: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0.1.0" }
}
