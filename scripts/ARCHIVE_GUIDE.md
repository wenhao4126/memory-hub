# 手动归档系统使用指南

> **作者**：小码 🟡  
> **日期**：2026-03-16  
> **版本**：v1.0

---

## 📋 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [归档流程](#归档流程)
4. [命令详解](#命令详解)
5. [常见问题](#常见问题)
6. [最佳实践](#最佳实践)

---

## 概述

### 什么是手动归档？

手动归档系统允许你按项目 ID 归档已完成的任务数据，而不是按时间自动归档。这样可以：

- ✅ 保持项目数据的完整性
- ✅ 灵活控制归档时机
- ✅ 减少数据库存储压力
- ✅ 保留历史数据用于审计

### 归档流程

```
1. 查看项目列表 → list-projects.sh
2. 选择要归档的项目
3. 执行归档 → archive-project.sh <project_id>
4. 查看归档历史 → list-archives.sh
```

---

## 快速开始

### 1. 初始化数据库

首次使用前，需要执行 SQL 脚本添加 `project_id` 字段：

```bash
# 进入项目目录
cd /home/wen/projects/memory-hub

# 执行 SQL 脚本
docker exec -i memory-hub-postgres psql -U memory_user -d memory_hub < database/03_add_project_id.sql
```

### 2. 为任务分配项目 ID

```sql
-- 为新任务分配项目 ID
INSERT INTO parallel_tasks (task_type, title, project_id, priority)
VALUES ('search', '搜索 AI 新闻', 'memory-hub-phase1', 'high');

-- 为现有任务分配项目 ID
UPDATE parallel_tasks 
SET project_id = 'memory-hub-phase1' 
WHERE id = '任务ID';
```

### 3. 查看项目列表

```bash
bash scripts/list-projects.sh
```

输出示例：
```
 项目ID              | 总任务数 | 已完成 | 已失败 | 活跃中
---------------------+----------+--------+--------+--------
 memory-hub-phase1   |       50 |     45 |      2 |      3
 agent-system-v2     |       30 |     30 |      0 |      0
 未分配              |       10 |      5 |      1 |      4
```

### 4. 归档项目

```bash
# 归档已完成的项目
bash scripts/archive-project.sh agent-system-v2

# 模拟归档（不删除数据）
bash scripts/archive-project.sh agent-system-v2 --dry-run
```

### 5. 查看归档历史

```bash
bash scripts/list-archives.sh
```

---

## 归档流程

### 步骤 1：查看项目列表

```bash
# 基本查询
bash scripts/list-projects.sh

# 详细模式（包含归档建议）
bash scripts/list-projects.sh --verbose
```

### 步骤 2：确认项目状态

归档前请确认：
- ✅ 项目没有活跃任务（pending/queued/running）
- ✅ 项目任务已完成或已失败
- ✅ 不需要再查询这些任务

### 步骤 3：执行归档

```bash
# 正式归档
bash scripts/archive-project.sh <project_id>

# 模拟归档（推荐先执行）
bash scripts/archive-project.sh <project_id> --dry-run
```

### 步骤 4：验证归档

```bash
# 查看归档历史
bash scripts/list-archives.sh

# 查看归档文件内容
tar -tzf /home/wen/archives/projects/<project_id>_<timestamp>.tar.gz

# 解压归档文件
tar -xzf /home/wen/archives/projects/<project_id>_<timestamp>.tar.gz -C /tmp/
```

---

## 命令详解

### list-projects.sh - 查看项目列表

**用法**：
```bash
bash scripts/list-projects.sh [--verbose]
```

**参数**：
- `--verbose` 或 `-v`：显示详细信息和归档建议

**输出字段**：
| 字段 | 说明 |
|------|------|
| 项目ID | 项目标识符 |
| 总任务数 | 该项目的任务总数 |
| 已完成 | 已完成的任务数 |
| 已失败 | 失败的任务数 |
| 活跃中 | 正在执行的任务数 |
| 首个任务 | 第一个任务的创建时间 |
| 最后任务 | 最后一个任务的创建时间 |

---

### archive-project.sh - 归档项目

**用法**：
```bash
bash scripts/archive-project.sh <project_id> [--dry-run]
```

**参数**：
- `project_id`：要归档的项目 ID（必需）
- `--dry-run`：模拟运行，不实际删除数据

**环境变量**：
| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 5432 | 数据库端口 |
| DB_NAME | memory_hub | 数据库名称 |
| DB_USER | memory_user | 数据库用户 |
| DB_PASSWORD | memory_pass_2026 | 数据库密码 |
| ARCHIVE_DIR | /home/wen/archives/projects | 归档目录 |

**归档内容**：
1. `parallel_tasks` 表中该项目的所有任务
2. `task_progress_history` 表中相关的进度历史
3. 压缩为 `.tar.gz` 文件

**示例**：
```bash
# 基本归档
bash scripts/archive-project.sh memory-hub-phase1

# 模拟归档
bash scripts/archive-project.sh memory-hub-phase1 --dry-run

# 使用自定义数据库连接
DB_HOST=192.168.1.100 DB_PORT=5433 bash scripts/archive-project.sh my-project
```

---

### list-archives.sh - 查看归档历史

**用法**：
```bash
bash scripts/list-archives.sh [--detailed]
```

**参数**：
- `--detailed` 或 `-d`：显示详细信息（包括文件路径）

**输出字段**：
| 字段 | 说明 |
|------|------|
| 项目ID | 归档的项目标识符 |
| 任务数 | 归档的任务数量 |
| 文件大小 | 归档文件大小 |
| 归档时间 | 归档操作的时间 |

---

## 常见问题

### Q1: 归档后数据还能恢复吗？

**可以**。归档文件是 CSV 格式的压缩包，可以通过以下方式恢复：

```bash
# 解压归档文件
tar -xzf /home/wen/archives/projects/<project_id>_<timestamp>.tar.gz -C /tmp/

# 查看解压后的 CSV 文件
head /tmp/<project_id>_<timestamp>.csv

# 恢复到数据库（需要手动处理）
# 注意：需要处理 UUID 和外键约束
```

### Q2: 归档时提示"项目有活跃任务"怎么办？

**建议**：
1. 等待活跃任务完成
2. 或取消不需要的任务
3. 或强制归档（输入 y 确认）

```sql
-- 取消任务
UPDATE parallel_tasks 
SET status = 'cancelled' 
WHERE project_id = 'xxx' AND status IN ('pending', 'queued');
```

### Q3: 如何为现有任务分配项目 ID？

```sql
-- 按时间范围分配
UPDATE parallel_tasks 
SET project_id = 'memory-hub-phase1'
WHERE created_at >= '2026-03-01' AND created_at < '2026-03-15';

-- 按任务类型分配
UPDATE parallel_tasks 
SET project_id = 'search-tasks'
WHERE task_type = 'search';

-- 按智能体分配
UPDATE parallel_tasks 
SET project_id = 'xiaoso-tasks'
WHERE agent_name = '小搜';
```

### Q4: 归档文件保存在哪里？

默认保存在 `/home/wen/archives/projects/`，可以通过环境变量修改：

```bash
ARCHIVE_DIR=/data/archives bash scripts/archive-project.sh my-project
```

### Q5: 如何查看归档文件的内容？

```bash
# 列出归档文件内容
tar -tzf /home/wen/archives/projects/<file>.tar.gz

# 解压到临时目录查看
tar -xzf /home/wen/archives/projects/<file>.tar.gz -C /tmp/
head /tmp/*.csv
```

### Q6: 归档会影响正在运行的任务吗？

**不会**。归档脚本会：
1. 检查活跃任务
2. 提示确认
3. 只删除已归档的任务

但建议在系统空闲时执行归档操作。

---

## 最佳实践

### 1. 项目命名规范

推荐使用有意义的命名：
```
<产品>-<阶段>-<版本>
例如：memory-hub-phase1-v1.0
```

### 2. 归档时机

建议在以下时机归档：
- ✅ 项目阶段完成
- ✅ 版本发布后
- ✅ 季度/年度总结时
- ✅ 数据库存储压力大时

### 3. 归档前检查

```bash
# 1. 查看项目状态
bash scripts/list-projects.sh --verbose

# 2. 模拟归档
bash scripts/archive-project.sh <project_id> --dry-run

# 3. 确认无误后正式归档
bash scripts/archive-project.sh <project_id>
```

### 4. 定期清理

```bash
# 查看归档历史
bash scripts/list-archives.sh

# 删除过期的归档文件（根据需要）
# 注意：删除前确保有备份
```

### 5. 备份归档文件

```bash
# 备份到远程存储
rsync -avz /home/wen/archives/projects/ user@backup-server:/backups/memory-hub/

# 或上传到云存储
aws s3 sync /home/wen/archives/projects/ s3://my-bucket/archives/
```

---

## 附录

### 文件结构

```
/home/wen/projects/memory-hub/
├── database/
│   ├── 01_parallel_tasks_schema.sql
│   ├── 02_parallel_tasks_functions.sql
│   └── 03_add_project_id.sql          # 新增
└── scripts/
    ├── archive-project.sh              # 新增
    ├── list-projects.sh                # 新增
    ├── list-archives.sh                # 新增
    └── ARCHIVE_GUIDE.md                # 新增

/home/wen/archives/projects/            # 归档目录
├── memory-hub-phase1_20260316_120000.tar.gz
├── memory-hub-phase1_20260316_120000.csv (临时，归档后删除)
└── ...
```

### 数据库表

**archive_history 表**：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| project_id | VARCHAR(100) | 项目 ID |
| archive_file | VARCHAR(500) | 归档文件路径 |
| task_count | INTEGER | 归档任务数 |
| file_size | BIGINT | 文件大小（字节） |
| archived_at | TIMESTAMP | 归档时间 |
| archived_by | VARCHAR(255) | 归档方式 |

**project_statistics 视图**：
显示每个项目的任务统计信息。

---

_使用指南完成！有问题随时找小码。_