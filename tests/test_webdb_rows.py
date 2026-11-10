import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import webdb  # noqa: E402


def test_a_row_carries_the_prompt_its_engine_prefilled_per_request():
    # raw-512-256 on Qwen: 6 measured requests of ~554 tokens (the 512-token shape, chat template and cold tag)
    assert webdb.prompt_per_request({"prompt_tokens": 3324, "requests": 6, "failed": 0}) == 554.0
    # failed requests carry no prompt tokens: the count is over the completed ones
    assert webdb.prompt_per_request({"prompt_tokens": 2770, "requests": 6, "failed": 1}) == 554.0
    # no count, or nothing completed: no figure, and the site falls back to the shape's nominal prompt
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
    # one figure per engine and platform, each with what it counts and where it came from
    assert len({(r["platform"], r["engine"]) for r in rows}) == len(rows)
    for r in rows:
        assert r["engine"] in engines
        assert isinstance(r["bytes"], int) and r["bytes"] > 0
        assert r["version"] and r["method"] and r["source"] and r["measured"]
        # the parts name pieces of the figure, never more than all of it
        assert sum(n for _, n in r["parts"]) <= r["bytes"]


def test_a_diagnostic_tag_never_reaches_the_site():
    # profilers and timing A/Bs slow their own tok/s on purpose: their tags are neither releases nor fills
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
    # alone, the mlx run is the model's row; on a Mac it is the comparison and the newest wins as before
    assert webdb.pick([mlx4], a2m)[("b200-x1", "pie", "gemma-4-31b", "prefill_batch")][1] is mlx4
    mac_bf16 = {**bf16, "platform": "m4-pro-48g"}
    mac_mlx4 = {**mlx4, "platform": "m4-pro-48g"}
    assert webdb.pick([mac_bf16, mac_mlx4], a2m)[("m4-pro-48g", "pie", "gemma-4-31b", "prefill_batch")][1] is mac_mlx4


def test_the_newest_run_of_a_cell_shows_whatever_tag_it_ran_under():
    key = ("tpu-v6e-1", "pie", "qwen3-0.6b", "prefill_batch")
    # tpu-v6e-fix is the newest tag (imported into again on 11-09) but measured this cell on 11-08; main-a2f02c75a,
    # dated earlier, measured it again on 11-09 (the site showed 21k over 105k tok/s, 2026-11-09)
    tagged = {"tpu-v6e-fix": {key: {"at": "2026-11-08 14:31", "pf": 21045.14}},
              "main-a2f02c75a": {key: {"at": "2026-11-09 04:40", "pf": 104742.73}},
              "tpu-v6e-full": {key: {"at": "2026-11-04 03:15", "pf": 9000.0}}}
    order = ["tpu-v6e-fix", "main-a2f02c75a", "tpu-v6e-full"]  # newest first, as main() orders the tags
    snaps = webdb.stack(order, tagged, [key], lambda item, key, src: {"pf": item["pf"], "release": src}, lambda item: item["at"])
    # the newest tag shows the cell's newest run, from the other tag and marked as its
    assert snaps["tpu-v6e-fix"][0]["pf"] == 104742.73
    assert snaps["tpu-v6e-fix"][0]["stale"] == {"tag": "main-a2f02c75a", "measured": "2026-11-09 04:40"}
    # a tag whose own run is the newest shows its own
    assert snaps["main-a2f02c75a"][0]["pf"] == 104742.73 and snaps["main-a2f02c75a"][0]["stale"] is None
    # never a later tag's run
    assert snaps["tpu-v6e-full"][0]["pf"] == 9000.0 and snaps["tpu-v6e-full"][0]["stale"] is None


def test_a_run_of_a_ci_fixture_never_takes_a_cell_and_the_build_says_why(capsys):
    # #1514: a40-rerun ran pie on deepseek-v4-flash-mini5 (the smoke fixture, its cut in bf16 MLX layout), a40-full on
    # deepseek-v4-flash-mini (the same cut from the released checkpoint, the weights vLLM and SGLang run there)
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
    # pie's newer c32 row never stands against vLLM's c256 (the v5e showed 5028 against 8759, 2026-11-10)
    assert picked[pie_key][1] is pie256
    # alone, the newest row wins as before
    assert webdb.pick([pie256, pie32], a2m)[pie_key][1] is pie32


def test_engines_share_a_workload_across_tags():
    t0, t1 = datetime(2026, 11, 9, 15, tzinfo=timezone.utc), datetime(2026, 11, 10, 9, tzinfo=timezone.utc)
    a2m = {"qwen3.5-0.8b-xla": "qwen3.5-0.8b"}
    base = {"platform": "tpu-v5e-1", "artifact": "qwen3.5-0.8b-xla", "scheme": "bf16", "status": "pass"}
    pie256 = {**base, "engine": "pie", "workload": "c256", "started_at": t0, "tag": "main-9e94273f0"}
    pie32 = {**base, "engine": "pie", "workload": "c32", "started_at": t1, "tag": "main-9e94273f0"}
    vllm256 = {**base, "engine": "vllm", "workload": "c256", "started_at": t0, "tag": "tpu-v5e-full"}
    kept = webdb.share_workload([pie256, pie32, vllm256], a2m)
    # pie's c32 (its tag holds no vLLM row) never reaches the cell vLLM's c256 shows in (2026-11-10)
    assert pie32 not in kept and pie256 in kept and vllm256 in kept
    # a workload only one engine measured stays where nothing is shared
    assert webdb.share_workload([pie32], a2m) == [pie32]


def test_engines_share_a_cut_of_the_model():
    t0, t1 = datetime(2026, 11, 8, tzinfo=timezone.utc), datetime(2026, 11, 9, tzinfo=timezone.utc)
    a2m = {"glm-5.3-mini78": "glm-5.3", "glm-5.3-mini78-e12": "glm-5.3"}
    base = {"platform": "b200-x1", "workload": "pf128-512", "scheme": "fp8", "status": "pass"}
    pie12 = {**base, "engine": "pie", "artifact": "glm-5.3-mini78-e12", "started_at": t1}
    rivals = [{**base, "engine": e, "artifact": "glm-5.3-mini78", "started_at": t0} for e in ("vllm", "sglang", "trtllm")]
    # pie's 12-expert cut never stands against the 16-expert one the others ran, though both read "78 of 78 layers"
    assert webdb.share_cut([pie12, *rivals], a2m) == rivals
    # once pie runs the shared cut, that row is the one kept
    pie16 = {**base, "engine": "pie", "artifact": "glm-5.3-mini78", "started_at": t0}
    assert webdb.share_cut([pie12, pie16, *rivals], a2m) == [pie16, *rivals]
    # one cut alone, or other platforms and categories, pass through
    assert webdb.share_cut([pie12], a2m) == [pie12]
    raw = {**rivals[0], "workload": "raw-512-256", "artifact": "glm-5.3-mini78-e12"}
    assert webdb.share_cut([raw, *rivals], a2m) == [raw, *rivals]


def test_one_cut_reads_alike_whichever_artifact_ran_it():
    # pie's Mac slice of gpt-oss-120b also runs in the browser; MLX's runs on Macs only: one cut, one label
    assert webdb.MINIATURE["gpt-oss-120b-mlx-mxfp4-slice-e10"] == webdb.MINIATURE["gpt-oss-120b-mlxlm-slice-e10"] == "36 layers, 10 experts"
    assert webdb.CUT["glm-5.3-mini"] == webdb.CUT["glm-5.3-mini-tpu"] != webdb.CUT["glm-5.3-mini78"] != webdb.CUT["glm-5.3-mini78-e12"]
    assert webdb.MINIATURE["glm-5.3-mini"] == "7 of 78 layers"
