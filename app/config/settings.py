from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "متجر مؤسسة سر التميز والأناقة"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # Security
    SECRET_KEY: str = os.environ.get("SESSION_SECRET", "changeme-super-secret-key-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Database
    DATABASE_URL: str = "sqlite:///./tamayoz.db"

    # Beezati
    BEEZATI_API_KEY: str = os.environ.get("BEEZATI_API_KEY", "")
    BEEZATI_SECRET: str = os.environ.get("BEEZATI_SECRET", "")
    BEEZATI_BASE_URL: str = "https://api.beezati.com/v1"
    BEEZATI_WEBHOOK_SECRET: str = os.environ.get("BEEZATI_WEBHOOK_SECRET", "")

    # Company
    COMPANY_NAME: str = "مؤسسة سر التميز والأناقة"
    COMPANY_LOGO: str = "/static/logo.png"
    CURRENCY_DEFAULT: str = "SAR"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
