<p align="center">
  <img src="docs/images/hero-banner.png" alt="Memory Hub" width="100%">
</p>

<h1 align="center">多智能体记忆中枢</h1>

<p align="center">
  <img src="logo/memory-hub-logo.png" alt="Logo" width="128" height="128">
</p>

<p align="center">
  <strong>让智能体拥有长期记忆，对话更懂你</strong>
</p>

<p align="center">
  <a href="https://github.com/wen41/memory-hub">
    <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </a>
  <a href="docker-compose.yml">
    <img src="https://img.shields.io/badge/docker-ready-brightgreen.svg" alt="Docker">
  </a>
</p>

---

## 🎯 这是什么？

**Memory Hub** 是一个**智能体记忆管理系统**，解决 AI 智能体"记性差"的问题。

### 痛点场景

你有没有遇到过这些情况：

- 🔴 跟 AI 说过的话，下次再问又忘了
- 🔴 每个 AI 助手都是独立记忆，信息不互通
- 🔴 只能关键词搜索，无法理解语义
- 🔴 聊天记录越来越多，找不到重点

### Memory Hub 能做什么？

```
┌─────────────────────────────────────────────────────────┐
│  你：我是憨货，喜欢吐槽风格，讨厌废话                    │
│       ↓ 存储到 Memory Hub                                │
│  下次对话...                                            │
│  AI：憨货你好！给你来个简洁的吐槽风回复 😄               │
│       ↑ 从 Memory Hub 回忆起你的偏好                      │
└─────────────────────────────────────────────────────────┘
```

**核心能力：**

- 🤖 **多智能体管理**：支持多个 AI 助手注册和身份识别
- 💾 **统一记忆存储**：事实、偏好、技能、经验四种记忆类型
- 🔍 **语义搜索**：不是关键词匹配，是理解意思的相似性搜索
- 🔄 **智能遗忘**：自动清理不重要的旧记忆，像人脑一样
- 🌐 **RESTful API**：标准 HTTP 接口，轻松集成到任何项目

---

## 🏗️ 系统架构

<p align="center">
  <img src="docs/images/architecture-diagram.png" alt="Architecture" width="100%">
</p>

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     智能体层                                 │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│   │ 小搜    │  │ 小码    │  │ 小笔    │  │ 小析    │      │
│   │ (搜索)  │  │ (代码)  │  │ (文案)  │  │ (分析)  │      │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘      │
└────────┼────────────┼────────────┼────────────┼────────────┘
         │            │            │            │
         └────────────┴─────┬──────┴────────────┘
                            │ HTTP API
                   ┌────────▼────────┐
                   │   Memory Hub    │
                   │   (FastAPI)     │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   PostgreSQL    │
                   │   + pgvector    │
                   └─────────────────┘
```

### 记忆类型

Memory Hub 支持四种记忆类型：

| 类型 | 英文 | 示例 |
|------|------|------|
| 📌 事实 | fact | "用户叫憨货，住在上海" |
| ❤️ 偏好 | preference | "喜欢简洁的回答，讨厌废话" |
| 🛠️ 技能 | skill | "会写 Python 代码，擅长数据分析" |
| 📖 经验 | experience | "上次用户遇到问题，用方案 A 解决了" |

---

## 📦 项目结构

```
memory-hub/
├── docker-compose.yml      # Docker 编排配置
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略配置
│
├── backend/                # 后端代码
│   ├── Dockerfile          # API 服务镜像
│   ├── app/
│   │   ├── main.py         # FastAPI 应用入口
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据模型
│   │   └── services/       # 业务服务
│   │
│   └── requirements.txt    # Python 依赖
│
├── scripts/                # 脚本
│   ├── start.sh            # 一键启动脚本
│   ├── backup.sh           # 数据库备份脚本
│   └── init-db.sql         # 数据库初始化
│
└── docs/                   # 文档目录
    ├── QUICKSTART.md       # 5 分钟上手指南
    ├── USER_GUIDE.md       # 用户使用手册
    ├── ARCHITECTURE.md     # 架构设计文档
    └── API.md              # API 参考手册
```

---

## 🚀 快速开始

### 前置要求

- ✅ Docker & Docker Compose（必须）
- ✅ Python 3.10+（仅本地开发需要）

### 1️⃣ 克隆项目

```bash
git clone https://github.com/wen41/memory-hub.git
cd memory-hub
```

### 2️⃣ 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（可选，默认配置即可用）
vim .env
```

### 3️⃣ 一键启动

#### 方式一：傻瓜式启动（新手推荐）✨

专为新手设计，自动处理 Docker 权限和环境问题：

```bash
# 进入交互式菜单
./scripts/quick-start.sh

# 或直接启动
./scripts/quick-start.sh start
```

**特色功能：**
- ✅ 自动检查 Docker 安装和权限
- ✅ 自动处理权限问题
- ✅ 自动检查端口占用
- ✅ 自动创建 .env 文件
- ✅ 友好的交互式菜单

#### 方式二：标准启动

```bash
# 一键启动所有服务（数据库 + API + pgAdmin）
./scripts/start.sh start
```

**服务地址：**
- 📚 API 文档：http://localhost:8000/docs
- 🔌 API 接口：http://localhost:8000/api/v1
- 🗄️ 数据库：localhost:5432
- 🛠️ pgAdmin：http://localhost:5050

### 4️⃣ 其他命令

```bash
# 查看服务状态
./scripts/start.sh status

# 查看日志
./scripts/start.sh logs

# 停止服务
./scripts/start.sh stop

# 测试 API
./scripts/start.sh test

# 清理数据（危险⚠️）
./scripts/start.sh clean
```

---

## 💻 使用示例

### 示例 1：创建智能体

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔",
    "description": "文案专家，擅长写文章",
    "capabilities": ["写作", "翻译", "润色"],
    "metadata": {"team_id": "003"}
  }'
```

**响应：**
```json
{
  "message": "智能体创建成功，ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

### 示例 2：创建记忆

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好", "沟通风格"]
  }'
```

### 示例 3：语义搜索记忆

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户喜欢什么样的回答？",
    "limit": 5
  }'
```

**响应：**
```json
[
  {
    "id": "记忆 ID",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "similarity": 0.92,
    "memory_type": "preference",
    "importance": 0.8
  }
]
```

### 示例 4：增强对话（核心功能）🚀

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "session_123",
    "user_message": "你好，帮我写个文案",
    "use_memory": true,
    "use_history": true,
    "auto_extract": true
  }'
```

**工作流程：**
1. 检索相关记忆（向量搜索）
2. 获取对话历史
3. 用 LLM 生成个性化回复
4. 记录对话到数据库
5. 自动提取新记忆

---

## 📚 文档导航

| 文档 | 说明 | 适合人群 |
|------|------|---------|
| [快速开始](docs/QUICKSTART.md) | 5 分钟上手指南 | 新手 |
| [用户文档](docs/USER_GUIDE.md) | 详细使用说明 | 普通用户 |
| [架构文档](docs/ARCHITECTURE.md) | 系统架构设计 | 开发者 |
| [API 文档](docs/API.md) | RESTful API 参考 | 开发者 |

---

## 🗄️ 数据模型

### 智能体（agents）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR | 智能体名称 |
| description | TEXT | 描述 |
| capabilities | TEXT[] | 能力标签 |
| metadata | JSONB | 扩展信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 记忆（memories）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| agent_id | UUID | 所属智能体 |
| content | TEXT | 记忆内容 |
| embedding | vector(1024) | 向量嵌入（text-embedding-v4） |
| memory_type | VARCHAR | 类型：fact/preference/skill/experience |
| importance | FLOAT | 重要性 0-1 |
| access_count | INTEGER | 访问次数 |
| tags | TEXT[] | 标签 |
| created_at | TIMESTAMP | 创建时间 |
| last_accessed | TIMESTAMP | 最后访问时间 |
| expires_at | TIMESTAMP | 过期时间 |

---

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 5432 | 数据库端口 |
| DB_USER | memory_user | 数据库用户 |
| DB_PASSWORD | memory_pass_2026 | 数据库密码 |
| DB_NAME | memory_hub | 数据库名称 |
| API_HOST | 0.0.0.0 | API 监听地址 |
| API_PORT | 8000 | API 端口 |
| API_DEBUG | false | 调试模式 |
| EMBEDDING_MODEL | text-embedding-v4 | 嵌入模型 |
| EMBEDDING_DIMENSION | 1024 | 向量维度 |
| DASHSCOPE_API_KEY | - | 阿里云 DashScope API Key |

### 生产环境部署

⚠️ **部署前必须修改：**

1. `DB_PASSWORD` - 使用强密码
2. `ADMIN_PASSWORD` - 使用强密码
3. `API_DEBUG` - 设置为 `false`
4. 配置防火墙，限制端口访问

---

## 🐳 Docker 命令

### 一键脚本（推荐）

```bash
# 一键启动
./scripts/start.sh start

# 查看状态
./scripts/start.sh status

# 查看日志
./scripts/start.sh logs

# 停止服务
./scripts/start.sh stop

# 测试 API
./scripts/start.sh test
```

### 手动 Docker 命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷（危险⚠️）
docker-compose down -v

# 进入数据库容器
docker exec -it memory-hub-db psql -U memory_user -d memory_hub

# 进入 pgAdmin
# 访问 http://localhost:5050
# 邮箱：admin@memory.hub
# 密码：admin123
```

### 数据备份与恢复

```bash
# 创建备份
./scripts/backup.sh create

# 列出备份
./scripts/backup.sh list

# 恢复备份
./scripts/backup.sh restore

# 清理旧备份（保留最近 5 个）
./scripts/backup.sh clean 5
```

---

## 🧪 测试

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=app --cov-report=term-missing
```

**测试覆盖：**
- ✅ API 端点测试：33 个测试
- ✅ 服务层测试：28 个测试
- ✅ 总覆盖率：77%（核心业务逻辑 >85%）

---

## 📋 开发路线

### 已完成 ✅

- [x] Day 1: 项目目录结构、Docker 环境、数据库
- [x] Day 2: 向量嵌入集成、记忆存储 API、单元测试
- [x] Day 3: 多智能体协作机制、记忆共享 API
- [x] Day 4: 向量搜索功能、监控和日志
- [x] Day 5: 性能优化、文档完善、部署脚本

### 进行中 🚧

- [ ] 知识库管理功能
- [ ] 对话历史管理
- [ ] 自动记忆提取优化

### 计划中 📅

- [ ] Web 管理界面
- [ ] 记忆可视化展示
- [ ] 多租户支持

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加某某功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 作者

- **小码** - *项目开发* - 傻妞管家团队 💻

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能 Web 框架
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL 向量扩展
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库
- [DashScope](https://dashscope.aliyun.com/) - 阿里云通义千问 API

---

> 💡 **小码提示**：有问题随时问憨货或傻妞，代码是给人看的，顺便给机器执行！

---

*多智能体记忆中枢 v0.1.0 - 2026.03.09*
