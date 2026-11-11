from server.headline import head_to_head


def _row(hw, engine, model, value, workload="raw", status="pass"):
    return {"hardware": hw, "engine": engine, "model": model, "workload": workload, "decode_tok_s": value, "status": status}


CORE = {
    "tags": [{"id": "new"}, {"id": "old"}],
    "hardware": [{"id": "h100", "vendor": "NVIDIA"}, {"id": "m4", "class": "mac", "vendor": "Apple"}, {"id": "v6e", "backend": "xla", "vendor": "Google"}],
    "engines": [{"id": "pie", "name": "Pie"}, {"id": "vllm", "name": "vLLM"}, {"id": "mlxlm", "name": "MLX"}],
    "snapshots": {
        "new": [
            _row("h100", "pie", "a", 200), _row("h100", "vllm", "a", 100),
            _row("h100", "pie", "b", 100), _row("h100", "vllm", "b", 200),
            _row("h100", "pie", "c", 900, workload="throughput"), _row("h100", "vllm", "c", 1, workload="throughput"),
            _row("m4", "pie", "a", 30), _row("m4", "pie", "a", 60), _row("m4", "mlxlm", "a", 40), _row("m4", "mlxlm", "b", 40, status="not_run"),
            _row("v6e", "vllm", "a", 10),
        ],
        "old": [_row("h100", "pie", "a", 1), _row("h100", "vllm", "a", 1000)],
    },
}


def test_each_platform_gets_the_geometric_mean_of_pies_lead_over_each_engine():
    out = head_to_head(CORE)
    assert out["release"] == "new"
    mac, nvidia = out["platforms"]
    assert (nvidia["id"], nvidia["machines"]) == ("nvidia", 1)
    assert nvidia["engines"] == [{"id": "vllm", "name": "vLLM", "speedup": 1.0, "pairs": 2}]  # 2x and 0.5x average to parity
    assert mac["engines"] == [{"id": "mlxlm", "name": "MLX", "speedup": 1.5, "pairs": 1}]  # pie's fastest result, 60 over 40


def test_a_platform_without_pie_results_is_left_out():
    assert "tpu" not in {p["id"] for p in head_to_head(CORE)["platforms"]}


def test_no_data_gives_an_empty_list():
    assert head_to_head({})["platforms"] == []
