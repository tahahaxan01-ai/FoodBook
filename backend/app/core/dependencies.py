from fastapi import Depends, Header, HTTPException, status
from typing import Optional, Dict, Any
from app.core.security import security_service
from app.core.database import db, SupabaseDB
from app.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException


async def get_db() -> SupabaseDB:
    return db


async def get_token_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise UnauthorizedException("Invalid authorization scheme. Use 'Bearer <token>'", error_code="INVALID_AUTH_SCHEME")
    return token.strip()


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_header),
    database: SupabaseDB = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces authentication.
    Returns user payload dictionary with 'id', 'email', 'full_name', 'avatar_url', etc.
    """
    if not token:
        raise UnauthorizedException("Authentication token is required", error_code="UNAUTHORIZED")

    auth_payload = await security_service.verify_token(token)
    user_id = auth_payload["id"]

    # Fetch user details from public.users table
    try:
        user_record = await database.select("users", filters={"id": f"eq.{user_id}"}, single=True)
    except Exception:
        user_record = None

    if not user_record:
        # Fallback profile from auth metadata if not yet created in public.users
        user_meta = auth_payload.get("user_metadata", {})
        user_record = {
            "id": user_id,
            "email": auth_payload.get("email", ""),
            "full_name": user_meta.get("full_name") or user_meta.get("name") or "",
            "avatar_url": user_meta.get("avatar_url") or user_meta.get("picture") or None,
            "created_at": None
        }

    return {
        **user_record,
        "token": token,
        "role": auth_payload.get("role", "authenticated")
    }


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    database: SupabaseDB = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for endpoints that can be accessed anonymously or with auth.
    """
    if not authorization:
        return None
    try:
        token = await get_token_from_header(authorization)
        if not token:
            return None
        return await get_current_user(token=token, database=database)
    except Exception:
        return None
