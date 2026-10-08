from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal

from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str = "Photo and Video Sharing API"
    VERSION: str = "1.0.0"

    # Database Configuration
    DATABASE_URL: str

    # Auth Configuration
    AUTH_SECRET_KEY: str = Field(min_length=32, repr=False)
    AUTH_ALGORITHM: Literal["HS256"] = "HS256"
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

    @field_validator("AUTH_SECRET_KEY")
    @classmethod
    def validate_auth_secret(cls, value: str) -> str:
        if value.startswith(("change-this-", "replace-with-", "your_")):
            raise ValueError("Set AUTH_SECRET_KEY to a generated secret")
        return value

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )


settings = Settings()
