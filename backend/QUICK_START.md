# 小码任务 API - 快速开始指南

## 🚀 5 分钟快速上手

### 1. 启动服务

```bash
cd /home/wen/projects/memory-hub/backend

# 确保 .env 文件配置正确
# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问 Swagger 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

在 Swagger UI 中搜索 "小码任务" 即可看到所有新增的 API 端点。

### 3. 快速测试

#### 方法 1: 使用测试脚本

```bash
cd /home/wen/projects/memory-hub/backend
export API_KEY=your_api_key
./test_coder_tasks_api.sh
```

#### 方法 2: 使用 curl

```bash
# 创建任务
curl -X POST "http://localhost:8000/api/v1/coder-tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "coder_id": "550e8400-e29b-41d4-a716-446655440001",
    "coder_name": "小码 1 号",
    "task_type": "code",
    "title": "测试任务",
    "status": "completed",
    "result": "任务完成",
    "duration_seconds": 120
  }'

# 查询任务列表
curl -X GET "http://localhost:8000/api/v1/coder-tasks?limit=10" \
  -H "X-API-Key: your_api_key"
```

#### 方法 3: 使用 Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_api_key"

headers = {"X-API-Key": API_KEY}

# 创建任务
response = requests.post(
    f"{BASE_URL}/coder-tasks",
    json={
        "coder_id": "550e8400-e29b-41d4-a716-446655440001",
        "coder_name": "小码 1 号",
        "task_type": "code",
        "title": "测试任务",
        "status": "completed",
        "result": "任务完成",
        "duration_seconds": 120
    },
    headers=headers
)
print("创建任务:", response.json())

# 查询列表
response = requests.get(
    f"{BASE_URL}/coder-tasks?coder_name=小码 1 号",
    headers=headers
)
print("查询列表:", response.json())
```

### 4. 验证结构

运行验证脚本确保 API 结构正确：

```bash
cd /home/wen/projects/memory-hub/backend
python verify_api_structure.py
```

预期输出：
```
============================================================
🟡 验证 coder_tasks API 结构
============================================================
...
✅ 所有检查通过！API 结构正确
============================================================
```

---

## 📚 完整文档

查看完整 API 文档：
- **本地文件**: `CODER_TASKS_API.md`
- **实现总结**: `IMPLEMENTATION_SUMMARY.md`
- **在线文档**: http://localhost:8000/docs

---

## 🔍 常见问题

### Q: API 返回 401 错误？
**A**: 确保请求头中包含正确的 API Key：
```bash
-H "X-API-Key: your_api_key"
```

### Q: API 返回 404 错误？
**A**: 检查：
1. 服务是否已启动
2. URL 路径是否正确（`/api/v1/coder-tasks`）
3. 路由是否已注册（查看 main.py）

### Q: 如何获取 API Key？
**A**: 查看 `.env` 文件中的 `API_KEY` 配置，或联系管理员获取。

---

## 🎯 下一步

1. ✅ 运行测试脚本验证功能
2. ✅ 在 Swagger UI 中探索所有端点
3. ✅ 集成到小测或其他工具中
4. ✅ 根据实际需求调整参数和过滤条件

---

**🟡 小码 1 号 祝您使用愉快！**
