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
