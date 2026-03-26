# 小码任务数据表 - 使用指南

> **作者**：小码 1 号 🟡  
> **日期**：2026-03-24  
> **版本**：v1.0

---

## 📋 目录

1. [概述](#概述)
2. [数据表结构](#数据表结构)
3. [执行迁移](#执行迁移)
4. [Python SDK 使用](#python-sdk-使用)
5. [SQL 使用示例](#sql-使用示例)
6. [测试](#测试)
7. [常见问题](#常见问题)

---

## 概述

`coder_tasks` 表用于存储各个小码（小码 1 号、小码 2 号、小码 3 号）完成任务的信息，是 Memory Hub 的核心表之一。

### 主要功能

- ✅ 追踪小码的任务执行历史
- ✅ 记录任务进度和状态
- ✅ 统计小码工作效率
- ✅ 关联记忆系统

### 适用场景

- 多智能体任务调度系统
- 任务执行历史追踪
- 工作效率分析
- 任务结果归档

---

## 数据表结构

### coder_tasks 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| task_id | VARCHAR(100) | 任务 ID（来自飞书任务表） |
| coder_id | UUID | 小码智能体 ID |
| coder_name | VARCHAR(50) | 小码名称（小码 1 号/小码 2 号/小码 3 号） |
| task_type | VARCHAR(50) | 任务类型（search/write/code/review/analyze） |
| title | VARCHAR(500) | 任务标题 |
| description | TEXT | 任务描述 |
| project_path | VARCHAR(500) | 项目路径 |
| status | VARCHAR(50) | 状态（pending/running/completed/failed） |
| priority | VARCHAR(20) | 优先级（高/中/低） |
| progress | INTEGER | 进度（0-100） |
| progress_message | TEXT | 进度描述 |
| result | TEXT | 任务结果 |
| error_message | TEXT | 错误信息 |
| start_time | TIMESTAMP | 开始时间 |
| complete_time | TIMESTAMP | 完成时间 |
| duration_seconds | INTEGER | 耗时（秒） |
| memory_id | UUID | 关联的记忆 ID（Memory Hub） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 索引设计

1. `idx_coder_name` - 按小码名称查询
2. `idx_status` - 按状态查询
3. `idx_task_id` - 按任务 ID 查询
4. `idx_created_at` - 按创建时间排序
5. `idx_coder_name_status` - 复合索引（小码 + 状态）
6. `idx_coder_name_created` - 复合索引（小码 + 时间）
7. `idx_status_created` - 复合索引（状态 + 时间）

---

## 执行迁移

### 方法 1：使用 Docker 容器内执行（推荐）

```bash
# 进入项目目录
cd /home/wen/projects/memory-hub

# 执行 SQL 迁移脚本
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

### 方法 2：使用本地 psql 执行

```bash
# 设置环境变量
export PGHOST=localhost
export PGPORT=5433
export PGDATABASE=memory_hub
export PGUSER=memory_user
export PGPASSWORD=admin

# 执行 SQL 文件
psql -f database/03_coder_tasks_table.sql
```

### 方法 3：使用 pgAdmin 执行

1. 打开 pgAdmin
2. 连接到 `memory_hub` 数据库
3. 打开 Query Tool
4. 复制粘贴 `03_coder_tasks_table.sql` 内容并执行

---

## Python SDK 使用

### 导入服务

```python
import asyncio
import sys
sys.path.insert(0, '/home/wen/projects/memory-hub/backend')

from app.database import db
from app.services.coder_task_service import coder_task_service

async def main():
    # 连接数据库
    await db.connect()
    
    # 使用服务
    # ... 你的代码 ...
    
    # 断开连接
    await db.disconnect()

asyncio.run(main())
```

### 创建任务

```python
task = await coder_task_service.create_coder_task(
    title="开发 API 接口",
    coder_id=uuid4(),  # 小码 ID
    coder_name="小码 1 号",
    task_id="feishu_task_001",  # 飞书任务 ID（可选）
    task_type="code",  # search/write/code/review/analyze
    description="实现用户管理 API",
    project_path="/home/wen/projects/memory-hub",
    priority="高"  # 高/中/低
)

print(f"任务 ID: {task['id']}")
print(f"状态：{task['status']}")  # pending
```

### 更新任务状态

```python
# 开始执行任务
task = await coder_task_service.update_coder_task(
    task_id=task_uuid,
    status="running",
    progress=0,
    start_time=datetime.utcnow()
)

# 更新进度
task = await coder_task_service.update_coder_task(
    task_id=task_uuid,
    progress=50,
    progress_message="正在实现功能..."
)
```

### 完成任务

```python
# 成功完成
task = await coder_task_service.complete_coder_task(
    task_id=task_uuid,
    result="成功实现用户管理 API，包含 CRUD 操作"
)

# 失败完成
task = await coder_task_service.complete_coder_task(
    task_id=task_uuid,
    result="",
    error_message="错误：API 连接超时"
)
```

### 查询任务

```python
# 根据 ID 查询
task = await coder_task_service.get_task_by_id(task_uuid)

# 根据小码名称查询
tasks = await coder_task_service.get_tasks_by_coder_name("小码 1 号")

# 根据状态查询
pending_tasks = await coder_task_service.get_tasks_by_status("pending")

# 获取待执行任务（按优先级排序）
pending_tasks = await coder_task_service.get_pending_tasks(
    coder_name="小码 1 号",
    limit=10
)
```

### 获取统计信息

```python
stats = await coder_task_service.get_task_statistics()

print("按状态统计:")
for status, count in stats['by_status'].items():
    print(f"  {status}: {count}")

print("按小码统计:")
for coder, count in stats['by_coder'].items():
    print(f"  {coder}: {count}")

print(f"平均耗时：{stats['avg_duration_seconds']}秒")
print(f"24 小时内任务数：{stats['recent_24h_count']}")
```

---

## SQL 使用示例

### 创建任务

```sql
INSERT INTO coder_tasks (coder_id, coder_name, task_type, title, description, priority)
VALUES 
    ('a1b2c3d4-1111-4000-8000-000000000003'::uuid, '小码 1 号', 'code', 
     '开发 API 接口', '实现用户管理 API', '高');
```

### 更新任务状态

```sql
-- 开始执行
UPDATE coder_tasks 
SET status = 'running', start_time = NOW()
WHERE id = '任务 ID';

-- 更新进度
UPDATE coder_tasks 
SET progress = 50, progress_message = '正在实现功能...'
WHERE id = '任务 ID';
```

### 完成任务

```sql
-- 成功完成
UPDATE coder_tasks 
SET 
    status = 'completed',
    result = '成功实现功能',
    complete_time = NOW(),
    duration_seconds = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER
WHERE id = '任务 ID';

-- 失败完成
UPDATE coder_tasks 
SET 
    status = 'failed',
    error_message = '错误信息',
    complete_time = NOW(),
    duration_seconds = EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER
WHERE id = '任务 ID';
```

### 查询任务

```sql
-- 查询小码 1 号的所有任务
SELECT * FROM coder_tasks 
WHERE coder_name = '小码 1 号'
ORDER BY created_at DESC;

-- 查询待执行任务（按优先级排序）
SELECT * FROM coder_tasks 
WHERE status = 'pending'
ORDER BY 
    CASE priority
        WHEN '高' THEN 1
        WHEN '中' THEN 2
        WHEN '低' THEN 3
        ELSE 4
    END,
    created_at ASC;

-- 查询某小码的待执行任务
SELECT * FROM coder_tasks 
WHERE coder_name = '小码 1 号' AND status = 'pending'
ORDER BY created_at ASC;

-- 统计各小码的任务数
SELECT 
    coder_name,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    AVG(duration_seconds) FILTER (WHERE status = 'completed') as avg_duration
FROM coder_tasks
GROUP BY coder_name;

-- 统计任务状态分布
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM coder_tasks
GROUP BY status;
```

---

## 测试

### SQL 测试

```bash
# 执行 SQL 测试脚本
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/test_coder_tasks.sql
```

### Python 测试

```bash
# 执行 Python 测试脚本
cd /home/wen/projects/memory-hub
python tests/test_coder_task_service.py
```

### 测试覆盖

- ✅ 创建任务
- ✅ 更新任务状态
- ✅ 更新任务进度
- ✅ 完成任务（成功/失败）
- ✅ 查询任务（按 ID/小码/状态）
- ✅ 获取待执行任务
- ✅ 获取统计信息
- ✅ 索引验证
- ✅ 触发器验证（updated_at 自动更新）

---

## 常见问题

### Q1: 报错 `relation "coder_tasks" does not exist`

**原因**：数据表未创建或创建失败。

**解决**：
```bash
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

### Q2: 报错 `update_updated_at_column() function does not exist`

**原因**：触发器函数未创建（该函数在 `01_parallel_tasks_schema.sql` 中定义）。

**解决**：先执行基础迁移脚本：
```bash
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/01_parallel_tasks_schema.sql
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

### Q3: 任务无法被查询到

**可能原因**：
1. 任务已被删除
2. 查询条件不匹配
3. 权限问题

**排查**：
```sql
-- 查看所有任务
SELECT COUNT(*) FROM coder_tasks;

-- 查看特定小码的任务
SELECT * FROM coder_tasks WHERE coder_name = '小码 1 号';

-- 查看最近创建的任务
SELECT * FROM coder_tasks ORDER BY created_at DESC LIMIT 10;
```

### Q4: 如何清空测试数据？

```sql
-- 清空所有测试数据
DELETE FROM coder_tasks WHERE coder_name IN ('小码 1 号', '小码 2 号', '小码 3 号');

-- 或者清空整个表（谨慎使用）
TRUNCATE TABLE coder_tasks CASCADE;
```

### Q5: 如何优化查询性能？

1. **使用索引字段查询**：
   ```sql
   -- ✅ 好的查询（使用索引）
   SELECT * FROM coder_tasks WHERE coder_name = '小码 1 号';
   SELECT * FROM coder_tasks WHERE status = 'pending';
   
   -- ❌ 避免的查询（不使用索引）
   SELECT * FROM coder_tasks WHERE LOWER(coder_name) = '小码 1 号';
   SELECT * FROM coder_tasks WHERE coder_name LIKE '%小码%';
   ```

2. **使用复合索引**：
   ```sql
   -- ✅ 使用复合索引
   SELECT * FROM coder_tasks 
   WHERE coder_name = '小码 1 号' AND status = 'pending';
   ```

3. **限制返回数量**：
   ```sql
   -- ✅ 添加 LIMIT
   SELECT * FROM coder_tasks 
   WHERE coder_name = '小码 1 号' 
   ORDER BY created_at DESC 
   LIMIT 50;
   ```

---

## 下一步

1. ✅ 数据库表创建完成
2. ✅ Python SDK 实现完成
3. ✅ 测试脚本完成
4. ✅ 文档完成
5. 🔄 集成到任务调度系统
6. 🔄 添加 API 路由（`/api/coder-tasks`）
7. 🔄 前端监控面板

---

_小码任务系统使用指南完成！有问题随时找小码。_
