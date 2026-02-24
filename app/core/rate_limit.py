"""请求限流中间件"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """获取客户端标识符（用于限流）
    
    优先使用认证用户ID，其次使用 X-Forwarded-For，最后使用远程地址
    """
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["200/minute"],
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """自定义限流响应"""
    logger.warning(f"[RATE LIMIT] 请求被限流: client={get_client_identifier(request)}, path={request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "请求过于频繁，请稍后再试",
                "detail": str(exc.detail)
            }
        }
    )


CHAT_RATE_LIMIT = "30/minute"
AUTH_RATE_LIMIT = "10/minute"
DEFAULT_RATE_LIMIT = "100/minute"
