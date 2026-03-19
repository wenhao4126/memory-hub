# Memory Hub 5 分钟快速入门教程 ⚡

> 本教程目标：5 分钟内让 Memory Hub 跑起来，完成第一次带记忆的对话

---

## 🎯 教程概览

```
步骤 1: 安装（2 分钟）
步骤 2: 启动（1 分钟）
步骤 3: 创建智能体（1 分钟）
步骤 4: 创建记忆（1 分钟）
步骤 5: 测试对话（1 分钟）
总计：6 分钟（稍微超时了😄）
```

---

## 步骤 1: 安装 Memory Hub

### 方式一：一键安装脚本（推荐）

```bash
# 执行安装脚本
curl -fsSL https://raw.githubusercontent.com/wen41/memory-hub/master/scripts/install.sh | bash

# 等待安装完成（约 30 秒）
# 安装过程会：
# - 安装 Node.js 依赖
# - 创建配置文件
# - 初始化数据库
```

**预期输出：**
```
✅ Memory Hub 安装完成！
版本：1.0.0
配置文件：~/.memory-hub/config.yaml
数据库：~/.memory-hub/data/

下一步：memory-hub start
```

### 方式二：Docker 部署

```bash
# 克隆项目
git clone https://github.com/wen41/memory-hub.git
cd memory-hub

# 启动 Docker 容器
docker-compose up -d

# 验证安装
curl http://localhost:8000/api/v1/health
```

**预期输出：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "uptime": "00:00:15"
}
```

---

## 步骤 2: 启动服务

```bash
# 启动 Memory Hub
memory-hub start

# 或者指定端口
memory-hub start -p 8080
```

**预期输出：**
```
🚀 Memory Hub 启动中...
📦 加载配置文件
🔗 连接数据库
🧠 初始化向量搜索
✅ 服务就绪！

API: http://localhost:8000
文档：http://localhost:8000/docs
日志：memory-hub logs -f
```

**验证服务：**
```bash
# 新开一个终端
curl http://localhost:8000/api/v1/health
```

---

## 步骤 3: 创建你的第一个智能体

```bash
# 创建智能体 API 调用
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔",
    "description": "文案写作助手",
    "capabilities": ["写作", "翻译", "润色"]
  }'
```

**预期输出：**
```json
{
  "id": "agent_abc123",
  "name": "小笔",
  "description": "文案写作助手",
  "capabilities": ["写作", "翻译", "润色"],
  "created_at": "2026-03-19T19:00:00Z",
  "memory_count": 0
}
```

**记住这个 `id`，后面要用！**

---

## 步骤 4: 创建记忆

现在给这个智能体添加一些记忆：

### 记忆 1: 用户偏好

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "memory_type": "preference",
    "importance": 0.9,
    "tags": ["用户偏好", "沟通风格"]
  }'
```

### 记忆 2: 用户信息

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "content": "用户是开发者，在北京工作",
    "memory_type": "fact",
    "importance": 0.7,
    "tags": ["用户信息", "职业"]
  }'
```

### 记忆 3: 项目信息

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "content": "用户正在开发 Memory Hub 项目",
    "memory_type": "fact",
    "importance": 0.8,
    "tags": ["项目", "工作"]
  }'
```

**验证记忆创建成功：**
```bash
# 列出所有记忆
curl http://localhost:8000/api/v1/agents/agent_abc123/memories
```

---

## 步骤 5: 测试带记忆的对话

### 测试 1: 普通对话

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "user_message": "你好，介绍一下你自己",
    "use_memory": false,
    "use_history": false
  }'
```

**预期输出（不使用记忆）：**
```json
{
  "response": "你好！我是小笔，一个文案写作助手...",
  "memory_used": false
}
```

### 测试 2: 带记忆的对话

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "user_message": "你好，介绍一下你自己",
    "use_memory": true,
    "use_history": true
  }'
```

**预期输出（使用记忆）：**
```json
{
  "response": "你好！我是小笔，你的文案写作助手。知道你喜欢简洁的回答，我就长话短说：我能帮你写作、翻译、润色文案。",
  "memory_used": true,
  "memories_found": [
    "用户喜欢简洁的回答，讨厌废话",
    "用户正在开发 Memory Hub 项目"
  ]
}
```

**看到区别了吗？** 🎉

带记忆的回复：
- ✅ 提到了用户的偏好（简洁）
- ✅ 回复本身就很简洁
- ✅ 更个性化

---

## 步骤 6: 测试语义搜索

Memory Hub 的核心是语义搜索，不依赖关键词。

### 搜索测试 1: 语义匹配

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "query": "用户喜欢什么样的沟通方式？",
    "match_count": 5
  }'
```

**预期输出：**
```json
{
  "results": [
    {
      "content": "用户喜欢简洁的回答，讨厌废话",
      "similarity": 0.89,
      "memory_type": "preference"
    }
  ]
}
```

**注意：** 查询里没有"简洁"这个词，但仍然匹配到了！这就是语义搜索的威力。

### 搜索测试 2: 模糊匹配

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "query": "他在做什么项目？",
    "match_count": 5
  }'
```

**预期输出：**
```json
{
  "results": [
    {
      "content": "用户正在开发 Memory Hub 项目",
      "similarity": 0.85,
      "memory_type": "fact"
    }
  ]
}
```

**注意：** 查询用"他"，记忆里是"用户"，仍然匹配成功！

---

## 步骤 7: 查看 Web UI（可选）

Memory Hub 提供可视化管理界面：

```bash
# 浏览器打开
open http://localhost:8000/dashboard
```

**功能：**
- 📊 查看智能体列表
- 🧠 浏览和管理记忆
- 🔍 测试语义搜索
- 📈 查看性能指标

---

## 🎓 进阶使用

### 批量导入记忆

```bash
# 使用批量导入 API
curl -X POST http://localhost:8000/api/v1/memories/batch \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "memories": [
      {"content": "...", "type": "preference", "importance": 0.8},
      {"content": "...", "type": "fact", "importance": 0.7},
      {"content": "...", "type": "experience", "importance": 0.9}
    ]
  }'
```

### 更新记忆

```bash
# 更新记忆的重要性
curl -X PATCH http://localhost:8000/api/v1/memories/memory_123 \
  -H "Content-Type: application/json" \
  -d '{
    "importance": 0.95
  }'
```

### 删除记忆

```bash
# 删除单条记忆
curl -X DELETE http://localhost:8000/api/v1/memories/memory_123

# 清空所有记忆
curl -X DELETE http://localhost:8000/api/v1/agents/agent_abc123/memories
```

---

## 🛠️ 常用命令速查

```bash
# 启动服务
memory-hub start

# 停止服务
memory-hub stop

# 查看状态
memory-hub status

# 查看日志
memory-hub logs -f

# 重启服务
memory-hub restart

# 查看帮助
memory-hub --help
```

---

## 📚 下一步学习

完成本教程后，你可以：

1. **阅读完整文档**
   - [API 参考文档](../docs/API.md)
   - [使用指南](../docs/USER_GUIDE.md)
   - [部署指南](../docs/DEPLOYMENT.md)

2. **查看示例代码**
   - [examples/](../examples/) 目录

3. **集成到你的项目**
   - [SDK 使用](../sdk/)
   - [技能集成](../skills/)

4. **参与贡献**
   - 提 Issue
   - 提 PR
   - 完善文档

---

## 🐛 遇到问题？

### 常见问题

**Q: 端口被占用**
```bash
# 查看占用进程
lsof -i :8000

# 或用其他端口
memory-hub start -p 8080
```

**Q: 数据库连接失败**
```bash
# 重启数据库
docker-compose restart db

# 查看数据库日志
docker-compose logs db
```

**Q: 找不到记忆**
- 检查 `agent_id` 是否正确
- 确认记忆已创建成功
- 查看日志排查问题

### 获取帮助

- 📖 [故障排查文档](../docs/TROUBLESHOOTING.md)
- 💬 GitHub Issues
- 📧 邮件列表

---

## ✅ 教程检查清单

完成本教程后，你应该能够：

- [ ] 成功安装 Memory Hub
- [ ] 启动服务并验证健康状态
- [ ] 创建智能体
- [ ] 创建记忆（偏好、事实、经验）
- [ ] 进行带记忆的对话
- [ ] 测试语义搜索
- [ ] 查看 Web UI（可选）
- [ ] 使用常用 CLI 命令

**全部完成？恭喜你成为 Memory Hub 用户！🎉**

---

*教程版本：1.0.0 | 最后更新：2026-03-19*
