# 傻妞任务派发器使用指南

> **版本**: v1.0  
> **日期**: 2026-03-16  
> **作者**: 傻妞 + 小码

---

## 🎯 核心功能

**傻妞自动拆解任务并创建到数据库**，让小码池自动抢活干！

---

## 📋 工作流程

### 完整流程

```
憨货给任务
        ↓
傻妞拆解任务（拆成子任务）
        ↓
创建任务到 parallel_tasks 表
        ↓
小码池自动轮询（每 30 秒）
        ↓
小码抢到任务 → 执行 → 完成 → 更新数据库
        ↓
傻妞审核结果 → 交付憨货
```

---

## 🔧 使用方法

### 方式 1：自动创建任务（推荐 ✅）

**憨货给任务**：
```
"小码，去开发个用户 API"
```

**傻妞自动处理**：
```python
# 1. 拆解任务
子任务 = [
    "设计 API 接口",
    "实现用户模型",
    "编写单元测试",
    "编写 API 文档"
]

# 2. 创建任务到数据库
from sdk.task_service import TaskService

service = TaskService()

for task in 子任务：
    await service.create_task(
        task_type='code',
        title=task,
        description=f'用户 API 开发 - {task}',
        project_id='user-api',
        priority='normal',
        agent_type='coder'
    )

# 3. 小码池自动抢活
# 等待小码池自动领取并执行
```

---

### 方式 2：手动创建任务

**憨货自己创建任务**：
```python
from sdk.task_service import TaskService
import asyncio

async def create_task():
    service = TaskService()
    
    task_id = await service.create_task(
        task_type='code',
        title='开发用户 API',
        description='实现用户注册、登录、信息修改等功能',
        project_id='user-api',
        priority='high',
        agent_type='coder'
    )
    print(f'任务已创建：{task_id}')

asyncio.run(create_task())
```

---

## 📊 任务表结构

### parallel_tasks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 任务 ID |
| task_type | ENUM | 任务类型（code/search/write/review...） |
| title | VARCHAR(500) | 任务标题 |
| description | TEXT | 任务描述 |
| agent_id | UUID | 执行智能体 ID |
| agent_name | VARCHAR(255) | 智能体名称 |
| status | ENUM | 状态（pending/running/completed...） |
| priority | ENUM | 优先级（low/normal/high/urgent） |
| progress | INTEGER | 进度（0-100） |
| project_id | VARCHAR(100) | 项目 ID |
| created_at | TIMESTAMP | 创建时间 |
| started_at | TIMESTAMP | 开始时间 |
| completed_at | TIMESTAMP | 完成时间 |

---

## 🤖 小码池自动抢活

### 小码池工作原理

```python
# worker/agent_worker.py

class AgentWorker:
    def start(self, poll_interval: int = 30):
        while True:
            # 每 30 秒轮询一次
            task = self.task_service.acquire_task(self.agent_id)
            
            if task:
                # 有任务，执行
                self._process_task(task)
            else:
                # 没任务，等待
                time.sleep(poll_interval)
```

### 查看小码池状态

```bash
# 查看小码池状态
bash /home/wen/projects/memory-hub/scripts/worker-status.sh

# 查看 systemd 服务状态
sudo systemctl status memory-hub-worker-pool

# 查看日志
tail -f /home/wen/projects/memory-hub/logs/worker-*.log
```

---

## 📝 任务拆解示例

### 示例 1：开发用户 API

**憨货**：
```
"小码，去开发个用户 API"
```

**傻妞拆解**：
```
主任务：用户 API 开发
├── 子任务 1：设计 API 接口
├── 子任务 2：实现用户模型
├── 子任务 3：实现注册接口
├── 子任务 4：实现登录接口
├── 子任务 5：实现用户信息修改
├── 子任务 6：编写单元测试
└── 子任务 7：编写 API 文档
```

**创建任务**：
```python
tasks = [
    {"title": "设计 API 接口", "priority": "high"},
    {"title": "实现用户模型", "priority": "high"},
    {"title": "实现注册接口", "priority": "normal"},
    {"title": "实现登录接口", "priority": "normal"},
    {"title": "实现用户信息修改", "priority": "normal"},
    {"title": "编写单元测试", "priority": "normal"},
    {"title": "编写 API 文档", "priority": "low"},
]

for task in tasks:
    await service.create_task(
        task_type='code',
        title=task['title'],
        description='用户 API 开发',
        project_id='user-api',
        priority=task['priority'],
        agent_type='coder'
    )
```

---

### 示例 2：搜索 AI 新闻

**憨货**：
```
"小搜，去搜一下最新的 AI 新闻"
```

**傻妞拆解**：
```
主任务：AI 新闻搜索
├── 子任务 1：搜索 Hacker News AI 板块
├── 子任务 2：搜索 Reddit r/MachineLearning
├── 子任务 3：搜索 Twitter/X AI 话题
├── 子任务 4：整理和总结新闻
└── 子任务 5：保存到知识库
```

**创建任务**：
```python
tasks = [
    {"title": "搜索 Hacker News AI 板块", "type": "search"},
    {"title": "搜索 Reddit r/MachineLearning", "type": "search"},
    {"title": "搜索 Twitter/X AI 话题", "type": "search"},
    {"title": "整理和总结新闻", "type": "write"},
    {"title": "保存到知识库", "type": "write"},
]

for task in tasks:
    await service.create_task(
        task_type=task['type'],
        title=task['title'],
        description='AI 新闻搜索',
        project_id='ai-news',
        priority='normal',
        agent_type='researcher'  # 或 'writer'
    )
```

---

## 🎯 任务派发策略

### 智能体类型映射

| 智能体 | agent_type | 任务类型 |
|--------|-----------|---------|
| 小码 🟡 | coder | code |
| 小搜 🟢 | researcher | search |
| 小写 🟢 | writer | write |
| 小审 🔴 | reviewer | review |
| 小析 🟡 | analyst | analyze |
| 小览 🟡 | browser | browser |
| 小图 🎨 | designer | design |
| 小排 📐 | layout | layout |

---

### 优先级策略

| 优先级 | 说明 | 使用场景 |
|--------|------|---------|
| urgent | 紧急 | 立即处理，插队 |
| high | 高 | 优先处理 |
| normal | 普通 | 默认优先级 |
| low | 低 | 有空再处理 |

---

## 📊 监控任务进度

### 查看任务状态

```bash
# 查看所有任务
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT id, title, status, priority, created_at FROM parallel_tasks ORDER BY created_at DESC LIMIT 10;"

# 查看待处理任务
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT id, title, priority, created_at FROM parallel_tasks WHERE status='pending' ORDER BY priority, created_at;"

# 查看运行中的任务
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT id, title, agent_id, started_at FROM parallel_tasks WHERE status='running';"

# 查看已完成的任务
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT id, title, completed_at FROM parallel_tasks WHERE status='completed' ORDER BY completed_at DESC LIMIT 5;"
```

---

### 查看小码日志

```bash
# 查看所有小码日志
for i in 1 2 3 4 5; do
    echo "=== 小码$i 日志最后 10 行 ==="
    tail -10 /home/wen/projects/memory-hub/logs/worker-$i.log
done
```

---

## 💡 最佳实践

### 1. 任务拆解原则

- ✅ 拆成独立可执行的子任务
- ✅ 每个子任务 5-30 分钟能完成
- ✅ 明确验收标准
- ✅ 设置合理优先级

### 2. 任务命名规范

- ✅ 标题简洁明了（不超过 50 字）
- ✅ 描述详细说明（包含背景、目标、验收标准）
- ✅ 使用中文命名

### 3. 任务监控

- ✅ 定期检查任务状态
- ✅ 超时任务及时处理（5 分钟超时机制）
- ✅ 失败任务重试或重新分配

---

## 🔧 故障排查

### 问题 1：小码池没抢到任务

**检查**：
```bash
# 1. 查看小码池状态
bash /home/wen/projects/memory-hub/scripts/worker-status.sh

# 2. 查看待处理任务
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT COUNT(*) FROM parallel_tasks WHERE status='pending';"

# 3. 查看小码日志
tail -20 /home/wen/projects/memory-hub/logs/worker-1.log
```

**解决**：
- 确保小码池在运行
- 确保任务 agent_type='coder'
- 检查数据库连接

---

### 问题 2：任务一直 pending

**检查**：
```bash
# 查看任务创建时间
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT id, title, created_at FROM parallel_tasks WHERE status='pending' ORDER BY created_at;"
```

**解决**：
- 等待小码池轮询（最多 30 秒）
- 检查小码池是否运行
- 手动重启小码池

---

## 📄 相关文档

- `/home/wen/projects/memory-hub/docs/WORKER_POOL.md` - 小码池使用指南
- `/home/wen/projects/memory-hub/docs/DOCUMENT_NAMING.md` - 文档命名规范
- `/home/wen/projects/memory-hub/tests/FINAL_AUDIT.md` - 最终审核报告

---

_傻妞任务派发器 - 让任务自动流转起来！_
