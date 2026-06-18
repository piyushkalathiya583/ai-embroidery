from functools import lru_cache

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

    openai_api_key: str = ""
    vision_model: str = "gpt-4o"
    image_model: str = "gpt-image-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
