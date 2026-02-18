import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application configuration settings.
    Values are read from environment variables, favoring .env file if present.
    """
    
    # Project Info
    PROJECT_NAME: str = "Headless Chat API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Database
    # Using asyncpg driver for PostgreSQL
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        # Load variables from .env file
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    """
    Creates and caches the settings object.
    Dependency injection should use this function.
    """
    return Settings()
