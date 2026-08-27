from typing import Optional, Dict, Any
import jwt
import httpx
import logging
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger("foodbook.security")


class SecurityService:
    """
    Handles authentication and Supabase JWT verification.
    """

    @classmethod
    async def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify and extract user data from Supabase JWT.
        First attempts local JWT decode with secret if configured.
        Falls back to verifying token directly with Supabase Auth API.
        """
        if not token:
            raise UnauthorizedException("Authorization token is missing", error_code="TOKEN_MISSING")

        # Strip 'Bearer ' if present
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        # Method 1: Local JWT verification if secret is provided
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated"
                )
                return {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role", "authenticated"),
                    "app_metadata": payload.get("app_metadata", {}),
                    "user_metadata": payload.get("user_metadata", {}),
                    "token": token
                }
            except jwt.ExpiredSignatureError:
                raise UnauthorizedException("Token has expired", error_code="TOKEN_EXPIRED")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Local JWT verification failed: {e}. Falling back to Supabase Auth API.")

        # Method 2: Verify via Supabase Auth API (/auth/v1/user)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                    headers={
                        "apikey": settings.anon_key_or_service,
                        "Authorization": f"Bearer {token}"
                    }
                )
                if res.status_code == 200:
                    user_data = res.json()
                    return {
                        "id": user_data.get("id"),
                        "email": user_data.get("email"),
                        "role": user_data.get("role", "authenticated"),
                        "app_metadata": user_data.get("app_metadata", {}),
                        "user_metadata": user_data.get("user_metadata", {}),
                        "token": token
                    }
                else:
                    logger.warning(f"Supabase auth validation failed: {res.status_code} {res.text}")
                    raise UnauthorizedException("Invalid or expired session token", error_code="INVALID_TOKEN")
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Error communicating with Supabase auth: {e}")
            # In development fallback: attempt unverified decode if token has valid structure
            if settings.DEBUG:
                try:
                    payload = jwt.decode(token, options={"verify_signature": False})
                    return {
                        "id": payload.get("sub"),
                        "email": payload.get("email"),
                        "role": payload.get("role", "authenticated"),
                        "app_metadata": payload.get("app_metadata", {}),
                        "user_metadata": payload.get("user_metadata", {}),
                        "token": token
                    }
                except Exception:
                    pass
            raise UnauthorizedException("Could not validate authorization token", error_code="AUTH_FAILED")


security_service = SecurityService()
