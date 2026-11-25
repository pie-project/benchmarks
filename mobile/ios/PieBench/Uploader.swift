import Foundation

enum Uploader {
    static func send(_ file: URL, base: String, token: String) async throws -> String {
        let body = try Data(contentsOf: file)
        guard !body.isEmpty else { throw BenchError.message("records.jsonl is empty") }
        var trimmed = base.trimmingCharacters(in: .whitespacesAndNewlines)
        while trimmed.hasSuffix("/") { trimmed.removeLast() }
        guard let url = URL(string: trimmed + "/v1/results") else { throw BenchError.message("bad ingest URL \(base)") }
        var req = URLRequest(url: url, timeoutInterval: 60)
        req.httpMethod = "POST"
        req.setValue("application/x-ndjson", forHTTPHeaderField: "Content-Type")
        if !token.isEmpty { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        req.httpBody = body
        let (data, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? -1
        return "HTTP \(code): \(String(decoding: data.prefix(2000), as: UTF8.self))"
    }
}
