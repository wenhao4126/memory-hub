# ============================================================
# 多智能体记忆中枢 - 统一错误处理模块
# ============================================================
# 功能：提供统一的错误响应格式和异常处理
# 作者：小码 3 号
# 日期：2026-03-22
# ============================================================

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 错误代码定义
# ============================================================

class ErrorCode:
    """错误代码定义"""
    # 通用错误 (1000-1099)
    UNKNOWN_ERROR = "E1000"
    INVALID_REQUEST = "E1001"
    VALIDATION_ERROR = "E1002"
    RESOURCE_NOT_FOUND = "E1003"
    UNAUTHORIZED = "E1004"
    FORBIDDEN = "E1005"
    RATE_LIMITED = "E1006"
    
    # 智能体错误 (2000-2099)
    AGENT_NOT_FOUND = "E2000"
    AGENT_ALREADY_EXISTS = "E2001"
    INVALID_AGENT_ID = "E2002"
    AGENT_CREATE_FAILED = "E2003"
    AGENT_UPDATE_FAILED = "E2004"
    AGENT_DELETE_FAILED = "E2005"
    
    # 记忆错误 (3000-3099)
    MEMORY_NOT_FOUND = "E3000"
    MEMORY_CREATE_FAILED = "E3001"
    MEMORY_UPDATE_FAILED = "E3002"
    MEMORY_DELETE_FAILED = "E3003"
    MEMORY_SEARCH_FAILED = "E3004"
    INVALID_MEMORY_TYPE = "E3005"
    INVALID_EMBEDDING = "E3006"
    
    # 任务错误 (4000-4099)
    TASK_NOT_FOUND = "E4000"
    TASK_CREATE_FAILED = "E4001"
    TASK_UPDATE_FAILED = "E4002"
    INVALID_TASK_TYPE = "E4003"
    INVALID_TASK_STATUS = "E4004"
    
    # 知识库错误 (5000-5099)
    KNOWLEDGE_NOT_FOUND = "E5000"
    KNOWLEDGE_CREATE_FAILED = "E5001"
    KNOWLEDGE_UPDATE_FAILED = "E5002"
    KNOWLEDGE_DELETE_FAILED = "E5003"
    
    # 对话错误 (6000-6099)
    CONVERSATION_NOT_FOUND = "E6000"
    CONVERSATION_CREATE_FAILED = "E6001"
    
    # 数据库错误 (9000-9099)
    DATABASE_ERROR = "E9000"
    DATABASE_CONNECTION_ERROR = "E9001"
    DATABASE_QUERY_ERROR = "E9002"
    
    # 服务器错误 (9999)
    INTERNAL_SERVER_ERROR = "E9999"


# ============================================================
# HTTP 状态码与错误代码映射
# ============================================================

HTTP_STATUS_TO_ERROR_CODE = {
    status.HTTP_400_BAD_REQUEST: ErrorCode.INVALID_REQUEST,
    status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
    status.HTTP_404_NOT_FOUND: ErrorCode.RESOURCE_NOT_FOUND,
    status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_ERROR,
    status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMITED,
    status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorCode.INTERNAL_SERVER_ERROR,
}


# ============================================================
# 统一错误响应模型
# ============================================================

class UnifiedErrorResponse:
    """
    统一错误响应格式
    
    所有 API 错误都使用此格式返回，确保客户端能够一致地处理错误。
    
    格式:
    {
        "success": false,
        "error": {
            "code": "E1001",
            "message": "人类可读的错误信息",
            "detail": "详细错误描述（可选）",
            "field": "出错的字段名（可选，用于验证错误）",
            "suggestion": "修复建议（可选）"
        },
        "meta": {
            "timestamp": "2026-03-22T23:43:00Z",
            "request_id": "req_xxx",
            "documentation": "https://docs.example.com/errors/E1001"
        }
    }
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        detail: Optional[str] = None,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
        request_id: Optional[str] = None,
        documentation_url: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.field = field
        self.suggestion = suggestion
        self.request_id = request_id
        self.documentation_url = documentation_url
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        from datetime import datetime
        
        error_obj = {
            "code": self.code,
            "message": self.message,
        }
        
        if self.detail:
            error_obj["detail"] = self.detail
        if self.field:
            error_obj["field"] = self.field
        if self.suggestion:
            error_obj["suggestion"] = self.suggestion
        
        from datetime import timezone
        meta_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        
        if self.request_id:
            meta_obj["request_id"] = self.request_id
        if self.documentation_url:
            meta_obj["documentation"] = self.documentation_url
        
        return {
            "success": False,
            "error": error_obj,
            "meta": meta_obj
        }
    
    def to_json_response(self, status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
        """转换为 FastAPI JSONResponse"""
        return JSONResponse(
            status_code=status_code,
            content=self.to_dict()
        )


# ============================================================
# 自定义异常类
# ============================================================

class APIException(HTTPException):
    """
    自定义 API 异常基类
    
    所有自定义异常都继承此类，确保统一的错误处理。
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[str] = None,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.field = field
        self.suggestion = suggestion
        
        # 构建统一的错误响应内容
        error_response = UnifiedErrorResponse(
            code=code,
            message=message,
            detail=detail,
            field=field,
            suggestion=suggestion
        )
        
        super().__init__(
            status_code=status_code,
            detail=error_response.to_dict(),
            headers=headers
        )


class ValidationException(APIException):
    """验证错误异常"""
    
    def __init__(
        self,
        message: str = "请求参数验证失败",
        detail: Optional[str] = None,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=detail,
            field=field,
            suggestion=suggestion
        )


class NotFoundException(APIException):
    """资源不存在异常"""
    
    def __init__(
        self,
        resource_type: str = "资源",
        resource_id: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        message = f"{resource_type}不存在"
        detail = f"找不到指定的{resource_type}"
        if resource_id:
            detail += f": {resource_id}"
        
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            suggestion=suggestion or "请检查资源 ID 是否正确"
        )


class AgentNotFoundException(NotFoundException):
    """智能体不存在异常"""
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(
            resource_type="智能体",
            resource_id=agent_id,
            suggestion="请检查智能体 ID 是否正确，或使用 /api/v1/agents 列出所有智能体"
        )
        self.code = ErrorCode.AGENT_NOT_FOUND


class MemoryNotFoundException(NotFoundException):
    """记忆不存在异常"""
    
    def __init__(self, memory_id: Optional[str] = None):
        super().__init__(
            resource_type="记忆",
            resource_id=memory_id,
            suggestion="请检查记忆 ID 是否正确"
        )
        self.code = ErrorCode.MEMORY_NOT_FOUND


class TaskNotFoundException(NotFoundException):
    """任务不存在异常"""
    
    def __init__(self, task_id: Optional[str] = None):
        super().__init__(
            resource_type="任务",
            resource_id=task_id,
            suggestion="请检查任务 ID 是否正确"
        )
        self.code = ErrorCode.TASK_NOT_FOUND


class KnowledgeNotFoundException(NotFoundException):
    """知识不存在异常"""
    
    def __init__(self, knowledge_id: Optional[str] = None):
        super().__init__(
            resource_type="知识",
            resource_id=knowledge_id,
            suggestion="请检查知识 ID 是否正确"
        )
        self.code = ErrorCode.KNOWLEDGE_NOT_FOUND


class ConversationNotFoundException(NotFoundException):
    """对话不存在异常"""
    
    def __init__(self, conversation_id: Optional[str] = None):
        super().__init__(
            resource_type="对话",
            resource_id=conversation_id,
            suggestion="请检查对话 ID 是否正确"
        )
        self.code = ErrorCode.CONVERSATION_NOT_FOUND


class DatabaseException(APIException):
    """数据库错误异常"""
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        detail: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            suggestion=suggestion or "请稍后重试，或联系管理员"
        )


class PermissionDeniedException(APIException):
    """权限不足异常"""
    
    def __init__(
        self,
        message: str = "权限不足",
        detail: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail or "您没有执行此操作的权限",
            suggestion=suggestion or "请检查您的权限设置，或联系管理员"
        )


class AuthenticationException(APIException):
    """认证失败异常"""
    
    def __init__(
        self,
        message: str = "认证失败",
        detail: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "请提供有效的认证信息",
            suggestion=suggestion or "请检查 API Key 是否正确",
            headers={"WWW-Authenticate": "ApiKey"}
        )


class RateLimitException(APIException):
    """请求限流异常"""
    
    def __init__(
        self,
        message: str = "请求过于频繁",
        detail: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail or "您的请求频率超过了限制",
            suggestion=suggestion or "请稍后重试，或降低请求频率"
        )


# ============================================================
# 错误响应构建函数
# ============================================================

def create_error_response(
    code: str,
    message: str,
    detail: Optional[str] = None,
    field: Optional[str] = None,
    suggestion: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    创建统一格式的错误响应
    
    Args:
        code: 错误代码
        message: 错误消息
        detail: 详细描述
        field: 出错的字段名
        suggestion: 修复建议
        status_code: HTTP 状态码
    
    Returns:
        JSONResponse: FastAPI JSON 响应
    """
    error_response = UnifiedErrorResponse(
        code=code,
        message=message,
        detail=detail,
        field=field,
        suggestion=suggestion
    )
    
    return error_response.to_json_response(status_code)


def create_validation_error_response(
    errors: List[Dict[str, Any]],
    message: str = "请求参数验证失败"
) -> JSONResponse:
    """
    创建验证错误响应
    
    Args:
        errors: 错误列表，每个错误包含 field, message, type
        message: 错误消息
    
    Returns:
        JSONResponse: FastAPI JSON 响应
    """
    error_details = []
    for error in errors:
        error_details.append({
            "field": error.get("field"),
            "message": error.get("message"),
            "type": error.get("type")
        })
    
    return create_error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        detail=f"共 {len(errors)} 个字段验证失败",
        suggestion="请检查请求参数，确保所有必填字段都已正确提供",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# ============================================================
# 全局异常处理器
# ============================================================

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    
    捕获所有未处理的异常，返回统一的错误响应格式。
    """
    # 如果已经是 APIException，使用其内置的错误信息
    if isinstance(exc, APIException):
        logger.error(f"APIException: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # 处理 HTTPException（包括 FastAPI 内置的）
    if isinstance(exc, HTTPException):
        # 如果 detail 已经是字典（统一格式），直接返回
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # 否则，转换为统一格式
        error_code = HTTP_STATUS_TO_ERROR_CODE.get(
            exc.status_code, 
            ErrorCode.UNKNOWN_ERROR
        )
        
        return create_error_response(
            code=error_code,
            message="请求处理失败",
            detail=str(exc.detail),
            status_code=exc.status_code
        )
    
    # 处理 ValueError（通常是业务逻辑错误）
    if isinstance(exc, ValueError):
        logger.warning(f"ValueError: {exc}")
        return create_error_response(
            code=ErrorCode.INVALID_REQUEST,
            message="请求参数错误",
            detail=str(exc),
            suggestion="请检查请求参数是否符合要求"
        )
    
    # 处理所有其他未预期的异常
    logger.exception(f"未预期的异常: {exc}")
    return create_error_response(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="服务器内部错误",
        detail="发生未预期的错误，请稍后重试",
        suggestion="如果问题持续存在，请联系管理员"
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    验证异常处理器（用于替换 FastAPI 默认的验证错误处理器）
    """
    from fastapi.exceptions import RequestValidationError
    
    if isinstance(exc, RequestValidationError):
        errors = []
        for error in exc.errors():
            loc = error.get("loc", [])
            field = loc[-1] if len(loc) > 0 else "unknown"
            errors.append({
                "field": field,
                "message": error.get("msg", "验证失败"),
                "type": error.get("type", "unknown")
            })
        
        return create_validation_error_response(errors)
    
    return await global_exception_handler(request, exc)