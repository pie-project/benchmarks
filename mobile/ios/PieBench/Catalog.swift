import Foundation

enum EngineID: String, CaseIterable, Identifiable {
    case llamacpp, mlxSwift = "mlx-swift", mlc, pie, litert
    var id: String { rawValue }
    var label: String {
        switch self {
        case .llamacpp: return "llama.cpp"
        case .mlxSwift: return "MLX Swift"
        case .mlc: return "MLC LLM"
        case .pie: return "Pie"
        case .litert: return "LiteRT-LM"
        }
    }
}

struct ModelEntry: Identifiable, Hashable {
    let engine: EngineID
    let artifact: String
    let model: String
    let repo: String
    let file: String?
    let bytes: Int64
    let pieSku: String?

    var id: String { "\(engine.rawValue)/\(artifact)" }
    var slug: String { model.replacingOccurrences(of: ".", with: "") }

    var directory: URL { Storage.models.appending(path: "\(engine.rawValue)/\(artifact)", directoryHint: .isDirectory) }

    static let all: [ModelEntry] = [
        .init(engine: .llamacpp, artifact: "qwen3.5-0.8b-llamacpp", model: "qwen3.5-0.8b", repo: "unsloth/Qwen3.5-0.8B-GGUF", file: "Qwen3.5-0.8B-Q4_K_M.gguf", bytes: 532_517_120, pieSku: nil),
        .init(engine: .llamacpp, artifact: "qwen3.5-4b-llamacpp", model: "qwen3.5-4b", repo: "unsloth/Qwen3.5-4B-GGUF", file: "Qwen3.5-4B-Q4_K_M.gguf", bytes: 2_740_937_888, pieSku: nil),
        .init(engine: .llamacpp, artifact: "gemma-4-e2b-llamacpp", model: "gemma-4-e2b", repo: "unsloth/gemma-4-E2B-it-GGUF", file: "gemma-4-E2B-it-Q4_K_M.gguf", bytes: 3_106_738_272, pieSku: nil),
        .init(engine: .llamacpp, artifact: "gemma-4-e4b-llamacpp", model: "gemma-4-e4b", repo: "unsloth/gemma-4-E4B-it-GGUF", file: "gemma-4-E4B-it-Q4_K_M.gguf", bytes: 4_977_171_584, pieSku: nil),
        .init(engine: .llamacpp, artifact: "gemma-4-12b-llamacpp", model: "gemma-4-12b", repo: "unsloth/gemma-4-12b-it-GGUF", file: "gemma-4-12b-it-Q4_K_M.gguf", bytes: 7_121_861_440, pieSku: nil),
        .init(engine: .mlxSwift, artifact: "qwen3.5-0.8b-mlx4", model: "qwen3.5-0.8b", repo: "mlx-community/Qwen3.5-0.8B-4bit", file: nil, bytes: 652_029_391, pieSku: nil),
        .init(engine: .mlxSwift, artifact: "qwen3.5-4b-mlxlm", model: "qwen3.5-4b", repo: "mlx-community/Qwen3.5-4B-4bit", file: nil, bytes: 3_061_130_647, pieSku: nil),
        .init(engine: .mlxSwift, artifact: "gemma-4-e2b-mlxlm", model: "gemma-4-e2b", repo: "mlx-community/gemma-4-e2b-it-4bit", file: nil, bytes: 3_583_088_661, pieSku: nil),
        .init(engine: .mlxSwift, artifact: "gemma-4-e4b-mlxlm", model: "gemma-4-e4b", repo: "mlx-community/gemma-4-e4b-it-4bit", file: nil, bytes: 5_179_241_512, pieSku: nil),
        .init(engine: .mlxSwift, artifact: "gemma-4-12b-mlxlm", model: "gemma-4-12b", repo: "mlx-community/gemma-4-12B-it-4bit", file: nil, bytes: 6_773_372_848, pieSku: nil),
        .init(engine: .mlc, artifact: "qwen3.5-0.8b-mlc", model: "qwen3.5-0.8b", repo: "mlc-ai/Qwen3.5-0.8B-q4f32_1-MLC", file: nil, bytes: 447_175_335, pieSku: nil),
        .init(engine: .mlc, artifact: "qwen3.5-4b-mlc", model: "qwen3.5-4b", repo: "mlc-ai/Qwen3.5-4B-q4f16_1-MLC", file: nil, bytes: 2_390_497_405, pieSku: nil),
        .init(engine: .mlc, artifact: "gemma-4-e2b-mlc", model: "gemma-4-e2b", repo: "mlc-ai/gemma-4-E2B-it-q4f16_1-MLC", file: nil, bytes: 2_831_045_154, pieSku: nil),
        .init(engine: .litert, artifact: "qwen3.5-0.8b-litert", model: "qwen3.5-0.8b", repo: "litert-community/Qwen3.5-0.8B", file: "Qwen3.5-0.8B_int8_gpu_composite_v0190.litertlm", bytes: 888_373_248, pieSku: nil),
        .init(engine: .litert, artifact: "qwen3.5-4b-litert", model: "qwen3.5-4b", repo: "litert-community/Qwen3.5-4B", file: "Qwen3.5-4B_mixed_int4_gpu_composite_v0190.litertlm", bytes: 2_712_846_336, pieSku: nil),
        .init(engine: .litert, artifact: "gemma-4-e2b-litert", model: "gemma-4-e2b", repo: "litert-community/gemma-4-E2B-it-litert-lm", file: "gemma-4-E2B-it.litertlm", bytes: 2_588_147_712, pieSku: nil),
        .init(engine: .litert, artifact: "gemma-4-e4b-litert", model: "gemma-4-e4b", repo: "litert-community/gemma-4-E4B-it-litert-lm", file: "gemma-4-E4B-it.litertlm", bytes: 3_659_530_240, pieSku: nil),
        .init(engine: .pie, artifact: "qwen3.5-0.8b-mlx4", model: "qwen3.5-0.8b", repo: "mlx-community/Qwen3.5-0.8B-4bit", file: nil, bytes: 652_029_391, pieSku: "qwen35-d0.8b-u4g64-kv-bf16"),
        .init(engine: .pie, artifact: "qwen3.5-4b-mlx4", model: "qwen3.5-4b", repo: "mlx-community/Qwen3.5-4B-4bit", file: nil, bytes: 3_061_130_647, pieSku: "qwen35-d4b-u4g64-kv-bf16"),
        .init(engine: .pie, artifact: "gemma-4-e2b-mlx4", model: "gemma-4-e2b", repo: "mlx-community/gemma-4-e2b-it-4bit", file: nil, bytes: 3_583_088_661, pieSku: "gemma4-e2b-u4g64-kv-bf16"),
        .init(engine: .pie, artifact: "gemma-4-e4b-mlx4", model: "gemma-4-e4b", repo: "mlx-community/gemma-4-e4b-it-4bit", file: nil, bytes: 5_179_241_512, pieSku: "gemma4-e4b-u4g64-kv-bf16"),
        .init(engine: .pie, artifact: "gemma-4-12b-mlx4", model: "gemma-4-12b", repo: "mlx-community/gemma-4-12B-it-4bit", file: nil, bytes: 6_773_372_848, pieSku: "gemma4-12b-u4g64-kv-bf16"),
    ]
}

enum Storage {
    static var home: URL? { ProcessInfo.processInfo.environment["PIEBENCH_HOME"].map { URL(fileURLWithPath: $0, isDirectory: true) } }
    static var documents: URL {
        guard let h = home else { return URL.documentsDirectory }
        let u = h.appending(path: "Documents", directoryHint: .isDirectory)
        try? FileManager.default.createDirectory(at: u, withIntermediateDirectories: true)
        return u
    }
    static var support: URL {
        let u = home?.appending(path: "Application Support", directoryHint: .isDirectory) ?? URL.applicationSupportDirectory
        try? FileManager.default.createDirectory(at: u, withIntermediateDirectories: true)
        return u
    }
    static var models: URL { support.appending(path: "models", directoryHint: .isDirectory) }
    static var records: URL { documents.appending(path: "records.jsonl") }
    static var importFolder: URL { documents.appending(path: "models", directoryHint: .isDirectory) }
    static var inProgress: URL { support.appending(path: "in-progress.json") }
}
