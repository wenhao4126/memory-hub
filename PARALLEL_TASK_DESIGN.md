# 多智能体记忆项目 - 并行任务系统设计

> **基于公共记忆数据表的多智能体并行处理方案**
> 
> 作者：小搜 🟢 | 日期：2026-03-16

---

## 📋 目录

1. [现有记忆系统分析](#一现有记忆系统分析)
2. [并行任务需求分析](#二并行任务需求分析)
3. [架构设计方案](#三架构设计方案)
4. [数据表设计](#四数据表设计)
5. [任务状态流转](#五任务状态流转)
6. [多小码协调机制](#六多小码协调机制)
7. [代码示例](#七代码示例)
8. [风险评估](#八风险评估)

---

## 一、现有记忆系统分析

### 1.1 数据库架构

目前记忆系统采用 **双表架构**（private_memories + shared_memories）：

```
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                │
├─────────────────────────┬───────────────────────────────┤
│   private_memories      │      shared_memories          │
│   (私人记忆表)          │      (共同记忆表)             │
├─────────────────────────┼───────────────────────────────┤
│ - id (UUID PK)          │ - id (UUID PK)                │
│ - agent_id (FK)         │ - agent_id (FK)               │
│ - content (TEXT)        │ - content (TEXT)              │
│ - embedding (vector)    │ - embedding (vector)          │
│ - memory_type           │ - memory_type                 │
│ - importance (FLOAT)    │ - importance                  │
│ - access_count          │ - access_count                │
│ - tags (TEXT[])         │ - tags                        │
│ - metadata (JSONB)      │ - metadata                    │
│ - created_at            │ - created_at                  │
│                         │ - visibility                  │
│                         │ - allowed_agents              │
└─────────────────────────┴───────────────────────────────┘
```

### 1.2 记忆类型

| 类型 | 英文 | 说明 | 示例 |
|------|------|------|------|
| 📌 事实 | fact | 客观信息 | "用户叫憨货，住在上海" |
| ❤️ 偏好 | preference | 用户喜好 | "喜欢简洁的回答，讨厌废话" |
| 🛠️ 技能 | skill | 能力标签 | "会写 Python 代码" |
| 📖 经验 | experience | 历史事件 | "上次用方案 A 解决了问题" |

### 1.3 并发机制分析

**现状：**

1. **数据库连接池**：使用 asyncpg 连接池（min=5, max=20）
2. **事务支持**：PostgreSQL 原生支持 ACID
3. **无锁机制**：目前无显式行级锁或分布式锁
4. **无任务队列**：没有内置的任务队列系统
5. **异步架构**：FastAPI + asyncpg 支持高并发

**代码示例（数据库连接）：**

```python
# database.py
self.pool = await asyncpg.create_pool(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
    min_size=5,      # 最小连接数
    max_size=20,     # 最大连接数
    command_timeout=60
)
```

### 1.4 现有并发问题

| 问题 | 说明 | 风险等级 |
|------|------|---------|
| 无行级锁 | 多个智能体同时修改同一记忆可能冲突 | ⚠️ 中 |
| 无任务状态 | 无法追踪长时间运行的任务 | 🔴 高 |
| 无进度追踪 | 无法知道任务执行进度 | 🔴 高 |
| 无失败重试 | 任务失败无法自动恢复 | ⚠️ 中 |
| 无资源限制 | 可能同时启动过多任务 | 🟡 低 |

---

## 二、并行任务需求分析

### 2.1 多智能体记忆项目的并行场景

```
┌─────────────────────────────────────────────────────────┐
│                    傻妞（总管家）                        │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
     ┌─────▼─────┐  ┌────▼────┐   ┌─────▼──────┐
     │  小搜 🟢  │  │ 小写 🟢 │   │  小码 🟡   │
     │ (搜索)    │  │ (文案)  │   │ (代码开发) │
     └─────┬─────┘  └────┬────┘   └─────┬──────┘
           │             │              │
           └─────────────┴──────────────┘
                         │
              ┌──────────▼──────────┐
              │   Memory Hub API    │
              │   (FastAPI)         │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   PostgreSQL        │
              │   + pgvector        │
              └─────────────────────┘
```

### 2.2 具体并行场景

| 场景 | 说明 | 并发数 |
|------|------|--------|
| **批量导入知识** | 多个小码同时导入 Obsidian 笔记 | 3-5 |
| **并行搜索** | 小搜同时搜索多个平台 | 5-10 |
| **批量生成图片** | 小图并行生成文章配图 | 3-5 |
| **代码审查** | 小审并行审查多个 PR | 2-3 |
| **数据分析** | 小析并行处理多个数据集 | 2-4 |

### 2.3 核心需求

1. **任务状态持久化**：任务状态需要存储在数据库中
2. **进度实时追踪**：能看到每个任务的执行进度
3. **多小码协调**：避免多个小码同时执行冲突任务
4. **失败自动重试**：任务失败能自动重试
5. **资源限制**：控制并发任务数量

---

## 三、架构设计方案

### 3.1 方案对比

| 方案 | 说明 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **A** | 复用记忆表（新增 task 类型） | 无需新表，简单 | 记忆表臃肿，查询复杂 | ⭐⭐ |
| **B** | 新建任务表，与记忆表关联 | 结构清晰，职责分离 | 需要维护两张表 | ⭐⭐⭐⭐ |
| **C** | 记忆表 + Redis/队列混合 | 性能好，功能强 | 引入新组件，复杂 | ⭐⭐⭐ |

### 3.2 推荐方案：方案 B（新建任务表）

**推荐理由：**

1. ✅ **职责分离**：任务和记忆是不同的概念，分开存储更清晰
2. ✅ **扩展性强**：任务表可以独立扩展，不影响记忆表性能
3. ✅ **查询高效**：任务状态查询不需要过滤记忆表的大量数据
4. ✅ **易于维护**：任务相关的逻辑集中在任务表，代码更清晰
5. ✅ **可复用记忆系统**：任务结果可以写入记忆表，实现"任务完成=记忆归档"

**架构图：**

```
┌─────────────────────────────────────────────────────────────┐
│                        智能体层                              │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│   │ 小搜 🟢 │  │ 小写 🟢 │  │ 小码 🟡 │  │ 小图 🎨 │       │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
└────────┼────────────┼────────────┼────────────┼────────────┘
         │            │            │            │
         └────────────┴──────┬─────┴────────────┘
                             │
                  ┌──────────▼──────────┐
                  │   Memory Hub API    │
                  │   (FastAPI)         │
                  └──────────┬──────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│  parallel_tasks │ │ private_memories│ │ shared_memories │
│  (任务表)       │ │ (私人记忆表)    │ │ (共同记忆表)    │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ - id (PK)       │ │ - id (PK)       │ │ - id (PK)       │
│ - agent_id (FK) │ │ - agent_id (FK) │ │ - agent_id (FK) │
│ - task_type     │ │ - content       │ │ - content       │
│ - status        │ │ - memory_type   │ │ - memory_type   │
│ - progress      │ │ - ...           │ │ - ...           │
│ - result        │ └─────────────────┘ └─────────────────┘
│ - memory_id(FK) │
└─────────────────┘
```

---

## 四、数据表设计

### 4.1 任务表 SQL

```sql
-- ============================================================
-- 并行任务表 - parallel_tasks
-- ============================================================
-- 功能：存储多智能体并行任务的状态和进度
-- 作者：小搜
-- 日期：2026-03-16
-- ============================================================

-- 创建任务状态枚举类型
CREATE TYPE task_status AS ENUM (
    'pending',      -- 待执行
    'queued',       -- 已入队
    'running',      -- 执行中
    'paused',       -- 已暂停
    'completed',    -- 已完成
    'failed',       -- 失败
    'cancelled',    -- 已取消
    'timeout'       -- 超时
);

-- 创建任务类型枚举
CREATE TYPE task_type AS ENUM (
    'search',       -- 搜索任务（小搜）
    'write',        -- 写作任务（小写）
    'code',         -- 代码任务（小码）
    'review',       -- 审查任务（小审）
    'analyze',      -- 分析任务（小析）
    'design',       -- 设计任务（小图）
    'layout',       -- 排版任务（小排）
    'custom'        -- 自定义任务
);

-- 创建任务优先级枚举
CREATE TYPE task_priority AS ENUM (
    'low',          -- 低优先级
    'normal',       -- 正常优先级
    'high',         -- 高优先级
    'urgent'        -- 紧急
);

-- ============================================================
-- 主任务表
-- ============================================================
CREATE TABLE IF NOT EXISTS parallel_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 任务基本信息
    task_type task_type NOT NULL,
    title VARCHAR(500) NOT NULL,                    -- 任务标题
    description TEXT,                               -- 任务描述
    
    -- 执行智能体
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    agent_name VARCHAR(255),                        -- 智能体名称（冗余，方便查询）
    
    -- 任务状态
    status task_status DEFAULT 'pending',
    priority task_priority DEFAULT 'normal',
    
    -- 进度追踪（0-100）
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    progress_message TEXT,                          -- 进度描述（如"正在搜索第 3/10 个平台"）
    
    -- 任务参数和结果
    params JSONB DEFAULT '{}',                      -- 任务参数（输入）
    result JSONB DEFAULT '{}',                      -- 任务结果（输出）
    error_message TEXT,                             -- 错误信息（失败时）
    
    -- 关联记忆（任务完成后归档到记忆系统）
    memory_id UUID REFERENCES shared_memories(id) ON DELETE SET NULL,
    
    -- 父任务（支持任务分解）
    parent_task_id UUID REFERENCES parallel_tasks(id) ON DELETE CASCADE,
    
    -- 重试机制
    retry_count INTEGER DEFAULT 0,                  -- 已重试次数
    max_retries INTEGER DEFAULT 3,                  -- 最大重试次数
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,            -- 开始执行时间
    completed_at TIMESTAMP WITH TIME ZONE,          -- 完成时间
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 超时设置（分钟）
    timeout_minutes INTEGER DEFAULT 30
);

-- 创建索引
CREATE INDEX idx_parallel_tasks_status ON parallel_tasks(status);
CREATE INDEX idx_parallel_tasks_agent_id ON parallel_tasks(agent_id);
CREATE INDEX idx_parallel_tasks_task_type ON parallel_tasks(task_type);
CREATE INDEX idx_parallel_tasks_priority ON parallel_tasks(priority);
CREATE INDEX idx_parallel_tasks_created_at ON parallel_tasks(created_at DESC);
CREATE INDEX idx_parallel_tasks_parent ON parallel_tasks(parent_task_id);

-- 创建复合索引（常用查询优化）
CREATE INDEX idx_parallel_tasks_status_agent ON parallel_tasks(status, agent_id);
CREATE INDEX idx_parallel_tasks_status_type ON parallel_tasks(status, task_type);

-- 添加表注释
COMMENT ON TABLE parallel_tasks IS '并行任务表：存储多智能体并行任务的状态和进度';
COMMENT ON COLUMN parallel_tasks.memory_id IS '关联的记忆ID，任务完成后归档到记忆系统';
COMMENT ON COLUMN parallel_tasks.parent_task_id IS '父任务ID，支持任务分解和子任务';

-- ============================================================
-- 任务锁表（用于分布式锁，避免多个小码同时执行同一任务）
-- ============================================================
CREATE TABLE IF NOT EXISTS task_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES parallel_tasks(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,   -- 锁过期时间
    
    UNIQUE(task_id)
);

-- 创建索引
CREATE INDEX idx_task_locks_agent ON task_locks(agent_id);
CREATE INDEX idx_task_locks_expires ON task_locks(expires_at);

COMMENT ON TABLE task_locks IS '任务锁表：分布式锁，确保同一任务只有一个智能体执行';

-- ============================================================
-- 任务进度历史表（记录进度变更历史）
-- ============================================================
CREATE TABLE IF NOT EXISTS task_progress_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES parallel_tasks(id) ON DELETE CASCADE,
    progress INTEGER NOT NULL CHECK (progress >= 0 AND progress <= 100),
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_progress_history_task ON task_progress_history(task_id);
CREATE INDEX idx_task_progress_history_created ON task_progress_history(created_at);

COMMENT ON TABLE task_progress_history IS '任务进度历史：记录任务进度的变更历史';

-- ============================================================
-- 辅助函数
-- ============================================================

-- 获取待执行的任务（带锁）
CREATE OR REPLACE FUNCTION acquire_pending_task(
    p_agent_id UUID,
    p_task_types task_type[] DEFAULT NULL,
    p_lock_duration_minutes INTEGER DEFAULT 30
)
RETURNS TABLE (
    task_id UUID,
    task_type task_type,
    title VARCHAR,
    params JSONB
)
LANGUAGE plpgsql
AS \$\$
DECLARE
    v_task_id UUID;
    v_lock_id UUID;
BEGIN
    -- 查找待执行的任务（按优先级排序）
    SELECT pt.id INTO v_task_id
    FROM parallel_tasks pt
    WHERE pt.status = 'pending'
      AND (p_task_types IS NULL OR pt.task_type = ANY(p_task_types))
      AND NOT EXISTS (
          SELECT 1 FROM task_locks tl 
          WHERE tl.task_id = pt.id 
          AND tl.expires_at > CURRENT_TIMESTAMP
      )
    ORDER BY 
        CASE pt.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'normal' THEN 3
            WHEN 'low' THEN 4
        END,
        pt.created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;
    
    -- 如果找到任务，创建锁
    IF v_task_id IS NOT NULL THEN
        INSERT INTO task_locks (task_id, agent_id, expires_at)
        VALUES (v_task_id, p_agent_id, CURRENT_TIMESTAMP + (p_lock_duration_minutes || ' minutes')::interval)
        RETURNING task_locks.id INTO v_lock_id;
        
        -- 更新任务状态
        UPDATE parallel_tasks
        SET status = 'running', 
            started_at = CURRENT_TIMESTAMP,
            agent_id = p_agent_id
        WHERE id = v_task_id;
        
        RETURN QUERY
        SELECT pt.id, pt.task_type, pt.title, pt.params
        FROM parallel_tasks pt
        WHERE pt.id = v_task_id;
    END IF;
END;
\$\$;

-- 更新任务进度
CREATE OR REPLACE FUNCTION update_task_progress(
    p_task_id UUID,
    p_progress INTEGER,
    p_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS \$\$
BEGIN
    -- 更新任务进度
    UPDATE parallel_tasks
    SET progress = p_progress,
        progress_message = COALESCE(p_message, progress_message),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_task_id;
    
    -- 记录进度历史
    INSERT INTO task_progress_history (task_id, progress, message)
    VALUES (p_task_id, p_progress, p_message);
END;
\$\$;

-- 完成任务
CREATE OR REPLACE FUNCTION complete_task(
    p_task_id UUID,
    p_result JSONB DEFAULT '{}',
    p_memory_id UUID DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS \$\$
BEGIN
    UPDATE parallel_tasks
    SET status = 'completed',
        progress = 100,
        result = p_result,
        memory_id = p_memory_id,
        completed_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_task_id;
    
    -- 删除任务锁
    DELETE FROM task_locks WHERE task_id = p_task_id;
END;
\$\$;

-- 失败任务（支持重试）
CREATE OR REPLACE FUNCTION fail_task(
    p_task_id UUID,
    p_error_message TEXT,
    p_auto_retry BOOLEAN DEFAULT true
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS \$\$
DECLARE
    v_retry_count INTEGER;
    v_max_retries INTEGER;
BEGIN
    SELECT retry_count, max_retries INTO v_retry_count, v_max_retries
    FROM parallel_tasks WHERE id = p_task_id;
    
    -- 如果允许重试且未超过最大重试次数
    IF p_auto_retry AND v_retry_count < v_max_retries THEN
        UPDATE parallel_tasks
        SET status = 'pending',
            retry_count = retry_count + 1,
            error_message = p_error_message,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_task_id;
        
        -- 删除旧锁
        DELETE FROM task_locks WHERE task_id = p_task_id;
        
        RETURN true; -- 已重试
    ELSE
        UPDATE parallel_tasks
        SET status = 'failed',
            error_message = p_error_message,
            completed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_task_id;
        
        -- 删除任务锁
        DELETE FROM task_locks WHERE task_id = p_task_id;
        
        RETURN false; -- 未重试，已失败
    END IF;
END;
\$\$;

-- 清理过期锁
CREATE OR REPLACE FUNCTION cleanup_expired_locks()
RETURNS INTEGER
LANGUAGE plpgsql
AS \$\$
DECLARE
    v_count INTEGER;
BEGIN
    -- 将过期锁对应的任务重置为 pending
    UPDATE parallel_tasks
    SET status = 'pending'
    WHERE id IN (
        SELECT task_id FROM task_locks 
        WHERE expires_at < CURRENT_TIMESTAMP
    );
    
    -- 删除过期锁
    DELETE FROM task_locks 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
\$\$;

-- 输出完成信息
DO \$\$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '并行任务表创建完成！';
    RAISE NOTICE '';
    RAISE NOTICE '创建的表：';
    RAISE NOTICE '  - parallel_tasks (主任务表)';
    RAISE NOTICE '  - task_locks (任务锁表)';
    RAISE NOTICE '  - task_progress_history (进度历史表)';
    RAISE NOTICE '';
    RAISE NOTICE '创建的函数：';
    RAISE NOTICE '  - acquire_pending_task() - 获取待执行任务';
    RAISE NOTICE '  - update_task_progress() - 更新任务进度';
    RAISE NOTICE '  - complete_task() - 完成任务';
    RAISE NOTICE '  - fail_task() - 失败任务（支持重试）';
    RAISE NOTICE '  - cleanup_expired_locks() - 清理过期锁';
    RAISE NOTICE '========================================';
END;
\$\$;

---

## 五、任务状态流转

### 5.1 状态流转图

```
                    ┌─────────────┐
                    │   pending   │
                    │   (待执行)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌───────────┐
        │ running │  │cancelled│  │  failed   │
        │ (执行中)│  │ (已取消)│  │  (失败)   │
        └────┬────┘  └─────────┘  └─────┬─────┘
             │                           │
      ┌──────┼──────┐                   │
      │      │      │                   │ (重试次数 < 最大重试次数)
      ▼      ▼      ▼                   │
┌─────────┐ ┌───────┐ ┌─────────┐      │
│paused   │ │timeout│ │completed│      │
│(已暂停) │ │(超时) │ │(已完成) │      │
└────┬────┘ └───────┘ └────┬────┘      │
     │                     │           │
     │                     ▼           │
     │              ┌─────────────┐    │
     │              │  memory     │    │
     │              │ (归档到记忆)│    │
     │              └─────────────┘    │
     │                                 │
     └─────────────────────────────────┘
                   (可恢复)
```

### 5.2 状态说明

| 状态 | 说明 | 可转换到 |
|------|------|---------|
| **pending** | 待执行，等待被智能体领取 | running, cancelled |
| **queued** | 已入队，等待调度 | running, cancelled |
| **running** | 执行中 | paused, completed, failed, timeout |
| **paused** | 已暂停，可恢复 | running, cancelled |
| **completed** | 已完成，结果已归档到记忆 | -（终态） |
| **failed** | 失败，可能触发重试 | pending（重试）, cancelled |
| **cancelled** | 已取消 | -（终态） |
| **timeout** | 超时 | pending（重试）, failed |

### 5.3 状态流转规则

```python
# 状态流转规则
STATE_TRANSITIONS = {
    'pending': ['running', 'cancelled'],
    'queued': ['running', 'cancelled'],
    'running': ['paused', 'completed', 'failed', 'timeout'],
    'paused': ['running', 'cancelled'],
    'completed': [],  # 终态
    'failed': ['pending'],  # 重试
    'cancelled': [],  # 终态
    'timeout': ['pending', 'failed']  # 重试或失败
}
```

---

## 六、多小码协调机制

### 6.1 核心问题

**问题：多个小码并行时，怎么通过记忆系统协调？**

**解决方案：基于数据库的分布式锁 + 任务队列**

### 6.2 协调机制架构

```
┌─────────────────────────────────────────────────────────────┐
│                        任务分发器                            │
│                    （Task Dispatcher）                       │
├─────────────────────────────────────────────────────────────┤
│  1. 创建任务 → 写入 parallel_tasks（status=pending）        │
│  2. 监控任务状态 → 查询任务进度                              │
│  3. 任务完成 → 结果归档到记忆系统                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        小码工作池                            │
│                    （Agent Worker Pool）                     │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   小搜 🟢   │   小写 🟢   │   小码 🟡   │     小图 🎨       │
│  (搜索)     │  (文案)     │  (代码)     │    (设计)         │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ 1. 获取任务 │ 1. 获取任务 │ 1. 获取任务 │ 1. 获取任务       │
│ 2. 创建锁   │ 2. 创建锁   │ 2. 创建锁   │ 2. 创建锁         │
│ 3. 执行     │ 3. 执行     │ 3. 执行     │ 3. 执行           │
│ 4. 更新进度 │ 4. 更新进度 │ 4. 更新进度 │ 4. 更新进度       │
│ 5. 完成     │ 5. 完成     │ 5. 完成     │ 5. 完成           │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL 数据库                       │
├─────────────────────┬───────────────────────────────────────┤
│   parallel_tasks    │           task_locks                  │
│   (任务状态)        │           (分布式锁)                  │
├─────────────────────┼───────────────────────────────────────┤
│ - id                │ - id                                  │
│ - status            │ - task_id (唯一)                      │
│ - agent_id          │ - agent_id                            │
│ - progress          │ - expires_at                          │
│ - ...               │                                       │
└─────────────────────┴───────────────────────────────────────┘
```

### 6.3 避免冲突的核心机制

**1. 任务锁（Task Lock）**

```sql
-- 获取任务时自动创建锁
INSERT INTO task_locks (task_id, agent_id, expires_at)
VALUES (task_id, agent_id, NOW() + interval '30 minutes');

-- 锁的唯一约束防止重复领取
UNIQUE(task_id)
```

**2. 原子性任务获取**

```sql
-- 使用 FOR UPDATE SKIP LOCKED 实现原子性获取
SELECT * FROM parallel_tasks
WHERE status = 'pending'
  AND NOT EXISTS (
      SELECT 1 FROM task_locks 
      WHERE task_id = parallel_tasks.id 
      AND expires_at > NOW()
  )
ORDER BY priority, created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

**3. 锁过期机制**

- 锁默认 30 分钟过期
- 过期后任务自动重置为 pending
- 其他小码可以重新领取

### 6.4 并发控制策略

| 策略 | 说明 | 实现方式 |
|------|------|---------|
| **互斥执行** | 同一任务只有一个执行者 | task_locks 唯一约束 |
| **优先级调度** | 紧急任务优先执行 | ORDER BY priority |
| **公平调度** | 避免某个小码独占任务 | 按 created_at 排序 |
| **超时释放** | 防止死锁 | expires_at 字段 |
| **重试机制** | 失败任务自动重试 | retry_count + max_retries |

---

## 七、代码示例

### 7.1 任务分发器（Task Dispatcher）

```python
# services/task_dispatcher.py
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..database import db
from ..models.schemas import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskDispatcher:
    """任务分发器：创建和管理并行任务"""
    
    async def create_task(
        self,
        task_type: str,
        title: str,
        description: str = None,
        agent_id: str = None,
        priority: str = 'normal',
        params: Dict[str, Any] = None,
        parent_task_id: str = None,
        timeout_minutes: int = 30
    ) -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型 (search/write/code/review/analyze/design/layout/custom)
            title: 任务标题
            description: 任务描述
            agent_id: 指定执行智能体（可选）
            priority: 优先级 (low/normal/high/urgent)
            params: 任务参数
            parent_task_id: 父任务ID（支持子任务）
            timeout_minutes: 超时时间（分钟）
        
        Returns:
            task_id: 任务ID
        """
        query = """
            INSERT INTO parallel_tasks 
            (task_type, title, description, agent_id, priority, 
             params, parent_task_id, timeout_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        
        task_id = await db.fetchval(
            query,
            task_type,
            title,
            description,
            uuid.UUID(agent_id) if agent_id else None,
            priority,
            params or {},
            uuid.UUID(parent_task_id) if parent_task_id else None,
            timeout_minutes
        )
        
        logger.info(f"任务创建成功: {task_id}, 类型: {task_type}, 优先级: {priority}")
        return str(task_id)
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        query = """
            SELECT pt.*, a.name as agent_name
            FROM parallel_tasks pt
            LEFT JOIN agents a ON pt.agent_id = a.id
            WHERE pt.id = $1
        """
        row = await db.fetchrow(query, uuid.UUID(task_id))
        return dict(row) if row else None
    
    async def list_tasks(
        self,
        status: str = None,
        agent_id: str = None,
        task_type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """列出任务"""
        conditions = []
        params = []
        
        if status:
            conditions.append(f"status = ${len(params) + 1}")
            params.append(status)
        
        if agent_id:
            conditions.append(f"agent_id = ${len(params) + 1}")
            params.append(uuid.UUID(agent_id))
        
        if task_type:
            conditions.append(f"task_type = ${len(params) + 1}")
            params.append(task_type)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM parallel_tasks
            {where_clause}
            ORDER BY 
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([limit, offset])
        
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        query = """
            UPDATE parallel_tasks
            SET status = 'cancelled',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND status IN ('pending', 'queued', 'paused')
            RETURNING id
        """
        result = await db.fetchval(query, uuid.UUID(task_id))
        
        if result:
            # 删除任务锁
            await db.execute("DELETE FROM task_locks WHERE task_id = $1", uuid.UUID(task_id))
            logger.info(f"任务已取消: {task_id}")
            return True
        return False


# 全局实例
task_dispatcher = TaskDispatcher()
```

### 7.2 小码工作池（Agent Worker）

```python
# services/agent_worker.py
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..database import db

logger = logging.getLogger(__name__)


class AgentWorker:
    """智能体工作器：每个小码的运行实例"""
    
    def __init__(self, agent_id: str, agent_name: str, supported_types: List[str]):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.supported_types = supported_types
        self.current_task_id = None
        self._running = False
    
    async def start(self):
        """启动工作器"""
        self._running = True
        logger.info(f"工作器启动: {self.agent_name} ({self.agent_id})")
        
        while self._running:
            try:
                # 1. 获取待执行任务
                task = await self._acquire_task()
                if task:
                    # 2. 执行任务
                    await self._execute_task(task)
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"工作器异常: {e}")
                await asyncio.sleep(10)
    
    async def stop(self):
        """停止工作器"""
        self._running = False
        logger.info(f"工作器停止: {self.agent_name}")
    
    async def _acquire_task(self) -> Optional[Dict]:
        """获取待执行任务（使用数据库函数）"""
        query = """
            SELECT * FROM acquire_pending_task(
                $1::uuid,
                $2::task_type[],
                30
            )
        """
        row = await db.fetchrow(
            query,
            uuid.UUID(self.agent_id),
            self.supported_types
        )
        
        if row:
            self.current_task_id = str(row['task_id'])
            logger.info(f"{self.agent_name} 领取任务: {self.current_task_id}")
            return dict(row)
        return None
    
    async def _execute_task(self, task: Dict):
        """执行任务"""
        task_id = str(task['task_id'])
        task_type = task['task_type']
        params = task['params']
        
        try:
            logger.info(f"开始执行任务: {task_id}, 类型: {task_type}")
            
            # 根据任务类型执行不同的逻辑
            if task_type == 'search':
                result = await self._do_search(params)
            elif task_type == 'write':
                result = await self._do_write(params)
            elif task_type == 'code':
                result = await self._do_code(params)
            elif task_type == 'review':
                result = await self._do_review(params)
            elif task_type == 'analyze':
                result = await self._do_analyze(params)
            elif task_type == 'design':
                result = await self._do_design(params)
            elif task_type == 'layout':
                result = await self._do_layout(params)
            else:
                result = await self._do_custom(params)
            
            # 完成任务
            await self._complete_task(task_id, result)
            
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            await self._fail_task(task_id, str(e))
        
        finally:
            self.current_task_id = None
    
    async def _update_progress(self, task_id: str, progress: int, message: str = None):
        """更新任务进度"""
        query = "SELECT update_task_progress($1::uuid, $2, $3)"
        await db.execute(query, uuid.UUID(task_id), progress, message)
        logger.debug(f"任务进度更新: {task_id} -> {progress}%")
    
    async def _complete_task(self, task_id: str, result: Dict):
        """完成任务"""
        # 将结果归档到记忆系统
        memory_id = await self._archive_to_memory(result)
        
        query = "SELECT complete_task($1::uuid, $2, $3)"
        await db.execute(
            query,
            uuid.UUID(task_id),
            result,
            uuid.UUID(memory_id) if memory_id else None
        )
        logger.info(f"任务完成: {task_id}")
    
    async def _fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        query = "SELECT fail_task($1::uuid, $2, true)"
        await db.execute(query, uuid.UUID(task_id), error_message)
        logger.warning(f"任务失败: {task_id}, 错误: {error_message}")
    
    async def _archive_to_memory(self, result: Dict) -> Optional[str]:
        """将任务结果归档到记忆系统"""
        # 这里调用 memory_service 创建记忆
        # 返回 memory_id
        pass
    
    # 各类型任务的具体实现
    async def _do_search(self, params: Dict) -> Dict:
        """搜索任务"""
        # 小搜的实现
        pass
    
    async def _do_write(self, params: Dict) -> Dict:
        """写作任务"""
        # 小写的实现
        pass
    
    async def _do_code(self, params: Dict) -> Dict:
        """代码任务"""
        # 小码的实现
        pass
    
    async def _do_review(self, params: Dict) -> Dict:
        """审查任务"""
        # 小审的实现
        pass
    
    async def _do_analyze(self, params: Dict) -> Dict:
        """分析任务"""
        # 小析的实现
        pass
    
    async def _do_design(self, params: Dict) -> Dict:
        """设计任务"""
        # 小图的实现
        pass
    
    async def _do_layout(self, params: Dict) -> Dict:
        """排版任务"""
        # 小排的实现
        pass
    
    async def _do_custom(self, params: Dict) -> Dict:
        """自定义任务"""
        pass


class WorkerPool:
    """工作池：管理多个小码工作器"""
    
    def __init__(self):
        self.workers: List[AgentWorker] = []
        self._tasks = []
    
    def register_worker(self, worker: AgentWorker):
        """注册工作器"""
        self.workers.append(worker)
        logger.info(f"工作器注册: {worker.agent_name}")
    
    async def start_all(self):
        """启动所有工作器"""
        self._tasks = [
            asyncio.create_task(worker.start())
            for worker in self.workers
        ]
        logger.info(f"所有工作器已启动，共 {len(self.workers)} 个")
    
    async def stop_all(self):
        """停止所有工作器"""
        for worker in self.workers:
            await worker.stop()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("所有工作器已停止")


# 全局工作池
worker_pool = WorkerPool()
```

### 7.3 进度追踪示例

```python
# 前端查询任务进度示例

async def get_task_progress(task_id: str):
    """获取任务进度"""
    # 查询当前进度
    query = """
        SELECT pt.*, 
               (SELECT json_agg(tph.*) 
                FROM task_progress_history tph 
                WHERE tph.task_id = pt.id 
                ORDER BY tph.created_at DESC 
                LIMIT 10) as progress_history
        FROM parallel_tasks pt
        WHERE pt.id = $1
    """
    row = await db.fetchrow(query, uuid.UUID(task_id))
    
    if not row:
        return None
    
    return {
        'task_id': str(row['id']),
        'status': row['status'],
        'progress': row['progress'],
        'progress_message': row['progress_message'],
        'agent_name': row['agent_name'],
        'created_at': row['created_at'],
        'started_at': row['started_at'],
        'history': row['progress_history'] or []
    }


# WebSocket 实时推送进度（可选）
async def broadcast_progress(task_id: str, progress: int, message: str):
    """广播任务进度更新"""
    # 通过 WebSocket 推送给前端
    pass
```

### 7.4 API 路由示例

```python
# api/routes_tasks.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from ..services.task_dispatcher import task_dispatcher
from ..services.agent_worker import worker_pool, AgentWorker

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest):
    """创建任务"""
    task_id = await task_dispatcher.create_task(
        task_type=request.task_type,
        title=request.title,
        description=request.description,
        priority=request.priority,
        params=request.params
    )
    return {"task_id": task_id, "status": "pending"}


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    """获取任务详情"""
    task = await task_dispatcher.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_type: Optional[str] = None
):
    """列出任务"""
    tasks = await task_dispatcher.list_tasks(
        status=status,
        agent_id=agent_id,
        task_type=task_type
    )
    return tasks


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    success = await task_dispatcher.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="任务无法取消（可能已在执行或已完成）"
        )
    return {"message": "任务已取消"}


@router.get("/tasks/{task_id}/progress")
async def get_progress(task_id: str):
    """获取任务进度"""
    progress = await get_task_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="任务不存在")
    return progress
```

---

## 八、风险评估

### 8.1 并发冲突风险

| 风险 | 说明 | 缓解措施 |
|------|------|---------|
| **重复领取** | 多个小码同时领取同一任务 | task_locks 唯一约束 |
| **死锁** | 任务锁未释放导致任务卡住 | 锁过期机制（30分钟） |
| **数据竞争** | 同时更新任务进度 | 数据库事务隔离 |
| **资源耗尽** | 同时启动过多任务 | 连接池限制（max=20） |

### 8.2 失败重试风险

| 风险 | 说明 | 缓解措施 |
|------|------|---------|
| **无限重试** | 失败任务不断重试 | max_retries 限制（默认3次） |
| **重试风暴** | 大量失败任务同时重试 | 指数退避 + 优先级降级 |
| **状态不一致** | 重试时状态混乱 | 事务保证原子性 |

### 8.3 资源限制

| 资源 | 当前限制 | 建议 |
|------|---------|------|
| 数据库连接 | 20 | 根据并发数调整 |
| 任务锁过期 | 30分钟 | 根据任务类型调整 |
| 最大重试次数 | 3次 | 根据任务重要性调整 |
| 并发任务数 | 无限制 | 建议添加限制 |

### 8.4 监控建议

```python
# 监控指标
METRICS = {
    'task_queue_depth': '待执行任务数',
    'task_completion_rate': '任务完成率',
    'task_failure_rate': '任务失败率',
    'average_task_duration': '平均任务执行时间',
    'lock_expiration_rate': '锁过期率',
    'retry_rate': '重试率'
}
```

---

## 九、总结

### 9.1 核心发现

1. **现有记忆系统**：采用双表架构（private/shared），支持向量搜索，但**无任务队列机制**

2. **推荐方案**：**方案 B（新建任务表）**
   - 新建 `parallel_tasks` 表存储任务状态
   - 新建 `task_locks` 表实现分布式锁
   - 新建 `task_progress_history` 表记录进度历史

3. **关键设计**：
   - ✅ 任务状态持久化到数据库
   - ✅ 基于数据库的分布式锁避免冲突
   - ✅ 任务完成后归档到记忆系统
   - ✅ 支持失败重试和超时处理

### 9.2 实施步骤

1. **第一步**：执行 SQL 脚本创建任务表
2. **第二步**：实现 TaskDispatcher 服务
3. **第三步**：实现 AgentWorker 工作器
4. **第四步**：添加 API 路由
5. **第五步**：集成到现有记忆系统

### 9.3 预期效果

- 🎯 **多小码并行**：支持 8 个小码同时工作
- 🎯 **进度实时追踪**：随时查看任务执行进度
- 🎯 **自动协调**：避免任务冲突和重复执行
- 🎯 **失败恢复**：自动重试失败任务
- 🎯 **结果归档**：任务结果自动存入记忆系统

---

> **文档完成！** 
> 
> 憨货，这个方案可以直接落地实现。有问题随时喊我！
> 
> —— 小搜 🟢
