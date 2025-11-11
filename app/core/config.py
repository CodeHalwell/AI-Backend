"""
Core Configuration Module

This module manages all application configuration using Pydantic Settings.
Configuration is loaded from environment variables and .env files.

Why Pydantic Settings?
- Type safety and validation
- Automatic parsing of environment variables
- Support for complex types (lists, dicts)
- Easy testing with dependency injection
"""

import secrets
from typing import List, Optional

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings can be overridden via environment variables.
    The naming convention is: UPPERCASE_WITH_UNDERSCORES

    Example:
        DATABASE_URL=postgresql://...
        OPENAI_API_KEY=sk-...
    """

    # Application
    APP_NAME: str = "AI-Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode - disable in production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=4, description="Number of worker processes")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes - development only")

    # Database (PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_backend",
        description="PostgreSQL connection string with asyncpg driver"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max connections beyond pool size")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Timeout for getting connection from pool")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after N seconds")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses async driver."""
        if "postgresql://" in v:
            # Convert sync URL to async
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection string")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Max Redis connections in pool")
    REDIS_CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT encoding - MUST be set in production"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Ensure secret key is set in production."""
        if info.data.get("ENVIRONMENT") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed HTTP headers")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Requests per minute per user")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Requests per hour per user")

    # AI APIs
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", description="Default OpenAI model")
    OPENAI_MAX_TOKENS: int = Field(default=4096, description="Max tokens for AI responses")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="AI temperature (0-1)")

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    ENABLE_TRACING: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        description="OpenTelemetry OTLP endpoint for traces (gRPC)"
    )

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default items per page")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum items per page")

    @field_validator("DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE")
    @classmethod
    def validate_page_sizes(cls, v: int) -> int:
        """Ensure page sizes are reasonable."""
        if v < 1 or v > 1000:
            raise ValueError("Page size must be between 1 and 1000")
        return v

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10485760, description="Max upload size in bytes (10MB)")

    # Feature Flags
    ENABLE_REGISTRATION: bool = Field(default=True, description="Allow new user registration")
    ENABLE_EMAIL_VERIFICATION: bool = Field(default=False, description="Require email verification")
    ENABLE_TOOL_EXECUTION: bool = Field(default=True, description="Allow tool execution in agents")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "")


# Singleton instance
settings = Settings()


# Export for easy importing
__all__ = ["settings", "Settings"]
