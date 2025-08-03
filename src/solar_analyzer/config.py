"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    # Database
    database_url: str = "postgresql://solar_user:solar_password@localhost:5432/solar_analyzer"

    # SunPower API
    sunpower_access_token: str = ""
    sunpower_site_key: str = ""
    sunpower_api_url: str = "https://monitor.mysunpower.com/CustomerPortal/api/v1/"

    # PVS6 Local Access
    pvs6_host: str = ""
    pvs6_port: int = 80

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"
    app_title: str = "Solar Analyzer"
    app_version: str = "0.1.0"

    # Data Collection
    data_collection_interval: int = 300  # seconds (5 minutes)
    data_retention_days: int = 365  # days to keep historical data

    # Logging
    log_level: str = "INFO"
    log_to_database: bool = True
    log_retention_days: int = 30  # days to keep logs in database
    performance_monitoring: bool = True


settings = Settings()
