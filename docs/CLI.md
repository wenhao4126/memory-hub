# Memory Hub CLI 命令手册 🛠️

> 完整的命令行工具参考

---

## 📋 目录

1. [安装 CLI](#安装-cli)
2. [全局选项](#全局选项)
3. [命令参考](#命令参考)
4. [使用示例](#使用示例)
5. [环境变量](#环境变量)
6. [故障排查](#故障排查)

---

## 安装 CLI

### 方式一：npm 全局安装（推荐）

```bash
npm install -g memory-hub
```

### 方式二：本地链接（开发）

```bash
cd memory-hub
npm link
```

### 验证安装

```bash
memory-hub --version
memory-hub --help
```

---

## 全局选项

```bash
memory-hub [options] [command]
```

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-V, --version` | 输出版本号 | - |
| `-h, --help` | 输出帮助信息 | - |
| `-v, --verbose` | 详细输出模式 | false |
| `-q, --quiet` | 静默模式 | false |

---

## 命令参考

### memory-hub init

初始化 Memory Hub 配置。

**用法**:
```bash
memory-hub init [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-d, --dir <directory>` | 初始化目录 | 当前目录 |
| `-f, --force` | 覆盖已有配置 | false |

**示例**:
```bash
# 在当前目录初始化
memory-hub init

# 指定目录初始化
memory-hub init -d ~/projects/my-app

# 强制覆盖
memory-hub init -f
```

**输出**:
```
✔ Memory Hub 初始化成功
📁 目录：/home/user/projects/memory-hub
📄 创建：config.yaml
📄 创建：.env
💡 提示：编辑 config.yaml 配置你的参数
```

---

### memory-hub start

启动 Memory Hub 服务器。

**用法**:
```bash
memory-hub start [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-p, --port <port>` | 服务器端口 | 8000 |
| `-h, --host <host>` | 服务器主机 | localhost |
| `-d, --daemon` | 后台运行 | false |
| `-w, --workers <num>` | 工作进程数 | 4 |

**示例**:
```bash
# 默认启动
memory-hub start

# 指定端口
memory-hub start -p 8080

# 指定主机和端口
memory-hub start -h 0.0.0.0 -p 8000

# 后台运行
memory-hub start -d

# 多工作进程
memory-hub start -w 8
```

**输出**:
```
ℹ 正在启动 Memory Hub...
ℹ 监听地址：http://localhost:8000
ℹ 工作进程：4
✔ Memory Hub 运行中
📖 API 文档：http://localhost:8000/docs
```

---

### memory-hub stop

停止 Memory Hub 服务器。

**用法**:
```bash
memory-hub stop [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-f, --force` | 强制停止 | false |
| `-g, --graceful` | 优雅关闭 | true |

**示例**:
```bash
# 正常停止
memory-hub stop

# 强制停止
memory-hub stop -f

# 优雅关闭（等待请求完成）
memory-hub stop -g
```

**输出**:
```
ℹ 正在停止 Memory Hub...
ℹ 等待请求完成...
✔ Memory Hub 已停止
```

---

### memory-hub status

检查 Memory Hub 服务器状态。

**用法**:
```bash
memory-hub status [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-j, --json` | JSON 格式输出 | false |
| `-v, --verbose` | 详细信息 | false |

**示例**:
```bash
# 基本状态
memory-hub status

# JSON 输出
memory-hub status -j

# 详细信息
memory-hub status -v
```

**输出**:
```
✔ Memory Hub 运行中

状态：active
运行时间：2h 34m 15s
端口：8000
工作进程：4/4
内存使用：256MB
数据库：已连接
```

**JSON 输出**:
```json
{
  "status": "running",
  "uptime": 9255,
  "port": 8000,
  "workers": {
    "total": 4,
    "active": 4
  },
  "memory": "256MB",
  "database": "connected"
}
```

---

### memory-hub logs

查看 Memory Hub 服务器日志。

**用法**:
```bash
memory-hub logs [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-n, --lines <number>` | 显示行数 | 50 |
| `-f, --follow` | 实时跟踪 | false |
| `-l, --level <level>` | 日志级别 | INFO |
| `-t, --timestamp` | 显示时间戳 | true |

**示例**:
```bash
# 查看最近 50 行
memory-hub logs

# 查看最近 100 行
memory-hub logs -n 100

# 实时跟踪
memory-hub logs -f

# 只看错误
memory-hub logs -l ERROR

# 隐藏时间戳
memory-hub logs --no-timestamp
```

**输出**:
```
2026-03-19 18:54:00 [INFO] Server started
2026-03-19 18:54:01 [INFO] Database connected
2026-03-19 18:54:02 [INFO] Ready to accept connections
2026-03-19 18:55:00 [INFO] POST /api/v1/memories - 201
2026-03-19 18:55:01 [INFO] POST /api/v1/chat - 200
```

---

### memory-hub restart

重启 Memory Hub 服务器。

**用法**:
```bash
memory-hub restart [options]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-p, --port <port>` | 服务器端口 | 8000 |
| `-g, --graceful` | 优雅重启 | true |

**示例**:
```bash
# 快速重启
memory-hub restart

# 优雅重启
memory-hub restart -g

# 修改端口重启
memory-hub restart -p 8080
```

---

### memory-hub config

管理配置文件。

**用法**:
```bash
memory-hub config [command]
```

**子命令**:
| 命令 | 说明 |
|------|------|
| `show` | 显示当前配置 |
| `edit` | 编辑配置文件 |
| `validate` | 验证配置 |
| `backup` | 备份配置 |
| `restore` | 恢复配置 |

**示例**:
```bash
# 显示配置
memory-hub config show

# 编辑配置（使用默认编辑器）
memory-hub config edit

# 验证配置
memory-hub config validate

# 备份配置
memory-hub config backup

# 恢复配置
memory-hub config restore backup-20260319.yaml
```

---

### memory-hub db

数据库管理命令。

**用法**:
```bash
memory-hub db [command]
```

**子命令**:
| 命令 | 说明 |
|------|------|
| `migrate` | 运行数据库迁移 |
| `seed` | 填充初始数据 |
| `backup` | 备份数据库 |
| `restore` | 恢复数据库 |
| `clean` | 清理过期数据 |

**示例**:
```bash
# 运行迁移
memory-hub db migrate

# 填充数据
memory-hub db seed

# 备份数据库
memory-hub db backup backup.sql

# 恢复数据库
memory-hub db restore backup.sql

# 清理过期数据（>90 天）
memory-hub db clean --days 90
```

---

### memory-hub agent

智能体管理命令。

**用法**:
```bash
memory-hub agent [command]
```

**子命令**:
| 命令 | 说明 |
|------|------|
| `list` | 列出所有智能体 |
| `create` | 创建智能体 |
| `delete` | 删除智能体 |
| `info` | 查看智能体详情 |

**示例**:
```bash
# 列出智能体
memory-hub agent list

# 创建智能体
memory-hub agent create --name "小笔" --desc "文案专家"

# 查看智能体
memory-hub agent info <agent_id>

# 删除智能体
memory-hub agent delete <agent_id>
```

---

### memory-hub memory

记忆管理命令。

**用法**:
```bash
memory-hub memory [command]
```

**子命令**:
| 命令 | 说明 |
|------|------|
| `list` | 列出记忆 |
| `create` | 创建记忆 |
| `delete` | 删除记忆 |
| `search` | 搜索记忆 |
| `export` | 导出记忆 |
| `import` | 导入记忆 |

**示例**:
```bash
# 列出记忆
memory-hub memory list --agent <agent_id>

# 创建记忆
memory-hub memory create --agent <agent_id> --content "内容"

# 搜索记忆
memory-hub memory search "用户偏好"

# 导出记忆
memory-hub memory export --agent <agent_id> --output memories.json

# 导入记忆
memory-hub memory import --agent <agent_id> --input memories.json
```

---

## 使用示例

### 完整工作流

```bash
# 1. 安装
npm install -g memory-hub

# 2. 初始化
memory-hub init

# 3. 编辑配置
memory-hub config edit

# 4. 启动服务
memory-hub start

# 5. 检查状态
memory-hub status

# 6. 创建智能体
memory-hub agent create --name "小笔" --desc "文案专家"

# 7. 查看日志
memory-hub logs -f
```

### Docker 环境

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 进入容器
docker-compose exec api bash

# 在容器内使用 CLI
memory-hub status
```

### 生产环境

```bash
# 后台运行
memory-hub start -d -w 8

# 设置系统服务（systemd）
memory-hub config systemd > /etc/systemd/system/memory-hub.service
systemctl enable memory-hub
systemctl start memory-hub

# 查看状态
systemctl status memory-hub

# 查看日志
journalctl -u memory-hub -f
```

---

## 环境变量

可以通过环境变量配置 CLI 行为：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MEMORY_HUB_PORT` | 默认端口 | 8000 |
| `MEMORY_HUB_HOST` | 默认主机 | localhost |
| `MEMORY_HUB_CONFIG` | 配置文件路径 | ./config.yaml |
| `MEMORY_HUB_LOG_LEVEL` | 日志级别 | INFO |
| `MEMORY_HUB_API_KEY` | API 密钥 | - |

**示例**:
```bash
export MEMORY_HUB_PORT=8080
export MEMORY_HUB_LOG_LEVEL=DEBUG
memory-hub start
```

---

## 故障排查

### CLI 无法识别

**问题**: `command not found: memory-hub`

**解决**:
```bash
# 检查 npm 全局路径
npm config get prefix

# 添加到 PATH（~/.bashrc 或 ~/.zshrc）
export PATH=$(npm config get prefix)/bin:$PATH

# 重新加载
source ~/.bashrc
```

### 权限问题

**问题**: `EACCES: permission denied`

**解决**:
```bash
# 使用 sudo（不推荐）
sudo memory-hub start

# 或修改目录权限
sudo chown -R $USER:$USER ~/.memory-hub
```

### 端口占用

**问题**: `EADDRINUSE: address already in use`

**解决**:
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
memory-hub start -p 8080
```

### 配置文件错误

**问题**: `Invalid configuration`

**解决**:
```bash
# 验证配置
memory-hub config validate

# 重置配置
memory-hub init -f

# 检查 YAML 语法
cat config.yaml | yq .
```

---

## 帮助信息

```bash
# 全局帮助
memory-hub --help

# 命令帮助
memory-hub start --help
memory-hub init --help

# 查看所有命令
memory-hub help
```

---

*Memory Hub CLI v1.0.0 - Made with ❤️ by 傻妞 Team*
