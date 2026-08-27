from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.restaurants import RestaurantResponse
from app.schemas.menus import MenuItemResponse


class SearchFilters(BaseModel):
    query: Optional[str] = Field(default=None, description="Natural language search term or restaurant/food name")
    cuisine: Optional[str] = Field(default=None, description="Cuisine type filter (e.g. 'Pakistani', 'Fast Food')")
    city: Optional[str] = Field(default=None, description="City filter (e.g. 'Lahore')")
    max_budget: Optional[float] = Field(default=None, ge=0.0, description="Max budget per person (PKR)")
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Minimum average rating")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    radius_meters: Optional[int] = Field(default=10000, ge=500, le=100000)
    taste_vector: Optional[List[float]] = Field(default=None, description="Optional 9-dim target taste vector")


class SearchResponse(BaseModel):
    restaurants: List[RestaurantResponse] = Field(default_factory=list)
    menu_items: List[MenuItemResponse] = Field(default_factory=list)
    total_matches: int = 0
    query: Optional[str] = None
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
