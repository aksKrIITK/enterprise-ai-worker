from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise AI Orchestrator"
    PORT: int = 8000
    DEBUG: bool = False

    SERVICE_TO_SERVICE_SECRET: str = "super_secret_jwt_service_token_gateway_to_orchestrator_internal_communication"
    DEFAULT_LLM_PROVIDER: str = "openai"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")



settings = Settings()
