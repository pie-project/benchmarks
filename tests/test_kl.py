import math

from pie_evals.quality.kl import compare, partition_kl


def lp(probs: dict[int, float]) -> dict[int, float]:
    return {t: math.log(v) for t, v in probs.items()}


def test_the_same_list_is_zero():
    p = lp({1: 0.5, 2: 0.2, 3: 0.1})
    assert partition_kl(p, p) == 0.0


def test_lists_that_share_no_token_are_far_past_the_line():
    # the reference's top three hold 0.69; the other engine's top list holds none of them
    ref = lp({1: 0.23, 2: 0.23, 3: 0.23, 4: 0.07})
    other = lp({10: 0.3, 11: 0.2, 12: 0.1, 13: 0.05})
    assert partition_kl(ref, other) > 3 * 0.15
    assert compare([[ref]], [[other]], [0])["kl_mean"] > 3 * 0.15


def test_a_tie_broken_differently_stays_near_zero():
    # about 100 tokens tied at the softcap: each engine lists a different 20 of them, the same distribution
    ref = lp({t: 0.0097 for t in range(20)})
    other = lp({t: 0.0097 for t in range(50, 70)})
    assert partition_kl(ref, other) < 1e-3


def test_full_overlap_is_unchanged():
    # every reference token in the other's list: the cells are the reference's tokens and the rest, as before
    ref = lp({1: 0.6, 2: 0.3})
    other = lp({1: 0.5, 2: 0.3, 3: 0.1})
    want = 0.6 * math.log(0.6 / 0.5) + 0.3 * math.log(0.3 / 0.3) + 0.1 * math.log(0.1 / 0.2)
    assert abs(partition_kl(ref, other) - want) < 1e-12


def test_a_low_ranked_token_missing_moves_it_little():
    ref = lp({1: 0.6, 2: 0.3, 3: 0.004})
    other = lp({1: 0.6, 2: 0.3, 4: 0.005})
    assert partition_kl(ref, other) < 0.01
