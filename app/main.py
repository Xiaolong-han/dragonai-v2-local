import asyncio
import os

import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.redis import redis_client
from app.core.cache_warmup import cache_warmup
from app.core.exceptions import DragonAIException
from app.agents.agent_factory import AgentFactory
from app.api.v1 import auth, conversations, files, knowledge, tools, models, chat


def setup_logging():
    log_dir = settings.log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)


async def dragonai_exception_handler(request: Request, exc: DragonAIException):
    """统一异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger()
    logger.info("Starting DragonAI...")

    await AgentFactory.init_checkpointer()
    logger.info("Checkpointer initialized")

    await redis_client.connect()
    logger.info("Redis connected")

    try:
        await cache_warmup.warmup_all()
    except Exception as e:
        logger.warning(f"[CACHE WARMUP] Cache warmup failed, continuing startup: {e}")

    yield

    await AgentFactory.close_checkpointer()

    await redis_client.close()
    logger.info("Shutting down DragonAI")


def create_app():
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="DragonAI API",
        description="DragonAI - 智能AI助手",
        version="2.0.0",
        lifespan=lifespan
    )
    
    app.add_exception_handler(DragonAIException, dragonai_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(knowledge.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")
    app.include_router(models.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Welcome to DragonAI API", "version": "2.0.0"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
