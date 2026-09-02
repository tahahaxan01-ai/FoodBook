from typing import List, Optional, Dict, Any
import re
import logging
import httpx
from app.core.config import settings
from app.core.database import SupabaseDB
from app.schemas.search import SearchFilters, SearchResponse
from app.schemas.restaurants import RestaurantResponse
from app.schemas.menus import MenuItemResponse
from app.schemas.branches import NearbyRestaurantQuery
from app.services.recommendation_service import cosine_similarity

logger = logging.getLogger("foodbook.search_service")

_QUERY_CUISINES = [
    "pizza", "pakistani", "chinese", "italian", "bbq", "fast food", "desi",
    "continental", "biryani", "burger", "sushi", "thai", "cafe", "lebanese", "mediterranean",
]

# Acronyms and multi-word cuisines that don't survive str.title() correctly
# (e.g. "bbq".title() == "Bbq", not "BBQ") get an explicit mapping; everything
# else falls through to .title(), matching how the OSM seeder capitalizes
# cuisine tags when it writes them into the `restaurants` table.
_CUISINE_CANONICAL_OVERRIDES = {"bbq": "BBQ"}


def _normalize_cuisine(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    lower = raw.strip().lower()
    return _CUISINE_CANONICAL_OVERRIDES.get(lower, raw.strip().title())


def _parse_query_fallback(query_text: str) -> Dict[str, Any]:
    """Zero-dependency query parser, used when the ML service is unreachable."""
    lower = query_text.lower()
    cuisine = next((c for c in _QUERY_CUISINES if c in lower), None)
    budget_match = re.search(r"(?:rs\.?|pkr|under|below)\s*[:\-]?\s*(\d{2,6})", lower)
    max_budget = float(budget_match.group(1)) if budget_match else None
    spice_level = None
    if any(w in lower for w in ["extra spicy", "very spicy", "spicy", "hot", "chili", "chilli"]):
        spice_level = "high"
    elif any(w in lower for w in ["mild", "not spicy", "less spicy"]):
        spice_level = "low"
    return {"cuisine": cuisine, "max_budget": max_budget, "spice_level": spice_level}


class SearchService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def _parse_query(self, query_text: str) -> Dict[str, Any]:
        """
        AI Food Finder: turn a free-text query ("spicy pizza under 1500") into
        structured filters. Tries the ML service's NLP parser first, falls
        back to a local regex/keyword parser so search never breaks.
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=2.0)) as client:
                res = await client.post(
                    f"{settings.RECOMMENDATION_SERVICE_URL.rstrip('/')}/search/parse-query",
                    json={"query": query_text}
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug(f"AI query parser unavailable ({e}), using local fallback")
        return _parse_query_fallback(query_text)

    async def search(self, filters: SearchFilters) -> SearchResponse:
        """
        Comprehensive search engine across restaurants and menu items with filters and ranking.
        """
        applied_filters: Dict[str, Any] = {}
        query_text = (filters.query or "").strip()

        parsed: Dict[str, Any] = {}
        if query_text:
            parsed = await self._parse_query(query_text)

        effective_cuisine = filters.cuisine or _normalize_cuisine(parsed.get("cuisine"))
        effective_budget = filters.max_budget if filters.max_budget is not None else parsed.get("max_budget")
        spice_level = parsed.get("spice_level")

        # Step 1: Query restaurants
        rest_filters: Dict[str, Any] = {"is_active": "eq.true"}

        if effective_cuisine:
            rest_filters["cuisines"] = f"cs.{{{effective_cuisine}}}"
            applied_filters["cuisine"] = effective_cuisine
            if not filters.cuisine:
                applied_filters["ai_detected_cuisine"] = effective_cuisine

        if effective_budget is not None:
            rest_filters["avg_price_per_person"] = f"lte.{effective_budget}"
            applied_filters["max_budget"] = effective_budget
            if filters.max_budget is None:
                applied_filters["ai_detected_budget"] = effective_budget

        if filters.min_rating is not None:
            rest_filters["avg_rating"] = f"gte.{filters.min_rating}"
            applied_filters["min_rating"] = filters.min_rating

        if query_text:
            rest_filters["name"] = f"ilike.*{query_text}*"
            applied_filters["query"] = query_text

        if spice_level:
            applied_filters["ai_detected_spice_level"] = spice_level

        restaurants_raw = await self.db.select(
            "restaurants",
            filters=rest_filters,
            order="avg_rating.desc,review_count.desc",
            limit=30
        ) or []

        # If a free-text query matched no restaurant by name, widen the net:
        # search by cuisine/spice signal alone so "spicy karahi" still returns
        # results even when no restaurant is literally named "karahi".
        if query_text and not restaurants_raw and (effective_cuisine or spice_level):
            widened_filters = {k: v for k, v in rest_filters.items() if k != "name"}
            restaurants_raw = await self.db.select(
                "restaurants", filters=widened_filters,
                order="avg_rating.desc,review_count.desc", limit=30
            ) or []

        # If location is provided, query nearby restaurants as well
        nearby_ids: set = set()
        if filters.latitude is not None and filters.longitude is not None:
            applied_filters["location"] = {"lat": filters.latitude, "lon": filters.longitude}
            rpc_params: Dict[str, Any] = {
                "user_lat": filters.latitude,
                "user_lon": filters.longitude,
                "radius_meters": filters.radius_meters or 15000
            }
            if effective_budget is not None and effective_budget > 0:
                rpc_params["max_budget"] = effective_budget

            try:
                nearby = await self.db.rpc("get_nearby_restaurants", params=rpc_params) or []
                nearby_ids = {n["restaurant_id"] for n in nearby}
            except Exception as e:
                logger.debug(f"Geo search RPC skipped: {e}")

        # Unified ranking pass: proximity, then explicit taste-vector match
        # (if the caller supplied one), then detected spice preference.
        target_vector = filters.taste_vector
        if target_vector and len(target_vector) == 9:
            applied_filters["taste_vector_ranked"] = True

        def _rank_key(r: Dict[str, Any]):
            near_rank = 0 if (nearby_ids and r["id"] in nearby_ids) else 1
            taste_rank = 0.0
            if target_vector and len(target_vector) == 9:
                rest_vec = r.get("aggregated_taste_vector") or r.get("base_taste_vector") or [0.5] * 9
                taste_rank = -cosine_similarity(target_vector, rest_vec)
            spice_rank = 0
            if spice_level:
                spicy_val = (r.get("base_taste_vector") or [0.5])[0]
                wants_high = spice_level == "high"
                matches = spicy_val >= 0.6 if wants_high else spicy_val <= 0.4
                spice_rank = 0 if matches else 1
            return (near_rank, taste_rank, spice_rank)

        if nearby_ids or target_vector or spice_level:
            restaurants_raw.sort(key=_rank_key)

        # Step 2: Query menu items matching query if query text present
        menu_items_raw: List[Dict[str, Any]] = []
        if query_text:
            item_filters = {
                "name": f"ilike.*{query_text}*",
                "is_available": "eq.true"
            }
            if filters.max_budget is not None:
                item_filters["price"] = f"lte.{filters.max_budget}"

            menu_items_raw = await self.db.select(
                "menu_items",
                filters=item_filters,
                limit=20
            ) or []

        matched_restaurants = [RestaurantResponse(**r) for r in restaurants_raw]
        matched_items = [MenuItemResponse(**m) for m in menu_items_raw]

        return SearchResponse(
            restaurants=matched_restaurants,
            menu_items=matched_items,
            total_matches=len(matched_restaurants) + len(matched_items),
            query=query_text or None,
            applied_filters=applied_filters
        )
