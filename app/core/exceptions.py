from typing import Optional


class DragonAIException(Exception):
    """DragonAI 基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(DragonAIException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class UnauthorizedException(DragonAIException):
    """未授权异常"""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details
        )


class ForbiddenException(DragonAIException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details
        )


class BadRequestException(DragonAIException):
    """错误请求异常"""
    
    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details
        )


class ValidationException(DragonAIException):
    """验证异常"""
    
    def __init__(self, message: str = "Validation error", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class ExternalServiceException(DragonAIException):
    """外部服务异常"""
    
    def __init__(self, message: str = "External service error", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details
        )


class LLMException(DragonAIException):
    """LLM 服务异常"""
    
    def __init__(self, message: str = "LLM service error", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details=details
        )
