# Memory Hub 架构设计文档 🏗️

> **系统架构、技术选型、核心模块设计**

---

## 📖 目录

1. [系统概览](#系统概览)
2. [技术栈](#技术栈)
3. [架构设计](#架构设计)
4. [数据模型](#数据模型)
5. [核心模块](#核心模块)
6. [API 设计](#api 设计)
7. [部署架构](#部署架构)

---

## 系统概览

### 定位

Memory Hub 是一个**智能体记忆管理系统**，为分布式智能体提供：

- 💾 统一的记忆存储
- 🔍 语义搜索能力
- 🔄 记忆生命周期管理
- 🤝 多智能体协作支持

### 设计目标

| 目标 | 说明 |
|------|------|
| **易用性** | 5 分钟上手，RESTful API 标准接口 |
| **高性能** | 基于 pgvector 的毫秒级向量搜索 |
| **可扩展** | 支持水平扩展，多智能体并发访问 |
| **可靠性** | 数据持久化，自动备份恢复 |
| **智能化** | 自动记忆提取，智能遗忘机制 |

---

## 技术栈

### 后端技术

| 组件 | 技术 | 选型理由 |
|------|------|---------|
| **Web 框架** | FastAPI | 现代高性能，异步支持，自动生成文档 |
| **数据库** | PostgreSQL 16 | 成熟稳定，支持 JSONB 和向量扩展 |
| **向量扩展** | pgvector | 原生支持向量相似度搜索 |
| **ORM** | 原生 SQL + asyncpg | 高性能，精细控制 |
| **数据验证** | Pydantic | 类型安全，自动验证 |
| **嵌入模型** | text-embedding-v4 | 中文优化，1024 维向量 |
| **LLM** | Qwen3.5-Plus | 强大的对话和记忆提取能力 |

### 基础设施

| 组件 | 技术 | 用途 |
|------|------|------|
| **容器化** | Docker | 环境一致性 |
| **编排** | Docker Compose | 多服务管理 |
| **数据库管理** | pgAdmin | 可视化数据库管理 |
| **备份** | pg_dump | 数据库备份恢复 |

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端层                                 │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│   │ Web App │  │ 移动端  │  │ 智能体  │  │ 第三方  │      │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘      │
└────────┼────────────┼────────────┼────────────┼────────────┘
         │            │            │            │
         └────────────┴─────┬──────┴────────────┘
                            │ HTTP/HTTPS
                   ┌────────▼────────┐
                   │   API Gateway   │
                   │   (FastAPI)     │
                   └────────┬────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
┌────────▼────────┐ ┌──────▼───────┐ ┌────────▼────────┐
│  业务逻辑层     │ │  数据访问层  │ │   外部服务      │
│  - Agent 服务   │ │  - asyncpg   │ │  - DashScope    │
│  - Memory 服务  │ │  - pgvector  │ │  - LLM API      │
│  - 对话增强     │ │  - SQL       │ │  - Embedding    │
└─────────────────┘ └──────────────┘ └─────────────────┘
                            │
                   ┌────────▼────────┐
                   │   PostgreSQL    │
                   │   + pgvector    │
                   └─────────────────┘
```

### 分层架构

#### 1️⃣ 表现层（API Layer）

**职责**：HTTP 请求处理、参数验证、响应格式化

**组件**：
- `api/routes.py` - 主路由
- `api/routes_conversations.py` - 对话路由
- `api/routes_knowledge.py` - 知识路由

**特点**：
- RESTful 设计规范
- Swagger UI 自动生成
- 请求参数 Pydantic 验证
- 统一错误处理

#### 2️⃣ 业务逻辑层（Service Layer）

**职责**：核心业务逻辑、数据处理、外部服务调用

**组件**：
- `services/memory_service.py` - 记忆管理服务
- `services/dialogue_enhancement_service.py` - 对话增强服务
- `services/knowledge_service.py` - 知识管理服务

**特点**：
- 无状态设计
- 异步编程
- 事务管理
- 日志记录

#### 3️⃣ 数据访问层（Data Access Layer）

**职责**：数据库连接、SQL 执行、结果映射

**组件**：
- `database.py` - 数据库连接池
- `models/schemas.py` - 数据模型
- 原生 SQL 查询

**特点**：
- 异步数据库驱动（asyncpg）
- 连接池管理
- 参数化查询（防 SQL 注入）

---

## 数据模型

### ER 图

```
┌─────────────────────┐
│       agents        │
├─────────────────────┤
│ PK id (UUID)        │
│    name (VARCHAR)   │
│    description      │
│    capabilities[]   │
│    metadata (JSONB) │
│    created_at       │
│    updated_at       │
└──────────┬──────────┘
           │ 1:N
           │
┌──────────▼──────────┐
│      memories       │
├─────────────────────┤
│ PK id (UUID)        │
│ FK agent_id (UUID)  │
│    content (TEXT)   │
│    embedding (vector)│
│    memory_type      │
│    importance       │
│    access_count     │
│    tags[]           │
│    metadata (JSONB) │
│    created_at       │
│    last_accessed    │
│    expires_at       │
└─────────────────────┘
```

### 核心表结构

#### agents（智能体表）

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capabilities TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明：**
- `id`：UUID 主键，全局唯一
- `name`：智能体名称，1-255 字符
- `description`：描述信息
- `capabilities`：能力标签数组
- `metadata`：扩展元数据（JSON 格式）

#### memories（记忆表）

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1024),
    memory_type VARCHAR(50) DEFAULT 'fact',
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    access_count INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 创建向量索引（加速相似度搜索）
CREATE INDEX memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**字段说明：**
- `embedding`：1024 维向量，使用 text-embedding-v4 生成
- `memory_type`：fact/preference/skill/experience
- `importance`：重要性分数，0-1 之间
- `access_count`：访问次数，用于智能遗忘
- `expires_at`：过期时间，用于自动清理

---

## 核心模块

### 1. 记忆管理服务（Memory Service）

**文件**：`services/memory_service.py`

**职责**：
- 记忆的增删改查
- 向量相似度搜索
- 记忆清理（智能遗忘）

**核心方法：**

```python
class MemoryService:
    async def create_memory(self, memory: MemoryCreate) -> str:
        """创建记忆"""
        
    async def get_memory(self, memory_id: str) -> dict:
        """获取记忆（增加访问计数）"""
        
    async def update_memory(self, memory_id: str, update: MemoryUpdate) -> dict:
        """更新记忆"""
        
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        
    async def search_similar(self, request: MemorySearchRequest) -> List[MemorySearchResult]:
        """向量相似度搜索"""
        
    async def search_by_text(self, request: MemoryTextSearchRequest) -> List[MemorySearchResult]:
        """文本搜索（自动生成向量）"""
        
    async def cleanup_old_memories(self, days_old: int, min_importance: float, max_access_count: int) -> int:
        """清理过期记忆"""
```

### 2. 对话增强服务（Dialogue Enhancement Service）

**文件**：`services/dialogue_enhancement_service.py`

**职责**：
- 基于记忆的智能对话
- 对话历史管理
- 自动记忆提取

**工作流程：**

```
用户消息
    ↓
1. 向量搜索相关记忆
    ↓
2. 获取对话历史
    ↓
3. 调用 LLM 生成回复（融合记忆 + 历史）
    ↓
4. 记录对话到数据库
    ↓
5. 自动提取新记忆（可选）
    ↓
返回增强回复
```

**核心方法：**

```python
class DialogueEnhancementService:
    async def chat_and_remember(
        self,
        agent_id: str,
        session_id: str,
        user_message: str,
        auto_extract: bool = True
    ) -> dict:
        """对话并自动记忆"""
        
    async def _retrieve_memories(self, agent_id: str, query: str) -> List[dict]:
        """检索相关记忆"""
        
    async def _get_conversation_history(self, session_id: str) -> List[dict]:
        """获取对话历史"""
        
    async def _generate_reply(
        self,
        agent_id: str,
        user_message: str,
        memories: List[dict],
        history: List[dict]
    ) -> str:
        """调用 LLM 生成回复"""
        
    async def _extract_memories(
        self,
        agent_id: str,
        conversation: str
    ) -> List[dict]:
        """从对话中提取记忆"""
```

### 3. 嵌入生成服务（Embedding Service）

**文件**：`services/embedding_service.py`

**职责**：
- 调用 DashScope API 生成向量
- 向量维度验证
- 错误处理和重试

**实现：**

```python
class EmbeddingService:
    def __init__(self):
        self.api_key = settings.DASHSCOPE_EMBEDDING_API_KEY
        self.api_url = settings.DASHSCOPE_BASE_URL
        
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        # 调用 DashScope API
        # 返回 1024 维向量
```

---

## API 设计

### RESTful 规范

| 操作 | HTTP 方法 | 路径 | 说明 |
|------|----------|------|------|
| 创建智能体 | POST | /api/v1/agents | 注册新智能体 |
| 获取智能体 | GET | /api/v1/agents/{id} | 获取详情 |
| 列出智能体 | GET | /api/v1/agents | 分页列表 |
| 更新智能体 | PUT | /api/v1/agents/{id} | 部分更新 |
| 删除智能体 | DELETE | /api/v1/agents/{id} | 级联删除记忆 |
| 创建记忆 | POST | /api/v1/memories | 创建新记忆 |
| 搜索记忆 | POST | /api/v1/memories/search/text | 文本搜索 |
| 增强对话 | POST | /api/v1/chat | 核心功能 |

### 响应格式

**成功响应：**

```json
{
  "id": "uuid",
  "name": "智能体名称",
  "description": "描述",
  "capabilities": ["写作", "翻译"],
  "metadata": {},
  "created_at": "2026-03-09T10:00:00Z"
}
```

**错误响应：**

```json
{
  "error": "Not Found",
  "detail": "智能体不存在：xxx",
  "status_code": 404
}
```

**列表响应：**

```json
[
  {
    "id": "uuid",
    "name": "智能体 1"
  },
  {
    "id": "uuid",
    "name": "智能体 2"
  }
]
```

---

## 部署架构

### 开发环境

```
┌─────────────────────┐
│   Docker Compose    │
├─────────────────────┤
│  - PostgreSQL       │
│  - Memory Hub API   │
│  - pgAdmin          │
└─────────────────────┘
```

**特点：**
- 一键启动
- 本地调试
- 热重载

### 生产环境

```
┌─────────────────────────────────────────┐
│           Load Balancer (Nginx)         │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌───▼───┐
│ API 1 │   │  API 2  │   │ API N │
└───┬───┘   └────┬────┘   └───┬───┘
    │            │            │
    └────────────┴────────────┘
                 │
        ┌────────▼────────┐
        │   PostgreSQL    │
        │   (主从复制)     │
        └─────────────────┘
```

**特点：**
- 多实例负载均衡
- 数据库主从复制
- 自动备份
- 监控告警

### 扩容策略

**水平扩容：**

```bash
# 增加 API 实例
docker-compose up -d --scale api=3
```

**垂直扩容：**

```yaml
# 增加资源限制
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 安全设计

### 1. SQL 注入防护

**措施：**
- 参数化查询（不使用字符串拼接）
- 字段名白名单验证
- Pydantic 数据验证

**示例：**

```python
# ✅ 正确：参数化查询
query = "SELECT * FROM agents WHERE id = $1"
row = await db.fetchrow(query, agent_id)

# ❌ 错误：字符串拼接
query = f"SELECT * FROM agents WHERE id = '{agent_id}'"
```

### 2. CORS 配置

**开发环境：**
```python
allow_origins=["*"]
```

**生产环境：**
```python
allow_origins=["https://yourdomain.com"]
```

### 3. 密码强度

**要求：**
- 至少 8 个字符
- 包含大小写字母
- 包含数字
- 包含特殊字符

---

## 性能优化

### 1. 数据库索引

```sql
-- 向量索引（加速相似度搜索）
CREATE INDEX memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops);

-- 外键索引（加速关联查询）
CREATE INDEX memories_agent_id_idx ON memories (agent_id);

-- 复合索引（加速多条件查询）
CREATE INDEX memories_type_importance_idx ON memories (memory_type, importance);
```

### 2. 连接池

```python
# 数据库连接池配置
pool = await asyncpg.create_pool(
    min_size=5,      # 最小连接数
    max_size=20,     # 最大连接数
    command_timeout=60
)
```

### 3. 异步编程

```python
# 所有 I/O 操作使用异步
async def get_memory(memory_id: str):
    row = await db.fetchrow(query, memory_id)  # 异步数据库查询
    return row
```

---

## 监控与日志

### 日志配置

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
```

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| API 响应时间 | P95 < 500ms | > 1s |
| 数据库连接数 | 使用率 < 80% | > 90% |
| 错误率 | < 1% | > 5% |
| 向量搜索延迟 | P95 < 100ms | > 500ms |

---

## 下一步

- 📖 阅读 [API 文档](API.md) 查看所有接口详情
- 💻 开始开发你的应用
- 🚀 部署到生产环境

---

*Memory Hub v0.1.0 - 2026.03.09*
