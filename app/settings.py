from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # База даних
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    # JWT
    SECRET_KEY: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24
    # CORS
    CORS_ALLOW_ORIGINS: str = "*"
    # Cloudinary — поддерживаем URL и поотдельности
    CLOUDINARY_URL: Optional[str] = None
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    # Redis
    REDIS_URL: Optional[str] = None
    CACHE_USER_TTL_SEC: int = 300
    # Tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Default avatar (глобальний)
    DEFAULT_AVATAR_URL: Optional[str] = None
    # Rate limit
    RATE_LIMIT_ME_CALLS: int = 5
    RATE_LIMIT_ME_WINDOW_SEC: int = 60
    # SMTP (опціонально)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # ВАЖНО: игнорируем неизвестные ключи в .env,
    # чтобы не падать, если там есть что-то ещё.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()