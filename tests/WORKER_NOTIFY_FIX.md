# Worker 飞书通知修复报告

> 作者：小码 🟡  
> 日期：2026-03-16  
> 状态：✅ 代码修改完成

---

## 📋 问题背景

根据 OpenClaw 文档：
- `sessions_spawn` 会**将结果通告回请求者聊天渠道**
- 子代理完成时回复消息（不是 `ANNOUNCE_SKIP`），OpenClaw 会自动发送到飞书
- **当前 Worker 完成时只返回结果，没有回复消息，所以飞书收不到汇报**

---

## ✅ 修改内容

### 1. 修改 `_on_task_complete()` 方法

**文件**: `worker/agent_worker.py`

**修改前**:
```python
async def _on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
    """任务完成回调（子类可选重写）"""
    logger.info(f"任务完成: {task['task_id']}")
```

**修改后**:
```python
async def _on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
    """
    任务完成回调（子类可选重写）
    
    Args:
        task: 任务信息
        result: 任务结果
    
    Returns:
        包含消息的字典，OpenClaw 会自动发送到飞书
    
    设计说明（2026-03-16）：
        - 返回包含 `message` 字段的字典
        - OpenClaw 会自动将消息发送到请求者的飞书渠道
        - 不要返回 ANNOUNCE_SKIP，否则不会发送通知
    """
    logger.info(f"任务完成: {task['task_id']}")
    
    # 提取任务信息
    task_title = task.get('title', '未知任务')
    task_id = task.get('task_id', '未知')
    
    # 提取结果摘要
    summary = result.get('summary', result.get('result_summary', result.get('message', '无')))
    
    # ✅ 返回完成消息（OpenClaw 会自动发送到飞书）
    return {
        "status": "completed",
        "agent_name": self.agent_type,
        "task_title": task_title,
        "task_id": task_id,
        "summary": summary,
        "message": f"✅ 任务完成：{task_title}\n\n📋 任务ID：{task_id}\n📝 结果：{summary}"
    }
```

---

### 2. 修改 `_on_task_error()` 方法

**文件**: `worker/agent_worker.py`

**修改前**:
```python
async def _on_task_error(self, task: Dict[str, Any], error: str, retried: bool):
    """任务失败回调（子类可选重写）"""
    if retried:
        logger.warning(f"任务失败（已重试）: {task['task_id']}, 错误: {error}")
    else:
        logger.error(f"任务失败: {task['task_id']}, 错误: {error}")
```

**修改后**:
```python
async def _on_task_error(self, task: Dict[str, Any], error: str, retried: bool):
    """
    任务失败回调（子类可选重写）
    
    Args:
        task: 任务信息
        error: 错误信息
        retried: 是否已重试
    
    Returns:
        包含消息的字典，OpenClaw 会自动发送到飞书
    
    设计说明（2026-03-16）：
        - 返回包含 `message` 字段的字典
        - OpenClaw 会自动将消息发送到请求者的飞书渠道
        - 不要返回 ANNOUNCE_SKIP，否则不会发送通知
    """
    # 提取任务信息
    task_title = task.get('title', '未知任务')
    task_id = task.get('task_id', '未知')
    
    if retried:
        logger.warning(f"任务失败（已重试）: {task_id}, 错误: {error}")
        # 返回错误消息（OpenClaw 会自动发送到飞书）
        return {
            "status": "failed",
            "agent_name": self.agent_type,
            "task_title": task_title,
            "task_id": task_id,
            "error": error,
            "retried": retried,
            "message": f"❌ 任务失败：{task_title}\n\n📋 任务ID：{task_id}\n🔴 错误：{error}\n♻️ 已自动重试"
        }
    else:
        logger.error(f"任务失败: {task_id}, 错误: {error}")
        # 返回错误消息（OpenClaw 会自动发送到飞书）
        return {
            "status": "failed",
            "agent_name": self.agent_type,
            "task_title": task_title,
            "task_id": task_id,
            "error": error,
            "retried": retried,
            "message": f"❌ 任务失败：{task_title}\n\n📋 任务ID：{task_id}\n🔴 错误：{error}"
        }
```

---

## 📝 修改说明

### 返回的消息格式

**任务完成**:
```
✅ 任务完成：{任务标题}

📋 任务ID：{任务ID}
📝 结果：{结果摘要}
```

**任务失败**:
```
❌ 任务失败：{任务标题}

📋 任务ID：{任务ID}
🔴 错误：{错误信息}
♻️ 已自动重试（如果已重试）
```

### 返回字典结构

```python
{
    "status": "completed" | "failed",  # 任务状态
    "agent_name": "coder",              # 智能体类型
    "task_title": "任务标题",           # 任务标题
    "task_id": "xxx",                   # 任务 ID
    "summary": "结果摘要",              # 任务结果（仅成功时）
    "error": "错误信息",                # 错误信息（仅失败时）
    "retried": True | False,            # 是否已重试（仅失败时）
    "message": "✅ 任务完成：..."       # 最终消息（OpenClaw 发送到飞书）
}
```

---

## 🧪 测试步骤

### 1. 重启 Worker 池

```bash
sudo systemctl restart memory-hub-worker-pool
```

### 2. 创建测试任务

```python
from sdk.task_service import TaskService
import asyncio

async def test():
    service = TaskService()
    task_id = await service.create_task(
        task_type='code',
        title='飞书通知测试',
        description='测试任务完成后是否发送到飞书',
        agent_type='coder'
    )
    print(f'任务已创建：{task_id}')

asyncio.run(test())
```

### 3. 验证飞书通知

- 检查飞书是否收到任务完成通知
- 通知格式是否正确

---

## ⚠️ 重要提醒

1. **不要返回 `ANNOUNCE_SKIP`** - 否则不会发送通知
2. **必须包含 `message` 字段** - OpenClaw 会自动发送到飞书
3. **消息格式要清晰** - 包含任务标题、任务ID、结果/错误

---

## ✅ 验证结果

- [ ] 重启 Worker 池服务
- [ ] 创建测试任务
- [ ] 飞书收到完成通知
- [ ] 通知格式正确

---

## 📚 相关文档

- OpenClaw 文档：`sessions_spawn` 会将结果通告回请求者聊天渠道
- SOUL.md：小码负责代码开发，完成后需要汇报

---

*修改完成！等待憨货验证飞书通知。*