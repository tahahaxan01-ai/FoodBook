from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class RestaurantResponse(BaseModel):
    id: str
    name: str
    slug: str
    cuisines: List[str] = Field(default_factory=list)
    avg_price_per_person: Optional[float] = 0.0
    base_taste_vector: Optional[List[float]] = None
    aggregated_taste_vector: Optional[List[float]] = None
    review_count: int = 0
    avg_rating: float = 0.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RestaurantDetailResponse(RestaurantResponse):
    branches: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    menu_categories: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    recent_reviews: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    is_saved: Optional[bool] = False


class RestaurantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: Optional[str] = None
    cuisines: List[str] = Field(default_factory=list)
    avg_price_per_person: Optional[float] = Field(default=1000.0, ge=0.0)
    base_taste_vector: Optional[List[float]] = Field(default_factory=lambda: [0.5]*9)
    is_active: bool = True


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    cuisines: Optional[List[str]] = None
    avg_price_per_person: Optional[float] = None
    base_taste_vector: Optional[List[float]] = None
    is_active: Optional[bool] = None


class RestaurantFilterParams(BaseModel):
    cuisine: Optional[str] = None
    max_budget: Optional[float] = None
    min_rating: Optional[float] = None
    city: Optional[str] = None
    search: Optional[str] = None
    is_active: Optional[bool] = True
