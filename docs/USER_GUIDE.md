# Memory Hub 用户文档 📚

> **5 分钟上手，让你的智能体拥有长期记忆**

---

## 📖 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [使用指南](#使用指南)
4. [配置说明](#配置说明)
5. [常见问题](#常见问题)

---

## 快速开始

### 第一步：启动服务

```bash
# 进入项目目录
cd /home/wen/projects/memory-hub

# 一键启动（推荐）
./scripts/start.sh start
```

**等待服务启动：**
```
✅ 数据库启动成功
✅ API 服务启动成功
✅ pgAdmin 启动成功

📚 API 文档：http://localhost:8000/docs
🔌 API 接口：http://localhost:8000/api/v1
🛠️ pgAdmin: http://localhost:5050
```

### 第二步：访问 API 文档

打开浏览器，访问：**http://localhost:8000/docs**

你会看到 Swagger UI 界面，所有 API 端点都有详细文档和"Try it out"按钮。

### 第三步：创建第一个智能体

在 Swagger UI 中找到 `POST /api/v1/agents` 接口：

1. 点击 **"Try it out"**
2. 填写请求体：
```json
{
  "name": "小笔",
  "description": "文案专家，擅长写文章和翻译",
  "capabilities": ["写作", "翻译", "润色"],
  "metadata": {
    "team_id": "003",
    "role": "writer"
  }
}
```
3. 点击 **"Execute"**
4. 看到响应：`智能体创建成功，ID: xxx`

### 第四步：创建第一条记忆

找到 `POST /api/v1/memories` 接口：

1. 点击 **"Try it out"**
2. 填写请求体（使用上一步的 agent_id）：
```json
{
  "agent_id": "你的智能体 ID",
  "content": "用户喜欢简洁的回答，讨厌废话",
  "memory_type": "preference",
  "importance": 0.8,
  "tags": ["用户偏好", "沟通风格"]
}
```
3. 点击 **"Execute"**

### 第五步：搜索记忆

找到 `POST /api/v1/memories/search/text` 接口：

1. 点击 **"Try it out"**
2. 填写请求体：
```json
{
  "query": "用户喜欢什么？",
  "match_count": 5
}
```
3. 点击 **"Execute"**

你会看到返回的记忆，即使查询词和记忆内容不完全一样，也能搜索到！

---

## 核心概念

### 什么是智能体（Agent）？

**智能体** 就是 AI 助手的身份标识。

```
例如：
- 小搜：搜索专家
- 小码：程序员
- 小笔：文案写手
- 小析：数据分析师
```

每个智能体有：
- **名称**：如"小笔"
- **描述**：如"文案专家"
- **能力标签**：如 ["写作", "翻译"]
- **元数据**：任意 JSON 对象，存储额外信息

### 什么是记忆（Memory）？

**记忆** 是智能体记住的信息。

#### 四种记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 📌 fact（事实） | 客观信息 | "用户叫憨货，住在上海" |
| ❤️ preference（偏好） | 用户喜好 | "喜欢简洁，讨厌废话" |
| 🛠️ skill（技能） | 能力标签 | "会 Python，擅长数据分析" |
| 📖 experience（经验） | 历史事件 | "上次用方案 A 解决了问题" |

#### 记忆的属性

- **content**：记忆内容（必填）
- **memory_type**：记忆类型（默认 fact）
- **importance**：重要性 0-1（默认 0.5）
- **tags**：标签列表
- **embedding**：向量（自动生成，可选）

### 什么是向量搜索？

**传统搜索**：关键词匹配
```
搜索"喜欢简洁" → 找到包含"喜欢"和"简洁"的记忆
```

**向量搜索**：语义理解
```
搜索"用户喜欢什么？" → 找到"用户喜欢简洁的回答"
（即使没有相同关键词）
```

**原理：**
1. 将文本转换为向量（1024 维数字列表）
2. 计算向量之间的相似度
3. 返回最相似的记忆

---

## 使用指南

### 场景 1：让 AI 记住用户偏好

**需求**：让智能体记住用户的沟通风格偏好。

**步骤：**

1. **创建记忆**
```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "智能体 ID",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好", "沟通风格"]
  }'
```

2. **在对话中使用**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "智能体 ID",
    "session_id": "session_123",
    "user_message": "帮我写个文案",
    "use_memory": true
  }'
```

**结果**：AI 会自动检索记忆，用简洁风格回复。

---

### 场景 2：多智能体共享记忆

**需求**：小搜搜索到的信息，小笔写文案时能用上。

**步骤：**

1. **小搜存储信息**
```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "小搜的 ID",
    "content": "Memory Hub 是一个记忆管理系统，支持向量搜索",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["项目信息", "产品介绍"]
  }'
```

2. **小笔查询信息**
```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Memory Hub 是什么？",
    "match_count": 5
  }'
```

**结果**：小笔可以获取小搜存储的信息。

---

### 场景 3：自动提取记忆

**需求**：对话中自动提取重要信息存储为记忆。

**使用增强对话 API：**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "智能体 ID",
    "session_id": "session_123",
    "user_message": "我是憨货，住在上海，喜欢吐槽风格",
    "auto_extract": true
  }'
```

**工作流程：**
1. AI 回复用户
2. 自动分析对话，提取关键信息
3. 创建新记忆存储到数据库

**自动提取的记忆：**
- "用户叫憨货"
- "用户住在上海"
- "用户喜欢吐槽风格"

---

### 场景 4：管理记忆生命周期

**需求**：清理过期和不重要的记忆。

**使用清理 API：**

```bash
curl -X POST http://localhost:8000/api/v1/memories/cleanup \
  -H "Content-Type: application/json" \
  -d '{
    "days_old": 30,
    "min_importance": 0.3,
    "max_access_count": 3
  }'
```

**清理规则：**
- 创建时间超过 30 天
- 重要性低于 0.3
- 访问次数少于 3 次

**响应：**
```json
{
  "message": "已清理 15 条过期记忆"
}
```

---

## 配置说明

### 基础配置

配置文件：`.env`

```bash
# 数据库配置
DB_USER=memory_user
DB_PASSWORD=你的强密码
DB_NAME=memory_hub
DB_PORT=5432

# API 配置
API_PORT=8000
API_DEBUG=false

# 嵌入模型配置
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024

# DashScope API Key（必须）
DASHSCOPE_API_KEY=你的 API Key
```

### 获取 DashScope API Key

1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通 DashScope 服务
4. 创建 API Key
5. 复制到 `.env` 文件

### CORS 配置（跨域访问）

如果需要从网页访问 API：

```bash
# 允许的来源（多个用逗号分隔）
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 生产环境配置

⚠️ **部署前必须修改：**

```bash
# 1. 使用强密码
DB_PASSWORD=强密码（大小写字母 + 数字 + 特殊字符）
ADMIN_PASSWORD=强密码

# 2. 关闭调试模式
API_DEBUG=false

# 3. 限制 CORS
ALLOWED_ORIGINS=https://yourdomain.com

# 4. 配置防火墙
# 只开放必要端口（8000, 5432）
```

---

## 常见问题

### Q1: 服务启动失败，端口被占用

**错误信息：**
```
Error: Address already in use
```

**解决方案：**

```bash
# 方案 1：查看占用端口的进程
lsof -i :8000

# 方案 2：杀死占用端口的进程
kill -9 <PID>

# 方案 3：修改端口
vim .env  # 修改 API_PORT=8001
```

---

### Q2: 向量搜索返回结果不相关

**可能原因：**

1. **记忆太少**：多创建一些记忆
2. **阈值太高**：降低 `match_threshold`
3. **Embedding API 问题**：检查 API Key

**解决方案：**

```bash
# 降低相似度阈值（默认 0.7）
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你的问题",
    "match_threshold": 0.5,
    "match_count": 10
  }'
```

---

### Q3: 智能体不存在

**错误信息：**
```
智能体不存在：xxx
```

**解决方案：**

1. 检查 agent_id 是否正确（UUID 格式）
2. 先创建智能体：`POST /api/v1/agents`
3. 列出所有智能体确认：`GET /api/v1/agents`

---

### Q4: Docker 权限问题

**错误信息：**
```
permission denied while trying to connect to the Docker daemon socket
```

**解决方案：**

```bash
# 方案 1：使用 sudo
sudo ./scripts/start.sh start

# 方案 2：将用户加入 docker 组
sudo usermod -aG docker $USER
# 重新登录生效
```

---

### Q5: 数据库连接失败

**错误信息：**
```
could not connect to server
```

**解决方案：**

```bash
# 1. 检查数据库是否启动
docker-compose ps

# 2. 查看数据库日志
docker-compose logs postgres

# 3. 检查 .env 配置
cat .env | grep DB_

# 4. 重启服务
./scripts/start.sh restart
```

---

### Q6: 如何备份数据？

```bash
# 创建备份
./scripts/backup.sh create

# 查看备份列表
./scripts/backup.sh list

# 恢复备份
./scripts/backup.sh restore
```

**备份文件位置：**
```
/home/wen/projects/memory-hub/backups/
```

---

### Q7: 如何查看记忆数据？

**方式 1：使用 pgAdmin**

1. 访问 http://localhost:5050
2. 登录：admin@memory.hub / admin123
3. 连接数据库：memory_hub
4. 查看表：agents, memories

**方式 2：使用命令行**

```bash
# 进入数据库容器
docker exec -it memory-hub-db psql -U memory_user -d memory_hub

# 查看所有智能体
SELECT * FROM agents;

# 查看所有记忆
SELECT id, content, memory_type, importance FROM memories;

# 退出
\q
```

---

### Q8: 如何重置所有数据？

⚠️ **警告：此操作会删除所有数据！**

```bash
# 停止服务
./scripts/start.sh stop

# 删除数据卷
docker-compose down -v

# 重新启动
./scripts/start.sh start
```

---

## 下一步

- 📖 阅读 [架构文档](ARCHITECTURE.md) 了解系统设计
- 🔌 阅读 [API 文档](API.md) 查看所有接口
- 💻 开始开发你的应用

---

*Memory Hub v0.1.0 - 2026.03.09*
