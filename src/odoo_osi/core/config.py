from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="ODOO_OSI_", env_file=".env", extra="ignore")

    env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://odoo_osi:odoo_osi@localhost:55432/odoo_osi"
    redis_url: str = "redis://localhost:6379/0"
    github_token: str | None = Field(default=None)
    github_owner: str = "OCA"
    oca_apps_module_estimate: int | None = Field(
        default=20000,
        description="Rough external catalog estimate used only for coverage gap reporting.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
