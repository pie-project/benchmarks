package org.pieevals.phonebench.engines

import android.content.Context
import org.json.JSONObject
import org.pieevals.phonebench.Artifact
import org.pieevals.phonebench.BuildConfig
import java.io.File

object LlamaNative {
    @Volatile private var ready = false

    fun ensure(context: Context) {
        if (ready) return
        synchronized(this) {
            if (ready) return
            System.loadLibrary("benchllama")
            init(context.applicationInfo.nativeLibraryDir)
            ready = true
        }
    }

    @JvmStatic external fun init(libDir: String)
    @JvmStatic external fun systemInfo(): String
    @JvmStatic external fun gpuDevices(): String
    @JvmStatic external fun load(path: String, nCtx: Int, nBatch: Int, nUbatch: Int, nThreads: Int, nSeq: Int, nGpuLayers: Int, flashAttn: Boolean): Long
    @JvmStatic external fun modelDesc(handle: Long): String
    @JvmStatic external fun run(handle: Long, prompts: Array<String>, maxNew: Int, slots: Int, ignoreEos: Boolean): LongArray
    @JvmStatic external fun free(handle: Long)
}

class LlamaCppEngine(private val context: Context, private val threads: Int, private val wantGpu: Boolean) : BenchEngine {
    override val id = "llamacpp"
    override val version = BuildConfig.LLAMA_CPP_TAG
    override val maxConcurrency = SLOTS
    private var handle = 0L
    private var desc = ""
    private var gpu = ""

    private val gpuBuild = BuildConfig.LLAMA_GPU != "none"
    private val useGpu get() = wantGpu && gpuBuild
    override val backend: String
        get() = if (useGpu) BuildConfig.LLAMA_GPU else "cpu"

    override fun config(): JSONObject = JSONObject()
        .put("n_ctx", N_CTX_PER_SLOT * SLOTS)
        .put("n_ctx_per_slot", N_CTX_PER_SLOT)
        .put("n_seq_max", SLOTS)
        .put("kv_unified", false)
        .put("n_batch", N_BATCH)
        .put("n_ubatch", N_UBATCH)
        .put("n_threads", threads)
        .put("n_gpu_layers", if (backend == "cpu") 0 else 99)
        .put("flash_attn", true)
        .put("sampler", "greedy argmax, end-of-generation tokens masked (ignore_eos)")
        .put("prompt", "raw text prefix+user+suffix, tokenized with parse_special on, no BOS added")
        .put("cache_prompt", false)
        .put("batching", "continuous: up to n_seq_max sequences share one llama_batch")
        .put("ggml_cpu", "GGML_CPU_ALL_VARIANTS + GGML_BACKEND_DL (best arm64 variant picked at load), KleidiAI on")
        .put("op_offload", useGpu)
        .put("gpu_backend_in_apk", BuildConfig.LLAMA_GPU)
        .put("gpu_devices", gpu)
        .put("model_desc", desc)
        .put("system_info", runCatching { LlamaNative.systemInfo() }.getOrDefault(""))

    override fun load(artifact: Artifact, model: File) {
        LlamaNative.ensure(context)
        gpu = runCatching { LlamaNative.gpuDevices() }.getOrDefault("")
        if (wantGpu && !gpuBuild) throw IllegalStateException("this APK has no llama.cpp GPU backend")
        if (useGpu && gpu.isEmpty()) throw IllegalStateException("no ${BuildConfig.LLAMA_GPU} GPU device found by ggml")
        val ngl = if (useGpu) 99 else 0
        handle = LlamaNative.load(model.absolutePath, N_CTX_PER_SLOT * SLOTS, N_BATCH, N_UBATCH, threads, SLOTS, ngl, true)
        desc = LlamaNative.modelDesc(handle)
    }

    override fun run(prompts: List<String>, maxNew: Int, concurrency: Int): List<ReqTiming> {
        val a = LlamaNative.run(handle, prompts.toTypedArray(), maxNew, concurrency, true)
        return prompts.indices.map { i ->
            ReqTiming(a[i * 5].toInt(), a[i * 5 + 1].toInt(), a[i * 5 + 2], a[i * 5 + 3], a[i * 5 + 4])
        }
    }

    override fun close() {
        if (handle != 0L) LlamaNative.free(handle)
        handle = 0L
    }

    companion object {
        const val SLOTS = 4
        const val N_CTX_PER_SLOT = 1024
        const val N_BATCH = 2048
        const val N_UBATCH = 512
    }
}
