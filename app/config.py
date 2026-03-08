from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    skills_dir: str = "./storage/skills"

    log_level: str = "INFO"
    log_dir: str = "./logs"

    model_general_fast: str = "qwen-plus-2025-09-11"
    model_general_expert: str = "qwen-plus-2025-12-01"

    model_vision_ocr: str = "qwen-vl-ocr"
    model_vision_general: str = "qwen3-vl-plus"

    model_image_fast: str = "qwen-image"
    model_image_expert: str = "qwen-image-plus"

    model_image_edit: str = "qwen-image-edit"

    model_coder_fast: str = "qwen3-coder-flash"
    model_coder_expert: str = "qwen3-coder-plus"

    model_translation_fast: str = "qwen-mt-flash"
    model_translation_expert: str = "qwen-mt-plus"

    model_embedding: str = "text-embedding-v4"

    agent_recursion_limit: int = 25
    agent_tool_call_limit: int = 10
    agent_timeout: int = 120

    rate_limit_storage: str = "redis"
    rate_limit_default: str = "100/minute"
    rate_limit_chat: str = "30/minute"
    rate_limit_auth: str = "10/minute"

    max_request_size: int = 10 * 1024 * 1024

    rag_enable_hybrid: bool = False
    rag_hybrid_alpha: float = 0.5

    rag_enable_rerank: bool = False

    rag_rerank_provider: str = "cross-encoder"
    rag_rerank_model: str = "BAAI/bge-reranker-base"

    # cohere_api_key: str = "your-cohere-api-key-here"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
