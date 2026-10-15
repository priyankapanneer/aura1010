
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AURA - Adaptive Utility-Aware AI Assistant"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./aura.db",
        description="Async database connection URL"
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./aura.db",
        description="Synchronous database connection URL for migrations"
    )

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai", "anthropic"
    LLM_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # Calendar Integration Provider
    CALENDAR_PROVIDER: str = "simulated"

    # Demo Mode & Seed
    DEMO_MODE: bool = True
    AUTO_SEED: bool = True

    # Security
    SECRET_KEY: str = "aura-super-secret-production-grade-key-at-least-32-chars-long"
    DEFAULT_USER_EMAIL: str = "aura_user@example.com"
    DEFAULT_USER_ID: str = "usr_default_aura_001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
