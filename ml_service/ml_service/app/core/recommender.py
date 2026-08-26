"""
Restaurant Similarity, Recommendation Engine, Collaborative Filtering, Hybrid,
Match Score, and Explainability — all live here because in v1 they share one
vector space (taste profile <-> restaurant feature vector), so keeping them
together avoids duplicating the vectorization logic.
"""
import math
from collections import defaultdict
from app.models.schemas import TasteProfile, Restaurant, UserInteraction, Recommendation


def _restaurant_vector(restaurant: Restaurant, vocab: dict[str, int]) -> list[float]:
    vec = [0.0] * len(vocab)
    for c in restaurant.cuisine:
        key = f"cuisine::{c}"
        if key in vocab:
            vec[vocab[key]] = 1.0
    for t in restaurant.tags:
        key = f"tag::{t}"
        if key in vocab:
            vec[vocab[key]] = 1.0
    return vec


def _profile_vector(profile: TasteProfile, vocab: dict[str, int]) -> list[float]:
    vec = [0.0] * len(vocab)
    for c, w in profile.cuisine_weights.items():
        key = f"cuisine::{c}"
        if key in vocab:
            vec[vocab[key]] = w
    for t, w in profile.tag_weights.items():
        key = f"tag::{t}"
        if key in vocab:
            vec[vocab[key]] = w
    return vec


def _build_vocab(restaurants: list[Restaurant]) -> dict[str, int]:
    vocab: dict[str, int] = {}
    for r in restaurants:
        for c in r.cuisine:
            vocab.setdefault(f"cuisine::{c}", len(vocab))
        for t in r.tags:
            vocab.setdefault(f"tag::{t}", len(vocab))
    return vocab


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def content_based_scores(
    profile: TasteProfile,
    restaurants: list[Restaurant],
) -> dict[str, float]:
    """Restaurant Similarity + core of the Recommendation Engine.
    Returns restaurant_id -> similarity score (0..1)."""
    vocab = _build_vocab(restaurants)
    p_vec = _profile_vector(profile, vocab)

    scores: dict[str, float] = {}
    for r in restaurants:
        r_vec = _restaurant_vector(r, vocab)
        sim = cosine_similarity(p_vec, r_vec)

        # soft penalty if price is far from the user's typical spend band
        price_gap = abs(r.price_band - profile.price_band_pref)
        price_penalty = max(0.0, 1 - price_gap * 0.15)

        scores[r.restaurant_id] = sim * price_penalty
    return scores


def collaborative_scores(
    target_user_id: str,
    interactions: list[UserInteraction],
    k_neighbors: int = 5,
) -> dict[str, float]:
    """
    User-based Collaborative Filtering (v1: simple, explainable).
    "Users with a similar rating pattern to you also liked these restaurants."

    Note: needs real interaction volume to be useful — with a small early
    user base this will return few/no results, which is expected. That's why
    the hybrid layer below falls back gracefully to content-based scores.
    """
    # build user -> {restaurant: rating} matrix
    user_ratings: dict[str, dict[str, float]] = defaultdict(dict)
    for i in interactions:
        if i.rating is not None:
            user_ratings[i.user_id][i.restaurant_id] = i.rating
        elif i.liked:
            user_ratings[i.user_id][i.restaurant_id] = 5.0

    target_ratings = user_ratings.get(target_user_id, {})
    if not target_ratings:
        return {}

    # similarity between target user and every other user (cosine over shared restaurants)
    similarities: list[tuple[str, float]] = []
    for other_id, other_ratings in user_ratings.items():
        if other_id == target_user_id:
            continue
        shared = set(target_ratings) & set(other_ratings)
        if not shared:
            continue
        a = [target_ratings[r] for r in shared]
        b = [other_ratings[r] for r in shared]
        sim = cosine_similarity(a, b)
        if sim > 0:
            similarities.append((other_id, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    top_neighbors = similarities[:k_neighbors]

    scores: dict[str, float] = defaultdict(float)
    weight_total = sum(sim for _, sim in top_neighbors) or 1.0
    for neighbor_id, sim in top_neighbors:
        for restaurant_id, rating in user_ratings[neighbor_id].items():
            if restaurant_id in target_ratings:
                continue  # already tried it
            scores[restaurant_id] += (rating / 5.0) * (sim / weight_total)

    return dict(scores)


def hybrid_scores(
    content: dict[str, float],
    collaborative: dict[str, float],
    content_weight: float = 0.7,
) -> dict[str, float]:
    """
    Combine content-based + collaborative into one score.
    Defaults to weighting content higher, since CF is sparse/unreliable early on
    (cold-start). As interaction volume grows, lower content_weight over time.
    """
    all_ids = set(content) | set(collaborative)
    combined = {}
    for rid in all_ids:
        c = content.get(rid, 0.0)
        cf = collaborative.get(rid, 0.0)
        combined[rid] = content_weight * c + (1 - content_weight) * cf
    return combined


def explain_recommendation(
    profile: TasteProfile,
    restaurant: Restaurant,
    liked_restaurant_name: str | None = None,
) -> str:
    """Explainability: turn the match into a human-readable reason."""
    top_cuisines = sorted(profile.cuisine_weights.items(), key=lambda x: -x[1])[:2]
    shared_cuisines = [c for c, _ in top_cuisines if c in restaurant.cuisine]
    top_tags = sorted(profile.tag_weights.items(), key=lambda x: -x[1])[:3]
    shared_tags = [t for t, _ in top_tags if t in restaurant.tags]

    reasons = []
    if liked_restaurant_name:
        reasons.append(f"you liked {liked_restaurant_name}")
    if shared_cuisines:
        reasons.append(f"you enjoy {', '.join(shared_cuisines)} food")
    if shared_tags:
        reasons.append(f"it matches your taste for {', '.join(shared_tags)}")

    if not reasons:
        return "This is a popular pick that fits your usual budget."
    return "Recommended because " + " and ".join(reasons) + "."


def to_match_score(raw_score: float) -> int:
    """Match Score: convert a 0..1 similarity into the '92% Taste Match' number."""
    return round(max(0.0, min(1.0, raw_score)) * 100)


def recommend(
    profile: TasteProfile,
    restaurants: list[Restaurant],
    interactions: list[UserInteraction],
    top_k: int = 10,
    max_budget: float | None = None,
) -> list[Recommendation]:
    """End-to-end: content + collaborative -> hybrid -> ranked, explained list."""
    content = content_based_scores(profile, restaurants)
    collaborative = collaborative_scores(profile.user_id, interactions)
    hybrid = hybrid_scores(content, collaborative)

    restaurants_by_id = {r.restaurant_id: r for r in restaurants}
    already_tried = {i.restaurant_id for i in interactions if i.user_id == profile.user_id}

    ranked = sorted(hybrid.items(), key=lambda x: x[1], reverse=True)

    results: list[Recommendation] = []
    for restaurant_id, score in ranked:
        if restaurant_id in already_tried:
            continue
        restaurant = restaurants_by_id.get(restaurant_id)
        if restaurant is None:
            continue
        if max_budget and restaurant.price_band > max_budget:
            continue

        source = "hybrid" if restaurant_id in collaborative else "content"
        results.append(Recommendation(
            restaurant_id=restaurant_id,
            name=restaurant.name,
            match_score=to_match_score(score),
            explanation=explain_recommendation(profile, restaurant),
            source=source,
        ))
        if len(results) >= top_k:
            break

    return results
