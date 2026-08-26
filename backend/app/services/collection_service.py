from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.schemas.collections import (
    CollectionResponse,
    CollectionDetailResponse,
    CollectionCreate,
    CollectionUpdate,
    CollectionItemResponse
)
from app.schemas.restaurants import RestaurantResponse
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger("foodbook.collection_service")


class CollectionService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def create_collection(self, user_id: str, data: CollectionCreate) -> CollectionResponse:
        """
        Create a new food collection.
        """
        insert_data = {
            "user_id": user_id,
            "title": data.title,
            "description": data.description or "",
            "cover_image_url": data.cover_image_url,
            "is_public": data.is_public,
            "saves_count": 0
        }
        created = await self.db.insert("collections", insert_data)
        record = created[0]

        # Fetch user name
        u_info = await self.db.select("users", columns="full_name", filters={"id": f"eq.{user_id}"}, single=True) or {}

        return CollectionResponse(
            **record,
            user_name=u_info.get("full_name", ""),
            items_count=0
        )

    async def get_public_collections(
        self,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[CollectionResponse]:
        """
        List public community food collections.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        all_cols = await self.db.select("collections", columns="id", filters={"is_public": "eq.true"})
        total = len(all_cols) if isinstance(all_cols, list) else 0

        collections = await self.db.select(
            "collections",
            filters={"is_public": "eq.true"},
            order="saves_count.desc,created_at.desc",
            limit=page_size,
            offset=offset
        ) or []

        items = []
        for c in collections:
            u_info = await self.db.select("users", columns="full_name", filters={"id": f"eq.{c['user_id']}"}, single=True) or {}
            c_items = await self.db.select("collection_items", columns="id", filters={"collection_id": f"eq.{c['id']}"}) or []
            items.append(
                CollectionResponse(
                    **c,
                    user_name=u_info.get("full_name", ""),
                    items_count=len(c_items)
                )
            )

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)

    async def get_user_collections(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[CollectionResponse]:
        """
        List collections created by a specific user.
        """
        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        offset = (page - 1) * page_size

        all_cols = await self.db.select("collections", columns="id", filters={"user_id": f"eq.{user_id}"})
        total = len(all_cols) if isinstance(all_cols, list) else 0

        collections = await self.db.select(
            "collections",
            filters={"user_id": f"eq.{user_id}"},
            order="created_at.desc",
            limit=page_size,
            offset=offset
        ) or []

        items = []
        for c in collections:
            u_info = await self.db.select("users", columns="full_name", filters={"id": f"eq.{user_id}"}, single=True) or {}
            c_items = await self.db.select("collection_items", columns="id", filters={"collection_id": f"eq.{c['id']}"}) or []
            items.append(
                CollectionResponse(
                    **c,
                    user_name=u_info.get("full_name", ""),
                    items_count=len(c_items)
                )
            )

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)

    async def get_collection_by_id(self, collection_id: str) -> CollectionDetailResponse:
        """
        Get full collection details including all restaurant items.
        """
        record = await self.db.select("collections", filters={"id": f"eq.{collection_id}"}, single=True)
        if not record:
            raise NotFoundException("Collection not found", error_code="COLLECTION_NOT_FOUND")

        u_info = await self.db.select("users", columns="full_name", filters={"id": f"eq.{record['user_id']}"}, single=True) or {}

        # Fetch collection items
        raw_items = await self.db.select(
            "collection_items",
            filters={"collection_id": f"eq.{collection_id}"},
            order="created_at.asc"
        ) or []

        items: List[CollectionItemResponse] = []
        for it in raw_items:
            rest_data = await self.db.select("restaurants", filters={"id": f"eq.{it['restaurant_id']}"}, single=True)
            items.append(CollectionItemResponse(
                id=it["id"],
                collection_id=it["collection_id"],
                restaurant_id=it["restaurant_id"],
                created_at=it.get("created_at"),
                restaurant=RestaurantResponse(**rest_data) if rest_data else None
            ))

        return CollectionDetailResponse(
            **record,
            user_name=u_info.get("full_name", ""),
            items_count=len(items),
            items=items
        )

    async def update_collection(self, collection_id: str, user_id: str, data: CollectionUpdate) -> CollectionResponse:
        """
        Update collection metadata (ownership enforced).
        """
        col = await self.db.select("collections", filters={"id": f"eq.{collection_id}"}, single=True)
        if not col:
            raise NotFoundException("Collection not found", error_code="COLLECTION_NOT_FOUND")
        if col["user_id"] != user_id:
            raise ForbiddenException("You can only edit your own collections", error_code="FORBIDDEN")

        update_data: Dict[str, Any] = {}
        if data.title is not None:
            update_data["title"] = data.title
        if data.description is not None:
            update_data["description"] = data.description
        if data.cover_image_url is not None:
            update_data["cover_image_url"] = data.cover_image_url
        if data.is_public is not None:
            update_data["is_public"] = data.is_public

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        updated = await self.db.update("collections", data=update_data, filters={"id": f"eq.{collection_id}"})
        return CollectionResponse(**updated[0])

    async def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """
        Delete collection and its items (ownership enforced).
        """
        col = await self.db.select("collections", filters={"id": f"eq.{collection_id}"}, single=True)
        if not col:
            raise NotFoundException("Collection not found", error_code="COLLECTION_NOT_FOUND")
        if col["user_id"] != user_id:
            raise ForbiddenException("You can only delete your own collections", error_code="FORBIDDEN")

        await self.db.delete("collection_items", filters={"collection_id": f"eq.{collection_id}"})
        await self.db.delete("collections", filters={"id": f"eq.{collection_id}"})
        return True

    async def add_item_to_collection(self, collection_id: str, user_id: str, restaurant_id: str) -> CollectionDetailResponse:
        """
        Add a restaurant to an existing collection (ownership enforced).
        """
        col = await self.db.select("collections", filters={"id": f"eq.{collection_id}"}, single=True)
        if not col:
            raise NotFoundException("Collection not found", error_code="COLLECTION_NOT_FOUND")
        if col["user_id"] != user_id:
            raise ForbiddenException("You can only modify your own collections", error_code="FORBIDDEN")

        # Verify restaurant exists
        rest = await self.db.select("restaurants", filters={"id": f"eq.{restaurant_id}"}, single=True)
        if not rest:
            raise NotFoundException("Restaurant not found", error_code="RESTAURANT_NOT_FOUND")

        # Check if already added
        existing = await self.db.select(
            "collection_items",
            filters={"collection_id": f"eq.{collection_id}", "restaurant_id": f"eq.{restaurant_id}"},
            single=True
        )
        if not existing:
            await self.db.insert("collection_items", {
                "collection_id": collection_id,
                "restaurant_id": restaurant_id
            })

        return await self.get_collection_by_id(collection_id)

    async def remove_item_from_collection(self, collection_id: str, user_id: str, restaurant_id: str) -> CollectionDetailResponse:
        """
        Remove a restaurant from a collection (ownership enforced).
        """
        col = await self.db.select("collections", filters={"id": f"eq.{collection_id}"}, single=True)
        if not col:
            raise NotFoundException("Collection not found", error_code="COLLECTION_NOT_FOUND")
        if col["user_id"] != user_id:
            raise ForbiddenException("You can only modify your own collections", error_code="FORBIDDEN")

        await self.db.delete(
            "collection_items",
            filters={"collection_id": f"eq.{collection_id}", "restaurant_id": f"eq.{restaurant_id}"}
        )
        return await self.get_collection_by_id(collection_id)
