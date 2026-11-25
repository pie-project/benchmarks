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
    import threading
    import time

    import jax
    from jax._src import xla_bridge

    command = os.path.join(DIR, "command")
    state = {"seq": None, "tracing": False}

    def act(seq, action):
        if action == "start":
            if state["tracing"]:
                return _mark("started", f"{seq} error already tracing")
            if not any(str(k).startswith("tpu") for k in getattr(xla_bridge, "_backends", None) or {}):
                return _mark("started", f"{seq} skip: no TPU backend in this process")
            try:
                options = jax.profiler.ProfileOptions()
                options.python_tracer_level = 0
                t0 = time.time_ns()
                jax.profiler.start_trace(os.path.join(DIR, str(os.getpid())), profiler_options=options)
                state["tracing"] = True
                _mark("started", f"{seq} ok {t0} {time.time_ns()}")
            except Exception as e:
                _mark("started", f"{seq} error {e}")
        elif not state["tracing"]:
            _mark("done", f"{seq} skip: not tracing")
        else:
            state["tracing"] = False
            try:
                jax.profiler.stop_trace()
                _mark("done", f"{seq} ok")
            except Exception as e:
                _mark("done", f"{seq} error {e}")

    def read():
        try:
            with open(command) as f:
                return f.read().split()[:2]
        except OSError:
            return []

    def watch():
        state["seq"] = (read() or [None])[0]
        while True:
            got = read()
            if len(got) == 2 and got[0] != state["seq"]:
                state["seq"] = got[0]
                act(*got)
            time.sleep(0.05)

    def begin():
        state["tracing"] = False
        threading.Thread(target=watch, name="pie-bench-trace", daemon=True).start()
        open(os.path.join(DIR, f"{os.getpid()}.pid"), "w").close()

    os.makedirs(DIR, exist_ok=True)
    begin()
    os.register_at_fork(after_in_child=begin)


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
