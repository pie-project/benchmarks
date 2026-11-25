package org.pieevals.phonebench.engines

import android.content.Context
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import org.pieproject.server.PieServer
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Callable
import java.util.concurrent.Executors

object PieFactory {
    const val PIE_COMMIT = "a6547509432d48c76e258bfefbb85bd58984f8e4"
    fun create(context: Context): BenchEngine = PieEngine(context)
}

class PieEngine(private val context: Context) : BenchEngine {
    override val id = "pie"
    override val version = PieFactory.PIE_COMMIT
    override val backend = "vulkan"
    override val maxConcurrency = 4
    private var server: PieServer? = null
    private var base = ""
    private var summary = JSONObject()

    override fun config(): JSONObject = JSONObject()
        .put("pie_commit", PieFactory.PIE_COMMIT)
        .put("api", "PieServer in process, POST /v1/completions stream=true on 127.0.0.1 (raw prompt, no chat template)")
        .put("max_model_len", 4096)
        .put("max_forward_tokens", 512)
        .put("max_forward_requests", 4)
        .put("max_concurrent_processes", 4)
        .put("device_memory_share", 0.6)
        .put("temperature", 0)
        .put("ignore_eos", true)
        .put("prefix_cache", "always on in pie embedded (no switch); cached_prompt_tokens as pie reports them")
        .put("token_counts", "usage chunk (stream_options.include_usage)")
        .put("summary", summary)

    override fun load(artifact: Artifact, model: File) {
        if (booted) throw IllegalStateException("pie runtime boots once per process; restart the app to run another pie model")
        booted = true
        val s = runBlocking {
            PieServer.start(model = model, home = File(context.cacheDir, "pie"), listen = "127.0.0.1:0") {
                maxModelLength = 4096; maxForwardRequests = 4; maxForwardTokens = 512; maxConcurrentProcesses = 4
            }
        }
        server = s
        base = "http://" + (s.listenAddress ?: error("pie gateway did not listen"))
        summary = JSONObject().put("model", s.summary.model).put("deployment", s.summary.deployment)
            .put("weight_bytes", s.summary.weightBytes).put("kv_pages", s.summary.kvPages).put("kv_page_size", s.summary.kvPageSize)
            .put("max_lanes", s.summary.maxLanes).put("max_tokens", s.summary.maxTokens)
    }

    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> {
        if (concurrency <= 1) return prompts.map { one(it, maxNew) }
        val pool = Executors.newFixedThreadPool(concurrency)
        try {
            return pool.invokeAll(prompts.map { p -> Callable { one(p, maxNew) } }).map { it.get() }
        } finally {
            pool.shutdown()
        }
    }

    private fun one(prompt: String, maxNew: Int): ReqTiming {
        val body = JSONObject().put("model", "default").put("prompt", prompt).put("max_tokens", maxNew)
            .put("temperature", 0).put("ignore_eos", true).put("stream", true)
            .put("stream_options", JSONObject().put("include_usage", true))
        val send = System.nanoTime()
        val c = URL("$base/v1/completions").openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.doOutput = true
        c.readTimeout = 5 * 60 * 1000
        c.setRequestProperty("Content-Type", "application/json")
        c.outputStream.use { it.write(body.toString().toByteArray()) }
        if (c.responseCode != 200) error("pie HTTP ${c.responseCode}: ${c.errorStream?.bufferedReader()?.readText()}")
        var first = 0L
        var last = 0L
        var chunks = 0
        var usage: JSONObject? = null
        c.inputStream.bufferedReader().useLines { lines ->
            for (line in lines) {
                if (!line.startsWith("data:")) continue
                val d = line.removePrefix("data:").trim()
                if (d == "[DONE]") break
                val o = JSONObject(d)
                o.optJSONObject("usage")?.let { usage = it }
                val ch = o.optJSONArray("choices")
                if (ch != null && ch.length() > 0 && ch.getJSONObject(0).optString("text").isNotEmpty()) {
                    val t = System.nanoTime()
                    if (first == 0L) first = t
                    last = t
                    chunks++
                }
            }
        }
        c.disconnect()
        val u = usage
        val out = u?.optInt("completion_tokens", chunks) ?: chunks
        val inTok = u?.optInt("prompt_tokens", -1) ?: -1
        val cached = u?.optJSONObject("prompt_tokens_details")?.optInt("cached_tokens", 0) ?: 0
        return ReqTiming(inTok, out, send, first, last, cached)
    }

    override fun close() {
        runCatching { runBlocking { server?.shutdown() } }
        server = null
    }

    companion object {
        @Volatile private var booted = false
    }
}
