from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from pie_evals.orchestrate.jobs import recorded_cell_keys
from pie_evals.orchestrate.store import Store
from pie_evals.schema.cell import Tier
from pie_evals.schema.record import ARROW_SCHEMA


def test_recorded_cell_keys_are_per_commit_and_tier(tmp_path: Path):
    st = Store(tmp_path)
    out = st.records_dir / "nightly" / "2026-09" / "run1.parquet"
    out.parent.mkdir(parents=True)
    rows = [
        {"cell_key": "pie|l40s-x1|a|ss-128-64|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "pass", "engine": "pie"},
        {"cell_key": "pie|l40s-x1|a|c8|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "crash", "engine": "pie"},
        {"cell_key": "pie|l40s-x1|a|c64|text-completion-bench|tp1", "pie_commit": "bbbb", "status": "pass", "engine": "pie"},
        {"cell_key": "vllm|l40s-x1|a|c8|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "vllm", "engine_version": "0.30.0"},
        {"cell_key": "vllm|l40s-x1|a|c64|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "vllm", "engine_version": "0.29.0"},
        {"cell_key": "pie|l40s-x1|a|c32|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "not_run", "engine": "pie"},
        {"cell_key": "pie|l40s-x1|a|c16|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "fail", "engine": "pie", "error_class": "harness_invalid"},
        {"cell_key": "pie|l40s-x1|a|c128|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "pass", "engine": "pie", "checkpoint_revision": "mini-l0-4-e16", "artifact_kind": "full"},
        {"cell_key": "pie|l40s-x1|a|c256|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "noisy", "engine": "pie"},
        {"cell_key": "vllm|h100-pcie-x1|k|c8|text-completion-bench|tp1", "pie_commit": None, "status": "fail", "engine": "vllm", "engine_version": "0.30.0", "error_class": "crash"},
        {"cell_key": "sglang|h100-pcie-x1|a|c256|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "sglang", "engine_version": "0.5.20", "started_at": datetime(2026, 9, 25, 3, 0, tzinfo=timezone.utc)},
    ]
    for row in rows:
        row.setdefault("started_at", datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc))
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    done = recorded_cell_keys(st, Tier("nightly"), "aaaa", {"vllm": "0.30.0", "sglang": "0.5.20"})
    # every pie outcome at this commit counts, a crash included — not a cell the budget never reached, not another
    # commit, not a full row that served a miniature snapshot, not a noisy measurement; a baseline counts at its pinned
    # version whatever the pie commit, only when it passed (a baseline crash is a recipe fault, remeasured), and only
    # once the recipe followed the cell (an SGLang c256 captured at the first cell's ceiling ran eager: remeasured)
    assert done == {rows[0]["cell_key"], rows[1]["cell_key"], rows[3]["cell_key"]}
    assert recorded_cell_keys(st, Tier("smoke"), "aaaa") == set()


def test_recorded_ollama_cells_count_at_their_pin(tmp_path: Path):
    st = Store(tmp_path)
    out = st.records_dir / "targeted" / "2026-09" / "run1.parquet"
    out.parent.mkdir(parents=True)
    rows = [
        {"cell_key": "pie|m4-pro-48g|a|ob-story-200|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "pass", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|c4|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "crash", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|ob-512-200|text-completion-bench|tp1", "pie_commit": "bbbb", "status": "pass", "engine": "pie"},
        {"cell_key": "ollama|m4-pro-48g|a#t:1b|c4|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "ollama", "engine_version": "0.34.4"},
        {"cell_key": "ollama|m4-pro-48g|a#t:1b|ob-512-200|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "ollama", "engine_version": "0.33.0"},
        {"cell_key": "pie|m4-pro-48g|a|ctx-4k-256|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "not_run", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|ctx-8k-256|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "fail", "engine": "pie", "error_class": "harness_invalid"},
        {"cell_key": "pie|m4-pro-48g|a|ob-short-100|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "noisy", "engine": "pie"},
        {"cell_key": "ollama|m4-pro-48g|a#t:1b|ob-story-200|text-completion-bench|tp1", "pie_commit": None, "status": "fail", "engine": "ollama", "engine_version": "0.34.4", "error_class": "crash"},
    ]
    for row in rows:
        row.setdefault("started_at", datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc))
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    done = recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"ollama": "0.34.4"})
    assert done == {rows[0]["cell_key"], rows[1]["cell_key"], rows[3]["cell_key"]}
    assert recorded_cell_keys(st, Tier.TARGETED, "aaaa") == {rows[0]["cell_key"], rows[1]["cell_key"]}
    assert recorded_cell_keys(Store(tmp_path / "empty"), Tier.TARGETED, "aaaa") == set()


def test_a_cell_invalidated_later_in_its_run_is_measured_again(tmp_path: Path):
    st = Store(tmp_path)
    out = st.records_dir / "targeted" / "2026-09" / "run1.parquet"
    out.parent.mkdir(parents=True)
    key = "ollama|m5-max-48g|g#muse-glimmer:30b|c4|text-completion-bench|tp1"
    rows = [{"run_id": "r1", "cell_id": "x", "cell_key": key, "status": status, "engine": "ollama", "engine_version": "0.34.4",
             "started_at": datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc)} for status in ("pass", "noisy")]
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    assert recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"ollama": "0.34.4"}) == set()
