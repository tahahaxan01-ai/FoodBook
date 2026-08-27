from typing import List, Optional, Dict, Any
import logging
from app.core.database import SupabaseDB
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.branches import (
    BranchResponse,
    BranchCreate,
    BranchUpdate,
    NearbyRestaurantQuery,
    NearbyRestaurantResponse
)

logger = logging.getLogger("foodbook.branch_service")


class BranchService:
    def __init__(self, db: SupabaseDB):
        self.db = db

    async def get_restaurant_branches(self, restaurant_id: str) -> List[BranchResponse]:
        """
        List all branches for a given restaurant.
        """
        records = await self.db.select("restaurant_branches", filters={"restaurant_id": f"eq.{restaurant_id}"})
        return [BranchResponse(**r) for r in (records or [])]

    async def get_branch_by_id(self, branch_id: str) -> BranchResponse:
        """
        Get branch details by ID.
        """
        record = await self.db.select("restaurant_branches", filters={"id": f"eq.{branch_id}"}, single=True)
        if not record:
            raise NotFoundException(f"Branch with ID {branch_id} not found", error_code="BRANCH_NOT_FOUND")
        return BranchResponse(**record)

    async def get_nearby_restaurants(self, query: NearbyRestaurantQuery) -> List[NearbyRestaurantResponse]:
        """
        Execute the PostGIS RPC function 'get_nearby_restaurants' to perform geospatial radius query.
        """
        rpc_params: Dict[str, Any] = {
            "user_lat": query.latitude,
            "user_lon": query.longitude,
            "radius_meters": query.radius_meters or 10000
        }
        if query.max_budget is not None and query.max_budget > 0:
            rpc_params["max_budget"] = query.max_budget

        try:
            results = await self.db.rpc("get_nearby_restaurants", params=rpc_params)
        except Exception as e:
            logger.exception(f"Error calling get_nearby_restaurants RPC: {e}")
            # Fallback if RPC fails or parameters differ
            results = []

        output = []
        for r in (results or []):
            output.append(NearbyRestaurantResponse(
                restaurant_id=r.get("restaurant_id"),
                restaurant_name=r.get("restaurant_name"),
                slug=r.get("slug"),
                branch_id=r.get("branch_id"),
                branch_name=r.get("branch_name"),
                address=r.get("address"),
                city=r.get("city"),
                phone_number=r.get("phone_number"),
                avg_price_per_person=r.get("avg_price_per_person"),
                avg_rating=r.get("avg_rating") or 0.0,
                review_count=r.get("review_count") or 0,
                distance_meters=round(r.get("distance_meters", 0.0), 2),
                latitude=r.get("latitude"),
                longitude=r.get("longitude")
            ))

        return output

    async def create_branch(self, restaurant_id: str, data: BranchCreate) -> BranchResponse:
        """
        Create a new branch for a restaurant with PostGIS coordinates.
        """
        # Formulate WKT geometry point for PostGIS (POINT(lng lat))
        point_wkt = f"POINT({data.longitude} {data.latitude})"

        insert_data = {
            "restaurant_id": restaurant_id,
            "branch_name": data.branch_name,
            "address": data.address,
            "city": data.city,
            "location": point_wkt,
            "phone_number": data.phone_number,
            "opening_time": data.opening_time,
            "closing_time": data.closing_time
        }

        created = await self.db.insert("restaurant_branches", insert_data)
        record = created[0]
        return BranchResponse(
            id=record["id"],
            restaurant_id=record["restaurant_id"],
            branch_name=record["branch_name"],
            address=record["address"],
            city=record["city"],
            phone_number=record.get("phone_number"),
            opening_time=record.get("opening_time"),
            closing_time=record.get("closing_time"),
            latitude=data.latitude,
            longitude=data.longitude,
            created_at=record.get("created_at")
        )

    async def update_branch(self, branch_id: str, data: BranchUpdate) -> BranchResponse:
        """
        Update branch details.
        """
        # Ensure exists
        existing = await self.get_branch_by_id(branch_id)

        update_data: Dict[str, Any] = {}
        if data.branch_name is not None:
            update_data["branch_name"] = data.branch_name
        if data.address is not None:
            update_data["address"] = data.address
        if data.city is not None:
            update_data["city"] = data.city
        if data.phone_number is not None:
            update_data["phone_number"] = data.phone_number
        if data.opening_time is not None:
            update_data["opening_time"] = data.opening_time
        if data.closing_time is not None:
            update_data["closing_time"] = data.closing_time

        if data.latitude is not None and data.longitude is not None:
            update_data["location"] = f"POINT({data.longitude} {data.latitude})"

        updated = await self.db.update("restaurant_branches", data=update_data, filters={"id": f"eq.{branch_id}"})
        record = updated[0]
        return BranchResponse(
            id=record["id"],
            restaurant_id=record["restaurant_id"],
            branch_name=record["branch_name"],
            address=record["address"],
            city=record["city"],
            phone_number=record.get("phone_number"),
            opening_time=record.get("opening_time"),
            closing_time=record.get("closing_time"),
            latitude=data.latitude or existing.latitude,
            longitude=data.longitude or existing.longitude,
            created_at=record.get("created_at")
        )
