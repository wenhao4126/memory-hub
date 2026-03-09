# 对话记忆提取失败问题排查报告

**排查日期**：2026-03-09
**排查人员**：小码
**问题级别**：紧急

---

## 一、问题描述

### 现象
- 数据库 `memories` 表的最新数据停留在 2026-03-07
- 2026-03-09（今天）憨货和傻妞的对话没有自动保存记忆
- Hook 机制已修复，但对话接口的自动记忆提取仍有问题

### 影响
- 对话过程中无法自动提取和存储记忆
- 导致智能体"忘记"用户信息和对话内容

---

## 二、排查过程

### 步骤 1：检查数据库表结构

```bash
docker exec memory-hub-db psql -U memory_user -d memory_hub -c "\dt"
```

**发现问题**：数据库中缺少 `conversations` 表！

```
 Schema |       Name       | Type  |    Owner    
--------+------------------+-------+-------------
 public | agents           | table | memory_user
 public | knowledge        | table | memory_user
 public | memories         | table | memory_user
 public | memory_relations | table | memory_user
 public | sessions         | table | memory_user
```

### 步骤 2：检查 API 日志

```bash
docker logs memory-hub-api --tail=200 | grep -E "(chat|memory|extract|error)"
```

**发现问题**：
1. LLM API 调用失败：`401 - Invalid API-key provided`
2. 记忆提取失败：`LLM API 调用失败: status=401`

### 步骤 3：检查代码逻辑

阅读以下文件：
- `backend/app/api/routes.py` - /chat 接口实现
- `backend/app/services/dialogue_enhancement_service.py` - chat_and_remember() 方法
- `backend/app/services/auto_memory_service.py` - auto_extract_and_store() 方法
- `backend/app/services/conversation_service.py` - 对话服务
- `backend/app/services/llm_service.py` - LLM 服务

**发现问题**：
1. `conversation_service.py` 尝试向 `conversations` 表插入数据，但表不存在
2. `llm_service.py` 使用 DashScope SDK，不支持 `sk-sp-` 开头的 Coding API Key

### 步骤 4：检查环境变量配置

```bash
docker exec memory-hub-api env | grep -E "(DASHSCOPE|LLM)"
```

**发现问题**：
- `DASHSCOPE_LLM_API_KEY=sk-sp-xxx`（Coding API Key）
- 但 `LLM_BASE_URL` 未传递到容器，导致使用默认值 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- DashScope SDK 不支持 Coding API Key

---

## 三、问题根因

### 根因 1：conversations 表不存在
- 初始化脚本 `scripts/init-auto-memory.sql` 未执行
- `conversation_service.py` 尝试插入数据时报错

### 根因 2：LLM API 配置不兼容
- `docker-compose.yml` 未传递 `LLM_BASE_URL` 环境变量
- `llm_service.py` 使用 DashScope SDK，不支持 Coding API Key
- 导致 LLM 调用失败，记忆提取失败

---

## 四、修复方案

### 修复 1：创建 conversations 表

```bash
docker exec -i memory-hub-db psql -U memory_user -d memory_hub < scripts/init-auto-memory.sql
```

### 修复 2：更新 docker-compose.yml

添加 `LLM_BASE_URL` 和 `LLM_MODEL` 环境变量：

```yaml
environment:
  # ...
  # LLM 配置（用于记忆提取和对话增强）
  LLM_MODEL: ${LLM_MODEL:-qwen3.5-plus}
  LLM_BASE_URL: ${LLM_BASE_URL:-https://coding.dashscope.aliyuncs.com/v1}
```

### 修复 3：修改 llm_service.py

将 DashScope SDK 改为 HTTP API 调用，支持 Coding API Key：

```python
# 使用 HTTP API 调用
url = f"{self.base_url}/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {self.api_key}"
}

payload = {
    "model": self.model_name,
    "messages": full_messages,
    "temperature": temperature,
    "max_tokens": max_tokens
}

async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(url, headers=headers, json=payload)
```

---

## 五、验证结果

### 测试 1：对话接口测试

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "83a4c7c5-ab61-43de-b8e1-0a1e688100c0",
    "session_id": "test_session_final",
    "user_message": "我是憨货，我喜欢吐槽风格，记住我喜欢吃火锅",
    "auto_extract": true
  }'
```

**结果**：成功！
- 对话回复符合"吐槽风格"
- 记忆提取成功（3 条新记忆）
- 对话记录成功保存

### 测试 2：数据库验证

```bash
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT * FROM memories ORDER BY created_at DESC LIMIT 5;"
```

**结果**：新记忆已存储
- "用户名叫憨货" - fact
- "用户喜欢吐槽风格" - fact
- "今天测试记忆功能" - experience

### 测试 3：对话记录验证

```bash
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 5;"
```

**结果**：对话记录已保存

---

## 六、总结

### 修复内容
1. ✅ 创建 `conversations` 表
2. ✅ 更新 `docker-compose.yml` 添加 LLM 配置
3. ✅ 修改 `llm_service.py` 支持 Coding API Key

### 遗留问题
1. **记忆去重逻辑**：当前使用向量相似度 > 0.85 判断重复，可能导致部分记忆被误判为重复
2. **性能优化**：LLM 调用延迟较高（约 60 秒），可以考虑异步处理或缓存

### 建议
1. 添加数据库迁移工具（如 Alembic），避免手动执行 SQL 脚本
2. 添加健康检查，检测 conversations 表是否存在
3. 优化 LLM 调用超时配置

---

**报告人**：小码
**完成时间**：2026-03-09 01:55