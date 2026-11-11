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
            sys.stderr.write(f"pie-bench: vLLM engine args {json.dumps(extra)}\n")

        spec.loader.exec_module = patched
        return spec


_extra = os.environ.get("PIE_BENCH_VLLM_ENGINE_ARGS")
if _extra:
    sys.meta_path.insert(0, _EngineArgsOverlay(json.loads(_extra)))


_GATHER = "tpu_inference.kernels.experimental.deepseek_v4.core_attention.csa_gather"
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
                import jax

                def proj_and_save_state(hidden_states, wkv_wgate, ape, positions, slot_mapping, cache, compress_ratio, interpret=False):
                    num_pages, page_size, d1, d2 = cache.shape
                    state_dim = wkv_wgate.shape[1]
                    width = state_dim // 2
                    kv_score = jnp.matmul(hidden_states, wkv_wgate)
                    packed = jnp.concatenate([kv_score[:, :width], kv_score[:, width:] + ape[jnp.mod(positions, compress_ratio)]], axis=-1)
                    per_slot = d1 * d2 // 4
                    spt = state_dim // per_slot
                    n = packed.shape[0]
                    rows = jax.lax.bitcast_convert_type(packed.astype(jnp.float32).reshape(n, spt, per_slot, 1), jnp.uint8)
                    rows = rows.reshape(n, spt, d2, d1).transpose(0, 1, 3, 2)
                    flat = cache.reshape(num_pages * (page_size // spt), spt, d1, d2)
                    idx = jnp.where(slot_mapping >= 0, slot_mapping // spt, flat.shape[0])
                    return flat.at[idx].set(rows, mode="drop").reshape(cache.shape)

                module.proj_and_save_state = proj_and_save_state
                sys.stderr.write("pie-bench: no SparseCore on this chip; DeepSeek-V4's proj_and_save_state runs as an XLA scatter of its reference\n")
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
            sys.stderr.write("pie-bench: no SparseCore on this chip; DeepSeek-V4's csa_gather runs as an XLA gather\n")

        spec.loader.exec_module = patched
        return spec


if os.environ.get("PIE_BENCH_TPU_XLA_CSA_GATHER") == "1":
    sys.meta_path.insert(0, _XlaCsaGather())
