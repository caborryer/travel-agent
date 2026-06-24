from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    tavily_api_key: str = ""
    groq_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    agent_model: str = "llama-3.3-70b-versatile"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
