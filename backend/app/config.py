import json
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(value: str) -> list[str]:
    raw = value.strip()
    if not raw:
        return ["http://localhost:3000"]
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    if "," in raw:
        return [part.strip() for part in raw.split(",") if part.strip()]
    return [raw]


class Settings(BaseSettings):
    tavily_api_key: str = ""
    groq_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    agent_model: str = "llama-3.3-70b-versatile"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return parse_cors_origins(self.cors_origins)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
