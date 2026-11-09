"""SGLang adapter: drives ``bench/sglang_bench.py``.

The one flag that must never be left to the engine's default is
``--sglang-cuda-graph-max-bs``: SGLang derives its graph ceiling from a
hardware-tier heuristic and a decode batch beyond it silently runs eager
(4,642 vs 14,042 tok/s on the same cell). It is always set to the shape's
concurrency, the way vLLM captures up to ``max_num_seqs``.
"""

from __future__ import annotations

import os
import subprocess

from pie_evals.schema import EngineName, WorkloadSpec

from .base import Engine, register
from .served import ServedEngine
from .shape import max_model_len_for, workload_concurrency


@register
class SglangEngine(Engine):
    name = EngineName.SGLANG
    script = "sglang_bench.py"
    #: the runner image has no nvcc: DeepGEMM's JIT (gemma / gpt-oss on
    #: Blackwell, nightly 35921789513) would abort every cell; the FlashInfer
    #: kernels come precompiled (baselines.ensure_flashinfer_aot).
    env_defaults = {"SGL_ENABLE_JIT_DEEPGEMM": "0", "SGLANG_ENABLE_JIT_DEEPGEMM": "0"}  # 0.5.20 reads the second, warns on the first

    def __new__(cls, *args, **kwargs):
        # the TPU build (sglang-jax) has no offline engine sglang_bench.py can drive: it is served
        platform = kwargs.get("platform")
        if cls is SglangEngine and platform is not None and str(platform.backend) == "xla":
            return SglangTpuEngine(*args, **kwargs)  # not an SglangEngine: Python skips __init__ on the return
        return super().__new__(cls)

    def default_env(self) -> dict[str, str]:
        # sgl_kernel_jit builds land on the volume instead of the pod's
        # container disk, so a kernel compiles once per (version, arch)
        from pie_evals.node.baselines import cache_root

        jit = cache_root() / "jit"
        env = {
            "SGLANG_JIT_CACHE_DIR": str(jit / "sglang"),
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            # FlashAttention 4's CuTe DSL kernels kept on the volume too, as vLLM's
            "FLASH_ATTENTION_CUTE_DSL_CACHE_ENABLED": "1",
            "FLASH_ATTENTION_CUTE_DSL_CACHE_DIR": str(jit / "cute_dsl"),
            **self.nccl_env(),
        }
        # sglang_bench.py has no flag for disable_custom_all_reduce and SGLang reads no env for
        # it. On the L40S x2 pod the custom kernel hung Qwen3.5-0.8B and died with "unspecified
        # launch failure" on Qwen3.6-27B (weekly 39545360541)
        env.update(self.no_peer_env())
        if self.artifact.family == "deepseek_v41" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" not in str(self.platform.accelerator):
            # on sm_100 0.5.22 scores DeepSeek-V4.1's candidate indexer only through DeepGEMM's JIT paged sparse
            # MQA logits ("the candidate indexer needs DeepGEMM's paged sparse MQA logits", b200-x1); the pod has nvcc
            env["SGLANG_ENABLE_JIT_DEEPGEMM"] = env["SGL_ENABLE_JIT_DEEPGEMM"] = "1"
        if self.artifact.id == "gpt-oss-120b-mxfp4" and self.platform is not None and str(self.platform.arch) == "hopper" and float(self.platform.memory_gib or 0) <= 80:
            # 0.5.22 swizzles gpt-oss-120b's MXFP4 experts for triton_kernels at load, and the swizzle's temporaries
            # fragment the caching allocator past what an 80 GB card holds ("Tried to allocate 1.03 GiB", 8.3 GiB
            # reserved but unallocated, h100-sxm-x1); with expandable segments it loads (raw decode 206 tok/s)
            env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        return env

    def default_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        # on ROCm the AMD image's own SGLang (baselines.BACKEND_SPECS)
        backend = str(self.platform.backend) if self.platform is not None else None
        py = baseline_python("sglang", pin, backend=backend) if pin else None
        return str(py) if py else "/root/.venv/sglang/bin/python"

    def model_arg(self) -> str:
        # The runner resolves the checkpoint (a miniature lives under a snapshot
        # dir with no refs/main, so an HF id would not find it) and passes the
        # path through the recipe; a bare HF id is the fallback.
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args: list[str] = ["--tp-size", str(max(1, int(self.mode.tp)))]
        gmu = r.get("gpu_mem_util", 0.90)
        card = float(self.platform.memory_gib or 0.0) / max(1, int(self.mode.tp))
        if gmu is not None:
            # SGLang counts the loaded weights against mem_fraction_static and refuses when
            # they leave no KV room under it (kimi-k3 mini, 18.4 GiB on a 32 GB 5090: "raise
            # --mem-fraction-static above 0.935"); a heavy checkpoint gets the fraction it needs
            weights = float(self.artifact.expected_gib or 0.0)
            # Qwen3.8-27B bf16 (52% of a 96 GB card, 63% of an 80 GB one) keeps 0.9: at 0.95 its prefill graphs fail
            # to capture (pf8-pf32; on the H100 "num_active_captures_ > 0" at pf4-pf32, c16, c32)
            # the 19.4 GiB Muse Glimmer mini12 (61% of a 32 GB 5090) at 0.95 OOMed past the static pool at pf16-512 and c64
            if weights and card and weights / card > 0.5 and not (self.artifact.family in ("qwen3_6", "muse_glimmer") and weights / card < 0.65):
                gmu = max(float(gmu), 0.95)
            elif self.artifact.family == "kimi_k3":
                # past the static pool SGLang keeps only graphs and activations; Kimi-K3's MoE
                # prefill wanted 1.5 GiB more than 0.85 left on 80/96 GB cards (nightly 36103857543)
                # and OOMs from c32 at 0.9 on a 48 GB L40S (36226636518), while the L40S at 0.75
                # has no KV left beside a 256-wide graph (36212036845) and at 0.82 kv-oversub OOMs in prefill (36264810212)
                wide = card < 80 and workload_concurrency(workload) >= 128
                gmu = min(float(gmu), 0.79 if wide else 0.75)
                if card < 48:
                    # the 12 GiB one-period Kimi-K3 mini on a 32 GB RTX 5090: at 0.75 its Triton fused MoE
                    # asked 710 MiB past the static pool at c64-c256 and every pf cell (365 MiB free)
                    gmu = min(float(gmu), 0.6)
            elif self.artifact.family == "deepseek_v4" and card < 80 and str(self.platform.arch) in ("ada", "ampere"):
                # below sm_90 the fork runs DeepSeek-V4 attention and indexer on Triton/torch fallbacks whose
                # activations live past the static pool: at 0.9 c512 and pf16-512 OOMed on the L40S
                gmu = min(float(gmu), 0.75)
            elif self.artifact.family in ("glm5_next", "qwen4_exp"):
                # 0.5.22 captures piecewise prefill graphs past the static pool, and the linear-attention
                # layers' chunk state makes them large: GLM-5.3-Flash's 2048-token graph took 5.7 GiB and
                # OOMed at 0.9 on an 80 GB H100 (weekly 40415495702; its c256 passed under the 0.80 cap
                # below), Qwen3.8-Flash-Next OOMed at 0.9 on a 24 GB 4090 (40421366253). vLLM's 0.9
                # already holds its graphs and activations; this keeps SGLang's inside the same card
                gmu = min(float(gmu), 0.85 if card >= 80 else 0.75)
            if self.platform.id == "l4-x1":
                # a 24 GB L4 keeps 3.4 GiB past the static pool for SGLang's graphs and activations: the 13 GiB
                # Qwen3.6-35B-A3B mini took 0.95 above and every c/pf graph capture failed ("num_active_captures_ > 0")
                gmu = min(float(gmu), 0.85)
            if self.artifact.id == "gpt-oss-120b-mxfp4" and str(self.platform.arch) == "ampere" and card >= 80:
                # gpt-oss-120b (61 GiB, 76% of an 80 GB A100) took the 0.95 above, and its Marlin MoE prefill graphs
                # OOMed capturing past the static pool at pf8/pf16-512 (184 MiB asked, 45 MiB free, a100-sxm-x1); pf64 served at 0.85
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "qwen3_6" and str(self.platform.arch) == "ampere" and card >= 80 and weights / card < 0.7:
                # Qwen3.6-27B bf16 (54 GiB, 68% of an 80 GB A100) took the 0.95 above, and its prefill OOMed past the
                # static pool at pf4/pf16-512 (272 MiB asked, 67 MiB free, a100-sxm-x1); 0.9, as Qwen3.8-27B keeps
                gmu = min(float(gmu), 0.9)
            if self.artifact.family in ("minimax_m3", "glm_moe_dsa") and card >= 80:
                # MiniMax-M3.1-Flash mini60-e16 (43.4 GiB, 54% of an 80 GB H100) took the 0.95 above and its
                # block-FP8 Triton prefill OOMed at pf8 past the static pool (347 MiB free); 0.88 leaves room
                # GLM-5.3 mini78-e12 (51 GiB) likewise OOMed in FA3 prefill at pf16/pf32-512 at 0.95
                gmu = min(float(gmu), 0.88)
            if self.artifact.family in ("glm_moe_dsa", "hy_v4", "minimax_m3") and card < 48:
                # the GLM-5.3 mini at 0.9 on a 32 GB RTX 5090 left 2.55 GB past the static pool, and its
                # 2048-token piecewise prefill graph OOMed capturing the MLA bmm buffers (every cell); 0.8 leaves it room.
                # The Hy4 mini OOMed the same way (2.54 GB free, radix attention output), the MiniMax-M3.1 mini at its
                # 4096-token graph (2.40 GB free, c64-c256 and every pf cell)
                gmu = min(float(gmu), 0.80)
            if self.artifact.family == "deepseek_v4" and str(self.platform.arch) == "hopper":
                # the 5-layer DeepSeek-V4-Flash mini leaves 0.9 of an H100 to KV, and FlashInfer's CUTLASS MoE
                # workspace for a 4096-token prefill OOMed past it (pf8-512, h100-sxm-x1)
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "muse_spark" and card <= 80:
                # Muse Spark mini4 (12 GiB) at 0.9 on an 80 GB H100: its pf16/pf32-512 prefill OOMed past
                # the static pool (512 MiB asked, 115 MiB free); pf64 and up passed. 0.85 leaves the activations room.
                # A 32 GB RTX 5090 at 0.85 still OOMed every c and pf cell (512 MiB asked, 199 MiB free): 0.75 there
                gmu = min(float(gmu), 0.85 if card >= 48 else 0.75)
            if card < 80 and workload_concurrency(workload) >= 512:
                # a 512-wide decode graph and batch OOM past the static pool at 0.9 on a 48 GB L40S
                # (Hy4 mini c512 / pf512-512: 160-190 MiB free); 0.85 leaves them room
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "nemotron_h" and 40 <= card < 80:
                # the Nemotron-3-Ultra mini's Triton fused MoE prefill asked 842-874 MiB past the static pool at 0.9 on a
                # 48 GB A40, with 111-187 MiB free (c256, pf16-512); its c256 and c512 passed at 0.85
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "muse_glimmer" and card < 80 and (workload_concurrency(workload) >= 128 or card <= 32):
                # the 27 GiB Muse Glimmer miniature's 256-wide batches OOM past the static pool at 0.95
                # on a 48 GB L40S (150-200 MiB free); 0.85 still holds the weights and the batch's KV. On a 32 GB
                # card its 12-layer mini (19.4 GiB) OOMed at 0.95 at every shape below c128 too (pro4500-x1)
                gmu = 0.85
            if self.artifact.family == "glm5_next" and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator) and card >= 80:
                # the TileLang DSA kernels (below) want more than 0.95 leaves past the static pool: GLM-5.3-Flash
                # OOMed by 72 MiB on the 96 GB card (weekly 39904326176); a 768-token cell needs little KV.
                # A 32 GB RTX 5090 keeps the 0.75 above: at 0.88 the 2048-token prefill graph OOMed (2.95 GB free)
                gmu = 0.88
            if self.artifact.family in ("glm5_next", "hy_v4", "muse_spark") and card <= 32:
                # 0.9 of a 32 GB card leaves 3 GiB past the static pool, and the GLM-5.3-Flash, Hy4 and Muse Spark minis'
                # prefill OOMed there (9 / 25 MiB free at 0.9, Muse Spark 230 MiB at 0.85; pro4500-x1)
                gmu = min(float(gmu), 0.78)
            if self.artifact.family == "qwen3_6_moe" and card <= 32:
                # the Qwen3.6-35B-A3B mini (20.4 GiB, 64% of a 32 GB card) took the 0.95 above and its prefill graphs
                # failed to capture past the static pool ("num_active_captures_ > 0", pro4500-x1 raw-512-256)
                gmu = min(float(gmu), 0.88)
            if self.artifact.family == "nemotron_h" and card <= 32:
                # the 18.9 GiB Nemotron-3-Ultra mini at 0.9 of a 32 GB RTX 5090 left its 1.2 GiB prefill buffers no room past
                # the static pool, and every batch failed and retried them (pf64-512: 2.9k tok/s); at 0.85 it runs clean (19.3k)
                gmu = min(float(gmu), 0.85)
            if self.platform.id == "rtx4090-x1":
                # 0.5.22 captures its piecewise prefill graphs past the static pool, and on a 24 GB card the
                # 10% left at 0.9 does not hold them (GLM-5.3 and Hy4 minis raw: OOM capturing at 36 MiB free);
                # 0.80 keeps the graphs, a checkpoint over 60% of the card the 0.85 its weights and KV need
                gmu = min(float(gmu), 0.85 if weights / card > 0.6 else 0.80)
                if self.artifact.family == "kimi_k3":
                    # the Kimi-K3 mini's MoE prefill wants 754 MiB more than 0.75 leaves (pf16-512 and c512 OOM)
                    gmu = min(float(gmu), 0.70)
            args += ["--gpu-mem-util", str(gmu)]  # -> mem_fraction_static
        graph_bs = r.get("cuda_graph_max_bs")
        if graph_bs is None:
            graph_bs = workload_concurrency(workload)
        if gmu is not None and card >= 80 and int(graph_bs) >= 64:
            # mem_fraction_static leaves the graphs and activations whatever is past it; on a
            # 96 GB card at 0.9 that was 9.5 GiB, and kimi-k3 mini at c64 wanted 1.2 GiB more
            # (nightly 36089882075 s04: OOM at c64, c256, mixed, prefix; c32 served)
            # a checkpoint over half the card keeps 0.85: at 0.80 Qwen3.6-35B-A3B bf16 (65 GB) left no KV on the 96 GB card
            capped = 0.80 if int(graph_bs) >= 256 and float(self.artifact.expected_gib or 0.0) / card <= 0.5 else 0.85
            if self.artifact.id == "gpt-oss-120b-mxfp4" and str(self.platform.arch) == "hopper" and card <= 80:
                # its weights alone take 0.896 of an 80 GB H100 under SGLang ("Raise --mem-fraction-static above
                # 0.896", h100-sxm-x1 c128): it keeps the 0.95 every heavy checkpoint gets, as its raw cells do
                capped = float(gmu)
            if float(gmu) > capped:
                args[-1] = str(capped)
        args += ["--max-model-len", str(max_model_len_for(workload))]  # -> context_length
        args += ["--sglang-cuda-graph-max-bs", str(int(graph_bs))]

        if r.get("report_timing", True):
            args += ["--report-timing"]
        if r.get("attention_backend"):
            args += ["--sglang-attention-backend", str(r["attention_backend"])]
        dsa = r.get("dsa_backend")
        if dsa is None and self.artifact.family == "glm5_next" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            # 0.5.22 picks trtllm-gen MLA for a bf16 KV cache on SM120, an SM100-only kernel ("TllmGenFmhaRunner:
            # Unsupported architecture", GLM-5.3-Flash on pro6000-x4, weekly 39901346624); TileLang runs on SM120
            dsa = "tilelang"
        blackwell = self.platform is not None and str(self.platform.arch) == "blackwell"
        rtx_blackwell = blackwell and "RTX" in str(self.platform.accelerator)
        # DeepSeek-V4's pool stores only the FP8 FlashMLA page layout ("assert self.store_dtype == torch.uint8" at a
        # bf16 KV, every cell on pro4500-x1 and b200-x1): it keeps the fp8 KV SGLang deploys it with
        if self.artifact.family in ("glm_moe_dsa", "glm5_next", "hy_v4") and blackwell:
            # 0.5.22 stores a DSA model's KV cache in fp8_e4m3 on SM100 and up (SM120 too), and DeepSeek-V4's on every
            # GPU; bf16 is the precision pie and vLLM serve: GLM-5.3 mini pf256-512 66k tok/s with fp8 KV, 26.7k with
            # bf16 (pro6000-x1)
            args += ["--sglang-kv-cache-dtype", "bfloat16"]
            if dsa is None and self.artifact.family == "glm_moe_dsa" and rtx_blackwell:
                # at a bf16 KV, trtllm-gen MLA is SM100-only and TileLang's sparse prefill wants 231 KB of shared memory
                dsa = "flashmla_sparse"
        if dsa:
            args += ["--sglang-dsa-backend", str(dsa)]
        moe = r.get("moe_runner_backend")
        if moe is None and self.artifact.family == "deepseek_v41" and int(self.mode.tp) == 4:
            # its auto pick, flashinfer_mxfp4, refuses a tp4 share of the experts ("hidden_size and
            # intermediate_size_per_partition to be multiples of 128 (got hidden=5120, intermediate=576)",
            # h200-x4 weekly 39999127297); Marlin is SGLang's other MXFP4 MoE runner
            moe = "marlin"
        if moe is None and self.artifact.family == "gpt_oss" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            # 0.5.22's auto pick on SM120, flashinfer_mxfp4 (cutlass_sm120), quantizes the activations to MXFP8
            # (MXFP8 x MXFP4); Marlin keeps them bf16 (W4A16), the precision pie and vLLM serve gpt-oss at.
            # triton_kernel, the other bf16 runner, fails there ("persistent kernel is required", pro6000-x1)
            moe = "marlin"
        if moe is None and self.artifact.family == "gpt_oss" and self.platform is not None and str(self.platform.arch) == "ampere":
            # 0.5.22's auto pick below sm_90 dequantizes every expert each forward (A100: TTFT 1.8 s at 600 tokens,
            # pf64-512 hangs past 600 s); Marlin is its W4A16 MXFP4 runner, the one vLLM picks on Ampere
            moe = "marlin"
        if moe is None and self.artifact.family == "kimi_k3" and blackwell and not rtx_blackwell:
            # 0.5.22's auto pick on SM100, flashinfer_mxfp4 (trtllm-gen), quantizes the activations to MXFP8, and
            # trtllm-gen has no bf16-activation kernel for Kimi-K3's experts ("No kernel found ... mDtypeB: Bfloat16");
            # Marlin keeps them bf16 (W4A16), as the release declares and pie serves (the triton kernels have no SITU)
            moe = "marlin"
        if moe is None and self.artifact.family == "nemotron_h" and self.platform is not None and str(self.platform.backend) == "rocm":
            # 0.5.22 resolves NemotronH's auto MoE runner to flashinfer_cutlass, which needs FlashInfer, a CUDA-only
            # library the ROCm image does not ship ("flashinfer_cutlass MoE runner backend requires flashinfer to be
            # installed", mi300x-x1); triton is its ROCm runner for these bf16 experts
            moe = "triton"
        if moe:
            args += ["--sglang-moe-runner-backend", str(moe)]
        if moe is None and self.artifact.family == "gpt_oss" and blackwell and not rtx_blackwell:
            # 0.5.22's auto pick on SM100, flashinfer_mxfp4 (trtllm-gen), quantizes the activations to MXFP8
            # (MXFP8 x MXFP4); its bf16 precision keeps them bf16 (W4A16), as pie and vLLM serve gpt-oss
            args += ["--sglang-flashinfer-mxfp4-moe-precision", "bf16"]
        if r.get("sampling_backend"):
            args += ["--sglang-sampling-backend", str(r["sampling_backend"])]
        if r.get("page_size"):
            args += ["--sglang-page-size", str(int(r["page_size"]))]
        if r.get("max_total_tokens"):
            args += ["--sglang-max-total-tokens", str(int(r["max_total_tokens"]))]
        if r.get("disable_cuda_graph"):
            args.append("--sglang-disable-cuda-graph")
        piecewise_off = r.get("disable_piecewise_cuda_graph")
        if piecewise_off is None and self.artifact.family in ("minimax_m3", "glm_moe_dsa", "hy_v4") and self.platform is not None and str(self.platform.arch) == "ampere":
            # 0.5.22 spends minutes per piecewise prefill shape compiling these models' sm_80 fallbacks (GLM-5.3 mini: 18 s a shape) (36 of 42 in
            # 5:51 on an A100, the bench's 180 s no-CPU-work stop kills it); decode graphs still capture
            piecewise_off = True
        if piecewise_off:
            args.append("--sglang-disable-piecewise-cuda-graph")

        hybrid_swa = r.get("disable_hybrid_swa_memory")
        if hybrid_swa is None:
            # Sliding-window families (Gemma): SGLang's hybrid sizer derives a
            # budget from the SWA layers and then refuses to start because the
            # full-attention layers cannot hold it (common.py's flag help).
            # One uniform pool is what vLLM does, so it is the comparable
            # policy as well as the one that runs.
            hybrid_swa = self.artifact.family.startswith("gemma")
        if hybrid_swa:
            args.append("--sglang-disable-hybrid-swa-memory")

        # TODO(pie/benches): sglang_bench.py hard-codes disable_radix_cache=True
        # and has no flag to enable it, so the prefix_shared shape cannot hand
        # SGLang its prefix cache (recipe knob `radix_cache` is recorded only).
        # TODO(pie/benches): no --sglang-enable-torch-compile flag (recipe knob
        # `torch_compile` is recorded only).

        if r.get("cpu_affinity"):
            args += ["--cpu-affinity", str(r["cpu_affinity"])]
        if r.get("request_timeout"):
            args += ["--request-timeout", str(r["request_timeout"])]
        return args

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.python, "-c", "import sglang; print(sglang.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["sglang::scheduler", "sglang::detokenizer", "sglang::scheduler_TP0"]


class SglangTpuEngine(ServedEngine):
    """SGLang's TPU build: ``python -m sgl_jax.launch_server`` (sgl-project/sglang-jax, at the
    engines.yaml backend pin) on the bf16 checkpoint, streamed through ``openai_bench.py`` the way
    llama.cpp and mlx-lm are. Its warmup and JIT precompile run before the server answers."""

    name = EngineName.SGLANG
    health_path = "/health"
    exact_length = "ignore_eos"

    def server_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        py = baseline_python("sglang", pin, backend="xla") if pin else None
        return str(py) if py else "python3"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def api_model(self) -> str:
        # sgl_jax's CompletionRequest requires ``model`` (tpu b5 39575054600: 400 on every request)
        return self.model_arg()

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        if r.get("max_running_requests"):  # the recurrent state slots one chip holds (recipe rationale)
            slots = min(slots, int(r["max_running_requests"]))
        cmd = [
            self.server_python(), "-m", "sgl_jax.launch_server", "--model-path", self.model_arg(),
            "--host", "127.0.0.1", "--port", str(port), "--device", "tpu", "--tp-size", str(max(1, int(self.mode.tp))),
            "--context-length", str(context), "--max-running-requests", str(slots),
            # a cold prompt every request, as on every other engine
            "--disable-radix-cache", "--log-level", "warning",
            # a checkpoint with custom code (MiMo-V2.6-Flash) is refused at config load without it, as vLLM is given it
            "--trust-remote-code",
        ]
        if r.get("gpu_mem_util") is not None:
            cmd += ["--mem-fraction-static", str(r["gpu_mem_util"])]
        if r.get("page_size"):
            cmd += ["--page-size", str(int(r["page_size"]))]
        if r.get("chunked_prefill_size"):
            cmd += ["--chunked-prefill-size", str(int(r["chunked_prefill_size"]))]
        return cmd

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "import sgl_jax; print(sgl_jax.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            pin = str(self.recipe.get("pin") or "")
            if pin.startswith("git-"):  # a commit's build reports no release of its own (setuptools-scm's fallback)
                return pin
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["sglang::scheduler", "sglang::detokenizer", "sgl_jax"]
