# Memory Hub - 多智能体记忆中枢 🧠

<p align="center">
  <strong>让智能体拥有长期记忆，对话更懂你</strong>
</p>

<p align="center">
  <a href="https://github.com/wen41/memory-hub">
    <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
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
```

---

## 🚀 快速开始

### 方式一：一键安装（推荐）

```bash
# 一键安装脚本
curl -fsSL https://raw.githubusercontent.com/wen41/memory-hub/master/scripts/install.sh | bash

# 初始化配置
memory-hub init

# 启动服务
memory-hub start
```

### 方式二：npm 安装

```bash
# 全局安装
npm install -g memory-hub

# 初始化
memory-hub init

# 启动
memory-hub start
```

### 方式三：Docker 部署（生产环境）

```bash
# 克隆项目
git clone https://github.com/wen41/memory-hub.git
cd memory-hub

# 配置环境变量
cp .env.example .env
nano .env

# 一键启动
docker-compose up -d

# 验证安装
curl http://localhost:8000/api/v1/health
```

---

## ✨ 功能特性

### 🧠 向量搜索
- 基于 pgvector 的语义搜索
- 支持相似度匹配，不依赖关键词
- 毫秒级响应速度

### 🤖 自动记忆提取
- 从对话中自动提取关键信息
- 智能分类：偏好、事实、经验
- 自动打标签，方便检索

### 👥 多智能体支持
- 一个中心管理多个 AI 助手
- 记忆共享，信息互通
- 独立命名空间，互不干扰

### 🔌 简单易用的 API
- RESTful 接口设计
- 完整的 Swagger 文档
- 支持流式响应

### 📊 可视化管理
- Web UI 管理界面
- 实时日志查看
- 性能监控面板

---

## 📋 配置说明

### 环境变量（.env）

```ini
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/memory_hub

# 连接池配置
DB_POOL_MIN=5
DB_POOL_MAX=20

# 任务配置
DEFAULT_LOCK_DURATION=30
DEFAULT_TIMEOUT=30
DEFAULT_MAX_RETRIES=3

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=false
```

### 配置文件（config.yaml）

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  mode: "development"

database:
  connection_mode: "url"
  pool:
    min: 5
    max: 20

vector:
  dimensions: 1536
  similarity_threshold: 0.7

logging:
  level: "INFO"
  format: "text"
```

### API 密钥配置

```ini
# .env 文件
DASHSCOPE_API_KEY=your_api_key_here
MEMORY_HUB_API_KEY=your_secret_key
```

---

## 🛠️ 常用命令

### CLI 命令

```bash
# 初始化配置
memory-hub init

# 启动服务
memory-hub start
memory-hub start -p 8080  # 指定端口

# 停止服务
memory-hub stop

# 查看状态
memory-hub status

# 查看日志
memory-hub logs
memory-hub logs -n 100    # 显示 100 行
memory-hub logs -f        # 实时跟踪
```

### Docker 命令

```bash
# 启动所有服务
docker-compose up -d

# 停止服务
docker-compose stop

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 完全重置（删除数据）
docker-compose down -v
```

---

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [📦 安装指南](docs/INSTALL.md) | 详细的安装步骤和配置 |
| [⚡ 快速入门](docs/QUICKSTART.md) | 5 分钟上手教程 |
| [🔌 API 参考](docs/API.md) | 完整的 API 文档 |
| [📚 使用指南](docs/USER_GUIDE.md) | 详细使用说明 |
| [🏗️ 系统架构](docs/ARCHITECTURE.md) | 技术架构详解 |
| [🛠️ CLI 手册](docs/CLI.md) | 命令行工具完整参考 |
| [🚀 部署指南](docs/DEPLOYMENT.md) | 生产环境部署 |

---

## 🐛 故障排查

### 常见问题

#### 1. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改端口
memory-hub start -p 8080
```

#### 2. 数据库连接失败

**错误**: `database connection failed`

**解决**:
```bash
# 检查数据库是否运行
docker-compose ps

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db
```

#### 3. 找不到记忆

**可能原因**:
- agent_id 不正确
- 记忆还没创建成功

**检查**:
```bash
# 列出所有智能体
curl http://localhost:8000/api/v1/agents

# 列出智能体的记忆
curl http://localhost:8000/api/v1/agents/<agent_id>/memories
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/memory-hub.log

# Docker 环境
docker-compose logs -f api

# 查看错误日志
grep ERROR logs/memory-hub.log
```

---

## 💡 示例代码

### 创建智能体

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔",
    "description": "文案专家",
    "capabilities": ["写作", "翻译"]
  }'
```

### 创建记忆

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-id",
    "content": "用户喜欢简洁的回答",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好"]
  }'
```

### 搜索记忆

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户喜欢什么？",
    "match_count": 5
  }'
```

### 带记忆的对话

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-id",
    "user_message": "你好",
    "use_memory": true,
    "use_history": true
  }'
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

```bash
# Fork 项目
git fork https://github.com/wen41/memory-hub

# 克隆到本地
git clone git@github.com:your-username/memory-hub.git

# 创建分支
git checkout -b feature/your-feature

# 提交代码
git commit -m "Add your feature"

# 推送分支
git push origin feature/your-feature
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 基于 [傻妞](https://github.com/wen41/openclaw) 项目开发
- 使用 PostgreSQL + pgvector 提供向量搜索
- 感谢所有贡献者

---

*Memory Hub v1.0.0 - Made with ❤️ by 傻妞 Team*
