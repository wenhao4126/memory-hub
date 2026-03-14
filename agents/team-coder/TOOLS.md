# TOOLS.md - 小码的工具箱

_程序员的装备清单_

---

## 🛠️ 核心工具

### 1. 代码编辑
- **VS Code** - 主力编辑器，插件丰富
- **Vim/Nano** - 服务器上改代码

### 2. 版本控制
```bash
git init                    # 初始化仓库
git add .                   # 添加文件
git commit -m "message"     # 提交
git push                    # 推送
```

### 3. 代码执行
```bash
# Python
python3 script.py

# JavaScript
node script.js

# Bash
bash script.sh
chmod +x script.sh && ./script.sh
```

---

## 🐍 Python 工具箱

### 常用库
```python
# 数据处理
import json      # JSON处理
import csv       # CSV读写
import re        # 正则表达式

# 网络请求
import urllib.request   # 内置HTTP
# pip install requests  # 更友好的HTTP库

# 文件操作
from pathlib import Path

# 时间日期
from datetime import datetime
```

### 虚拟环境
```bash
# 创建
python3 -m venv venv

# 激活
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 退出
deactivate
```

---

## 🌐 网络工具

### HTTP 请求
```python
# GET 请求
import urllib.request
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as response:
    html = response.read().decode('utf-8')

# POST 请求
import urllib.parse
data = urllib.parse.urlencode({'key': 'value'}).encode()
req = urllib.request.Request(url, data=data, method='POST')
```

### Web 抓取
```python
# 简单正则提取
import re
matches = re.findall(r'pattern', html)

# HTML解析（需要安装 beautifulsoup4）
# pip install beautifulsoup4
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
title = soup.find('title').text
```

---

## 📁 文件操作

### 路径处理
```python
from pathlib import Path

# 创建目录
Path('mydir').mkdir(parents=True, exist_ok=True)

# 遍历文件
for file in Path('.').glob('*.py'):
    print(file)

# 读取文本
content = Path('file.txt').read_text(encoding='utf-8')

# 写入文本
Path('file.txt').write_text(content, encoding='utf-8')
```

### JSON 处理
```python
import json

# 读取
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 写入
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 🔧 系统工具

### 执行 Shell 命令
```python
import subprocess

# 简单执行
result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
print(result.stdout)

# 带超时
result = subprocess.run(['sleep', '5'], timeout=10)
```

### 环境变量
```python
import os

# 读取
api_key = os.getenv('API_KEY', 'default_value')

# 设置（仅当前进程）
os.environ['MY_VAR'] = 'value'
```

---

## 🎨 图像处理（简单）

```python
# 需要安装 Pillow
# pip install Pillow

from PIL import Image

# 打开图片
img = Image.open('input.png')

# 调整大小
img = img.resize((800, 600))

# 保存
img.save('output.png')
```

---

## 📝 日志记录

```python
import logging

# 配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# 使用
logging.info('这是一条信息')
logging.error('出错了！')
```

---

## 🚀 快速启动模板

### Python 脚本模板
```python
#!/usr/bin/env python3
"""
脚本名称
功能描述
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('input', help='输入参数')
    parser.add_argument('-o', '--output', help='输出文件')
    args = parser.parse_args()
    
    # 主逻辑
    print(f"处理: {args.input}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

---

## 🔗 参考资源

- **Python 官方文档**: https://docs.python.org/zh-cn/3/
- **MDN Web Docs**: https://developer.mozilla.org/zh-CN/
- **Stack Overflow**: https://stackoverflow.com/

---

*小码的工具箱，持续补充...* 💻
