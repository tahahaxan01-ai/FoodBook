from typing import Any, Dict, List, Optional, Union
import httpx
import json
import logging
from app.core.config import settings
from app.core.exceptions import DatabaseException, NotFoundException, ConflictException, UnauthorizedException

logger = logging.getLogger("foodbook.database")


class SupabaseDB:
    """
    Async Supabase Database and RPC Client.
    Connects to Supabase REST and Auth endpoints with service role / bearer authentication.
    """

    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.rest_url = f"{self.base_url}/rest/v1"
        self.auth_url = f"{self.base_url}/auth/v1"
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self._client: Optional[httpx.AsyncClient] = None
        self._loop = None

    async def get_client(self) -> httpx.AsyncClient:
        import asyncio
        current_loop = asyncio.get_running_loop()
        if self._client is None or self._client.is_closed or self._loop != current_loop:
            if self._client and not self._client.is_closed:
                try:
                    await self._client.aclose()
                except Exception:
                    pass
            self._loop = current_loop
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _get_headers(self, user_token: Optional[str] = None, prefer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {user_token if user_token else self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _handle_error_response(self, response: httpx.Response, context: str = "operation"):
        if response.is_success:
            return
        
        status_code = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("message") or error_data.get("error_description") or error_data.get("msg") or str(error_data)
            code = error_data.get("code") or f"SUPABASE_ERROR_{status_code}"
            details = error_data.get("details") or error_data.get("hint")
        except Exception:
            message = response.text or f"Database error ({status_code})"
            code = f"SUPABASE_ERROR_{status_code}"
            details = None

        logger.error(f"Supabase error during {context}: {status_code} - {message} (code: {code})")

        if status_code == 404:
            raise NotFoundException(message=f"Resource not found: {message}", error_code="NOT_FOUND", details=details)
        elif status_code == 409:
            raise ConflictException(message=f"Conflict: {message}", error_code="CONFLICT", details=details)
        elif status_code == 401:
            raise UnauthorizedException(message=f"Unauthorized: {message}", error_code="UNAUTHORIZED", details=details)
        else:
            raise DatabaseException(message=f"Database error: {message}", error_code=code, details=details)

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        single: bool = False,
        user_token: Optional[str] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Execute a SELECT query on a Supabase table.
        """
        client = await self.get_client()
        params: Dict[str, Any] = {"select": columns}

        if filters:
            for k, v in filters.items():
                params[k] = v

        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        headers = self._get_headers(user_token=user_token)
        url = f"{self.rest_url}/{table}"

        try:
            response = await client.get(url, params=params, headers=headers)
            self._handle_error_response(response, context=f"select from {table}")
            data = response.json()
            if single:
                return data[0] if len(data) > 0 else None
            return data
        except (NotFoundException, ConflictException, UnauthorizedException, DatabaseException):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error querying {table}: {e}")
            raise DatabaseException(message=f"Failed to query {table}: {str(e)}")

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        upsert: bool = False,
        user_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Insert one or more records into a table.
        """
        client = await self.get_client()
        prefer = "return=representation"
        if upsert:
            prefer += ",resolution=merge-duplicates"

        headers = self._get_headers(user_token=user_token, prefer=prefer)
        url = f"{self.rest_url}/{table}"

        try:
            response = await client.post(url, json=data, headers=headers)
            self._handle_error_response(response, context=f"insert into {table}")
            return response.json()
        except (NotFoundException, ConflictException, UnauthorizedException, DatabaseException):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error inserting into {table}: {e}")
            raise DatabaseException(message=f"Failed to insert into {table}: {str(e)}")

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        user_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Update records in a table matching filters.
        """
        client = await self.get_client()
        headers = self._get_headers(user_token=user_token, prefer="return=representation")
        url = f"{self.rest_url}/{table}"

        try:
            response = await client.patch(url, json=data, params=filters, headers=headers)
            self._handle_error_response(response, context=f"update {table}")
            return response.json()
        except (NotFoundException, ConflictException, UnauthorizedException, DatabaseException):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating {table}: {e}")
            raise DatabaseException(message=f"Failed to update {table}: {str(e)}")

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        user_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Delete records in a table matching filters.
        """
        client = await self.get_client()
        headers = self._get_headers(user_token=user_token, prefer="return=representation")
        url = f"{self.rest_url}/{table}"

        try:
            response = await client.delete(url, params=filters, headers=headers)
            self._handle_error_response(response, context=f"delete from {table}")
            return response.json()
        except (NotFoundException, ConflictException, UnauthorizedException, DatabaseException):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting from {table}: {e}")
            raise DatabaseException(message=f"Failed to delete from {table}: {str(e)}")

    async def rpc(
        self,
        function_name: str,
        params: Optional[Dict[str, Any]] = None,
        user_token: Optional[str] = None
    ) -> Any:
        """
        Execute a Supabase RPC / Stored Function (e.g. get_nearby_restaurants).
        """
        client = await self.get_client()
        headers = self._get_headers(user_token=user_token)
        url = f"{self.rest_url}/rpc/{function_name}"

        try:
            response = await client.post(url, json=params or {}, headers=headers)
            self._handle_error_response(response, context=f"rpc {function_name}")
            return response.json()
        except (NotFoundException, ConflictException, UnauthorizedException, DatabaseException):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error calling rpc {function_name}: {e}")
            raise DatabaseException(message=f"Failed to call RPC {function_name}: {str(e)}")


db = SupabaseDB()
