from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = 1


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    display_order: Optional[int] = None


class MenuCategoryResponse(BaseModel):
    id: str
    restaurant_id: str
    name: str
    display_order: int = 1
    created_at: Optional[datetime] = None


class MenuItemResponse(BaseModel):
    id: str
    restaurant_id: str
    category_id: str
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    item_taste_vector: Optional[List[float]] = None
    is_available: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MenuItemCreate(BaseModel):
    category_id: str
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    image_url: Optional[str] = None
    item_taste_vector: Optional[List[float]] = Field(default_factory=lambda: [0.5]*9)
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    item_taste_vector: Optional[List[float]] = None
    is_available: Optional[bool] = None


class MenuCategoryWithItems(MenuCategoryResponse):
    items: List[MenuItemResponse] = Field(default_factory=list)


class RestaurantMenuResponse(BaseModel):
    restaurant_id: str
    categories: List[MenuCategoryWithItems] = Field(default_factory=list)
