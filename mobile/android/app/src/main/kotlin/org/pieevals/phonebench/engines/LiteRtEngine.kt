package org.pieevals.phonebench.engines

import android.content.Context
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import com.google.ai.edge.litertlm.InputData
import com.google.ai.edge.litertlm.ResponseCallback
import com.google.ai.edge.litertlm.SamplerConfig
import com.google.ai.edge.litertlm.SessionConfig
import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

class LiteRtEngine(private val context: Context, private val useGpu: Boolean, private val threads: Int) : BenchEngine {
    override val id = "litert"
    override val version = LITERTLM_VERSION
    override val backend get() = if (useGpu) "gpu" else "cpu"
    override val maxConcurrency = 1
    private var engine: Engine? = null
    private var stripBos = false
    private var stoppedEarly = 0

    override fun config(): JSONObject = JSONObject()
        .put("api", "com.google.ai.edge.litertlm Session.generateContentStream (raw prompt text)")
        .put("backend", if (useGpu) "GPU" else "CPU")
        .put("cpu_threads", if (useGpu) JSONObject.NULL else threads)
        .put("max_num_tokens", MAX_TOKENS)
        .put("sampler", "top_k=1 top_p=1 temperature=0 (greedy)")
        .put("ignore_eos", false)
        .put("ignore_eos_note", "LiteRT-LM has no ignore_eos; decode is cancelled after `decode` stream chunks, a model that stops early records its real count")
        .put("output_tokens_source", "stream callbacks (one per decode step)")
        .put("prompt_tokens_source", "harness tokenizer count from workloads.json (LiteRT-LM Session does not report it)")
        .put("bos", if (stripBos) "leading '<bos>' text removed, the session adds the model's start token itself" else "none in template")
        .put("session", "fresh session per request (cold KV), created before the send timestamp")
        .put("requests_stopped_by_eos", stoppedEarly)

    override fun load(artifact: Artifact, model: File) {
        val be = if (useGpu) Backend.GPU() else Backend.CPU(threads, null)
        val cfg = EngineConfig(modelPath = model.absolutePath, backend = be, maxNumTokens = MAX_TOKENS, cacheDir = context.cacheDir.absolutePath)
        val e = Engine(cfg)
        e.initialize()
        engine = e
        stripBos = artifact.model.startsWith("gemma")
    }

    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> {
        require(concurrency == 1) { "serves one request at a time" }
        return prompts.map { one(it, maxNew) }
    }

    private fun one(prompt0: String, maxNew: Int): ReqTiming {
        val e = engine ?: error("not loaded")
        val prompt = if (stripBos && prompt0.startsWith("<bos>")) prompt0.removePrefix("<bos>") else prompt0
        val session = e.createSession(SessionConfig(SamplerConfig(1, 1.0, 0.0, 0)))
        try {
            val n = AtomicInteger(0)
            var first = 0L
            var last = 0L
            var err: Throwable? = null
            val latch = CountDownLatch(1)
            val send = System.nanoTime()
            session.generateContentStream(listOf(InputData.Text(prompt)), object : ResponseCallback {
                override fun onNext(response: String) {
                    val t = System.nanoTime()
                    val k = n.incrementAndGet()
                    if (k == 1) first = t
                    if (k <= maxNew) last = t
                    if (k == maxNew) runCatching { session.cancelProcess() }
                }
                override fun onDone() { latch.countDown() }
                override fun onError(throwable: Throwable) {
                    if (n.get() < maxNew) err = throwable
                    latch.countDown()
                }
            })
            if (!latch.await(30, TimeUnit.MINUTES)) error("LiteRT-LM request timed out")
            err?.let { throw RuntimeException("LiteRT-LM: ${it.message}", it) }
            val out = minOf(n.get(), maxNew)
            if (out < maxNew) stoppedEarly++
            return ReqTiming(-1, out, send, first, last)
        } finally {
            session.close()
        }
    }

    override fun close() {
        engine?.close()
        engine = null
    }

    companion object {
        const val LITERTLM_VERSION = "0.19.1"
        const val MAX_TOKENS = 2048
    }
}
