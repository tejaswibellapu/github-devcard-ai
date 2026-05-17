from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GITHUB_TOKEN: str
    GEMINI_API_KEY: str
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Static directory for cards
    STATIC_DIR: str = "app/static"
    CARDS_DIR: str = "app/static/cards"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
