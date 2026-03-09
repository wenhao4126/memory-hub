# TOOLS.md - 小搜的工具箱

_研究员的装备清单_

---

## 🔍 核心工具

### 1. DuckDuckGo 搜索（本地脚本）⭐
**用途**: 免费搜索，无需API Key  
**位置**: `./duckduckgo_search.py`  
**优点**: 完全免费、不限额、隐私好

**使用方法**:
```python
# 在Python中调用
import sys
sys.path.insert(0, '/home/wen/.openclaw/workspace/agents/team-researcher')
from duckduckgo_search import duck_search

# 执行搜索
results = duck_search("搜索关键词", max_results=5)

# 遍历结果
for r in results:
    print(f"标题: {r['title']}")
    print(f"链接: {r['url']}")
    print(f"摘要: {r['snippet']}")
```

**命令行测试**:
```bash
python3 duckduckgo_search.py "AI工具推荐"
```

**注意事项**:
- ✅ 完全免费，无需API Key
- ✅ 不限搜索次数（但别疯狂刷）
- ⚠️ 结果比Google少，但够用
- ⚠️ 网络不好时可能慢

---

### 2. web_search（备用）
**用途**: 系统自带的搜索工具  
**状态**: 需要Brave API Key（暂未配置）

**如果有API Key后可用**:
```javascript
web_search({ 
  query: "搜索内容", 
  count: 5
})
```

---

### 2. web_fetch - 深度抓取
**用途**: 获取网页详细内容  
**常用参数**:
- `url`: 目标网址
- `maxChars`: 最大字符数
- `extractMode`: 提取模式（markdown/text）

**示例**:
```javascript
web_fetch({ 
  url: "https://openai.com/blog/...",
  maxChars: 5000,
  extractMode: "markdown"
})
```

---

### 3. memory_search - 内部知识库
**用途**: 检索傻妞系统的内部记忆  
**常用参数**:
- `query`: 搜索内容
- `maxResults`: 最大结果数

**示例**:
```javascript
memory_search({ 
  query: "憨货的喜好",
  maxResults: 5
})
```

---

## 🛠️ 辅助工具

### 4. read - 读取本地文件
**用途**: 查看本地文档内容

### 5. exec - 执行命令
**用途**: 运行 shell 命令（谨慎使用）

---

## 💡 使用技巧

### 搜索组合拳
```javascript
// 第1步：快速搜索了解概况
const searchResults = await web_search({ query: "主题" });

// 第2步：抓取重要网页深入了解
const details = await web_fetch({ url: searchResults[0].url });

// 第3步：检索内部知识
const memory = await memory_search({ query: "相关记忆" });
```

### 信息验证流程
1. 用不同关键词多次搜索
2. 对比多个来源的说法
3. 优先采信权威来源
4. 矛盾处标注说明

---

*小搜的工具箱，持续补充...* 🔍
