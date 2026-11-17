package org.pieevals.phonebench

/**
 * One matrix artifact (ids are fixed; the ingest server checks them).
 * `file` = the single file to download; null = the whole repo (MLC weight dirs, pie artifacts).
 */
data class Artifact(
    val id: String,
    val engine: String,
    val model: String,          // site model id, keys workloads.json templates
    val repo: String,
    val file: String?,
    val approxBytes: Long,
    val format: String,
    val cpuFile: String? = null, // LiteRT: the CPU build of the same model when `file` is the GPU one
    val note: String? = null,
)

object Catalog {
    /** pie .vulkan.zt files are made on a Mac with `pie model import` and are not hosted: adb push or pick the file. */
    const val PIE_NOTE = "made by `pie model import --deployment <sku>` from the MLX 4-bit checkpoint"
    fun downloadable(a: Artifact) = a.engine != "pie"

    val engines = listOf("llamacpp", "litert", "mlc", "pie")
    val models = listOf("qwen3.5-0.8b", "qwen3.5-4b", "gemma-4-e2b", "gemma-4-e4b", "gemma-4-12b")

    val artifacts: List<Artifact> = listOf(
        // llama.cpp: GGUF Q4_K_M (sizes from the HF API)
        Artifact("qwen3.5-0.8b-llamacpp", "llamacpp", "qwen3.5-0.8b", "unsloth/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_K_M.gguf", 532_517_120, "GGUF Q4_K_M"),
        Artifact("qwen3.5-4b-llamacpp", "llamacpp", "qwen3.5-4b", "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-Q4_K_M.gguf", 2_740_937_888, "GGUF Q4_K_M"),
        Artifact("gemma-4-e2b-llamacpp", "llamacpp", "gemma-4-e2b", "unsloth/gemma-4-E2B-it-GGUF", "gemma-4-E2B-it-Q4_K_M.gguf", 3_106_738_272, "GGUF Q4_K_M"),
        Artifact("gemma-4-e4b-llamacpp", "llamacpp", "gemma-4-e4b", "unsloth/gemma-4-E4B-it-GGUF", "gemma-4-E4B-it-Q4_K_M.gguf", 4_977_171_584, "GGUF Q4_K_M"),
        Artifact("gemma-4-12b-llamacpp", "llamacpp", "gemma-4-12b", "unsloth/gemma-4-12b-it-GGUF", "gemma-4-12b-it-Q4_K_M.gguf", 7_121_861_440, "GGUF Q4_K_M"),
        // LiteRT-LM: .litertlm (GPU build where the repo has one)
        Artifact("gemma-4-e2b-litert", "litert", "gemma-4-e2b", "litert-community/gemma-4-E2B-it-litert-lm", "gemma-4-E2B-it.litertlm", 2_588_147_712, ".litertlm (Android/iOS build; -gpu is the Web one)"),
        Artifact("gemma-4-e4b-litert", "litert", "gemma-4-e4b", "litert-community/gemma-4-E4B-it-litert-lm", "gemma-4-E4B-it.litertlm", 3_659_530_240, ".litertlm (Android/iOS build; -gpu is the Web one)"),
        Artifact("gemma-4-12b-litert", "litert", "gemma-4-12b", "litert-community/gemma-4-12B-it-litert-lm", "gemma-4-12B-it.litertlm", 6_883_278_368, ".litertlm (Android/iOS build; -gpu is the Web one)"),
        Artifact("qwen3.5-0.8b-litert", "litert", "qwen3.5-0.8b", "litert-community/Qwen3.5-0.8B", "Qwen3.5-0.8B_int8_gpu_composite_v0190.litertlm", 888_373_248, ".litertlm int8, GPU composites", cpuFile = "Qwen3.5-0.8B_int8.litertlm", note = "int8 weights (the repo has no 4-bit text build), not 4-bit"),
        Artifact("qwen3.5-4b-litert", "litert", "qwen3.5-4b", "litert-community/Qwen3.5-4B", "Qwen3.5-4B_mixed_int4_gpu_composite_v0190.litertlm", 2_712_846_336, ".litertlm mixed int4, GPU composites", cpuFile = "Qwen3.5-4B_int8.litertlm"),
        // MLC LLM: prebuilt weight dirs (model libraries compiled into the APK)
        Artifact("qwen3.5-4b-mlc", "mlc", "qwen3.5-4b", "mlc-ai/Qwen3.5-4B-q4f16_1-MLC", null, 2_400_000_000, "MLC q4f16_1"),
        Artifact("gemma-4-e2b-mlc", "mlc", "gemma-4-e2b", "mlc-ai/gemma-4-E2B-it-q4f16_1-MLC", null, 3_000_000_000, "MLC q4f16_1"),
        Artifact("qwen3.5-0.8b-mlc", "mlc", "qwen3.5-0.8b", "mlc-ai/Qwen3.5-0.8B-q4f32_1-MLC", null, 450_000_000, "MLC q4f32_1"),
        // pie: .vulkan.zt artifacts made by `pie model import` from the MLX 4-bit checkpoints
        Artifact("qwen3.5-0.8b-mlx4", "pie", "qwen3.5-0.8b", "mlx-community/Qwen3.5-0.8B-4bit", "mlx-community--qwen3-5-0-8b-4bit.qwen35-d0-8b-u4g64-kv-bf16.vulkan.zt", 440_571_887, "pie .vulkan.zt (u4g64, kv bf16)", note = PIE_NOTE + "; pie_sku qwen35-d0.8b-u4g64-kv-bf16"),
        Artifact("qwen3.5-4b-mlx4", "pie", "qwen3.5-4b", "mlx-community/Qwen3.5-4B-4bit", "mlx-community--qwen3-5-4b-4bit.qwen35-d4b-u4g64-kv-bf16.vulkan.zt", 2_386_086_219, "pie .vulkan.zt (u4g64, kv bf16)", note = PIE_NOTE + "; pie_sku qwen35-d4b-u4g64-kv-bf16"),
        Artifact("gemma-4-e2b-mlx4", "pie", "gemma-4-e2b", "mlx-community/gemma-4-e2b-it-4bit", "mlx-community--gemma-4-e2b-it-4bit.gemma4-e2b-u4g64-kv-bf16.vulkan.zt", 2_634_036_933, "pie .vulkan.zt (u4g64, kv bf16)", note = PIE_NOTE),
        Artifact("gemma-4-e4b-mlx4", "pie", "gemma-4-e4b", "mlx-community/gemma-4-e4b-it-4bit", "mlx-community--gemma-4-e4b-it-4bit.gemma4-e4b-u4g64-kv-bf16.vulkan.zt", 4_230_641_444, "pie .vulkan.zt (u4g64, kv bf16)", note = PIE_NOTE),
        Artifact("gemma-4-12b-mlx4", "pie", "gemma-4-12b", "mlx-community/gemma-4-12B-it-4bit", "mlx-community--gemma-4-12b-it-4bit.gemma4-12b-u4g64-kv-bf16.vulkan.zt", 6_740_787_292, "pie .vulkan.zt (u4g64, kv bf16)", note = PIE_NOTE),
    )

    fun find(engine: String, model: String) = artifacts.firstOrNull { it.engine == engine && it.model == model }
    fun byId(id: String) = artifacts.firstOrNull { it.id == id }
}
