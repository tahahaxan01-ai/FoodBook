from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.schemas.restaurants import RestaurantResponse


class SaveRestaurantRequest(BaseModel):
    restaurant_id: str


class SavedRestaurantResponse(BaseModel):
    user_id: str
    restaurant_id: str
    created_at: Optional[datetime] = None
    restaurant: Optional[RestaurantResponse] = None
