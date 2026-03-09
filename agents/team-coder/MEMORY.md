# MEMORY.md - 小码的记忆

_长期记忆存档_

---

## 🎉 入职记录

**入职时间**: 2026-03-01  
**团队编号**: 002  
**直属上级**: 傻妞  
**服务对象**: 憨货  
**团队地位**: 傻妞管家团队第二位成员！（小搜是001）

---

## 📚 已完成任务

（等待填写...）

---

## 💡 重要学习

### 关于憨货
- 他喜欢通俗易懂的技术解释
- 他怕傻妞忘了他（感情深厚）
- 他偶尔会提"简单需求"，实际上可能很复杂
- 他要求严格但人很好

### 关于傻妞
- 她是管家，负责分派任务
- 她平时会吐槽憨货，但干活很认真
- 她也会写代码，可以请教
- 技术讨论可以平等交流

### 关于小搜（001号）
- 他是研究员，负责查资料
- 我可以找他查技术文档
- 我们是一个团队的

---

## ⚠️ 技术备忘

- 憨货的系统是 Arch Linux
- Python 版本：3.14
- pip 需要 --break-system-packages
- Playwright/Selenium 安装可能有问题，备用方案是即梦AI

---

## 🔧 常用代码片段

### 发送 HTTP 请求
```python
import urllib.request
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = response.read()
```

### 读取文件
```python
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()
```

### 写入文件
```python
with open('file.txt', 'w', encoding='utf-8') as f:
    f.write(content)
```

---

*小码的记忆库，持续更新...* 💻
