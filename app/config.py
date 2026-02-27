
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

    skills_dir: str = "./storage/skills"

    log_level: str = "INFO"
    log_dir: str = "./logs"

    # 模型配置 - 开发者可自定义模型映射
    # 通用模型配置"qwen-flash-2025-07-28" deepseek-v3.2
    # glm支持4.5 4.6 4.7 5
    model_general_fast: str = "glm-4.6" 
    model_general_expert: str = "glm-4.7"
    
    # 视觉模型配置
    model_vision_ocr: str = "qwen-vl-ocr"
    model_vision_general: str = "qwen3-vl-plus"
    
    # 图像生成模型配置
    model_image_fast: str = "qwen-image"  # 使用qwen-image作为快速模型
    model_image_expert: str = "qwen-image-plus"  # 专家模型也用qwen-image-max
    
    # 图像编辑模型配置
    model_image_edit: str = "qwen-image-edit"  # 图像编辑模型
    
    # 编程模型配置
    model_coder_fast: str = "qwen3-coder-flash"
    model_coder_expert: str = "qwen3-coder-plus"
    
    # 翻译模型配置
    model_translation_fast: str = "qwen-mt-flash"
    model_translation_expert: str = "qwen-mt-plus"
    
    # Embedding模型配置
    model_embedding: str = "text-embedding-v4"
    
    # Agent配置
    agent_recursion_limit: int = 25  # Agent递归深度限制（工具调用最大轮次）

    class Config:
        env_file = ".env"
        case_sensitive = False





@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
