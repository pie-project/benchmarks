package org.pieevals.phonebench.engines

import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import java.io.File

data class ReqTiming(
    val promptTokens: Int,
    val outputTokens: Int,
    val sendNs: Long,
    val firstNs: Long,
    val lastNs: Long,
    val cachedPromptTokens: Int = 0,
)

interface BenchEngine {
    val id: String
    val version: String
    val backend: String
    val maxConcurrency: Int

    fun config(): JSONObject

    fun load(artifact: Artifact, model: File)

    fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming>

    fun close()
}

class UnavailableEngine(override val id: String, val reason: String, override val backend: String, override val version: String = "unavailable") : BenchEngine {
    override val maxConcurrency = 0
    override fun config() = JSONObject().put("unavailable_reason", reason)
    override fun load(artifact: Artifact, model: File) = throw UnsupportedOperationException(reason)
    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> = throw UnsupportedOperationException(reason)
    override fun close() {}
}
