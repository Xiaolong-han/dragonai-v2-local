"""请求追踪中间件"""

import uuid
import logging
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """获取当前请求的追踪 ID"""
    return request_id_var.get()


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件
    
    为每个请求生成唯一的追踪 ID，并添加到响应头和日志上下文中
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        request_id_var.set(request_id)
        
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        response.headers["X-Request-ID"] = request_id
        
        logger.debug(
            f"[REQUEST] method={request.method} path={request.url.path} "
            f"status_code={response.status_code} request_id={request_id}"
        )
        
        return response
