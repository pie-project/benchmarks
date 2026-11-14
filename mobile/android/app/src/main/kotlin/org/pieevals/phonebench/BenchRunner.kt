package org.pieevals.phonebench

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import org.json.JSONArray
import org.json.JSONObject
import org.pieevals.phonebench.engines.BenchEngine
import org.pieevals.phonebench.engines.LiteRtEngine
import org.pieevals.phonebench.engines.LlamaCppEngine
import org.pieevals.phonebench.engines.MlcFactory
import org.pieevals.phonebench.engines.PieFactory
import org.pieevals.phonebench.engines.ReqTiming
import java.io.File
import java.security.SecureRandom
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

data class RunConfig(
    val engines: List<String>,
    val models: List<String>,       // site model ids
    val workloads: List<String>,
    val tag: String?,
    val litertGpu: Boolean = true,
    val llamaGpu: Boolean = false,  // llama.cpp on the APK's GPU backend (Vulkan) instead of CPU
    val threads: Int = 0,           // 0 = DeviceInfo.defaultThreads()
    val download: Boolean = true,
    val send: Boolean = false,
    val url: String = "",
    val token: String = "",
)

/** A display row (computed locally, display only; the server recomputes from the raw timings). */
data class ResultRow(val engine: String, val artifact: String, val workload: String, val status: String,
                     val decodeTokS: Double?, val prefillTokS: Double?, val ttftS: Double?, val peakGib: Double?, val error: String?)

object BenchState {
    val log = MutableStateFlow<List<String>>(emptyList())
    val running = MutableStateFlow(false)
    val progress = MutableStateFlow("")
    val results = MutableStateFlow<List<ResultRow>>(emptyList())
    val lastReply = MutableStateFlow("")
    @Volatile var cancel = false

    fun say(s: String) {
        android.util.Log.i("bench", s)
        val t = SimpleDateFormat("HH:mm:ss", Locale.US).format(Date())
        log.value = (log.value + "$t $s").takeLast(400)
    }
}

class BenchRunner(private val context: Context, private val cfg: RunConfig) {
    private val wl = Workloads.load(context)
    private val store = ModelStore(context)
    val recordsFile: File = context.filesDir.resolve("records.jsonl")

    private fun utc(fmt: String, d: Date = Date()) = SimpleDateFormat(fmt, Locale.US).apply { timeZone = TimeZone.getTimeZone("UTC") }.format(d)
    private fun hex4() = ByteArray(2).also { SecureRandom().nextBytes(it) }.joinToString("") { "%02x".format(it) }

    private fun makeEngine(id: String, threads: Int): BenchEngine = when (id) {
        "llamacpp" -> LlamaCppEngine(context, threads, cfg.llamaGpu)
        "litert" -> LiteRtEngine(context, cfg.litertGpu, threads)
        "mlc" -> MlcFactory.create(context)
        "pie" -> PieFactory.create(context)
        else -> error("unknown engine $id")
    }

    fun run() {
        val threads = if (cfg.threads > 0) cfg.threads else DeviceInfo.defaultThreads()
        recordsFile.writeText("")
        BenchState.results.value = emptyList()
        val workloads = wl.workloads.filter { it.id in cfg.workloads }
        val ram = DeviceInfo.totalRamBytes(context)
        BenchState.say("run: engines=${cfg.engines} models=${cfg.models} workloads=${workloads.map { it.id }} threads=$threads tag=${cfg.tag}")
        for (model in cfg.models) {
            val runId = "phone-$model-${utc("yyyyMMdd'T'HHmmss")}-${hex4()}"
            for (engineId in cfg.engines) {
                if (BenchState.cancel) return
                val a = Catalog.find(engineId, model) ?: continue
                runCell(runId, a, engineId, workloads, threads, ram)
            }
        }
        BenchState.say("done: ${recordsFile.absolutePath} (${recordsFile.readLines().count { it.isNotBlank() }} rows)")
    }

    private class Ctx(val runId: String, val a: Artifact, val engine: BenchEngine, val local: LocalModel?, val loadS: Double?, val rssBefore: Double, val thermalStart: String)

    private fun runCell(runId: String, a: Artifact, engineId: String, workloads: List<Workload>, threads: Int, ram: Long) {
        val engine = makeEngine(engineId, threads)
        val thermalStart = DeviceInfo.thermal(context)
        val litertCpu = engineId == "litert" && !cfg.litertGpu
        fun failAll(cls: String?, status: String, msg: String, local: LocalModel? = null, loadS: Double? = null) {
            val c = Ctx(runId, a, engine, local, loadS, Mem.rssGib(), thermalStart)
            for (w in workloads) emit(c, w, status, cls, msg, emptyList(), System.currentTimeMillis(), 0.0)
        }
        if (engine.maxConcurrency == 0) {  // engine not in this APK
            BenchState.say("${a.id}: declared_unsupported: ${(engine.config().optString("unavailable_reason"))}")
            failAll(null, "declared_unsupported", engine.config().optString("unavailable_reason"))
            return
        }
        // a model clearly too big for this phone's RAM is not loaded at all
        if (a.approxBytes > ram * FIT_FRACTION) {
            val msg = "model %.2f GiB > %.0f%% of device RAM %.2f GiB".format(a.approxBytes / DeviceInfo.GIB, FIT_FRACTION * 100, ram / DeviceInfo.GIB)
            BenchState.say("${a.id}: doesnt_fit: $msg")
            failAll("doesnt_fit", "fail", msg)
            return
        }
        var local = store.local(a, litertCpu)
        if (local == null) {
            if (!cfg.download) { failAll("load_fail", "fail", "model not on device and download disabled"); return }
            BenchState.say("${a.id}: downloading ${a.repo}/${store.fileFor(a, litertCpu) ?: "*"} (~%.2f GiB)".format(a.approxBytes / DeviceInfo.GIB))
            local = runCatching {
                store.download(a, litertCpu, { f, d, t -> BenchState.progress.value = "download $f %.0f / %.0f MiB".format(d / 1048576.0, t / 1048576.0) }, { BenchState.cancel })
            }.getOrElse { failAll("load_fail", "fail", "download failed: ${it.message}"); BenchState.say("${a.id}: download failed: ${it.message}"); return }
        }
        val rssBefore = Mem.rssGib()
        BenchState.say("${a.id}: loading ${local.path.name} (${local.bytes} bytes), rss before %.2f GiB".format(rssBefore))
        val t0 = System.nanoTime()
        try {
            engine.load(a, local.path)
        } catch (t: Throwable) {
            val cls = if (t is OutOfMemoryError) "oom" else "load_fail"
            BenchState.say("${a.id}: load failed: $t")
            runCatching { engine.close() }
            failAll(cls, "fail", "load: ${t.message ?: t.toString()}", local)
            return
        }
        val loadS = (System.nanoTime() - t0) / 1e9
        BenchState.say("${a.id}: loaded in %.2f s on ${engine.backend}".format(loadS))
        val c = Ctx(runId, a, engine, local, loadS, rssBefore, thermalStart)
        val tpl = wl.templates[a.model]
        try {
            for (w in workloads) {
                if (BenchState.cancel) break
                val started = System.currentTimeMillis()
                val tw = System.nanoTime()
                if (w.concurrency > 1 && engine.maxConcurrency < w.concurrency) {
                    BenchState.say("${a.id} ${w.id}: declared_unsupported (serves one request at a time)")
                    emit(c, w, "declared_unsupported", null, "serves one request at a time", emptyList(), started, 0.0)
                    continue
                }
                if (tpl == null) { emit(c, w, "fail", "incompatible", "no chat template for ${a.model} in workloads.json", emptyList(), started, 0.0); continue }
                try {
                    val rounds = runWorkload(c, w, tpl)
                    emit(c, w, "pass", null, null, rounds, started, (System.nanoTime() - tw) / 1e9)
                } catch (t: Throwable) {
                    val cls = if (t is OutOfMemoryError || (t.message ?: "").contains("alloc", true)) "oom" else "crash"
                    BenchState.say("${a.id} ${w.id}: failed: $t")
                    emit(c, w, "fail", cls, t.message ?: t.toString(), emptyList(), started, (System.nanoTime() - tw) / 1e9)
                }
            }
        } finally {
            runCatching { engine.close() }
        }
    }

    private data class RoundOut(val wallS: Double, val peakGib: Double, val reqs: List<ReqTiming>, val peakReset: Boolean)

    private val mismatches = HashMap<String, Int>()

    private fun runWorkload(c: Ctx, w: Workload, tpl: Template): List<RoundOut> {
        val out = ArrayList<RoundOut>()
        for ((r, round) in w.rounds.withIndex()) {
            if (BenchState.cancel) error("cancelled")
            BenchState.progress.value = "${c.a.id} ${w.id} round ${r + 1}/${w.rounds.size}: warmup"
            // warmup one request at a time, as the Mac harness does
            for (p in round.warmup) c.engine.run(listOf(tpl.render(p)), w.decode, 1)
            val reset = Mem.resetPeak()
            BenchState.progress.value = "${c.a.id} ${w.id} round ${r + 1}/${w.rounds.size}: ${round.measured.size} measured"
            val prompts = round.measured.map { tpl.render(it) }
            val reqs = if (w.concurrency <= 1) prompts.flatMap { c.engine.run(listOf(it), w.decode, 1) }
                       else c.engine.run(prompts, w.decode, w.concurrency)
            val peak = Mem.hwmGib()
            // engines that do not count prompt tokens take the harness tokenizer's count
            val fixed = reqs.mapIndexed { i, q ->
                val exp = tpl.expected(w.id, r, i)
                if (q.promptTokens < 0) q.copy(promptTokens = exp)
                else { if (exp >= 0 && exp != q.promptTokens) mismatches[w.id] = (mismatches[w.id] ?: 0) + 1; q }
            }
            val wall = (fixed.maxOf { it.lastNs } - fixed.minOf { it.sendNs }) / 1e9
            out += RoundOut(wall, peak, fixed, reset)
            val m = summarize(listOf(out.last()))
            BenchState.say("${c.a.id} ${w.id} r${r + 1}: wall %.2fs decode %s tok/s prefill %s tok/s ttft %s s peak %.2f GiB".format(
                wall, fmt(m.first), fmt(m.second), fmt(m.third, 3), peak))
        }
        return out
    }

    private fun fmt(v: Double?, d: Int = 1) = v?.let { "%.${d}f".format(it) } ?: "-"

    /** Medians over requests: decode tok/s, prefill tok/s, TTFT s (display only). */
    private fun summarize(rounds: List<RoundOut>): Triple<Double?, Double?, Double?> {
        val reqs = rounds.flatMap { it.reqs }
        fun med(xs: List<Double>) = xs.sorted().takeIf { it.isNotEmpty() }?.let { if (it.size % 2 == 1) it[it.size / 2] else (it[it.size / 2 - 1] + it[it.size / 2]) / 2 }
        val dec = med(reqs.filter { it.outputTokens > 1 && it.lastNs > it.firstNs }.map { (it.outputTokens - 1) / ((it.lastNs - it.firstNs) / 1e9) })
        val pre = med(reqs.filter { it.firstNs > it.sendNs }.map { it.promptTokens / ((it.firstNs - it.sendNs) / 1e9) })
        val ttft = med(reqs.map { (it.firstNs - it.sendNs) / 1e9 })
        return Triple(dec, pre, ttft)
    }

    private fun emit(c: Ctx, w: Workload, status: String, errClass: String?, error: String?, rounds: List<RoundOut>, startedMs: Long, durS: Double) {
        val cfgJ = c.engine.config()
            .put("rss_before_load_gib", c.rssBefore)
            .put("peak_rss_reset_per_round", rounds.isNotEmpty() && rounds.all { it.peakReset })
            .put("peak_mem_source", if (rounds.isNotEmpty() && rounds.all { it.peakReset }) "VmHWM after clear_refs=5 at round start" else "VmHWM since process start")
            .put("warmup", "sequential, ${w.warmup} per round")
            .put("dispatch", if (w.concurrency > 1) "${w.concurrency} in flight (closed loop); send time = slot admission" else "one at a time")
            .put("prompt_token_mismatches", mismatches[w.id] ?: 0)
            .put("model_load", "once per engine x model; load_s shared by its rows")
        if (c.a.note != null) cfgJ.put("artifact_note", c.a.note)
        val roundsJ = JSONArray()
        for (r in rounds) {
            val reqs = JSONArray()
            for (q in r.reqs) reqs.put(JSONObject()
                .put("prompt_tokens", q.promptTokens).put("output_tokens", q.outputTokens)
                .put("ttft_s", (q.firstNs - q.sendNs) / 1e9).put("latency_s", (q.lastNs - q.sendNs) / 1e9)
                .put("cached_prompt_tokens", q.cachedPromptTokens))
            roundsJ.put(JSONObject().put("wall_s", r.wallS).put("peak_mem_gib", r.peakGib).put("requests", reqs))
        }
        val ck = c.local?.let { JSONObject().put("repo", it.repo).put("file", it.file ?: JSONObject.NULL).put("revision", it.revision ?: JSONObject.NULL).put("bytes", it.bytes) }
            ?: JSONObject().put("repo", c.a.repo).put("file", store.fileFor(c.a, c.engine.id == "litert" && !cfg.litertGpu) ?: JSONObject.NULL).put("revision", JSONObject.NULL).put("bytes", JSONObject.NULL)
        val row = JSONObject()
            .put("schema", "pie-evals-phone/1")
            .put("run_id", c.runId)
            .put("tag", cfg.tag?.ifBlank { null } ?: JSONObject.NULL)
            .put("started_at", utc("yyyy-MM-dd'T'HH:mm:ss'Z'", Date(startedMs)))
            .put("duration_s", durS)
            .put("app", JSONObject().put("version", BuildConfig.VERSION_NAME).put("harness_commit", wl.harnessCommit).put("platform", "android"))
            .put("device", DeviceInfo.json(context, c.thermalStart, DeviceInfo.thermal(context)))
            .put("engine", c.engine.id)
            .put("engine_version", c.engine.version)
            .put("engine_backend", c.engine.backend)
            .put("engine_config", cfgJ)
            .put("artifact", c.a.id)
            .put("checkpoint", ck)
            .put("workload", w.id)
            .put("status", status)
            .put("error_class", errClass ?: JSONObject.NULL)
            .put("error", error ?: JSONObject.NULL)
            .put("load_s", c.loadS ?: JSONObject.NULL)
            .put("rounds", roundsJ)
        recordsFile.appendText(row.toString() + "\n")
        val m = summarize(rounds)
        BenchState.results.value = BenchState.results.value + ResultRow(c.engine.id, c.a.id, w.id, status, m.first, m.second, m.third,
            rounds.maxOfOrNull { it.peakGib }, error)
    }

    companion object {
        /** A model whose file is over this share of total RAM is reported doesnt_fit without loading. */
        const val FIT_FRACTION = 0.7
    }
}
