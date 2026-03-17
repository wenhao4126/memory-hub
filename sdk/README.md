# 多智能体并行任务系统 - Python SDK

> 作者：小码 🟡 | 日期：2026-03-16

---

## 📋 目录

1. [安装说明](#安装说明)
2. [快速开始](#快速开始)
3. [API 文档](#api-文档)
4. [示例代码](#示例代码)
5. [最佳实践](#最佳实践)

---

## 安装说明

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+
- 已创建数据库表（参考 `database/01_parallel_tasks_schema.sql`）

### 2. 安装依赖

```bash
cd /home/wen/projects/memory-hub
pip install -r sdk/requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

关键配置：

```bash
# 数据库连接（推荐方式）
DATABASE_URL=postgresql://memory_user:memory_pass_2026@localhost:5432/memory_hub

# 或者分别配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=memory_hub
DB_USER=memory_user
DB_PASSWORD=memory_pass_2026
```

---

## 快速开始

### 创建任务服务

```python
from sdk.task_service import TaskService

# 创建服务实例（自动从环境变量读取数据库连接）
service = TaskService()

# 或者手动指定连接字符串
service = TaskService("postgresql://user:pass@host:port/db")
```

### 创建任务

```python
task_id = await service.create_task(
    task_type="code",
    title="开发用户登录功能",
    description="实现用户登录、注册、登出功能",
    priority="high",
    params={
        "language": "python",
        "framework": "fastapi"
    }
)
print(f"任务创建成功: {task_id}")
```

### 领取任务

```python
task = await service.acquire_task(
    agent_id="your-agent-uuid",
    task_types=["code"]  # 可选：只领取特定类型的任务
)

if task:
    print(f"领取任务: {task['title']}")
```

### 更新进度

```python
await service.update_progress(
    task_id=task_id,
    progress_percent=50,
    status_message="正在编写代码..."
)
```

### 完成任务

```python
await service.complete_task(
    task_id=task_id,
    result_summary={
        "status": "success",
        "files_changed": 5,
        "lines_added": 200
    }
)
```

### 标记失败

```python
retried = await service.fail_task(
    task_id=task_id,
    error_message="连接超时",
    retry=True  # 允许重试
)
```

---

## API 文档

### TaskService 类

#### 初始化

```python
TaskService(db_url: str = None)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| db_url | str | 数据库连接字符串（可选，默认从环境变量读取） |

#### 方法列表

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `create_task()` | 创建新任务 | task_id (str) |
| `acquire_task()` | 领取待执行任务 | task (dict) 或 None |
| `update_progress()` | 更新任务进度 | bool |
| `complete_task()` | 完成任务 | bool |
| `fail_task()` | 标记任务失败 | bool (True=已重试) |
| `get_task()` | 查询任务详情 | task (dict) 或 None |
| `list_tasks()` | 列出任务 | List[dict] |
| `get_task_statistics()` | 获取统计信息 | dict |
| `cleanup_expired_locks()` | 清理过期锁 | int |
| `close()` | 关闭连接池 | None |

#### create_task() 参数

```python
async def create_task(
    task_type: str,          # 任务类型（必填）
    title: str,              # 任务标题（必填）
    description: str = None, # 任务描述
    priority: str = "normal",# 优先级：low/normal/high/urgent
    params: dict = None,     # 任务参数
    agent_id: str = None,    # 指定执行智能体
    parent_task_id: str = None, # 父任务ID
    timeout_minutes: int = 30,  # 超时时间
    max_retries: int = 3     # 最大重试次数
) -> str
```

#### acquire_task() 返回值

```python
{
    "task_id": "uuid-string",
    "task_type": "code",
    "title": "任务标题",
    "description": "任务描述",
    "params": {"key": "value"},
    "priority": "normal",
    "timeout_minutes": 30
}
```

---

### AgentWorker 类

#### 初始化

```python
AgentWorker(
    agent_id: str,           # 智能体ID
    agent_type: str,         # 智能体类型
    task_service: TaskService, # TaskService实例
    supported_types: List[str] = None  # 支持的任务类型
)
```

#### 核心方法

| 方法 | 说明 | 是否必须实现 |
|------|------|-------------|
| `start()` | 启动工作循环 | 调用 |
| `stop()` | 停止工作器 | 调用 |
| `_process_task()` | 处理任务 | **必须实现** |
| `_on_task_complete()` | 任务完成回调 | 可选 |
| `_on_task_error()` | 任务失败回调 | 可选 |
| `update_progress()` | 更新进度 | 使用 |

#### 自定义 Worker 示例

```python
from worker.agent_worker import AgentWorker

class MyWorker(AgentWorker):
    async def _process_task(self, task: dict) -> dict:
        # 更新进度
        await self.update_progress(50, "处理中...")
        
        # 执行任务逻辑
        result = await do_something(task)
        
        # 返回结果
        return result
```

---

### WorkerPool 类

#### 方法

| 方法 | 说明 |
|------|------|
| `register_worker(worker)` | 注册工作器 |
| `start_all(poll_interval=5)` | 启动所有工作器 |
| `stop_all()` | 停止所有工作器 |
| `get_status()` | 获取工作池状态 |

#### 使用示例

```python
from worker.agent_worker import WorkerPool

pool = WorkerPool()
pool.register_worker(worker1)
pool.register_worker(worker2)

await pool.start_all(poll_interval=5)
# ... 运行中 ...
await pool.stop_all()
```

---

## 示例代码

### 示例 1：基础用法

```bash
python examples/01_basic_usage.py
```

演示内容：
- 创建任务服务
- 创建/查询/更新/完成任务
- 获取统计信息

### 示例 2：自定义 Worker

```bash
python examples/02_custom_worker.py
```

演示内容：
- 继承 AgentWorker 创建自定义工作器
- 实现任务处理逻辑
- 进度更新回调

### 示例 3：多 Worker 并发

```bash
python examples/03_concurrent_workers.py
```

演示内容：
- 创建多个 Worker
- 使用 WorkerPool 管理并发
- 不同类型 Worker 协作

---

## 最佳实践

### 1. 错误处理

```python
try:
    result = await service.complete_task(task_id, result)
except Exception as e:
    logger.error(f"完成任务失败: {e}")
    await service.fail_task(task_id, str(e), retry=True)
```

### 2. 资源管理

```python
# 使用上下文管理器或 try-finally
service = TaskService()
try:
    # 使用服务
    await service.create_task(...)
finally:
    await service.close()
```

### 3. 并发控制

- Worker 数量建议：CPU 核心数 × 2
- 轮询间隔建议：5-10 秒
- 连接池大小建议：Worker 数量 + 5

### 4. 任务分解

复杂任务应该分解为子任务：

```python
# 创建父任务
parent_id = await service.create_task(
    task_type="code",
    title="开发用户系统",
    priority="high"
)

# 创建子任务
for feature in ["登录", "注册", "登出"]:
    await service.create_task(
        task_type="code",
        title=f"实现{feature}功能",
        parent_task_id=parent_id
    )
```

### 5. 超时处理

```python
# 设置合理的超时时间
await service.create_task(
    task_type="search",
    title="批量搜索任务",
    timeout_minutes=60  # 1小时
)
```

---

## 故障排除

### 问题 1：连接数据库失败

```
检查项：
1. 数据库是否启动：docker ps
2. 连接信息是否正确
3. 防火墙是否开放端口
```

### 问题 2：领取任务失败

```
检查项：
1. agents 表中是否存在对应的智能体记录
2. 是否有 pending 状态的任务
3. 任务是否已被锁定
```

### 问题 3：任务一直 pending

```
检查项：
1. 是否有对应类型的 Worker 在运行
2. 锁是否过期（运行 cleanup_expired_locks）
3. 查看日志确认具体原因
```

---

## 文件结构

```
memory-hub/
├── sdk/
│   ├── __init__.py
│   ├── task_service.py    # 任务服务 SDK
│   ├── config.py          # 配置管理
│   ├── requirements.txt   # Python 依赖
│   └── README.md          # 本文档
├── worker/
│   ├── __init__.py
│   └── agent_worker.py    # Agent Worker 基类
├── examples/
│   ├── 01_basic_usage.py       # 基础用法
│   ├── 02_custom_worker.py     # 自定义 Worker
│   └── 03_concurrent_workers.py # 多 Worker 并发
├── database/
│   ├── 01_parallel_tasks_schema.sql   # 数据表定义
│   └── 02_parallel_tasks_functions.sql # 数据库函数
└── .env.example          # 环境变量模板
```

---

## 更新日志

### v1.0.0 (2026-03-16)

- ✅ 实现 TaskService SDK
- ✅ 实现 AgentWorker 基类
- ✅ 实现 WorkerPool 管理器
- ✅ 添加 3 个示例代码
- ✅ 添加详细文档

---

> 如有问题，请联系小码 🟡