"""Arms JAX tracing in an engine process for the profiler: once jax loads, SIGUSR1 starts a trace, SIGUSR2 stops it.

Active only with PIE_BENCH_JAX_TRACE_DIR set. Any sitecustomize further down sys.path still runs.
"""

import importlib.machinery
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("PIE_BENCH_JAX_TRACE_DIR")


def _arm():
    import signal

    import jax

    out = os.path.join(DIR, str(os.getpid()))
    signal.signal(signal.SIGUSR1, lambda *_: jax.profiler.start_trace(out, create_perfetto_trace=True))
    signal.signal(signal.SIGUSR2, lambda *_: jax.profiler.stop_trace())
    os.makedirs(DIR, exist_ok=True)
    open(os.path.join(DIR, f"{os.getpid()}.pid"), "w").close()


class _AfterJax:
    def find_spec(self, name, path=None, target=None):
        if name != "jax":
            return None
        sys.meta_path.remove(self)
        spec = importlib.util.find_spec(name)
        load = spec.loader.exec_module

        def exec_module(module):
            load(module)
            try:
                _arm()
            except Exception as e:
                sys.stderr.write(f"pie-bench profiler: jax tracing not armed: {e}\n")

        spec.loader.exec_module = exec_module
        return spec


if DIR:
    sys.meta_path.insert(0, _AfterJax())
_paths = [os.path.abspath(p or ".") for p in sys.path]
for _entry in sys.path[_paths.index(HERE) + 1:] if HERE in _paths else []:
    _spec = importlib.machinery.PathFinder.find_spec("sitecustomize", [_entry])
    if _spec is not None:
        _spec.loader.exec_module(importlib.util.module_from_spec(_spec))
        break
