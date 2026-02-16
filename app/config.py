
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DragonAI"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str = "postgresql://user:password@localhost:5432/dragonai"

    redis_url: str = "redis://localhost:6379/0"

    chroma_persist_dir: str = "./chroma_db"

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    tavily_api_key: str = ""

    storage_dir: str = "./storage"

    log_level: str = "INFO"
    log_dir: str = "./logs"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
