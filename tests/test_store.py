def test_a_newer_good_row_replaces_the_stored_one_under_a_tag():
    from pie_bench.results.store import _tag_keep

    class Cur:
        def __init__(self, stored):
            self.stored, self.deleted = stored, []

        def execute(self, sql, args):
            if sql.startswith("DELETE"):
                self.deleted += args[1]

        def fetchall(self):
            return self.stored

    cols = ["cell_key", "status", "decode_tok_s", "prefill_tok_s"]
    stored = [("a", "pass", 10.0, None), ("b", "pass", 10.0, None), ("c", "fail", None, None)]
    rows = [("a", "pass", 11.0, 500.0), ("b", "fail", None, None), ("c", "pass", 9.0, 300.0)]
    cur = Cur(stored)
    keep = _tag_keep(cur, rows, "0.5.3-b1", cols)
    assert keep == {"b"}
    assert sorted(cur.deleted) == ["a", "c"]
