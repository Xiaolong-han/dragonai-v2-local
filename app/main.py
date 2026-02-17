
import logging
import os
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.redis import redis_client
from app.core.cache_warmup import cache_warmup
from app.api.v1 import auth, conversations, files, knowledge, skills, models, chat


def setup_logging():
    log_dir = settings.log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logging()
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    
    await redis_client.connect()
    logger.info("Redis connected")
    
    # 缓存预热
    try:
        await cache_warmup.warmup_all()
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")
    
    yield
    
    await redis_client.disconnect()
    logger.info("Redis disconnected")
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="AI Agent Backend System",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app_name": settings.app_name}


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "2.0.0",
        "docs": "/docs"
    }


app.include_router(auth.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1/knowledge")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )
