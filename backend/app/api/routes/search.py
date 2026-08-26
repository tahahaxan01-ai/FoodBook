from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.core.dependencies import get_db
from app.core.database import SupabaseDB
from app.schemas.search import SearchFilters, SearchResponse
from app.schemas.common import ApiResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


def get_search_service(db: SupabaseDB = Depends(get_db)) -> SearchService:
    return SearchService(db)


@router.get(
    "",
    response_model=ApiResponse[SearchResponse],
    summary="Multi-faceted natural search across restaurants and menu items"
)
async def search_get(
    q: Optional[str] = Query(None, description="Search query string"),
    cuisine: Optional[str] = Query(None, description="Cuisine filter"),
    city: Optional[str] = Query(None, description="City filter"),
    max_budget: Optional[float] = Query(None, description="Maximum budget (PKR)"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    latitude: Optional[float] = Query(None, description="User latitude"),
    longitude: Optional[float] = Query(None, description="User longitude"),
    radius_meters: Optional[int] = Query(15000, description="Distance radius"),
    service: SearchService = Depends(get_search_service)
):
    filters = SearchFilters(
        query=q,
        cuisine=cuisine,
        city=city,
        max_budget=max_budget,
        min_rating=min_rating,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters
    )
    result = await service.search(filters)
    return ApiResponse(success=True, data=result)


@router.post(
    "",
    response_model=ApiResponse[SearchResponse],
    summary="Structured/conversational search with detailed filters"
)
async def search_post(
    filters: SearchFilters,
    service: SearchService = Depends(get_search_service)
):
    """
    Search endpoint designed for structured filters extracted by AI conversational interfaces.
    """
    result = await service.search(filters)
    return ApiResponse(success=True, data=result)
