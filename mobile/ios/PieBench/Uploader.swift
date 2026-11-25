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

    static func gzipBase64(_ data: Data) throws -> String {
        guard let deflated = try? (data as NSData).compressed(using: .zlib) as Data else {
            throw BenchError.message("deflate failed")
        }
        var out = Data([0x1f, 0x8b, 0x08, 0x00, 0, 0, 0, 0, 0x00, 0x03])
        out.append(deflated)
        var crc = crc32(data).littleEndian
        var size = UInt32(truncatingIfNeeded: data.count).littleEndian
        withUnsafeBytes(of: &crc) { out.append(contentsOf: $0) }
        withUnsafeBytes(of: &size) { out.append(contentsOf: $0) }
        return out.base64EncodedString()
    }

    private static let table: [UInt32] = (0..<256).map { i -> UInt32 in
        var c = UInt32(i)
        for _ in 0..<8 { c = (c & 1) != 0 ? 0xEDB8_8320 ^ (c >> 1) : c >> 1 }
        return c
    }

    static func crc32(_ data: Data) -> UInt32 {
        var c: UInt32 = 0xFFFF_FFFF
        for b in data { c = table[Int((c ^ UInt32(b)) & 0xFF)] ^ (c >> 8) }
        return c ^ 0xFFFF_FFFF
    }
}
