from types import SimpleNamespace as P

from pie_bench.runner.round_checks import expected_requests, round_problem


def perf(requests=8, failed=0, prompt_tokens=4440):
    return P(requests=requests, failed=failed, prompt_tokens=prompt_tokens)


def test_the_request_count_comes_from_the_client_flags():
    assert expected_requests(["--requests", "8"]) == 8
    assert expected_requests(["--num-requests", "128", "--concurrency", "32"]) == 128
    assert expected_requests(["--concurrency", "32"]) is None


def test_rounds_that_did_the_asked_work_pass():
    assert round_problem(8, [perf(), perf(prompt_tokens=4450), perf(prompt_tokens=4430)]) is None


def test_a_failed_request_in_any_round_fails_the_cell():
    assert "round 2" in round_problem(8, [perf(), perf(failed=1), perf()])


def test_a_round_that_ran_fewer_requests_fails_the_cell():
    assert "ran 7 of 8" in round_problem(8, [perf(), perf(requests=7)])


def test_rounds_on_different_prompts_fail_the_cell():
    assert "different prompts" in round_problem(8, [perf(prompt_tokens=4440), perf(prompt_tokens=3000)])
