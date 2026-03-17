# Memory Hub 智能体自动连接机制

> 让所有智能体（傻妞和 8 个手下）自动连接到 Memory Hub，实现记忆检索和存储的自动化。

## 🎯 概述

Memory Hub 作为**唯一长期记忆存储**，为所有智能体提供：

- **启动时自动检索**：智能体启动时，自动检索相关记忆，注入到任务上下文
- **完成后自动存储**：智能体完成任务后，自动提取关键信息存储为记忆
- **智能体注册管理**：统一管理所有智能体的身份信息

## ⚠️ 重要：MEMORY.md 已废弃

**OpenClaw 的 MEMORY.md 文件已废弃**，仅作为历史备份保留。

### 为什么废弃 MEMORY.md？

| 对比项 | MEMORY.md | Memory Hub |
|--------|-----------|------------|
| 存储方式 | 文件 | 数据库 |
| 语义搜索 | ❌ 仅关键词 | ✅ 向量搜索 |
| 多智能体共享 | ❌ 每个独立 | ✅ 统一管理 |
| 自动分类 | ❌ 手动 | ✅ 自动路由 |
| 智能遗忘 | ❌ 无 | ✅ 自动清理 |

### 迁移脚本

使用 `scripts/migrate-memory-md-to-hub.sh` 将 MEMORY.md 内容迁移到 Memory Hub：

```bash
# 预览模式（不实际存储）
./scripts/migrate-memory-md-to-hub.sh --dry-run

# 执行迁移
./scripts/migrate-memory-md-to-hub.sh

# 指定智能体
./scripts/migrate-memory-md-to-hub.sh --agent-name "傻妞"
```

## 📦 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    傻妞任务派发流程                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ on-agent-start│   │ sessions_spawn│   │on-agent-complete│
│   (检索记忆)   │ → │   (派发任务)   │ → │   (存储记忆)   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   ┌─────────────────┐
                   │   Memory Hub    │
                   │  (记忆中枢 API)  │
                   └─────────────────┘
```

### 1. 智能体注册脚本

**文件**: `scripts/register-agent.sh`

**功能**: 将所有智能体注册到 Memory Hub，生成唯一 ID

**用法**:
```bash
# 注册所有智能体
./scripts/register-agent.sh

# 强制重新注册
./scripts/register-agent.sh --force

# 列出已注册的智能体
./scripts/register-agent.sh --list

# 显示本地注册表
./scripts/register-agent.sh --registry
```

**注册的智能体**:
| 名称 | 专长 | Agent ID |
|------|------|----------|
| 傻妞 | CEO 和总管家 | team-shaniu |
| 小搜 | 信息采集专家 | team-researcher |
| 小写 | 文案撰写专家 | team-writer |
| 小码 | 代码开发专家 | team-coder |
| 小审 | 质量审核专家 | team-reviewer |
| 小析 | 数据分析专家 | team-analyst |
| 小览 | 浏览器操作专家 | team-browser |
| 小图 | 视觉设计专家 | team-designer |
| 小排 | 内容排版专家 | team-layout |

### 2. 启动 Hook

**文件**: `hooks/on-agent-start.sh`

**功能**: 智能体启动时，从 Memory Hub 检索相关记忆

**用法**:
```bash
# 基本用法
./hooks/on-agent-start.sh "小搜"

# 注入到任务文件
./hooks/on-agent-start.sh "小搜" /path/to/TASK_CURRENT.md
```

**工作流程**:
1. 根据智能体名称查找 ID
2. 调用 Memory Hub API 检索相关记忆
3. 格式化记忆内容
4. 可选：注入到任务文件

**输出示例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🧠 Memory Hub - 智能体启动记忆检索
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 智能体 ID: 550e8400-e29b-41d4-a716-446655440000

ℹ️  检索关键词: 重要记忆 工作经验 用户偏好

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🧠 记忆中枢检索结果

### 📌 experience

用户喜欢简洁的回答，讨厌废话

_重要性: 0.8 | 访问: 5 次_

### 📌 preference

用户习惯用飞书沟通

_重要性: 0.7 | 访问: 3 次_
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 记忆检索完成
```

### 3. 完成 Hook

**文件**: `hooks/on-agent-complete.sh`

**功能**: 智能体完成任务后，自动存储记忆

**用法**:
```bash
# 基本用法
./hooks/on-agent-complete.sh "小搜" "完成搜索任务，找到了5篇相关文章"

# 指定记忆类型和重要性
./hooks/on-agent-complete.sh "小码" "修复了登录bug" experience 0.9

# 存储用户偏好
./hooks/on-agent-complete.sh "小写" "用户喜欢简洁的文案风格" preference 0.8
```

**记忆类型**:
- `fact`: 事实（如："用户叫憨货，住在上海"）
- `preference`: 偏好（如："喜欢简洁的回答，讨厌废话"）
- `skill`: 技能（如："会写 Python 代码，擅长数据分析"）
- `experience`: 经验（如："上次用户遇到问题，用方案 A 解决了"）

**工作流程**:
1. 根据智能体名称查找 ID
2. 提取关键词标签
3. 调用 Memory Hub API 存储记忆
4. 自动路由到 private 或 shared 表

**输出示例**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  💾 Memory Hub - 智能体完成记忆存储
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 智能体 ID: 550e8400-e29b-41d4-a716-446655440000

ℹ️  任务结果:
完成搜索任务，找到了5篇相关文章

ℹ️  记忆类型: experience
ℹ️  重要性: 0.7
ℹ️  标签: 完成 搜索 调研 2026-03-17

✅ 记忆存储成功！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  记忆 ID:  660e8400-e29b-41d4-a716-446655440001
  存储表:   private
  类型:     experience
  重要性:   0.7
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 任务完成记忆已保存到 Memory Hub
```

## 🔄 集成到傻妞任务派发流程

### 方式一：修改 SOUL.md（推荐）

在 `~/.openclaw/workspace/SOUL.md` 中添加记忆检索流程：

```markdown
### 任务派发流程（带 Memory Hub）

1. **憨货给任务** → 傻妞拆解
2. **检索记忆** → 调用 `hooks/on-agent-start.sh`
3. **创建任务卡片** → 注入记忆到 TASK_CURRENT.md
4. **派发任务** → spawn 手下执行
5. **存储记忆** → 调用 `hooks/on-agent-complete.sh`
6. **傻妞审核** → 交付憨货
```

### 方式二：修改任务派发脚本

在傻妞的任务派发逻辑中集成 Hook：

```bash
#!/bin/bash
# 示例：派发任务给小搜

# 1. 检索记忆
MEMORY_HUB_ROOT="/home/wen/projects/memory-hub"
TASK_FILE="/path/to/project/TASK_CURRENT.md"

$MEMORY_HUB_ROOT/hooks/on-agent-start.sh "小搜" "$TASK_FILE"

# 2. 派发任务
sessions_spawn \
  --agentId team-researcher \
  --cwd /path/to/workspace \
  --task "$(cat $TASK_FILE)"

# 3. 任务完成后存储记忆
# 在任务完成的回调中调用
$MEMORY_HUB_ROOT/hooks/on-agent-complete.sh "小搜" "$TASK_RESULT"
```

### 方式三：使用数据库持久化（小码专用）

小码使用 `parallel_tasks` 数据库表持久化任务，已集成 Memory Hub：

```sql
-- parallel_tasks 表结构
CREATE TABLE parallel_tasks (
    id SERIAL PRIMARY KEY,
    task TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    agent_id TEXT,
    result TEXT,
    memory_id TEXT,  -- 新增：关联的记忆 ID
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

**小码池工作流程**:
1. 轮询 `parallel_tasks` 表抢任务
2. 启动时调用 `on-agent-start.sh` 检索记忆
3. 执行任务
4. 完成后调用 `on-agent-complete.sh` 存储记忆
5. 更新任务状态和 `memory_id`

## 📁 文件结构

```
memory-hub/
├── scripts/
│   └── register-agent.sh       # 智能体注册脚本
├── hooks/
│   ├── on-agent-start.sh       # 启动时检索记忆
│   └── on-agent-complete.sh    # 完成后存储记忆
├── data/
│   └── agent-registry.json     # 本地智能体注册表
└── docs/
    └── agent-auto-connect/
        └── README.md           # 本文档
```

## 🧪 测试验证

### 1. 运行测试脚本

```bash
cd /home/wen/projects/memory-hub

# 运行完整测试
./scripts/test-agent-auto-connect.sh
```

### 2. 手动测试

```bash
# 1. 确保 Memory Hub 启动
./scripts/start.sh status

# 2. 注册智能体
./scripts/register-agent.sh

# 3. 测试检索记忆
./hooks/on-agent-start.sh "小搜"

# 4. 测试存储记忆
./hooks/on-agent-complete.sh "小搜" "这是一个测试记忆" experience 0.8

# 5. 再次检索，验证记忆已存储
./hooks/on-agent-start.sh "小搜"
```

## 🔧 配置

### 环境变量

```bash
# Memory Hub API 地址
export MEMORY_HUB_API="http://localhost:8000/api/v1"

# 本地注册表路径
export MEMORY_HUB_REGISTRY="/home/wen/projects/memory-hub/data/agent-registry.json"
```

### 自定义配置

修改 `scripts/register-agent.sh` 中的 `AGENTS` 数组，添加新的智能体配置：

```bash
["新智能体"]="{
    \"name\": \"新智能体\",
    \"description\": \"智能体描述\",
    \"capabilities\": [\"能力1\", \"能力2\"],
    \"metadata\": {
        \"workspace\": \"$HOME/.openclaw/workspace-team-xxx/\",
        \"agent_id\": \"team-xxx\",
        \"role\": \"worker\",
        \"emoji\": \"🆕\"
    }
}"
```

## 📊 API 参考

### 注册智能体

```bash
POST /api/v1/agents
Content-Type: application/json

{
    "name": "小搜",
    "description": "信息采集专家",
    "capabilities": ["搜索", "调研", "收集"],
    "metadata": {
        "workspace": "~/.openclaw/workspace-team-researcher/",
        "agent_id": "team-researcher"
    }
}
```

### 检索记忆

```bash
POST /api/v1/memories/search/text
Content-Type: application/json

{
    "query": "重要记忆",
    "agent_id": "agent-uuid",
    "match_count": 10
}
```

### 存储记忆

```bash
POST /api/v1/memories
Content-Type: application/json

{
    "agent_id": "agent-uuid",
    "content": "记忆内容",
    "memory_type": "experience",
    "importance": 0.8,
    "tags": ["标签1", "标签2"],
    "auto_route": true
}
```

## ❓ 常见问题

### Q: 记忆检索失败怎么办？

A: 检查以下几点：
1. Memory Hub API 是否启动：`curl http://localhost:8000/api/v1/health`
2. 智能体是否已注册：`./scripts/register-agent.sh --list`
3. 智能体是否有记忆：`curl http://localhost:8000/api/v1/agents/{agent_id}/memories`

### Q: 如何清除测试记忆？

A: 调用删除 API：
```bash
curl -X DELETE "http://localhost:8000/api/v1/memories/{memory_id}"
```

### Q: 如何批量注册智能体？

A: 直接运行注册脚本：
```bash
./scripts/register-agent.sh
```

### Q: 记忆会存储到哪个表？

A: 使用 `auto_route: true`，系统会自动判断：
- **private** 表：私人记忆（密码、习惯、偏好等）
- **shared** 表：共同记忆（经验、知识、规范等）

---

## 📝 更新日志

### v1.1.0 (2026-03-17)

- ✅ **MEMORY.md 已废弃**，仅作为历史备份
- ✅ 创建迁移脚本 `migrate-memory-md-to-hub.sh`
- ✅ Memory Hub 是唯一的长期记忆存储
- ✅ 更新 SOUL.md 集成 Memory Hub

### v1.0.0 (2026-03-17)

- ✅ 创建智能体注册脚本 `register-agent.sh`
- ✅ 创建启动 Hook `on-agent-start.sh`
- ✅ 创建完成 Hook `on-agent-complete.sh`
- ✅ 支持注册 9 个智能体（傻妞 + 8 个手下）
- ✅ 支持自动检索和存储记忆
- ✅ 支持记忆缓存（5 分钟有效期）
- ✅ 支持智能标签提取
- ✅ 完善的错误处理和日志输出

---

*文档作者: 小码 💻*
*最后更新: 2026-03-17*