package org.pieevals.phonebench.engines

import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import java.io.File

/** One measured request: raw timestamps (System.nanoTime clock), the server derives everything else. */
data class ReqTiming(
    val promptTokens: Int,
    val outputTokens: Int,
    val sendNs: Long,
    val firstNs: Long,
    val lastNs: Long,
    val cachedPromptTokens: Int = 0,
)

/**
 * The one interface every on-device engine sits behind.
 *
 * load() once per model; run() serves `prompts` (already chat-template-rendered:
 * prefix + user + suffix) with up to `concurrency` requests in flight as real parallel
 * sequences, greedy, `maxNew` output tokens (ignoring EOS where the engine allows),
 * every prompt cold (no KV / prefix reuse between requests).
 */
interface BenchEngine {
    val id: String                     // "llamacpp" | "litert" | "mlc" | "pie"
    val version: String                // engine release / commit
    val backend: String                // "cpu" | "vulkan" | "opencl" | "gpu"
    /** Largest number of requests the engine can serve at once (1 = one at a time). */
    val maxConcurrency: Int

    /** Knobs that shape the numbers; written to engine_config. */
    fun config(): JSONObject

    fun load(artifact: Artifact, model: File)

    fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming>

    fun close()
}

/** An engine that is not built into this APK: its rows say why instead of carrying numbers. */
class UnavailableEngine(override val id: String, val reason: String, override val backend: String, override val version: String = "unavailable") : BenchEngine {
    override val maxConcurrency = 0
    override fun config() = JSONObject().put("unavailable_reason", reason)
    override fun load(artifact: Artifact, model: File) = throw UnsupportedOperationException(reason)
    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> = throw UnsupportedOperationException(reason)
    override fun close() {}
}
