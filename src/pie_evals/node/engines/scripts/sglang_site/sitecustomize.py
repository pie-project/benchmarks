"""Loaded at interpreter start by every SGLang process pie-evals launches on a platform with
``peer_access: false`` (SglangEngine.default_env puts this directory on PYTHONPATH).

SGLang decides whether to build its custom all-reduce from
``custom_all_reduce_utils.can_p2p``; with ``enable_p2p_check`` off (its default) that trusts the
driver, which on such a pod advertises peer access it cannot deliver. Making ``can_p2p`` answer
False is what ``disable_custom_all_reduce=True`` does: SGLang logs that the custom all-reduce
is disabled and NCCL carries every all-reduce. Nothing else is changed.
"""

import os
import sys

_TARGET = "sglang.srt.distributed.device_communicators.custom_all_reduce_utils"


class _NoPeerAllReduce:
    def find_spec(self, name, path=None, target=None):
        if name != _TARGET:
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(name, path, target)
            if spec is not None:
                break
        else:
            return None
        loader = spec.loader
        exec_module = loader.exec_module

        def patched(module):
            exec_module(module)
            module.can_p2p = lambda rank, world_size: False
            sys.stderr.write("pie-evals: SGLang custom all-reduce off (no GPU peer access); NCCL carries it\n")

        loader.exec_module = patched
        return spec


if os.environ.get("SGLANG_PIE_EVALS_NO_CUSTOM_AR") == "1":
    sys.meta_path.insert(0, _NoPeerAllReduce())
