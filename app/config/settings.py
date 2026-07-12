from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "متجر مؤسسة سر التميز والأناقة"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # ─── Security ────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="T@m@yoz-S3cr3t-K3y-2024-XyZ!@#$%^",
        alias="SESSION_SECRET",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://gamalalmaqtary:xLETQQcyz4g5YQrH1DNJMolBy353PtIv@dpg-d99t3t77f7vs73bapu20-a.oregon-postgres.render.com/secret_of_excellence_and_elegance"

    # ─── Beezati Payment Gateway ─────────────────────────────────────────────
    BEEZATI_API_KEY: str = ""
    BEEZATI_SECRET: str = ""
    BEEZATI_BASE_URL: str = "https://api.beezati.com/v1"
    BEEZATI_WEBHOOK_SECRET: str = ""

    # ─── Admin Seed ──────────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@tamayoz.com"
    ADMIN_PASSWORD: str = "Admin@123456"

    # ─── Company Info ────────────────────────────────────────────────────────
    COMPANY_NAME: str = "مؤسسة سر التميز والأناقة"
    COMPANY_LOGO: str = "/static/logo.png"
    CURRENCY_DEFAULT: str = "SAR"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
