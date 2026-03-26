# ============================================================
# 多智能体记忆中枢 - API 路由示例（统一错误格式）
# ============================================================
# 功能：展示如何使用统一错误格式的示例代码
# 作者：小码 3 号
# 日期：2026-03-22
# ============================================================

"""
统一错误处理使用示例

本文件展示了如何在路由中使用新的统一错误格式。

## 旧方式（不推荐）
```python
from fastapi import HTTPException, status

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    row = await db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_uuid)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"智能体不存在: {agent_id}"
        )
    return Agent(**dict(row))
```

## 新方式（推荐）
```python
from ..errors import (
    AgentNotFoundException,
    ValidationException,
    create_error_response,
    ErrorCode
)

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise ValidationException(
            message="无效的智能体 ID 格式",
            detail=f"提供的 ID '{agent_id}' 不是有效的 UUID 格式",
            suggestion="请提供有效的 UUID 格式，例如：550e8400-e29b-41d4-a716-446655440000"
        )
    
    row = await db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_uuid)
    if not row:
        raise AgentNotFoundException(agent_id=agent_id)
    
    return Agent(**dict(row))
```

## 错误响应格式对比

### 旧格式
```json
{
  "detail": "智能体不存在: xxx"
}
```

### 新格式（统一）
```json
{
  "success": false,
  "error": {
    "code": "E2000",
    "message": "智能体不存在",
    "detail": "找不到指定的智能体: xxx",
    "suggestion": "请检查智能体 ID 是否正确，或使用 /api/v1/agents 列出所有智能体"
  },
  "meta": {
    "timestamp": "2026-03-22T23:43:00Z"
  }
}
```

## 可用的异常类

### 基础异常
- `APIException` - 所有自定义异常的基类
- `ValidationException` - 验证错误
- `NotFoundException` - 资源不存在
- `DatabaseException` - 数据库错误
- `PermissionDeniedException` - 权限不足
- `AuthenticationException` - 认证失败
- `RateLimitException` - 请求限流

### 具体资源异常
- `AgentNotFoundException` - 智能体不存在
- `MemoryNotFoundException` - 记忆不存在
- `TaskNotFoundException` - 任务不存在
- `KnowledgeNotFoundException` - 知识不存在
- `ConversationNotFoundException` - 对话不存在

## 错误代码

| 代码 | 含义 |
|------|------|
| E1000 | 未知错误 |
| E1001 | 无效请求 |
| E1002 | 验证错误 |
| E1003 | 资源不存在 |
| E1004 | 未授权 |
| E1005 | 禁止访问 |
| E1006 | 请求限流 |
| E2000 | 智能体不存在 |
| E3000 | 记忆不存在 |
| E4000 | 任务不存在 |
| E5000 | 知识不存在 |
| E6000 | 对话不存在 |
| E9000 | 数据库错误 |
| E9999 | 服务器内部错误 |
"""

# 导入示例（实际使用时请从正确的路径导入）
# from ..errors import (
#     ErrorCode,
#     create_error_response,
#     AgentNotFoundException,
#     ValidationException,
#     DatabaseException,
#     NotFoundException
# )