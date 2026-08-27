from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ReviewDishRatingCreate(BaseModel):
    menu_item_id: str
    rating: float = Field(..., ge=1.0, le=5.0)


class ReviewDishRatingResponse(BaseModel):
    id: str
    review_id: str
    menu_item_id: str
    rating: float
    menu_item_name: Optional[str] = None
    created_at: Optional[datetime] = None


class ReviewCreate(BaseModel):
    restaurant_id: str
    branch_id: Optional[str] = None
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = Field(default="", max_length=2000)
    dish_ratings: Optional[List[ReviewDishRatingCreate]] = Field(default_factory=list)
    # Extracted aspects & taste vector can be provided directly or auto-extracted by AI/ML service
    extracted_aspects: Optional[Dict[str, Any]] = None
    extracted_taste_vector: Optional[List[float]] = None


class ReviewUpdate(BaseModel):
    overall_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_text: Optional[str] = Field(None, max_length=2000)
    dish_ratings: Optional[List[ReviewDishRatingCreate]] = None


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = ""
    user_avatar: Optional[str] = None
    restaurant_id: str
    restaurant_name: Optional[str] = ""
    branch_id: Optional[str] = None
    overall_rating: float
    review_text: Optional[str] = ""
    extracted_aspects: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extracted_taste_vector: Optional[List[float]] = None
    likes_count: int = 0
    dish_ratings: Optional[List[ReviewDishRatingResponse]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AspectExtractionPayload(BaseModel):
    review_text: str
    extracted_aspects: Dict[str, Any]
    extracted_taste_vector: List[float]
