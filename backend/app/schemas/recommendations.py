from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.restaurants import RestaurantResponse


class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    taste_vector: Optional[List[float]] = None
    preferred_cuisines: Optional[List[str]] = Field(default_factory=list)
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    max_budget: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = 15000
    limit: Optional[int] = 10


class RecommendationItem(BaseModel):
    restaurant: RestaurantResponse
    match_score: float = Field(..., ge=0.0, le=1.0, description="Normalized match score (0.0 - 1.0)")
    match_percentage: int = Field(..., description="Integer match percentage (e.g. 92 for 92%)")
    reasons: List[str] = Field(default_factory=list, description="Human-readable explanation reasons")
    distance_meters: Optional[float] = None


class RecommendationResponse(BaseModel):
    user_id: Optional[str] = None
    total_recommendations: int
    recommendations: List[RecommendationItem]
    model_version: str = "foodbook-taste-v1"
