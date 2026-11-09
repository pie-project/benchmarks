from pie_evals.plan.changes import docs_only


def test_a_commit_of_docs_and_ci_files_is_docs_only():
    assert docs_only(["README.md", "docs/guide/intro.rst", ".github/workflows/ci.yml", "LICENSE"])


def test_one_code_file_makes_it_worth_measuring():
    assert not docs_only(["README.md", "crates/engine-metal/src/serve.rs"])
    assert not docs_only(["packages/python/client/src/pie_client/client.py"])


def test_an_unknown_change_list_is_measured():
    assert not docs_only([])
    assert not docs_only(["", "\n"])
