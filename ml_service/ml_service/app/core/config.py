"""
ML Service Settings.

Reuses the same Supabase project as the backend by reading backend/.env
(one project, one set of credentials — no separate secrets to manage).
Falls back to a local ml_service/.env or process env vars if that file
isn't present, so the service can still be pointed at a different
Supabase project when needed.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "../../../../"))
_BACKEND_ENV = os.path.join(_REPO_ROOT, "backend", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_ENV, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    @property
    def has_database(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)


settings = Settings()
