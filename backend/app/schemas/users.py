from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = ""
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPublicProfile(BaseModel):
    id: str
    full_name: Optional[str] = ""
    avatar_url: Optional[str] = None
