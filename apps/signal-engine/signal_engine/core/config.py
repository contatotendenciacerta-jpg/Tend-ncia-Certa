from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://localhost:6379/0"
    API_BASE_URL: str = "http://localhost:8000"
    API_INTERNAL_TOKEN: str = "changeme"


settings = Settings()
