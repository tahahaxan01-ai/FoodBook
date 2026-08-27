from typing import List, Optional, Dict, Any, Tuple
import re
import logging
from datetime import datetime, timezone
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.schemas.restaurants import (
    RestaurantResponse,
    RestaurantDetailResponse,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantFilterParams
)
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger("foodbook.restaurant_service")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


class RestaurantService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def list_restaurants(
        self,
        filters: Optional[RestaurantFilterParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[RestaurantResponse]:
        """
        List restaurants with filtering and pagination.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        query_filters: Dict[str, Any] = {}
        if filters:
            if filters.is_active is not None:
                query_filters["is_active"] = f"eq.{str(filters.is_active).lower()}"
            if filters.max_budget is not None:
                query_filters["avg_price_per_person"] = f"lte.{filters.max_budget}"
            if filters.min_rating is not None:
                query_filters["avg_rating"] = f"gte.{filters.min_rating}"
            if filters.cuisine:
                query_filters["cuisines"] = f"cs.{{{filters.cuisine}}}"
            if filters.search:
                query_filters["name"] = f"ilike.*{filters.search}*"

        # Get total count
        all_records = await self.db.select(
            "restaurants",
            columns="id",
            filters=query_filters
        )
        total_count = len(all_records) if isinstance(all_records, list) else 0

        # Get page records
        records = await self.db.select(
            "restaurants",
            filters=query_filters,
            order="avg_rating.desc,review_count.desc,created_at.desc",
            limit=page_size,
            offset=offset
        )

        items = [RestaurantResponse(**r) for r in (records or [])]
        return PaginatedResponse.create(items=items, total=total_count, page=page, page_size=page_size)

    async def get_restaurant_by_id(self, restaurant_id: str, current_user_id: Optional[str] = None) -> RestaurantDetailResponse:
        """
        Get full restaurant details by ID, including branches, menu categories with items, and reviews.
        """
        restaurant = await self.db.select("restaurants", filters={"id": f"eq.{restaurant_id}"}, single=True)
        if not restaurant:
            raise NotFoundException(f"Restaurant with ID {restaurant_id} not found", error_code="RESTAURANT_NOT_FOUND")

        # Fetch branches
        branches = await self.db.select("restaurant_branches", filters={"restaurant_id": f"eq.{restaurant_id}"}) or []

        # Fetch menu categories
        categories = await self.db.select(
            "menu_categories",
            filters={"restaurant_id": f"eq.{restaurant_id}"},
            order="display_order.asc"
        ) or []

        # Fetch all menu items for the restaurant
        menu_items = await self.db.select(
            "menu_items",
            filters={"restaurant_id": f"eq.{restaurant_id}"}
        ) or []

        # Nest items inside categories for structured response
        categories_with_items = []
        for cat in categories:
            cat_items = [item for item in menu_items if item.get("category_id") == cat["id"]]
            categories_with_items.append({
                **cat,
                "items": cat_items
            })

        # Fetch recent reviews
        recent_reviews = await self.db.select(
            "reviews",
            filters={"restaurant_id": f"eq.{restaurant_id}"},
            order="created_at.desc",
            limit=5
        ) or []

        # Check if saved by current user
        is_saved = False
        if current_user_id:
            saved_record = await self.db.select(
                "saved_restaurants",
                filters={"user_id": f"eq.{current_user_id}", "restaurant_id": f"eq.{restaurant_id}"},
                single=True
            )
            is_saved = bool(saved_record)

        return RestaurantDetailResponse(
            **restaurant,
            branches=branches,
            menu_categories=categories_with_items,
            recent_reviews=recent_reviews,
            is_saved=is_saved
        )

    async def get_restaurant_by_slug(self, slug: str, current_user_id: Optional[str] = None) -> RestaurantDetailResponse:
        """
        Get full restaurant details by unique slug.
        """
        restaurant = await self.db.select("restaurants", filters={"slug": f"eq.{slug}"}, single=True)
        if not restaurant:
            raise NotFoundException(f"Restaurant with slug '{slug}' not found", error_code="RESTAURANT_NOT_FOUND")
        return await self.get_restaurant_by_id(restaurant["id"], current_user_id=current_user_id)

    async def create_restaurant(self, data: RestaurantCreate) -> RestaurantResponse:
        """
        Create a new restaurant profile.
        """
        slug = data.slug or slugify(data.name)
        # Check slug uniqueness
        existing = await self.db.select("restaurants", filters={"slug": f"eq.{slug}"}, single=True)
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        base_vector = data.base_taste_vector or [0.5]*9
        insert_data = {
            "name": data.name,
            "slug": slug,
            "cuisines": data.cuisines,
            "avg_price_per_person": data.avg_price_per_person,
            "base_taste_vector": base_vector,
            "aggregated_taste_vector": base_vector,
            "review_count": 0,
            "avg_rating": 0.0,
            "is_active": data.is_active
        }

        created = await self.db.insert("restaurants", insert_data)
        return RestaurantResponse(**created[0])

    async def update_restaurant(self, restaurant_id: str, data: RestaurantUpdate) -> RestaurantResponse:
        """
        Update restaurant information.
        """
        # Ensure exists
        await self.get_restaurant_by_id(restaurant_id)

        update_data: Dict[str, Any] = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.slug is not None:
            update_data["slug"] = data.slug
        if data.cuisines is not None:
            update_data["cuisines"] = data.cuisines
        if data.avg_price_per_person is not None:
            update_data["avg_price_per_person"] = data.avg_price_per_person
        if data.base_taste_vector is not None:
            update_data["base_taste_vector"] = data.base_taste_vector
        if data.is_active is not None:
            update_data["is_active"] = data.is_active

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        updated = await self.db.update("restaurants", data=update_data, filters={"id": f"eq.{restaurant_id}"})
        return RestaurantResponse(**updated[0])
