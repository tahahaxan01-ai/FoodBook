from fastapi import APIRouter, Depends, Query, status
from typing import Optional, Dict, Any
from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.core.database import SupabaseDB
from app.schemas.restaurants import (
    RestaurantResponse,
    RestaurantDetailResponse,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantFilterParams
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


def get_restaurant_service(db: SupabaseDB = Depends(get_db)) -> RestaurantService:
    return RestaurantService(db)


@router.get(
    "/nearby",
    response_model=ApiResponse[list],
    summary="Find restaurants near a geographical coordinate using PostGIS"
)
async def get_nearby_restaurants(
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude (alias for latitude)"),
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude (alias for longitude)"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude"),
    radius_meters: Optional[int] = Query(10000, ge=500, le=100000, description="Radius in meters (default 10km)"),
    max_budget: Optional[float] = Query(None, description="Optional max budget filter"),
    db: SupabaseDB = Depends(get_db)
):
    from app.services.branch_service import BranchService
    from app.schemas.branches import NearbyRestaurantQuery
    
    target_lat = latitude if latitude is not None else lat
    target_lon = longitude if longitude is not None else lon
    
    if target_lat is None or target_lon is None:
        return ApiResponse(
            success=False,
            message="Latitude and longitude coordinates are required",
            data=[]
        )
    
    branch_service = BranchService(db)
    query = NearbyRestaurantQuery(
        latitude=target_lat,
        longitude=target_lon,
        radius_meters=radius_meters,
        max_budget=max_budget
    )
    results = await branch_service.get_nearby_restaurants(query)
    return ApiResponse(
        success=True,
        message=f"Found {len(results)} restaurants within {radius_meters}m",
        data=results
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[RestaurantResponse]],
    summary="List restaurants with filters and pagination"
)
async def list_restaurants(
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (e.g. 'Pakistani', 'Fast Food')"),
    max_budget: Optional[float] = Query(None, description="Maximum average price per person"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    city: Optional[str] = Query(None, description="City name"),
    search: Optional[str] = Query(None, description="Search by restaurant name"),
    is_active: Optional[bool] = Query(True, description="Filter active restaurants"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RestaurantService = Depends(get_restaurant_service)
):
    filters = RestaurantFilterParams(
        cuisine=cuisine,
        max_budget=max_budget,
        min_rating=min_rating,
        city=city,
        search=search,
        is_active=is_active
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated_data = await service.list_restaurants(filters=filters, pagination=pagination)
    return ApiResponse(success=True, data=paginated_data)


@router.get(
    "/slug/{slug}",
    response_model=ApiResponse[RestaurantDetailResponse],
    summary="Get restaurant details by slug"
)
async def get_restaurant_by_slug(
    slug: str,
    optional_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    service: RestaurantService = Depends(get_restaurant_service)
):
    user_id = optional_user["id"] if optional_user else None
    detail = await service.get_restaurant_by_slug(slug, current_user_id=user_id)
    return ApiResponse(success=True, data=detail)


@router.get(
    "/{restaurant_id}",
    response_model=ApiResponse[RestaurantDetailResponse],
    summary="Get restaurant details by UUID"
)
async def get_restaurant_by_id(
    restaurant_id: str,
    optional_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    service: RestaurantService = Depends(get_restaurant_service)
):
    user_id = optional_user["id"] if optional_user else None
    detail = await service.get_restaurant_by_id(restaurant_id, current_user_id=user_id)
    return ApiResponse(success=True, data=detail)


@router.post(
    "",
    response_model=ApiResponse[RestaurantResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new restaurant"
)
async def create_restaurant(
    data: RestaurantCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: RestaurantService = Depends(get_restaurant_service)
):
    created = await service.create_restaurant(data)
    return ApiResponse(
        success=True,
        message="Restaurant created successfully",
        data=created
    )


@router.put(
    "/{restaurant_id}",
    response_model=ApiResponse[RestaurantResponse],
    summary="Update restaurant profile"
)
async def update_restaurant(
    restaurant_id: str,
    data: RestaurantUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: RestaurantService = Depends(get_restaurant_service)
):
    updated = await service.update_restaurant(restaurant_id, data)
    return ApiResponse(
        success=True,
        message="Restaurant updated successfully",
        data=updated
    )
