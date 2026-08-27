from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.menus import (
    MenuCategoryResponse,
    MenuCategoryWithItems,
    MenuItemResponse,
    MenuItemCreate,
    MenuItemUpdate,
    CategoryCreate,
    CategoryUpdate,
    RestaurantMenuResponse
)

logger = logging.getLogger("foodbook.menu_service")


class MenuService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def get_restaurant_menu(self, restaurant_id: str) -> RestaurantMenuResponse:
        """
        Get full hierarchical menu (categories + items) for a restaurant.
        """
        # Fetch categories
        categories = await self.db.select(
            "menu_categories",
            filters={"restaurant_id": f"eq.{restaurant_id}"},
            order="display_order.asc,name.asc"
        ) or []

        # Fetch menu items
        items = await self.db.select(
            "menu_items",
            filters={"restaurant_id": f"eq.{restaurant_id}"},
            order="name.asc"
        ) or []

        # Group items by category_id
        items_by_cat: Dict[str, List[MenuItemResponse]] = {}
        for it in items:
            cat_id = it.get("category_id")
            if cat_id not in items_by_cat:
                items_by_cat[cat_id] = []
            items_by_cat[cat_id].append(MenuItemResponse(**it))

        category_items: List[MenuCategoryWithItems] = []
        for cat in categories:
            cat_id = cat["id"]
            cat_items = items_by_cat.get(cat_id, [])
            category_items.append(
                MenuCategoryWithItems(
                    **cat,
                    items=cat_items
                )
            )

        return RestaurantMenuResponse(
            restaurant_id=restaurant_id,
            categories=category_items
        )

    async def get_item_by_id(self, item_id: str) -> MenuItemResponse:
        record = await self.db.select("menu_items", filters={"id": f"eq.{item_id}"}, single=True)
        if not record:
            raise NotFoundException(f"Menu item with ID {item_id} not found", error_code="ITEM_NOT_FOUND")
        return MenuItemResponse(**record)

    async def create_category(self, restaurant_id: str, data: CategoryCreate) -> MenuCategoryResponse:
        insert_data = {
            "restaurant_id": restaurant_id,
            "name": data.name,
            "display_order": data.display_order or 1
        }
        created = await self.db.insert("menu_categories", insert_data)
        return MenuCategoryResponse(**created[0])

    async def update_category(self, category_id: str, data: CategoryUpdate) -> MenuCategoryResponse:
        update_data: Dict[str, Any] = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.display_order is not None:
            update_data["display_order"] = data.display_order

        updated = await self.db.update("menu_categories", data=update_data, filters={"id": f"eq.{category_id}"})
        if not updated:
            raise NotFoundException("Category not found", error_code="CATEGORY_NOT_FOUND")
        return MenuCategoryResponse(**updated[0])

    async def create_menu_item(self, restaurant_id: str, data: MenuItemCreate) -> MenuItemResponse:
        # Verify category belongs to restaurant
        category = await self.db.select(
            "menu_categories",
            filters={"id": f"eq.{data.category_id}", "restaurant_id": f"eq.{restaurant_id}"},
            single=True
        )
        if not category:
            raise BadRequestException("Invalid category_id for this restaurant", error_code="INVALID_CATEGORY")

        insert_data = {
            "restaurant_id": restaurant_id,
            "category_id": data.category_id,
            "name": data.name,
            "description": data.description,
            "price": data.price,
            "image_url": data.image_url,
            "item_taste_vector": data.item_taste_vector or [0.5]*9,
            "is_available": data.is_available
        }

        created = await self.db.insert("menu_items", insert_data)
        return MenuItemResponse(**created[0])

    async def update_menu_item(self, item_id: str, data: MenuItemUpdate) -> MenuItemResponse:
        await self.get_item_by_id(item_id)

        update_data: Dict[str, Any] = {}
        if data.category_id is not None:
            update_data["category_id"] = data.category_id
        if data.name is not None:
            update_data["name"] = data.name
        if data.description is not None:
            update_data["description"] = data.description
        if data.price is not None:
            update_data["price"] = data.price
        if data.image_url is not None:
            update_data["image_url"] = data.image_url
        if data.item_taste_vector is not None:
            update_data["item_taste_vector"] = data.item_taste_vector
        if data.is_available is not None:
            update_data["is_available"] = data.is_available

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        updated = await self.db.update("menu_items", data=update_data, filters={"id": f"eq.{item_id}"})
        return MenuItemResponse(**updated[0])

    async def toggle_availability(self, item_id: str, is_available: bool) -> MenuItemResponse:
        return await self.update_menu_item(item_id, MenuItemUpdate(is_available=is_available))

    async def delete_menu_item(self, item_id: str) -> bool:
        await self.db.delete("menu_items", filters={"id": f"eq.{item_id}"})
        return True
