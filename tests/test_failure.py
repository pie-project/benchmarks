from pie_bench.node.engines.base import classify_failure
from pie_bench.schema import ErrorClass


def test_a_traceback_is_told_by_its_whole_message():
    stderr = """Traceback (most recent call last):
  File "bench_pie.py", line 689, in serve
    raise RuntimeError(
RuntimeError: pie serve exited before startup completed:
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  INFO gateway worker-facing listener up
  creating engine for model "default" group 0
  impossible submission: the device does not hold this deployment: recommendedMaxWorkingSetSize is 40200896512 bytes
"""
    cls, msg = classify_failure(1, stderr, "", False)
    assert cls == ErrorClass.DOESNT_FIT
    assert msg.startswith("RuntimeError: pie serve exited before startup completed:")
    assert "impossible submission" in msg


def test_a_code_line_is_never_the_message():
    stderr = """Traceback (most recent call last):
  File "bench_pie.py", line 12, in main
    resolved_model = resolve_local_model(args.model)
ValueError: no such model
"""
    cls, msg = classify_failure(1, stderr, "", False)
    assert cls == ErrorClass.CRASH
    assert msg == "ValueError: no such model"
