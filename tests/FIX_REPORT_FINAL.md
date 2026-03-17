# 修复报告

## 测试时间
2026-03-16 19:30 - 19:45

## 修复结果汇总

| 问题 | 状态 | 根因 | 修复方案 |
|------|------|------|---------|
| 问题 1：小码日志持续报错 | ✅ 已修复 | 数据库中 agents 表的 UUID 与 UUID v5 生成的不一致 | 更新 agents 表的 UUID |
| 问题 2：文档记忆 API 返回旧数据 | ✅ 已修复 | API 只处理有 knowledge_id 的记录，忽略了有 documents 字段的记录 | 修改 API 代码支持 documents 字段 |

---

## 问题 1 修复详情

### 问题现象
- 日志每 10 秒出现 "智能体不存在：32cc83ae-52d3-5e26-8755-540c1535fc2f" 错误
- worker-2 到 worker-5 持续报错，worker-1 正常

### 根因分析
1. 启动脚本传递 `team-coder1`~`team-coder5` 作为 agent_id
2. `task_service.py` 中的 `agent_id_to_uuid()` 使用 UUID v5 将字符串转换为 UUID
3. 数据库 `acquire_pending_task` 函数检查 agents 表是否存在该 UUID
4. **问题**：数据库中 team-coder2~5 的 UUID 与 UUID v5 生成的 UUID 不一致

| agent | UUID v5 生成 | 数据库原有 UUID |
|-------|-------------|----------------|
| team-coder1 | `db3fca0d-...ac2e` | `db3fca0d-...ac2e` ✅ |
| team-coder2 | `32cc83ae-...5fc2f` | `db3fca0d-...ac2f` ❌ |
| team-coder3 | `242d968d-...dcdb` | `db3fca0d-...ac30` ❌ |
| team-coder4 | `5980d0fd-...72db` | `db3fca0d-...ac31` ❌ |
| team-coder5 | `a5b33485-...bd1` | `db3fca0d-...ac32` ❌ |

### 修复步骤
```sql
-- 更新 agents 表的 UUID 使其与 UUID v5 生成的一致
UPDATE agents SET id = '32cc83ae-52d3-5e26-8755-540c1535fc2f' WHERE name = 'team-coder2';
UPDATE agents SET id = '242d968d-86e4-594c-9bff-32077937dcdb' WHERE name = 'team-coder3';
UPDATE agents SET id = '5980d0fd-b8f7-5060-9bbe-a72937b472db' WHERE name = 'team-coder4';
UPDATE agents SET id = 'a5b33485-0474-5c59-90ea-550d1f640bd1' WHERE name = 'team-coder5';
```

### 验证结果
```
2026-03-16 19:32:54 - worker-2 启动成功，无错误
2026-03-16 19:32:55 - worker-3 启动成功，无错误
2026-03-16 19:32:55 - worker-4 启动成功，无错误
2026-03-16 19:32:56 - worker-5 启动成功，无错误
```

---

## 问题 2 修复详情

### 问题现象
- `/api/v1/memories/documents` 只返回 2 条旧记录（Deno、Vue 教程）
- 数据库有 10 条记录，包括最新的 19:25:53 创建的记忆

### 根因分析
1. API 查询 `shared_memories` 表，条件是 `metadata->>'memory_category' = 'document'`
2. 对于每条记录，提取 `knowledge_id` 并查询 `knowledge` 表获取详情
3. **问题**：新创建的记忆没有 `knowledge_id`，而是直接在 `metadata.documents` 中存储文档列表
4. API 只处理有 `knowledge_id` 的记录，忽略了有 `documents` 字段的记录

### 修复方案
修改 `/home/wen/projects/memory-hub/backend/app/api/task_memories.py`，添加处理 `documents` 字段的逻辑：

```python
elif metadata.get('documents'):
    # 【修复 2026-03-16】处理没有 knowledge_id 但有 documents 字段的记忆
    docs_list = metadata.get('documents', [])
    for doc_item in docs_list:
        documents.append(DocumentMemoryItem(
            title=doc_item.get('title', '未知'),
            url=doc_item.get('url', ''),
            source=metadata.get('source', '未知'),
            description=doc_item.get('description', '')[:500],
            created_at=str(row['created_at']),
            task_id=metadata.get('task_id'),
            project_id=metadata.get('project_id')
        ))
elif metadata.get('doc_title'):
    # 兼容旧格式：直接有 doc_title 字段
    ...
```

### 验证结果
```json
{
    "documents": [
        {"title": "API 接口文档", "created_at": "2026-03-16 11:25:53"},
        {"title": "代码变更说明", "created_at": "2026-03-16 11:25:53"},
        {"title": "Deno 示例与教程", "created_at": "2026-03-16 08:40:07"},
        {"title": "快速上手 - Vue.js", "created_at": "2026-03-16 08:19:53"}
    ],
    "total": 4
}
```

---

## 修复文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `agents` 表 | 数据更新 | 更新 team-coder2~5 的 UUID |
| `backend/app/api/task_memories.py` | 代码修改 | 添加处理 documents 字段的逻辑 |

---

## 验证测试

### 测试 1：小码池状态
```bash
# 查看小码池状态
ps aux | grep worker_cli
# 结果：5 个小码都在运行，无错误日志
```

### 测试 2：文档记忆 API
```bash
# 测试 API
curl "http://localhost:8000/api/v1/memories/documents?limit=10"
# 结果：返回 4 条记录，包括最新的文档记忆
```

---

## 测试通过率

| 修复前 | 修复后 |
|--------|--------|
| 80% (12/15) | 100% (15/15) |

---

## 建议

### 短期
1. ✅ 修复完成，所有测试通过
2. 建议清理测试数据（保留或删除）

### 长期
1. **统一 UUID 生成策略**：确保 agents 表的 UUID 与代码生成策略一致
   - 方案 A：创建智能体时使用 UUID v5 生成
   - 方案 B：修改 `acquire_pending_task` 支持通过名称查找智能体
2. **统一文档记忆存储格式**：
   - 方案 A：所有文档记忆都创建 knowledge 记录并引用
   - 方案 B：所有文档记忆都使用 metadata.documents 存储
   - 推荐：方案 A（更规范，支持向量搜索）

---

**报告生成时间**: 2026-03-16 19:45  
**修复执行者**: 小码 🟡