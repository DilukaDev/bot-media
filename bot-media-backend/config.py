from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    database_url: str = Field(..., description="PostgreSQL connection string")
    admin_api_key: str = Field(..., description="Admin API key")
    post_cooldown_seconds: int = Field(default=5, description="Post rate-limit cooldown in seconds")

    allowed_origins: list[str] = Field(
        default=["http://localhost:5173"],
        description="List of allowed CORS origins",
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        """Parse comma-separated origins string into a list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
