from typing import Dict, Any, Optional
import httpx
import logging
from app.core.config import settings
from app.core.database import SupabaseDB
from app.core.exceptions import UnauthorizedException, BadRequestException, ConflictException, DatabaseException
from app.schemas.auth import SignUpRequest, LoginRequest, AuthTokenResponse, UserAuthInfo

logger = logging.getLogger("foodbook.auth_service")


class AuthService:
    def __init__(self, db: SupabaseDB):
        self.db = db
        self.auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
        self.anon_key = settings.anon_key_or_service

    async def sign_up(self, request: SignUpRequest) -> AuthTokenResponse:
        """
        Register a new user in Supabase Auth and ensure user profile & taste profile exist.
        Uses Supabase Admin User API if service role key is configured to auto-confirm email.
        """
        payload = {
            "email": request.email,
            "password": request.password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": request.full_name,
                "avatar_url": request.avatar_url
            }
        }
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }

        user_id = None
        user_info = {}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Try admin endpoint first (auto-confirms email)
                res = await client.post(f"{self.auth_url}/admin/users", json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    user_info = res.json()
                    user_id = user_info.get("id")
                else:
                    # Fallback to standard signup endpoint
                    std_payload = {
                        "email": request.email,
                        "password": request.password,
                        "data": {
                            "full_name": request.full_name,
                            "avatar_url": request.avatar_url
                        }
                    }
                    res = await client.post(
                        f"{self.auth_url}/signup",
                        json=std_payload,
                        headers={"apikey": self.anon_key, "Content-Type": "application/json"}
                    )
                    if res.status_code >= 400:
                        error_data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                        msg = error_data.get("msg") or error_data.get("message") or error_data.get("error_description") or res.text
                        if res.status_code == 422 or "already registered" in msg.lower():
                            raise ConflictException("A user with this email already exists", error_code="USER_ALREADY_EXISTS")
                        raise BadRequestException(f"Signup failed: {msg}", error_code="SIGNUP_FAILED")
                    user_data = res.json()
                    user_info = user_data.get("user") or user_data
                    user_id = user_info.get("id")
            except (ConflictException, BadRequestException):
                raise
            except Exception as e:
                logger.exception(f"Failed to reach Supabase Auth for signup: {e}")
                raise DatabaseException(f"Authentication service unavailable: {str(e)}")

        # Ensure record in public.users
        try:
            await self.db.insert(
                "users",
                {
                    "id": user_id,
                    "email": request.email,
                    "full_name": request.full_name or "",
                    "avatar_url": request.avatar_url
                },
                upsert=True
            )
        except Exception as e:
            logger.warning(f"Could not upsert public.users during signup: {e}")

        # Ensure record in public.user_taste_profiles
        try:
            default_taste_vector = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            await self.db.insert(
                "user_taste_profiles",
                {
                    "user_id": user_id,
                    "taste_vector": default_taste_vector,
                    "preferred_cuisines": [],
                    "dietary_restrictions": [],
                    "preferred_dining_styles": []
                },
                upsert=True
            )
        except Exception as e:
            logger.warning(f"Could not upsert default user_taste_profiles during signup: {e}")

        # Retrieve active session tokens via login
        try:
            return await self.login(LoginRequest(email=request.email, password=request.password))
        except Exception:
            return AuthTokenResponse(
                access_token="",
                token_type="bearer",
                expires_in=3600,
                refresh_token=None,
                user=UserAuthInfo(
                    id=user_id,
                    email=request.email,
                    full_name=request.full_name,
                    avatar_url=request.avatar_url,
                    role=user_info.get("role", "authenticated")
                )
            )

    async def login(self, request: LoginRequest) -> AuthTokenResponse:
        """
        Authenticate user with email and password via Supabase Auth.
        """
        payload = {
            "email": request.email,
            "password": request.password
        }
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(
                    f"{self.auth_url}/token?grant_type=password",
                    json=payload,
                    headers=headers
                )
            except Exception as e:
                logger.exception(f"Failed to reach Supabase Auth for login: {e}")
                raise DatabaseException(f"Authentication service unavailable: {str(e)}")

        if res.status_code >= 400:
            error_data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            msg = error_data.get("error_description") or error_data.get("message") or error_data.get("msg") or "Invalid email or password"
            raise UnauthorizedException("Invalid email or password", error_code="INVALID_CREDENTIALS", details=msg)

        auth_data = res.json()
        user_info = auth_data.get("user", {})
        user_id = user_info.get("id")

        # Fetch profile from public.users
        user_record = await self.db.select("users", filters={"id": f"eq.{user_id}"}, single=True)

        full_name = ""
        avatar_url = None
        if user_record:
            full_name = user_record.get("full_name", "")
            avatar_url = user_record.get("avatar_url")
        else:
            meta = user_info.get("user_metadata", {})
            full_name = meta.get("full_name") or meta.get("name") or ""
            avatar_url = meta.get("avatar_url")

        return AuthTokenResponse(
            access_token=auth_data.get("access_token"),
            token_type="bearer",
            expires_in=auth_data.get("expires_in", 3600),
            refresh_token=auth_data.get("refresh_token"),
            user=UserAuthInfo(
                id=user_id,
                email=user_info.get("email", request.email),
                full_name=full_name,
                avatar_url=avatar_url,
                role=user_info.get("role", "authenticated")
            )
        )

    async def logout(self, token: str) -> bool:
        """
        Invalidate user session on Supabase Auth.
        """
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {token}"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(f"{self.auth_url}/logout", headers=headers)
            except Exception as e:
                logger.warning(f"Supabase logout call returned error: {e}")
        return True
