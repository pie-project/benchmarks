import Foundation

#if canImport(LiteRtLm)
import LiteRtLm

final class LiteRtCore: @unchecked Sendable {
    static let version = "0.19.1"
    let maxNumTokens: Int
    private let engine: OpaquePointer

    init(path: String, backend: String, maxNumTokens: Int, cacheDir: String) throws {
        self.maxNumTokens = maxNumTokens
        try? FileManager.default.createDirectory(atPath: cacheDir, withIntermediateDirectories: true)
        var settings: OpaquePointer?
        try LiteRtCore.check(litert_lm_engine_settings_create(path, backend, nil, nil, &settings), "engine_settings_create")
        defer { litert_lm_engine_settings_delete(settings) }
        try LiteRtCore.check(litert_lm_engine_settings_set_max_num_tokens(settings, Int32(maxNumTokens)), "set_max_num_tokens")
        try LiteRtCore.check(litert_lm_engine_settings_set_cache_dir(settings, cacheDir), "set_cache_dir")
        var e: OpaquePointer?
        try LiteRtCore.check(litert_lm_engine_create(settings, &e), "engine_create")
        guard let e else { throw LiteRtCore.Failure(message: "engine_create returned no engine") }
        engine = e
    }

    deinit { litert_lm_engine_delete(engine) }

    struct Failure: LocalizedError {
        let message: String
        var errorDescription: String? { "LiteRT-LM: \(message)" }
    }

    static func check(_ status: LiteRtLmStatusCode, _ what: String) throws {
        guard status != kLiteRtLmStatusOk else { return }
        let msg = litert_lm_get_last_error_message().map { String(cString: $0) } ?? "status \(status.rawValue)"
        throw Failure(message: "\(what): \(msg)")
    }

    struct Stream {
        var sent: Double
        var first: Double
        var last: Double
        var tokens: Int
        var text: String?
    }

    private final class Box {
        let want: Int
        let clock: () -> Double
        var session: OpaquePointer?
        var tokens = 0
        var first = 0.0
        var last = 0.0
        var error: String?
        var text: String?
        let done = DispatchSemaphore(value: 0)
        init(want: Int, clock: @escaping () -> Double) { self.want = want; self.clock = clock }
    }

    func generate(_ prompt: String, want: Int, keepText: Bool = false, clock: @escaping () -> Double) throws -> Stream {
        var params: OpaquePointer?
        try LiteRtCore.check(litert_lm_sampler_params_create(kLiteRtLmSamplerTypeTopP, &params), "sampler_params_create")
        defer { litert_lm_sampler_params_delete(params) }
        try LiteRtCore.check(litert_lm_sampler_params_set_top_k(params, 1), "set_top_k")
        try LiteRtCore.check(litert_lm_sampler_params_set_top_p(params, 1), "set_top_p")
        try LiteRtCore.check(litert_lm_sampler_params_set_temperature(params, 0), "set_temperature")
        try LiteRtCore.check(litert_lm_sampler_params_set_seed(params, 0), "set_seed")
        var config: OpaquePointer?
        try LiteRtCore.check(litert_lm_session_config_create(&config), "session_config_create")
        defer { litert_lm_session_config_delete(config) }
        try LiteRtCore.check(litert_lm_session_config_set_sampler_params(config, params), "set_sampler_params")
        var session: OpaquePointer?
        try LiteRtCore.check(litert_lm_engine_create_session(engine, config, &session), "engine_create_session")
        defer { litert_lm_session_delete(session) }

        var input: OpaquePointer?
        let bytes = Array(prompt.utf8)
        try bytes.withUnsafeBytes { raw in
            try LiteRtCore.check(litert_lm_input_data_create(kLiteRtLmInputDataTypeText, raw.baseAddress, raw.count, &input), "input_data_create")
        }
        defer { litert_lm_input_data_delete(input) }

        let box = Box(want: want, clock: clock)
        box.session = session
        if keepText { box.text = "" }
        let ctx = Unmanaged.passRetained(box)
        defer { ctx.release() }
        let callback: LiteRtLmStreamCallback = { data, chunk in
            let box = Unmanaged<Box>.fromOpaque(data!).takeUnretainedValue()
            let t = box.clock()
            var final = false
            _ = litert_lm_stream_chunk_is_final(chunk, &final)
            if final {
                var err: UnsafePointer<CChar>?
                _ = litert_lm_stream_chunk_get_error(chunk, &err)
                if let err, box.tokens < box.want { box.error = String(cString: err) }
                box.done.signal()
                return
            }
            box.tokens += 1
            if box.text != nil, box.tokens <= box.want {
                var s: UnsafePointer<CChar>?
                if litert_lm_stream_chunk_get_text(chunk, &s) == kLiteRtLmStatusOk, let s { box.text! += String(cString: s) }
            }
            if box.tokens == 1 { box.first = t }
            if box.tokens <= box.want { box.last = t }
            if box.tokens == box.want { _ = litert_lm_session_cancel_process(box.session) }
        }
        let sent = clock()
        var inputs: [OpaquePointer?] = [input]
        try LiteRtCore.check(litert_lm_session_generate_content_stream(session, &inputs, 1, callback, ctx.toOpaque()),
                             "generate_content_stream")
        if box.done.wait(timeout: .now() + 1800) == .timedOut { throw Failure(message: "request timed out") }
        if let e = box.error { throw Failure(message: e) }
        return Stream(sent: sent, first: box.first, last: box.last, tokens: min(box.tokens, want), text: box.text)
    }
}
#endif
