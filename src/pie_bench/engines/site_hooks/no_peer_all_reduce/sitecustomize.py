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
            sys.stderr.write(
                f"pie-bench: {name}.{attr} -> False (no GPU peer access); NCCL carries the all-reduce\n"
            )

        spec.loader.exec_module = patched
        return spec


if os.environ.get("PIE_BENCH_NO_CUSTOM_AR") == "1":
    sys.meta_path.insert(0, _NoPeerAllReduce())
