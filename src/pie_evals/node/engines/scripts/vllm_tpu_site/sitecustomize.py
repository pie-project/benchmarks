"""Loaded at interpreter start by the vLLM-TPU processes pie-evals launches (VllmEngine.default_env puts this
directory on PYTHONPATH when the model needs engine arguments vllm_bench.py has no flag for).

``PIE_EVALS_VLLM_ENGINE_ARGS`` holds a JSON object of EngineArgs fields (``additional_config``, ``hf_overrides``);
they are merged into the EngineArgs before vLLM builds its config, as ``--additional-config`` / ``--hf-overrides``
would set them on ``vllm serve``. Nothing else is changed.
"""

import json
import os
import sys

_MODULE = "vllm.engine.arg_utils"


class _EngineArgsOverlay:
    def __init__(self, extra):
        self.extra = extra

    def find_spec(self, name, path=None, target=None):
        if name != _MODULE:
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(name, path, target)
            if spec is not None:
                break
        else:
            return None
        exec_module = spec.loader.exec_module
        extra = self.extra

        def patched(module):
            exec_module(module)
            create = module.EngineArgs.create_engine_config

            def create_engine_config(self, *args, **kwargs):
                for field, value in extra.items():
                    have = getattr(self, field, None)
                    setattr(self, field, {**have, **value} if isinstance(have, dict) and isinstance(value, dict) else value)
                return create(self, *args, **kwargs)

            module.EngineArgs.create_engine_config = create_engine_config
            sys.stderr.write(f"pie-evals: vLLM engine args {json.dumps(extra)}\n")

        spec.loader.exec_module = patched
        return spec


_extra = os.environ.get("PIE_EVALS_VLLM_ENGINE_ARGS")
if _extra:
    sys.meta_path.insert(0, _EngineArgsOverlay(json.loads(_extra)))


# DeepSeek-V4's sparse attention gathers its cached tokens with a SparseCore kernel (csa_gather), and a v5e has no
# SparseCore ("SparseCore info is missing"). Where the chip has none, the same gather in XLA: each token's 512 nope
# bytes (its (4, 128) uint8 block) and its 64 rope bf16 (high bytes [0:64], low [64:128] of its 128-byte row).
_GATHER = "tpu_inference.kernels.experimental.deepseek_v4.core_attention.csa_gather"
# and its compressor's projection kernel (proj_and_save_state) halts a v5e ("Semaphore ... has a nonzero value upon exit
# from a Mosaic kernel", tpu.yml 42179311323): there tpu-inference's own golden reference for it (project_and_save_state_ref)
_PROJ = "tpu_inference.kernels.experimental.deepseek_v4.compress_and_store.proj_and_save_state"


class _XlaCsaGather:
    def find_spec(self, name, path=None, target=None):
        if name not in (_GATHER, _PROJ):
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(name, path, target)
            if spec is not None:
                break
        else:
            return None
        exec_module = spec.loader.exec_module

        def patched(module):
            exec_module(module)
            from jax.experimental.pallas import tpu as pltpu

            if pltpu.get_tpu_info().sparse_core is not None:
                return
            import jax.numpy as jnp

            if name == _PROJ:
                from tpu_inference.kernels.experimental.deepseek_v4.compress_and_store.project_and_save_state_ref import \
                    ref_wkv_proj_and_save_state

                def proj_and_save_state(hidden_states, wkv_wgate, ape, positions, slot_mapping, cache, compress_ratio, interpret=False):
                    # the reference reads head_dim and overlap only as their product, the state width
                    state_dim = wkv_wgate.shape[1]
                    slots_per_token = state_dim // (cache.shape[2] * cache.shape[3] // 4)
                    return ref_wkv_proj_and_save_state(hidden_states, wkv_wgate, ape, positions, slot_mapping, cache,
                                                       state_block_size=cache.shape[1] // slots_per_token,
                                                       head_dim=state_dim // 2, compress_ratio=compress_ratio, overlap=False)

                module.proj_and_save_state = proj_and_save_state
                sys.stderr.write("pie-evals: no SparseCore on this chip; DeepSeek-V4's proj_and_save_state runs as its XLA reference\n")
                return

            def csa_gather(nope_cache, rope_cache, indices):
                nope = jnp.take(nope_cache.reshape(-1, 4 * nope_cache.shape[3]), indices, axis=0)
                rope = jnp.take(rope_cache.reshape(-1, rope_cache.shape[3]), indices, axis=0).astype(jnp.uint16)
                half = rope.shape[1] // 2
                bits = jnp.left_shift(rope[:, :half], 8) | rope[:, half:]
                return nope, jax_bitcast(bits)

            def jax_bitcast(bits):
                import jax

                return jax.lax.bitcast_convert_type(bits, jnp.bfloat16)

            module.csa_gather = csa_gather
            sys.stderr.write("pie-evals: no SparseCore on this chip; DeepSeek-V4's csa_gather runs as an XLA gather\n")

        spec.loader.exec_module = patched
        return spec


if os.environ.get("PIE_EVALS_TPU_XLA_CSA_GATHER") == "1":
    sys.meta_path.insert(0, _XlaCsaGather())
