# 多智能体系统数据持久化方案

> **调研报告**  
> 作者：小搜 🟢  
> 日期：2026-03-16  
> 版本：v1.0

---

## 📋 目录

1. [执行摘要](#一执行摘要)
2. [现有系统分析](#二现有系统分析)
3. [数据类型分类](#三数据类型分类)
4. [存储策略设计](#四存储策略设计)
5. [2T 空间分配方案](#五2t-空间分配方案)
6. [备份和恢复策略](#六备份和恢复策略)
7. [性能优化建议](#七性能优化建议)
8. [PostgreSQL 配置建议](#八postgresql-配置建议)
9. [实施路线图](#九实施路线图)
10. [附录：命令速查](#十附录命令速查)

---

## 一、执行摘要

### 1.1 调研背景

- **存储资源**：憨货拥有 2TB 固态硬盘，空间充足
- **使用场景**：个人电脑会关机，需要任务持久化
- **核心系统**：多智能体记忆系统（memory-hub）正在建设中

### 1.2 核心发现

| 发现项 | 现状 | 建议 |
|--------|------|------|
| **数据库表** | 已有 8+ 张核心表 | 新增 3 张任务表 |
| **数据量** | 当前约 7.4GB | 预计年增长 100-200GB |
| **备份策略** | 无系统备份 | 建立每日备份机制 |
| **归档策略** | 无自动归档 | 90天滚动保留 |

### 1.3 关键建议

1. ✅ **分层存储**：热数据（PostgreSQL）+ 温数据（文件系统）+ 冷数据（归档）
2. ✅ **双备份策略**：本地备份 + 云端备份（可选）
3. ✅ **自动归档**：任务历史 90 天归档，日志 30 天清理
4. ✅ **SSD 优化**：启用 TRIM，调整 PostgreSQL 缓存配置

---

## 二、现有系统分析

### 2.1 目录结构分析

```
/home/wen/projects/memory-hub/          [7.4GB]
├── agents/                             # 8个智能体配置
│   ├── team-coder/                     # 小码工作区
│   ├── team-researcher/                # 小搜工作区
│   ├── team-writer/                    # 小写工作区
│   └── ...                             # 其他智能体
├── backend/                            # FastAPI 后端
│   ├── app/
│   │   ├── api/                        # API 路由
│   │   ├── models/                     # 数据模型
│   │   ├── services/                   # 业务逻辑
│   │   ├── database.py                 # 数据库连接
│   │   └── config.py                   # 配置管理
│   └── tests/                          # 测试代码
├── database/                           # SQL 脚本
│   ├── 01_parallel_tasks_schema.sql    # 并行任务表
│   └── 02_parallel_tasks_functions.sql # 任务函数
├── scripts/                            # 数据库初始化脚本
│   ├── init-db.sql                     # 基础表创建
│   ├── 003_split_memory_tables.sql     # 双表架构迁移
│   └── ...
├── memory/                             # 记忆文件
├── generated_images/                   # 生成的图片
└── docs/                               # 文档

/home/wen/.openclaw/workspace/          [7.8MB]
├── skills/                             # 技能库
├── memory/                             # 每日记忆文件
└── AGENTS.md, SOUL.md, TOOLS.md        # 配置文件
```

### 2.2 数据库表结构分析

#### 2.2.1 现有核心表

| 表名 | 用途 | 数据量预估 | 增长趋势 |
|------|------|-----------|---------|
| `agents` | 智能体注册 | < 100 条 | 稳定 |
| `private_memories` | 私人记忆 | 10万-100万条 | 快速增长 |
| `shared_memories` | 共同记忆 | 1万-10万条 | 中等增长 |
| `memory_relations` | 记忆关联 | 10万-50万条 | 快速增长 |
| `sessions` | 会话上下文 | < 1000 条 | 稳定 |
| `knowledge` | 知识库 | 1万-5万条 | 中等增长 |

#### 2.2.2 新增任务表（即将创建）

| 表名 | 用途 | 预估数据量 | 保留策略 |
|------|------|-----------|---------|
| `parallel_tasks` | 并行任务主表 | 100万+ 条/年 | 90天归档 |
| `task_locks` | 分布式锁 | < 100 条 | 实时清理 |
| `task_progress_history` | 进度历史 | 1000万+ 条/年 | 30天清理 |

### 2.3 现有数据类型识别

#### 2.3.1 结构化数据（PostgreSQL 中）

| 数据类型 | 表名 | 大小预估 | 访问频率 |
|----------|------|---------|---------|
| 智能体元数据 | agents | < 1MB | 低 |
| 记忆内容 | private/shared_memories | 10-100GB | 高 |
| 向量嵌入 | private/shared_memories | 5-50GB | 高 |
| 任务状态 | parallel_tasks | 1-10GB | 极高 |
| 进度历史 | task_progress_history | 10-50GB | 中 |
| 会话上下文 | sessions | < 100MB | 中 |

#### 2.3.2 非结构化数据（文件系统中）

| 数据类型 | 位置 | 大小预估 | 访问频率 |
|----------|------|---------|---------|
| 技能文件 | skills/ | 10-50MB | 低 |
| 配置文件 | .env, *.md | < 10MB | 低 |
| 生成图片 | generated_images/ | 1-10GB | 中 |
| 日志文件 | logs/ | 1-5GB | 低 |
| 备份文件 | backups/ | 50-200GB | 极低 |
| 代码文件 | backend/, agents/ | 1-5GB | 高 |

---

## 三、数据类型分类

### 3.1 核心业务数据

#### 3.1.1 记忆数据

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 私人记忆 (private_memories) | PostgreSQL + pgvector | 需要向量搜索 | 永久 |
| 共同记忆 (shared_memories) | PostgreSQL + pgvector | 需要向量搜索 | 永久 |
| 记忆关联 (memory_relations) | PostgreSQL | 结构化关系 | 永久 |

#### 3.1.2 任务数据

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 任务主表 (parallel_tasks) | PostgreSQL | 需要事务、锁机制 | 90天归档 |
| 任务锁 (task_locks) | PostgreSQL | 分布式锁 | 实时清理 |
| 进度历史 (task_progress_history) | PostgreSQL | 审计追踪 | 30天清理 |

#### 3.1.3 会话数据

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 会话记录 (sessions) | PostgreSQL | 结构化数据 | 7天清理 |
| 对话历史 | PostgreSQL + 文件 | 大文本 + 结构化 | 30天归档 |

#### 3.1.4 配置数据

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 智能体配置 | PostgreSQL (agents表) | 结构化 | 永久 |
| 系统配置 | 文件 (.env, config) | 易编辑 | 版本控制 |
| 技能配置 | SKILL.md 文件 | 大文本 | 版本控制 |

### 3.2 执行过程数据

#### 3.2.1 代码文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 项目源码 | 文件系统 + Git | 版本控制 | 永久 |
| 脚本文件 | 文件系统 + Git | 版本控制 | 永久 |
| 临时代码 | 文件系统 | 快速访问 | 任务完成即删 |

#### 3.2.2 文档文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 设计文档 | 文件系统 + Git | 版本控制 | 永久 |
| 报告文档 | 文件系统 | 大文件 | 永久 |
| 临时文档 | 文件系统 | 快速访问 | 任务完成即删 |

#### 3.2.3 日志数据

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 应用日志 | 文件 + 数据库索引 | 快速写入、可查询 | 30天滚动 |
| 错误日志 | 文件 + 数据库索引 | 快速写入、可查询 | 90天滚动 |
| 访问日志 | 文件 | 大文件 | 7天滚动 |

#### 3.2.4 中间结果

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 临时文件 | /tmp 或 cache/ | 快速访问 | 定期清理 |
| 缓存数据 | 文件系统 | 快速访问 | LRU 策略 |
| 下载文件 | cache/downloads/ | 临时存储 | 7天清理 |

### 3.3 用户资产数据

#### 3.3.1 技能文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| SKILL.md | 文件系统 + Git | 版本控制 | 永久 |
| 技能资源 | 文件系统 | 大文件 | 永久 |
| 技能缓存 | 文件系统 | 快速访问 | 按需清理 |

#### 3.3.2 配置文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| .env | 文件系统 | 敏感信息 | 永久 + 备份 |
| config.json | 文件系统 + Git | 结构化配置 | 版本控制 |
| 智能体配置 | 文件系统 + Git | 个性化配置 | 版本控制 |

#### 3.3.3 项目文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 项目源码 | 文件系统 + Git | 版本控制 | 永久 |
| 项目文档 | 文件系统 + Git | 版本控制 | 永久 |
| 构建产物 | 文件系统 | 临时文件 | 按需清理 |

#### 3.3.4 媒体文件

| 子类型 | 存储方式 | 理由 | 保留策略 |
|--------|---------|------|---------|
| 生成图片 | 文件系统 | 大文件 | 按需保留 |
| 音频文件 | 文件系统 | 大文件 | 7天清理 |
| 视频文件 | 文件系统 | 超大文件 | 立即清理 |

---

## 四、存储策略设计

### 4.1 分层存储架构

```
┌─────────────────────────────────────────────────────────────┐
│                      数据分层存储架构                        │
├─────────────────────────────────────────────────────────────┤
│  热数据层 (Hot)    │  PostgreSQL 数据库                      │
│  访问频率：极高    │  - 任务状态                             │
│  延迟要求：< 10ms  │  - 记忆查询                             │
│  保留策略：永久    │  - 会话上下文                           │
├─────────────────────────────────────────────────────────────┤
│  温数据层 (Warm)   │  文件系统                               │
│  访问频率：中等    │  - 技能文件                             │
│  延迟要求：< 100ms │  - 配置文件                             │
│  保留策略：永久    │  - 项目源码                             │
├─────────────────────────────────────────────────────────────┤
│  冷数据层 (Cold)   │  归档存储                               │
│  访问频率：低      │  - 历史任务                             │
│  延迟要求：< 1s    │  - 旧日志                               │
│  保留策略：90天    │  - 备份文件                             │
├─────────────────────────────────────────────────────────────┤
│  临时数据层 (Temp) │  内存 / 临时文件                        │
│  访问频率：一次性  │  - 下载文件                             │
│  延迟要求：无      │  - 缓存数据                             │
│  保留策略：立即清理│  - 中间结果                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据存储策略总表

| 数据类型 | 存储方式 | 具体位置 | 保留策略 | 备份策略 |
|----------|---------|----------|---------|---------|
| **记忆数据** | PostgreSQL | memory_hub.private/shared_memories | 永久 | 每日全量 |
| **任务主表** | PostgreSQL | memory_hub.parallel_tasks | 90天归档 | 每日全量 |
| **进度历史** | PostgreSQL | memory_hub.task_progress_history | 30天清理 | 不备份 |
| **任务锁** | PostgreSQL | memory_hub.task_locks | 实时清理 | 不备份 |
| **会话数据** | PostgreSQL | memory_hub.sessions | 7天清理 | 不备份 |
| **代码文件** | Git + 文件 | ~/projects/ | 永久 | Git 推送 |
| **技能文件** | Git + 文件 | ~/.openclaw/workspace/skills/ | 永久 | Git 推送 |
| **配置文件** | 文件 | ~/.openclaw/workspace/ | 永久 | Git 推送 |
| **日志文件** | 文件 | ~/projects/memory-hub/logs/ | 30天滚动 | 不备份 |
| **生成图片** | 文件 | ~/projects/memory-hub/generated_images/ | 按需保留 | 可选备份 |
| **备份文件** | 文件 | ~/backups/ | 30天滚动 | 云端同步 |
| **归档数据** | 文件 | ~/archives/ | 90天滚动 | 云端同步 |

---

## 五、2T 空间分配方案

### 5.1 总体分配

```
/home/wen/ (2TB SSD)
├── projects/                    # 项目源码 [200GB]
│   └── memory-hub/              # 多智能体记忆中枢
├── databases/                   # PostgreSQL 数据 [100GB]
│   └── memory_hub/              # 数据库文件
├── workspace/                   # OpenClaw 工作区 [50GB]
│   ├── skills/                  # 技能库
│   ├── memory/                  # 每日记忆
│   └── agents/                  # 智能体配置
├── archives/                    # 归档数据 [500GB]
│   ├── tasks/                   # 历史任务归档
│   ├── memories/                # 历史记忆归档
│   ├── logs/                    # 日志归档
│   └── media/                   # 媒体文件归档
├── cache/                       # 缓存 [50GB]
│   ├── downloads/               # 下载文件
│   ├── temp/                    # 临时文件
│   └── embeddings/              # 向量缓存
└── backups/                     # 备份 [500GB]
    ├── database/                # 数据库备份
    ├── files/                   # 文件备份
    └── config/                  # 配置备份
```

### 5.2 详细分配表

| 目录 | 用途 | 预估大小 | 使用率 |
|------|------|---------|--------|
| /home/wen/projects/ | 项目源码 | 200GB | 10% |
| /home/wen/databases/ | PostgreSQL 数据 | 100GB | 5% |
| /home/wen/workspace/ | OpenClaw 工作区 | 50GB | 2.5% |
| /home/wen/archives/ | 归档数据 | 500GB | 25% |
| /home/wen/cache/ | 缓存 | 50GB | 2.5% |
| /home/wen/backups/ | 备份 | 500GB | 25% |
| **预留空间** | 增长缓冲 | 600GB | 30% |
| **总计** | - | **2000GB** | **100%** |

### 5.3 PostgreSQL 数据目录规划

```
/home/wen/databases/memory_hub/
├── base/                        # 数据库文件
│   ├── 16384/                   # memory_hub 数据库
│   └── ...
├── pg_wal/                      # WAL 日志
├── pg_stat/                     # 统计信息
├── pg_notify/                   # 通知数据
└── postgresql.conf              # 配置文件
```

---

## 六、备份和恢复策略

### 6.1 备份策略总览

| 数据类型 | 备份频率 | 备份方式 | 保留时间 | 存储位置 |
|----------|---------|---------|---------|---------|
| **数据库** | 每日 02:00 | pg_dump 全量 | 30天 | 本地 + 云端 |
| **WAL 日志** | 实时 | 归档模式 | 7天 | 本地 |
| **项目文件** | 每次提交 | Git 推送 | 永久 | GitHub |
| **配置文件** | 每日 | rsync | 30天 | 本地 |
| **技能文件** | 每日 | rsync | 30天 | 本地 |
| **生成图片** | 每周 | 可选备份 | 按需 | 云端 |

### 6.2 数据库备份脚本

```bash
#!/bin/bash
# /home/wen/projects/memory-hub/scripts/backup-database.sh
# 数据库每日备份脚本

BACKUP_DIR="/home/wen/backups/database"
DB_NAME="memory_hub"
DB_USER="memory_user"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
docker exec memory-hub-postgres pg_dump -U "$DB_USER" -d "$DB_NAME" \
    -Fc -f "/tmp/backup_${DATE}.dump"

# 复制到备份目录
docker cp memory-hub-postgres:/tmp/backup_${DATE}.dump \
    "$BACKUP_DIR/backup_${DATE}.dump"

# 清理旧备份
find "$BACKUP_DIR" -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] 数据库备份完成: backup_${DATE}.dump"
```

### 6.3 数据库恢复脚本

```bash
#!/bin/bash
# /home/wen/projects/memory-hub/scripts/restore-database.sh
# 数据库恢复脚本
# 用法: ./restore-database.sh backup_20260316_020000.dump

BACKUP_FILE="$1"
DB_NAME="memory_hub"
DB_USER="memory_user"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件名>"
    echo "可用备份:"
    ls -la /home/wen/backups/database/
    exit 1
fi

# 停止应用
docker stop memory-hub-backend

# 恢复数据库
docker exec -i memory-hub-postgres pg_restore \
    -U "$DB_USER" -d "$DB_NAME" --clean --if-exists \
    < "/home/wen/backups/database/$BACKUP_FILE"

# 启动应用
docker start memory-hub-backend

echo "[$(date)] 数据库恢复完成: $BACKUP_FILE"
```

### 6.4 文件备份脚本

```bash
#!/bin/bash
# /home/wen/projects/memory-hub/scripts/backup-files.sh
# 文件备份脚本

BACKUP_DIR="/home/wen/backups/files"
SOURCE_DIRS=(
    "/home/wen/.openclaw/workspace"
    "/home/wen/projects/memory-hub/config"
    "/home/wen/projects/memory-hub/agents"
)
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份每个目录
for dir in "${SOURCE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        tar -czf "$BACKUP_DIR/${name}_${DATE}.tar.gz" -C "$(dirname "$dir")" "$name"
        echo "[$(date)] 备份完成: ${name}_${DATE}.tar.gz"
    fi
done

# 清理旧备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
```

### 6.5 定时任务配置

```bash
# 添加到 crontab: crontab -e

# 每日 02:00 执行数据库备份
0 2 * * * /home/wen/projects/memory-hub/scripts/backup-database.sh >> /home/wen/backups/backup.log 2>&1

# 每日 03:00 执行文件备份
0 3 * * * /home/wen/projects/memory-hub/scripts/backup-files.sh >> /home/wen/backups/backup.log 2>&1

# 每周日 04:00 清理归档数据
0 4 * * 0 /home/wen/projects/memory-hub/scripts/cleanup-archives.sh >> /home/wen/backups/cleanup.log 2>&1
```

### 6.6 恢复测试计划

| 测试类型 | 频率 | 方法 | 验证标准 |
|----------|------|------|---------|
| 备份完整性 | 每日 | 检查文件大小 | 备份文件 > 0 |
| 恢复测试 | 每月 | 恢复到测试库 | 数据一致性检查 |
| 灾难恢复 | 每季度 | 完整恢复演练 | RTO < 1小时 |

---

## 七、性能优化建议

### 7.1 PostgreSQL 配置优化

#### 7.1.1 内存配置

```conf
# /home/wen/databases/memory_hub/postgresql.conf

# 共享内存缓冲区 (推荐: 25% 系统内存)
shared_buffers = 4GB

# 有效缓存大小 (推荐: 50% 系统内存)
effective_cache_size = 8GB

# 工作内存 (用于排序、哈希等操作)
work_mem = 256MB

# 维护工作内存 (用于 VACUUM、CREATE INDEX 等)
maintenance_work_mem = 512MB
```

#### 7.1.2 连接配置

```conf
# 最大连接数
max_connections = 100

# 连接池配置 (使用 PgBouncer 时)
# max_connections = 20

# 超级用户保留连接
superuser_reserved_connections = 3
```

#### 7.1.3 WAL 配置

```conf
# WAL 级别
wal_level = replica

# WAL 缓冲区
wal_buffers = 64MB

# 检查点间隔
checkpoint_timeout = 10min
checkpoint_completion_target = 0.9

# WAL 归档
archive_mode = on
archive_command = 'cp %p /home/wen/archives/wal/%f'
```

#### 7.1.4 查询优化

```conf
# 随机页面成本 (SSD 设置为 1.1)
random_page_cost = 1.1

# 顺序页面成本
seq_page_cost = 1.0

# 并行 workers
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

### 7.2 文件系统优化

#### 7.2.1 SSD 优化

```bash
# 启用 TRIM
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer

# 查看 TRIM 状态
systemctl status fstrim.timer

# 文件系统挂载选项
# 编辑 /etc/fstab
# UUID=xxx /home/wen ext4 noatime,nodiratime,discard 0 2
```

#### 7.2.2 I/O 调度器

```bash
# 查看当前调度器
cat /sys/block/nvme0n1/queue/scheduler

# 设置为 mq-deadline (SSD 推荐)
echo 'mq-deadline' | sudo tee /sys/block/nvme0n1/queue/scheduler

# 永久设置
# 编辑 /etc/udev/rules.d/60-ssd-scheduler.rules
# ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="mq-deadline"
```

### 7.3 索引策略

#### 7.3.1 记忆表索引

```sql
-- 向量索引 (HNSW 算法，适合高维向量)
CREATE INDEX idx_private_memories_embedding ON private_memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 查询索引
CREATE INDEX idx_private_memories_agent_id ON private_memories(agent_id);
CREATE INDEX idx_private_memories_type ON private_memories(memory_type);
CREATE INDEX idx_private_memories_importance ON private_memories(importance DESC);
CREATE INDEX idx_private_memories_created_at ON private_memories(created_at DESC);
CREATE INDEX idx_private_memories_tags ON private_memories USING GIN(tags);
```

#### 7.3.2 任务表索引

```sql
-- 状态查询索引
CREATE INDEX idx_parallel_tasks_status ON parallel_tasks(status);
CREATE INDEX idx_parallel_tasks_agent_id ON parallel_tasks(agent_id);
CREATE INDEX idx_parallel_tasks_task_type ON parallel_tasks(task_type);
CREATE INDEX idx_parallel_tasks_priority ON parallel_tasks(priority);
CREATE INDEX idx_parallel_tasks_created_at ON parallel_tasks(created_at DESC);

-- 复合索引
CREATE INDEX idx_parallel_tasks_status_agent ON parallel_tasks(status, agent_id);
CREATE INDEX idx_parallel_tasks_status_type ON parallel_tasks(task_type, status);
CREATE INDEX idx_parallel_tasks_pending_priority ON parallel_tasks(status, priority, created_at)
    WHERE status = 'pending';
```

### 7.4 归档策略

#### 7.4.1 自动归档脚本

```bash
#!/bin/bash
# /home/wen/projects/memory-hub/scripts/archive-old-data.sh
# 自动归档旧数据脚本

DB_NAME="memory_hub"
DB_USER="memory_user"
ARCHIVE_DIR="/home/wen/archives"
DATE=$(date +%Y%m%d)

# 归档 90 天前的已完成任务
psql -U "$DB_USER" -d "$DB_NAME" << EOF
\copy (
    SELECT * FROM parallel_tasks 
    WHERE status IN ('completed', 'failed', 'cancelled')
    AND completed_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
) TO '${ARCHIVE_DIR}/tasks/tasks_${DATE}.csv' WITH CSV HEADER;

DELETE FROM parallel_tasks 
WHERE status IN ('completed', 'failed', 'cancelled')
AND completed_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
EOF

# 归档 30 天前的进度历史
psql -U "$DB_USER" -d "$DB_NAME" << EOF
DELETE FROM task_progress_history 
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
EOF

# 清理 7 天前的会话
psql -U "$DB_USER" -d "$DB_NAME" << EOF
DELETE FROM sessions 
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
EOF

echo "[$(date)] 数据归档完成"
```

#### 7.4.2 归档时间表

| 数据类型 | 归档条件 | 归档动作 | 清理时间 |
|----------|---------|---------|---------|
| 已完成任务 | completed_at > 90天 | 导出 CSV + 删除 | 每日 04:00 |
| 失败任务 | completed_at > 90天 | 导出 CSV + 删除 | 每日 04:00 |
| 进度历史 | created_at > 30天 | 直接删除 | 每日 04:00 |
| 会话数据 | created_at > 7天 | 直接删除 | 每日 04:00 |
| 应用日志 | mtime > 30天 | 压缩归档 | 每周日 |
| 备份文件 | mtime > 30天 | 删除 | 每日 05:00 |

---

## 八、PostgreSQL 配置建议

### 8.1 完整配置文件

```conf
# /home/wen/databases/memory_hub/postgresql.conf
# PostgreSQL 14+ 优化配置

#------------------------------------------------------------------------------
# 文件位置
#------------------------------------------------------------------------------
data_directory = '/home/wen/databases/memory_hub'
hba_file = '/home/wen/databases/memory_hub/pg_hba.conf'
ident_file = '/home/wen/databases/memory_hub/pg_ident.conf'

#------------------------------------------------------------------------------
# 连接和认证
#------------------------------------------------------------------------------
listen_addresses = 'localhost,172.17.0.1'
port = 5432
max_connections = 100
superuser_reserved_connections = 3

#------------------------------------------------------------------------------
# 内存配置 (假设系统内存 16GB)
#------------------------------------------------------------------------------
shared_buffers = 4GB
effective_cache_size = 8GB
work_mem = 256MB
maintenance_work_mem = 512MB
dynamic_shared_memory_type = posix

#------------------------------------------------------------------------------
# WAL 配置
#------------------------------------------------------------------------------
wal_level = replica
wal_buffers = 64MB
max_wal_size = 2GB
min_wal_size = 512MB
checkpoint_timeout = 10min
checkpoint_completion_target = 0.9

# WAL 归档
archive_mode = on
archive_command = 'cp %p /home/wen/archives/wal/%f'
archive_timeout = 1h

#------------------------------------------------------------------------------
# 查询规划器
#------------------------------------------------------------------------------
random_page_cost = 1.1
seq_page_cost = 1.0
effective_io_concurrency = 200

# 并行查询
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

#------------------------------------------------------------------------------
# 日志配置
#------------------------------------------------------------------------------
log_destination = 'stderr'
logging_collector = on
log_directory = '/home/wen/projects/memory-hub/logs/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

#------------------------------------------------------------------------------
# 自动清理
#------------------------------------------------------------------------------
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.2
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.1

#------------------------------------------------------------------------------
# 时区
#------------------------------------------------------------------------------
timezone = 'Asia/Shanghai'
log_timezone = 'Asia/Shanghai'

#------------------------------------------------------------------------------
# 扩展
#------------------------------------------------------------------------------
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 10000
```

### 8.2 pg_hba.conf 配置

```conf
# /home/wen/databases/memory_hub/pg_hba.conf
# 客户端认证配置

# 本地连接
type  database    user            address                 method
local all         all                                     trust
host  all         all             127.0.0.1/32            trust
host  all         all             ::1/128                 trust

# Docker 网络
host  all         all             172.17.0.0/16           md5
host  all         all             172.18.0.0/16           md5

# 本地网络 (可选)
# host  all         all             192.168.0.0/16          md5
```

### 8.3 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg14
    container_name: memory-hub-postgres
    environment:
      POSTGRES_USER: memory_user
      POSTGRES_PASSWORD: memory_pass_2026
      POSTGRES_DB: memory_hub
      PGDATA: /var/lib/postgresql/data
    volumes:
      - /home/wen/databases/memory_hub:/var/lib/postgresql/data
      - /home/wen/projects/memory-hub/logs/postgresql:/var/log/postgresql
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/01-init.sql
    ports:
      - "5432:5432"
    command: >
      postgres
      -c config_file=/var/lib/postgresql/data/postgresql.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U memory_user -d memory_hub"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: memory-hub-backend
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: memory_user
      DB_PASSWORD: memory_pass_2026
      DB_NAME: memory_hub
    volumes:
      - /home/wen/projects/memory-hub:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
```

---

## 九、实施路线图

### 9.1 第一阶段：基础架构（1-2周）

| 任务 | 负责人 | 状态 | 验收标准 |
|------|--------|------|---------|
| 创建目录结构 | 小码 | ⏳ 待开始 | 目录存在且权限正确 |
| 配置 PostgreSQL | 小码 | ⏳ 待开始 | 数据库可正常连接 |
| 创建备份脚本 | 小码 | ⏳ 待开始 | 可成功执行备份 |
| 配置定时任务 | 小码 | ⏳ 待开始 | crontab 配置完成 |

### 9.2 第二阶段：数据迁移（2-3周）

| 任务 | 负责人 | 状态 | 验收标准 |
|------|--------|------|---------|
| 执行并行任务表 SQL | 小码 | ⏳ 待开始 | 表创建成功 |
| 迁移现有数据 | 小码 | ⏳ 待开始 | 数据完整性检查通过 |
| 创建索引 | 小码 | ⏳ 待开始 | 索引创建成功 |
| 验证查询性能 | 小码 | ⏳ 待开始 | 查询 < 100ms |

### 9.3 第三阶段：归档策略（3-4周）

| 任务 | 负责人 | 状态 | 验收标准 |
|------|--------|------|---------|
| 创建归档脚本 | 小码 | ⏳ 待开始 | 脚本可执行 |
| 测试归档流程 | 小码 | ⏳ 待开始 | 归档数据完整 |
| 配置自动清理 | 小码 | ⏳ 待开始 | 定时任务生效 |
| 验证恢复流程 | 小码 | ⏳ 待开始 | 可成功恢复数据 |

### 9.4 第四阶段：监控优化（持续）

| 任务 | 负责人 | 状态 | 验收标准 |
|------|--------|------|---------|
| 配置监控告警 | 小码 | ⏳ 待开始 | 告警可触发 |
| 性能调优 | 小码 | ⏳ 待开始 | QPS 达标 |
| 定期备份测试 | 小码 | ⏳ 待开始 | 每月恢复测试 |
| 容量规划 | 小搜 | ⏳ 待开始 | 每季度评估 |

---

## 十、附录：命令速查

### 10.1 数据库操作

```bash
# 连接数据库
docker exec -it memory-hub-postgres psql -U memory_user -d memory_hub

# 查看表大小
\dt+ 
SELECT pg_size_pretty(pg_total_relation_size('parallel_tasks'));

# 查看数据库大小
SELECT pg_size_pretty(pg_database_size('memory_hub'));

# 查看连接数
SELECT count(*) FROM pg_stat_activity;

# 查看慢查询
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# 手动执行归档
SELECT cleanup_old_memories(30, 0.3, 3);
SELECT cleanup_expired_locks();

# 备份数据库
docker exec memory-hub-postgres pg_dump -U memory_user -d memory_hub -Fc > backup.dump

# 恢复数据库
docker exec -i memory-hub-postgres pg_restore -U memory_user -d memory_hub --clean < backup.dump
```

### 10.2 文件操作

```bash
# 查看磁盘使用
df -h /home/wen
du -sh /home/wen/projects/memory-hub/*

# 清理日志
find /home/wen/projects/memory-hub/logs -name "*.log" -mtime +30 -delete

# 压缩归档
tar -czf archive.tar.gz /path/to/data

# 解压
 tar -xzf archive.tar.gz

# 同步备份
rsync -avz --delete /home/wen/projects/memory-hub/ /home/wen/backups/files/
```

### 10.3 Docker 操作

```bash
# 查看容器状态
docker ps -a | grep memory-hub

# 查看日志
docker logs -f memory-hub-postgres
docker logs -f memory-hub-backend

# 重启服务
docker restart memory-hub-postgres
docker restart memory-hub-backend

# 进入容器
docker exec -it memory-hub-postgres bash

# 查看资源使用
docker stats memory-hub-postgres
```

### 10.4 系统监控

```bash
# 查看系统资源
top
htop

# 查看磁盘 I/O
iostat -x 1

# 查看 PostgreSQL 统计
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
ORDER BY n_tup_ins DESC;
"

# 查看索引使用情况
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
"
```

### 10.5 故障排查

```bash
# 检查数据库连接
docker exec memory-hub-postgres pg_isready -U memory_user

# 检查表是否存在
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "\dt"

# 检查索引是否存在
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "\di"

# 查看锁等待
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
"

# 强制释放锁 (谨慎使用)
docker exec memory-hub-postgres psql -U memory_user -d memory_hub -c "
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction';
"
```

---

## 十一、总结

### 11.1 核心发现

1. **现有数据量**：约 7.4GB，预计年增长 100-200GB
2. **核心表结构**：8+ 张表，即将新增 3 张任务表
3. **存储需求**：2TB 空间充足，需合理规划
4. **备份现状**：无系统备份，需建立机制

### 11.2 关键建议

1. ✅ **分层存储**：热数据 PostgreSQL + 温数据文件系统 + 冷数据归档
2. ✅ **双备份策略**：本地每日备份 + Git 版本控制
3. ✅ **自动归档**：任务 90 天归档，日志 30 天清理
4. ✅ **性能优化**：SSD TRIM + PostgreSQL 缓存调优

### 11.3 下一步行动

| 优先级 | 任务 | 负责人 | 截止时间 |
|--------|------|--------|---------|
| P0 | 创建备份脚本并配置定时任务 | 小码 | 3天内 |
| P0 | 执行并行任务表 SQL | 小码 | 3天内 |
| P1 | 配置 PostgreSQL 优化参数 | 小码 | 1周内 |
| P1 | 创建归档脚本 | 小码 | 1周内 |
| P2 | 配置监控告警 | 小码 | 2周内 |
| P2 | 定期恢复测试 | 小码 | 每月 |

### 11.4 风险提示

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 数据库损坏 | 高 | 每日备份 + WAL 归档 |
| 磁盘空间不足 | 中 | 自动归档 + 容量监控 |
| 性能下降 | 中 | 索引优化 + 查询优化 |
| 数据丢失 | 高 | 双备份策略 + 定期测试 |

---

> **报告完成！**
>
> 憨货，数据持久化方案调研完成！方案已针对你的 2TB SSD 和个人电脑使用场景设计，重点解决了关机重启、任务持久化、自动归档等问题。
>
> 建议优先实施备份策略和并行任务表创建，其他的可以逐步推进。
>
> —— 小搜 🟢
