from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_db, get_current_user
from app.core.database import SupabaseDB
from app.schemas.auth import SignUpRequest, LoginRequest, AuthTokenResponse, UserAuthInfo
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: SupabaseDB = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/signup",
    response_model=ApiResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def signup(
    request: SignUpRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account with Supabase Auth.
    Automatically creates public user record and default 9-dimensional taste profile.
    """
    token_response = await auth_service.sign_up(request)
    return ApiResponse(
        success=True,
        message="User account created successfully",
        data=token_response
    )


@router.post(
    "/login",
    response_model=ApiResponse[AuthTokenResponse],
    summary="Log in with email and password"
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and retrieve Supabase JWT access token.
    """
    token_response = await auth_service.login(request)
    return ApiResponse(
        success=True,
        message="Logged in successfully",
        data=token_response
    )


@router.post(
    "/logout",
    response_model=ApiResponse[bool],
    summary="Log out current user"
)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Invalidate current Supabase session.
    """
    token = current_user.get("token")
    if token:
        await auth_service.logout(token)
    return ApiResponse(
        success=True,
        message="Logged out successfully",
        data=True
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserAuthInfo],
    summary="Get currently authenticated user info"
)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns current user's authenticated identity and profile.
    """
    return ApiResponse(
        success=True,
        data=UserAuthInfo(
            id=current_user["id"],
            email=current_user.get("email", ""),
            full_name=current_user.get("full_name", ""),
            avatar_url=current_user.get("avatar_url"),
            role=current_user.get("role", "authenticated")
        )
    )
