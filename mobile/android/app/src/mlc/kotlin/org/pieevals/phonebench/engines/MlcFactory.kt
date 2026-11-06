package org.pieevals.phonebench.engines

import ai.mlc.mlcllm.JSONFFIEngine
import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import org.pieevals.phonebench.Workloads
import java.io.File
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

object MlcFactory {
    const val MLC_COMMIT = "44fd06d04f22c87820e205b0f2b2e5e6a1f6ca85"
    const val TVM_COMMIT = "629cc65820b8699db4d777f5749bb9d3b7444be0"
    /** Model libraries compiled into libtvm4j_runtime_packed.so (mlc_llm package, android/OpenCL). */
    val MODEL_LIBS = mapOf(
        "qwen3.5-0.8b-mlc" to "qwen3_5_q4f32_1_74360ec5594368cd833f5174680568d9",
        "qwen3.5-4b-mlc" to "qwen3_5_q4f16_1_5765e01927a6e834b4f68cb410e5cf36",
        "gemma-4-e2b-mlc" to "gemma4_q4f16_1_ffc90a6442e7f40347a1f9736fb36b09",
    )
    fun create(context: Context): BenchEngine = MlcEngine(context)
}

/**
 * MLC LLM through its JSON FFI engine (mlc4j, TVM runtime, OpenCL). Mode "local" with 4 sequences:
 * concurrent chat completions decode as one batch. MLC takes chat messages only, so the rendered
 * prompt is split back into system + user and MLC applies the model's conversation template.
 */
class MlcEngine(private val context: Context) : BenchEngine {
    override val id = "mlc"
    override val version = MlcFactory.MLC_COMMIT.take(12)
    override val backend = "opencl"
    override val maxConcurrency = 4
    private var ffi: JSONFFIEngine? = null
    private var template: org.pieevals.phonebench.Template? = null
    private var system = ""
    private var modelLib = ""
    private var patchedThink = false
    private var gemma = false
    private val events = LinkedBlockingQueue<JSONObject>()
    private var seq = 0

    override fun config(): JSONObject = JSONObject()
        .put("mlc_commit", MlcFactory.MLC_COMMIT)
        .put("tvm_commit", MlcFactory.TVM_COMMIT)
        .put("model_lib", modelLib)
        .put("api", "JSONFFIEngine chat_completion, stream + include_usage")
        .put("input", "chat messages (system + user); MLC renders its own conversation template, not the raw prompt")
        .put("thinking_off", if (patchedThink) "assistant role patched to '<|im_start|>assistant\\n<think>\\n\\n</think>\\n'" else "template has no thinking block")
        .put("mode", "local").put("max_num_sequence", 4).put("max_total_sequence_length", 4096)
        .put("max_single_sequence_length", 2048).put("prefill_chunk_size", 512)
        .put("context_window_size_compiled", 2048).put("max_batch_size_compiled", 4)
        .put("prefix_cache_mode", "disable")
        .put("temperature", 0).put("top_p", 1).put("ignore_eos", true)
        .put("token_counts", "usage chunk (prompt_tokens, completion_tokens)")
        .apply { if (gemma) put("gemma_lib", "text-only model library, audio encoder omitted (MLC_GEMMA4_TEXT_ONLY)") }
        .put("build_patches", "TVM attach_global_symbol fix; dlight gemv fallback schedule")

    override fun load(artifact: Artifact, model: File) {
        modelLib = MlcFactory.MODEL_LIBS[artifact.id] ?: throw IllegalArgumentException("no compiled MLC model library for ${artifact.id}")
        // TVM's OpenCL init dereferences null (SIGSEGV, killing the app) when there is no OpenCL driver: check first
        val cl = listOf("/vendor/lib64/libOpenCL.so", "/system/vendor/lib64/libOpenCL.so", "/vendor/lib64/egl/libGLES_mali.so", "/system/lib64/libOpenCL.so")
        if (cl.none { File(it).exists() }) throw IllegalStateException("no OpenCL driver on this device (looked for ${cl.joinToString()})")
        val wl = Workloads.load(context)
        template = wl.templates[artifact.model]
        system = wl.system
        gemma = artifact.model.startsWith("gemma")
        // Qwen3.5's MLC template has no empty think block: patch the device copy so thinking is off as on the Mac
        if (artifact.model.startsWith("qwen")) {
            val f = model.resolve("mlc-chat-config.json")
            val j = JSONObject(f.readText())
            val roles = j.getJSONObject("conv_template").getJSONObject("roles")
            val want = "<|im_start|>assistant\n<think>\n\n</think>\n"
            if (roles.optString("assistant") != want) { roles.put("assistant", want); f.writeText(j.toString(1)) }
            patchedThink = true
        }
        val e = JSONFFIEngine()
        e.initBackgroundEngine { s -> route(s) }
        thread(name = "mlc-loop", isDaemon = true) { e.runBackgroundLoop() }
        thread(name = "mlc-stream", isDaemon = true) { e.runBackgroundStreamBackLoop() }
        e.reload(JSONObject().put("model", model.absolutePath).put("model_lib", "system://$modelLib").put("mode", "local")
            .put("max_num_sequence", 4).put("max_total_sequence_length", 4096).put("max_single_sequence_length", 2048)
            .put("prefill_chunk_size", 512).put("prefix_cache_mode", "disable").toString())
        ffi = e
    }

    private fun route(s: String) {
        val arr = runCatching { JSONArray(s) }.getOrNull() ?: return
        val t = System.nanoTime()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            o.put("_t", t)
            events.offer(o)
        }
    }

    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> {
        val e = ffi ?: error("not loaded")
        val tpl = template ?: error("no template")
        val results = arrayOfNulls<ReqTiming>(prompts.size)
        val inflight = HashMap<String, Triple<Int, Long, LongArray>>() // id -> (index, send, [first,last,chunks])
        var next = 0
        events.clear()
        fun submit() {
            val i = next++
            val user = prompts[i].removePrefix(tpl.prefix).removeSuffix(tpl.suffix)
            val id = "req-${seq++}"
            val req = JSONObject()
                .put("messages", JSONArray().put(JSONObject().put("role", "system").put("content", system)).put(JSONObject().put("role", "user").put("content", user)))
                .put("stream", true).put("stream_options", JSONObject().put("include_usage", true))
                .put("max_tokens", maxNew).put("temperature", 0).put("top_p", 1)
                .put("debug_config", JSONObject().put("ignore_eos", true))
            val send = System.nanoTime()
            inflight[id] = Triple(i, send, longArrayOf(0, 0, 0))
            e.chatCompletion(req.toString(), id)
        }
        while (next < prompts.size && inflight.size < maxOf(1, concurrency)) submit()
        while (inflight.isNotEmpty()) {
            // a silent engine for 5 minutes is a hang: the cell fails instead of the run hanging
            val o = events.poll(5, TimeUnit.MINUTES) ?: error("MLC: no stream output for 5 minutes")
            val id = o.optString("id")
            val (i, send, st) = inflight[id] ?: continue
            val t = o.getLong("_t")
            val ch = o.optJSONArray("choices")
            if (ch != null && ch.length() > 0) {
                val txt = ch.getJSONObject(0).optJSONObject("delta")?.optString("content").orEmpty()
                if (txt.isNotEmpty()) { if (st[0] == 0L) st[0] = t; st[1] = t; st[2]++ }
            }
            val u = o.optJSONObject("usage")
            if (u != null) {
                results[i] = ReqTiming(u.optInt("prompt_tokens", -1), u.optInt("completion_tokens", st[2].toInt()), send, st[0], st[1])
                inflight.remove(id)
                if (next < prompts.size) submit()
            }
        }
        return results.map { it!! }
    }

    override fun close() {
        runCatching { ffi?.unload() }
        runCatching { ffi?.exitBackgroundLoop() }
        ffi = null
    }
}
