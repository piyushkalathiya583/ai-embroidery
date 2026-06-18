from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Embroidery Sketch Composer"
    debug: bool = True
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 10080
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./embroidery.db"

    # Storage backend: "fs" (local files) or "db" (bytes in Postgres — serverless).
    storage_backend: str = "fs"
    storage_root: str = "./storage"
    upload_dir: str = "./storage/uploads"
    thumbnail_dir: str = "./storage/thumbnails"
    max_upload_mb: int = 15

    # Providers: "openai" | "gemini" (vision/review), "openai" | "pollinations" (image)
    vision_provider: str = "openai"
    image_provider: str = "openai"

    openai_api_key: str = ""
    vision_model: str = "gpt-4o"
    image_model: str = "gpt-image-1"

    # Free dev providers
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"  # higher free-tier limits
    pollinations_model: str = "flux"  # high quality (~20-40s/img); "turbo" for speed

    # Module 12 review can be disabled to cut latency on short timeouts.
    review_enabled: bool = True

    # Admin endpoint guard (set ADMIN_TOKEN in env to enable /api/admin/*).
    admin_token: str = ""

    @field_validator(
        "storage_backend", "image_provider", "vision_provider", mode="after"
    )
    @classmethod
    def _normalize(cls, v: str) -> str:
        # Env vars set via CLI piping can carry stray whitespace/newlines.
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator(
        "openai_api_key",
        "gemini_api_key",
        "secret_key",
        "database_url",
        "admin_token",
        mode="after",
    )
    @classmethod
    def _strip(cls, v: str) -> str:
        # Keys/secrets are case-sensitive: strip whitespace only, never lowercase.
        return v.strip() if isinstance(v, str) else v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
