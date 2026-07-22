"""
Centralized application settings, loaded from environment variables / .env file.
Never hardcode secrets — everything sensitive comes through here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://trading:change_me@localhost:5432/trading_signals"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET_KEY: str = "insecure-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Notifications
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alerts@yourdomain.com"
    WEBPUSH_PUBLIC_KEY: str = ""
    WEBPUSH_PRIVATE_KEY: str = ""

    # Market data
    MARKET_DATA_PROVIDER: str = "twelvedata"
    MARKET_DATA_API_KEY: str = ""

    # Billing (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_BASIC: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file is only parsed once per process."""
    return Settings()


settings = get_settings()
