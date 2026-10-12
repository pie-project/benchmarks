from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from pie_evals.plan.jobs import recorded_cell_keys
from pie_evals.results.store import Store
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


def test_recorded_baseline_cells_count_at_their_pin(tmp_path: Path):
    st = Store(tmp_path)
    out = st.records_dir / "targeted" / "2026-09" / "run1.parquet"
    out.parent.mkdir(parents=True)
    rows = [
        {"cell_key": "pie|m4-pro-48g|a|ob-story-200|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "pass", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|c4|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "crash", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|ob-512-200|text-completion-bench|tp1", "pie_commit": "bbbb", "status": "pass", "engine": "pie"},
        {"cell_key": "splash|m4-pro-48g|a#Splash|c4|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "splash", "engine_version": "1.1.0"},
        {"cell_key": "splash|m4-pro-48g|a#Splash|ob-512-200|text-completion-bench|tp1", "pie_commit": None, "status": "pass", "engine": "splash", "engine_version": "1.0.0"},
        {"cell_key": "pie|m4-pro-48g|a|ctx-4k-256|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "not_run", "engine": "pie"},
        {"cell_key": "pie|m4-pro-48g|a|ctx-8k-256|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "fail", "engine": "pie", "error_class": "harness_invalid"},
        {"cell_key": "pie|m4-pro-48g|a|ob-short-100|text-completion-bench|tp1", "pie_commit": "aaaa", "status": "noisy", "engine": "pie"},
        {"cell_key": "splash|m4-pro-48g|a#Splash|ob-story-200|text-completion-bench|tp1", "pie_commit": None, "status": "fail", "engine": "splash", "engine_version": "1.1.0", "error_class": "crash"},
    ]
    for row in rows:
        row.setdefault("started_at", datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc))
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    done = recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"splash": "1.1.0"})
    assert done == {rows[0]["cell_key"], rows[1]["cell_key"], rows[3]["cell_key"]}
    assert recorded_cell_keys(st, Tier.TARGETED, "aaaa") == {rows[0]["cell_key"], rows[1]["cell_key"]}
    assert recorded_cell_keys(Store(tmp_path / "empty"), Tier.TARGETED, "aaaa") == set()


def test_a_cell_invalidated_later_in_its_run_is_measured_again(tmp_path: Path):
    st = Store(tmp_path)
    out = st.records_dir / "targeted" / "2026-09" / "run1.parquet"
    out.parent.mkdir(parents=True)
    key = "splash|m5-max-48g|g#Splash|c4|text-completion-bench|tp1"
    rows = [{"run_id": "r1", "cell_id": "x", "cell_key": key, "status": status, "engine": "splash", "engine_version": "1.1.0",
             "started_at": datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc)} for status in ("pass", "noisy")]
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    assert recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"splash": "1.1.0"}) == set()


def _baseline_rows(tmp_path: Path, rows: list[dict]) -> Store:
    st = Store(tmp_path)
    out = st.records_dir / "targeted" / "2026-10" / "run1.parquet"
    out.parent.mkdir(parents=True)
    for i, row in enumerate(rows):
        row.setdefault("run_id", f"r{i}")
        row.setdefault("cell_id", row["cell_key"])
        row.setdefault("started_at", datetime(2026, 10, 1, 8, i, tzinfo=timezone.utc))
    cols = {name: [row.get(name) for row in rows] for name in ARROW_SCHEMA.names}
    pq.write_table(pa.table(cols, schema=ARROW_SCHEMA), out)
    return st


def test_a_baseline_that_updated_itself_past_its_pin_still_counts(tmp_path: Path):
    key = lambda engine, wl: f"{engine}|m5-max-48g|a|{wl}|text-completion-bench|tp1"  # noqa: E731
    st = _baseline_rows(tmp_path, [
        {"cell_key": key("splash", "c4"), "status": "pass", "engine": "splash", "engine_version": "1.2.0"},
        {"cell_key": key("splash", "ob-512-200"), "status": "pass", "engine": "splash", "engine_version": "1.1.9"},
        {"cell_key": key("llamacpp", "c4"), "status": "pass", "engine": "llamacpp", "engine_version": "b11400"},
        {"cell_key": key("llamacpp", "ob-512-200"), "status": "pass", "engine": "llamacpp", "engine_version": "unknown"},
    ])
    done = recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"splash": "1.2.0", "llamacpp": "b11312"})
    assert done == {key("splash", "c4"), key("llamacpp", "c4")}  # at the pin or newer; older or unreadable is measured again


def test_a_baseline_that_is_noisy_twice_is_kept_as_measured(tmp_path: Path):
    key = lambda wl: f"splash|m5-max-48g|a|{wl}|text-completion-bench|tp1"  # noqa: E731
    noisy = {"status": "noisy", "engine": "splash", "engine_version": "1.1.0"}
    st = _baseline_rows(tmp_path, [
        {"cell_key": key("c4"), **noisy}, {"cell_key": key("c4"), **noisy},
        {"cell_key": key("ob-512-200"), **noisy},
        {"cell_key": key("ctx-4k-256"), **noisy}, {"cell_key": key("ctx-4k-256"), **noisy, "error_class": "harness_invalid"},
    ])
    # once is chance and is tried again; twice is the engine's nature; a run the harness spoiled does not count
    assert recorded_cell_keys(st, Tier.TARGETED, "aaaa", {"splash": "1.1.0"}) == {key("c4")}
