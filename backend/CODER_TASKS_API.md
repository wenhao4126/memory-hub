# 小码任务 API 文档

## 概述

小码任务 API 提供对小码智能体任务的管理功能，支持任务查询、创建和状态跟踪。

**基础 URL**: `http://localhost:8000/api/v1`

**认证**: 所有请求需要在请求头中提供 API Key
```
X-API-Key: your_api_key_here
```

---

## API 端点

### 1. GET /coder-tasks - 查询任务列表

查询小码任务列表，支持多种过滤条件。

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| coder_id | string | 否 | - | 按小码 ID 过滤 |
| coder_name | string | 否 | - | 按小码名称过滤（如：小码 1 号） |
| status | string | 否 | - | 按状态过滤（pending/running/completed/failed） |
| limit | integer | 否 | 50 | 返回数量限制（1-500） |
| offset | integer | 否 | 0 | 偏移量 |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/coder-tasks?coder_name=小码 1 号&status=completed&limit=20" \
  -H "X-API-Key: your_api_key"
```

#### 响应示例

```json
{
  "total": 10,
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "task_id": "task_001",
      "coder_id": "550e8400-e29b-41d4-a716-446655440001",
      "coder_name": "小码 1 号",
      "task_type": "code",
      "title": "实现 API 路由",
      "description": "测试任务描述",
      "project_path": "/home/wen/projects/memory-hub/backend",
      "status": "completed",
      "priority": "高",
      "progress": 100,
      "progress_message": null,
      "result": "成功创建 coder_tasks API 路由",
      "error_message": null,
      "start_time": "2026-03-24T10:00:00Z",
      "complete_time": "2026-03-24T10:03:00Z",
      "duration_seconds": 180,
      "memory_id": null,
      "created_at": "2026-03-24T10:00:00Z",
      "updated_at": "2026-03-24T10:03:00Z"
    }
  ]
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total | integer | 总记录数 |
| tasks | array | 任务列表 |
| tasks[].id | string | 任务 UUID |
| tasks[].task_id | string | 飞书任务 ID（可选） |
| tasks[].coder_id | string | 小码智能体 ID |
| tasks[].coder_name | string | 小码名称 |
| tasks[].task_type | string | 任务类型（search/write/code/review/analyze） |
| tasks[].title | string | 任务标题 |
| tasks[].status | string | 任务状态 |
| tasks[].duration_seconds | integer | 任务耗时（秒） |
| tasks[].created_at | string | 创建时间 |
| tasks[].complete_time | string | 完成时间 |

---

### 2. POST /coder-tasks - 创建任务记录

创建或完成小码任务记录。

#### 请求体

```json
{
  "coder_id": "550e8400-e29b-41d4-a716-446655440001",
  "coder_name": "小码 1 号",
  "task_id": "task_001",
  "task_type": "code",
  "title": "任务标题",
  "project_path": "/项目路径",
  "status": "completed",
  "result": "任务完成结果",
  "duration_seconds": 180,
  "description": "任务描述",
  "priority": "高"
}
```

#### 请求字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| coder_id | string | 是 | - | 小码智能体 ID（UUID 格式） |
| coder_name | string | 是 | - | 小码名称（小码 1 号/小码 2 号/小码 3 号） |
| task_id | string | 否 | - | 飞书任务 ID |
| task_type | string | 否 | - | 任务类型（search/write/code/review/analyze） |
| title | string | 是 | - | 任务标题 |
| project_path | string | 否 | - | 项目路径 |
| status | string | 否 | completed | 任务状态（pending/running/completed/failed） |
| result | string | 否 | - | 任务完成结果 |
| duration_seconds | integer | 否 | - | 任务耗时（秒） |
| description | string | 否 | - | 任务描述 |
| priority | string | 否 | 中 | 优先级（高/中/低） |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/coder-tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "coder_id": "550e8400-e29b-41d4-a716-446655440001",
    "coder_name": "小码 1 号",
    "task_id": "task_001",
    "task_type": "code",
    "title": "实现 API 路由",
    "project_path": "/home/wen/projects/memory-hub/backend",
    "status": "completed",
    "result": "成功创建 coder_tasks API 路由",
    "duration_seconds": 180
  }'
```

#### 响应示例

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "created",
  "message": "任务记录已创建"
}
```

---

### 3. GET /coder-tasks/{task_id} - 获取任务详情

根据任务 ID 获取详细信息。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 UUID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/coder-tasks/550e8400-e29b-41d4-a716-446655440001" \
  -H "X-API-Key: your_api_key"
```

#### 响应示例

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "task_id": "task_001",
  "coder_id": "550e8400-e29b-41d4-a716-446655440001",
  "coder_name": "小码 1 号",
  "task_type": "code",
  "title": "实现 API 路由",
  "description": "测试任务描述",
  "project_path": "/home/wen/projects/memory-hub/backend",
  "status": "completed",
  "priority": "高",
  "progress": 100,
  "result": "成功创建 coder_tasks API 路由",
  "duration_seconds": 180,
  "created_at": "2026-03-24T10:00:00Z",
  "complete_time": "2026-03-24T10:03:00Z"
}
```

---

## 错误响应

### 400 Bad Request

请求参数错误。

```json
{
  "detail": "请求参数错误：无效的 UUID 格式"
}
```

### 404 Not Found

任务不存在。

```json
{
  "detail": "任务不存在：550e8400-e29b-41d4-a716-446655440001"
}
```

### 500 Internal Server Error

服务器内部错误。

```json
{
  "detail": "查询任务列表失败：数据库连接失败"
}
```

---

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_api_key"

headers = {"X-API-Key": API_KEY}

# 创建任务
create_data = {
    "coder_id": "550e8400-e29b-41d4-a716-446655440001",
    "coder_name": "小码 1 号",
    "task_type": "code",
    "title": "实现新功能",
    "status": "completed",
    "result": "功能已完成",
    "duration_seconds": 300
}

response = requests.post(
    f"{BASE_URL}/coder-tasks",
    json=create_data,
    headers=headers
)
print(response.json())

# 查询任务列表
params = {
    "coder_name": "小码 1 号",
    "status": "completed",
    "limit": 10
}

response = requests.get(
    f"{BASE_URL}/coder-tasks",
    params=params,
    headers=headers
)
print(response.json())
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'your_api_key';

// 创建任务
async function createTask(taskData) {
  const response = await fetch(`${BASE_URL}/coder-tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify(taskData)
  });
  return await response.json();
}

// 查询任务列表
async function getTasks(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/coder-tasks?${params}`, {
    headers: {
      'X-API-Key': API_KEY
    }
  });
  return await response.json();
}

// 使用示例
createTask({
  coder_id: '550e8400-e29b-41d4-a716-446655440001',
  coder_name: '小码 1 号',
  title: '实现新功能',
  status: 'completed',
  result: '功能已完成'
}).then(console.log);

getTasks({ coder_name: '小码 1 号', limit: 10 })
  .then(console.log);
```

---

## Swagger/OpenAPI 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

在 Swagger UI 中可以：
- 查看所有可用端点
- 在线测试 API
- 下载 OpenAPI 规范

---

## 测试

运行测试脚本：

```bash
cd /home/wen/projects/memory-hub/backend

# 设置环境变量（可选）
export API_BASE_URL=http://localhost:8000
export API_KEY=your_api_key

# 运行测试
./test_coder_tasks_api.sh
```

---

## 数据库表结构

`coder_tasks` 表包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | VARCHAR | 飞书任务 ID |
| coder_id | UUID | 小码智能体 ID |
| coder_name | VARCHAR | 小码名称 |
| task_type | VARCHAR | 任务类型 |
| title | VARCHAR | 任务标题 |
| description | TEXT | 任务描述 |
| project_path | VARCHAR | 项目路径 |
| status | VARCHAR | 状态 |
| priority | VARCHAR | 优先级 |
| progress | INTEGER | 进度（0-100） |
| progress_message | TEXT | 进度描述 |
| result | TEXT | 任务结果 |
| error_message | TEXT | 错误信息 |
| start_time | TIMESTAMP | 开始时间 |
| complete_time | TIMESTAMP | 完成时间 |
| duration_seconds | INTEGER | 耗时（秒） |
| memory_id | UUID | 关联记忆 ID |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 更新日志

### v1.0 (2026-03-24)

- ✅ 实现 GET /api/v1/coder-tasks 查询接口
- ✅ 实现 POST /api/v1/coder-tasks 创建接口
- ✅ 实现 GET /api/v1/coder-tasks/{task_id} 详情接口
- ✅ 支持多种过滤条件（coder_id, coder_name, status）
- ✅ 支持分页（limit, offset）
- ✅ 集成 CoderTaskService
- ✅ 添加 API 认证和 CORS 支持
- ✅ 提供测试脚本和文档
