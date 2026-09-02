"""
Minimal async Supabase REST client for the ML service.

Read-only by design (select + rpc) — the ML service reasons over restaurant
and review data, it never writes back to the database. Deliberately not
importing the backend's SupabaseDB: these are two separate microservices
and shouldn't reach across each other's package boundary.
"""
from typing import Any, Dict, List, Optional, Union
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("ml_service.database")


class SupabaseReadClient:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
        self.rest_url = f"{self.base_url}/rest/v1"
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_connected(self) -> bool:
        return settings.has_database

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []
        client = await self._get_client()
        params: Dict[str, Any] = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit

        try:
            res = await client.get(f"{self.rest_url}/{table}", params=params, headers=self._headers())
            if not res.is_success:
                logger.warning(f"Supabase select {table} failed: {res.status_code} {res.text}")
                return []
            return res.json()
        except Exception as e:
            logger.warning(f"Supabase select {table} error: {e}")
            return []

    async def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Union[List[Dict[str, Any]], None]:
        if not self.is_connected:
            return None
        client = await self._get_client()
        try:
            res = await client.post(f"{self.rest_url}/rpc/{function_name}", json=params or {}, headers=self._headers())
            if not res.is_success:
                logger.warning(f"Supabase rpc {function_name} failed: {res.status_code} {res.text}")
                return None
            return res.json()
        except Exception as e:
            logger.warning(f"Supabase rpc {function_name} error: {e}")
            return None


db = SupabaseReadClient()
