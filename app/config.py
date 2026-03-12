from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "adaptive_diagnostic"
    GROQ_API_KEY: str = ""
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Adaptive test config
    INITIAL_ABILITY: float = 0.5
    MAX_QUESTIONS: int = 10
    DIFFICULTY_MIN: float = 0.1
    DIFFICULTY_MAX: float = 1.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
