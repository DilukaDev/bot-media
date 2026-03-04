from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    database_url: str = Field(..., description="PostgreSQL connection string")
    admin_api_key: str = Field(..., description="Admin API key")
    post_cooldown_seconds: int = Field(..., description="Post rate-limit cooldown in seconds")
    allowed_origin: str = Field(..., description="CORS allowed origin")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
