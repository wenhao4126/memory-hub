# Memory Hub API 文档 🔌

> **完整的 RESTful API 参考手册**

---

## 📖 目录

1. [API 概览](#api 概览)
2. [认证说明](#认证说明)
3. [智能体 API](#智能体 api)
4. [记忆 API](#记忆 api)
5. [对话 API](#对话 api)
6. [搜索 API](#搜索 api)
7. [维护 API](#维护 api)
8. [错误码](#错误码)

---

## API 概览

### 基础信息

- **基础 URL**：`http://localhost:8000/api/v1`
- **文档地址**：`http://localhost:8000/docs`（Swagger UI）
- **数据格式**：JSON
- **字符编码**：UTF-8

### 快速测试

使用 Swagger UI 测试所有接口：

1. 打开 http://localhost:8000/docs
2. 展开任意接口
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"

### 通用响应格式

**成功响应（200/201）：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "智能体名称",
  ...
}
```

**消息响应：**

```json
{
  "message": "操作成功",
  "success": true
}
```

**错误响应：**

```json
{
  "error": "错误类型",
  "detail": "详细描述",
  "status_code": 404
}
```

---

## 认证说明

当前版本不需要认证（内网使用）。

生产环境建议添加：
- API Key 认证
- JWT Token 认证
- OAuth 2.0

---

## 智能体 API

### 创建智能体

**请求：**

```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "小笔",
  "description": "文案专家，擅长写文章和翻译",
  "capabilities": ["写作", "翻译", "润色"],
  "metadata": {
    "team_id": "003",
    "role": "writer"
  }
}
```

**响应（201）：**

```json
{
  "message": "智能体创建成功，ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 智能体名称，1-255 字符 |
| description | string | ❌ | 描述信息 |
| capabilities | string[] | ❌ | 能力标签列表 |
| metadata | object | ❌ | 任意 JSON 对象 |

**cURL 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔",
    "description": "文案专家",
    "capabilities": ["写作", "翻译"],
    "metadata": {"team_id": "003"}
  }'
```

---

### 获取智能体详情

**请求：**

```http
GET /api/v1/agents/{agent_id}
```

**响应（200）：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "小笔",
  "description": "文案专家，擅长写文章",
  "capabilities": ["写作", "翻译", "润色"],
  "metadata": {
    "team_id": "003",
    "role": "writer"
  },
  "created_at": "2026-03-09T10:00:00Z",
  "updated_at": "2026-03-09T10:00:00Z"
}
```

**cURL 示例：**

```bash
curl http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000
```

---

### 列出所有智能体

**请求：**

```http
GET /api/v1/agents?limit=50&offset=0
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 返回数量（1-100） |
| offset | int | 0 | 偏移量 |

**响应（200）：**

```json
[
  {
    "id": "uuid-1",
    "name": "小搜",
    "description": "搜索专家",
    "capabilities": ["搜索", "研究"],
    "metadata": {},
    "created_at": "2026-03-09T09:00:00Z",
    "updated_at": "2026-03-09T09:00:00Z"
  },
  {
    "id": "uuid-2",
    "name": "小码",
    "description": "程序员",
    "capabilities": ["编程", "调试"],
    "metadata": {},
    "created_at": "2026-03-09T09:30:00Z",
    "updated_at": "2026-03-09T09:30:00Z"
  }
]
```

**cURL 示例：**

```bash
curl "http://localhost:8000/api/v1/agents?limit=10&offset=0"
```

---

### 更新智能体

**请求：**

```http
PUT /api/v1/agents/{agent_id}
Content-Type: application/json

{
  "name": "小笔（高级）",
  "description": "资深文案专家，10 年经验"
}
```

**说明：**
- 只更新提供的字段
- 未提供的字段保持不变

**响应（200）：**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "小笔（高级）",
  "description": "资深文案专家，10 年经验",
  "capabilities": ["写作", "翻译", "润色"],
  "metadata": {"team_id": "003"},
  "created_at": "2026-03-09T10:00:00Z",
  "updated_at": "2026-03-09T11:00:00Z"
}
```

**cURL 示例：**

```bash
curl -X PUT http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔（高级）"
  }'
```

---

### 删除智能体

**请求：**

```http
DELETE /api/v1/agents/{agent_id}
```

**说明：**
- 级联删除该智能体的所有记忆
- 不可恢复

**响应（200）：**

```json
{
  "message": "智能体删除成功"
}
```

**cURL 示例：**

```bash
curl -X DELETE http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000
```

---

## 记忆 API

### 创建记忆

**请求：**

```http
POST /api/v1/memories
Content-Type: application/json

{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "用户喜欢简洁的回答，讨厌废话",
  "memory_type": "preference",
  "importance": 0.8,
  "tags": ["用户偏好", "沟通风格"],
  "metadata": {}
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | string | ✅ | 所属智能体 ID（UUID） |
| content | string | ✅ | 记忆内容 |
| memory_type | string | ❌ | fact/preference/skill/experience（默认 fact） |
| importance | float | ❌ | 重要性 0-1（默认 0.5） |
| tags | string[] | ❌ | 标签列表 |
| metadata | object | ❌ | 额外元数据 |
| embedding | float[] | ❌ | 向量（可选，自动生成） |
| expires_at | datetime | ❌ | 过期时间 |

**响应（201）：**

```json
{
  "message": "记忆创建成功，ID: 660e8400-e29b-41d4-a716-446655440001"
}
```

**cURL 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "用户喜欢简洁的回答",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好"]
  }'
```

---

### 获取单条记忆

**请求：**

```http
GET /api/v1/memories/{memory_id}
```

**说明：**
- 获取时会自动增加访问计数

**响应（200）：**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "用户喜欢简洁的回答，讨厌废话",
  "memory_type": "preference",
  "importance": 0.8,
  "access_count": 5,
  "tags": ["用户偏好", "沟通风格"],
  "metadata": {},
  "created_at": "2026-03-09T10:00:00Z",
  "last_accessed": "2026-03-09T12:00:00Z",
  "expires_at": null
}
```

**cURL 示例：**

```bash
curl http://localhost:8000/api/v1/memories/660e8400-e29b-41d4-a716-446655440001
```

---

### 更新记忆

**请求：**

```http
PUT /api/v1/memories/{memory_id}
Content-Type: application/json

{
  "content": "用户非常喜欢简洁的回答，极其讨厌废话",
  "importance": 0.9
}
```

**说明：**
- 只更新提供的字段

**响应（200）：**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "用户非常喜欢简洁的回答，极其讨厌废话",
  "memory_type": "preference",
  "importance": 0.9,
  "access_count": 5,
  "tags": ["用户偏好", "沟通风格"],
  "metadata": {},
  "created_at": "2026-03-09T10:00:00Z",
  "last_accessed": "2026-03-09T12:00:00Z",
  "expires_at": null
}
```

**cURL 示例：**

```bash
curl -X PUT http://localhost:8000/api/v1/memories/660e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -d '{
    "importance": 0.9
  }'
```

---

### 删除记忆

**请求：**

```http
DELETE /api/v1/memories/{memory_id}
```

**响应（200）：**

```json
{
  "message": "记忆删除成功"
}
```

**cURL 示例：**

```bash
curl -X DELETE http://localhost:8000/api/v1/memories/660e8400-e29b-41d4-a716-446655440001
```

---

### 列出智能体的所有记忆

**请求：**

```http
GET /api/v1/agents/{agent_id}/memories?limit=50&offset=0
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 返回数量（1-100） |
| offset | int | 0 | 偏移量 |

**响应（200）：**

```json
[
  {
    "id": "记忆 ID",
    "agent_id": "智能体 ID",
    "content": "记忆内容 1",
    "memory_type": "preference",
    "importance": 0.8,
    "access_count": 5,
    "tags": ["标签 1"],
    "created_at": "2026-03-09T10:00:00Z"
  },
  {
    "id": "记忆 ID",
    "agent_id": "智能体 ID",
    "content": "记忆内容 2",
    "memory_type": "fact",
    "importance": 0.6,
    "access_count": 2,
    "tags": [],
    "created_at": "2026-03-09T11:00:00Z"
  }
]
```

**cURL 示例：**

```bash
curl "http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/memories?limit=10"
```

---

## 搜索 API

### 文本相似性搜索（推荐）⭐

**请求：**

```http
POST /api/v1/memories/search/text
Content-Type: application/json

{
  "query": "用户喜欢什么？",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "match_threshold": 0.7,
  "match_count": 10
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 查询文本 |
| agent_id | string | ❌ | 限定智能体（不填则搜索全部） |
| match_threshold | float | ❌ | 相似度阈值 0-1（默认 0.7） |
| match_count | int | ❌ | 返回数量 1-100（默认 10） |

**响应（200）：**

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "similarity": 0.92,
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好", "沟通风格"]
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "用户偏好简短的回复",
    "similarity": 0.85,
    "memory_type": "preference",
    "importance": 0.7,
    "tags": ["用户偏好"]
  }
]
```

**说明：**
- 服务端自动生成查询向量
- 返回按相似度降序排列
- similarity 越接近 1 越相似

**cURL 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户喜欢什么？",
    "match_count": 5
  }'
```

---

### 向量相似性搜索（旧版）

**请求：**

```http
POST /api/v1/memories/search
Content-Type: application/json

{
  "query_embedding": [0.1, 0.2, 0.3, ...],
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "match_threshold": 0.7,
  "match_count": 10
}
```

**说明：**
- 需要客户端提供 1024 维向量
- 推荐使用 `/search/text` 接口

---

## 对话 API

### 增强对话（核心功能）⭐

**请求：**

```http
POST /api/v1/chat
Content-Type: application/json

{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_123",
  "user_message": "你好，我是憨货，喜欢吐槽风格",
  "use_memory": true,
  "use_history": true,
  "auto_extract": true
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | string | ✅ | 智能体 ID |
| session_id | string | ✅ | 会话标识（自定义） |
| user_message | string | ✅ | 用户消息 |
| use_memory | boolean | ❌ | 是否使用记忆增强（默认 true） |
| use_history | boolean | ❌ | 是否使用对话历史（默认 true） |
| auto_extract | boolean | ❌ | 是否自动提取记忆（默认 true） |

**响应（200）：**

```json
{
  "reply": "憨货你好！👋 收到你的偏好：吐槽风格 + 简洁回答。有啥需要尽管说，保证不整废话！😄",
  "memories_used": [
    {
      "id": "记忆 ID",
      "content": "用户喜欢简洁的回答，讨厌废话",
      "similarity": 0.92
    }
  ],
  "memories_extracted": [
    {
      "id": "新记忆 ID",
      "content": "用户自称憨货",
      "memory_type": "fact"
    }
  ],
  "session_id": "session_123",
  "conversation_id": "对话 ID"
}
```

**工作流程：**

1. **检索记忆**：基于用户消息向量搜索相关记忆
2. **获取历史**：获取该 session 的对话历史
3. **生成回复**：调用 LLM，融合记忆和历史生成个性化回复
4. **记录对话**：保存对话到数据库
5. **提取记忆**：分析对话，自动提取新记忆

**cURL 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "test_session",
    "user_message": "帮我写个文案"
  }'
```

---

## 维护 API

### 清理过期记忆

**请求：**

```http
POST /api/v1/memories/cleanup?days_old=30&min_importance=0.3&max_access_count=3
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days_old | int | 30 | 保留天数（1-365） |
| min_importance | float | 0.3 | 最小重要性 0-1 |
| max_access_count | int | 3 | 最大访问次数 |

**清理规则：**

同时满足以下条件的记忆会被删除：
- 创建时间超过 `days_old` 天
- 重要性低于 `min_importance`
- 访问次数少于 `max_access_count`

**响应（200）：**

```json
{
  "message": "已清理 15 条过期记忆"
}
```

**cURL 示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/memories/cleanup?days_old=30&min_importance=0.3&max_access_count=3"
```

---

### 健康检查

**请求：**

```http
GET /api/v1/health
```

**响应（200）：**

```json
{
  "status": "ok",
  "database": "connected",
  "version": "0.1.0"
}
```

**说明：**
- 用于监控服务状态
- 检查数据库连接

**cURL 示例：**

```bash
curl http://localhost:8000/api/v1/health
```

---

## 错误码

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

### 常见错误

#### 400 Bad Request

```json
{
  "error": "Bad Request",
  "detail": "无效的智能体 ID 格式，需要 UUID 格式",
  "status_code": 400
}
```

**原因：**
- UUID 格式不正确
- 参数类型错误

#### 404 Not Found

```json
{
  "error": "Not Found",
  "detail": "智能体不存在：550e8400-e29b-41d4-a716-446655440000",
  "status_code": 404
}
```

**原因：**
- 资源 ID 不存在

#### 422 Unprocessable Entity

```json
{
  "error": "Unprocessable Entity",
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

**原因：**
- 缺少必填字段
- 字段格式不符合要求

#### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "detail": "服务器内部错误，请稍后重试",
  "status_code": 500
}
```

**原因：**
- 数据库连接失败
- 外部 API 调用失败
- 代码异常

---

## 最佳实践

### 1. 批量创建记忆

```python
# Python 示例
import requests

memories = [
    {"content": "记忆 1", "memory_type": "fact"},
    {"content": "记忆 2", "memory_type": "preference"},
    {"content": "记忆 3", "memory_type": "skill"},
]

for memory in memories:
    requests.post("http://localhost:8000/api/v1/memories", json=memory)
```

### 2. 错误处理

```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误：{e}")
    print(f"详情：{response.json()}")
except requests.exceptions.RequestException as e:
    print(f"请求失败：{e}")
```

### 3. 分页查询

```python
def list_all_memories(agent_id):
    all_memories = []
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"http://localhost:8000/api/v1/agents/{agent_id}/memories",
            params={"limit": limit, "offset": offset}
        )
        memories = response.json()
        
        if not memories:
            break
        
        all_memories.extend(memories)
        offset += limit
    
    return all_memories
```

---

## SDK 示例

### Python SDK

```python
import requests

class MemoryHubClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def create_agent(self, name, description="", capabilities=None):
        response = requests.post(
            f"{self.base_url}/agents",
            json={
                "name": name,
                "description": description,
                "capabilities": capabilities or []
            }
        )
        return response.json()
    
    def create_memory(self, agent_id, content, memory_type="fact", importance=0.5):
        response = requests.post(
            f"{self.base_url}/memories",
            json={
                "agent_id": agent_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance
            }
        )
        return response.json()
    
    def search_memories(self, query, agent_id=None, limit=10):
        response = requests.post(
            f"{self.base_url}/memories/search/text",
            json={
                "query": query,
                "agent_id": agent_id,
                "match_count": limit
            }
        )
        return response.json()
    
    def chat(self, agent_id, session_id, user_message):
        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "agent_id": agent_id,
                "session_id": session_id,
                "user_message": user_message
            }
        )
        return response.json()

# 使用示例
client = MemoryHubClient()

# 创建智能体
agent = client.create_agent("小笔", "文案专家")
print(agent)

# 创建记忆
memory = client.create_memory(agent_id, "用户喜欢简洁的回答")
print(memory)

# 搜索记忆
results = client.search_memories("用户偏好")
print(results)

# 对话
reply = client.chat(agent_id, "session_1", "帮我写个文案")
print(reply)
```

---

*Memory Hub v0.1.0 - 2026.03.09*
