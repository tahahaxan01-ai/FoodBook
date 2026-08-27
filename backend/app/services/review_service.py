from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import httpx
import logging
from app.core.config import settings
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.schemas.reviews import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    ReviewDishRatingResponse,
    ReviewDishRatingCreate
)
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger("foodbook.review_service")

Tuple_Aspects_Vector = Tuple[Dict[str, Any], List[float]]


class ReviewService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def _extract_aspects_from_ai(self, review_text: str) -> Tuple_Aspects_Vector:
        """
        Calls Shehryar's ML service to extract structured aspects and 9-dim taste vector.
        Falls back to rule-based keyword extraction if ML service is unreachable.
        """
        if not review_text or len(review_text.strip()) == 0:
            return {}, [0.5]*9

        # Attempt to call ML service
        try:
            async with httpx.AsyncClient(timeout=0.5) as client:
                res = await client.post(
                    f"{settings.RECOMMENDATION_SERVICE_URL.rstrip('/')}/extract-aspects",
                    json={"text": review_text}
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("aspects", {}), data.get("taste_vector", [0.5]*9)
        except Exception as e:
            logger.debug(f"AI aspect extraction service unavailable ({e}), using default fallback")

        # Basic fallback heuristic
        aspects: Dict[str, Any] = {}
        # Simple taste keyword matching
        keywords = {
            "spicy": (0, 0.8), "mild": (0, 0.2), "sweet": (1, 0.8), "salty": (2, 0.7),
            "sour": (3, 0.7), "cheesy": (6, 0.9), "creamy": (6, 0.85),
            "crispy": (7, 0.85), "smoky": (5, 0.8), "rich": (8, 0.8)
        }
        vector = [0.5]*9
        txt_lower = review_text.lower()
        for kw, (idx, val) in keywords.items():
            if kw in txt_lower:
                vector[idx] = val
                aspects[kw] = "high"

        return aspects, vector

    async def create_review(self, user_id: str, data: ReviewCreate) -> ReviewResponse:
        """
        Create a new review, store dish ratings, and extract aspects.
        """
        # Validate restaurant exists
        restaurant = await self.db.select("restaurants", filters={"id": f"eq.{data.restaurant_id}"}, single=True)
        if not restaurant:
            raise NotFoundException("Restaurant not found", error_code="RESTAURANT_NOT_FOUND")

        # Aspects & taste vector extraction
        aspects = data.extracted_aspects
        taste_vector = data.extracted_taste_vector
        if aspects is None or taste_vector is None:
            extracted_asp, extracted_vec = await self._extract_aspects_from_ai(data.review_text or "")
            aspects = aspects or extracted_asp
            taste_vector = taste_vector or extracted_vec

        insert_data = {
            "user_id": user_id,
            "restaurant_id": data.restaurant_id,
            "branch_id": data.branch_id,
            "overall_rating": data.overall_rating,
            "review_text": data.review_text or "",
            "extracted_aspects": aspects,
            "extracted_taste_vector": taste_vector,
            "likes_count": 0
        }

        created = await self.db.insert("reviews", insert_data)
        review_record = created[0]
        review_id = review_record["id"]

        # Insert dish ratings if present
        dish_rating_responses: List[ReviewDishRatingResponse] = []
        if data.dish_ratings:
            dish_inserts = []
            for dr in data.dish_ratings:
                dish_inserts.append({
                    "review_id": review_id,
                    "menu_item_id": dr.menu_item_id,
                    "rating": dr.rating
                })
            created_dish_ratings = await self.db.insert("review_dish_ratings", dish_inserts)
            dish_rating_responses = [ReviewDishRatingResponse(**r) for r in (created_dish_ratings or [])]

        # Fetch user info
        user_info = await self.db.select("users", filters={"id": f"eq.{user_id}"}, single=True) or {}

        return ReviewResponse(
            **review_record,
            user_name=user_info.get("full_name", ""),
            user_avatar=user_info.get("avatar_url"),
            restaurant_name=restaurant.get("name", ""),
            dish_ratings=dish_rating_responses
        )

    async def get_restaurant_reviews(
        self,
        restaurant_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[ReviewResponse]:
        """
        List reviews for a specific restaurant.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        all_revs = await self.db.select("reviews", columns="id", filters={"restaurant_id": f"eq.{restaurant_id}"})
        total = len(all_revs) if isinstance(all_revs, list) else 0

        reviews = await self.db.select(
            "reviews",
            filters={"restaurant_id": f"eq.{restaurant_id}"},
            order="created_at.desc",
            limit=page_size,
            offset=offset
        ) or []

        items = []
        for r in reviews:
            # Fetch user info
            u_info = await self.db.select("users", filters={"id": f"eq.{r['user_id']}"}, single=True) or {}
            # Fetch dish ratings
            dish_ratings = await self.db.select("review_dish_ratings", filters={"review_id": f"eq.{r['id']}"}) or []
            items.append(
                ReviewResponse(
                    **r,
                    user_name=u_info.get("full_name", ""),
                    user_avatar=u_info.get("avatar_url"),
                    dish_ratings=[ReviewDishRatingResponse(**dr) for dr in dish_ratings]
                )
            )

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)

    async def get_user_reviews(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[ReviewResponse]:
        """
        List all reviews submitted by a specific user.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        all_revs = await self.db.select("reviews", columns="id", filters={"user_id": f"eq.{user_id}"})
        total = len(all_revs) if isinstance(all_revs, list) else 0

        reviews = await self.db.select(
            "reviews",
            filters={"user_id": f"eq.{user_id}"},
            order="created_at.desc",
            limit=page_size,
            offset=offset
        ) or []

        items = []
        for r in reviews:
            rest_info = await self.db.select("restaurants", columns="name", filters={"id": f"eq.{r['restaurant_id']}"}, single=True) or {}
            dish_ratings = await self.db.select("review_dish_ratings", filters={"review_id": f"eq.{r['id']}"}) or []
            items.append(
                ReviewResponse(
                    **r,
                    restaurant_name=rest_info.get("name", ""),
                    dish_ratings=[ReviewDishRatingResponse(**dr) for dr in dish_ratings]
                )
            )

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)

    async def delete_review(self, review_id: str, user_id: str) -> bool:
        """
        Delete a review, checking ownership.
        """
        review = await self.db.select("reviews", filters={"id": f"eq.{review_id}"}, single=True)
        if not review:
            raise NotFoundException("Review not found", error_code="REVIEW_NOT_FOUND")

        if review["user_id"] != user_id:
            raise ForbiddenException("You can only delete your own reviews", error_code="FORBIDDEN")

        # Delete associated dish ratings first
        await self.db.delete("review_dish_ratings", filters={"review_id": f"eq.{review_id}"})
        await self.db.delete("reviews", filters={"id": f"eq.{review_id}"})
        return True
