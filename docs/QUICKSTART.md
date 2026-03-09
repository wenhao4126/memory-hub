# Memory Hub 快速开始指南 🚀

> **5 分钟上手，让智能体拥有长期记忆**

---

## ⏱️ 时间规划

| 步骤 | 内容 | 时间 |
|------|------|------|
| 1 | 启动服务 | 2 分钟 |
| 2 | 创建智能体 | 1 分钟 |
| 3 | 创建记忆 | 1 分钟 |
| 4 | 测试搜索 | 1 分钟 |
| **总计** | | **5 分钟** |

---

## 第一步：启动服务（2 分钟）

### 1.1 进入项目目录

```bash
cd /home/wen/projects/memory-hub
```

### 1.2 一键启动

```bash
./scripts/start.sh start
```

**等待输出：**

```
🚀 启动多智能体记忆中枢...

✅ 数据库启动成功
✅ API 服务启动成功
✅ pgAdmin 启动成功

📚 API 文档：http://localhost:8000/docs
🔌 API 接口：http://localhost:8000/api/v1
🛠️ pgAdmin: http://localhost:5050
```

### 1.3 验证服务

```bash
curl http://localhost:8000/api/v1/health
```

**成功响应：**

```json
{
  "status": "ok",
  "database": "connected",
  "version": "0.1.0"
}
```

✅ **完成！** 服务已启动，继续下一步。

---

## 第二步：创建智能体（1 分钟）

### 方式 1：使用 Swagger UI（推荐新手）

1. 打开浏览器，访问：http://localhost:8000/docs
2. 找到 `POST /api/v1/agents` 接口
3. 点击 **"Try it out"**
4. 填写请求体：

```json
{
  "name": "小笔",
  "description": "文案专家，擅长写文章",
  "capabilities": ["写作", "翻译", "润色"],
  "metadata": {
    "team_id": "003"
  }
}
```

5. 点击 **"Execute"**
6. 看到响应：

```json
{
  "message": "智能体创建成功，ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

7. **复制 agent_id**，下一步要用

### 方式 2：使用 cURL

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

✅ **完成！** 智能体已创建，记住 agent_id。

---

## 第三步：创建记忆（1 分钟）

### 方式 1：使用 Swagger UI

1. 在 Swagger UI 中找到 `POST /api/v1/memories` 接口
2. 点击 **"Try it out"**
3. 填写请求体（**替换为你的 agent_id**）：

```json
{
  "agent_id": "你的 agent_id",
  "content": "用户喜欢简洁的回答，讨厌废话",
  "memory_type": "preference",
  "importance": 0.8,
  "tags": ["用户偏好", "沟通风格"]
}
```

4. 点击 **"Execute"**
5. 看到响应：

```json
{
  "message": "记忆创建成功，ID: 660e8400-e29b-41d4-a716-446655440001"
}
```

### 方式 2：使用 cURL

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "你的 agent_id",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好", "沟通风格"]
  }'
```

✅ **完成！** 记忆已创建，继续下一步测试搜索。

---

## 第四步：测试搜索（1 分钟）

### 测试语义搜索

**神奇之处：** 即使查询词和记忆内容不一样，也能搜到！

### 方式 1：使用 Swagger UI

1. 在 Swagger UI 中找到 `POST /api/v1/memories/search/text` 接口
2. 点击 **"Try it out"**
3. 填写请求体：

```json
{
  "query": "用户喜欢什么？",
  "match_count": 5
}
```

4. 点击 **"Execute"**
5. 看到响应：

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "content": "用户喜欢简洁的回答，讨厌废话",
    "similarity": 0.92,
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["用户偏好", "沟通风格"]
  }
]
```

**相似度 0.92** 表示非常相关！🎉

### 方式 2：使用 cURL

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户喜欢什么？",
    "match_count": 5
  }'
```

✅ **完成！** 恭喜你已经掌握了 Memory Hub 的核心功能！

---

## 🎓 进阶使用

### 测试增强对话（核心功能）

这是 Memory Hub 最强大的功能：**让 AI 基于记忆进行个性化对话**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "你的 agent_id",
    "session_id": "test_001",
    "user_message": "你好，帮我写个文案",
    "use_memory": true,
    "use_history": true,
    "auto_extract": true
  }'
```

**AI 会自动：**
1. 检索记忆（知道你喜欢简洁）
2. 生成个性化回复（用简洁风格）
3. 记录对话
4. 提取新记忆

---

## 📚 下一步

完成快速开始后，你可以：

### 1. 阅读详细文档

- 📖 [用户文档](USER_GUIDE.md) - 详细使用说明
- 🏗️ [架构文档](ARCHITECTURE.md) - 系统设计详解
- 🔌 [API 文档](API.md) - 完整 API 参考

### 2. 尝试更多功能

- 创建多个智能体（小搜、小码、小笔...）
- 创建不同类型的记忆（事实、偏好、技能、经验）
- 测试智能遗忘（清理过期记忆）
- 多智能体记忆共享

### 3. 集成到你的项目

- 使用 Python SDK 调用 API
- 在智能体项目中集成 Memory Hub
- 开发 Web 管理界面

---

## 🐛 遇到问题？

### 问题 1：服务启动失败

**错误：** `Address already in use`

**解决：**

```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改端口
vim .env  # 修改 API_PORT=8001
```

### 问题 2：Docker 权限问题

**错误：** `permission denied`

**解决：**

```bash
# 使用 sudo
sudo ./scripts/start.sh start

# 或将用户加入 docker 组
sudo usermod -aG docker $USER
# 重新登录生效
```

### 问题 3：找不到记忆

**可能原因：**
- agent_id 不正确
- 记忆还没创建成功

**检查：**

```bash
# 列出所有智能体
curl http://localhost:8000/api/v1/agents

# 列出智能体的记忆
curl http://localhost:8000/api/v1/agents/你的 agent_id/memories
```

---

## 💡 小贴士

### 1. 使用 Swagger UI 最方便

对于新手，**强烈推荐**使用 Swagger UI（http://localhost:8000/docs）：
- 可视化界面
- 自动填充示例
- 一键测试
- 实时查看响应

### 2. 保存你的 agent_id

创建智能体后，**务必保存 agent_id**，后续所有操作都需要它。

建议记录：
```
智能体名称：小笔
Agent ID: 550e8400-e29b-41d4-a716-446655440000
创建时间：2026-03-09
```

### 3. 记忆类型选择

| 场景 | 推荐类型 |
|------|---------|
| 用户基本信息 | fact（事实） |
| 用户喜好 | preference（偏好） |
| 能力标签 | skill（技能） |
| 历史事件 | experience（经验） |

### 4. 重要性分数

- **0.8-1.0**：非常重要（如用户核心偏好）
- **0.5-0.8**：一般重要（如普通事实）
- **0.0-0.5**：不太重要（如临时信息）

---

## 🎉 恭喜完成！

你已经完成了 Memory Hub 的快速开始指南！

**现在你可以：**
- ✅ 启动和管理服务
- ✅ 创建智能体
- ✅ 创建和管理记忆
- ✅ 使用语义搜索
- ✅ 测试增强对话

**开始构建你的智能应用吧！** 🚀

---

*Memory Hub v0.1.0 - 2026.03.09*
