from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str  
    database_url : str

    ollama_base_url : str = "http://localhost:11434"
    ollama_model : str = "qwen3:1.7b"
    

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings() 
