from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:devpassword@localhost:5432/trustlayer"
    app_env: str = "development"
    log_level: str = "info"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()