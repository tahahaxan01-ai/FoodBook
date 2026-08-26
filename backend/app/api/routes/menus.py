from fastapi import APIRouter, Depends, Query, status
from typing import Dict, Any, List
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.menus import (
    RestaurantMenuResponse,
    MenuCategoryResponse,
    MenuItemResponse,
    MenuItemCreate,
    MenuItemUpdate,
    CategoryCreate,
    CategoryUpdate
)
from app.schemas.common import ApiResponse
from app.services.menu_service import MenuService

router = APIRouter(tags=["Menus & Items"])


def get_menu_service(db: SupabaseDB = Depends(get_db)) -> MenuService:
    return MenuService(db)


@router.get(
    "/restaurants/{restaurant_id}/menu",
    response_model=ApiResponse[RestaurantMenuResponse],
    summary="Get full restaurant menu structured by categories"
)
async def get_restaurant_menu(
    restaurant_id: str,
    service: MenuService = Depends(get_menu_service)
):
    menu = await service.get_restaurant_menu(restaurant_id)
    return ApiResponse(success=True, data=menu)


@router.get(
    "/menu-items/{item_id}",
    response_model=ApiResponse[MenuItemResponse],
    summary="Get details of a specific menu item"
)
async def get_menu_item(
    item_id: str,
    service: MenuService = Depends(get_menu_service)
):
    item = await service.get_item_by_id(item_id)
    return ApiResponse(success=True, data=item)


@router.post(
    "/restaurants/{restaurant_id}/menu/categories",
    response_model=ApiResponse[MenuCategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new menu category for a restaurant"
)
async def create_category(
    restaurant_id: str,
    data: CategoryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    created = await service.create_category(restaurant_id, data)
    return ApiResponse(
        success=True,
        message="Menu category created successfully",
        data=created
    )


@router.put(
    "/menu-categories/{category_id}",
    response_model=ApiResponse[MenuCategoryResponse],
    summary="Update category name or display order"
)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    updated = await service.update_category(category_id, data)
    return ApiResponse(
        success=True,
        message="Category updated successfully",
        data=updated
    )


@router.post(
    "/restaurants/{restaurant_id}/menu/items",
    response_model=ApiResponse[MenuItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new dish/item to restaurant menu"
)
async def create_menu_item(
    restaurant_id: str,
    data: MenuItemCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    created = await service.create_menu_item(restaurant_id, data)
    return ApiResponse(
        success=True,
        message="Menu item created successfully",
        data=created
    )


@router.put(
    "/menu-items/{item_id}",
    response_model=ApiResponse[MenuItemResponse],
    summary="Update menu item information (price, taste vector, image)"
)
async def update_menu_item(
    item_id: str,
    data: MenuItemUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    updated = await service.update_menu_item(item_id, data)
    return ApiResponse(
        success=True,
        message="Menu item updated successfully",
        data=updated
    )


@router.patch(
    "/menu-items/{item_id}/availability",
    response_model=ApiResponse[MenuItemResponse],
    summary="Toggle availability of a menu item"
)
async def toggle_item_availability(
    item_id: str,
    is_available: bool = Query(..., description="Availability status"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    updated = await service.toggle_availability(item_id, is_available)
    return ApiResponse(
        success=True,
        message=f"Item marked as {'available' if is_available else 'unavailable'}",
        data=updated
    )


@router.delete(
    "/menu-items/{item_id}",
    response_model=ApiResponse[bool],
    summary="Delete a menu item"
)
async def delete_menu_item(
    item_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service)
):
    await service.delete_menu_item(item_id)
    return ApiResponse(
        success=True,
        message="Menu item deleted successfully",
        data=True
    )
