from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional, Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.branches import (
    BranchResponse,
    BranchCreate,
    BranchUpdate,
    NearbyRestaurantQuery,
    NearbyRestaurantResponse
)
from app.schemas.common import ApiResponse
from app.services.branch_service import BranchService

router = APIRouter(tags=["Branches & Location"])


def get_branch_service(db: SupabaseDB = Depends(get_db)) -> BranchService:
    return BranchService(db)


@router.get(
    "/branches/nearby",
    response_model=ApiResponse[List[NearbyRestaurantResponse]],
    summary="Find restaurants near a geographical coordinate using PostGIS"
)
async def get_nearby_restaurants(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude (e.g. 31.4697)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude (e.g. 74.2728)"),
    radius_meters: Optional[int] = Query(10000, ge=500, le=100000, description="Radius in meters (default 10km)"),
    max_budget: Optional[float] = Query(None, description="Optional max budget filter"),
    service: BranchService = Depends(get_branch_service)
):
    """
    Geospatial discovery endpoint powered by PostgreSQL + PostGIS ST_DWithin and ST_Distance.
    Returns branches sorted by proximity along with exact distances in meters.
    """
    query = NearbyRestaurantQuery(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        max_budget=max_budget
    )
    results = await service.get_nearby_restaurants(query)
    return ApiResponse(
        success=True,
        message=f"Found {len(results)} restaurants within {radius_meters}m",
        data=results
    )


@router.get(
    "/restaurants/{restaurant_id}/branches",
    response_model=ApiResponse[List[BranchResponse]],
    summary="List all branches of a restaurant"
)
async def get_restaurant_branches(
    restaurant_id: str,
    service: BranchService = Depends(get_branch_service)
):
    branches = await service.get_restaurant_branches(restaurant_id)
    return ApiResponse(success=True, data=branches)


@router.get(
    "/branches/{branch_id}",
    response_model=ApiResponse[BranchResponse],
    summary="Get single branch details"
)
async def get_branch_by_id(
    branch_id: str,
    service: BranchService = Depends(get_branch_service)
):
    branch = await service.get_branch_by_id(branch_id)
    return ApiResponse(success=True, data=branch)


@router.post(
    "/restaurants/{restaurant_id}/branches",
    response_model=ApiResponse[BranchResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new branch with coordinates to a restaurant"
)
async def create_branch(
    restaurant_id: str,
    data: BranchCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(get_branch_service)
):
    created = await service.create_branch(restaurant_id, data)
    return ApiResponse(
        success=True,
        message="Branch created successfully",
        data=created
    )


@router.put(
    "/branches/{branch_id}",
    response_model=ApiResponse[BranchResponse],
    summary="Update branch information and coordinates"
)
async def update_branch(
    branch_id: str,
    data: BranchUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: BranchService = Depends(get_branch_service)
):
    updated = await service.update_branch(branch_id, data)
    return ApiResponse(
        success=True,
        message="Branch updated successfully",
        data=updated
    )
