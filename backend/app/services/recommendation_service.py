from typing import List, Optional, Dict, Any, Tuple
import math
import httpx
import logging
from app.core.config import settings
from app.core.database import SupabaseDB
from app.schemas.recommendations import (
    RecommendationRequest,
    RecommendationItem,
    RecommendationResponse
)
from app.schemas.restaurants import RestaurantResponse
from app.schemas.taste_profiles import TASTE_DIMENSIONS

logger = logging.getLogger("foodbook.recommendation_service")


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two 9-dimensional taste vectors.
    Returns float between 0.0 and 1.0.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.5

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.5

    sim = dot_product / (norm_a * norm_b)
    return max(0.0, min(1.0, sim))


def generate_taste_explanation(
    user_vector: List[float],
    restaurant_vector: List[float],
    cuisines: List[str],
    preferred_cuisines: List[str],
    distance_meters: Optional[float] = None
) -> List[str]:
    """
    Generate human-readable, explainable recommendation reasons.
    """
    reasons: List[str] = []

    # 1. Taste dimension matches
    if user_vector and restaurant_vector and len(user_vector) == 9 and len(restaurant_vector) == 9:
        prominent_matches = []
        for i, dim_name in enumerate(TASTE_DIMENSIONS):
            user_val = user_vector[i]
            rest_val = restaurant_vector[i]
            # Both user and restaurant score high on this dimension (>0.6) and are close
            if user_val >= 0.6 and rest_val >= 0.6 and abs(user_val - rest_val) <= 0.25:
                prominent_matches.append(dim_name)

        if prominent_matches:
            match_str = ", ".join(prominent_matches[:3])
            reasons.append(f"Matches your preference for {match_str} food")

    # 2. Cuisine preference matches
    if preferred_cuisines and cuisines:
        common_cuisines = [c for c in cuisines if c in preferred_cuisines]
        if common_cuisines:
            reasons.append(f"Specializes in your favorite {', '.join(common_cuisines[:2])} cuisine")

    # 3. Location proximity
    if distance_meters is not None:
        if distance_meters < 2000:
            reasons.append(f"Very close to you ({round(distance_meters/1000, 1)} km away)")
        elif distance_meters < 5000:
            reasons.append(f"Nearby in your area ({round(distance_meters/1000, 1)} km away)")

    if not reasons:
        reasons.append("High overall taste profile similarity with your preferences")

    return reasons


class RecommendationService:
    """
    Recommendation Engine Interface.
    Coordinates between user taste preferences, restaurant profiles, and Shehryar's AI/ML Service.
    """

    def __init__(self, db: SupabaseDB):
        self.db = db
        self.ml_service_url = settings.RECOMMENDATION_SERVICE_URL.rstrip("/")

    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Generate personalized restaurant recommendations.
        Attempts to call Shehryar's AI/ML service first.
        If unavailable, uses built-in vector similarity engine.
        """
        # Load user profile if user_id is provided
        user_vector = request.taste_vector
        preferred_cuisines = request.preferred_cuisines or []
        dietary_restrictions = request.dietary_restrictions or []
        budget = request.max_budget

        if request.user_id:
            profile = await self.db.select("user_taste_profiles", filters={"user_id": f"eq.{request.user_id}"}, single=True)
            if profile:
                user_vector = user_vector or profile.get("taste_vector")
                preferred_cuisines = preferred_cuisines or profile.get("preferred_cuisines") or []
                dietary_restrictions = dietary_restrictions or profile.get("dietary_restrictions") or []

        if not user_vector or len(user_vector) != 9:
            user_vector = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        # Check if Shehryar's AI/ML service is active
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                ml_payload = {
                    "user_id": request.user_id,
                    "taste_vector": user_vector,
                    "preferred_cuisines": preferred_cuisines,
                    "dietary_restrictions": dietary_restrictions,
                    "max_budget": budget,
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "limit": request.limit or 10
                }
                res = await client.post(f"{self.ml_service_url}/recommend", json=ml_payload)
                if res.status_code == 200:
                    ml_data = res.json()
                    logger.info("Successfully received recommendations from Shehryar's AI/ML service")
                    return RecommendationResponse(**ml_data)
        except Exception as e:
            logger.debug(f"AI/ML recommendation service not reachable ({e}). Using built-in taste vector matching.")

        # Built-in Recommendation Algorithm
        return await self._built_in_recommendations(
            user_vector=user_vector,
            preferred_cuisines=preferred_cuisines,
            budget=budget,
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters or 15000,
            limit=request.limit or 10,
            user_id=request.user_id
        )

    async def _built_in_recommendations(
        self,
        user_vector: List[float],
        preferred_cuisines: List[str],
        budget: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
        radius_meters: int,
        limit: int,
        user_id: Optional[str]
    ) -> RecommendationResponse:
        """
        Calculates similarity scores using cosine similarity on aggregated/base taste vectors,
        cuisine matching bonuses, and distance penalties.
        """
        # Fetch active restaurants
        filters: Dict[str, Any] = {"is_active": "eq.true"}
        if budget:
            filters["avg_price_per_person"] = f"lte.{budget}"

        restaurants = await self.db.select("restaurants", filters=filters, limit=50) or []

        # Fetch distances if coordinates available
        distance_map: Dict[str, float] = {}
        if latitude is not None and longitude is not None:
            rpc_params: Dict[str, Any] = {
                "user_lat": latitude,
                "user_lon": longitude,
                "radius_meters": radius_meters
            }
            if budget is not None and budget > 0:
                rpc_params["max_budget"] = budget

            try:
                nearby = await self.db.rpc("get_nearby_restaurants", params=rpc_params) or []
                for n in nearby:
                    distance_map[n["restaurant_id"]] = float(n.get("distance_meters", 0.0))
            except Exception as e:
                logger.debug(f"Geo RPC distance map failed: {e}")

        scored_items: List[Tuple[float, Dict[str, Any], Optional[float]]] = []

        for r in restaurants:
            rest_vector = r.get("aggregated_taste_vector") or r.get("base_taste_vector") or [0.5]*9
            # 1. Base taste similarity (weight: 0.6)
            taste_sim = cosine_similarity(user_vector, rest_vector)

            # 2. Cuisine bonus (weight: 0.25)
            cuisine_bonus = 0.0
            r_cuisines = r.get("cuisines") or []
            if preferred_cuisines and r_cuisines:
                matches = sum(1 for c in r_cuisines if c in preferred_cuisines)
                cuisine_bonus = min(1.0, matches / len(preferred_cuisines))

            # 3. Rating factor (weight: 0.15)
            rating_factor = min(1.0, float(r.get("avg_rating") or 0.0) / 5.0)

            # Combine score
            composite_score = (taste_sim * 0.60) + (cuisine_bonus * 0.25) + (rating_factor * 0.15)

            dist = distance_map.get(r["id"])
            scored_items.append((composite_score, r, dist))

        # Sort descending by composite score
        scored_items.sort(key=lambda x: x[0], reverse=True)

        recommendation_items: List[RecommendationItem] = []
        for score, r_data, dist in scored_items[:limit]:
            rest_vec = r_data.get("aggregated_taste_vector") or r_data.get("base_taste_vector") or [0.5]*9
            reasons = generate_taste_explanation(
                user_vector=user_vector,
                restaurant_vector=rest_vec,
                cuisines=r_data.get("cuisines") or [],
                preferred_cuisines=preferred_cuisines,
                distance_meters=dist
            )
            pct = int(round(score * 100))
            recommendation_items.append(
                RecommendationItem(
                    restaurant=RestaurantResponse(**r_data),
                    match_score=round(score, 3),
                    match_percentage=min(99, max(50, pct)),
                    reasons=reasons,
                    distance_meters=dist
                )
            )

        return RecommendationResponse(
            user_id=user_id,
            total_recommendations=len(recommendation_items),
            recommendations=recommendation_items,
            model_version="foodbook-vector-v1"
        )
