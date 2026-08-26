from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, List
from app.core.dependencies import get_db, get_optional_user, get_current_user
from app.core.database import SupabaseDB
from app.schemas.recommendations import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem
)
from app.schemas.common import ApiResponse
from app.services.recommendation_service import RecommendationService
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/recommendations", tags=["Recommendations & AI"])


def get_rec_service(db: SupabaseDB = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)


def get_rest_service(db: SupabaseDB = Depends(get_db)) -> RestaurantService:
    return RestaurantService(db)


@router.get(
    "",
    response_model=ApiResponse[RecommendationResponse],
    summary="Get personalized taste-matched recommendations for current user"
)
async def get_recommendations(
    latitude: Optional[float] = Query(None, description="User latitude for distance matching"),
    longitude: Optional[float] = Query(None, description="User longitude for distance matching"),
    max_budget: Optional[float] = Query(None, description="Optional maximum budget per person"),
    radius_meters: Optional[int] = Query(15000, description="Proximity radius in meters"),
    limit: Optional[int] = Query(10, ge=1, le=50),
    optional_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    service: RecommendationService = Depends(get_rec_service)
):
    """
    Returns explainable recommendations based on the user's 9-dimensional taste vector,
    cuisine preferences, and geographical proximity.
    """
    user_id = optional_user["id"] if optional_user else None
    request = RecommendationRequest(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        max_budget=max_budget,
        radius_meters=radius_meters,
        limit=limit
    )
    result = await service.get_recommendations(request)
    return ApiResponse(
        success=True,
        message=f"Generated {result.total_recommendations} personalized recommendations",
        data=result
    )


@router.post(
    "",
    response_model=ApiResponse[RecommendationResponse],
    summary="Generate recommendations with explicit taste vector and preference overrides"
)
async def post_custom_recommendations(
    request: RecommendationRequest,
    optional_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    service: RecommendationService = Depends(get_rec_service)
):
    """
    Generate recommendations with explicit parameters.
    Can be used by frontend explore tools or conversational AI bots.
    """
    if optional_user and not request.user_id:
        request.user_id = optional_user["id"]

    result = await service.get_recommendations(request)
    return ApiResponse(success=True, data=result)


@router.get(
    "/similar/{restaurant_id}",
    response_model=ApiResponse[RecommendationResponse],
    summary="Find restaurants with a similar taste profile (e.g. 'More like Cheezious')"
)
async def get_similar_restaurants(
    restaurant_id: str,
    limit: Optional[int] = Query(6, ge=1, le=20),
    rest_service: RestaurantService = Depends(get_rest_service),
    rec_service: RecommendationService = Depends(get_rec_service)
):
    """
    Given a restaurant (e.g. Cheezious), finds other restaurants that share a similar
    taste vector and culinary profile.
    """
    target = await rest_service.get_restaurant_by_id(restaurant_id)
    target_vector = target.aggregated_taste_vector or target.base_taste_vector or [0.5]*9

    request = RecommendationRequest(
        taste_vector=target_vector,
        preferred_cuisines=target.cuisines,
        limit=limit + 1  # Fetch one extra to exclude target itself
    )
    result = await rec_service.get_recommendations(request)

    # Exclude the target restaurant itself
    filtered_recs = [r for r in result.recommendations if r.restaurant.id != restaurant_id][:limit]
    result.recommendations = filtered_recs
    result.total_recommendations = len(filtered_recs)

    return ApiResponse(
        success=True,
        message=f"Found {len(filtered_recs)} restaurants with similar taste to {target.name}",
        data=result
    )
