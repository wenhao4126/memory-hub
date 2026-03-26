# Memory Hub API 常见问题 📋

> **API 使用常见问题和解决方案**

---

## 📖 目录

1. [认证相关](#认证相关)
2. [智能体 API 问题](#智能体-api-问题)
3. [记忆 API 问题](#记忆-api-问题)
4. [任务 API 问题](#任务-api-问题)
5. [对话 API 问题](#对话-api-问题)
6. [搜索 API 问题](#搜索-api-问题)

---

## 认证相关

### Q: API 是否需要认证？

A: 当前版本不需要认证（内网使用）。生产环境建议添加 API Key 或 JWT 认证。

---

## 智能体 API 问题

### Q: 创建智能体时返回 422 错误？

A: 检查请求体格式：

**正确示例：**
```json
{
  "name": "小笔",
  "description": "文案专家",
  "capabilities": ["写作", "翻译"],
  "metadata": {}
}
```

**常见错误：**
```json
// ❌ 错误：缺少 name 字段
{
  "description": "文案专家"
}

// ❌ 错误：name 为空字符串
{
  "name": ""
}
```

---

## 记忆 API 问题

### Q: POST /memories 返回 422 错误？

A: **`agent_id` 是必需字段！** 请确保请求体中包含该字段。

**正确示例：**
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "用户喜欢简洁的回答",
  "memory_type": "preference",
  "importance": 0.8,
  "tags": ["用户偏好"]
}
```

**错误示例：**
```json
// ❌ 错误：缺少 agent_id
{
  "content": "用户喜欢简洁的回答",
  "memory_type": "preference"
}
```

**错误响应示例：**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "agent_id"],
      "msg": "Field required",
      "input": {
        "content": "用户喜欢简洁的回答"
      }
    }
  ]
}
```

**解决方案：**
1. 确保请求体中包含 `agent_id` 字段
2. `agent_id` 必须是有效的 UUID 格式
3. 可以先通过 `GET /api/v1/agents` 获取已创建的智能体 ID

---

### Q: 如何获取 agent_id？

A: 有两种方式：

**方式 1：创建智能体时保存返回的 ID**
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "小笔", "description": "文案专家"}'

# 响应：{"message": "智能体创建成功，ID: 550e8400-e29b-41d4-a716-446655440000"}
```

**方式 2：查询现有智能体列表**
```bash
curl http://localhost:8000/api/v1/agents
```

---

### Q: memory_type 有哪些可选值？

A: `memory_type` 支持以下枚举值（不区分大小写）：

| 值 | 说明 | 示例 |
|---|---|---|
| `fact` | 事实：客观信息 | "用户叫憨货" |
| `preference` | 偏好：用户喜好 | "喜欢简洁的回答" |
| `skill` | 技能：能力标签 | "擅长 Python" |
| `experience` | 经验：历史事件 | "去年完成过类似项目" |

**默认值：** `fact`

---

### Q: importance 字段如何设置？

A: `importance` 是 0.0-1.0 之间的浮点数：

- **0.0-0.3**: 低重要性（临时信息）
- **0.4-0.6**: 中等重要性（普通信息）
- **0.7-0.9**: 高重要性（核心信息）
- **1.0**: 最高重要性（永久记忆）

**默认值：** 0.5

---

## 任务 API 问题

### Q: POST /tasks 返回 422 错误？

A: **`task_type` 是必需字段！** 且 `priority` 必须是字符串枚举值。

**正确示例：**
```json
{
  "task_type": "code",
  "title": "修复 bug",
  "description": "修复登录页面的 bug",
  "priority": "high",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误示例：**
```json
// ❌ 错误 1：缺少 task_type
{
  "title": "修复 bug",
  "priority": "high"
}

// ❌ 错误 2：priority 是数字（应该是字符串）
{
  "task_type": "code",
  "title": "修复 bug",
  "priority": 1
}
```

**错误响应示例：**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "task_type"],
      "msg": "Field required"
    },
    {
      "type": "enum",
      "loc": ["body", "priority"],
      "msg": "Input should be 'low', 'normal', 'high' or 'urgent'",
      "input": 1
    }
  ]
}
```

---

### Q: task_type 有哪些可选值？

A: `task_type` 支持以下枚举值：

| 值 | 说明 |
|---|---|
| `search` | 搜索任务 |
| `write` | 写作任务 |
| `code` | 编码任务 |
| `review` | 审核任务 |
| `analyze` | 分析任务 |
| `design` | 设计任务 |
| `layout` | 布局任务 |
| `custom` | 自定义任务 |

---

### Q: priority 有哪些可选值？

A: `priority` 支持以下字符串枚举值：

| 值 | 说明 | 默认 |
|---|---|---|
| `low` | 低优先级 | |
| `normal` | 普通优先级 | ✅ 默认值 |
| `high` | 高优先级 | |
| `urgent` | 紧急优先级 | |

**注意：** 必须使用字符串，不能使用数字！

---

## 对话 API 问题

### Q: POST /chat 返回 422 错误？

A: **`agent_id` 和 `user_message` 是必需字段！** 且字段名必须是 `user_message`，不是 `message`。

**正确示例：**
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_123",
  "user_message": "你好，我是憨货"
}
```

**错误示例：**
```json
// ❌ 错误 1：字段名错误（message 应该是 user_message）
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "你好"
}

// ❌ 错误 2：缺少 agent_id
{
  "user_message": "你好"
}

// ❌ 错误 3：缺少 user_message
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误响应示例：**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "agent_id"],
      "msg": "Field required"
    },
    {
      "type": "missing",
      "loc": ["body", "user_message"],
      "msg": "Field required"
    }
  ]
}
```

---

### Q: session_id 如何设置？

A: `session_id` 是自定义的会话标识，用于区分不同的对话会话。

**建议格式：**
- 用户 ID + 时间戳：`user_123_20260320`
- 随机字符串：`session_abc123xyz`
- 业务标识：`chat_support_ticket_456`

**注意：**
- 长度限制：1-255 字符
- 同一个 session_id 的对话会保存历史记录

---

### Q: use_memory 和 use_history 参数有什么用？

A: 这两个参数控制对话增强功能：

| 参数 | 说明 | 默认值 |
|---|---|---|
| `use_memory` | 是否使用记忆增强（从数据库检索相关记忆） | `true` |
| `use_history` | 是否使用对话历史（检索历史对话） | `true` |
| `auto_extract` | 是否自动从对话中提取新记忆 | `true` |

**示例：**
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_123",
  "user_message": "你好",
  "use_memory": true,
  "use_history": true,
  "auto_extract": true
}
```

---

## 搜索 API 问题

### Q: POST /memories/search/semantic 返回 404？

A: **该端点暂未实现！** 请使用以下替代接口：

| 接口 | 说明 | 推荐度 |
|---|---|---|
| `POST /memories/search/text` | 文本搜索（自动生成向量） | ⭐⭐⭐ 推荐 |
| `POST /memories/search` | 向量搜索（需提供向量） | ⭐ 需自行生成向量 |

**推荐使用文本搜索：**
```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户喜欢什么？",
    "match_count": 5
  }'
```

---

### Q: 如何使用向量搜索？

A: 向量搜索需要自行生成 1024 维向量：

```bash
curl -X POST http://localhost:8000/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_embedding": [0.1, 0.2, 0.3, ...],  // 1024 维向量
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "match_threshold": 0.7,
    "match_count": 10
  }'
```

**推荐：** 直接使用 `/search/text` 接口，服务端会自动生成向量。

---

### Q: match_threshold 如何设置？

A: `match_threshold` 是相似度阈值（0.0-1.0）：

- **0.0-0.5**: 低阈值，返回更多结果（可能包含不相关内容）
- **0.6-0.8**: 中等阈值，平衡准确率和召回率
- **0.9-1.0**: 高阈值，只返回高度相关结果

**推荐值：** 0.7（默认值）

---

## 常见错误码

| 状态码 | 说明 | 常见原因 |
|--------|------|----------|
| 200 | 成功 | - |
| 201 | 创建成功 | - |
| 400 | 请求参数错误 | UUID 格式错误、参数类型错误 |
| 404 | 资源不存在 | ID 不存在、端点不存在 |
| 422 | 参数验证失败 | 缺少必需字段、字段格式错误 |
| 500 | 服务器内部错误 | 数据库连接失败、代码异常 |

---

## 快速测试命令

### 完整测试流程

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health

# 2. 创建智能体
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "测试智能体", "description": "测试用"}'

# 3. 创建记忆（替换 agent_id）
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "你的 agent_id",
    "content": "测试记忆内容",
    "memory_type": "fact"
  }'

# 4. 搜索记忆
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{"query": "测试", "match_count": 5}'

# 5. 创建任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "custom",
    "title": "测试任务",
    "priority": "normal"
  }'

# 6. 对话
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "你的 agent_id",
    "session_id": "test_session",
    "user_message": "你好"
  }'
```

---

*最后更新：2026-03-22*