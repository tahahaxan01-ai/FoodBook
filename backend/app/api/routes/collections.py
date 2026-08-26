from fastapi import APIRouter, Depends, Query, status
from typing import Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.collections import (
    CollectionResponse,
    CollectionDetailResponse,
    CollectionCreate,
    CollectionUpdate,
    CollectionItemCreate
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.services.collection_service import CollectionService

router = APIRouter(tags=["Collections"])


def get_collection_service(db: SupabaseDB = Depends(get_db)) -> CollectionService:
    return CollectionService(db)


@router.post(
    "/collections",
    response_model=ApiResponse[CollectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new community food collection"
)
async def create_collection(
    data: CollectionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    created = await service.create_collection(current_user["id"], data)
    return ApiResponse(
        success=True,
        message="Collection created successfully",
        data=created
    )


@router.get(
    "/collections",
    response_model=ApiResponse[PaginatedResponse[CollectionResponse]],
    summary="List public community food collections"
)
async def get_public_collections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CollectionService = Depends(get_collection_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_public_collections(pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/users/me/collections",
    response_model=ApiResponse[PaginatedResponse[CollectionResponse]],
    summary="Get collections created by the current user"
)
async def get_my_collections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_user_collections(current_user["id"], pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/collections/{collection_id}",
    response_model=ApiResponse[CollectionDetailResponse],
    summary="Get collection detail with all restaurant items"
)
async def get_collection_detail(
    collection_id: str,
    service: CollectionService = Depends(get_collection_service)
):
    detail = await service.get_collection_by_id(collection_id)
    return ApiResponse(success=True, data=detail)


@router.put(
    "/collections/{collection_id}",
    response_model=ApiResponse[CollectionResponse],
    summary="Update collection details (author only)"
)
async def update_collection(
    collection_id: str,
    data: CollectionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    updated = await service.update_collection(collection_id, current_user["id"], data)
    return ApiResponse(
        success=True,
        message="Collection updated successfully",
        data=updated
    )


@router.delete(
    "/collections/{collection_id}",
    response_model=ApiResponse[bool],
    summary="Delete a collection (author only)"
)
async def delete_collection(
    collection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    await service.delete_collection(collection_id, current_user["id"])
    return ApiResponse(
        success=True,
        message="Collection deleted successfully",
        data=True
    )


@router.post(
    "/collections/{collection_id}/items",
    response_model=ApiResponse[CollectionDetailResponse],
    summary="Add a restaurant to collection"
)
async def add_item_to_collection(
    collection_id: str,
    data: CollectionItemCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    updated_detail = await service.add_item_to_collection(collection_id, current_user["id"], data.restaurant_id)
    return ApiResponse(
        success=True,
        message="Restaurant added to collection",
        data=updated_detail
    )


@router.delete(
    "/collections/{collection_id}/items/{restaurant_id}",
    response_model=ApiResponse[CollectionDetailResponse],
    summary="Remove a restaurant from collection"
)
async def remove_item_from_collection(
    collection_id: str,
    restaurant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service)
):
    updated_detail = await service.remove_item_from_collection(collection_id, current_user["id"], restaurant_id)
    return ApiResponse(
        success=True,
        message="Restaurant removed from collection",
        data=updated_detail
    )
