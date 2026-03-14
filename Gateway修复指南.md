# Gateway 配置修复指南 - 傻妞管家团队部署

> 问题：创建常驻智能体时 Gateway Token 认证失败
> 目标：修复配置，成功创建常驻智能体团队

---

## 🔍 问题诊断

从 `openclaw status` 输出看到：
```
Gateway: local · ws://127.0.0.1:18789 (local loopback) · 
unreachable (connect failed: unauthorized: gateway token mismatch)
```

**原因**：
1. Gateway 正在运行（pid 524）✅
2. 端口 18789 已监听 ✅
3. 但子智能体连接时 Token 认证失败 ❌

**根本原因**：
- 当前配置中 `gateway.auth.token` 已设置
- 但 `sessions_spawn` 工具调用时没有正确传递 token
- 或者 token 格式/权限不匹配

---

## 🛠️ 解决方案（按推荐顺序）

### 方案一：检查并重新生成 Gateway Token（推荐）

#### 步骤 1：查看当前 Token
```bash
# 查看配置文件中的 token
cat ~/.openclaw/openclaw.json | grep -A 5 '"auth"'
```

#### 步骤 2：生成新的 Gateway Token
```bash
# 生成新的随机 token
openclaw gateway token generate

# 或者手动设置一个（如果不支持 generate 命令）
NEW_TOKEN=$(openssl rand -hex 32)
echo "新 Token: $NEW_TOKEN"
```

#### 步骤 3：更新配置文件
```bash
# 备份原配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d)

# 使用 openclaw config 命令设置 token
openclaw config set gateway.auth.token "$NEW_TOKEN"

# 或者直接编辑配置文件
# 修改 ~/.openclaw/openclaw.json 中的 gateway.auth.token
```

#### 步骤 4：重启 Gateway
```bash
# 方法 A：使用 systemd
systemctl --user restart openclaw-gateway

# 方法 B：手动重启
openclaw gateway restart

# 方法 C：kill 后重新启动
kill 524  # 原进程 pid
openclaw gateway start
```

#### 步骤 5：验证
```bash
openclaw status
# 应该显示 Gateway: reachable ✅
```

---

### 方案二：配置环境变量传递 Token

如果方案一不行，尝试配置环境变量：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export OPENCLAW_GATEWAY_TOKEN="你的token"' >> ~/.bashrc
source ~/.bashrc

# 验证
env | grep OPENCLAW
```

---

### 方案三：使用 openclaw 命令行创建智能体（绕过 API）

如果 API 调用有问题，直接用命令行创建：

```bash
# 创建研究员智能体
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-researcher \
  --task-file /path/to/researcher_prompt.txt
```

---

### 方案四：检查 Gateway 绑定模式

如果以上都不行，可能是绑定模式问题：

```bash
# 查看当前绑定设置
openclaw config get gateway.bind

# 如果是 loopback，尝试改为 local（允许本地所有接口）
openclaw config set gateway.bind local

# 或者改为所有接口（如果你需要从其他机器访问）
openclaw config set gateway.bind 0.0.0.0

# 重启生效
openclaw gateway restart
```

---

## 📝 一键修复脚本

保存为 `fix_gateway.sh`，然后运行：

```bash
#!/bin/bash
set -e

echo "🔧 傻妞管家团队 - Gateway 修复脚本"
echo "=================================="

# 1. 备份配置
echo "📦 备份原配置..."
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)

# 2. 生成新 token
echo "🔑 生成新 Gateway Token..."
NEW_TOKEN=$(openssl rand -hex 32)
echo "新 Token: ${NEW_TOKEN:0:16}...${NEW_TOKEN: -8}"

# 3. 更新配置
echo "⚙️ 更新配置..."
# 使用 jq 修改 JSON（如果没有 jq，需要手动编辑）
if command -v jq &> /dev/null; then
    jq --arg token "$NEW_TOKEN" '.gateway.auth.token = $token' \
        ~/.openclaw/openclaw.json > ~/.openclaw/openclaw.json.tmp \
        && mv ~/.openclaw/openclaw.json.tmp ~/.openclaw/openclaw.json
else
    echo "⚠️ 未安装 jq，请手动编辑 ~/.openclaw/openclaw.json"
    echo "将 gateway.auth.token 改为: $NEW_TOKEN"
    exit 1
fi

# 4. 重启 Gateway
echo "🔄 重启 Gateway..."
if systemctl --user is-active openclaw-gateway &> /dev/null; then
    systemctl --user restart openclaw-gateway
else
    # 查找并杀死旧进程
    pkill -f "openclaw-gateway" || true
    sleep 1
    openclaw gateway start &
    sleep 2
fi

# 5. 验证
echo "✅ 验证状态..."
sleep 2
openclaw status | grep -A 2 "Gateway"

echo ""
echo "🎉 修复完成！"
echo "现在可以创建常驻智能体团队了"
echo "运行: openclaw subagents list"
```

---

## 🧪 修复后测试

### 测试 1：检查 Gateway 状态
```bash
openclaw status
# 应该显示：Gateway: reachable ✅
```

### 测试 2：查看子智能体列表
```bash
openclaw subagents list
# 应该正常返回，不报 token 错误
```

### 测试 3：创建测试智能体
```bash
# 创建一个简单的测试智能体
openclaw sessions spawn \
  --runtime subagent \
  --mode run \
  --label test-agent \
  --task "你好，请回复'测试成功'" \
  --timeout 30

# 如果成功，就可以创建常驻团队了！
```

---

## 🚀 创建傻妞管家团队（修复后）

Gateway 修复成功后，使用以下命令创建团队：

```bash
#!/bin/bash
# start_silly_team.sh

echo "🚀 启动傻妞管家团队..."

# 1. 研究员
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-researcher \
  --task "你是【研究员】..." &

# 2. 程序员
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-coder \
  --task "你是【程序员】..." &

# 3. 写手
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-writer \
  --task "你是【写手】..." &

# 4. 分析师
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-analyst \
  --task "你是【分析师】..." &

# 5. 浏览器专家
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-browser \
  --task "你是【浏览器专家】..." &

# 6. 代码审查员
openclaw sessions spawn \
  --runtime subagent \
  --mode session \
  --thread \
  --label team-code-reviewer \
  --task "你是【高级代码审查员】..." &

wait
echo "✅ 傻妞管家团队全部就位！"
openclaw subagents list
```

---

## ❓ 如果还是不行

### 检查 1：确认 openclaw 版本
```bash
openclaw --version
# 建议升级到最新版
npm install -g openclaw
```

### 检查 2：查看 Gateway 日志
```bash
# 如果有 systemd
journalctl --user -u openclaw-gateway -f

# 或者
openclaw logs --follow
```

### 检查 3：直接查看配置文件
```bash
cat ~/.openclaw/openclaw.json | jq '.gateway'
```

### 检查 4：临时方案（不用常驻智能体）
如果暂时搞不定 Gateway，可以先使用 **临时智能体**（`mode: run`）：

```javascript
// 每次有任务就创建一个，干完活自动退出
const result = await sessions_spawn({
  task: "任务内容",
  runtime: "subagent",
  mode: "run",  // 不是 session，不需要长期保持
  runTimeoutSeconds: 600
});
```

这个方案**不需要修复 Gateway** 也能工作！

---

## 📝 配置文件参考

修复后的 `~/.openclaw/openclaw.json` 应该包含：

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "你的64位十六进制token"
    },
    "nodes": {
      "denyCommands": [...]
    }
  }
}
```

---

**憨货，按这个步骤来，应该能搞定！** 搞不定随时喊我 😎
