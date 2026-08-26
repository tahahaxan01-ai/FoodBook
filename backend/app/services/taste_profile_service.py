from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.taste_profiles import (
    TasteProfileResponse,
    TasteProfileUpdate,
    TasteVector,
    TasteVectorUpdate
)

logger = logging.getLogger("foodbook.taste_profile_service")

DEFAULT_TASTE_VECTOR = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]


BUDGET_MAP = {
    "low": 1,
    "budget": 1,
    "inexpensive": 1,
    "moderate": 2,
    "medium": 2,
    "high": 3,
    "expensive": 3,
    "fine_dining": 4,
    "luxury": 4
}


def normalize_budget(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        if val.isdigit():
            return int(val)
        return BUDGET_MAP.get(val.lower().strip(), 2)
    return 2


class TasteProfileService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def get_or_create_taste_profile(self, user_id: str) -> TasteProfileResponse:
        """
        Get user taste profile. If it doesn't exist yet, creates and returns a default one.
        """
        record = await self.db.select("user_taste_profiles", filters={"user_id": f"eq.{user_id}"}, single=True)
        if not record:
            # Create default taste profile
            default_data = {
                "user_id": user_id,
                "taste_vector": DEFAULT_TASTE_VECTOR,
                "preferred_cuisines": [],
                "dietary_restrictions": [],
                "budget_level": 2,
                "preferred_dining_styles": []
            }
            try:
                res = await self.db.insert("user_taste_profiles", default_data, upsert=True)
                record = res[0] if res else default_data
            except Exception as e:
                logger.warning(f"Error creating default taste profile for {user_id}: {e}")
                record = default_data

        t_vec = record.get("taste_vector") or DEFAULT_TASTE_VECTOR
        taste_attr = TasteVector.from_list(t_vec)

        return TasteProfileResponse(
            user_id=user_id,
            taste_vector=t_vec,
            taste_attributes=taste_attr,
            preferred_cuisines=record.get("preferred_cuisines") or [],
            dietary_restrictions=record.get("dietary_restrictions") or [],
            budget_level=record.get("budget_level"),
            preferred_dining_styles=record.get("preferred_dining_styles") or [],
            updated_at=record.get("updated_at")
        )

    async def update_taste_profile(self, user_id: str, update_data: TasteProfileUpdate) -> TasteProfileResponse:
        """
        Update taste profile preferences (taste vector, cuisines, dietary restrictions, budget, dining style).
        """
        data_to_update: Dict[str, Any] = {}

        if update_data.taste_attributes is not None:
            data_to_update["taste_vector"] = update_data.taste_attributes.to_list()
        elif update_data.taste_vector is not None:
            data_to_update["taste_vector"] = update_data.taste_vector

        if update_data.preferred_cuisines is not None:
            data_to_update["preferred_cuisines"] = update_data.preferred_cuisines

        if update_data.dietary_restrictions is not None:
            data_to_update["dietary_restrictions"] = update_data.dietary_restrictions

        if update_data.budget_level is not None:
            data_to_update["budget_level"] = normalize_budget(update_data.budget_level)

        if update_data.preferred_dining_styles is not None:
            data_to_update["preferred_dining_styles"] = update_data.preferred_dining_styles

        data_to_update["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Update or upsert
        updated = await self.db.update(
            "user_taste_profiles",
            data=data_to_update,
            filters={"user_id": f"eq.{user_id}"}
        )

        if not updated:
            # If not existed, upsert with defaults
            full_data = {
                "user_id": user_id,
                "taste_vector": data_to_update.get("taste_vector", DEFAULT_TASTE_VECTOR),
                "preferred_cuisines": data_to_update.get("preferred_cuisines", []),
                "dietary_restrictions": data_to_update.get("dietary_restrictions", []),
                "budget_level": data_to_update.get("budget_level", "moderate"),
                "preferred_dining_styles": data_to_update.get("preferred_dining_styles", []),
                "updated_at": data_to_update["updated_at"]
            }
            res = await self.db.insert("user_taste_profiles", full_data, upsert=True)
            record = res[0]
        else:
            record = updated[0]

        t_vec = record.get("taste_vector") or DEFAULT_TASTE_VECTOR
        taste_attr = TasteVector.from_list(t_vec)

        return TasteProfileResponse(
            user_id=user_id,
            taste_vector=t_vec,
            taste_attributes=taste_attr,
            preferred_cuisines=record.get("preferred_cuisines") or [],
            dietary_restrictions=record.get("dietary_restrictions") or [],
            budget_level=record.get("budget_level"),
            preferred_dining_styles=record.get("preferred_dining_styles") or [],
            updated_at=record.get("updated_at")
        )

    async def update_taste_vector(self, user_id: str, vector_update: TasteVectorUpdate) -> TasteProfileResponse:
        """
        Convenience method to specifically update just the 9-dim taste vector.
        """
        vector = None
        if vector_update.taste_attributes is not None:
            vector = vector_update.taste_attributes.to_list()
        elif vector_update.taste_vector is not None:
            vector = vector_update.taste_vector
        else:
            raise BadRequestException("Either taste_vector or taste_attributes must be provided")

        update_dto = TasteProfileUpdate(taste_vector=vector)
        return await self.update_taste_profile(user_id, update_dto)
