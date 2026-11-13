from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class StrEnumBase(StrEnum):
    def __str__(self) -> str:
        return self.value


class EngineName(StrEnumBase):
    PIE = "pie"
    VLLM = "vllm"
    SGLANG = "sglang"
    TRTLLM = "trtllm"
    LLAMACPP = "llamacpp"
    MLXLM = "mlxlm"
    VLLM_METAL = "vllm-metal"
    SPLASH = "splash"
    LITERT = "litert"
    MLC = "mlc"
    MLX_SWIFT = "mlx-swift"
    WEBLLM = "webllm"
    LLAMACPP_WEBGPU = "llamacpp-webgpu"
    OLLAMA = "ollama"


class Backend(StrEnumBase):

    CUDA = "cuda"
    METAL = "metal"
    VULKAN = "vulkan"
    WGPU = "wgpu"
    XLA = "xla"
    WEBGPU = "webgpu"
    ROCM = "rocm"


class QuantScheme(StrEnumBase):
    BF16 = "bf16"
    FP8 = "fp8"
    MXFP4 = "mxfp4"
    AFFINE_U4_G64 = "affine_u4_g64"
    MLX_2BIT = "mlx_2bit"
    W4A16_MARLIN = "w4a16_marlin"
    GGUF_Q4_K_M = "gguf_q4_k_m"
    GGUF_Q2_K = "gguf_q2_k"
    GGUF_Q2_0 = "gguf_q2_0"
    GGUF_Q8_0 = "gguf_q8_0"
    GGUF_UD_Q4_K_XL = "gguf_ud_q4_k_xl"
    AWQ = "awq"
    GPTQ = "gptq"
    NVFP4 = "nvfp4"
    LITERT_INT4 = "litert_int4"
    LITERT_INT8 = "litert_int8"
    LITERT_MIXED = "litert_mixed"
    MLC_Q4F16_1 = "mlc_q4f16_1"
    MLC_Q4F32_1 = "mlc_q4f32_1"


class SourceFormat(StrEnumBase):
    HF_SAFETENSORS = "hf_safetensors"
    GGUF = "gguf"
    MLX = "mlx"
    SPLASH = "splash"
    LITERT = "litert"
    MLC = "mlc"


class ArtifactKind(StrEnumBase):
    FULL = "full"
    MINIATURE = "miniature"


class WorkloadKind(StrEnumBase):
    SINGLE_STREAM = "single_stream"
    CONCURRENCY = "concurrency"
    LONG_CONTEXT = "long_context"
    PREFIX_SHARED = "prefix_shared"
    MIXED_LENGTH = "mixed_length"
    REPLAY = "replay"
    CONTROL_AA = "control_aa"


class Tier(StrEnumBase):
    SMOKE = "smoke"
    NIGHTLY = "nightly"
    WEEKLY = "weekly"
    TARGETED = "targeted"


class CellStatus(StrEnumBase):
    PASS = "pass"
    FAIL = "fail"
    DECLARED_UNSUPPORTED = "declared_unsupported"
    NOT_RUN = "not_run"
    NOISY = "noisy"


class ErrorClass(StrEnumBase):
    LOAD_FAIL = "load_fail"
    CRASH = "crash"
    HANG = "hang"
    OOM = "oom"
    DOESNT_FIT = "doesnt_fit"
    GATE_FAIL = "gate_fail"
    HARNESS_INVALID = "harness_invalid"
    INPUT_MISMATCH = "input_mismatch"
    INCOMPATIBLE = "incompatible"


class AccuracyStatus(StrEnumBase):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED_MINIATURE = "skipped_miniature"
    SKIPPED_NO_REFERENCE = "skipped_no_reference"
    NOT_RUN = "not_run"


class MiniatureRecipe(BaseModel):

    layers: str = Field(description="source layer selection, e.g. '0-4' or '0-5,39'")
    experts: int | None = Field(default=None, description="routed experts kept per MoE layer (None = all)")
    repeat: int = 1
    text_only: bool = False
    period: int = Field(default=1, description="layer-type pattern period the selection must be a multiple of")
    engram_vocab: int | None = Field(default=None, description="DeepSeek-V4.1: re-carve each Engram hash table to this bucket base (--engram-vocab)")
    attn_res_block_size: int | None = Field(default=None, description="Kimi-K3: AttnRes block stride of the cut (--attn-res-block-size)")
    shrink_family: str | None = Field(default=None, description="the shrink script's family where the checkpoint's index matches several (--family)")
    keep_fp8: bool = Field(default=False, description="DeepSeek-V4/V4.1: keep the fp8 planes as released (--keep-fp8); read out to bf16 they no longer match the config's quantization_config, which vLLM and SGLang load by")
    widen_bf16: bool = Field(default=False, description="the cut's quantized planes (MXFP8, NVFP4) read out to bf16 and its quantization_config dropped (node/widen.py), for an engine that cannot load the release's quantization; pie runs the same files")
    mlx_quantize: str | None = Field(default=None, description="the bf16 cut quantized where it is built, by mlx_lm.convert in mlx-lm's interpreter (MLX_PY), to this MLX scheme (affine_u4_g64: 4 bits in 64-wide groups; node/mlx_quantize.py): a 4-bit slice of a model no MLX release quantizes, for a machine the bf16 cut does not fit; pie and mlx-lm read the same files")
    note: str = ""

    @property
    def recipe_hash(self) -> str:
        key = json.dumps([self.layers, self.experts, self.repeat, self.text_only, self.engram_vocab, self.attn_res_block_size] + ([True] if self.keep_fp8 else [])
                         + (["bf16"] if self.widen_bf16 else []) + ([self.mlx_quantize] if self.mlx_quantize else []), sort_keys=True)
        return hashlib.sha256(key.encode()).hexdigest()[:10]

    @property
    def tag(self) -> str:
        t = f"mini-l{self.layers.replace(',', '_')}"
        if self.experts is not None:
            t += f"-e{self.experts}"
        if self.repeat > 1:
            t += f"-r{self.repeat}"
        if self.text_only:
            t += "-txt"
        if self.engram_vocab is not None:
            t += f"-g{self.engram_vocab}"
        if self.attn_res_block_size is not None:
            t += f"-b{self.attn_res_block_size}"
        if self.keep_fp8:
            t += "-fp8"
        if self.widen_bf16:
            t += "-bf16"
        if self.mlx_quantize:
            t += f"-mlx-{self.mlx_quantize}"
        return t


class ArtifactSpec(BaseModel):
    id: str
    base_model: str = Field(description="HF repo id or local path of the checkpoint")
    revision: str | None = Field(default=None, description="checkpoint commit; resolved at run time if None")
    family: str = Field(description="model family key (qwen3, gemma4, deepseek_v4, ...)")
    scheme: QuantScheme
    kv_dtype: str = "bf16"
    source_format: SourceFormat = SourceFormat.HF_SAFETENSORS
    kind: ArtifactKind = ArtifactKind.FULL
    miniature: MiniatureRecipe | None = None
    expected_gib: float | None = Field(default=None, description="LM-only resident weight size")
    degradation_budget: dict[str, float] | None = Field(
        default=None,
        description="for quant schemes without a same-weights reference: allowed ppl ratio / score drop vs bf16",
    )
    chat_template: bool = False
    pie_sku: str | None = Field(default=None, description="pie SKU row name carrying the quantization (e.g. gptoss-20b-dflash-u4g64-mxfp4-kv-bf16)")
    pie_drafter: str | None = Field(default=None, description="the drafter pie publishes for this base_model (e.g. dflash): the import takes the base model by repository id with `--drafter`, which fetches the published head and lands the drafter row")
    draft_model: str | None = Field(default=None, description="HF repo of a small same-family model (identical vocabulary) a baseline engine drafts with on the rows pie speculates (llama.cpp --model-draft, mlx-lm --draft-model); fetched with the artifact")
    draft_gguf_file: str | None = Field(default=None, description="file name of the draft inside a GGUF ``draft_model`` repo (llama.cpp)")
    max_context: int | None = Field(default=None, description="tokens one sequence may hold on this artifact as pie ships it (the SKU's max_context), when smaller than the HF config's")
    gguf_file: str | None = Field(default=None, description="file name inside a GGUF repo (the arm must be named, never the quant tag)")
    gguf_config_from: str | None = Field(default=None, description="HF repo whose config.json is copied next to the GGUF (pie reads the encoding from config.json; GGUF repos ship none)")
    tokenizer_from: str | None = Field(default=None, description="HF repo whose tokenizer and chat template render this artifact's prompts (a GGUF repo ships none)")
    display_name: str | None = Field(default=None, description="name the site shows for this model (``gemma4:26b``)")
    baseline_of: str | None = Field(default=None, description="the pie artifact whose weights this copy carries, so a baseline engine's numbers compare with it")
    baseline_label: str | None = Field(default=None, description="column name for this baseline arm on the site (``llama.cpp``, ``mlx-lm``)")
    variant: str | None = Field(default=None, description="what sets this artifact apart from another serving the same checkpoint (e.g. ``dflash2``, a drafter deployment); part of its cells' identity")
    platforms: list[str] | None = Field(default=None, description="the only platform ids this artifact runs on (None = every platform); elsewhere it is not a cell at all")
    tiers: list[Tier] = Field(default_factory=lambda: [Tier.NIGHTLY, Tier.WEEKLY])

    @model_validator(mode="after")
    def _miniature_needs_recipe(self) -> ArtifactSpec:
        if self.kind == ArtifactKind.MINIATURE and self.miniature is None:
            raise ValueError(f"artifact {self.id}: miniature artifacts need a recipe")
        return self

    @property
    def artifact_key(self) -> str:
        key = f"{self.base_model}@{self.scheme}/{self.source_format}"
        if self.kind == ArtifactKind.MINIATURE:
            key += f"#mini-{self.miniature.recipe_hash}"
        if self.baseline_label:
            key += f"#{self.baseline_label}"
        if self.variant:
            key += f"#{self.variant}"
        if self.platforms:
            key += "#" + "+".join(self.platforms)
        return key


class PlatformSpec(BaseModel):
    id: str
    os: str
    backend: Backend
    accelerator: str = Field(description="human name, e.g. 'NVIDIA L40S', 'Apple M1 Max'")
    arch: str = Field(description="ada | blackwell | hopper | ampere | apple7 | apple8 | apple9 ...")
    count: int = 1
    memory_gib: float
    interconnect: str = "pcie"
    peer_access: bool = Field(default=True, description="false where the pod advertises GPU peer access it cannot deliver: tp>1 baselines then keep their all-reduce on NCCL, as pie does there")
    runner_labels: list[str] = Field(default_factory=list, description="GitHub self-hosted runner labels")
    runpod_gpu_type: str | None = None
    runpod_image: str | None = Field(default=None, description="pod image for this platform in place of the CUDA runner image; {sglang} and {vllm} take the run's pins")
    catalog: str | None = Field(default=None, description="hardware.yaml id, where the RunPod GPU type does not name it")
    tp_capable: bool = False
    tiers: list[Tier] = Field(default_factory=lambda: [Tier.NIGHTLY, Tier.WEEKLY])
    fit_factor: float | None = Field(default=None, description="headroom the fit rule asks of this platform's memory (default: support.yaml fit_factor)")
    pod: str | None = Field(default=None, description="platform whose pod hosts this one's jobs (an x1 on the x2 pod of the same GPU, one GPU masked); default: its own")
    container_disk_gb: int | None = Field(default=None, description="container disk its pod asks for when runpod.yaml's is too small (a checkpoint of a terabyte and more)")
    device_models: list[str] = Field(default_factory=list, description="a phone's model codes (Android Build.MODEL, iPhone identifier), matched as prefixes by the phone ingest")


class WorkloadSpec(BaseModel):
    id: str
    kind: WorkloadKind
    params: dict[str, Any] = Field(default_factory=dict)
    tiers: list[Tier] = Field(default_factory=lambda: [Tier.NIGHTLY])
    est_minutes: float = 1.0


class ProgramSpec(BaseModel):

    id: str
    path: str = Field(description="path under the pie tree, e.g. examples/text-completion-bench")
    category: str
    baseline_equivalents: dict[str, str] = Field(
        default_factory=dict, description="engine -> mode flag that is the comparable feature, if any"
    )
    accuracy_gate: str = "token_parity"
    pie_only: bool = True
    spec_dec: str | None = Field(default=None, description="speculative mode this program requires")
    bench_args: list[str] = Field(default_factory=list, description="extra bench flags this program needs (e.g. a sampling inferlet rejects temperature 0)")
    workloads: list[str] | None = Field(default=None, description="restrict to these workload ids (None = all)")
    families: list[str] | None = Field(default=None, description="restrict to these model families (None = all)")
    tiers: list[Tier] = Field(default_factory=lambda: [Tier.NIGHTLY, Tier.WEEKLY])


class Mode(BaseModel):
    id: str = "tp1"
    tp: int = 1
    spec_dec: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    tiers: list[Tier] = Field(default_factory=lambda: [Tier.NIGHTLY, Tier.WEEKLY])

    @property
    def key(self) -> str:
        parts = [f"tp{self.tp}"]
        if self.spec_dec:
            parts.append(self.spec_dec)
        for k in sorted(self.extra):
            parts.append(f"{k}={self.extra[k]}")
        return ",".join(parts)


class Cell(BaseModel):
    engine: EngineName
    engine_version: str | None = Field(default=None, description="baseline version or pie commit; filled at run time")
    platform: PlatformSpec
    artifact: ArtifactSpec
    workload: WorkloadSpec
    program: ProgramSpec
    mode: Mode = Field(default_factory=Mode)
    tiers: list[Tier] = Field(default_factory=list)
    declared_unsupported_reason: str | None = None

    @property
    def cell_key(self) -> str:
        return "|".join(
            [
                str(self.engine),
                self.platform.id,
                self.artifact.artifact_key,
                self.workload.id,
                self.program.id,
                self.mode.key,
            ]
        )

    @property
    def cell_id(self) -> str:
        return hashlib.sha256(self.cell_key.encode()).hexdigest()[:16]
