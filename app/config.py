"""
Configuration Management

Application configuration loaded from environment variables.
"""

import logging
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "openstack-vm-api"
    api_version: str = "v1"
    environment: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    # OpenStack Integration
    use_real_openstack: bool = (
        False  # Set to True to use real OpenStack instead of mock
    )
    openstack_auth_url: Optional[str] = None
    openstack_username: Optional[str] = None
    openstack_password: Optional[str] = None
    openstack_project_name: Optional[str] = None
    openstack_project_domain_name: Optional[str] = "Default"
    openstack_user_domain_name: Optional[str] = "Default"
    openstack_region_name: Optional[str] = "RegionOne"

    # Database (for future use)
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis (for future caching)
    redis_url: Optional[str] = None
    redis_max_connections: int = 10

    # Security (for future authentication)
    secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True

    # Rate Limiting (for future use)
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Global settings instance
settings = Settings()


def configure_logging():
    """Configure application logging"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set uvicorn log level
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)


# Configure logging on module import
configure_logging()
