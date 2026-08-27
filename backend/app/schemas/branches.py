from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class BranchResponse(BaseModel):
    id: str
    restaurant_id: str
    branch_name: str
    address: str
    city: str
    phone_number: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None


class BranchCreate(BaseModel):
    branch_name: str = Field(..., min_length=2)
    address: str = Field(..., min_length=5)
    city: str = Field(default="Lahore")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    phone_number: Optional[str] = None
    opening_time: Optional[str] = "11:00:00"
    closing_time: Optional[str] = "00:00:00"


class BranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone_number: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None


class NearbyRestaurantQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="User current latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="User current longitude")
    radius_meters: Optional[int] = Field(default=10000, ge=500, le=100000, description="Search radius in meters")
    max_budget: Optional[float] = Field(default=None, ge=0.0, description="Maximum budget per person")


class NearbyRestaurantResponse(BaseModel):
    restaurant_id: str
    restaurant_name: str
    slug: str
    branch_id: str
    branch_name: str
    address: str
    city: str
    phone_number: Optional[str] = None
    avg_price_per_person: Optional[float] = None
    avg_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    distance_meters: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
