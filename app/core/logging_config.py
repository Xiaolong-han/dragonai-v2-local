"""统一日志配置模块

提供集中管理的日志配置，包括：
- 日志级别控制
- 格式化器配置
- 处理器配置
- 第三方库日志控制
- 环境感知配置
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, List, Optional


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

THIRD_PARTY_LOG_LEVELS: Dict[str, str] = {
    "sqlalchemy.engine": "WARNING",
    "sqlalchemy.pool": "WARNING",
    "sqlalchemy.dialects": "WARNING",
    "httpx": "WARNING",
    "httpcore": "WARNING",
    "urllib3": "WARNING",
    "asyncio": "WARNING",
    "multipart": "WARNING",
    "uvicorn.access": "WARNING",
    "uvicorn.error": "INFO",
    "chromadb": "WARNING",
    "langchain": "WARNING",
    "langgraph": "WARNING",
    "openai": "WARNING",
    "anthropic": "WARNING",
    "http": "WARNING",
    "dashscope": "WARNING",
}


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        import datetime
        ct = self.converter(record.created)
        timestamp = datetime.datetime.fromtimestamp(
            record.created, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S") + f",{int(record.msecs):03d}"
        
        log_data = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "request_id") and record.request_id:
            log_data["request_id"] = record.request_id
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["data"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，支持添加额外上下文"""
    
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_log_level(env_level: str, default: str = "INFO") -> int:
    """获取日志级别"""
    return LOG_LEVELS.get(env_level.upper(), LOG_LEVELS.get(default.upper(), logging.INFO))


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    app_env: str = "development",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_structured: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    when: str = "midnight",
    interval: int = 1,
) -> None:
    """设置日志配置
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        app_env: 应用环境 (development/test/production)
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        enable_structured: 是否启用结构化日志
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        when: 时间轮转时机 (midnight, H, D, W0-W6)
        interval: 轮转间隔
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level(log_level))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers: List[logging.Handler] = []
    
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(get_log_level(log_level))
        
        if app_env == "development":
            console_format = ColoredConsoleFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        else:
            console_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        console_handler.setFormatter(console_format)
        handlers.append(console_handler)
    
    if enable_file:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(get_log_level(log_level))
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        handlers.append(file_handler)
        
        size_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "app_size.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        size_handler.setLevel(get_log_level(log_level))
        size_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        handlers.append(size_handler)
    
    if enable_structured:
        structured_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "structured.log"),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding="utf-8",
        )
        structured_handler.setLevel(get_log_level(log_level))
        structured_handler.setFormatter(StructuredFormatter())
        handlers.append(structured_handler)
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    configure_third_party_loggers(app_env)


def configure_third_party_loggers(app_env: str = "development") -> None:
    """配置第三方库日志级别
    
    Args:
        app_env: 应用环境，开发环境下可以适当放宽日志级别
    """
    for logger_name, level in THIRD_PARTY_LOG_LEVELS.items():
        lib_logger = logging.getLogger(logger_name)
        
        if app_env == "development" and level == "WARNING":
            lib_logger.setLevel(logging.INFO)
        else:
            lib_logger.setLevel(get_log_level(level))
        
        lib_logger.propagate = True
    
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
    sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.propagate = False


def get_logger(name: str, extra: Optional[Dict] = None) -> logging.Logger:
    """获取带有额外上下文的日志器
    
    Args:
        name: 日志器名称
        extra: 额外上下文信息
        
    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    if extra:
        return LoggerAdapter(logger, extra)
    return logger


class LogContext:
    """日志上下文管理器，用于临时修改日志级别"""
    
    def __init__(self, logger_name: str, level: str):
        self.logger = logging.getLogger(logger_name)
        self.original_level = self.logger.level
        self.temp_level = get_log_level(level)
    
    def __enter__(self):
        self.logger.setLevel(self.temp_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)
        return False


def log_execution_time(logger: logging.Logger, operation: str = "operation"):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"[{operation}] 完成, 耗时: {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[{operation}] 失败, 耗时: {elapsed:.3f}s, 错误: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"[{operation}] 完成, 耗时: {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[{operation}] 失败, 耗时: {elapsed:.3f}s, 错误: {e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
