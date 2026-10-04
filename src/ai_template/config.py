from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    debug: bool

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
