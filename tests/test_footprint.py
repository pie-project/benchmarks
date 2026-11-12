import pytest

from server.footprint import sizes

PAGES = {
    "https://hub.docker.com/v2/repositories/lmsysorg/sglang/tags/latest": {"images": [{"os": "linux", "architecture": "arm64", "size": 1}, {"os": "linux", "architecture": "amd64", "size": 16_111_000_000}]},
    "https://hub.docker.com/v2/repositories/vllm/vllm-openai/tags/latest": {"images": [{"os": "linux", "architecture": "amd64", "size": 9_738_000_000}]},
    "https://api.github.com/repos/pie-project/pie/releases/latest": {"tag_name": "0.6.0", "assets": [
        {"name": "pie-aarch64-linux-cuda13.0.tar.gz", "size": 1},
        {"name": "pie-x86_64-linux-vulkan.tar.gz", "size": 2},
        {"name": "pie-x86_64-linux-cuda13.0.tar.gz", "size": 31_400_000},
    ]},
}


def test_sizes_are_the_amd64_images_against_the_linux_cuda_archive():
    out = sizes(PAGES.__getitem__)
    assert [(e["id"], e["mb"]) for e in out["engines"]] == [("sglang", 16111), ("vllm", 9738), ("pie", 31)]
    assert out["engines"][2]["source"] == "pie-project/pie 0.6.0 pie-x86_64-linux-cuda13.0.tar.gz"


def test_a_missing_archive_fails_loudly_so_the_last_sizes_stay():
    pages = {**PAGES, "https://api.github.com/repos/pie-project/pie/releases/latest": {"tag_name": "0.7.0", "assets": []}}
    with pytest.raises(StopIteration):
        sizes(pages.__getitem__)
