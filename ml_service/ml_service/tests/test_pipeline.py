"""
End-to-end smoke tests for the recommendation pipeline.
Run with: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.schemas import Restaurant, UserInteraction, Review
from app.core.taste_profile import build_taste_profile
from app.core.recommender import recommend, content_based_scores, to_match_score
from app.core.aspect_sentiment import analyze_review
from app.core.search_ai import parse_query_rule_based
from app.core.evaluation import precision_at_k, recall_at_k, ndcg_at_k


def _sample_restaurants():
    return [
        Restaurant(restaurant_id="r1", name="Cheezious Pizza", cuisine=["pizza"],
                   price_band=2, tags=["cheesy", "spicy"]),
        Restaurant(restaurant_id="r2", name="Broadway Pizza", cuisine=["pizza"],
                   price_band=2, tags=["cheesy", "family"]),
        Restaurant(restaurant_id="r3", name="Bundu Khan", cuisine=["pakistani", "bbq"],
                   price_band=3, tags=["spicy", "bbq"]),
        Restaurant(restaurant_id="r4", name="Sushi One", cuisine=["sushi"],
                   price_band=4, tags=["light", "raw"]),
    ]


def test_taste_profile_reflects_liked_restaurant():
    restaurants = {r.restaurant_id: r for r in _sample_restaurants()}
    interactions = [
        UserInteraction(user_id="u1", restaurant_id="r1", rating=5, liked=True),
    ]
    profile = build_taste_profile("u1", interactions, restaurants)
    assert profile.cuisine_weights.get("pizza", 0) > 0
    assert "cheesy" in profile.tag_weights


def test_content_based_recommends_similar_not_identical():
    restaurants = _sample_restaurants()
    restaurants_by_id = {r.restaurant_id: r for r in restaurants}
    interactions = [UserInteraction(user_id="u1", restaurant_id="r1", rating=5, liked=True)]
    profile = build_taste_profile("u1", interactions, restaurants_by_id)

    recs = recommend(profile, restaurants, interactions, top_k=3)
    rec_ids = [r.restaurant_id for r in recs]

    assert "r1" not in rec_ids, "should not recommend a restaurant the user already tried"
    assert "r2" in rec_ids, "Broadway Pizza shares cuisine+tag with liked restaurant, should surface"
    assert recs[0].match_score >= 0 and recs[0].match_score <= 100
    assert "Recommended because" in recs[0].explanation


def test_aspect_sentiment_splits_mixed_review():
    review = Review(review_id="rev1", user_id="u1", restaurant_id="r1",
                     text="Pizza was delicious but too oily.")
    analysis = analyze_review(review)
    aspects_by_name = {a.aspect: a for a in analysis.aspects}
    assert "taste" in aspects_by_name
    assert aspects_by_name["taste"].sentiment == "positive"


def test_search_ai_extracts_filters():
    parsed = parse_query_rule_based("I want spicy cheesy pizza under Rs. 1500 near Johar Town")
    assert parsed.cuisine == "pizza"
    assert parsed.max_budget == 1500
    assert parsed.spice_level == "high"
    assert "johar town" in parsed.location.lower()


def test_evaluation_metrics_sane_ranges():
    recommended = ["r1", "r2", "r3", "r4"]
    relevant = {"r2", "r4"}
    p = precision_at_k(recommended, relevant, k=4)
    r = recall_at_k(recommended, relevant, k=4)
    n = ndcg_at_k(recommended, relevant, k=4)
    assert 0 <= p <= 1 and 0 <= r <= 1 and 0 <= n <= 1
    assert p == 0.5
    assert r == 1.0


def test_match_score_bounds():
    assert to_match_score(1.5) == 100
    assert to_match_score(-0.5) == 0
    assert to_match_score(0.92) == 92
