"""Loaded at interpreter start by every vLLM / SGLang process pie-evals launches for tp>1 on a
platform with ``peer_access: false`` (Engine.no_peer_env puts this directory on PYTHONPATH, and
spawned workers inherit it).

Both engines build their custom all-reduce only when a P2P check passes, and by default that
check trusts the driver, which on such a pod advertises peer access it cannot deliver. Making
the check answer False is what ``disable_custom_all_reduce=True`` does: the engine logs that its
custom all-reduce is disabled and NCCL carries every all-reduce. Nothing else is changed.

- vLLM: ``vllm.distributed.device_communicators.custom_all_reduce._can_p2p``
- SGLang: ``sglang.srt.distributed.device_communicators.custom_all_reduce_utils.can_p2p``
"""

import os
import sys

_PATCHES = {
    "vllm.distributed.device_communicators.custom_all_reduce": "_can_p2p",
    "sglang.srt.distributed.device_communicators.custom_all_reduce_utils": "can_p2p",
}


class _NoPeerAllReduce:
    def find_spec(self, name, path=None, target=None):
        attr = _PATCHES.get(name)
        if attr is None:
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
            setattr(module, attr, lambda rank, world_size: False)
            sys.stderr.write(f"pie-evals: {name}.{attr} -> False (no GPU peer access); NCCL carries the all-reduce\n")

        spec.loader.exec_module = patched
        return spec


if os.environ.get("PIE_EVALS_NO_CUSTOM_AR") == "1":
    sys.meta_path.insert(0, _NoPeerAllReduce())
