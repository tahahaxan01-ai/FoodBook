from typing import List, Optional
from datetime import datetime, timezone
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.saved_restaurants import SavedRestaurantResponse
from app.schemas.restaurants import RestaurantResponse
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger("foodbook.saved_restaurant_service")


class SavedRestaurantService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def save_restaurant(self, user_id: str, restaurant_id: str) -> SavedRestaurantResponse:
        """
        Save/bookmark a restaurant for a user.
        """
        # Verify restaurant exists
        restaurant = await self.db.select("restaurants", filters={"id": f"eq.{restaurant_id}"}, single=True)
        if not restaurant:
            raise NotFoundException("Restaurant not found", error_code="RESTAURANT_NOT_FOUND")

        insert_data = {
            "user_id": user_id,
            "restaurant_id": restaurant_id
        }

        try:
            res = await self.db.insert("saved_restaurants", insert_data, upsert=True)
            record = res[0]
        except ConflictException:
            record = insert_data

        return SavedRestaurantResponse(
            user_id=user_id,
            restaurant_id=restaurant_id,
            created_at=record.get("created_at") or datetime.now(timezone.utc),
            restaurant=RestaurantResponse(**restaurant)
        )

    async def unsave_restaurant(self, user_id: str, restaurant_id: str) -> bool:
        """
        Remove a restaurant from user's saved list.
        """
        await self.db.delete(
            "saved_restaurants",
            filters={"user_id": f"eq.{user_id}", "restaurant_id": f"eq.{restaurant_id}"}
        )
        return True

    async def is_saved(self, user_id: str, restaurant_id: str) -> bool:
        rec = await self.db.select(
            "saved_restaurants",
            filters={"user_id": f"eq.{user_id}", "restaurant_id": f"eq.{restaurant_id}"},
            single=True
        )
        return bool(rec)

    async def get_saved_restaurants(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[SavedRestaurantResponse]:
        """
        List all saved restaurants for a user with pagination.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        all_saved = await self.db.select("saved_restaurants", columns="restaurant_id", filters={"user_id": f"eq.{user_id}"})
        total = len(all_saved) if isinstance(all_saved, list) else 0

        saved_records = await self.db.select(
            "saved_restaurants",
            filters={"user_id": f"eq.{user_id}"},
            order="created_at.desc",
            limit=page_size,
            offset=offset
        ) or []

        items = []
        for s in saved_records:
            rest = await self.db.select("restaurants", filters={"id": f"eq.{s['restaurant_id']}"}, single=True)
            if rest:
                items.append(SavedRestaurantResponse(
                    user_id=user_id,
                    restaurant_id=s["restaurant_id"],
                    created_at=s.get("created_at"),
                    restaurant=RestaurantResponse(**rest)
                ))

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
