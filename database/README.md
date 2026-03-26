# Memory Hub - 数据库迁移指南

> **作者**：小码 🟡  
> **日期**：2026-03-16  
> **版本**：v2.0  
> **更新**：2026-03-24 - 添加小码任务数据表

---

## 📋 目录

1. [概述](#概述)
2. [迁移脚本列表](#迁移脚本列表)
3. [前置条件](#前置条件)
4. [执行步骤](#执行步骤)
5. [验证方法](#验证方法)
6. [测试示例](#测试示例)
7. [常见问题](#常见问题)

---

## 概述

本目录包含 Memory Hub 的所有数据库迁移脚本，用于创建和维护多智能体系统的核心数据表。

### 数据表列表

1. **parallel_tasks** - 并行任务主表（多智能体任务调度）
2. **task_locks** - 分布式锁表
3. **task_progress_history** - 任务进度历史表
4. **coder_tasks** - 小码任务表（存储各小码完成任务的信息）⭐ NEW

---

## 迁移脚本列表

按执行顺序排列：

| 序号 | 文件名 | 描述 | 创建日期 |
|------|--------|------|----------|
| 01 | `01_parallel_tasks_schema.sql` | 并行任务系统数据表（3 张表） | 2026-03-16 |
| 02 | `02_parallel_tasks_functions.sql` | 并行任务系统函数（6 个函数） | 2026-03-16 |
| 03 | `03_add_project_id.sql` | 添加项目 ID 字段 | 2026-03-16 |
| 04 | `04_add_file_path_to_knowledge.sql` | 添加文件路径到知识表 | 2026-03-16 |
| 05 | `03_coder_tasks_table.sql` | 小码任务数据表 | 2026-03-24 |

### 执行顺序

```bash
# 基础迁移（按顺序执行）
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/01_parallel_tasks_schema.sql
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/02_parallel_tasks_functions.sql
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_add_project_id.sql
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/04_add_file_path_to_knowledge.sql

# 小码任务系统（新增）
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

---

## 前置条件

### 1. 环境要求

- PostgreSQL 12+ （推荐 14+）
- 已安装 `pgvector` 扩展
- 已存在 `agents` 表（基础表）
- 已存在 `shared_memories` 表（可选，用于归档）

### 2. 数据库连接信息

```
主机: postgres（Docker 内）或 localhost（本地）
端口: 5432
数据库: memory_hub
用户名: memory_user
密码: memory_pass_2026
```

### 3. 确认基础表存在

```sql
-- 检查 agents 表是否存在
SELECT COUNT(*) FROM agents;

-- 预期结果：至少 10 条记录（傻妞 + 8 个手下 + 小测）
```

---

## 执行步骤

### 方法 1：使用 Docker 容器内执行（推荐）

```bash
# 进入项目目录
cd /home/wen/projects/memory-hub

# 方法 A：使用 docker exec 执行 SQL 文件
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/01_parallel_tasks_schema.sql
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/02_parallel_tasks_functions.sql

# 方法 B：进入容器后执行
docker exec -it memory-hub-postgres psql -U memory_user -d memory_hub
\i /path/to/01_parallel_tasks_schema.sql
\i /path/to/02_parallel_tasks_functions.sql
```

### 方法 2：使用本地 psql 执行

```bash
# 设置环境变量
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=memory_hub
export PGUSER=memory_user
export PGPASSWORD=memory_pass_2026

# 执行 SQL 文件
psql -f database/01_parallel_tasks_schema.sql
psql -f database/02_parallel_tasks_functions.sql
```

### 方法 3：使用 pgAdmin 执行

1. 打开 pgAdmin（默认端口 5050）
2. 连接到 `memory_hub` 数据库
3. 打开 Query Tool
4. 复制粘贴 SQL 文件内容并执行

---

## 验证方法

### 1. 验证表结构

```sql
-- 查看创建的表
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('parallel_tasks', 'task_locks', 'task_progress_history')
ORDER BY table_name;

-- 预期结果：
-- | table_name              | column_count |
-- |-------------------------|--------------|
-- | parallel_tasks          | 22           |
-- | task_locks              | 5            |
-- | task_progress_history   | 4            |
```

### 2. 验证枚举类型

```sql
-- 查看枚举类型
SELECT 
    t.typname as enum_name,
    array_agg(e.enumlabel ORDER BY e.enumsortorder) as values
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname IN ('task_status', 'task_type', 'task_priority')
GROUP BY t.typname
ORDER BY t.typname;

-- 预期结果：
-- | enum_name     | values                                           |
-- |---------------|--------------------------------------------------|
-- | task_priority | {low,normal,high,urgent}                         |
-- | task_status   | {pending,queued,running,paused,...}              |
-- | task_type     | {search,write,code,review,analyze,design,layout} |
```

### 3. 验证索引

```sql
-- 查看 parallel_tasks 表的索引
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'parallel_tasks'
ORDER BY indexname;

-- 预期结果：至少 9 个索引
```

### 4. 验证函数

```sql
-- 查看创建的函数
SELECT 
    proname as function_name,
    pg_get_function_arguments(oid) as arguments
FROM pg_proc
WHERE proname IN (
    'acquire_pending_task',
    'update_task_progress',
    'complete_task',
    'fail_task',
    'cleanup_expired_locks',
    'get_task_statistics'
)
ORDER BY proname;

-- 预期结果：6 个函数
```

---

## 测试示例

### 测试 1：创建任务

```sql
-- 创建一个测试任务
INSERT INTO parallel_tasks (task_type, title, description, params, priority)
VALUES (
    'search',
    '搜索最新的 AI 新闻',
    '搜索并整理最近的 AI 行业新闻',
    '{"platforms": ["twitter", "reddit"], "limit": 10}'::jsonb,
    'high'
);

-- 查看创建的任务
SELECT id, task_type, title, status, priority, created_at 
FROM parallel_tasks 
ORDER BY created_at DESC 
LIMIT 5;
```

### 测试 2：获取任务

```sql
-- 使用小搜的 agent_id 获取任务
-- 小搜 ID: a1b2c3d4-1111-4000-8000-000000000001
SELECT * FROM acquire_pending_task(
    'a1b2c3d4-1111-4000-8000-000000000001'::uuid,
    ARRAY['search']::task_type[],
    30
);

-- 查看任务状态（应该是 running）
SELECT id, status, agent_name, started_at 
FROM parallel_tasks 
WHERE status = 'running';
```

### 测试 3：更新进度

```sql
-- 获取正在运行的任务 ID
SELECT id FROM parallel_tasks WHERE status = 'running' LIMIT 1;

-- 更新进度（假设任务 ID 是上面查到的）
SELECT update_task_progress(
    '任务ID'::uuid,
    50,
    '正在搜索 Twitter...'
);
```

### 测试 4：完成任务

```sql
-- 完成任务
SELECT complete_task(
    '任务ID'::uuid,
    '{"news_count": 10, "platforms_searched": 2}'::jsonb
);

-- 查看完成的任务
SELECT id, status, result, completed_at 
FROM parallel_tasks 
WHERE status = 'completed';
```

### 测试 5：失败重试

```sql
-- 创建一个会失败的任务
INSERT INTO parallel_tasks (task_type, title, max_retries)
VALUES ('code', '测试失败重试', 2);

-- 获取任务
SELECT * FROM acquire_pending_task(
    'a1b2c3d4-1111-4000-8000-000000000003'::uuid,  -- 小码的 ID
    ARRAY['code']::task_type[]
);

-- 标记失败（第一次，会重试）
SELECT fail_task(
    '任务ID'::uuid,
    '测试错误：第一次失败',
    true
);

-- 查看重试次数（应该是 1）
SELECT id, status, retry_count, max_retries 
FROM parallel_tasks 
WHERE title = '测试失败重试';

-- 再次获取并失败（第二次，会重试）
-- ... 重复上述步骤

-- 第三次失败（超过最大重试次数，标记为 failed）
-- ... 重复上述步骤
```

### 测试 6：清理过期锁

```sql
-- 创建一个短期锁（1 分钟）
SELECT * FROM acquire_pending_task(
    'a1b2c3d4-1111-4000-8000-000000000001'::uuid,
    NULL,
    1  -- 1 分钟后过期
);

-- 等待 1 分钟后，执行清理
SELECT cleanup_expired_locks();

-- 查看任务状态（应该被重置为 pending）
SELECT id, status FROM parallel_tasks WHERE status = 'pending';
```

### 测试 7：获取统计信息

```sql
-- 获取任务统计
SELECT * FROM get_task_statistics();

-- 预期输出：
-- | status    | count | oldest_pending | avg_duration |
-- |-----------|-------|----------------|--------------|
-- | completed | 1     | NULL           | 00:05:30     |
-- | failed    | 1     | NULL           | NULL         |
-- | pending   | 1     | 00:00:15       | NULL         |
```

---

## 完整测试脚本

将以下内容保存为 `test_parallel_tasks.sql` 并执行：

```sql
-- ============================================================
-- 并行任务系统完整测试
-- ============================================================

\echo '========================================'
\echo '开始测试并行任务系统'
\echo '========================================'

-- 清理测试数据
DELETE FROM task_progress_history;
DELETE FROM task_locks;
DELETE FROM parallel_tasks;

\echo ''
\echo '1. 创建测试任务...'
INSERT INTO parallel_tasks (task_type, title, description, params, priority)
VALUES 
    ('search', '搜索 AI 新闻', '搜索最新 AI 行业新闻', '{"limit": 10}'::jsonb, 'high'),
    ('write', '撰写技术博客', '写一篇关于 RAG 的博客', '{"topic": "RAG"}'::jsonb, 'normal'),
    ('code', '开发 API 接口', '实现用户管理 API', '{"language": "python"}'::jsonb, 'urgent');

SELECT id, task_type, title, status, priority FROM parallel_tasks ORDER BY priority, created_at;

\echo ''
\echo '2. 小搜领取搜索任务...'
SELECT * FROM acquire_pending_task(
    'a1b2c3d4-1111-4000-8000-000000000001'::uuid,  -- 小搜
    ARRAY['search']::task_type[]
);

\echo ''
\echo '3. 小码领取代码任务...'
SELECT * FROM acquire_pending_task(
    'a1b2c3d4-1111-4000-8000-000000000003'::uuid,  -- 小码
    ARRAY['code']::task_type[]
);

\echo ''
\echo '4. 查看任务状态...'
SELECT id, task_type, title, status, agent_name, progress FROM parallel_tasks ORDER BY status, priority;

\echo ''
\echo '5. 更新小搜任务进度...'
SELECT update_task_progress(
    (SELECT id FROM parallel_tasks WHERE agent_name = '小搜' LIMIT 1),
    50,
    '正在搜索 Twitter 和 Reddit...'
);

\echo ''
\echo '6. 完成小搜任务...'
SELECT complete_task(
    (SELECT id FROM parallel_tasks WHERE agent_name = '小搜' LIMIT 1),
    '{"news_count": 15, "platforms": ["twitter", "reddit"]}'::jsonb
);

\echo ''
\echo '7. 小码任务失败（第一次）...'
SELECT fail_task(
    (SELECT id FROM parallel_tasks WHERE agent_name = '小码' LIMIT 1),
    '测试错误：API 连接超时',
    true
);

\echo ''
\echo '8. 查看重试状态...'
SELECT id, task_type, title, status, retry_count, max_retries, error_message 
FROM parallel_tasks 
WHERE task_type = 'code';

\echo ''
\echo '9. 获取任务统计...'
SELECT * FROM get_task_statistics();

\echo ''
\echo '========================================'
\echo '测试完成！'
\echo '========================================'
```

执行测试：

```bash
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/test_parallel_tasks.sql
```

---

## 常见问题

### Q1: 报错 `relation "agents" does not exist`

**原因**：`agents` 表不存在，需要先执行基础建表脚本。

**解决**：
```bash
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < scripts/002_add_agents_table.sql
```

### Q2: 报错 `type "vector" does not exist`

**原因**：未安装 `pgvector` 扩展。

**解决**：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Q3: 报错 `function acquire_pending_task does not exist`

**原因**：函数脚本未执行或执行失败。

**解决**：检查函数脚本执行日志，确保没有错误。

### Q4: 任务无法被领取

**可能原因**：
1. 任务已被其他智能体锁定
2. 任务状态不是 `pending`
3. 任务类型与智能体支持的类型不匹配

**排查**：
```sql
-- 查看任务状态和锁
SELECT pt.id, pt.status, tl.agent_id, tl.expires_at
FROM parallel_tasks pt
LEFT JOIN task_locks tl ON pt.id = tl.task_id
WHERE pt.status = 'pending';

-- 清理过期锁
SELECT cleanup_expired_locks();
```

### Q5: 如何清空测试数据？

```sql
-- 清空所有测试数据（按依赖顺序）
DELETE FROM task_progress_history;
DELETE FROM task_locks;
DELETE FROM parallel_tasks;
```

---

## 表结构速查

### parallel_tasks 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| task_type | task_type | 任务类型 |
| title | VARCHAR(500) | 任务标题 |
| description | TEXT | 任务描述 |
| agent_id | UUID | 执行智能体ID |
| agent_name | VARCHAR(255) | 智能体名称 |
| status | task_status | 任务状态 |
| priority | task_priority | 优先级 |
| progress | INTEGER | 进度（0-100） |
| progress_message | TEXT | 进度描述 |
| params | JSONB | 任务参数 |
| result | JSONB | 任务结果 |
| error_message | TEXT | 错误信息 |
| memory_id | UUID | 关联记忆ID |
| parent_task_id | UUID | 父任务ID |
| retry_count | INTEGER | 已重试次数 |
| max_retries | INTEGER | 最大重试次数 |
| created_at | TIMESTAMP | 创建时间 |
| started_at | TIMESTAMP | 开始时间 |
| completed_at | TIMESTAMP | 完成时间 |
| updated_at | TIMESTAMP | 更新时间 |
| timeout_minutes | INTEGER | 超时时间 |

### task_locks 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 任务ID（唯一） |
| agent_id | UUID | 智能体ID |
| locked_at | TIMESTAMP | 锁定时间 |
| expires_at | TIMESTAMP | 过期时间 |

### task_progress_history 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 任务ID |
| progress | INTEGER | 进度（0-100） |
| message | TEXT | 进度描述 |
| created_at | TIMESTAMP | 创建时间 |

---

## 下一步

1. ✅ 数据库表和函数已创建
2. 🔄 实现 Python SDK（`backend/app/services/task_service.py`）
3. 🔄 实现 Agent Worker（智能体任务执行器）
4. 🔄 添加 API 路由（`/api/tasks`）
5. 🔄 前端界面（任务监控面板）

---

_执行指南完成！有问题随时找小码。_