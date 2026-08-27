from typing import List, Optional, Dict, Any
import logging
from app.core.database import SupabaseDB
from app.schemas.search import SearchFilters, SearchResponse
from app.schemas.restaurants import RestaurantResponse
from app.schemas.menus import MenuItemResponse
from app.schemas.branches import NearbyRestaurantQuery

logger = logging.getLogger("foodbook.search_service")


class SearchService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def search(self, filters: SearchFilters) -> SearchResponse:
        """
        Comprehensive search engine across restaurants and menu items with filters and ranking.
        """
        applied_filters: Dict[str, Any] = {}
        query_text = (filters.query or "").strip()

        # Step 1: Query restaurants
        rest_filters: Dict[str, Any] = {"is_active": "eq.true"}

        if filters.cuisine:
            rest_filters["cuisines"] = f"cs.{{{filters.cuisine}}}"
            applied_filters["cuisine"] = filters.cuisine

        if filters.max_budget is not None:
            rest_filters["avg_price_per_person"] = f"lte.{filters.max_budget}"
            applied_filters["max_budget"] = filters.max_budget

        if filters.min_rating is not None:
            rest_filters["avg_rating"] = f"gte.{filters.min_rating}"
            applied_filters["min_rating"] = filters.min_rating

        if query_text:
            rest_filters["name"] = f"ilike.*{query_text}*"
            applied_filters["query"] = query_text

        restaurants_raw = await self.db.select(
            "restaurants",
            filters=rest_filters,
            order="avg_rating.desc,review_count.desc",
            limit=30
        ) or []

        # If location is provided, query nearby restaurants as well
        if filters.latitude is not None and filters.longitude is not None:
            applied_filters["location"] = {"lat": filters.latitude, "lon": filters.longitude}
            rpc_params: Dict[str, Any] = {
                "user_lat": filters.latitude,
                "user_lon": filters.longitude,
                "radius_meters": filters.radius_meters or 15000
            }
            if filters.max_budget is not None and filters.max_budget > 0:
                rpc_params["max_budget"] = filters.max_budget

            try:
                nearby = await self.db.rpc("get_nearby_restaurants", params=rpc_params) or []
                nearby_ids = {n["restaurant_id"] for n in nearby}
                # Prioritize nearby restaurants in ranking
                restaurants_raw.sort(
                    key=lambda r: 0 if r["id"] in nearby_ids else 1
                )
            except Exception as e:
                logger.debug(f"Geo search RPC skipped: {e}")

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
