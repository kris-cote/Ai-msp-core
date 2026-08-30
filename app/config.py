from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./aimsp.db"
    redis_url: str = "redis://localhost:6379/0"
    ai_provider: str = "openai"
    ai_model: str = "gpt-5.6"
    autonomy_default: int = 1
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
