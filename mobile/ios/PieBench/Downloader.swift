import Foundation

/// What was downloaded for a model, kept next to it.
struct Checkpoint: Codable {
    var repo: String
    var file: String?
    var revision: String?
    var bytes: Int64
    var imported: Bool = false

    var json: J {
        .obj([("repo", .str(repo)), ("file", .opt(file)), ("revision", .opt(revision)), ("bytes", .int(Int(bytes)))])
    }

    static func read(_ dir: URL) -> Checkpoint? {
        guard let d = try? Data(contentsOf: dir.appending(path: ".checkpoint.json")) else { return nil }
        return try? JSONDecoder().decode(Checkpoint.self, from: d)
    }

    func write(_ dir: URL) throws {
        try JSONEncoder().encode(self).write(to: dir.appending(path: ".checkpoint.json"))
    }
}

enum Downloader {
    struct RepoInfo: Decodable {
        struct Sibling: Decodable { let rfilename: String; let size: Int64? }
        let sha: String
        let siblings: [Sibling]
    }

    /// Files a repo snapshot needs on the phone (weights, configs, tokenizer); images/docs skipped.
    static func wanted(_ name: String) -> Bool {
        if name.hasPrefix(".") || name.hasSuffix(".md") || name.hasSuffix(".png") || name.hasSuffix(".jpg") { return false }
        return true
    }

    static func repoInfo(_ repo: String) async throws -> RepoInfo {
        let url = URL(string: "https://huggingface.co/api/models/\(repo)/revision/main?blobs=true")!
        let (data, resp) = try await URLSession.shared.data(from: url)
        guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
            throw BenchError.message("Hugging Face API \(repo): HTTP \((resp as? HTTPURLResponse)?.statusCode ?? -1)")
        }
        return try JSONDecoder().decode(RepoInfo.self, from: data)
    }

    /// The model's checkpoint when it is on the phone already (downloaded or imported).
    static func present(_ m: ModelEntry) -> Checkpoint? {
        if m.engine == .pie {
            guard let f = pieFile(m) else { return nil }
            let size = (try? f.resourceValues(forKeys: [.fileSizeKey]).fileSize).map(Int64.init) ?? 0
            var c = Checkpoint.read(m.directory) ?? Checkpoint(repo: m.repo, file: nil, revision: nil, bytes: size, imported: true)
            c.file = f.lastPathComponent
            c.bytes = size
            return c
        }
        return Checkpoint.read(m.directory)
    }

    /// A pie `.metal.zt` in the model's folder, `Documents/models/<artifact>.metal.zt` from Finder/Files, or one bundled in the app.
    static func pieFile(_ m: ModelEntry) -> URL? {
        let fm = FileManager.default
        var candidates = [Storage.importFolder.appending(path: "\(m.artifact).metal.zt"), m.directory.appending(path: "model.metal.zt")]
        if let bundled = Bundle.main.url(forResource: m.artifact, withExtension: "metal.zt") { candidates.append(bundled) }
        if let c = candidates.first(where: { fm.fileExists(atPath: $0.path) }) { return c }
        if let items = try? fm.contentsOfDirectory(at: m.directory, includingPropertiesForKeys: nil) {
            return items.first { $0.lastPathComponent.hasSuffix(".metal.zt") }
        }
        return nil
    }

    static func ensure(_ m: ModelEntry, log: @escaping (String) -> Void, progress: @escaping (Double) -> Void) async throws -> Checkpoint {
        if let c = present(m) { return c }
        if m.engine == .pie {
            throw BenchError.message("no \(m.artifact).metal.zt on the phone: run `pie model import \(m.repo) --deployment \(m.pieSku ?? "?")` on a Mac and copy the .metal.zt into PieBench/models/ (Files or Finder)")
        }
        let fm = FileManager.default
        try fm.createDirectory(at: m.directory, withIntermediateDirectories: true)
        let info = try await repoInfo(m.repo)
        let files: [(String, Int64)]
        if let f = m.file {
            files = [(f, info.siblings.first { $0.rfilename == f }?.size ?? m.bytes)]
        } else {
            files = info.siblings.filter { wanted($0.rfilename) }.map { ($0.rfilename, $0.size ?? 0) }
        }
        let total = max(1, files.reduce(0) { $0 + $1.1 })
        var done: Int64 = 0
        var commit: String? = nil
        for (name, size) in files {
            let dest = m.directory.appending(path: name)
            if let s = try? dest.resourceValues(forKeys: [.fileSizeKey]).fileSize, size > 0, Int64(s) == size {
                done += size
                continue
            }
            log("download \(m.repo)/\(name) (\(String(format: "%.2f", Double(size) / 1e9)) GB)")
            let url = URL(string: "https://huggingface.co/\(m.repo)/resolve/\(info.sha)/\(name)")!
            let base = done
            let (tmp, header) = try await fetch(url) { got in progress(Double(base + got) / Double(total)) }
            commit = commit ?? header
            try fm.createDirectory(at: dest.deletingLastPathComponent(), withIntermediateDirectories: true)
            try? fm.removeItem(at: dest)
            try fm.moveItem(at: tmp, to: dest)
            done += size
        }
        let c = Checkpoint(repo: m.repo, file: m.file, revision: commit ?? info.sha, bytes: files.reduce(0) { $0 + $1.1 })
        try c.write(m.directory)
        return c
    }

    /// Downloads to a temp file, reporting bytes; returns the X-Repo-Commit header seen on the way.
    static func fetch(_ url: URL, progress: @escaping (Int64) -> Void) async throws -> (URL, String?) {
        let watcher = RedirectWatcher()
        let session = URLSession(configuration: .default, delegate: watcher, delegateQueue: nil)
        defer { session.finishTasksAndInvalidate() }
        return try await withCheckedThrowingContinuation { cont in
            var timer: Timer?
            let task = session.downloadTask(with: url) { tmp, resp, err in
                DispatchQueue.main.async { timer?.invalidate() }
                if let err { cont.resume(throwing: err); return }
                guard let tmp, let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
                    cont.resume(throwing: BenchError.message("HTTP \((resp as? HTTPURLResponse)?.statusCode ?? -1) for \(url.lastPathComponent)"))
                    return
                }
                // The temp file is deleted when this handler returns: move it first.
                let keep = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
                do { try FileManager.default.moveItem(at: tmp, to: keep) } catch { cont.resume(throwing: error); return }
                cont.resume(returning: (keep, watcher.commit ?? http.value(forHTTPHeaderField: "X-Repo-Commit")))
            }
            DispatchQueue.main.async {
                timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in progress(task.countOfBytesReceived) }
            }
            task.resume()
        }
    }

    final class RedirectWatcher: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
        var commit: String?
        func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                        newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
            if let c = response.value(forHTTPHeaderField: "X-Repo-Commit") { commit = commit ?? c }
            completionHandler(request)
        }
    }

    /// Copies a user-picked file or folder in as this model's weights.
    static func importItem(_ src: URL, for m: ModelEntry) throws {
        let fm = FileManager.default
        let scoped = src.startAccessingSecurityScopedResource()
        defer { if scoped { src.stopAccessingSecurityScopedResource() } }
        try fm.createDirectory(at: m.directory, withIntermediateDirectories: true)
        var isDir: ObjCBool = false
        fm.fileExists(atPath: src.path, isDirectory: &isDir)
        var bytes: Int64 = 0
        if isDir.boolValue {
            for item in try fm.contentsOfDirectory(at: src, includingPropertiesForKeys: nil) {
                let d = m.directory.appending(path: item.lastPathComponent)
                try? fm.removeItem(at: d)
                try fm.copyItem(at: item, to: d)
                bytes += Int64((try? d.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0)
            }
        } else {
            let name = m.engine == .pie ? "model.metal.zt" : (m.file ?? src.lastPathComponent)
            let d = m.directory.appending(path: name)
            try? fm.removeItem(at: d)
            try fm.copyItem(at: src, to: d)
            bytes = Int64((try? d.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0)
        }
        // An import carries no Hugging Face commit: revision stays null unless a downloaded .checkpoint.json came along.
        if Checkpoint.read(m.directory) == nil {
            try Checkpoint(repo: m.repo, file: m.file, revision: nil, bytes: bytes, imported: true).write(m.directory)
        }
    }
}
