
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

    # 通义千问API配置
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 图像生成API配置（阿里云百炼多模态生成API）
    qwen_image_base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    tavily_api_key: str = ""

    storage_dir: str = "./storage"

    log_level: str = "INFO"
    log_dir: str = "./logs"

    # 模型配置 - 开发者可自定义模型映射
    # 通用模型配置
    model_general_fast: str = "qwen-flash" 
    model_general_expert: str = "qwen3-max"
    
    # 视觉模型配置
    model_vision_ocr: str = "qwen-vl-ocr"
    model_vision_general: str = "qwen3-vl-plus"
    
    # 图像生成模型配置
    model_image_fast: str = "qwen-image"  # 使用qwen-image作为快速模型
    model_image_expert: str = "qwen-image-plus"  # 专家模型也用qwen-image-max
    
    # 编程模型配置
    model_coder_fast: str = "qwen3-coder-flash"
    model_coder_expert: str = "qwen3-coder-plus"
    
    # 翻译模型配置
    model_translation_fast: str = "qwen-mt-flash"
    model_translation_expert: str = "qwen-mt-plus"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 模型能力配置
MODEL_CAPABILITIES = {
    "qwen3-max": {"supports_thinking": True, "supports_streaming": True},
    "qwen-plus": {"supports_thinking": True, "supports_streaming": True},
    "qwen-flash": {"supports_thinking": False, "supports_streaming": True},
    "qwen3-vl-plus": {"supports_thinking": False, "supports_streaming": True},
    "qwen3-vl-flash": {"supports_thinking": False, "supports_streaming": True},
    "qwen-vl-ocr": {"supports_thinking": False, "supports_streaming": True},
    "z-image-turbo": {"supports_thinking": False, "supports_streaming": False},
    "qwen-image": {"supports_thinking": False, "supports_streaming": False},
    "qwen-image-plus": {"supports_thinking": False, "supports_streaming": False},
    "qwen3-coder-flash": {"supports_thinking": False, "supports_streaming": True},
    "qwen3-coder-plus": {"supports_thinking": True, "supports_streaming": True},
    "qwen-mt-flash": {"supports_thinking": False, "supports_streaming": True},
    "qwen-mt-plus": {"supports_thinking": False, "supports_streaming": True},
}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
