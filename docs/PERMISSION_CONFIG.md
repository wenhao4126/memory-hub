# Memory Hub 数据库权限配置

> **创建日期**: 2026-03-17
> **创建者**: 小码 🟡
> **需求来源**: 憨货亲定

---

## 📋 权限规则总览

### 1. parallel_tasks 表（并行任务）

| 操作 | 允许的智能体 | 说明 |
|------|-------------|------|
| **写入** | 傻妞 | 只有傻妞能创建任务 |
| **读取** | 小码, team-coder2-5 | 小码池能领取/读取任务 |
| **其他** | 无权限 | 其他智能体无法访问 |

**设计决策**：
- 傻妞是 CEO，负责派发任务
- 小码池负责执行任务，只能读取分配给自己的任务
- 其他智能体（小搜、小写等）不使用任务系统

---

### 2. shared_memories 表（共享记忆）

| 操作 | 允许的智能体 | 说明 |
|------|-------------|------|
| **读取** | 所有智能体 | 全员可读 |
| **写入** | 小搜, 小写, 小审, 小析, 小览, 小图, 小排 | 执行任务的智能体 |
| **禁止写入** | 小码, team-coder2-5 | 小码池不能写共享记忆 |

**设计决策**：
- 共享记忆是团队知识库，所有人都能学习
- 只有执行任务的智能体才能创建共享记忆
- 小码池专注于代码开发，不应该产生业务记忆

---

### 3. knowledge 表（知识库）

| 操作 | 允许的智能体 | 说明 |
|------|-------------|------|
| **读取** | 所有智能体 | 全员可读 |
| **写入** | 所有智能体 | 全员可写 |

**设计决策**：
- 知识库存储 .md 文档，所有智能体都能生成
- 开放写入鼓励知识沉淀

---

### 4. private_memories 表（私人记忆）

| 操作 | 允许的智能体 | 说明 |
|------|-------------|------|
| **读取** | 创建者（owner） | 只能访问自己的私人记忆 |
| **写入** | 创建者（owner） | 只能写自己的私人记忆 |

**设计决策**：
- 私人记忆包含敏感信息（密码、偏好等）
- 严格隔离，只允许创建者访问

---

## 📁 文件结构

```
/home/wen/projects/memory-hub/
├── backend/app/
│   ├── config/
│   │   └── permissions.json          # 权限配置文件
│   └── services/
│       └── permission_service.py     # 权限服务
├── sdk/
│   └── task_service.py               # SDK 层权限校验
└── scripts/
    └── test_permissions.py           # 权限测试脚本
```

---

## 🔧 使用方法

### API 层权限校验

```python
from ..services.permission_service import permission_service

# 检查权限
if not permission_service.check_permission(agent_id, "shared_memories", "write"):
    raise HTTPException(status_code=403, detail="无权限")

# 或使用 require_permission（自动抛出异常）
permission_service.require_permission(agent_id, "shared_memories", "write")
```

### SDK 层权限校验

```python
from task_service import check_parallel_tasks_permission, PermissionDeniedError

# 检查权限
if not check_parallel_tasks_permission(agent_id, "write"):
    raise PermissionDeniedError(f"智能体 {agent_id} 无权限创建任务")
```

---

## ✅ 测试验证

运行测试脚本：

```bash
cd /home/wen/projects/memory-hub
python scripts/test_permissions.py
```

**测试结果**：
- ✅ parallel_tasks 权限测试: 8/8 通过
- ✅ shared_memories 权限测试: 7/7 通过
- ✅ knowledge 权限测试: 6/6 通过
- ✅ TaskService 集成测试: 4/4 通过

---

## 📝 更新记录

| 日期 | 变更内容 | 操作人 |
|------|---------|--------|
| 2026-03-17 | 创建权限配置文件 | 小码 🟡 |
| 2026-03-17 | 创建权限服务 | 小码 🟡 |
| 2026-03-17 | 修改 API 路由添加权限校验 | 小码 🟡 |
| 2026-03-17 | 修改 SDK 添加权限校验 | 小码 🟡 |
| 2026-03-17 | 创建测试脚本并验证 | 小码 🟡 |

---

## 🔐 安全注意事项

1. **权限配置文件**（`permissions.json`）应该被保护，避免未授权修改
2. **生产环境**建议使用数据库存储权限配置，而不是 JSON 文件
3. **日志记录**所有权限拒绝事件，便于安全审计
4. **定期审查**权限配置，确保符合业务需求

---

_此文档由小码 🟡 创建，憨货审核通过。_