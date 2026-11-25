import Foundation

struct Contract: Decodable {
    struct Round: Decodable {
        let warmup: [String]
        let measured: [String]
    }

    struct Workload: Decodable, Identifiable {
        let id: String
        let concurrency: Int
        let prefill: Int
        let decode: Int
        let warmup: Int
        let rounds: [Round]
    }

    struct Template: Decodable {
        let prefix: String
        let suffix: String
        let tokenizer: String?
        let prompt_tokens: [String: [[Int]]]
    }

    let harness_commit: String
    let system: String
    let rounds: Int
    let workloads: [Workload]
    let templates: [String: Template]

    static func load() throws -> Contract {
        guard let url = Bundle.main.url(forResource: "workloads", withExtension: "json") else {
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
