from typing import Optional, Dict, Any
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.users import UserProfileResponse, UserProfileUpdate, UserPublicProfile

logger = logging.getLogger("foodbook.user_service")


class UserService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def get_user_by_id(self, user_id: str) -> UserProfileResponse:
        record = await self.db.select("users", filters={"id": f"eq.{user_id}"}, single=True)
        if not record:
            raise NotFoundException(f"User with ID {user_id} not found", error_code="USER_NOT_FOUND")
        return UserProfileResponse(**record)

    async def get_public_profile(self, user_id: str) -> UserPublicProfile:
        record = await self.db.select("users", columns="id,full_name,avatar_url", filters={"id": f"eq.{user_id}"}, single=True)
        if not record:
            raise NotFoundException(f"User with ID {user_id} not found", error_code="USER_NOT_FOUND")
        return UserPublicProfile(**record)

    async def update_profile(self, user_id: str, update_data: UserProfileUpdate) -> UserProfileResponse:
        data_to_update: Dict[str, Any] = {}
        if update_data.full_name is not None:
            data_to_update["full_name"] = update_data.full_name
        if update_data.avatar_url is not None:
            data_to_update["avatar_url"] = update_data.avatar_url

        if not data_to_update:
            return await self.get_user_by_id(user_id)

        updated_records = await self.db.update(
            "users",
            data=data_to_update,
            filters={"id": f"eq.{user_id}"}
        )
        if not updated_records:
            # If user didn't exist in public.users, upsert it
            upsert_data = {
                "id": user_id,
                "full_name": update_data.full_name or "",
                "avatar_url": update_data.avatar_url
            }
            res = await self.db.insert("users", upsert_data, upsert=True)
            return UserProfileResponse(**res[0])

        return UserProfileResponse(**updated_records[0])
