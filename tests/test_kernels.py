from pie_evals.quality.kernels import parse

LOG = """\
     Running unittests src/lib.rs (/tmp/target/release/deps/kernels_rocm-1)
running 1 test
test tuning::picks ... ok

test result: ok. 1 passed; 0 failed; 0 ignored

     Running tests/linear_moe.rs (/tmp/target/release/deps/linear_moe-2)
running 4 tests
test routes_softmax ... ok
test mxfp4_bank ... FAILED
test slow_leg ... ignored, needs 8 GPUs
test dense_bank ... ok

successes:

---- routes_softmax stdout ----
KERR moe_route_softmax max_abs=0.001 max_rel=0.01

---- dense_bank stdout ----
KERR moe_dense max_abs=0.5 max_rel=0.002
KERR moe_dense max_abs=0.25 max_rel=0.003

successes:
    routes_softmax
    dense_bank

failures:

---- mxfp4_bank stdout ----
KERR moe_mxfp4 max_abs=2.0 max_rel=0.4
thread 'mxfp4_bank' panicked at crates/kernels-rocm/tests/linear_moe.rs:120:5:
row 3: 1.5 vs 3.5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

failures:
    mxfp4_bank

test result: FAILED. 2 passed; 1 failed; 1 ignored

     Running tests/conv.rs (/tmp/target/release/deps/conv-3)
running 2 tests
test conv_ok ... ok
test conv_dies ... error: test failed, to rerun pass `-p kernels-rocm --test conv`
Caused by:
  process didn't exit successfully: `/tmp/target/release/deps/conv-3 --test-threads=1` (signal: 11, SIGSEGV: invalid memory reference)
"""


def test_parse_counts_failures_and_kerr():
    s = parse(LOG)
    assert (s["passed"], s["failed"], s["ignored"], s["n"]) == (4, 2, 1, 6)
    assert s["score"] == round(4 / 6, 4) and s["ci95"] == [s["score"], s["score"]]
    f = {x["name"]: x["message"] for x in s["failures"]}
    assert "panicked at" in f["linear_moe::mxfp4_bank"] and "1.5 vs 3.5" in f["linear_moe::mxfp4_bank"] and "KERR" not in f["linear_moe::mxfp4_bank"]
    assert "SIGSEGV" in f["conv::conv_dies"]
    assert s["errors"]["moe_dense"] == {"max_abs": 0.5, "max_rel": 0.003}
    assert s["worst_abs"] == {"name": "moe_mxfp4", "max_abs": 2.0} and s["worst_rel"]["name"] == "moe_mxfp4"


def test_parse_nothing_ran():
    s = parse("error[E0425]: cannot find value\nerror: could not compile `kernels-cuda`\n")
    assert s["n"] == 0 and s["score"] is None and s["ci95"] is None
