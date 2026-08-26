from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.restaurants import RestaurantResponse


class CollectionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(default="", max_length=1000)
    cover_image_url: Optional[str] = None
    is_public: bool = True


class CollectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_public: Optional[bool] = None


class CollectionItemCreate(BaseModel):
    restaurant_id: str


class CollectionItemResponse(BaseModel):
    id: str
    collection_id: str
    restaurant_id: str
    created_at: Optional[datetime] = None
    restaurant: Optional[RestaurantResponse] = None


class CollectionResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = ""
    title: str
    description: Optional[str] = ""
    cover_image_url: Optional[str] = None
    is_public: bool = True
    saves_count: int = 0
    items_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CollectionDetailResponse(CollectionResponse):
    items: List[CollectionItemResponse] = Field(default_factory=list)
