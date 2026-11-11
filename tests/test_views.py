from datetime import datetime, timezone

from server import views as webdb


def test_a_row_carries_the_prompt_its_engine_prefilled_per_request():
    assert webdb.prompt_per_request({"prompt_tokens": 3324, "requests": 6, "failed": 0}) == 554.0
    assert webdb.prompt_per_request({"prompt_tokens": 2770, "requests": 6, "failed": 1}) == 554.0
    assert webdb.prompt_per_request({"prompt_tokens": None, "requests": 6, "failed": 0}) is None
    assert webdb.prompt_per_request({"prompt_tokens": 100, "requests": 2, "failed": 2}) is None
    assert webdb.prompt_per_request({}) is None


def test_a_prefill_only_rerun_brings_its_prompt_count_with_its_prefill():
    t0, t1 = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 2, tzinfo=timezone.utc)
    base = {"platform": "pro6000-x1", "engine": "pie", "artifact": "qwen3.6-35b-a3b-bf16", "workload": "raw-512-256", "scheme": "bf16"}
    old = {**base, "started_at": t0, "decode_tok_s": 185.0, "prefill_tok_s": 9000.0, "ttft_ms_p50": 61.5, "ttft_ms_p99": 62.0,
           "prompt_tokens": 3300, "requests": 6, "failed": 0}
    new = {**base, "started_at": t1, "decode_tok_s": 150.0, "prefill_tok_s": 12823.7, "ttft_ms_p50": 43.2, "ttft_ms_p99": 44.4,
           "prompt_tokens": 2770, "requests": 5, "failed": 0}
    key = ("pro6000-x1", "pie", "qwen3.6-35b-a3b", "raw")
    picked = {key: ((t1,), new)}
    webdb.keep_decode([old, new], picked, {"qwen3.6-35b-a3b-bf16": "qwen3.6-35b-a3b"}, "pie", t1)
    row = picked[key][1]
    assert row["decode_tok_s"] == 185.0 and row["prefill_tok_s"] == 12823.7
    assert webdb.prompt_per_request(row) == 554.0


def test_every_install_size_names_its_engine_bytes_and_how_it_was_counted():
    rows = webdb.install_sizes()
    engines = {e["id"] for e in webdb.load("engines")["engines"]}
    assert {r["platform"] for r in rows} <= {"mac", "nvidia", "web", "amd", "tpu", "android"}
    assert len({(r["platform"], r["engine"]) for r in rows}) == len(rows)
    for r in rows:
        assert r["engine"] in engines
        assert isinstance(r["bytes"], int) and r["bytes"] > 0
        assert r["version"] and r["method"] and r["source"] and r["measured"]
        assert sum(n for _, n in r["parts"]) <= r["bytes"]


def test_a_diagnostic_tag_never_reaches_the_site():
    assert webdb.is_diag_tag("tpu-diag-c256prof")
    assert webdb.is_diag_tag("tpu-diag-window-fix")
    assert not webdb.is_diag_tag("tpu-v6e-green")
    assert not webdb.is_diag_tag("a40-rerun")
    assert not webdb.is_diag_tag("0.5.3-b5")


def test_off_a_mac_the_released_checkpoint_outranks_a_later_mlx_run():
    t0, t1 = datetime(2026, 11, 9, 15, tzinfo=timezone.utc), datetime(2026, 11, 9, 17, tzinfo=timezone.utc)
    a2m = {"gemma-4-31b-bf16": "gemma-4-31b", "gemma-4-31b-mlx4": "gemma-4-31b"}
    base = {"engine": "pie", "workload": "pf32-512", "scheme": "bf16", "status": "pass"}
    bf16 = {**base, "platform": "b200-x1", "artifact": "gemma-4-31b-bf16", "started_at": t0, "prefill_tok_s": 18509.0}
    mlx4 = {**base, "platform": "b200-x1", "artifact": "gemma-4-31b-mlx4", "started_at": t1, "prefill_tok_s": 4709.0}
    picked = webdb.pick([bf16, mlx4], a2m)
    assert picked[("b200-x1", "pie", "gemma-4-31b", "prefill_batch")][1] is bf16
    assert webdb.pick([mlx4], a2m)[("b200-x1", "pie", "gemma-4-31b", "prefill_batch")][1] is mlx4
    mac_bf16 = {**bf16, "platform": "m4-pro-48g"}
    mac_mlx4 = {**mlx4, "platform": "m4-pro-48g"}
    assert webdb.pick([mac_bf16, mac_mlx4], a2m)[("m4-pro-48g", "pie", "gemma-4-31b", "prefill_batch")][1] is mac_mlx4


def test_the_newest_run_of_a_cell_shows_whatever_tag_it_ran_under():
    key = ("tpu-v6e-1", "pie", "qwen3-0.6b", "prefill_batch")
    tagged = {"tpu-v6e-fix": {key: {"at": "2026-11-08 14:31", "pf": 21045.14}},
              "main-a2f02c75a": {key: {"at": "2026-11-09 04:40", "pf": 104742.73}},
              "tpu-v6e-full": {key: {"at": "2026-11-04 03:15", "pf": 9000.0}}}
    order = ["tpu-v6e-fix", "main-a2f02c75a", "tpu-v6e-full"]
    snaps = webdb.stack(order, tagged, [key], lambda item, key, src: {"pf": item["pf"], "release": src}, lambda item: item["at"])
    assert snaps["tpu-v6e-fix"][0]["pf"] == 104742.73
    assert snaps["tpu-v6e-fix"][0]["stale"] == {"tag": "main-a2f02c75a", "measured": "2026-11-09 04:40"}
    assert snaps["main-a2f02c75a"][0]["pf"] == 104742.73 and snaps["main-a2f02c75a"][0]["stale"] is None
    assert snaps["tpu-v6e-full"][0]["pf"] == 9000.0 and snaps["tpu-v6e-full"][0]["stale"] is None


def test_a_run_of_a_ci_fixture_never_takes_a_cell_and_the_build_says_why(capsys):
    t0, t1 = datetime(2026, 11, 3, 12, tzinfo=timezone.utc), datetime(2026, 11, 8, 14, 46, tzinfo=timezone.utc)
    a2m, _ = webdb.artifact_to_model()
    base = {"platform": "a40-x1", "engine": "pie", "engine_version": "", "workload": "c512", "scheme": None, "status": "pass",
            "pie_commit": "ba82f3425", "tag_kind": "manual", "decode_tok_s": 27.4}
    released = {**base, "artifact": "deepseek-v4-flash-mini", "tag": "a40-full", "started_at": t0, "output_tok_s": 11947.3}
    fixture = {**base, "artifact": "deepseek-v4-flash-mini5", "tag": "a40-rerun", "started_at": t1, "output_tok_s": 11798.6}

    class Store:
        def table(self):
            return self

        def select(self, cols):
            return self

        def to_pylist(self):
            return [{**dict.fromkeys(webdb.METRICS), **r} for r in (released, fixture)]

    tagged, _ = webdb.results_by_tag(Store(), a2m, ["a40-x1"], ["pie"])
    key = ("a40-x1", "pie", "deepseek-v4-flash", "throughput")
    assert tagged["a40-full"][key][1]["output_tok_s"] == 11947.3 and key not in tagged["a40-rerun"]
    assert "[webdb] a40-rerun: pie deepseek-v4-flash-mini5 on a40-x1 not shown: a CI fixture" in capsys.readouterr().err


def test_engines_are_compared_on_the_workload_they_share():
    t0, t1 = datetime(2026, 11, 9, 15, tzinfo=timezone.utc), datetime(2026, 11, 10, 9, tzinfo=timezone.utc)
    a2m = {"qwen3.5-0.8b-xla": "qwen3.5-0.8b"}
    base = {"platform": "tpu-v5e-1", "artifact": "qwen3.5-0.8b-xla", "scheme": "bf16", "status": "pass"}
    pie256 = {**base, "engine": "pie", "workload": "c256", "started_at": t0, "decode_tok_s": 7023.0}
    pie32 = {**base, "engine": "pie", "workload": "c32", "started_at": t1, "decode_tok_s": 5028.0}
    vllm256 = {**base, "engine": "vllm", "workload": "c256", "started_at": t0, "decode_tok_s": 8759.0}
    picked = webdb.pick([pie256, pie32, vllm256], a2m)
    (pie_key,) = [k for k in picked if k[1] == "pie"]
    assert picked[pie_key][1] is pie256
    assert webdb.pick([pie256, pie32], a2m)[pie_key][1] is pie32


def test_engines_share_a_workload_across_tags():
    t0, t1 = datetime(2026, 11, 9, 15, tzinfo=timezone.utc), datetime(2026, 11, 10, 9, tzinfo=timezone.utc)
    a2m = {"qwen3.5-0.8b-xla": "qwen3.5-0.8b"}
    base = {"platform": "tpu-v5e-1", "artifact": "qwen3.5-0.8b-xla", "scheme": "bf16", "status": "pass"}
    pie256 = {**base, "engine": "pie", "workload": "c256", "started_at": t0, "tag": "main-9e94273f0"}
    pie32 = {**base, "engine": "pie", "workload": "c32", "started_at": t1, "tag": "main-9e94273f0"}
    vllm256 = {**base, "engine": "vllm", "workload": "c256", "started_at": t0, "tag": "tpu-v5e-full"}
    kept = webdb.share_workload([pie256, pie32, vllm256], a2m)
    assert pie32 not in kept and pie256 in kept and vllm256 in kept
    assert webdb.share_workload([pie32], a2m) == [pie32]


def test_engines_share_a_cut_of_the_model():
    t0, t1 = datetime(2026, 11, 8, tzinfo=timezone.utc), datetime(2026, 11, 9, tzinfo=timezone.utc)
    a2m = {"glm-5.3-mini78": "glm-5.3", "glm-5.3-mini78-e12": "glm-5.3"}
    base = {"platform": "b200-x1", "workload": "pf128-512", "scheme": "fp8", "status": "pass"}
    pie12 = {**base, "engine": "pie", "artifact": "glm-5.3-mini78-e12", "started_at": t1}
    rivals = [{**base, "engine": e, "artifact": "glm-5.3-mini78", "started_at": t0} for e in ("vllm", "sglang", "trtllm")]
    assert webdb.share_cut([pie12, *rivals], a2m) == rivals
    pie16 = {**base, "engine": "pie", "artifact": "glm-5.3-mini78", "started_at": t0}
    assert webdb.share_cut([pie12, pie16, *rivals], a2m) == [pie16, *rivals]
    assert webdb.share_cut([pie12], a2m) == [pie12]
    raw = {**rivals[0], "workload": "raw-512-256", "artifact": "glm-5.3-mini78-e12"}
    assert webdb.share_cut([raw, *rivals], a2m) == [raw, *rivals]


def test_one_cut_reads_alike_whichever_artifact_ran_it():
    assert webdb.MINIATURE["gpt-oss-120b-mlx-mxfp4-slice-e10"] == webdb.MINIATURE["gpt-oss-120b-mlxlm-slice-e10"] == "36 layers, 10 experts"
    assert webdb.CUT["glm-5.3-mini"] == webdb.CUT["glm-5.3-mini-tpu"] != webdb.CUT["glm-5.3-mini78"] != webdb.CUT["glm-5.3-mini78-e12"]
    assert webdb.MINIATURE["glm-5.3-mini"] == "7 of 78 layers"
