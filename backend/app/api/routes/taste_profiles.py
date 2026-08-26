from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.taste_profiles import (
    TasteProfileResponse,
    TasteProfileUpdate,
    TasteVectorUpdate
)
from app.schemas.common import ApiResponse
from app.services.taste_profile_service import TasteProfileService

router = APIRouter(prefix="/taste-profile", tags=["Taste Profiles"])


def get_taste_service(db: SupabaseDB = Depends(get_db)) -> TasteProfileService:
    return TasteProfileService(db)


@router.get(
    "/me",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Get current user's taste profile & vector"
)
async def get_my_taste_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TasteProfileService = Depends(get_taste_service)
):
    profile = await service.get_or_create_taste_profile(current_user["id"])
    return ApiResponse(success=True, data=profile)


@router.put(
    "/me",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Update current user's taste profile preferences"
)
async def update_my_taste_profile(
    update_data: TasteProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TasteProfileService = Depends(get_taste_service)
):
    updated = await service.update_taste_profile(current_user["id"], update_data)
    return ApiResponse(
        success=True,
        message="Taste profile updated successfully",
        data=updated
    )


@router.patch(
    "/me/vector",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Update specifically the 9-dimensional taste vector"
)
async def update_my_taste_vector(
    vector_data: TasteVectorUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TasteProfileService = Depends(get_taste_service)
):
    updated = await service.update_taste_vector(current_user["id"], vector_data)
    return ApiResponse(
        success=True,
        message="Taste vector updated successfully",
        data=updated
    )
