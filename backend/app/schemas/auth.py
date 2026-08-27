from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    full_name: Optional[str] = Field(default="", description="User full name")
    avatar_url: Optional[str] = Field(default=None, description="Optional avatar URL")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserAuthInfo(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = ""
    avatar_url: Optional[str] = None
    role: Optional[str] = "authenticated"


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = 3600
    refresh_token: Optional[str] = None
    user: UserAuthInfo
