from fastapi import APIRouter, Depends, Query, status
from typing import Dict, Any
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.reviews import ReviewCreate, ReviewResponse
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.services.review_service import ReviewService

router = APIRouter(tags=["Reviews & Ratings"])


def get_review_service(db: SupabaseDB = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.post(
    "/reviews",
    response_model=ApiResponse[ReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit user review, dish ratings, and pass raw review text for ML aspect extraction"
)
async def submit_review(
    data: ReviewCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    """
    Submits a review for a restaurant.
    Accepts restaurant_id, overall_rating, review_text, dish_ratings, etc.
    Automatically coordinates with AI/ML aspect extraction to populate `extracted_aspects`
    and `extracted_taste_vector` if not supplied.
    """
    if not data.restaurant_id:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("restaurant_id is required to submit a review")
    created = await service.create_review(current_user["id"], data)
    return ApiResponse(
        success=True,
        message="Review submitted successfully",
        data=created
    )


@router.get(
    "/reviews/restaurant/{restaurant_id}",
    response_model=ApiResponse[PaginatedResponse[ReviewResponse]],
    summary="Get paginated reviews for a specific restaurant"
)
async def get_reviews_by_restaurant_id(
    restaurant_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ReviewService = Depends(get_review_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_restaurant_reviews(restaurant_id, pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/reviews/me",
    response_model=ApiResponse[PaginatedResponse[ReviewResponse]],
    summary="Get all reviews submitted by the current authenticated user"
)
async def get_my_reviews_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_user_reviews(current_user["id"], pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.post(
    "/restaurants/{restaurant_id}/reviews",
    response_model=ApiResponse[ReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a review with aspect-based ratings and dish ratings"
)
async def create_restaurant_review(
    restaurant_id: str,
    data: ReviewCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    """
    Submits a review for a restaurant.
    Automatically coordinates with AI/ML aspect extraction to populate `extracted_aspects`
    and `extracted_taste_vector` if not supplied.
    """
    data.restaurant_id = restaurant_id
    created = await service.create_review(current_user["id"], data)
    return ApiResponse(
        success=True,
        message="Review submitted successfully",
        data=created
    )


@router.get(
    "/restaurants/{restaurant_id}/reviews",
    response_model=ApiResponse[PaginatedResponse[ReviewResponse]],
    summary="Get all reviews for a restaurant"
)
async def get_restaurant_reviews(
    restaurant_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ReviewService = Depends(get_review_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_restaurant_reviews(restaurant_id, pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/users/me/reviews",
    response_model=ApiResponse[PaginatedResponse[ReviewResponse]],
    summary="Get all reviews submitted by the current authenticated user"
)
async def get_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    pagination = PaginationParams(page=page, page_size=page_size)
    paginated = await service.get_user_reviews(current_user["id"], pagination=pagination)
    return ApiResponse(success=True, data=paginated)


@router.delete(
    "/reviews/{review_id}",
    response_model=ApiResponse[bool],
    summary="Delete a review (author only)"
)
async def delete_review(
    review_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    await service.delete_review(review_id, current_user["id"])
    return ApiResponse(
        success=True,
        message="Review deleted successfully",
        data=True
    )
