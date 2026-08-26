from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.users import UserProfileResponse, UserProfileUpdate, UserPublicProfile
from app.schemas.taste_profiles import TasteProfileResponse, TasteProfileUpdate, TasteVectorUpdate
from app.schemas.common import ApiResponse
from app.services.user_service import UserService
from app.services.taste_profile_service import TasteProfileService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: SupabaseDB = Depends(get_db)) -> UserService:
    return UserService(db)


def get_taste_service(db: SupabaseDB = Depends(get_db)) -> TasteProfileService:
    return TasteProfileService(db)


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Get current user's profile"
)
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    profile = await user_service.get_user_by_id(current_user["id"])
    return ApiResponse(success=True, data=profile)


@router.put(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Update current user's profile (name, avatar)"
)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    updated = await user_service.update_profile(current_user["id"], update_data)
    return ApiResponse(
        success=True,
        message="Profile updated successfully",
        data=updated
    )


@router.get(
    "/me/taste-profile",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Get current authenticated user's 9-dim taste profile & preferences"
)
async def get_my_taste_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    taste_service: TasteProfileService = Depends(get_taste_service)
):
    profile = await taste_service.get_or_create_taste_profile(current_user["id"])
    return ApiResponse(success=True, data=profile)


@router.put(
    "/me/taste-profile",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Update current user's taste profile, budget preferences, and dietary restrictions"
)
async def update_my_taste_profile(
    update_data: TasteProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    taste_service: TasteProfileService = Depends(get_taste_service)
):
    updated = await taste_service.update_taste_profile(current_user["id"], update_data)
    return ApiResponse(
        success=True,
        message="Taste profile updated successfully",
        data=updated
    )


@router.patch(
    "/me/taste-profile/vector",
    response_model=ApiResponse[TasteProfileResponse],
    summary="Update specifically the 9-dimensional taste vector"
)
async def update_my_taste_vector(
    vector_data: TasteVectorUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    taste_service: TasteProfileService = Depends(get_taste_service)
):
    updated = await taste_service.update_taste_vector(current_user["id"], vector_data)
    return ApiResponse(
        success=True,
        message="Taste vector updated successfully",
        data=updated
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserPublicProfile],
    summary="Get public profile of any user"
)
async def get_public_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    profile = await user_service.get_public_profile(user_id)
    return ApiResponse(success=True, data=profile)
