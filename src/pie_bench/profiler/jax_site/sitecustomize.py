"""Arms JAX tracing in an engine process for the profiler: once jax loads, SIGUSR1 starts a trace, SIGUSR2 stops it.
A process with no TPU backend of its own (a server's front end) skips both. Markers <pid>.started and <pid>.done
say when each is over.

Active only with PIE_BENCH_JAX_TRACE_DIR set. Any sitecustomize further down sys.path still runs.
"""

import importlib.machinery
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("PIE_BENCH_JAX_TRACE_DIR")


def _mark(kind, text):
    path = os.path.join(DIR, f"{os.getpid()}.{kind}")
    with open(path + ".tmp", "w") as f:
        f.write(text)
    os.replace(path + ".tmp", path)


def _arm():
    import signal
    import time

    import jax
    from jax._src import xla_bridge

    tracing = []

    def start(*_):
        if tracing:
            return _mark("started", "error already tracing")
        if not any(str(k).startswith("tpu") for k in getattr(xla_bridge, "_backends", None) or {}):
            return _mark("started", "skip: no TPU backend in this process")
        try:
            t0 = time.time_ns()
            jax.profiler.start_trace(os.path.join(DIR, str(os.getpid())))
            tracing.append(1)
            _mark("started", f"ok {t0} {time.time_ns()}")
        except Exception as e:
            _mark("started", f"error {e}")

    def stop(*_):
        if not tracing:
            return _mark("done", "skip: not tracing")
        tracing.clear()
        try:
            jax.profiler.stop_trace()
            _mark("done", "ok")
        except Exception as e:
            _mark("done", f"error {e}")

    signal.signal(signal.SIGUSR1, start)
    signal.signal(signal.SIGUSR2, stop)
    os.makedirs(DIR, exist_ok=True)
    pidfile = lambda: open(os.path.join(DIR, f"{os.getpid()}.pid"), "w").close()
    pidfile()
    os.register_at_fork(after_in_child=lambda: (tracing.clear(), pidfile()))


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
