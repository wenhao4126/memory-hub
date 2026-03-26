# 统一错误处理系统

## 概述

Memory Hub API 的统一错误处理系统，确保所有错误响应遵循一致的格式。

## 快速开始

```python
from app.errors import AgentNotFoundException, ValidationException

# 使用预定义异常
raise AgentNotFoundException(agent_id='xxx')

# 自定义验证错误
raise ValidationException(
    message="参数验证失败",
    field="agent_id",
    suggestion="请提供有效的 UUID"
)
```

## 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "E2000",
    "message": "智能体不存在",
    "detail": "找不到指定的智能体: xxx",
    "suggestion": "请检查智能体 ID 是否正确"
  },
  "meta": {
    "timestamp": "2026-03-22T23:43:00Z"
  }
}
```

## 错误代码

| 代码 | 说明 |
|------|------|
| E1002 | 验证错误 |
| E2000 | 智能体不存在 |
| E3000 | 记忆不存在 |
| E4000 | 任务不存在 |
| E5000 | 知识不存在 |
| E9000 | 数据库错误 |
| E9999 | 服务器内部错误 |

## 详细文档

参见 `/tmp/phase1-error/UNIFIED_ERROR_HANDLING.md`
