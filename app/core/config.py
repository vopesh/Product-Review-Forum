from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str = "Photo and Video Sharing API"
    VERSION: str = "1.0.0"

    # Database Configuration
    DATABASE_URL: str

    # Auth Configuration
    AUTH_SECRET_KEY: str = "change-this-development-secret-key"
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ImageKit Configuration
    IMAGEKIT_PUBLIC_KEY: str
    IMAGEKIT_PRIVATE_KEY: str
    IMAGEKIT_URL_ENDPOINT: str

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
