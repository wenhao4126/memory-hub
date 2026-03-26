# 小码任务数据表 - 快速开始指南

> **作者**：小码 1 号 🟡  
> **日期**：2026-03-24  
> **版本**：v1.0

---

## 🚀 快速开始

### 1. 执行迁移（如果还未执行）

```bash
docker exec -i memory-hub-db psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

### 2. 验证表已创建

```bash
docker exec -i memory-hub-db psql -U memory_user -d memory_hub -c "\d coder_tasks"
```

### 3. 使用 Python SDK

```python
# 导入
import asyncio
import sys
sys.path.insert(0, '/home/wen/projects/memory-hub/backend')

from app.database import db
from app.services.coder_task_service import coder_task_service

# 使用
async def main():
    await db.connect()
    
    # 创建任务
    task = await coder_task_service.create_coder_task(
        title="我的第一个任务",
        coder_name="小码 1 号",
        task_type="code",
        priority="高"
    )
    print(f"创建任务：{task['id']}")
    
    # 更新状态
    await coder_task_service.update_coder_task(
        task_id=task['id'],
        status="running",
        progress=0
    )
    
    # 更新进度
    await coder_task_service.update_coder_task(
        task_id=task['id'],
        progress=50,
        progress_message="完成一半"
    )
    
    # 完成任务
    await coder_task_service.complete_coder_task(
        task_id=task['id'],
        result="任务完成！"
    )
    
    # 获取统计
    stats = await coder_task_service.get_task_statistics()
    print(f"统计：{stats}")
    
    await db.disconnect()

asyncio.run(main())
```

### 4. 使用 SQL

```sql
-- 创建任务
INSERT INTO coder_tasks (coder_name, task_type, title, priority)
VALUES ('小码 1 号', 'code', '开发新功能', '高');

-- 查看所有任务
SELECT * FROM coder_tasks ORDER BY created_at DESC;

-- 查看小码 1 号的任务
SELECT * FROM coder_tasks WHERE coder_name = '小码 1 号';

-- 查看待执行任务
SELECT * FROM coder_tasks WHERE status = 'pending';

-- 统计
SELECT coder_name, status, COUNT(*) 
FROM coder_tasks 
GROUP BY coder_name, status;
```

### 5. 运行测试

```bash
# SQL 测试
docker exec -i memory-hub-db psql -U memory_user -d memory_hub < database/test_coder_tasks.sql

# Python 测试
python tests/test_coder_tasks_simple.py
```

---

## 📚 完整文档

- **详细使用**: [CODER_TASKS_README.md](./CODER_TASKS_README.md)
- **实现总结**: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
- **数据库迁移**: [README.md](./README.md)

---

## 🆘 常见问题

**Q: 表不存在？**
```bash
docker exec -i memory-hub-db psql -U memory_user -d memory_hub < database/03_coder_tasks_table.sql
```

**Q: 如何清空数据？**
```sql
DELETE FROM coder_tasks;
```

**Q: 如何查看表结构？**
```bash
docker exec -i memory-hub-db psql -U memory_user -d memory_hub -c "\d coder_tasks"
```

---

_快速开始指南完成！_
