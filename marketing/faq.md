# Memory Hub 常见问题解答 (FAQ) ❓

> 常见问题、故障排查、最佳实践合集

---

## 📋 目录

1. [基础问题](#基础问题)
2. [安装部署](#安装部署)
3. [使用问题](#使用问题)
4. [性能优化](#性能优化)
5. [故障排查](#故障排查)
6. [最佳实践](#最佳实践)
7. [安全与隐私](#安全与隐私)
8. [贡献与反馈](#贡献与反馈)

---

## 基础问题

### Q1: Memory Hub 是什么？

**A**: Memory Hub 是一个**智能体记忆管理系统**，解决 AI 智能体"记性差"的问题。

**核心功能**:
- 🧠 向量语义搜索（基于 pgvector）
- 🤖 自动记忆提取
- 👥 多智能体记忆共享
- 🔌 RESTful API

**适用场景**:
- 个人 AI 助手记忆管理
- 客服机器人客户记忆
- 企业知识库管理
- 多智能体系统

---

### Q2: 为什么需要 Memory Hub？

**A**: 因为大模型本身**没有长期记忆**。

**问题场景**:
```
你：我喜欢简洁的回答
AI：好的记住了！

（下次对话）
你：帮我写个文档
AI：（开始长篇大论...）
你：不是说简洁点吗？
AI：啥时候说的？
```

**Memory Hub 解决**:
- 持久化存储记忆
- 语义搜索检索
- 多智能体共享

---

### Q3: 和向量数据库有什么区别？

**A**: Memory Hub **基于**向量数据库（pgvector），但提供更多功能。

| 功能 | 纯向量数据库 | Memory Hub |
|------|------------|------------|
| 向量存储 | ✅ | ✅ |
| 语义搜索 | ✅ | ✅ |
| 记忆管理 | ❌ | ✅ |
| 自动提取 | ❌ | ✅ |
| 多智能体 | ❌ | ✅ |
| API 封装 | ❌ | ✅ |
| Web UI | ❌ | ✅ |

**简单说**: Memory Hub = 向量数据库 + 记忆管理 + API + UI

---

### Q4: 支持哪些大模型？

**A**: Memory Hub **不绑定特定大模型**，是独立的记忆层。

**支持**:
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Anthropic (Claude)
- ✅ 阿里通义千问
- ✅ 百度文心一言
- ✅ 任何支持 API 的 LLM

**集成方式**:
```javascript
// 在你的 AI 应用中
const memories = await memoryHub.search(agentId, userMessage);
const response = await llm.chat({
  message: userMessage,
  context: memories  // 注入记忆
});
```

---

### Q5: 收费吗？

**A**: **完全免费**，开源项目（MIT License）。

- ✅ 免费使用
- ✅ 免费部署
- ✅ 免费商用

**成本**:
- 自己部署：服务器成本（可选）
- 本地使用：零成本

---

## 安装部署

### Q6: 最低配置要求？

**A**: 

**本地开发**:
- CPU: 任意双核
- 内存：2GB
- 磁盘：1GB
- 系统：Linux/Mac/Windows

**生产环境**:
- CPU: 4 核+
- 内存：8GB+
- 磁盘：SSD 推荐
- 系统：Linux 推荐

**Docker 部署**:
```yaml
# docker-compose.yml 资源配置
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

---

### Q7: 安装失败怎么办？

**A**: 按以下步骤排查：

**步骤 1: 查看错误信息**
```bash
# 查看详细日志
memory-hub logs --verbose
```

**步骤 2: 常见问题**

**Node.js 版本过低**:
```bash
# 检查版本
node --version

# 需要 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**端口被占用**:
```bash
# 查看占用
lsof -i :8000

# 或用其他端口
memory-hub start -p 8080
```

**权限问题**:
```bash
# Linux/Mac
sudo memory-hub start

# 或修改目录权限
chmod -R 755 ~/.memory-hub
```

**步骤 3: 重新安装**
```bash
# 完全卸载
memory-hub uninstall

# 清理残留
rm -rf ~/.memory-hub

# 重新安装
curl -fsSL https://raw.githubusercontent.com/wenhao4126/memory-hub/master/scripts/install.sh | bash
```

---

### Q8: Docker 部署和直接安装有什么区别？

**A**:

| 特性 | Docker 部署 | 直接安装 |
|------|-----------|---------|
| 隔离性 | 完全隔离 | 共享系统 |
| 部署速度 | 快（镜像拉取） | 中（依赖安装） |
| 资源占用 | 稍高 | 较低 |
| 易用性 | 一键启动 | 需配置环境 |
| 生产推荐 | ✅ | ⚠️ 需额外配置 |

**选择建议**:
- **开发测试**: 直接安装（调试方便）
- **生产环境**: Docker 部署（隔离、稳定）
- **快速体验**: Docker 部署（最简单）

---

### Q9: 如何升级到新版本？

**A**:

**方式一：自动升级**
```bash
memory-hub upgrade
```

**方式二：手动升级**
```bash
# npm 安装
npm update -g memory-hub

# Docker 部署
docker-compose pull
docker-compose up -d
```

**方式三：重新安装**
```bash
memory-hub uninstall
curl -fsSL https://raw.githubusercontent.com/wenhao4126/memory-hub/master/scripts/install.sh | bash
```

**升级前注意**:
- ✅ 备份数据（`~/.memory-hub/data/`）
- ✅ 查看更新日志
- ✅ 测试环境先升级

---

## 使用问题

### Q10: 如何创建智能体？

**A**:

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "小笔",
    "description": "文案助手",
    "capabilities": ["写作", "翻译"]
  }'
```

**返回**:
```json
{
  "id": "agent_abc123",
  "name": "小笔",
  "created_at": "2026-03-19T19:00:00Z"
}
```

**保存好 `id`，后续操作需要！**

---

### Q11: 如何创建记忆？

**A**:

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "content": "用户喜欢简洁回答",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["偏好"]
  }'
```

**记忆类型**:
- `preference` - 用户偏好
- `fact` - 事实信息
- `experience` - 经验事件

**重要性**: 0.0-1.0，越高越重要

---

### Q12: 如何搜索记忆？

**A**:

**语义搜索**:
```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "query": "用户喜欢什么？",
    "match_count": 5
  }'
```

**标签搜索**:
```bash
curl "http://localhost:8000/api/v1/memories/search?agent_id=xxx&tags=偏好"
```

**混合搜索**:
```bash
curl -X POST http://localhost:8000/api/v1/memories/search/hybrid \
  -d '{
    "query": "用户偏好",
    "tags": ["偏好"],
    "min_importance": 0.7
  }'
```

---

### Q13: 记忆越多搜索越慢吗？

**A**: **不会**，使用了 HNSW 索引。

**性能数据**:
- 100 条记忆：~2ms
- 1 万条记忆：~5ms
- 100 万条记忆：~15ms

**优化建议**:
- 设置合理的 `similarity_threshold`（默认 0.7）
- 限制 `match_count`（默认 10）
- 使用标签过滤

---

### Q14: 如何删除记忆？

**A**:

**删除单条**:
```bash
curl -X DELETE http://localhost:8000/api/v1/memories/memory_123
```

**批量删除**:
```bash
curl -X POST http://localhost:8000/api/v1/memories/batch-delete \
  -d '{
    "agent_id": "agent_abc123",
    "tags": ["过期标签"]
  }'
```

**清空所有**:
```bash
curl -X DELETE http://localhost:8000/api/v1/agents/agent_abc123/memories
```

**注意**: 删除操作不可恢复！

---

### Q15: 如何更新记忆？

**A**:

```bash
curl -X PATCH http://localhost:8000/api/v1/memories/memory_123 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的内容",
    "importance": 0.9
  }'
```

**可更新字段**:
- `content` - 记忆内容
- `importance` - 重要性
- `tags` - 标签
- `memory_type` - 类型

---

## 性能优化

### Q16: 如何提高搜索速度？

**A**:

**1. 使用 HNSW 索引**
```sql
CREATE INDEX ON memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**2. 配置连接池**
```yaml
database:
  pool:
    min: 10
    max: 50
    idle_timeout: 30000
```

**3. 启用缓存**
```yaml
cache:
  enabled: true
  ttl: 3600
  max_size: 10000
```

**4. 优化查询**
```javascript
// ❌ 慢查询
search({ query: "", match_count: 1000 })

// ✅ 快查询
search({ 
  query: "具体查询", 
  match_count: 10,
  min_importance: 0.7,
  tags: ["重要"]
})
```

---

### Q17: 支持多少并发？

**A**: 取决于配置。

**默认配置**:
- 单实例：~100 QPS
- 连接池：20-100 连接

**生产配置**（5 实例集群）:
- 并发：~500 QPS
- 延迟：< 50ms (P99)

**扩展方式**:
```bash
# 增加 API 实例
docker-compose up -d --scale api=5

# 增加数据库连接池
DB_POOL_MAX=200 memory-hub start
```

---

### Q18: 记忆数量有限制吗？

**A**: **理论上无限制**，取决于数据库容量。

**实际建议**:
- 单个智能体：< 10 万条
- 总记忆量：< 1000 万条
- 单条记忆大小：< 10KB

**优化建议**:
- 定期清理过期记忆
- 归档历史记忆
- 分库分表（超大规模）

---

### Q19: 如何监控性能？

**A**:

**1. 内置监控端点**
```bash
curl http://localhost:8000/api/v1/metrics
```

**返回**:
```json
{
  "uptime": "7d 12h 30m",
  "requests_total": 123456,
  "avg_response_time": "12ms",
  "memory_count": 5678,
  "active_agents": 42
}
```

**2. 查看日志**
```bash
memory-hub logs --level WARN
```

**3. Web UI 监控**
```
http://localhost:8000/dashboard/metrics
```

---

## 故障排查

### Q20: 服务启动失败

**症状**: `memory-hub start` 报错

**排查步骤**:

**1. 查看错误日志**
```bash
memory-hub logs --verbose
```

**2. 常见错误**

**端口占用**:
```
Error: Address already in use (os error 98)
```
**解决**:
```bash
lsof -i :8000
kill -9 <PID>
# 或换端口
memory-hub start -p 8080
```

**数据库连接失败**:
```
Error: database connection failed
```
**解决**:
```bash
# 检查数据库
docker-compose ps

# 重启数据库
docker-compose restart db

# 查看数据库日志
docker-compose logs db
```

**配置文件错误**:
```
Error: invalid config file
```
**解决**:
```bash
# 重新生成配置
rm ~/.memory-hub/config.yaml
memory-hub init
```

---

### Q21: 搜索不到记忆

**症状**: 明明创建了记忆，搜索返回空

**排查步骤**:

**1. 确认记忆已创建**
```bash
curl http://localhost:8000/api/v1/agents/agent_xxx/memories
```

**2. 检查 agent_id**
```bash
# 列出所有智能体
curl http://localhost:8000/api/v1/agents

# 确认使用正确的 agent_id
```

**3. 调整相似度阈值**
```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -d '{
    "query": "xxx",
    "similarity_threshold": 0.5  # 降低阈值
  }'
```

**4. 检查嵌入模型**
```bash
# 测试嵌入服务
curl http://localhost:8000/api/v1/embeddings/test
```

---

### Q22: 记忆内容不准确

**症状**: 搜索返回的记忆不相关

**原因分析**:

1. **嵌入质量问题**
   - 嵌入模型不适合中文
   - 文本太短或太长

2. **阈值设置过高**
   - 默认 0.7 可能太高

3. **记忆内容问题**
   - 内容太模糊
   - 缺乏上下文

**解决方案**:

```bash
# 1. 降低相似度阈值
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -d '{
    "query": "xxx",
    "similarity_threshold": 0.6
  }'

# 2. 优化记忆内容
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "content": "具体、详细的记忆内容，包含上下文",
    "tags": ["明确", "具体"],
    "importance": 0.8
  }'

# 3. 使用标签过滤
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -d '{
    "query": "xxx",
    "tags": ["相关标签"]
  }'
```

---

### Q23: 数据库性能下降

**症状**: 使用一段时间后变慢

**排查步骤**:

**1. 检查数据库大小**
```bash
docker-compose exec db psql -c "SELECT pg_size_pretty(pg_database_size('memory_hub'));"
```

**2. 检查索引**
```bash
docker-compose exec db psql -c "\di memories*"
```

**3. 分析慢查询**
```bash
docker-compose exec db psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

**解决方案**:

```sql
-- 1. 重建索引
REINDEX INDEX memories_embedding_idx;

-- 2. 清理过期数据
DELETE FROM memories 
WHERE created_at < NOW() - INTERVAL '90 days';

-- 3. 优化表
VACUUM ANALYZE memories;

-- 4. 调整配置
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET work_mem = '64MB';
SELECT pg_reload_conf();
```

---

## 最佳实践

### Q24: 记忆内容怎么写？

**A**:

**✅ 好的记忆**:
```
"用户喜欢简洁的回答，通常不超过 3 段"
"用户是开发者，主要使用 TypeScript 和 Node.js"
"用户在北京工作，时区 GMT+8"
"项目 Memory Hub 于 2026-03 启动"
```

**❌ 差的记忆**:
```
"用户很好"  // 太模糊
"一些信息"  // 无意义
"..."       // 不完整
```

**写作原则**:
1. **具体** - 包含明确信息
2. **完整** - 有上下文
3. **结构化** - 便于搜索
4. **简洁** - 不啰嗦

---

### Q25: 如何组织记忆标签？

**A**:

**推荐标签体系**:

```
用户相关:
- 用户偏好
- 用户信息
- 用户历史

项目相关:
- 项目背景
- 技术栈
- 待办事项

对话相关:
- 重要决策
- 待跟进
- 已完成
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "content": "用户决定使用 PostgreSQL 作为数据库",
    "tags": ["项目决策", "技术选型", "重要"],
    "importance": 0.9
  }'
```

**标签原则**:
- 少而精（3-5 个）
- 层次清晰
- 便于搜索

---

### Q26: 重要性如何设置？

**A**:

**重要性分级**:

| 值范围 | 含义 | 示例 |
|--------|------|------|
| 0.9-1.0 | 极其重要 | 用户核心偏好、关键决策 |
| 0.7-0.9 | 重要 | 项目信息、技术栈 |
| 0.5-0.7 | 一般 | 普通事实、背景信息 |
| 0.3-0.5 | 次要 | 临时信息、细节 |
| 0.0-0.3 | 可忽略 | 过期信息、错误记忆 |

**动态调整**:
```bash
# 提升重要性
curl -X PATCH http://localhost:8000/api/v1/memories/memory_123 \
  -d '{"importance": 0.95}'

# 降低重要性
curl -X PATCH http://localhost:8000/api/v1/memories/memory_456 \
  -d '{"importance": 0.3}'
```

---

### Q27: 如何定期清理记忆？

**A**:

**方式一：按时间清理**
```bash
# 删除 90 天前的记忆
curl -X POST http://localhost:8000/api/v1/memories/batch-delete \
  -d '{
    "agent_id": "agent_xxx",
    "created_before": "2025-12-19T00:00:00Z"
  }'
```

**方式二：按标签清理**
```bash
curl -X POST http://localhost:8000/api/v1/memories/batch-delete \
  -d '{
    "agent_id": "agent_xxx",
    "tags": ["临时", "过期"]
  }'
```

**方式三：按重要性清理**
```bash
curl -X POST http://localhost:8000/api/v1/memories/batch-delete \
  -d '{
    "agent_id": "agent_xxx",
    "max_importance": 0.2
  }'
```

**自动化脚本**:
```bash
#!/bin/bash
# 每月 1 号执行清理
curl -X POST http://localhost:8000/api/v1/memories/batch-delete \
  -d '{"created_before": "'$(date -d '90 days ago' -I)'"}'
```

---

## 安全与隐私

### Q28: 数据安全吗？

**A**: 

**安全措施**:
- ✅ 本地部署（数据在你控制下）
- ✅ 支持加密存储
- ✅ 访问权限控制
- ✅ 审计日志

**建议**:
```yaml
# 生产环境配置
security:
  encryption_at_rest: true  # 加密存储
  api_key_required: true    # API 密钥认证
  rate_limiting: true       # 限流
  audit_logging: true       # 审计日志
```

---

### Q29: 如何保护敏感数据？

**A**:

**1. 加密存储**
```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "content": "敏感信息",
    "encryption": true,
    "access_level": "admin"
  }'
```

**2. 访问控制**
```yaml
access_control:
  roles:
    - name: admin
      permissions: [read, write, delete, admin]
    - name: user
      permissions: [read, write]
    - name: guest
      permissions: [read]
```

**3. 审计日志**
```bash
# 查看访问日志
curl http://localhost:8000/api/v1/audit-logs?memory_id=xxx
```

---

### Q30: 合规性如何保证？

**A**:

**GDPR 合规**:
- ✅ 数据可导出
- ✅ 数据可删除（被遗忘权）
- ✅ 访问日志记录
- ✅ 数据最小化

**实现示例**:
```bash
# 导出个人数据
curl http://localhost:8000/api/v1/export?agent_id=xxx

# 删除个人数据
curl -X DELETE http://localhost:8000/api/v1/agents/xxx

# 查看访问记录
curl http://localhost:8000/api/v1/access-logs?agent_id=xxx
```

---

## 贡献与反馈

### Q31: 如何提 Issue？

**A**: GitHub Issues: https://github.com/wenhao4126/memory-hub/issues

**提 Issue 模板**:

```markdown
**问题描述**:
简要描述问题

**复现步骤**:
1. ...
2. ...
3. ...

**预期行为**:
应该发生什么

**实际行为**:
实际发生了什么

**环境信息**:
- OS: 
- Node.js: 
- Memory Hub: 
- 部署方式：Docker/直接安装

**日志**:
```
相关日志内容
```
```

---

### Q32: 如何贡献代码？

**A**:

**步骤**:
```bash
# 1. Fork 项目
git fork https://github.com/wenhao4126/memory-hub

# 2. 克隆到本地
git clone git@github.com:your-username/memory-hub.git

# 3. 创建分支
git checkout -b feature/your-feature

# 4. 开发并提交
git commit -m "Add your feature"

# 5. 推送
git push origin feature/your-feature

# 6. 提 PR
# 在 GitHub 上创建 Pull Request
```

**代码规范**:
- 遵循 TypeScript 规范
- 添加单元测试
- 更新文档
- 通过 CI 检查

---

### Q33: 在哪里讨论？

**A**:

- 💬 GitHub Discussions: https://github.com/wenhao4126/memory-hub/discussions
- 📧 邮件列表：memory-hub@googlegroups.com（待创建）
- 🐦 Twitter: @MemoryHub（待创建）

---

## 还没找到答案？

**获取帮助**:

1. 📖 [完整文档](../docs/)
2. 💬 [GitHub Issues](https://github.com/wenhao4126/memory-hub/issues)
3. 📧 邮件联系（待添加）
4. 🐦 社交媒体（待添加）

---

*FAQ 持续更新中... 欢迎提交你的问题！*

**最后更新**: 2026-03-19
