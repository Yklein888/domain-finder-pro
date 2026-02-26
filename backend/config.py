import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/domain_finder")

    # API Keys
    APIFY_TOKEN: str = os.getenv("APIFY_TOKEN", "")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SLACK_WEBHOOK: str = os.getenv("SLACK_WEBHOOK", "")

    # App Settings
    APP_NAME: str = "Domain Finder Pro"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # Scraper Settings
    SCRAPER_ENABLED: bool = os.getenv("SCRAPER_ENABLED", "True").lower() == "true"
    SCRAPER_TIME: str = os.getenv("SCRAPER_TIME", "09:00")  # 9 AM UTC

    # Alert Settings
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "70"))
    TOP_DOMAINS_COUNT: int = int(os.getenv("TOP_DOMAINS_COUNT", "20"))

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
