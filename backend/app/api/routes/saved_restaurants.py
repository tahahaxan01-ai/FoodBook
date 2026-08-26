from fastapi import APIRouter, Depends, Query, status
from typing import Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.saved_restaurants import SavedRestaurantResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.services.saved_restaurant_service import SavedRestaurantService

router = APIRouter(tags=["Saved Restaurants"])


def get_saved_service(db: SupabaseDB = Depends(get_db)) -> SavedRestaurantService:
    return SavedRestaurantService(db)


@router.post(
    "/restaurants/{restaurant_id}/save",
    response_model=ApiResponse[SavedRestaurantResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Save / bookmark a restaurant"
)
async def save_restaurant(
    restaurant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SavedRestaurantService = Depends(get_saved_service)
):
    saved = await service.save_restaurant(current_user["id"], restaurant_id)
    return ApiResponse(
        success=True,
        message="Restaurant saved to your favorites",
        data=saved
    )


@router.delete(
    "/restaurants/{restaurant_id}/save",
    response_model=ApiResponse[bool],
    summary="Remove a restaurant from saved list"
)
async def unsave_restaurant(
    restaurant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SavedRestaurantService = Depends(get_saved_service)
):
    await service.unsave_restaurant(current_user["id"], restaurant_id)
    return ApiResponse(
        success=True,
        message="Restaurant removed from saved favorites",
        data=True
    )


@router.get(
    "/users/me/saved-restaurants",
    response_model=ApiResponse[PaginatedResponse[SavedRestaurantResponse]],
    summary="Get list of current user's saved restaurants"
)
async def get_my_saved_restaurants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SavedRestaurantService = Depends(get_saved_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_saved_restaurants(current_user["id"], pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/saved-restaurants",
    response_model=ApiResponse[PaginatedResponse[SavedRestaurantResponse]],
    summary="Alias for /api/users/me/saved-restaurants"
)
async def get_saved_restaurants_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SavedRestaurantService = Depends(get_saved_service)
):
    return await get_my_saved_restaurants(page=page, page_size=page_size, current_user=current_user, service=service)
