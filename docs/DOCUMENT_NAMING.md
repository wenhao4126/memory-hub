# 文档命名规范

> **最后更新**: 2026-03-16  
> **作者**: 小码 🟡  
> **决策者**: 憨货

---

## 📋 概述

小搜/小写等手下生成的 `.md` 文档，根据内容自动生成有意义的中文名字，保存到 Obsidian 目录，并添加到数据库 `knowledge` 表。

---

## 🔄 流程对比

### 旧流程
```
小搜搜索 → 保存为时间戳命名 → 存入 knowledge 表
20260316_143000_API 文档.md
```

### 新流程
```
小搜搜索 → 根据内容生成中文名字 → 保存到 Obsidian → 存入 knowledge 表
Python 快速入门教程_20260316_194800.md
```

---

## 📝 命名规则

### 基本原则

1. **有意义** - 能看出文档内容
2. **简洁** - 不超过 30 个字
3. **中文优先** - 优先使用中文
4. **保留关键英文** - 技术名词保留英文（如 Python、Vue.js）

### 命名格式

```
{内容主题}_{时间戳}.md
```

**示例：**
- `Python 快速入门教程_20260316_194800.md`
- `Deno 运行时官方文档_20260316_194801.md`
- `Vue.js 组件开发指南_20260316_194802.md`
- `React 快速上手_20260316_194803.md`
- `Docker 入门教程_20260316_194804.md`

---

## 🧹 清理规则

### 移除的内容
- 网站名称后缀：`菜鸟教程`、`廖雪峰`、`CSDN`、`掘金` 等
- 多余的分隔符：`-`、`|`、`_`
- 非法字符：`< > : " / \ | ? *`

### 保留的内容
- 中文字符
- 英文字母、数字
- 常见标点：`.`（点）、`+`（加号）、`#`（井号）
- 空格（保持可读性）

---

## 🔧 技术实现

### 核心服务

#### 1. DocumentNamingService（文档命名服务）

**文件位置**: `backend/app/services/document_naming_service.py`

**主要方法**:
```python
async def generate_chinese_name(
    self,
    title: str,
    content: str = None,
    source: str = None,
    url: str = None
) -> str:
    """
    根据文档内容生成有意义的中文名字
    
    返回：中文文件名（不含 .md 后缀）
    """
```

**功能特点**:
- 提取技术名词（Python、Vue.js、React 等）
- 清理网站名称和多余符号
- 自动添加文档类型后缀（教程、指南、文档等）
- 限制长度不超过 30 个字

#### 2. DocumentStorageService（文档存储服务）

**文件位置**: `backend/app/services/document_storage_service.py`

**主要修改**:
```python
async def save_document(
    self,
    title: str,
    content: str,
    source: str,
    url: str = None,
    metadata: dict = None
) -> str:
    # 1. 调用命名服务生成中文名字
    chinese_name = await document_naming_service.generate_chinese_name(
        title=title,
        content=content,
        source=source,
        url=url
    )
    
    # 2. 生成文件名（中文名字 + 时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{chinese_name}_{timestamp}.md"
    
    # 3. 保存到 Obsidian
    filepath = os.path.join(self.storage_dir, filename)
    ...
```

#### 3. SearchIntegrationService（搜索集成服务）

**文件位置**: `backend/app/services/search_integration_service.py`

**工作流程**:
1. 小搜搜索完成
2. 调用 `process_search_results()`
3. 抓取文档内容
4. **调用 `save_document()` → 自动生成中文名字**
5. 存入 `knowledge` 表
6. 创建 `shared_memory` 引用

---

## 📊 数据库字段

### knowledge 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `title` | TEXT | 文档标题 |
| `content` | TEXT | 文档内容 |
| `source` | TEXT | 来源（小搜/小写） |
| `file_path` | TEXT | .md 文件路径 |
| `metadata` | JSONB | 额外元数据 |
| `created_at` | TIMESTAMP | 创建时间 |

**示例记录**:
```sql
INSERT INTO knowledge (
    title, content, source, file_path, metadata
) VALUES (
    'Python 快速入门教程',
    '# Python 快速入门教程\n...',
    '小搜',
    '/home/wen/tools/obsidian/Python 快速入门教程_20260316_194800.md',
    '{"search_query": "Python 教程", "url": "https://..."}'
);
```

---

## 🧪 测试验证

### 1. 测试搜索功能

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python 教程", "max_results": 3}'
```

### 2. 查看生成的文件名

```bash
ls -lt /home/wen/tools/obsidian/ | head -10
```

**期望输出**:
```
Python 快速入门教程_20260316_194800.md
Deno 运行时官方文档_20260316_194801.md
Vue.js 组件开发指南_20260316_194802.md
```

### 3. 验证 knowledge 表

```bash
docker exec memory-hub-db psql -U memory_user -d memory_hub \
  -c "SELECT title, file_path FROM knowledge ORDER BY created_at DESC LIMIT 3;"
```

---

## 📚 示例

### 示例 1：菜鸟教程

**原始标题**:
```
Python 基础教程 | 菜鸟教程
```

**生成的文件名**:
```
Python 基础教程_20260316_194800.md
```

### 示例 2：Vue.js 官方文档

**原始标题**:
```
快速上手 - Vue.js
```

**生成的文件名**:
```
Vue.js 快速上手指南_20260316_194801.md
```

### 示例 3：Deno 官方文档

**原始标题**:
```
Deno 示例与教程 - Deno 文档
```

**生成的文件名**:
```
Deno 示例与教程_20260316_194802.md
```

---

## ⚠️ 注意事项

1. **时间戳避免重复** - 同一秒内保存的文件会有不同的时间戳
2. **文件名唯一性** - 如果文件名重复，时间戳会不同
3. **可读性优先** - 文件名保留空格，方便阅读
4. **技术名词保留英文** - Python、Vue.js、React 等不翻译

---

## 🔄 更新记录

### 2026-03-16
- ✅ 创建 `DocumentNamingService` 命名服务
- ✅ 修改 `DocumentStorageService.save_document()` 方法
- ✅ 更新服务导出 `__init__.py`
- ✅ 创建使用文档 `DOCUMENT_NAMING.md`

---

_小码 🟡 汇报完毕！_