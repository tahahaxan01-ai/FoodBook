"""
Database-backed recommendation engine (v2).

This is the real engine behind `POST /recommend`: it reads live restaurants
and review history straight from Supabase (no in-memory/demo store, no
staleness) and blends three signals:

  1. Content-based: cosine similarity between the user's 9D taste vector
     and each restaurant's taste vector, plus a cuisine-match bonus and a
     rating factor.
  2. Collaborative filtering: user-based CF over real star ratings pulled
     from the `reviews` table (reuses the generic, already-tested
     `collaborative_scores` from recommender.py — it only needs
     user/restaurant/rating rows, so it works unmodified against real data).
  3. Distance: via the same `get_nearby_restaurants` PostGIS RPC the
     backend uses, when the caller supplies coordinates.

Then a diversity pass keeps any single cuisine from dominating the top-N,
and each result gets a human-readable explanation.
"""
import math
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.core.database import db
from app.core.recommender import cosine_similarity, collaborative_scores, hybrid_scores
from app.models.schemas import UserInteraction

TASTE_DIMENSIONS = ["spicy", "sweet", "salty", "sour", "umami", "smoky", "creamy", "crispy", "rich"]


def _cuisine_bonus(restaurant_cuisines: List[str], preferred_cuisines: List[str]) -> float:
    if not preferred_cuisines or not restaurant_cuisines:
        return 0.0
    matches = sum(1 for c in restaurant_cuisines if c in preferred_cuisines)
    return min(1.0, matches / len(preferred_cuisines))


def _explain(
    taste_vector: List[float],
    restaurant: Dict[str, Any],
    preferred_cuisines: List[str],
    distance_meters: Optional[float],
    is_collaborative: bool,
) -> List[str]:
    reasons: List[str] = []
    rest_vec = restaurant.get("aggregated_taste_vector") or restaurant.get("base_taste_vector")

    if rest_vec and len(rest_vec) == 9 and len(taste_vector) == 9:
        prominent = [
            TASTE_DIMENSIONS[i] for i in range(9)
            if taste_vector[i] >= 0.6 and rest_vec[i] >= 0.6 and abs(taste_vector[i] - rest_vec[i]) <= 0.25
        ]
        if prominent:
            reasons.append(f"Matches your preference for {', '.join(prominent[:3])} food")

    cuisines = restaurant.get("cuisines") or []
    shared = [c for c in cuisines if c in preferred_cuisines]
    if shared:
        reasons.append(f"Specializes in your favorite {', '.join(shared[:2])} cuisine")

    if is_collaborative:
        reasons.append("Diners with a similar taste profile to you rated this highly")

    if distance_meters is not None:
        km = round(distance_meters / 1000, 1)
        if distance_meters < 2000:
            reasons.append(f"Very close to you ({km} km away)")
        elif distance_meters < 5000:
            reasons.append(f"Nearby in your area ({km} km away)")

    if not reasons:
        rating = restaurant.get("avg_rating") or 0
        reasons.append(f"Highly rated overall ({rating}★) and within your budget" if rating else "Popular pick that fits your budget")

    return reasons


def _diversify(ranked: List[tuple], restaurants_by_id: Dict[str, Dict[str, Any]], limit: int) -> List[tuple]:
    """Cap how many results share the same primary cuisine so top-N isn't one-note."""
    max_per_cuisine = max(2, math.ceil(limit / 3))
    cuisine_count: Dict[str, int] = defaultdict(int)
    kept, overflow = [], []

    for rid, score in ranked:
        cuisines = restaurants_by_id.get(rid, {}).get("cuisines") or ["Other"]
        primary = cuisines[0]
        if cuisine_count[primary] < max_per_cuisine:
            kept.append((rid, score))
            cuisine_count[primary] += 1
        else:
            overflow.append((rid, score))
        if len(kept) >= limit:
            break

    if len(kept) < limit:
        kept.extend(overflow[: limit - len(kept)])
    return kept[:limit]


async def recommend_from_database(
    taste_vector: List[float],
    preferred_cuisines: List[str],
    max_budget: Optional[float],
    latitude: Optional[float],
    longitude: Optional[float],
    radius_meters: int,
    limit: int,
    user_id: Optional[str],
) -> Dict[str, Any]:
    filters: Dict[str, Any] = {"is_active": "eq.true"}
    if max_budget:
        filters["avg_price_per_person"] = f"lte.{max_budget}"

    restaurants = await db.select("restaurants", filters=filters, limit=100)
    restaurants_by_id = {r["id"]: r for r in restaurants}

    # --- distance signal (optional) ---
    distance_map: Dict[str, float] = {}
    if latitude is not None and longitude is not None:
        rpc_params: Dict[str, Any] = {
            "user_lat": latitude,
            "user_lon": longitude,
            "radius_meters": radius_meters,
        }
        if max_budget:
            rpc_params["max_budget"] = max_budget
        nearby = await db.rpc("get_nearby_restaurants", params=rpc_params) or []
        for n in nearby:
            distance_map[n["restaurant_id"]] = float(n.get("distance_meters", 0.0))

    # --- content-based scores over the real 9D vectors ---
    content: Dict[str, float] = {}
    for r in restaurants:
        rest_vec = r.get("aggregated_taste_vector") or r.get("base_taste_vector") or [0.5] * 9
        taste_sim = cosine_similarity(taste_vector, rest_vec)
        cuisine_bonus = _cuisine_bonus(r.get("cuisines") or [], preferred_cuisines)
        rating_factor = min(1.0, float(r.get("avg_rating") or 0.0) / 5.0)

        dist = distance_map.get(r["id"])
        distance_factor = 0.0
        if dist is not None:
            distance_factor = max(0.0, 1 - dist / max(radius_meters, 1))

        content[r["id"]] = (
            taste_sim * 0.55
            + cuisine_bonus * 0.25
            + rating_factor * 0.10
            + distance_factor * 0.10
        )

    # --- real collaborative filtering from actual review ratings ---
    collaborative: Dict[str, float] = {}
    if user_id:
        review_rows = await db.select(
            "reviews", columns="user_id,restaurant_id,overall_rating", limit=5000
        )
        interactions = [
            UserInteraction(user_id=row["user_id"], restaurant_id=row["restaurant_id"], rating=row.get("overall_rating"))
            for row in review_rows
            if row.get("overall_rating") is not None
        ]
        collaborative = collaborative_scores(user_id, interactions)

    # weight CF higher when we actually have a real signal for this user (less cold-start)
    content_weight = 0.65 if collaborative else 1.0
    hybrid = hybrid_scores(content, collaborative, content_weight=content_weight)

    ranked = sorted(hybrid.items(), key=lambda x: x[1], reverse=True)
    ranked = _diversify(ranked, restaurants_by_id, limit)

    items = []
    for rid, score in ranked:
        restaurant = restaurants_by_id.get(rid)
        if not restaurant:
            continue
        pct = int(round(max(0.0, min(1.0, score)) * 100))
        items.append({
            "restaurant": restaurant,
            "match_score": round(max(0.0, min(1.0, score)), 3),
            "match_percentage": min(99, max(50, pct)),
            "reasons": _explain(taste_vector, restaurant, preferred_cuisines, distance_map.get(rid), rid in collaborative),
            "distance_meters": distance_map.get(rid),
        })

    return {
        "user_id": user_id,
        "total_recommendations": len(items),
        "recommendations": items,
        "model_version": "foodbook-ml-service-hybrid-v2",
    }
