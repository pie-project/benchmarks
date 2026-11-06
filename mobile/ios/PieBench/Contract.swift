import Foundation

/// mobile/shared/workloads.json, written by the harness (mobile/tools/gen_workloads.py).
struct Contract: Decodable {
    struct Round: Decodable {
        let warmup: [String]
        let measured: [String]
    }

    struct Workload: Decodable, Identifiable {
        let id: String
        let kind: String
        let concurrency: Int
        let prefill: Int
        let decode: Int
        let requests: Int
        let warmup: Int
        let cold_cache: Bool
        let temperature: Double
        let ignore_eos: Bool
        let rounds: [Round]
    }

    struct Template: Decodable {
        let prefix: String
        let suffix: String
        let tokenizer: String?
        /// prompt_tokens[workload][round][i]: the count each prompt must come to.
        let prompt_tokens: [String: [[Int]]]
    }

    let schema: String
    let harness_commit: String
    let system: String
    let rounds: Int
    let workloads: [Workload]
    let templates: [String: Template]

    static func load() throws -> Contract {
        // PIEBENCH_WORKLOADS_JSON: the Mac test harness (e2e/) reads mobile/shared/workloads.json directly.
        let override = ProcessInfo.processInfo.environment["PIEBENCH_WORKLOADS_JSON"].map { URL(fileURLWithPath: $0) }
        guard let url = override ?? Bundle.main.url(forResource: "workloads", withExtension: "json") else {
            throw BenchError.message("workloads.json is not in the app bundle")
        }
        return try JSONDecoder().decode(Contract.self, from: Data(contentsOf: url))
    }

    func workload(_ id: String) -> Workload? { workloads.first { $0.id == id } }
}

enum BenchError: LocalizedError {
    case message(String)
    var errorDescription: String? {
        switch self { case .message(let m): return m }
    }
}
