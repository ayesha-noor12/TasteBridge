from app import config, ranker
from tests.helpers import cand, profile


def test_weights_sum_to_one():
    assert abs(sum(config.WEIGHTS.values()) - 1.0) < 1e-9


def test_deterministic_ordering_and_name_tiebreak():
    cs = [cand("b"), cand("a"), cand("c")]
    first = [c.id for c, _ in ranker.rank(cs, profile())]
    assert first == ["a", "b", "c"]
    assert first == [c.id for c, _ in ranker.rank(list(reversed(cs)), profile())]


def test_slider_extremes():
    fam, disc = cand("fam", mode="familiar"), cand("disc", mode="discover")
    assert ranker.rank([fam, disc], profile(familiarity=0))[0][0].id == "disc"
    assert ranker.rank([fam, disc], profile(familiarity=1))[0][0].id == "fam"


def test_curated_cannot_outrank_qloo_on_taste():
    q = cand("q", source="qloo", rank=10, total=10, name="z-qloo")
    c = cand("c", source="curated", name="a-curated")
    assert ranker.taste_match(c) == 0.0
    assert ranker.taste_match(q) > 0.0
    assert ranker.rank([c, q], profile())[0][0].id == "q"


def test_affordability_and_proximity_clip():
    p = profile(budget_per_activity_cad=20, max_travel_minutes=40)
    assert ranker.affordability(cand("x", cost=40), p) == 0.0
    assert ranker.affordability(cand("x", cost=0), p) == 1.0
    assert ranker.affordability(cand("x"), p) == 0.0
    assert ranker.proximity(cand("x", travel=10), p) == 0.75


def test_social_boost_raises_social_items():
    s, n = cand("social", social=True, category="music"), cand("nonsocial", category="food")
    base = ranker.score(s, profile())
    assert ranker.score(s, profile(), social_boost=0.5) > base
    assert ranker.score(n, profile(), social_boost=0.5) == ranker.score(n, profile())
