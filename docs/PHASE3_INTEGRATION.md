# Phase 3 集成文档：任务系统与记忆系统集成

> **作者**: 小码 🟡  
> **日期**: 2026-03-16  
> **版本**: v1.3

---

## 📋 概述

Phase 3 将多智能体并行任务系统与记忆系统深度集成，实现任务完成后自动写入记忆，并提供任务记忆的查询和搜索功能。

### 核心功能

1. **自动记忆创建** - 任务完成后自动创建记忆记录
2. **任务记忆查询** - 按任务 ID、项目 ID 查询记忆
3. **向量搜索** - 支持语义搜索任务记忆
4. **统计分析** - 任务记忆的统计信息
5. **文档记忆查询** - 专门查询文档/资源记忆

### ⚠️ 重要架构升级（2026-03-16 憨货决策）

**knowledge 表存文档 + shared_memories 表存引用**

```
┌─────────────────────────────────────────────────────────────────┐
│                     文档存储架构（2026-03-16）                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐                                           │
│  │   任务完成        │                                           │
│  │  (小搜/小码等)    │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ 1. 存入          │────>│ knowledge 表     │                 │
│  │    knowledge 表   │     │ - id             │                 │
│  │                   │     │ - title          │                 │
│  │                   │     │ - content        │                 │
│  │                   │     │ - source         │                 │
│  │                   │     │ - url            │                 │
│  │                   │     │ - embedding      │                 │
│  └────────┬─────────┘     └────────┬─────────┘                 │
│           │                        │                           │
│           │                        │ knowledge_id              │
│           ▼                        ▼                           │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ 2. 创建          │────>│ shared_memories  │                 │
│  │    shared_memory │     │ - id             │                 │
│  │                   │     │ - content        │                 │
│  │                   │     │ - metadata       │                 │
│  │                   │     │   └─knowledge_id │ ← 引用          │
│  └──────────────────┘     └──────────────────┘                 │
│                                                                 │
│  查询流程：                                                      │
│  1. 查 shared_memories 表获取 knowledge_id                       │
│  2. 查 knowledge 表获取文档详情                                   │
│  3. 支持向量语义搜索                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**优势**：
- 结构清晰：文档内容与记忆引用分离
- 知识独立管理：knowledge 表支持专门的向量搜索
- 记忆表轻量：shared_memories 只存引用，不存大文本
- 查询灵活：可以先查记忆再查文档，也可以直接搜索 knowledge 表

### ⚠️ 重要设计决策（2026-03-16 憨货亲定）

**公共记忆数据表只保存文档位置/资源地址**

- **原因**：没有文档的搜索结果价值低，会污染记忆系统
- **规则**：只有 `result_summary` 中包含 `documents`/`urls`/`file_paths` 才会保存
- **类型**：文档记忆统一使用 `fact` 类型（事实型记忆）
- **重要性**：固定为 `0.8`（高优先级）
- **元数据**：必须包含 `url`/`title`/`source` 字段

### ⚠️ 重要设计决策（2026-03-16 更新）

**只持久化小码（team-coder）的任务**

- **原因**：其他智能体（小搜、小写、小审等）都是一次性任务，不需要保存到数据库
- **好处**：避免数据混乱，减少数据库负担
- **配置**：可通过 `PERSISTENCE_ENABLED` 字典调整哪些智能体需要持久化

---

## 🔄 智能体类型与持久化策略

### 智能体映射表

| 智能体名称 | 类型标识 | 持久化 | 执行模式 | 说明 |
|-----------|---------|--------|---------|------|
| 小码 (team-coder) | coder | ✅ 是 | 持久化 | 代码开发任务，需要跟踪进度 |
| 小搜 (team-researcher) | researcher | ❌ 否 | 直接执行 | 一次性搜索任务 |
| 小写 (team-writer) | writer | ❌ 否 | 直接执行 | 一次性写作任务 |
| 小审 (team-reviewer) | reviewer | ❌ 否 | 直接执行 | 一次性审核任务 |
| 小析 (team-analyst) | analyst | ❌ 否 | 直接执行 | 一次性分析任务 |
| 小览 (team-browser) | browser | ❌ 否 | 直接执行 | 一次性浏览器操作 |
| 小图 (team-designer) | designer | ❌ 否 | 直接执行 | 一次性设计任务 |
| 小排 (team-layout) | layout | ❌ 否 | 直接执行 | 一次性排版任务 |

### 配置文件：`sdk/config.py`

```python
# 智能体名称 -> 智能体类型映射
AGENT_TYPES = {
    'team-coder': 'coder',
    'team-researcher': 'researcher',
    'team-writer': 'writer',
    'team-reviewer': 'reviewer',
    'team-analyst': 'analyst',
    'team-browser': 'browser',
    'team-designer': 'designer',
    'team-layout': 'layout',
}

# 任务持久化开关
PERSISTENCE_ENABLED = {
    'coder': True,       # ✅ 小码 - 需要持久化
    'researcher': False, # ❌ 其他智能体 - 不持久化
    'writer': False,
    'reviewer': False,
    'analyst': False,
    'browser': False,
    'designer': False,
    'layout': False,
}
```

### 使用示例

```python
from sdk import TaskService, ShaniuDispatcher, is_persistence_enabled

# 1. 创建任务（只有 coder 类型会保存到数据库）
service = TaskService(db_url)

# 小码任务 - 会保存到数据库
task_id = await service.create_task(
    task_type="code",
    title="修复登录 bug",
    agent_type="coder"  # 关键：指定智能体类型
)
print(task_id)  # 输出: "abc-123-def"

# 小搜任务 - 不会保存到数据库
task_id = await service.create_task(
    task_type="search",
    title="搜索 AI 新闻",
    agent_type="researcher"  # 非 coder 类型
)
print(task_id)  # 输出: None

# 2. 使用派发器
dispatcher = ShaniuDispatcher(task_service=service)

# 派发任务给小码（持久化模式）
result = await dispatcher.dispatch_task(
    agent_name="team-coder",
    task_description="实现用户登录功能"
)
print(result["mode"])  # 输出: "persistent"

# 派发任务给小搜（直接执行模式）
result = await dispatcher.dispatch_task(
    agent_name="team-researcher",
    task_description="搜索 AI 新闻"
)
print(result["mode"])  # 输出: "direct"

# 3. 检查是否需要持久化
is_persistence_enabled("coder")      # True
is_persistence_enabled("researcher") # False
```

---

## 🏗️ 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     多智能体并行任务系统                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    完成任务     ┌──────────────────────┐      │
│  │ TaskService  │ ──────────────> │ TaskMemoryService    │      │
│  │              │                 │                      │      │
│  │ - create     │                 │ - create_task_memory │      │
│  │ - acquire    │                 │ - get_task_memories  │      │
│  │ - complete   │                 │ - search_memories    │      │
│  └──────────────┘                 └──────────────────────┘      │
│         │                                   │                   │
│         │                                   │                   │
│         ▼                                   ▼                   │
│  ┌──────────────┐                 ┌──────────────────────┐      │
│  │ PostgreSQL   │                 │ MemoryService        │      │
│  │              │                 │                      │      │
│  │ parallel_    │                 │ - create_memory      │      │
│  │ tasks        │                 │ - search_similar     │      │
│  │              │                 │ - route_memory       │      │
│  └──────────────┘                 └──────────────────────┘      │
│         │                                   │                   │
│         │                                   │                   │
│         ▼                                   ▼                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL                             │   │
│  │                                                          │   │
│  │  parallel_tasks  │  private_memories  │  shared_memories │   │
│  │  (任务数据)       │  (私人记忆)         │  (共享记忆)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 数据流转说明

### 1. 任务完成 → 记忆创建流程

```
用户请求完成任务
       │
       ▼
┌──────────────────┐
│ TaskService.     │
│ complete_task()  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 1. 更新任务状态   │ ───> PostgreSQL: parallel_tasks
│    为 completed  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. 获取任务详情   │ ───> 提取任务信息
│    计算执行耗时   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. 创建记忆      │ ───> MemoryService.create_memory()
│    - 内容构建    │
│    - 元数据组装  │
│    - 自动路由    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. 生成向量      │ ───> EmbeddingService.get_embedding()
│    (1024维)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. 存储记忆      │ ───> PostgreSQL: private_memories / shared_memories
│    - 更新索引    │
│    - 关联任务    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. 更新任务      │ ───> parallel_tasks.memory_id
│    的 memory_id  │
└──────────────────┘
```

### 2. 记忆内容结构

```python
{
    "content": "【任务完成】搜索 GitHub trending 项目\n描述：搜索当天 GitHub 上 trending 的项目...\n执行者：小搜",
    "memory_type": "fact",  # 根据任务类型自动确定
    "importance": 0.6,      # 根据执行时间动态计算
    "tags": ["search", "任务"],
    "metadata": {
        "task_id": "abc-123-def",
        "task_type": "search",
        "agent_name": "小搜",
        "project_id": "daily-news",
        "duration_seconds": 45.3,
        "created_at": "2026-03-16T13:00:00",
        "result_summary": {
            "repos_found": 10,
            "top_repo": "awesome-project"
        }
    }
}
```

### 3. 任务类型 → 记忆类型映射

| 任务类型 | 记忆类型 | 说明 |
|---------|---------|------|
| search | fact | 搜索结果是客观事实 |
| write | experience | 写作经验是过程性知识 |
| code | skill | 代码开发是技能性知识 |
| review | experience | 审查经验是过程性知识 |
| analyze | fact | 分析结果是客观事实 |
| design | skill | 设计是技能性知识 |
| layout | skill | 排版是技能性知识 |
| custom | experience | 自定义任务默认为经验 |

---

## 🔌 API 使用示例

### 1. 任务完成后自动创建记忆

**SDK 调用**:

```python
from sdk.task_service import TaskService

# 创建服务实例
service = TaskService("postgresql://user:pass@localhost/memory_hub")

# 创建任务
task_id = await service.create_task(
    task_type="search",
    title="搜索 AI 新闻",
    description="搜索最新的 AI 行业新闻",
    agent_id="agent-uuid"
)

# 领取任务
await service.acquire_task(agent_id="agent-uuid")

# 完成任务（自动创建记忆）
result = await service.complete_task(
    task_id=task_id,
    result_summary={
        "news_count": 5,
        "top_news": "OpenAI 发布新模型"
    },
    create_memory=True,           # 默认为 True
    memory_visibility="shared"    # 可选：指定可见性
)

print(f"任务完成，记忆 ID: {result['memory_id']}")
```

### 2. 查询任务记忆

**API 请求**:

```bash
# 获取任务的所有记忆
curl "http://localhost:8000/api/v1/tasks/{task_id}/memories?limit=10"

# 响应
{
    "memories": [
        {
            "id": "memory-uuid",
            "content": "【任务完成】搜索 AI 新闻...",
            "memory_type": "fact",
            "importance": 0.6,
            "visibility": "shared",
            "task_type": "search",
            "created_at": "2026-03-16T13:00:00"
        }
    ],
    "total": 1,
    "task_id": "task-uuid"
}
```

### 3. 查询项目记忆

**API 请求**:

```bash
# 获取项目的所有记忆
curl "http://localhost:8000/api/v1/projects/daily-news/memories?limit=50&offset=0"

# 响应
{
    "memories": [...],
    "total": 25,
    "project_id": "daily-news"
}
```

### 4. 搜索任务记忆

**API 请求**:

```bash
# 搜索任务记忆（向量搜索）
curl "http://localhost:8000/api/v1/memories/search?q=AI新闻&limit=10"

# 响应
{
    "results": [
        {
            "id": "memory-uuid",
            "content": "【任务完成】搜索 AI 新闻...",
            "similarity": 0.8923,
            "visibility": "shared"
        }
    ],
    "query": "AI新闻",
    "total": 5
}
```

### 5. 获取智能体任务记忆

**API 请求**:

```bash
# 获取智能体的所有任务记忆
curl "http://localhost:8000/api/v1/agents/{agent_id}/task-memories?task_type=search&limit=20"
```

### 6. 获取任务记忆统计

**API 请求**:

```bash
# 获取统计信息
curl "http://localhost:8000/api/v1/task-memories/statistics?project_id=daily-news"

# 响应
{
    "total_memories": 50,
    "by_task_type": {
        "search": 20,
        "code": 15,
        "write": 15
    },
    "by_visibility": {
        "private": 10,
        "shared": 40
    },
    "avg_importance": 0.62
}
```

### 7. 查询文档记忆（新增，2026-03-16）

**⚠️ 憨货决策**：公共记忆数据表只保存文档/资源地址，没有文档的搜索结果不保存。

**API 请求**:

```bash
# 查询所有文档记忆
curl "http://localhost:8000/api/v1/memories/documents?limit=20"

# 按关键词搜索文档
curl "http://localhost:8000/api/v1/memories/documents?query=API文档&limit=10"

# 按项目过滤
curl "http://localhost:8000/api/v1/memories/documents?project_id=daily-news&limit=20"

# 按来源过滤（小搜、小码等）
curl "http://localhost:8000/api/v1/memories/documents?source=小搜&limit=20"

# 响应
{
    "documents": [
        {
            "title": "OpenAI API 文档",
            "url": "https://platform.openai.com/docs",
            "source": "小搜",
            "description": "OpenAI 官方 API 文档",
            "created_at": "2026-03-16T13:00:00",
            "task_id": "task-uuid",
            "project_id": "daily-news"
        },
        {
            "title": "GitHub Trending",
            "url": "https://github.com/trending",
            "source": "小搜",
            "description": "",
            "created_at": "2026-03-16T12:00:00",
            "task_id": null,
            "project_id": null
        }
    ],
    "total": 2,
    "query": null
}
```

**使用场景**：
- 快速查找之前搜索过的文档
- 按项目聚合所有相关文档
- 按来源查看小搜/小码找到的资源

### 8. 知识库 API（2026-03-16 新增）

**⚠️ 架构升级**：knowledge 表存文档 + shared_memories 表存引用

**查询知识详情**：

```bash
# 根据 ID 查询知识详情
curl "http://localhost:8000/api/v1/knowledge/{knowledge_id}"

# 响应
{
    "id": "knowledge-uuid",
    "title": "OpenAI API 文档",
    "content": "OpenAI 官方 API 文档...",
    "category": "documentation",
    "tags": ["search", "文档"],
    "source": "小搜",
    "importance": 0.5,
    "metadata": {
        "url": "https://platform.openai.com/docs",
        "task_id": "task-uuid",
        "project_id": "daily-news"
    },
    "created_at": "2026-03-16T13:00:00"
}
```

**搜索知识（向量语义搜索）**：

```bash
# POST 请求（原有方式）
curl -X POST "http://localhost:8000/api/v1/knowledge/search/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "API 文档", "match_count": 5}'

# GET 请求（新增，更符合 REST 风格）
curl "http://localhost:8000/api/v1/knowledge/search?query=API文档&source=小搜&limit=10"

# 响应
[
    {
        "id": "knowledge-uuid",
        "title": "OpenAI API 文档",
        "content": "OpenAI 官方 API 文档...",
        "category": "documentation",
        "source": "小搜",
        "similarity": 0.89
    }
]
```

**列出知识（按来源）**：

```bash
# 列出小搜找到的所有知识
curl "http://localhost:8000/api/v1/knowledge?source=小搜&limit=50"

# 列出所有知识
curl "http://localhost:8000/api/v1/knowledge?limit=50"
```

**知识统计**：

```bash
# 获取知识库统计信息
curl "http://localhost:8000/api/v1/knowledge/statistics"

# 按来源过滤
curl "http://localhost:8000/api/v1/knowledge/statistics?source=小搜"

# 响应
{
    "total": 100,
    "categories": 5,
    "sources": 3,
    "source_filter": "小搜"
}
```

---

## 📄 文档记忆格式说明

### 记忆内容结构

文档记忆的内容格式：

```
【文档记忆】搜索 AI 新闻
描述：搜索最新的 AI 行业新闻...

文档 (3 个):
  1. OpenAI API 文档
     https://platform.openai.com/docs
  2. Anthropic Claude
     https://anthropic.com
  3. Google Gemini
     https://ai.google.dev

资源链接 (5 个):
  1. https://example.com/doc1
  2. https://example.com/doc2
  ...

执行者：小搜
```

### 记忆元数据结构

```json
{
    "task_id": "abc-123-def",
    "task_type": "search",
    "agent_name": "小搜",
    "project_id": "daily-news",
    "duration_seconds": 45.3,
    "created_at": "2026-03-16T13:00:00",
    
    "documents": [
        {
            "title": "OpenAI API 文档",
            "url": "https://platform.openai.com/docs",
            "description": "..."
        }
    ],
    "urls": ["https://example.com/doc1", "https://example.com/doc2"],
    "file_paths": ["/path/to/file.pdf"],
    
    "source": "小搜",
    "memory_category": "document"
}
```

### 必须包含的字段

| 字段 | 说明 | 必需 |
|------|------|------|
| `documents` | 文档列表，每个包含 `title`/`url`/`description` | 二选一 |
| `urls` | URL 列表 | 二选一 |
| `file_paths` | 文件路径列表 | 二选一 |
| `source` | 来源（小搜/小码等） | ✅ |
| `memory_category` | 固定为 `document` | ✅ |

### 记忆类型和重要性

- **记忆类型**：统一使用 `fact`（事实型记忆）
- **重要性**：固定为 `0.8`（高优先级）
- **标签**：`[task_type, "任务", "文档"]`

---

## ⚙️ 配置说明

### 环境变量

```bash
# 数据库连接
DATABASE_URL=postgresql://memory_user:memory_pass_2026@localhost:5432/memory_hub

# 记忆系统 API 地址（SDK 使用）
MEMORY_API_URL=http://localhost:8000/api/v1

# 向量维度（默认 1024，使用 text-embedding-v4）
EMBEDDING_DIMENSION=1024
```

### 配置文件

**`sdk/config.py`**:

```python
@dataclass
class Settings:
    # 数据库配置
    DATABASE_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    
    # 记忆系统配置
    MEMORY_API_URL: str = "http://localhost:8000/api/v1"
    
    # 任务默认配置
    DEFAULT_LOCK_DURATION: int = 30  # 分钟
    DEFAULT_TIMEOUT: int = 30  # 分钟
```

---

## 📁 文件结构

```
memory-hub/
├── sdk/
│   ├── task_service.py          # 任务服务 SDK（已修改）
│   └── config.py                # 配置管理（已修改）
│
├── backend/
│   └── app/
│       ├── api/
│       │   └── task_memories.py # 任务记忆 API（新增）
│       │
│       ├── services/
│       │   └── task_memory_service.py  # 任务记忆服务（新增）
│       │
│       └── main.py              # 主程序（已修改）
│
├── tests/
│   └── test_task_memory_integration.py  # 集成测试（新增）
│
└── docs/
    └── PHASE3_INTEGRATION.md    # 本文档（新增）
```

---

## 🧪 测试

### 运行集成测试

```bash
# 方式 1：使用 pytest
pytest tests/test_task_memory_integration.py -v

# 方式 2：直接运行
python -m tests.test_task_memory_integration
```

### 测试场景

1. **test_complete_task_creates_memory**
   - 创建任务 → 领取 → 完成 → 验证记忆创建

2. **test_get_task_memories**
   - 查询特定任务的记忆

3. **test_search_task_memories**
   - 搜索任务记忆（向量搜索）

4. **test_project_memories**
   - 按项目查询记忆

---

## 🔧 故障排查

### 问题 1：记忆没有被创建

**症状**: 任务完成但 `memory_id` 为 `None`，且没有错误

**可能原因**: 憨货决策（2026-03-16）只保存有文档/资源的记忆

**排查步骤**:
1. 检查 `result_summary` 是否包含 `documents`/`urls`/`file_paths`
2. 查看日志是否有 "没有文档/资源地址，不保存到记忆系统" 的提示
3. 如果确实需要保存，在 `result_summary` 中添加文档信息

```python
# 正确的结果摘要格式
result_summary = {
    "documents": [
        {
            "title": "API 文档",
            "url": "https://example.com/docs",
            "description": "..."
        }
    ],
    "urls": ["https://example.com/resource"],
    # ... 其他字段
}
```

### 问题 2：记忆创建失败

**症状**: 任务完成但 `memory_id` 为 `None`，有错误信息

**排查步骤**:
1. 检查记忆系统是否启动
2. 检查 `MEMORY_API_URL` 配置
3. 查看日志中的错误信息

```bash
# 检查记忆系统状态
curl http://localhost:8000/api/v1/health

# 查看日志
docker logs memory-hub-backend
```

### 问题 3：向量搜索无结果

**症状**: 搜索返回空列表

**排查步骤**:
1. 检查 embedding 服务是否正常
2. 确认记忆已有向量（检查 `embedding` 字段）
3. 调整 `match_threshold` 参数

### 问题 4：数据库连接失败

**症状**: `asyncpg.exceptions.PostgresConnectionError`

**排查步骤**:
1. 检查数据库是否运行
2. 验证连接字符串格式
3. 检查网络连接

---

## 📈 性能优化建议

### 1. 批量创建记忆

对于批量任务，建议使用异步并发：

```python
import asyncio

async def complete_tasks_batch(task_ids, service):
    tasks = [
        service.complete_task(task_id, create_memory=True)
        for task_id in task_ids
    ]
    return await asyncio.gather(*tasks)
```

### 2. 缓存常用查询

使用 Redis 缓存热门任务记忆：

```python
# 伪代码
async def get_task_memories_cached(task_id):
    cached = await redis.get(f"task_memories:{task_id}")
    if cached:
        return cached
    
    memories = await task_memory_service.get_task_memories(task_id)
    await redis.set(f"task_memories:{task_id}", memories, ex=3600)
    return memories
```

### 3. 定期清理

设置定期清理任务，删除过期的低重要性记忆：

```sql
-- 清理 30 天前的低重要性记忆
DELETE FROM shared_memories
WHERE created_at < NOW() - INTERVAL '30 days'
  AND importance < 0.3
  AND access_count < 3;
```

---

## 🚀 后续计划

### Phase 4: 高级功能

1. **记忆关联** - 自动关联相关任务记忆
2. **知识图谱** - 构建任务知识图谱
3. **智能推荐** - 基于历史记忆推荐任务执行策略

### Phase 5: 多智能体协作

1. **记忆共享** - 智能体间共享任务经验
2. **协同学习** - 多智能体协同学习
3. **冲突检测** - 检测和解决记忆冲突

---

## 📝 更新日志

### v1.4 (2026-03-16)

- ✅ **架构升级**：小搜搜索结果先保存为 .md 文件，再存入 knowledge 表
- ✅ 创建 `DocumentStorageService` 服务类 (`backend/app/services/document_storage_service.py`)
  - 保存文档为 .md 文件
  - 支持读取、删除、列出文档
  - 文件命名格式：`YYYYMMDD_HHMMSS_标题.md`
- ✅ 创建 `SearchIntegrationService` 服务类 (`backend/app/services/search_integration_service.py`)
  - 集成搜索结果处理流程
  - 抓取文档内容 → 保存 .md 文件 → 存入 knowledge 表
- ✅ 添加文档文件 API (`backend/app/api/routes_knowledge.py`)
  - `GET /api/v1/knowledge/{id}/file` - 读取知识文档文件
  - `GET /api/v1/documents` - 列出所有文档文件
  - `GET /api/v1/documents/{filename}` - 读取指定文档文件
- ✅ 创建搜索 API (`backend/app/api/routes_search.py`)
  - `POST /api/v1/search` - 执行搜索并自动保存结果
  - `GET /api/v1/search` - 同上（GET 请求版本）
- ✅ 文档存储位置：`/home/wen/projects/memory-hub/documents/`
- ✅ knowledge 表 metadata 记录 file_path，可追溯原文

#### 文档保存流程

```
小搜搜索
    │
    ▼
┌──────────────────┐
│ 1. DuckDuckGo    │
│    搜索          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. 抓取文档内容   │
│    (httpx)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────────────────┐
│ 3. 保存为        │────>│ /home/wen/projects/memory-hub │
│    .md 文件       │     │ /documents/                  │
└────────┬─────────┘     │ 20260316_144000_标题.md      │
         │               └──────────────────────────────┘
         ▼
┌──────────────────┐
│ 4. 读取 .md 文件 │
│    内容          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. 存入          │────> knowledge 表
│    knowledge 表   │      - content = 文件内容
└────────┬─────────┘      - metadata.file_path = 文件路径
         │
         ▼
┌──────────────────┐
│ 6. 创建          │────> shared_memories 表（可选）
│    shared_memory │      引用 knowledge_id
└──────────────────┘
```

#### .md 文件格式

```markdown
# 文档标题

**来源**: 小搜
**URL**: https://example.com/article
**时间**: 2026-03-16T14:40:00

---

正文内容...
```

#### 文件命名规则

| 组成部分 | 格式 | 示例 |
|---------|------|------|
| 时间戳 | YYYYMMDD_HHMMSS | 20260316_144000 |
| 标题 | 清理后的标题（最多 50 字符） | Python教程 |
| 扩展名 | .md | .md |

**非法字符处理**：
- `< > : " / \ | ? *` → 替换为 `_`
- 空格 → 替换为 `_`
- 连续下划线 → 合并为单个

#### API 使用示例

**执行搜索并保存结果**：

```bash
# POST 请求
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python教程", "max_results": 5}'

# GET 请求
curl "http://localhost:8000/api/v1/search?query=Python教程&max_results=5"

# 响应
{
  "query": "Python教程",
  "total": 5,
  "success_count": 5,
  "failed_count": 0,
  "results": [
    {
      "title": "Python教程 - 菜鸟教程",
      "url": "https://www.runoob.com/python",
      "snippet": "...",
      "knowledge_id": "uuid-xxx",
      "file_path": "/home/wen/projects/memory-hub/documents/20260316_144000_Python教程.md",
      "status": "success"
    }
  ]
}
```

**读取文档文件**：

```bash
# 通过 knowledge ID 读取
curl "http://localhost:8000/api/v1/knowledge/{knowledge_id}/file"

# 通过文件名读取
curl "http://localhost:8000/api/v1/documents/20260316_144000_Python教程.md"

# 列出所有文档
curl "http://localhost:8000/api/v1/documents?limit=50"
```

### v1.3 (2026-03-16)

- ✅ **架构升级**：knowledge 表存文档 + shared_memories 表存引用
- ✅ 创建 `KnowledgeService` 服务类 (`backend/app/services/knowledge_service.py`)
- ✅ 修改 `TaskMemoryService.create_task_memory()` 使用新架构
  - 文档内容存入 knowledge 表
  - shared_memories 表只存引用（knowledge_id）
- ✅ 更新 `task_memories.py` API 文档查询逻辑
  - 先查 shared_memories 表
  - 从 metadata 提取 knowledge_id
  - 再查 knowledge 表获取文档详情
- ✅ 更新 `routes_knowledge.py` 知识查询 API
  - `GET /api/v1/knowledge/search` - 向量搜索（GET 请求）
  - `GET /api/v1/knowledge?source=小搜` - 按来源列出
  - `GET /api/v1/knowledge/statistics` - 知识统计
- ✅ 支持向量语义搜索 knowledge 表
- ✅ 更新文档说明新架构和数据流向

### v1.2 (2026-03-16)

- ✅ **核心修改**：公共记忆数据表只保存文档/资源地址
- ✅ 修改 `TaskMemoryService.create_task_memory()` 只保存有文档的记忆
- ✅ 修改 `TaskService._create_task_memory()` 同样的逻辑
- ✅ 添加 `GET /api/v1/memories/documents` 文档记忆查询接口
- ✅ 文档记忆统一使用 `fact` 类型，重要性固定为 `0.8`
- ✅ 元数据必须包含 `url`/`title`/`source` 字段
- ✅ 更新文档说明设计决策和使用方法

### v1.1 (2026-03-16)

- ✅ **核心修改**：只持久化小码（team-coder）的任务
- ✅ 修改 `TaskService.create_task()` 添加 `agent_type` 参数
- ✅ 修改 `AgentWorker` 支持非持久化模式
- ✅ 创建 `sdk/config.py` 智能体类型配置
- ✅ 创建 `sdk/shaniu_dispatcher.py` 傻妞任务派发器
- ✅ 添加 `execute_direct()` 方法用于直接执行任务
- ✅ 更新文档说明设计决策

### v1.0 (2026-03-16)

- ✅ 实现 `complete_task()` 自动创建记忆
- ✅ 创建 `TaskMemoryService` 服务类
- ✅ 创建任务记忆 API 路由
- ✅ 编写集成测试
- ✅ 编写集成文档

---

## 👥 贡献者

- **小码 🟡** - 代码开发和系统集成

---

*本文档由小码 🟡 编写，属于多智能体并行任务系统 Phase 3 集成项目。*