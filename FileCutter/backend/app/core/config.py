from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    lm_studio_url: str = "http://localhost:1234/v1/chat/completions"
    downloads_path: str = str(Path.home() / "Downloads")
    # Retained for backward compatibility with the cache module's import surface.
    # The cache module owns its own absolute-path resolution; leaving this as
    # None here signals "no override from settings."
    cache_db_path: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
